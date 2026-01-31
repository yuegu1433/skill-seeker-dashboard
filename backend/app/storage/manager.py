"""SkillStorageManager - Core storage management for MinIO.

This module provides the SkillStorageManager class which serves as the main
interface for all storage operations in the MinIO storage system.
"""

import asyncio
import io
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .client import MinIOClient, MinIOClientManager
from .models import Skill, SkillFile, StorageBucket, FileVersion
from .schemas.file_operations import (
    FileUploadRequest,
    FileUploadResult,
    FileDownloadRequest,
    FileDownloadResult,
    FileInfo,
    FileDeleteRequest,
    FileDeleteResult,
    FileListRequest,
    FileListResult,
    FileMoveRequest,
    FileMoveResult,
)
from .schemas.storage_config import StorageConfig
from .utils.checksum import calculate_sha256, verify_checksum
from .utils.validators import (
    validate_file_path,
    validate_skill_id,
    validate_bucket_name,
    validate_metadata,
    validate_tags,
    sanitize_filename,
    validate_object_name,
)
from .utils.formatters import format_file_size, format_timestamp

logger = logging.getLogger(__name__)


class SkillStorageError(Exception):
    """Base exception for storage operations."""
    pass


class FileNotFoundError(SkillStorageError):
    """Raised when file is not found."""
    pass


class SkillNotFoundError(SkillStorageError):
    """Raised when skill is not found."""
    pass


class StorageQuotaExceededError(SkillStorageError):
    """Raised when storage quota is exceeded."""
    pass


class SkillStorageManager:
    """Core storage manager for skill files in MinIO.

    Provides a unified interface for all storage operations including
    file upload, download, deletion, versioning, and metadata management.
    """

    def __init__(
        self,
        minio_client: MinIOClient,
        database_session: Session,
        config: StorageConfig,
    ):
        """Initialize storage manager.

        Args:
            minio_client: MinIO client instance
            database_session: SQLAlchemy database session
            config: Storage configuration
        """
        self.minio_client = minio_client
        self.db = database_session
        self.config = config

        # Storage statistics
        self._total_files = 0
        self._total_size = 0

    async def upload_file(
        self,
        request: FileUploadRequest,
        file_data: Union[bytes, BinaryIO],
    ) -> FileUploadResult:
        """Upload a file to MinIO storage.

        Args:
            request: File upload request
            file_data: File data to upload

        Returns:
            FileUploadResult with upload details

        Raises:
            SkillNotFoundError: If skill doesn't exist
            StorageQuotaExceededError: If storage quota exceeded
        """
        # Validate request
        skill_id = validate_skill_id(request.skill_id)
        file_path = validate_file_path(request.file_path)
        metadata = validate_metadata(request.metadata)
        tags = validate_tags(request.tags)

        # Check if skill exists
        skill = await self._get_skill(skill_id)
        if not skill:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")

        # Check storage quota
        await self._check_storage_quota(skill_id, file_data)

        # Calculate file size and checksum
        if isinstance(file_data, bytes):
            file_size = len(file_data)
            checksum = calculate_sha256(file_data)
        else:
            # File-like object
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Reset to beginning
            checksum = calculate_sha256(file_data)

        # Generate object name
        object_name = self._generate_object_name(skill_id, file_path)

        # Upload to MinIO
        try:
            with self.minio_client.operation_context(f"upload_{file_path}"):
                result = self.minio_client.put_object(
                    bucket_name=self.config.default_bucket,
                    object_name=object_name,
                    data=file_data,
                    length=file_size,
                    content_type=request.content_type,
                    metadata=metadata,
                )

            # Create file record in database
            skill_file = SkillFile(
                skill_id=skill_id,
                object_name=result["object_name"],
                file_path=file_path,
                file_type=self._determine_file_type(file_path),
                file_size=file_size,
                content_type=request.content_type,
                checksum=checksum,
                metadata=metadata,
                tags=tags,
                is_public=request.is_public,
            )

            self.db.add(skill_file)
            self.db.commit()

            # Update skill statistics
            await self._update_skill_stats(skill_id, file_size)

            logger.info(
                f"Uploaded file {file_path} for skill {skill_id}: "
                f"{format_file_size(file_size)}"
            )

            return FileUploadResult(
                success=True,
                object_name=result["object_name"],
                file_path=file_path,
                file_size=file_size,
                checksum=checksum,
                upload_url=None,
                error=None,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise SkillStorageError(f"Upload failed: {e}")

    async def download_file(
        self,
        request: FileDownloadRequest,
    ) -> FileDownloadResult:
        """Download a file from MinIO storage.

        Args:
            request: File download request

        Returns:
            FileDownloadResult with download details

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        skill_id = validate_skill_id(request.skill_id)
        file_path = validate_file_path(request.file_path)

        # Get file record from database
        skill_file = await self._get_file(skill_id, file_path)
        if not skill_file:
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get download URL
        try:
            with self.minio_client.operation_context(f"download_{file_path}"):
                download_url = self.minio_client.presigned_get_object(
                    bucket_name=self.config.default_bucket,
                    object_name=skill_file.object_name,
                    expires=3600,  # 1 hour
                )

            # Update access time
            await self._update_access_time(skill_file.id)

            logger.debug(f"Generated download URL for {file_path}")

            return FileDownloadResult(
                success=True,
                file_path=file_path,
                file_size=skill_file.file_size,
                content_type=skill_file.content_type,
                checksum=skill_file.checksum,
                download_url=download_url,
                expires_at=datetime.utcnow() + timedelta(hours=1),
                error=None,
            )

        except Exception as e:
            logger.error(f"Failed to download file {file_path}: {e}")
            raise SkillStorageError(f"Download failed: {e}")

    async def delete_file(
        self,
        request: FileDeleteRequest,
    ) -> FileDeleteResult:
        """Delete a file from MinIO storage.

        Args:
            request: File delete request

        Returns:
            FileDeleteResult with deletion details

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        skill_id = validate_skill_id(request.skill_id)
        file_path = validate_file_path(request.file_path)

        # Get file record from database
        skill_file = await self._get_file(skill_id, file_path)
        if not skill_file:
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Delete from MinIO
            with self.minio_client.operation_context(f"delete_{file_path}"):
                self.minio_client.remove_object(
                    bucket_name=self.config.default_bucket,
                    object_name=skill_file.object_name,
                )

            # Delete from database
            self.db.delete(skill_file)
            self.db.commit()

            # Update skill statistics
            await self._update_skill_stats(skill_id, -skill_file.file_size)

            logger.info(f"Deleted file {file_path} for skill {skill_id}")

            return FileDeleteResult(
                success=True,
                file_path=file_path,
                version_id=None,
                error=None,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete file {file_path}: {e}")
            raise SkillStorageError(f"Deletion failed: {e}")

    async def list_files(
        self,
        request: FileListRequest,
    ) -> FileListResult:
        """List files for a skill.

        Args:
            request: File list request

        Returns:
            FileListResult with file list

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill_id = validate_skill_id(request.skill_id)

        # Check if skill exists
        skill = await self._get_skill(skill_id)
        if not skill:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")

        # Build query
        query = self.db.query(SkillFile).filter(SkillFile.skill_id == skill_id)

        if request.prefix:
            query = query.filter(SkillFile.file_path.startswith(request.prefix))

        if request.file_type:
            query = query.filter(SkillFile.file_type == request.file_type)

        if request.is_public is not None:
            query = query.filter(SkillFile.is_public == request.is_public)

        # Get total count
        total = query.count()

        # Apply pagination
        query = query.order_by(SkillFile.created_at.desc())
        query = query.limit(request.limit).offset(request.offset)

        # Execute query
        files = query.all()

        # Convert to response format
        file_infos = [
            FileInfo(
                id=file.id,
                skill_id=file.skill_id,
                object_name=file.object_name,
                file_path=file.file_path,
                file_type=file.file_type,
                file_size=file.file_size,
                content_type=file.content_type,
                checksum=file.checksum,
                metadata=file.metadata or {},
                tags=file.tags or [],
                is_public=file.is_public,
                version_count=len(file.versions) if file.versions else 0,
                created_at=file.created_at,
                updated_at=file.updated_at,
                last_accessed_at=file.last_accessed_at,
            )
            for file in files
        ]

        has_more = total > request.offset + request.limit

        logger.debug(
            f"Listed {len(file_infos)} files for skill {skill_id} "
            f"(total: {total}, has_more: {has_more})"
        )

        return FileListResult(
            files=file_infos,
            total=total,
            has_more=has_more,
            limit=request.limit,
            offset=request.offset,
        )

    async def move_file(
        self,
        request: FileMoveRequest,
    ) -> FileMoveResult:
        """Move/rename a file.

        Args:
            request: File move request

        Returns:
            FileMoveResult with move details

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        skill_id = validate_skill_id(request.skill_id)
        source_path = validate_file_path(request.source_path)
        target_path = validate_file_path(request.target_path)

        # Get source file
        skill_file = await self._get_file(skill_id, source_path)
        if not skill_file:
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Check if target already exists
        existing_file = await self._get_file(skill_id, target_path)
        if existing_file:
            raise SkillStorageError(f"Target file already exists: {target_path}")

        # Generate new object name
        new_object_name = self._generate_object_name(skill_id, target_path)

        try:
            # Copy to new location in MinIO
            with self.minio_client.operation_context(f"move_{source_path}_to_{target_path}"):
                self.minio_client.copy_object(
                    bucket_name=self.config.default_bucket,
                    object_name=new_object_name,
                    source=CopySource(
                        bucket_name=self.config.default_bucket,
                        object_name=skill_file.object_name,
                    ),
                )

                # Remove old object
                self.minio_client.remove_object(
                    bucket_name=self.config.default_bucket,
                    object_name=skill_file.object_name,
                )

            # Update database record
            skill_file.file_path = target_path
            skill_file.object_name = new_object_name
            skill_file.updated_at = datetime.utcnow()

            self.db.commit()

            logger.info(
                f"Moved file {source_path} to {target_path} for skill {skill_id}"
            )

            return FileMoveResult(
                success=True,
                source_path=source_path,
                target_path=target_path,
                new_object_name=new_object_name,
                error=None,
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to move file {source_path} to {target_path}: {e}")
            raise SkillStorageError(f"Move failed: {e}")

    async def get_file_info(
        self,
        skill_id: UUID,
        file_path: str,
    ) -> FileInfo:
        """Get detailed file information.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            FileInfo with file details

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        skill_file = await self._get_file(skill_id, file_path)
        if not skill_file:
            raise FileNotFoundError(f"File not found: {file_path}")

        return FileInfo(
            id=skill_file.id,
            skill_id=skill_file.skill_id,
            object_name=skill_file.object_name,
            file_path=skill_file.file_path,
            file_type=skill_file.file_type,
            file_size=skill_file.file_size,
            content_type=skill_file.content_type,
            checksum=skill_file.checksum,
            metadata=skill_file.metadata or {},
            tags=skill_file.tags or [],
            is_public=skill_file.is_public,
            version_count=len(skill_file.versions) if skill_file.versions else 0,
            created_at=skill_file.created_at,
            updated_at=skill_file.updated_at,
            last_accessed_at=skill_file.last_accessed_at,
        )

    async def get_skill_stats(self, skill_id: UUID) -> Dict[str, Any]:
        """Get storage statistics for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Dictionary with statistics

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = await self._get_skill(skill_id)
        if not skill:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")

        # Get file count and size
        result = (
            self.db.query(func.count(SkillFile.id), func.sum(SkillFile.file_size))
            .filter(SkillFile.skill_id == skill_id)
            .one()
        )

        file_count = result[0] or 0
        total_size = result[1] or 0

        # Get file type breakdown
        type_breakdown = (
            self.db.query(
                SkillFile.file_type,
                func.count(SkillFile.id),
                func.sum(SkillFile.file_size),
            )
            .filter(SkillFile.skill_id == skill_id)
            .group_by(SkillFile.file_type)
            .all()
        )

        file_types = {
            row[0]: {"count": row[1], "size": row[2] or 0}
            for row in type_breakdown
        }

        return {
            "skill_id": skill_id,
            "file_count": file_count,
            "total_size": total_size,
            "total_size_human": format_file_size(total_size),
            "file_types": file_types,
            "last_updated": skill.updated_at.isoformat() if skill.updated_at else None,
        }

    async def verify_file_integrity(self, skill_id: UUID, file_path: str) -> bool:
        """Verify file integrity using checksum.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            True if file is intact, False otherwise

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        skill_file = await self._get_file(skill_id, file_path)
        if not skill_file:
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            # Get file from MinIO
            response = self.minio_client.get_object(
                bucket_name=self.config.default_bucket,
                object_name=skill_file.object_name,
            )

            # Calculate checksum
            calculated_checksum = calculate_sha256(response)

            # Verify against stored checksum
            is_valid = verify_checksum(
                calculated_checksum,
                skill_file.checksum,
                algorithm="sha256",
            )

            logger.debug(
                f"File integrity check for {file_path}: "
                f"{'valid' if is_valid else 'invalid'}"
            )

            return is_valid

        except Exception as e:
            logger.error(f"Integrity check failed for {file_path}: {e}")
            return False

    async def ensure_skill_storage(self, skill_id: UUID) -> bool:
        """Ensure storage is ready for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            True if storage is ready

        Raises:
            SkillNotFoundError: If skill doesn't exist
        """
        skill = await self._get_skill(skill_id)
        if not skill:
            raise SkillNotFoundError(f"Skill not found: {skill_id}")

        # Ensure bucket exists
        if not self.minio_client.bucket_exists(self.config.default_bucket):
            self.minio_client.create_bucket(self.config.default_bucket)

        logger.debug(f"Storage ensured for skill {skill_id}")
        return True

    # Private helper methods

    async def _get_skill(self, skill_id: UUID) -> Optional[Skill]:
        """Get skill from database.

        Args:
            skill_id: Skill ID

        Returns:
            Skill instance or None
        """
        try:
            return self.db.query(Skill).filter(Skill.id == skill_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error getting skill {skill_id}: {e}")
            return None

    async def _get_file(self, skill_id: UUID, file_path: str) -> Optional[SkillFile]:
        """Get file from database.

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
            logger.error(f"Database error getting file {file_path}: {e}")
            return None

    def _generate_object_name(self, skill_id: UUID, file_path: str) -> str:
        """Generate MinIO object name.

        Args:
            skill_id: Skill ID
            file_path: File path

        Returns:
            Object name
        """
        # Create a unique object name based on skill ID and file path
        safe_path = sanitize_filename(file_path)
        timestamp = int(time.time())
        unique_id = str(uuid4())[:8]
        return f"skills/{skill_id}/{timestamp}_{unique_id}_{safe_path}"

    def _determine_file_type(self, file_path: str) -> str:
        """Determine file type from path.

        Args:
            file_path: File path

        Returns:
            File type string
        """
        path = Path(file_path)

        if path.name == "SKILL.md":
            return "skill_file"
        elif path.name in ("config.json", "metadata.json"):
            return "config"
        elif path.suffix in (".md", ".txt", ".rst"):
            return "reference"
        elif path.name in ("creation.log", "enhancement.log"):
            return "log"
        else:
            return "other"

    async def _check_storage_quota(self, skill_id: UUID, file_data: Union[bytes, BinaryIO]) -> None:
        """Check if storage quota allows the upload.

        Args:
            skill_id: Skill ID
            file_data: File data to check

        Raises:
            StorageQuotaExceededError: If quota exceeded
        """
        # Calculate file size
        if isinstance(file_data, bytes):
            file_size = len(file_data)
        else:
            file_data.seek(0, 2)
            file_size = file_data.tell()
            file_data.seek(0)

        # Get current usage
        stats = await self.get_skill_stats(skill_id)
        current_size = stats["total_size"]

        # Check against configured quota (implement quota logic here)
        # For now, just check against overall storage limits
        MAX_SKILL_SIZE = 1024 * 1024 * 1024  # 1GB per skill

        if current_size + file_size > MAX_SKILL_SIZE:
            raise StorageQuotaExceededError(
                f"Storage quota exceeded for skill {skill_id}. "
                f"Current: {format_file_size(current_size)}, "
                f"Adding: {format_file_size(file_size)}, "
                f"Max: {format_file_size(MAX_SKILL_SIZE)}"
            )

    async def _update_skill_stats(self, skill_id: UUID, size_delta: int) -> None:
        """Update skill storage statistics.

        Args:
            skill_id: Skill ID
            size_delta: Size change (positive or negative)
        """
        try:
            skill = await self._get_skill(skill_id)
            if skill:
                skill.total_size_bytes += size_delta
                skill.file_count = skill.files.count() if skill.files else 0
                skill.updated_at = datetime.utcnow()
                self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to update skill stats for {skill_id}: {e}")
            self.db.rollback()

    async def _update_access_time(self, file_id: UUID) -> None:
        """Update file last accessed time.

        Args:
            file_id: File ID
        """
        try:
            skill_file = self.db.query(SkillFile).filter(SkillFile.id == file_id).first()
            if skill_file:
                skill_file.last_accessed_at = datetime.utcnow()
                self.db.commit()
        except SQLAlchemyError as e:
            logger.error(f"Failed to update access time for file {file_id}: {e}")
            self.db.rollback()

    @asynccontextmanager
    async def storage_operation(self, operation_name: str):
        """Context manager for storage operations.

        Args:
            operation_name: Name of operation
        """
        logger.debug(f"Starting storage operation: {operation_name}")
        start_time = time.time()

        try:
            yield
            duration = time.time() - start_time
            logger.debug(
                f"Storage operation '{operation_name}' completed in {duration:.3f}s"
            )
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Storage operation '{operation_name}' failed after {duration:.3f}s: {e}"
            )
            raise
