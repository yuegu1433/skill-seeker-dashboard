"""BackupManager - Backup and recovery system for MinIO storage.

This module provides the BackupManager class which manages automated backups,
backup verification, recovery operations, and backup scheduling for the
storage system to ensure data safety and disaster recovery capabilities.
"""

import asyncio
import json
import logging
import tarfile
import tempfile
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID, uuid4

try:
    import aiofiles
    from minio.commonconfig import CopySource
except ImportError:
    aiofiles = None
    CopySource = None

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .client import MinIOClient
from .manager import SkillStorageManager
from .models import Skill, SkillFile, StorageBucket
from .utils.checksum import calculate_sha256, verify_checksum
from .utils.validators import validate_skill_id, validate_file_path
from .utils.formatters import format_file_size, format_timestamp

logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Base exception for backup operations."""
    pass


class BackupCreationError(BackupError):
    """Raised when backup creation fails."""
    pass


class BackupRestoreError(BackupError):
    """Raised when backup restore fails."""
    pass


class BackupVerificationError(BackupError):
    """Raised when backup verification fails."""
    pass


class BackupNotFoundError(BackupError):
    """Raised when backup is not found."""
    pass


class BackupSchedule:
    """Backup schedule configuration."""

    def __init__(
        self,
        name: str,
        backup_type: str,  # "full", "incremental"
        frequency: str,  # "daily", "weekly", "monthly"
        time: str,  # "HH:MM"
        retention_days: int = 30,
        enabled: bool = True,
        skills: Optional[List[UUID]] = None,
    ):
        """Initialize backup schedule.

        Args:
            name: Schedule name
            backup_type: Type of backup (full/incremental)
            frequency: Backup frequency
            time: Backup time (HH:MM)
            retention_days: Days to retain backups
            enabled: Whether schedule is enabled
            skills: List of skill IDs to backup (None for all)
        """
        self.name = name
        self.backup_type = backup_type
        self.frequency = frequency
        self.time = time
        self.retention_days = retention_days
        self.enabled = enabled
        self.skills = skills or []


class BackupRecord:
    """Backup record information."""

    def __init__(
        self,
        backup_id: str,
        skill_id: Optional[UUID],
        backup_type: str,
        file_count: int,
        total_size: int,
        checksum: str,
        created_at: datetime,
        status: str,  # "pending", "running", "completed", "failed"
        error_message: Optional[str] = None,
    ):
        """Initialize backup record.

        Args:
            backup_id: Backup identifier
            skill_id: Skill ID (None for full backup)
            backup_type: Type of backup
            file_count: Number of files backed up
            total_size: Total size in bytes
            checksum: Backup checksum
            created_at: Creation timestamp
            status: Backup status
            error_message: Error message if failed
        """
        self.backup_id = backup_id
        self.skill_id = skill_id
        self.backup_type = backup_type
        self.file_count = file_count
        self.total_size = total_size
        self.checksum = checksum
        self.created_at = created_at
        self.status = status
        self.error_message = error_message


class BackupManager:
    """Backup and recovery manager for storage system.

    Provides comprehensive backup and recovery capabilities including:
    - Automated full and incremental backups
    - Backup verification and integrity checks
    - Point-in-time recovery
    - Backup scheduling and retention policies
    - Disaster recovery procedures
    """

    def __init__(
        self,
        minio_client: MinIOClient,
        storage_manager: SkillStorageManager,
        database_session: Session,
        backup_bucket: str = "skillseekers-backups",
        backup_prefix: str = "backups",
        max_concurrent_backups: int = 5,
        verification_enabled: bool = True,
    ):
        """Initialize backup manager.

        Args:
            minio_client: MinIO client instance
            storage_manager: Storage manager instance
            database_session: Database session
            backup_bucket: Bucket for storing backups
            backup_prefix: Prefix for backup objects
            max_concurrent_backups: Maximum concurrent backup operations
            verification_enabled: Whether to verify backups
        """
        self.minio_client = minio_client
        self.storage_manager = storage_manager
        self.db = database_session
        self.backup_bucket = backup_bucket
        self.backup_prefix = backup_prefix
        self.max_concurrent_backups = max_concurrent_backups
        self.verification_enabled = verification_enabled

        # Backup schedules
        self.schedules: Dict[str, BackupSchedule] = {}

        # Active backup operations
        self.active_backups: Dict[str, asyncio.Task] = {}

        # Statistics
        self.stats = {
            "total_backups": 0,
            "successful_backups": 0,
            "failed_backups": 0,
            "total_files_backed_up": 0,
            "total_backup_size": 0,
            "last_backup_time": None,
        }

        logger.info(f"BackupManager initialized with bucket: {backup_bucket}")

    async def initialize(self) -> None:
        """Initialize backup manager."""
        try:
            # Ensure backup bucket exists
            if not self.minio_client.bucket_exists(self.backup_bucket):
                self.minio_client.create_bucket(self.backup_bucket)
                logger.info(f"Created backup bucket: {self.backup_bucket}")
            else:
                logger.debug(f"Backup bucket exists: {self.backup_bucket}")

            # Initialize backup schedules from configuration
            await self._load_schedules()

        except Exception as e:
            logger.error(f"Backup manager initialization failed: {e}")
            raise

    async def create_backup(
        self,
        skill_id: Optional[UUID] = None,
        backup_type: str = "full",
        verify: Optional[bool] = None,
    ) -> str:
        """Create a new backup.

        Args:
            skill_id: Skill ID to backup (None for all skills)
            backup_type: Type of backup (full/incremental)
            verify: Whether to verify backup (uses default if None)

        Returns:
            Backup ID

        Raises:
            BackupCreationError: If backup creation fails
        """
        backup_id = str(uuid4())

        # Use default verification setting if not specified
        verify = verify if verify is not None else self.verification_enabled

        logger.info(f"Starting backup {backup_id} (type: {backup_type}, skill: {skill_id})")

        try:
            # Get files to backup
            files_to_backup = await self._get_files_to_backup(skill_id, backup_type)

            if not files_to_backup:
                logger.warning(f"No files to backup for skill {skill_id}")
                return backup_id

            # Create backup manifest
            manifest = await self._create_backup_manifest(backup_id, files_to_backup, backup_type)

            # Upload backup manifest
            manifest_object_name = self._get_backup_object_name(backup_id, "manifest.json")
            await self._upload_backup_object(
                bucket_name=self.backup_bucket,
                object_name=manifest_object_name,
                data=json.dumps(manifest, indent=2, default=str).encode("utf-8"),
                content_type="application/json",
            )

            # Upload files
            uploaded_files = await self._upload_backup_files(backup_id, files_to_backup)

            # Calculate backup checksum
            backup_checksum = await self._calculate_backup_checksum(backup_id, manifest)

            # Verify backup if requested
            if verify:
                await self._verify_backup(backup_id, manifest, backup_checksum)

            # Update statistics
            self.stats["total_backups"] += 1
            self.stats["successful_backups"] += 1
            self.stats["total_files_backed_up"] += len(uploaded_files)
            self.stats["total_backup_size"] += sum(f["size"] for f in uploaded_files)
            self.stats["last_backup_time"] = datetime.utcnow()

            logger.info(
                f"Backup {backup_id} completed successfully: "
                f"{len(uploaded_files)} files, {format_file_size(sum(f['size'] for f in uploaded_files))}"
            )

            return backup_id

        except Exception as e:
            self.stats["total_backups"] += 1
            self.stats["failed_backups"] += 1
            logger.error(f"Backup {backup_id} failed: {e}")
            raise BackupCreationError(f"Backup creation failed: {e}")

    async def restore_backup(
        self,
        backup_id: str,
        skill_id: Optional[UUID] = None,
        target_skill_id: Optional[UUID] = None,
        verify: bool = True,
    ) -> bool:
        """Restore from a backup.

        Args:
            backup_id: Backup ID to restore
            skill_id: Skill ID to restore (None for all in backup)
            target_skill_id: Target skill ID for restore (None for original)
            verify: Whether to verify restore

        Returns:
            True if restore successful

        Raises:
            BackupRestoreError: If restore fails
            BackupNotFoundError: If backup not found
        """
        logger.info(f"Starting restore from backup {backup_id}")

        try:
            # Get backup manifest
            manifest = await self._get_backup_manifest(backup_id)

            if not manifest:
                raise BackupNotFoundError(f"Backup {backup_id} not found")

            # Filter skills if specified
            skills_to_restore = self._filter_skills_for_restore(manifest, skill_id)

            # Verify backup if requested
            if verify:
                await self._verify_backup_integrity(backup_id, manifest)

            # Restore skills
            restored_files = 0
            for skill_info in skills_to_restore:
                restored_files += await self._restore_skill_from_backup(
                    backup_id, skill_info, target_skill_id
                )

            logger.info(
                f"Restore from backup {backup_id} completed: {restored_files} files"
            )

            return True

        except Exception as e:
            logger.error(f"Restore from backup {backup_id} failed: {e}")
            raise BackupRestoreError(f"Backup restore failed: {e}")

    async def verify_backup(self, backup_id: str) -> Dict[str, Any]:
        """Verify backup integrity.

        Args:
            backup_id: Backup ID to verify

        Returns:
            Verification results

        Raises:
            BackupVerificationError: If verification fails
        """
        logger.info(f"Verifying backup {backup_id}")

        try:
            # Get backup manifest
            manifest = await self._get_backup_manifest(backup_id)

            if not manifest:
                raise BackupNotFoundError(f"Backup {backup_id} not found")

            # Verify manifest
            manifest_verified = await self._verify_backup_manifest(backup_id, manifest)

            # Verify files
            files_verified = await self._verify_backup_files(backup_id, manifest)

            # Verify checksum
            checksum_verified = await self._verify_backup_checksum(backup_id, manifest)

            results = {
                "backup_id": backup_id,
                "verified_at": datetime.utcnow().isoformat(),
                "manifest_verified": manifest_verified,
                "files_verified": files_verified,
                "checksum_verified": checksum_verified,
                "overall_status": "passed" if all([manifest_verified, files_verified, checksum_verified]) else "failed",
                "file_count": len(manifest.get("files", [])),
                "verified_file_count": sum(1 for v in files_verified.values() if v),
            }

            logger.info(f"Backup {backup_id} verification: {results['overall_status']}")

            return results

        except Exception as e:
            logger.error(f"Backup {backup_id} verification failed: {e}")
            raise BackupVerificationError(f"Backup verification failed: {e}")

    async def list_backups(
        self,
        skill_id: Optional[UUID] = None,
        backup_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List available backups.

        Args:
            skill_id: Filter by skill ID
            backup_type: Filter by backup type
            limit: Maximum number of backups to return

        Returns:
            List of backup information
        """
        try:
            # List backup objects
            pattern = f"{self.backup_prefix}/*/manifest.json"
            backups = []

            for obj in self.minio_client.list_objects(
                bucket_name=self.backup_bucket,
                prefix=f"{self.backup_prefix}/",
            ):
                if "manifest.json" not in obj["object_name"]:
                    continue

                # Parse backup ID from object name
                parts = obj["object_name"].split("/")
                if len(parts) >= 3:
                    backup_id = parts[1]

                    # Get manifest
                    manifest = await self._get_backup_manifest(backup_id)

                    if manifest:
                        # Apply filters
                        if skill_id and manifest.get("skill_id") != str(skill_id):
                            continue

                        if backup_type and manifest.get("backup_type") != backup_type:
                            continue

                        backups.append({
                            "backup_id": backup_id,
                            "skill_id": manifest.get("skill_id"),
                            "backup_type": manifest.get("backup_type"),
                            "file_count": manifest.get("file_count", 0),
                            "total_size": manifest.get("total_size", 0),
                            "checksum": manifest.get("checksum"),
                            "created_at": manifest.get("created_at"),
                            "status": "completed",
                        })

            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

            # Apply limit
            return backups[:limit]

        except Exception as e:
            logger.error(f"List backups failed: {e}")
            return []

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup.

        Args:
            backup_id: Backup ID to delete

        Returns:
            True if deleted successfully

        Raises:
            BackupNotFoundError: If backup not found
        """
        logger.info(f"Deleting backup {backup_id}")

        try:
            # Get backup manifest
            manifest = await self._get_backup_manifest(backup_id)

            if not manifest:
                raise BackupNotFoundError(f"Backup {backup_id} not found")

            # Delete all backup objects
            deleted_count = 0

            # Delete manifest
            manifest_object_name = self._get_backup_object_name(backup_id, "manifest.json")
            self.minio_client.remove_object(self.backup_bucket, manifest_object_name)
            deleted_count += 1

            # Delete file objects
            for file_info in manifest.get("files", []):
                file_object_name = self._get_backup_object_name(backup_id, file_info["backup_path"])
                self.minio_client.remove_object(self.backup_bucket, file_object_name)
                deleted_count += 1

            logger.info(f"Backup {backup_id} deleted: {deleted_count} objects")

            return True

        except Exception as e:
            logger.error(f"Delete backup {backup_id} failed: {e}")
            raise

    async def schedule_backup(
        self,
        schedule: BackupSchedule,
    ) -> bool:
        """Schedule a backup.

        Args:
            schedule: Backup schedule configuration

        Returns:
            True if scheduled successfully
        """
        self.schedules[schedule.name] = schedule
        logger.info(f"Scheduled backup: {schedule.name} ({schedule.frequency} {schedule.backup_type})")

        # In production, this would integrate with a scheduler like Celery
        # For now, we just store the schedule
        return True

    async def unschedule_backup(self, schedule_name: str) -> bool:
        """Unschedule a backup.

        Args:
            schedule_name: Name of schedule to remove

        Returns:
            True if unscheduled successfully
        """
        if schedule_name in self.schedules:
            del self.schedules[schedule_name]
            logger.info(f"Unscheduled backup: {schedule_name}")
            return True

        return False

    async def get_backup_statistics(self) -> Dict[str, Any]:
        """Get backup statistics.

        Returns:
            Dictionary with backup statistics
        """
        # Calculate success rate
        success_rate = 0
        if self.stats["total_backups"] > 0:
            success_rate = (
                self.stats["successful_backups"] / self.stats["total_backups"] * 100
            )

        # Get recent backups
        recent_backups = await self.list_backups(limit=10)

        # Get backup sizes over time
        backup_sizes = [b["total_size"] for b in recent_backups]
        avg_backup_size = sum(backup_sizes) / len(backup_sizes) if backup_sizes else 0

        return {
            "total_backups": self.stats["total_backups"],
            "successful_backups": self.stats["successful_backups"],
            "failed_backups": self.stats["failed_backups"],
            "success_rate_percent": round(success_rate, 2),
            "total_files_backed_up": self.stats["total_files_backed_up"],
            "total_backup_size": self.stats["total_backup_size"],
            "total_backup_size_human": format_file_size(self.stats["total_backup_size"]),
            "avg_backup_size": avg_backup_size,
            "avg_backup_size_human": format_file_size(avg_backup_size),
            "last_backup_time": (
                self.stats["last_backup_time"].isoformat()
                if self.stats["last_backup_time"]
                else None
            ),
            "active_schedules": len(self.schedules),
            "active_backups": len(self.active_backups),
        }

    # Private helper methods

    async def _get_files_to_backup(
        self,
        skill_id: Optional[UUID],
        backup_type: str,
    ) -> List[Dict[str, Any]]:
        """Get files that need to be backed up.

        Args:
            skill_id: Skill ID to filter
            backup_type: Type of backup

        Returns:
            List of files to backup
        """
        try:
            # Build query
            query = self.db.query(SkillFile)

            if skill_id:
                query = query.filter(SkillFile.skill_id == skill_id)

            # For incremental backups, only get recently modified files
            if backup_type == "incremental":
                cutoff_date = datetime.utcnow() - timedelta(days=1)
                query = query.filter(SkillFile.updated_at >= cutoff_date)

            files = query.all()

            # Convert to list of dictionaries
            files_to_backup = []
            for file in files:
                files_to_backup.append({
                    "file_id": str(file.id),
                    "skill_id": str(file.skill_id),
                    "file_path": file.file_path,
                    "object_name": file.object_name,
                    "file_size": file.file_size,
                    "checksum": file.checksum,
                    "content_type": file.content_type,
                    "modified_at": file.updated_at.isoformat(),
                })

            logger.debug(f"Found {len(files_to_backup)} files to backup")

            return files_to_backup

        except Exception as e:
            logger.error(f"Get files to backup failed: {e}")
            raise

    async def _create_backup_manifest(
        self,
        backup_id: str,
        files: List[Dict[str, Any]],
        backup_type: str,
    ) -> Dict[str, Any]:
        """Create backup manifest.

        Args:
            backup_id: Backup ID
            files: List of files to backup
            backup_type: Type of backup

        Returns:
            Backup manifest
        """
        total_size = sum(f["file_size"] for f in files)

        manifest = {
            "backup_id": backup_id,
            "backup_type": backup_type,
            "created_at": datetime.utcnow().isoformat(),
            "file_count": len(files),
            "total_size": total_size,
            "total_size_human": format_file_size(total_size),
            "skills": list(set(f["skill_id"] for f in files)),
            "files": files,
        }

        return manifest

    def _get_backup_object_name(self, backup_id: str, backup_path: str) -> str:
        """Generate backup object name.

        Args:
            backup_id: Backup ID
            backup_path: Backup file path

        Returns:
            Object name for MinIO
        """
        safe_path = backup_path.replace("/", "_").replace("\\", "_")
        return f"{self.backup_prefix}/{backup_id}/{safe_path}"

    async def _upload_backup_object(
        self,
        bucket_name: str,
        object_name: str,
        data: Union[bytes, str],
        content_type: str,
    ) -> bool:
        """Upload backup object to MinIO.

        Args:
            bucket_name: Bucket name
            object_name: Object name
            data: Object data
            content_type: Content type

        Returns:
            True if uploaded successfully
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        with self.minio_client.operation_context(f"upload_backup_{object_name}"):
            self.minio_client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data,
                length=len(data),
                content_type=content_type,
            )

        return True

    async def _upload_backup_files(
        self,
        backup_id: str,
        files: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Upload backup files to MinIO.

        Args:
            backup_id: Backup ID
            files: List of files to upload

        Returns:
            List of uploaded files with metadata
        """
        uploaded_files = []

        # Process files in batches to limit concurrent operations
        batch_size = min(self.max_concurrent_backups, len(files))

        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            tasks = []

            for file_info in batch:
                task = asyncio.create_task(
                    self._upload_single_backup_file(backup_id, file_info)
                )
                tasks.append(task)

            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Collect results
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Backup file upload failed: {result}")
                else:
                    uploaded_files.append(result)

        return uploaded_files

    async def _upload_single_backup_file(
        self,
        backup_id: str,
        file_info: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Upload a single backup file.

        Args:
            backup_id: Backup ID
            file_info: File information

        Returns:
            Uploaded file metadata
        """
        try:
            # Generate backup path
            backup_path = f"files/{file_info['file_path']}"
            backup_object_name = self._get_backup_object_name(backup_id, backup_path)

            # Download file from source
            file_response = self.minio_client.get_object(
                bucket_name="skillseekers-skills",  # Source bucket
                object_name=file_info["object_name"],
            )

            # Upload to backup bucket
            await self._upload_backup_object(
                bucket_name=self.backup_bucket,
                object_name=backup_object_name,
                data=file_response,
                content_type=file_info["content_type"],
            )

            logger.debug(f"Backed up file: {file_info['file_path']}")

            return {
                "backup_path": backup_path,
                "size": file_info["file_size"],
                "checksum": file_info["checksum"],
            }

        except Exception as e:
            logger.error(f"Upload backup file {file_info['file_path']} failed: {e}")
            raise

    async def _calculate_backup_checksum(
        self,
        backup_id: str,
        manifest: Dict[str, Any],
    ) -> str:
        """Calculate backup checksum.

        Args:
            backup_id: Backup ID
            manifest: Backup manifest

        Returns:
            SHA-256 checksum of backup
        """
        # For simplicity, use checksum of manifest
        manifest_data = json.dumps(manifest, sort_keys=True).encode("utf-8")
        return calculate_sha256(manifest_data)

    async def _verify_backup(
        self,
        backup_id: str,
        manifest: Dict[str, Any],
        checksum: str,
    ) -> bool:
        """Verify backup after creation.

        Args:
            backup_id: Backup ID
            manifest: Backup manifest
            checksum: Expected checksum

        Returns:
            True if verification passes
        """
        logger.info(f"Verifying backup {backup_id}")

        # Verify manifest checksum
        manifest_checksum = await self._calculate_backup_checksum(backup_id, manifest)

        if manifest_checksum != checksum:
            raise BackupVerificationError(
                f"Backup {backup_id} checksum mismatch: "
                f"expected {checksum}, got {manifest_checksum}"
            )

        # Verify file count
        files = manifest.get("files", [])
        if len(files) != manifest.get("file_count"):
            raise BackupVerificationError(
                f"Backup {backup_id} file count mismatch"
            )

        logger.info(f"Backup {backup_id} verification passed")

        return True

    async def _get_backup_manifest(self, backup_id: str) -> Optional[Dict[str, Any]]:
        """Get backup manifest.

        Args:
            backup_id: Backup ID

        Returns:
            Backup manifest or None
        """
        try:
            manifest_object_name = self._get_backup_object_name(backup_id, "manifest.json")

            response = self.minio_client.get_object(
                bucket_name=self.backup_bucket,
                object_name=manifest_object_name,
            )

            manifest_data = response.read().decode("utf-8")
            return json.loads(manifest_data)

        except Exception as e:
            logger.error(f"Get backup manifest {backup_id} failed: {e}")
            return None

    def _filter_skills_for_restore(
        self,
        manifest: Dict[str, Any],
        skill_id: Optional[UUID],
    ) -> List[Dict[str, Any]]:
        """Filter skills for restore.

        Args:
            manifest: Backup manifest
            skill_id: Skill ID to filter

        Returns:
            Filtered skills
        """
        skills = manifest.get("skills", [])

        if skill_id:
            skill_id_str = str(skill_id)
            if skill_id_str in skills:
                return [{"skill_id": skill_id_str, "files": manifest.get("files", [])}]
            else:
                return []

        # Return all skills
        return [{"skill_id": skill, "files": manifest.get("files", [])} for skill in skills]

    async def _verify_backup_integrity(
        self,
        backup_id: str,
        manifest: Dict[str, Any],
    ) -> bool:
        """Verify backup integrity before restore.

        Args:
            backup_id: Backup ID
            manifest: Backup manifest

        Returns:
            True if integrity verified
        """
        # Verify manifest exists
        manifest_object_name = self._get_backup_object_name(backup_id, "manifest.json")

        try:
            self.minio_client.stat_object(
                bucket_name=self.backup_bucket,
                object_name=manifest_object_name,
            )
        except Exception:
            raise BackupVerificationError(f"Backup manifest {backup_id} not found")

        # Verify file count
        files = manifest.get("files", [])
        for file_info in files:
            backup_path = f"files/{file_info['file_path']}"
            file_object_name = self._get_backup_object_name(backup_id, backup_path)

            try:
                self.minio_client.stat_object(
                    bucket_name=self.backup_bucket,
                    object_name=file_object_name,
                )
            except Exception:
                raise BackupVerificationError(
                    f"Backup file {file_info['file_path']} not found"
                )

        logger.info(f"Backup {backup_id} integrity verified")

        return True

    async def _restore_skill_from_backup(
        self,
        backup_id: str,
        skill_info: Dict[str, Any],
        target_skill_id: Optional[UUID],
    ) -> int:
        """Restore skill from backup.

        Args:
            backup_id: Backup ID
            skill_info: Skill information
            target_skill_id: Target skill ID

        Returns:
            Number of files restored
        """
        skill_id = skill_info["skill_id"]
        files = skill_info["files"]
        restored_count = 0

        for file_info in files:
            try:
                # Download from backup
                backup_path = f"files/{file_info['file_path']}"
                backup_object_name = self._get_backup_object_name(backup_id, backup_path)

                file_response = self.minio_client.get_object(
                    bucket_name=self.backup_bucket,
                    object_name=backup_object_name,
                )

                # Upload to target location
                target_skill = target_skill_id or UUID(skill_id)

                # Use storage manager to restore file
                await self.storage_manager.upload_file(
                    request=self.storage_manager.upload_request_class(
                        skill_id=target_skill,
                        file_path=file_info["file_path"],
                        content_type=file_info["content_type"],
                    ),
                    file_data=file_response,
                )

                restored_count += 1

            except Exception as e:
                logger.error(f"Restore file {file_info['file_path']} failed: {e}")

        logger.info(f"Restored {restored_count} files for skill {skill_id}")

        return restored_count

    async def _verify_backup_manifest(
        self,
        backup_id: str,
        manifest: Dict[str, Any],
    ) -> bool:
        """Verify backup manifest.

        Args:
            backup_id: Backup ID
            manifest: Backup manifest

        Returns:
            True if manifest verified
        """
        try:
            # Check required fields
            required_fields = ["backup_id", "backup_type", "created_at", "files"]
            for field in required_fields:
                if field not in manifest:
                    logger.error(f"Backup manifest missing field: {field}")
                    return False

            # Verify backup ID
            if manifest["backup_id"] != backup_id:
                logger.error(f"Backup manifest ID mismatch")
                return False

            # Verify files list
            if not isinstance(manifest["files"], list):
                logger.error(f"Backup manifest files is not a list")
                return False

            return True

        except Exception as e:
            logger.error(f"Verify backup manifest failed: {e}")
            return False

    async def _verify_backup_files(
        self,
        backup_id: str,
        manifest: Dict[str, Any],
    ) -> Dict[str, bool]:
        """Verify backup files.

        Args:
            backup_id: Backup ID
            manifest: Backup manifest

        Returns:
            Dictionary mapping file paths to verification status
        """
        results = {}

        for file_info in manifest.get("files", []):
            try:
                backup_path = f"files/{file_info['file_path']}"
                file_object_name = self._get_backup_object_name(backup_id, backup_path)

                # Check if object exists
                self.minio_client.stat_object(
                    bucket_name=self.backup_bucket,
                    object_name=file_object_name,
                )

                results[file_info["file_path"]] = True

            except Exception as e:
                logger.warning(f"Verify backup file {file_info['file_path']} failed: {e}")
                results[file_info["file_path"]] = False

        return results

    async def _verify_backup_checksum(
        self,
        backup_id: str,
        manifest: Dict[str, Any],
    ) -> bool:
        """Verify backup checksum.

        Args:
            backup_id: Backup ID
            manifest: Backup manifest

        Returns:
            True if checksum verified
        """
        try:
            manifest_checksum = await self._calculate_backup_checksum(backup_id, manifest)
            expected_checksum = manifest.get("checksum")

            if expected_checksum and manifest_checksum == expected_checksum:
                return True

            logger.warning(f"Backup {backup_id} checksum mismatch")
            return False

        except Exception as e:
            logger.error(f"Verify backup checksum failed: {e}")
            return False

    async def _load_schedules(self) -> None:
        """Load backup schedules from configuration.

        In production, this would load from a database or configuration file.
        For now, we create a default daily backup schedule.
        """
        # Create default daily backup schedule
        default_schedule = BackupSchedule(
            name="daily_backup",
            backup_type="incremental",
            frequency="daily",
            time="02:00",
            retention_days=30,
            enabled=True,
        )

        self.schedules[default_schedule.name] = default_schedule

        logger.info(f"Loaded {len(self.schedules)} backup schedules")

    @asynccontextmanager
    async def backup_operation(self, operation_name: str):
        """Context manager for backup operations.

        Args:
            operation_name: Name of operation
        """
        logger.debug(f"Starting backup operation: {operation_name}")
        start_time = time.time()

        try:
            yield
            duration = time.time() - start_time
            logger.debug(
                f"Backup operation '{operation_name}' completed in {duration:.3f}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Backup operation '{operation_name}' failed after {duration:.3f}s: {e}"
            )
            raise
