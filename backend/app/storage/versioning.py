"""VersionManager - File version control for MinIO storage.

This module provides the VersionManager class which manages file versions
and history in the MinIO storage system, providing complete version control
capabilities similar to Git.
"""

import asyncio
import io
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .client import MinIOClient, CopySource
from .models import SkillFile, FileVersion
from .schemas.file_operations import (
    FileVersionInfo,
    FileVersionCreateRequest,
    FileVersionRestoreRequest,
)
from .utils.checksum import calculate_sha256, verify_checksum
from .utils.validators import validate_file_path, validate_skill_id, validate_object_name
from .utils.formatters import format_file_size, format_timestamp

logger = logging.getLogger(__name__)


class VersioningError(Exception):
    """Base exception for versioning operations."""
    pass


class VersionNotFoundError(VersioningError):
    """Raised when version is not found."""
    pass


class VersionLimitExceededError(VersioningError):
    """Raised when version limit is exceeded."""
    pass


class VersionRestoreError(VersioningError):
    """Raised when version restore fails."""
    pass


class VersionManager:
    """Version control manager for skill files.

    Provides Git-like version control for files stored in MinIO,
    including version creation, listing, restoration, and cleanup.
    """

    def __init__(
        self,
        minio_client: MinIOClient,
        storage_manager,
        database_session: Session,
        max_versions: int = 10,
        cleanup_threshold_days: int = 90,
    ):
        """Initialize version manager.

        Args:
            minio_client: MinIO client instance
            storage_manager: SkillStorageManager instance
            database_session: SQLAlchemy database session
            max_versions: Maximum number of versions per file
            cleanup_threshold_days: Days after which old versions are cleaned up
        """
        self.minio_client = minio_client
        self.storage_manager = storage_manager
        self.db = database_session
        self.max_versions = max_versions
        self.cleanup_threshold_days = cleanup_threshold_days

        # Version storage configuration
        self.versions_bucket = "skillseekers-versions"
        self.versions_prefix = "versions"

    async def create_version(
        self,
        request: FileVersionCreateRequest,
        file_data: Union[bytes, BinaryIO],
    ) -> str:
        """Create a new version of a file.

        Args:
            request: Version creation request
            file_data: File data for the new version

        Returns:
            Version ID

        Raises:
            VersionNotFoundError: If source file doesn't exist
            VersionLimitExceededError: If version limit exceeded
        """
        skill_id = validate_skill_id(request.skill_id)
        file_path = validate_file_path(request.file_path)

        # Get source file
        source_file = await self._get_source_file(skill_id, file_path)
        if not source_file:
            raise VersionNotFoundError(f"Source file not found: {file_path}")

        # Calculate file size and checksum
        if isinstance(file_data, bytes):
            file_size = len(file_data)
            checksum = calculate_sha256(file_data)
        else:
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)
            checksum = calculate_sha256(file_data)

        # Get next version number
        version_number = await self._get_next_version_number(source_file.id)

        # Check version limit
        if version_number > self.max_versions:
            # Clean up oldest versions
            await self._cleanup_old_versions(source_file.id)

            # Re-check version number after cleanup
            version_number = await self._get_next_version_number(source_file.id)
            if version_number > self.max_versions:
                raise VersionLimitExceededError(
                    f"Version limit exceeded for file {file_path}. "
                    f"Maximum {self.max_versions} versions allowed."
                )

        # Generate version ID
        version_id = FileVersion.generate_version_id()

        # Generate version object name
        version_object_name = self._generate_version_object_name(
            source_file.id, file_path, version_id
        )

        try:
            # Upload version to MinIO
            with self.minio_client.operation_context(f"create_version_{file_path}"):
                result = self.minio_client.put_object(
                    bucket_name=self.versions_bucket,
                    object_name=version_object_name,
                    data=file_data,
                    length=file_size,
                    content_type=source_file.content_type,
                    metadata=request.metadata or {},
                )

            # Create version record in database
            file_version = FileVersion(
                file_id=source_file.id,
                version_id=version_id,
                version_number=version_number,
                object_name=result["object_name"],
                file_size=file_size,
                checksum=checksum,
                comment=request.comment or f"Version {version_number}",
                metadata=request.metadata or {},
                created_by="system",  # TODO: Get from context
            )

            self.db.add(file_version)
            self.db.commit()

            # Update source file metadata
            source_file.file_size = file_size
            source_file.checksum = checksum
            source_file.updated_at = datetime.utcnow()
            self.db.commit()

            logger.info(
                f"Created version {version_number} for file {file_path}: "
                f"{format_file_size(file_size)}"
            )

            return version_id

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create version for {file_path}: {e}")
            raise VersioningError(f"Version creation failed: {e}")

    async def list_versions(
        self,
        skill_id: UUID,
        file_path: str,
    ) -> List[FileVersionInfo]:
        """List all versions of a file.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            List of file version information

        Raises:
            VersionNotFoundError: If file doesn't exist
        """
        skill_id = validate_skill_id(skill_id)
        file_path = validate_file_path(file_path)

        # Get source file
        source_file = await self._get_source_file(skill_id, file_path)
        if not source_file:
            raise VersionNotFoundError(f"File not found: {file_path}")

        # Get all versions
        versions = (
            self.db.query(FileVersion)
            .filter(FileVersion.file_id == source_file.id)
            .order_by(desc(FileVersion.version_number))
            .all()
        )

        # Convert to response format
        version_infos = [
            FileVersionInfo(
                id=version.id,
                version_id=version.version_id,
                version_number=version.version_number,
                file_size=version.file_size,
                checksum=version.checksum,
                comment=version.comment,
                created_at=version.created_at,
                created_by=version.created_by,
                is_latest=version.is_latest,
            )
            for version in versions
        ]

        logger.debug(
            f"Listed {len(version_infos)} versions for file {file_path}"
        )

        return version_infos

    async def restore_version(
        self,
        request: FileVersionRestoreRequest,
    ) -> bool:
        """Restore file to a specific version.

        Args:
            request: Version restore request

        Returns:
            True if restore successful

        Raises:
            VersionNotFoundError: If file or version doesn't exist
        """
        skill_id = validate_skill_id(request.skill_id)
        file_path = validate_file_path(request.file_path)

        # Get source file
        source_file = await self._get_source_file(skill_id, file_path)
        if not source_file:
            raise VersionNotFoundError(f"File not found: {file_path}")

        # Get specific version
        version = await self._get_version(source_file.id, request.version_id)
        if not version:
            raise VersionNotFoundError(f"Version not found: {request.version_id}")

        try:
            # Download version from MinIO
            with self.minio_client.operation_context(f"restore_version_{file_path}"):
                version_response = self.minio_client.get_object(
                    bucket_name=self.versions_bucket,
                    object_name=version.object_name,
                )

            # Upload to current file location
            version_response.seek(0)  # Reset to beginning
            await self.storage_manager.upload_file(
                FileUploadRequest(
                    skill_id=skill_id,
                    file_path=file_path,
                    content_type=source_file.content_type,
                ),
                version_response,
            )

            logger.info(
                f"Restored file {file_path} to version {version.version_number}"
            )

            return True

        except Exception as e:
            logger.error(f"Failed to restore version {request.version_id}: {e}")
            raise VersionRestoreError(f"Version restore failed: {e}")

    async def compare_versions(
        self,
        skill_id: UUID,
        file_path: str,
        version_id_1: str,
        version_id_2: str,
    ) -> Dict[str, Any]:
        """Compare two versions of a file.

        Args:
            skill_id: Skill ID
            file_path: File path
            version_id_1: First version ID
            version_id_2: Second version ID

        Returns:
            Dictionary with comparison results

        Raises:
            VersionNotFoundError: If file or versions don't exist
        """
        skill_id = validate_skill_id(skill_id)
        file_path = validate_file_path(file_path)

        # Get source file
        source_file = await self._get_source_file(skill_id, file_path)
        if not source_file:
            raise VersionNotFoundError(f"File not found: {file_path}")

        # Get both versions
        version1 = await self._get_version(source_file.id, version_id_1)
        version2 = await self._get_version(source_file.id, version_id_2)

        if not version1:
            raise VersionNotFoundError(f"Version not found: {version_id_1}")

        if not version2:
            raise VersionNotFoundError(f"Version not found: {version_id_2}")

        # Download and compare
        try:
            with self.minio_client.operation_context(f"compare_versions_{file_path}"):
                # Get version 1
                response1 = self.minio_client.get_object(
                    bucket_name=self.versions_bucket,
                    object_name=version1.object_name,
                )
                data1 = response1.read()

                # Get version 2
                response2 = self.minio_client.get_object(
                    bucket_name=self.versions_bucket,
                    object_name=version2.object_name,
                )
                data2 = response2.read()

            # Perform comparison
            size_diff = len(data2) - len(data1)
            checksum_diff = version2.checksum != version1.checksum

            comparison_result = {
                "file_path": file_path,
                "version_1": {
                    "version_id": version1.version_id,
                    "version_number": version1.version_number,
                    "size": version1.file_size,
                    "checksum": version1.checksum,
                    "created_at": version1.created_at.isoformat(),
                    "comment": version1.comment,
                },
                "version_2": {
                    "version_id": version2.version_id,
                    "version_number": version2.version_number,
                    "size": version2.file_size,
                    "checksum": version2.checksum,
                    "created_at": version2.created_at.isoformat(),
                    "comment": version2.comment,
                },
                "differences": {
                    "size_difference": size_diff,
                    "checksum_different": checksum_diff,
                    "size_change_percentage": (
                        (size_diff / version1.file_size * 100) if version1.file_size > 0 else 0
                    ),
                },
                "comparison_timestamp": datetime.utcnow().isoformat(),
            }

            logger.debug(
                f"Compared versions {version_id_1} and {version_id_2} for {file_path}"
            )

            return comparison_result

        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            raise VersioningError(f"Version comparison failed: {e}")

    async def delete_version(
        self,
        skill_id: UUID,
        file_path: str,
        version_id: str,
    ) -> bool:
        """Delete a specific version.

        Args:
            skill_id: Skill ID
            file_path: File path
            version_id: Version ID to delete

        Returns:
            True if delete successful

        Raises:
            VersionNotFoundError: If file or version doesn't exist
        """
        skill_id = validate_skill_id(skill_id)
        file_path = validate_file_path(file_path)

        # Get source file
        source_file = await self._get_source_file(skill_id, file_path)
        if not source_file:
            raise VersionNotFoundError(f"File not found: {file_path}")

        # Get specific version
        version = await self._get_version(source_file.id, version_id)
        if not version:
            raise VersionNotFoundError(f"Version not found: {version_id}")

        # Check if it's the only version
        version_count = (
            self.db.query(func.count(FileVersion.id))
            .filter(FileVersion.file_id == source_file.id)
            .scalar()
        )

        if version_count <= 1:
            raise VersioningError(
                "Cannot delete the only version of a file"
            )

        try:
            # Delete from MinIO
            with self.minio_client.operation_context(f"delete_version_{file_path}"):
                self.minio_client.remove_object(
                    bucket_name=self.versions_bucket,
                    object_name=version.object_name,
                )

            # Delete from database
            self.db.delete(version)
            self.db.commit()

            logger.info(
                f"Deleted version {version_id} for file {file_path}"
            )

            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete version {version_id}: {e}")
            raise VersioningError(f"Version deletion failed: {e}")

    async def cleanup_old_versions(self, skill_id: Optional[UUID] = None) -> int:
        """Clean up old versions based on retention policy.

        Args:
            skill_id: Optional skill ID to filter cleanup

        Returns:
            Number of versions cleaned up

        Raises:
            VersioningError: If cleanup fails
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.cleanup_threshold_days)

            # Build query
            query = self.db.query(FileVersion).filter(
                FileVersion.created_at < cutoff_date
            )

            # Filter by skill if specified
            if skill_id:
                query = query.join(SkillFile).filter(
                    SkillFile.skill_id == skill_id
                )

            # Get versions to clean up (keep latest 3 per file)
            versions_to_cleanup = []
            file_version_counts = {}

            # First pass: count versions per file
            for version in query.all():
                file_id = version.file_id
                file_version_counts[file_id] = file_version_counts.get(file_id, 0) + 1

            # Second pass: identify versions to delete
            for version in query.all():
                file_id = version.file_id
                versions_to_delete = file_version_counts[file_id] - 3

                if versions_to_delete > 0:
                    # Only keep latest versions, delete the rest
                    if not version.is_latest:
                        versions_to_cleanup.append(version)
                        file_version_counts[file_id] -= 1

            deleted_count = 0

            # Delete versions
            for version in versions_to_cleanup[:100]:  # Limit batch size
                try:
                    # Delete from MinIO
                    self.minio_client.remove_object(
                        bucket_name=self.versions_bucket,
                        object_name=version.object_name,
                    )

                    # Delete from database
                    self.db.delete(version)
                    deleted_count += 1

                except Exception as e:
                    logger.warning(f"Failed to delete version {version.version_id}: {e}")

            self.db.commit()

            logger.info(
                f"Cleaned up {deleted_count} old versions"
            )

            return deleted_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Version cleanup failed: {e}")
            raise VersioningError(f"Version cleanup failed: {e}")

    async def get_version_statistics(self, skill_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get version control statistics.

        Args:
            skill_id: Optional skill ID to filter statistics

        Returns:
            Dictionary with version statistics
        """
        # Build query
        query = self.db.query(FileVersion)

        # Filter by skill if specified
        if skill_id:
            query = query.join(SkillFile).filter(
                SkillFile.skill_id == skill_id
            )

        # Get total versions
        total_versions = query.count()

        # Get versions by age
        now = datetime.utcnow()
        versions_last_7_days = query.filter(
            FileVersion.created_at >= now - timedelta(days=7)
        ).count()

        versions_last_30_days = query.filter(
            FileVersion.created_at >= now - timedelta(days=30)
        ).count()

        # Get average versions per file
        avg_versions_per_file = 0
        if skill_id:
            # Count files for this skill
            file_count = (
                self.db.query(func.count(SkillFile.id))
                .filter(SkillFile.skill_id == skill_id)
                .scalar()
            )
            if file_count > 0:
                avg_versions_per_file = total_versions / file_count

        # Get storage usage
        total_size = query.with_entities(
            func.sum(FileVersion.file_size)
        ).scalar() or 0

        # Get version count distribution
        version_counts = (
            self.db.query(
                FileVersion.file_id,
                func.count(FileVersion.id).label('version_count')
            )
            .group_by(FileVersion.file_id)
            .all()
        )

        version_distribution = {
            "1": 0, "2-5": 0, "6-10": 0, "10+": 0
        }

        for _, count in version_counts:
            if count == 1:
                version_distribution["1"] += 1
            elif count <= 5:
                version_distribution["2-5"] += 1
            elif count <= 10:
                version_distribution["6-10"] += 1
            else:
                version_distribution["10+"] += 1

        return {
            "total_versions": total_versions,
            "versions_last_7_days": versions_last_7_days,
            "versions_last_30_days": versions_last_30_days,
            "avg_versions_per_file": round(avg_versions_per_file, 2),
            "total_storage_used": total_size,
            "total_storage_human": format_file_size(total_size),
            "version_distribution": version_distribution,
            "cleanup_threshold_days": self.cleanup_threshold_days,
            "max_versions_per_file": self.max_versions,
        }

    # Private helper methods

    async def _get_source_file(self, skill_id: UUID, file_path: str) -> Optional[SkillFile]:
        """Get source file from database.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            SkillFile instance or None
        """
        try:
            return (
                self.db.query(SkillFile)
                .filter(
                    and_(
                        SkillFile.skill_id == skill_id,
                        SkillFile.file_path == file_path,
                    )
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting source file: {e}")
            return None

    async def _get_version(self, file_id: UUID, version_id: str) -> Optional[FileVersion]:
        """Get version from database.

        Args:
            file_id: File ID
            version_id: Version ID

        Returns:
            FileVersion instance or None
        """
        try:
            return (
                self.db.query(FileVersion)
                .filter(
                    and_(
                        FileVersion.file_id == file_id,
                        FileVersion.version_id == version_id,
                    )
                )
                .first()
            )
        except SQLAlchemyError as e:
            logger.error(f"Database error getting version: {e}")
            return None

    async def _get_next_version_number(self, file_id: UUID) -> int:
        """Get next version number for a file.

        Args:
            file_id: File ID

        Returns:
            Next version number
        """
        try:
            result = (
                self.db.query(func.max(FileVersion.version_number))
                .filter(FileVersion.file_id == file_id)
                .scalar()
            )

            return (result or 0) + 1
        except SQLAlchemyError as e:
            logger.error(f"Database error getting version number: {e}")
            return 1

    def _generate_version_object_name(
        self,
        file_id: UUID,
        file_path: str,
        version_id: str,
    ) -> str:
        """Generate object name for version storage.

        Args:
            file_id: File ID
            file_path: Original file path
            version_id: Version ID

        Returns:
            Object name for MinIO
        """
        # Sanitize file path
        safe_path = file_path.replace("/", "_").replace("\\", "_")
        return f"{self.versions_prefix}/{file_id}/{safe_path}/{version_id}"

    async def _cleanup_old_versions(self, file_id: UUID) -> int:
        """Clean up oldest versions for a file.

        Args:
            file_id: File ID

        Returns:
            Number of versions cleaned up
        """
        try:
            # Get all versions ordered by version number
            versions = (
                self.db.query(FileVersion)
                .filter(FileVersion.file_id == file_id)
                .order_by(desc(FileVersion.version_number))
                .all()
            )

            # Delete versions beyond max limit (keep latest ones)
            versions_to_delete = versions[self.max_versions:]

            deleted_count = 0
            for version in versions_to_delete:
                try:
                    # Delete from MinIO
                    self.minio_client.remove_object(
                        bucket_name=self.versions_bucket,
                        object_name=version.object_name,
                    )

                    # Delete from database
                    self.db.delete(version)
                    deleted_count += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup version {version.version_id}: {e}"
                    )

            self.db.commit()

            if deleted_count > 0:
                logger.debug(f"Cleaned up {deleted_count} old versions for file {file_id}")

            return deleted_count

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to cleanup old versions: {e}")
            return 0

    @asynccontextmanager
    async def versioning_operation(self, operation_name: str):
        """Context manager for versioning operations.

        Args:
            operation_name: Name of operation
        """
        logger.debug(f"Starting versioning operation: {operation_name}")
        start_time = time.time()

        try:
            yield
            duration = time.time() - start_time
            logger.debug(
                f"Versioning operation '{operation_name}' completed in {duration:.3f}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Versioning operation '{operation_name}' failed after {duration:.3f}s: {e}"
            )
            raise
