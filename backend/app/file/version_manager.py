"""Version Manager.

This module contains the VersionManager class which provides comprehensive
file version control capabilities including version creation, query, restore,
compare, and metadata management.
"""

import asyncio
import logging
import hashlib
import difflib
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, text
from sqlalchemy.orm import selectinload

# Import models and schemas
from app.file.models.file import File
from app.file.models.file_version import FileVersion, VersionStatus
from app.file.schemas.file_operations import FileResponse

logger = logging.getLogger(__name__)


class VersionSortBy(Enum):
    """Version sort options."""
    CREATED_AT = "created_at"
    VERSION_NUMBER = "version_number"
    AUTHOR = "author_name"
    SIZE = "size"
    STATUS = "status"


class VersionFilter:
    """Version filter criteria."""

    def __init__(
        self,
        status: Optional[VersionStatus] = None,
        author_id: Optional[str] = None,
        author_name: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        size_min: Optional[int] = None,
        size_max: Optional[int] = None,
        version_contains: Optional[str] = None,
        message_contains: Optional[str] = None,
        is_current: Optional[bool] = None,
    ):
        self.status = status
        self.author_id = author_id
        self.author_name = author_name
        self.date_from = date_from
        self.date_to = date_to
        self.size_min = size_min
        self.size_max = size_max
        self.version_contains = version_contains
        self.message_contains = message_contains
        self.is_current = is_current


class VersionCompareResult:
    """Version comparison result."""

    def __init__(
        self,
        from_version_id: str,
        to_version_id: str,
        content_diff: List[str],
        size_diff: int,
        metadata_diff: Dict[str, Any],
        stats: Dict[str, Any],
    ):
        self.from_version_id = from_version_id
        self.to_version_id = to_version_id
        self.content_diff = content_diff
        self.size_diff = size_diff
        self.metadata_diff = metadata_diff
        self.stats = stats


class VersionStatistics:
    """Version statistics."""

    def __init__(self, file_id: str):
        self.file_id = file_id
        self.total_versions = 0
        self.active_versions = 0
        self.archived_versions = 0
        self.total_size = 0
        self.average_size = 0
        self.oldest_version = None
        self.newest_version = None
        self.contributors = set()
        self.version_timeline = []


class VersionManager:
    """File version management system."""

    def __init__(self, db_session: AsyncSession):
        """Initialize version manager.

        Args:
            db_session: Database session
        """
        self.db = db_session

    async def create_version(
        self,
        file_id: UUID,
        author_id: str,
        author_name: str,
        content: Optional[str] = None,
        storage_key: Optional[str] = None,
        size: int = 0,
        mime_type: str = "text/plain",
        checksum: Optional[str] = None,
        message: str = "New version",
        version_tag: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FileVersion:
        """Create a new file version.

        Args:
            file_id: File ID
            author_id: Author user ID
            author_name: Author name
            content: File content (for text files)
            storage_key: Storage key in MinIO
            size: File size in bytes
            mime_type: MIME type
            checksum: File checksum
            message: Version message
            version_tag: Version tag (optional)
            metadata: Additional metadata

        Returns:
            Created FileVersion instance
        """
        try:
            # Get current version
            current_version = await self.get_current_version(file_id)

            # Calculate content hash if content is provided
            content_hash = None
            if content is not None:
                content_hash = hashlib.sha256(content.encode()).hexdigest()

                # Check if content has changed
                if current_version and current_version.content_hash == content_hash:
                    logger.info(f"Content unchanged, skipping version creation for file {file_id}")
                    return current_version

            # Determine next version number
            if current_version:
                next_version_number = current_version.version_number + 1
                parent_version_id = current_version.id

                # Calculate diff from previous version
                diff_from_previous = None
                if content is not None and current_version.content is not None:
                    diff_from_previous = self._generate_diff(
                        current_version.content, content
                    )
            else:
                next_version_number = 1
                parent_version_id = None
                diff_from_previous = None

            # Generate storage key if not provided
            if storage_key is None:
                storage_key = f"files/{file_id}/versions/{uuid4()}"

            # Create new version
            if current_version:
                version = FileVersion.create_new_version(
                    file_id=str(file_id),
                    parent_version_id=str(parent_version_id),
                    version_number=next_version_number,
                    author_id=author_id,
                    author_name=author_name,
                    storage_key=storage_key,
                    size=size,
                    mime_type=mime_type,
                    content=content,
                    checksum=checksum,
                    message=message,
                    version_tag=version_tag,
                )
            else:
                version = FileVersion.create_initial_version(
                    file_id=str(file_id),
                    author_id=author_id,
                    author_name=author_name,
                    storage_key=storage_key,
                    size=size,
                    mime_type=mime_type,
                    content=content,
                    checksum=checksum,
                    message=message,
                )

            # Add metadata
            if metadata:
                for key, value in metadata.items():
                    version.add_metadata(key, value)

            # Set diff
            if diff_from_previous:
                version.diff_from_previous = diff_from_previous

            # Add to database
            self.db.add(version)

            # Mark previous version as not current
            if current_version:
                current_version.unset_as_current()

            # Commit changes
            await self.db.commit()
            await self.db.refresh(version)

            logger.info(
                f"Created version {version.version} for file {file_id} by {author_name}"
            )
            return version

        except Exception as e:
            logger.error(f"Error creating version for file {file_id}: {str(e)}")
            await self.db.rollback()
            raise

    async def get_version(self, version_id: UUID) -> Optional[FileVersion]:
        """Get version by ID.

        Args:
            version_id: Version ID

        Returns:
            FileVersion instance or None if not found
        """
        try:
            result = await self.db.execute(
                select(FileVersion).where(FileVersion.id == version_id)
            )
            version = result.scalar_one_or_none()

            if version:
                version.increment_access_count()
                await self.db.commit()

            return version
        except Exception as e:
            logger.error(f"Error getting version {version_id}: {str(e)}")
            return None

    async def get_current_version(self, file_id: UUID) -> Optional[FileVersion]:
        """Get current version of a file.

        Args:
            file_id: File ID

        Returns:
            Current FileVersion or None if not found
        """
        try:
            result = await self.db.execute(
                select(FileVersion)
                .where(
                    and_(
                        FileVersion.file_id == file_id,
                        FileVersion.is_current == True,  # noqa: E712
                    )
                )
                .order_by(desc(FileVersion.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting current version for file {file_id}: {str(e)}")
            return None

    async def get_versions(
        self,
        file_id: UUID,
        filter: Optional[VersionFilter] = None,
        sort_by: VersionSortBy = VersionSortBy.CREATED_AT,
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[FileVersion], int]:
        """Get versions of a file.

        Args:
            file_id: File ID
            filter: Version filter criteria
            sort_by: Sort field
            sort_order: Sort order ("asc" or "desc")
            limit: Result limit
            offset: Result offset

        Returns:
            Tuple of (versions list, total count)
        """
        try:
            # Build base query
            query = select(FileVersion).where(FileVersion.file_id == file_id)

            # Apply filters
            if filter:
                if filter.status:
                    query = query.where(FileVersion.status == filter.status)

                if filter.author_id:
                    query = query.where(FileVersion.author_id == filter.author_id)

                if filter.author_name:
                    query = query.where(FileVersion.author_name.ilike(f"%{filter.author_name}%"))

                if filter.date_from:
                    query = query.where(FileVersion.created_at >= filter.date_from)

                if filter.date_to:
                    query = query.where(FileVersion.created_at <= filter.date_to)

                if filter.size_min is not None:
                    query = query.where(FileVersion.size >= filter.size_min)

                if filter.size_max is not None:
                    query = query.where(FileVersion.size <= filter.size_max)

                if filter.version_contains:
                    query = query.where(FileVersion.version.ilike(f"%{filter.version_contains}%"))

                if filter.message_contains:
                    query = query.where(FileVersion.message.ilike(f"%{filter.message_contains}%"))

                if filter.is_current is not None:
                    query = query.where(FileVersion.is_current == filter.is_current)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            count_result = await self.db.execute(count_query)
            total = count_result.scalar()

            # Apply sorting
            sort_field = {
                VersionSortBy.CREATED_AT: FileVersion.created_at,
                VersionSortBy.VERSION_NUMBER: FileVersion.version_number,
                VersionSortBy.AUTHOR: FileVersion.author_name,
                VersionSortBy.SIZE: FileVersion.size,
                VersionSortBy.STATUS: FileVersion.status,
            }[sort_by]

            if sort_order.lower() == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))

            # Apply pagination
            query = query.offset(offset).limit(limit)

            # Execute query
            result = await self.db.execute(query)
            versions = result.scalars().all()

            return versions, total

        except Exception as e:
            logger.error(f"Error getting versions for file {file_id}: {str(e)}")
            return [], 0

    async def restore_version(
        self,
        version_id: UUID,
        user_id: str,
        user_name: str,
        message: Optional[str] = None,
    ) -> FileVersion:
        """Restore a specific version as the current version.

        Args:
            version_id: Version ID to restore
            user_id: User ID
            user_name: User name
            message: Restore message

        Returns:
            Restored FileVersion instance
        """
        try:
            # Get version to restore
            version_to_restore = await self.get_version(version_id)
            if not version_to_restore:
                raise ValueError(f"Version {version_id} not found")

            # Get current version
            current_version = await self.get_current_version(version_to_restore.file_id)

            # Create restore message
            if message is None:
                message = f"Restored to version {version_to_restore.version}"

            # Create new version based on the restored version
            new_version = await self.create_version(
                file_id=version_to_restore.file_id,
                author_id=user_id,
                author_name=user_name,
                content=version_to_restore.content,
                storage_key=version_to_restore.storage_key,
                size=version_to_restore.size,
                mime_type=version_to_restore.mime_type,
                checksum=version_to_restore.checksum,
                message=message,
                metadata={
                    "restored_from_version_id": str(version_to_restore.id),
                    "restored_from_version": version_to_restore.version,
                },
            )

            logger.info(
                f"Restored version {version_to_restore.version} for file {version_to_restore.file_id}"
            )
            return new_version

        except Exception as e:
            logger.error(f"Error restoring version {version_id}: {str(e)}")
            raise

    async def compare_versions(
        self,
        from_version_id: UUID,
        to_version_id: UUID,
    ) -> VersionCompareResult:
        """Compare two file versions.

        Args:
            from_version_id: Source version ID
            to_version_id: Target version ID

        Returns:
            VersionCompareResult instance
        """
        try:
            # Get both versions
            from_version = await self.get_version(from_version_id)
            to_version = await self.get_version(to_version_id)

            if not from_version:
                raise ValueError(f"Source version {from_version_id} not found")
            if not to_version:
                raise ValueError(f"Target version {to_version_id} not found")

            # Generate content diff
            content_diff = []
            if from_version.content is not None and to_version.content is not None:
                from_lines = from_version.content.splitlines(keepends=True)
                to_lines = to_version.content.splitlines(keepends=True)
                content_diff = list(
                    difflib.unified_diff(
                        from_lines,
                        to_lines,
                        fromfile=f"version_{from_version.version}",
                        tofile=f"version_{to_version.version}",
                        lineterm="",
                    )
                )

            # Calculate size difference
            size_diff = to_version.size - from_version.size

            # Compare metadata
            metadata_diff = {}
            from_metadata = from_version.metadata or {}
            to_metadata = to_version.metadata or {}

            # Added metadata
            for key, value in to_metadata.items():
                if key not in from_metadata:
                    metadata_diff[f"added:{key}"] = value

            # Removed metadata
            for key, value in from_metadata.items():
                if key not in to_metadata:
                    metadata_diff[f"removed:{key}"] = value

            # Modified metadata
            for key in from_metadata.keys() & to_metadata.keys():
                if from_metadata[key] != to_metadata[key]:
                    metadata_diff[f"modified:{key}"] = {
                        "from": from_metadata[key],
                        "to": to_metadata[key],
                    }

            # Calculate statistics
            stats = {
                "lines_added": 0,
                "lines_removed": 0,
                "lines_changed": 0,
            }

            if content_diff:
                for line in content_diff:
                    if line.startswith("+") and not line.startswith("+++"):
                        stats["lines_added"] += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        stats["lines_removed"] += 1
                    elif line.startswith("@@"):
                        stats["lines_changed"] += 1

            return VersionCompareResult(
                from_version_id=str(from_version_id),
                to_version_id=str(to_version_id),
                content_diff=content_diff,
                size_diff=size_diff,
                metadata_diff=metadata_diff,
                stats=stats,
            )

        except Exception as e:
            logger.error(f"Error comparing versions {from_version_id} and {to_version_id}: {str(e)}")
            raise

    async def get_version_statistics(self, file_id: UUID) -> VersionStatistics:
        """Get version statistics for a file.

        Args:
            file_id: File ID

        Returns:
            VersionStatistics instance
        """
        try:
            stats = VersionStatistics(str(file_id))

            # Get all versions
            query = select(FileVersion).where(FileVersion.file_id == file_id)
            result = await self.db.execute(query)
            versions = result.scalars().all()

            if not versions:
                return stats

            # Calculate statistics
            stats.total_versions = len(versions)
            stats.total_size = sum(v.size for v in versions)
            stats.average_size = stats.total_size / stats.total_versions if stats.total_versions > 0 else 0

            # Count by status
            for version in versions:
                if version.status == VersionStatus.ACTIVE:
                    stats.active_versions += 1
                elif version.status == VersionStatus.ARCHIVED:
                    stats.archived_versions += 1

                # Track contributors
                if version.author_name:
                    stats.contributors.add(version.author_name)

                # Track timeline
                stats.version_timeline.append(
                    {
                        "version": version.version,
                        "created_at": version.created_at.isoformat(),
                        "author": version.author_name,
                        "message": version.message,
                    }
                )

            # Find oldest and newest
            versions.sort(key=lambda v: v.created_at)
            stats.oldest_version = versions[0]
            stats.newest_version = versions[-1]

            return stats

        except Exception as e:
            logger.error(f"Error getting version statistics for file {file_id}: {str(e)}")
            raise

    async def archive_version(self, version_id: UUID, user_id: str) -> bool:
        """Archive a version.

        Args:
            version_id: Version ID
            user_id: User ID performing the action

        Returns:
            True if successful
        """
        try:
            version = await self.get_version(version_id)
            if not version:
                return False

            version.archive()
            await self.db.commit()

            logger.info(f"Archived version {version_id} by {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error archiving version {version_id}: {str(e)}")
            return False

    async def lock_version(self, version_id: UUID, user_id: str) -> bool:
        """Lock a version.

        Args:
            version_id: Version ID
            user_id: User ID performing the action

        Returns:
            True if successful
        """
        try:
            version = await self.get_version(version_id)
            if not version:
                return False

            version.lock()
            await self.db.commit()

            logger.info(f"Locked version {version_id} by {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error locking version {version_id}: {str(e)}")
            return False

    async def unlock_version(self, version_id: UUID, user_id: str) -> bool:
        """Unlock a version.

        Args:
            version_id: Version ID
            user_id: User ID performing the action

        Returns:
            True if successful
        """
        try:
            version = await self.get_version(version_id)
            if not version:
                return False

            version.unlock()
            await self.db.commit()

            logger.info(f"Unlocked version {version_id} by {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error unlocking version {version_id}: {str(e)}")
            return False

    async def cleanup_old_versions(
        self,
        file_id: UUID,
        keep_count: int = 10,
        older_than_days: Optional[int] = None,
    ) -> int:
        """Clean up old versions.

        Args:
            file_id: File ID
            keep_count: Minimum number of versions to keep
            older_than_days: Remove versions older than this many days

        Returns:
            Number of versions cleaned up
        """
        try:
            # Get all versions sorted by creation date
            query = select(FileVersion).where(FileVersion.file_id == file_id)
            result = await self.db.execute(query)
            versions = result.scalars().all()

            if len(versions) <= keep_count:
                return 0

            # Sort by creation date (oldest first)
            versions.sort(key=lambda v: v.created_at)

            # Determine cutoff date
            cutoff_date = None
            if older_than_days:
                cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            # Mark versions for deletion
            versions_to_delete = []
            for version in versions[:-keep_count]:  # Keep the newest versions
                if cutoff_date and version.created_at < cutoff_date:
                    if not version.is_current and version.status != VersionStatus.LOCKED:
                        versions_to_delete.append(version)

            # Delete versions
            deleted_count = 0
            for version in versions_to_delete:
                self.db.delete(version)
                deleted_count += 1

            if deleted_count > 0:
                await self.db.commit()
                logger.info(
                    f"Cleaned up {deleted_count} old versions for file {file_id}"
                )

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old versions for file {file_id}: {str(e)}")
            return 0

    async def get_version_timeline(
        self,
        file_id: UUID,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get version timeline for a file.

        Args:
            file_id: File ID
            limit: Number of versions to return

        Returns:
            List of version timeline entries
        """
        try:
            versions, _ = await self.get_versions(
                file_id=file_id,
                sort_by=VersionSortBy.CREATED_AT,
                sort_order="desc",
                limit=limit,
            )

            timeline = []
            for version in versions:
                timeline.append({
                    "id": str(version.id),
                    "version": version.version,
                    "version_number": version.version_number,
                    "author": version.author_name,
                    "author_id": version.author_id,
                    "message": version.message,
                    "status": version.status,
                    "is_current": version.is_current,
                    "size": version.size,
                    "human_readable_size": version.human_readable_size,
                    "created_at": version.created_at.isoformat() if version.created_at else None,
                    "age_days": version.age_days,
                })

            return timeline

        except Exception as e:
            logger.error(f"Error getting version timeline for file {file_id}: {str(e)}")
            return []

    async def get_contributors(self, file_id: UUID) -> List[Dict[str, Any]]:
        """Get all contributors to a file.

        Args:
            file_id: File ID

        Returns:
            List of contributors with their statistics
        """
        try:
            # Get versions grouped by author
            query = (
                select(
                    FileVersion.author_id,
                    FileVersion.author_name,
                    func.count(FileVersion.id).label("version_count"),
                    func.max(FileVersion.created_at).label("last_contribution"),
                )
                .where(FileVersion.file_id == file_id)
                .group_by(FileVersion.author_id, FileVersion.author_name)
                .order_by(desc("last_contribution"))
            )

            result = await self.db.execute(query)
            contributor_rows = result.all()

            contributors = []
            for row in contributor_rows:
                contributors.append({
                    "author_id": row.author_id,
                    "author_name": row.author_name,
                    "version_count": row.version_count,
                    "last_contribution": row.last_contribution.isoformat() if row.last_contribution else None,
                })

            return contributors

        except Exception as e:
            logger.error(f"Error getting contributors for file {file_id}: {str(e)}")
            return []

    def _generate_diff(self, old_content: str, new_content: str) -> str:
        """Generate diff between two content strings.

        Args:
            old_content: Original content
            new_content: New content

        Returns:
            Unified diff string
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile="previous",
                tofile="current",
                lineterm="",
            )
        )

        return "\n".join(diff)
