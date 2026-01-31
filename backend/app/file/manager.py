"""File Manager.

This module contains the FileManager class which provides unified file management
operations including CRUD, search, filtering, permissions, and bulk operations.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Union, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, not_
from sqlalchemy.orm import selectinload

# Import models
from app.file.models.file import File, FileStatus, FileType
from app.file.models.file_version import FileVersion, VersionStatus
from app.file.models.file_permission import FilePermission, PermissionType, PermissionScope
from app.file.models.file_backup import FileBackup, BackupStatus

# Import schemas
from app.file.schemas.file_operations import (
    FileCreate,
    FileUpdate,
    FileResponse,
    FileListResponse,
    FileSearch,
    FileSearchResult,
    FileFilter,
    FileBulkOperation,
    FileBulkResult,
    FileDelete,
    FileRestore,
    FileMove,
    FileCopy,
)

# Import utils
from app.file.utils.validators import FileValidator, BusinessRuleValidator
from app.file.utils.formatters import format_file_size, format_timestamp
from app.file.utils.processors import calculate_checksum


logger = logging.getLogger(__name__)


class FileManager:
    """File manager for handling file operations."""

    def __init__(self, db_session: AsyncSession):
        """Initialize file manager.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.file_validator = FileValidator()
        self.business_validator = BusinessRuleValidator()

    async def create_file(self, file_data: FileCreate, user_id: str) -> FileResponse:
        """Create a new file.

        Args:
            file_data: File creation data
            user_id: User ID

        Returns:
            Created file response

        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate file data
            is_valid, error = self.file_validator.validate_file_name(file_data.name)
            if not is_valid:
                raise ValueError(f"Invalid file name: {error}")

            is_valid, error = self.file_validator.validate_file_size(file_data.size)
            if not is_valid:
                raise ValueError(f"Invalid file size: {error}")

            is_valid, error = self.file_validator.validate_file_type(file_data.name, file_data.mime_type)
            if not is_valid:
                raise ValueError(f"Invalid file type: {error}")

            is_valid, error = self.file_validator.validate_storage_path(file_data.storage_key)
            if not is_valid:
                raise ValueError(f"Invalid storage path: {error}")

            # Check if file already exists
            existing_file = await self.get_file_by_path(file_data.storage_key)
            if existing_file:
                raise ValueError(f"File already exists at path: {file_data.storage_key}")

            # Check user limits
            user_file_count = await self.get_user_file_count(user_id)
            is_valid, error = self.business_validator.validate_user_file_limit(user_file_count)
            if not is_valid:
                raise ValueError(error)

            user_storage = await self.get_user_storage_used(user_id)
            is_valid, error = self.business_validator.validate_user_storage_limit(user_storage, file_data.size)
            if not is_valid:
                raise ValueError(error)

            # Create file instance
            file = File.create_file(
                name=file_data.name,
                size=file_data.size,
                mime_type=file_data.mime_type,
                owner_id=user_id,
                storage_key=file_data.storage_key,
                bucket=file_data.bucket,
                parent_id=file_data.parent_id,
                folder_id=file_data.folder_id,
                checksum=file_data.checksum,
            )

            # Add metadata
            if file_data.description:
                file.description = file_data.description
            if file_data.tags:
                file.tags = file_data.tags
            if file_data.metadata:
                file.metadata = file_data.metadata

            # Add to database
            self.db.add(file)
            await self.db.commit()
            await self.db.refresh(file)

            logger.info(f"File created: {file.id} by user {user_id}")
            return FileResponse.model_validate(file)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating file: {str(e)}")
            raise

    async def get_file(self, file_id: UUID, user_id: str) -> Optional[FileResponse]:
        """Get file by ID.

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            File response or None if not found
        """
        try:
            # Query file with relationships
            query = (
                select(File)
                .options(
                    selectinload(File.versions),
                    selectinload(File.permissions),
                    selectinload(File.backups),
                )
                .where(File.id == file_id)
            )

            result = await self.db.execute(query)
            file = result.scalar_one_or_none()

            if not file:
                return None

            # Check permissions
            if not await self._check_file_permission(file, user_id, PermissionType.READ):
                return None

            # Update access time
            file.update_access_time()
            await self.db.commit()

            return FileResponse.model_validate(file)

        except Exception as e:
            logger.error(f"Error getting file {file_id}: {str(e)}")
            return None

    async def update_file(self, file_id: UUID, file_data: FileUpdate, user_id: str) -> Optional[FileResponse]:
        """Update file.

        Args:
            file_id: File ID
            file_data: File update data
            user_id: User ID

        Returns:
            Updated file response or None if not found
        """
        try:
            # Get existing file
            file = await self._get_file_by_id(file_id)
            if not file:
                return None

            # Check permissions
            if not await self._check_file_permission(file, user_id, PermissionType.WRITE):
                return None

            # Update fields
            if file_data.name is not None:
                is_valid, error = self.file_validator.validate_file_name(file_data.name)
                if not is_valid:
                    raise ValueError(f"Invalid file name: {error}")
                file.name = file_data.name

            if file_data.description is not None:
                file.description = file_data.description

            if file_data.tags is not None:
                is_valid, error = self.file_validator.validate_tags(file_data.tags)
                if not is_valid:
                    raise ValueError(f"Invalid tags: {error}")
                file.tags = file_data.tags

            if file_data.metadata is not None:
                is_valid, error = self.file_validator.validate_metadata(file_data.metadata)
                if not is_valid:
                    raise ValueError(f"Invalid metadata: {error}")
                file.metadata = file_data.metadata

            if file_data.is_public is not None:
                file.is_public = file_data.is_public

            if file_data.status is not None:
                file.status = file_data.status

            # Update timestamp
            file.updated_at = datetime.utcnow()

            await self.db.commit()
            await self.db.refresh(file)

            logger.info(f"File updated: {file_id} by user {user_id}")
            return FileResponse.model_validate(file)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating file {file_id}: {str(e)}")
            raise

    async def delete_file(self, file_id: UUID, user_id: str, delete_data: FileDelete) -> bool:
        """Delete file.

        Args:
            file_id: File ID
            user_id: User ID
            delete_data: Delete data

        Returns:
            True if deleted successfully
        """
        try:
            # Get existing file
            file = await self._get_file_by_id(file_id)
            if not file:
                return False

            # Check permissions
            if not await self._check_file_permission(file, user_id, PermissionType.DELETE):
                return False

            if delete_data.permanent:
                # Permanent delete - remove from database
                await self.db.delete(file)
            else:
                # Soft delete
                file.soft_delete()

            await self.db.commit()

            logger.info(f"File {'permanently deleted' if delete_data.permanent else 'deleted'}: {file_id} by user {user_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting file {file_id}: {str(e)}")
            raise

    async def restore_file(self, file_id: UUID, user_id: str, restore_data: FileRestore) -> Optional[FileResponse]:
        """Restore deleted file.

        Args:
            file_id: File ID
            user_id: User ID
            restore_data: Restore data

        Returns:
            Restored file response or None if not found
        """
        try:
            # Get deleted file
            query = select(File).where(
                and_(
                    File.id == file_id,
                    File.is_deleted == True
                )
            )

            result = await self.db.execute(query)
            file = result.scalar_one_or_none()

            if not file:
                return None

            # Check permissions
            if not await self._check_file_permission(file, user_id, PermissionType.WRITE):
                return None

            # Restore file
            file.restore()

            await self.db.commit()
            await self.db.refresh(file)

            logger.info(f"File restored: {file_id} by user {user_id}")
            return FileResponse.model_validate(file)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error restoring file {file_id}: {str(e)}")
            raise

    async def list_files(
        self,
        filters: Optional[FileFilter] = None,
        user_id: str = None,
        page: int = 1,
        page_size: int = 20,
        order_by: str = "created_at",
        order_dir: str = "desc"
    ) -> FileListResponse:
        """List files with filtering and pagination.

        Args:
            filters: File filters
            user_id: User ID
            page: Page number
            page_size: Page size
            order_by: Order by field
            order_dir: Order direction

        Returns:
            File list response
        """
        try:
            # Build query
            query = select(File)

            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)

            # Apply user filter if specified
            if user_id:
                # User can see their own files and files they have permission for
                permission_filter = await self._get_user_file_filter(user_id)
                if permission_filter:
                    query = query.filter(permission_filter)

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()

            # Apply ordering
            order_field = getattr(File, order_by, File.created_at)
            if order_dir.lower() == "desc":
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)

            # Execute query
            result = await self.db.execute(query)
            files = result.scalars().all()

            # Convert to responses
            file_responses = [FileResponse.model_validate(file) for file in files]

            # Calculate pagination info
            pages = (total + page_size - 1) // page_size
            has_next = page < pages
            has_prev = page > 1

            return FileListResponse(
                files=file_responses,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
                has_next=has_next,
                has_prev=has_prev
            )

        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            raise

    async def search_files(self, search: FileSearch, user_id: str) -> FileSearchResult:
        """Search files.

        Args:
            search: Search parameters
            user_id: User ID

        Returns:
            Search results
        """
        try:
            start_time = datetime.utcnow()

            # Build search query
            query = select(File)

            # Apply text search
            if search.query:
                search_filter = or_(
                    File.name.ilike(f"%{search.query}%"),
                    File.description.ilike(f"%{search.query}%"),
                    File.tags.contains(search.query)
                )
                query = query.filter(search_filter)

            # Apply filters
            if search.filters:
                query = self._apply_filters(query, search.filters)

            # Apply user permissions
            permission_filter = await self._get_user_file_filter(user_id)
            if permission_filter:
                query = query.filter(permission_filter)

            # Apply ordering
            order_field = getattr(File, search.sort_by or "created_at", File.created_at)
            if search.sort_order.lower() == "desc":
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())

            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar()

            # Apply pagination
            offset = (search.page - 1) * search.page_size
            query = query.offset(offset).limit(search.page_size)

            # Execute query
            result = await self.db.execute(query)
            files = result.scalars().all()

            # Convert to responses
            file_responses = [FileResponse.model_validate(file) for file in files]

            # Calculate search time
            end_time = datetime.utcnow()
            search_time = (end_time - start_time).total_seconds()

            return FileSearchResult(
                files=file_responses,
                total=total,
                page=search.page,
                page_size=search.page_size,
                pages=(total + search.page_size - 1) // search.page_size,
                query=search.query,
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            raise

    async def bulk_operation(self, operation: FileBulkOperation, user_id: str) -> FileBulkResult:
        """Perform bulk file operation.

        Args:
            operation: Bulk operation data
            user_id: User ID

        Returns:
            Bulk operation result
        """
        try:
            start_time = datetime.utcnow()
            results = []
            errors = []

            # Process files in batches
            batch_size = 100
            for i in range(0, len(operation.file_ids), batch_size):
                batch = operation.file_ids[i:i + batch_size]
                batch_results, batch_errors = await self._process_batch(operation, batch, user_id)
                results.extend(batch_results)
                errors.extend(batch_errors)

            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            # Count successful and failed operations
            successful = len(results)
            failed = len(errors)

            return FileBulkResult(
                operation=operation.operation,
                total_files=len(operation.file_ids),
                successful=successful,
                failed=failed,
                results=results,
                errors=errors,
                execution_time=execution_time
            )

        except Exception as e:
            logger.error(f"Error in bulk operation: {str(e)}")
            raise

    async def move_file(self, file_id: UUID, move_data: FileMove, user_id: str) -> Optional[FileResponse]:
        """Move file to new location.

        Args:
            file_id: File ID
            move_data: Move data
            user_id: User ID

        Returns:
            Moved file response or None if not found
        """
        try:
            # Get file
            file = await self._get_file_by_id(file_id)
            if not file:
                return None

            # Check permissions
            if not await self._check_file_permission(file, user_id, PermissionType.WRITE):
                return None

            # Update location
            if move_data.target_folder_id:
                file.folder_id = move_data.target_folder_id
            if move_data.new_name:
                file.name = move_data.new_name

            # Update path
            if move_data.target_path:
                file.path = move_data.target_path

            await self.db.commit()
            await self.db.refresh(file)

            logger.info(f"File moved: {file_id} by user {user_id}")
            return FileResponse.model_validate(file)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error moving file {file_id}: {str(e)}")
            raise

    async def copy_file(self, file_id: UUID, copy_data: FileCopy, user_id: str) -> Optional[FileResponse]:
        """Copy file to new location.

        Args:
            file_id: File ID
            copy_data: Copy data
            user_id: User ID

        Returns:
            Copied file response or None if not found
        """
        try:
            # Get original file
            original_file = await self._get_file_by_id(file_id)
            if not original_file:
                return None

            # Check permissions
            if not await self._check_file_permission(original_file, user_id, PermissionType.READ):
                return None

            # Create copy
            new_name = copy_data.new_name or f"Copy of {original_file.name}"
            storage_key = copy_data.target_path or f"{original_file.storage_key}_copy"

            new_file = File.create_file(
                name=new_name,
                size=original_file.size,
                mime_type=original_file.mime_type,
                owner_id=user_id,
                storage_key=storage_key,
                bucket=original_file.bucket,
                parent_id=original_file.parent_id,
                folder_id=copy_data.target_folder_id,
            )

            # Copy metadata
            new_file.description = original_file.description
            new_file.tags = original_file.tags
            new_file.metadata = original_file.metadata
            new_file.is_public = original_file.is_public

            self.db.add(new_file)
            await self.db.commit()
            await self.db.refresh(new_file)

            logger.info(f"File copied: {file_id} to {new_file.id} by user {user_id}")
            return FileResponse.model_validate(new_file)

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error copying file {file_id}: {str(e)}")
            raise

    async def get_file_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get file statistics for user.

        Args:
            user_id: User ID

        Returns:
            Dictionary of statistics
        """
        try:
            # Get total files
            total_files_query = select(func.count(File.id)).where(File.owner_id == user_id)
            total_files_result = await self.db.execute(total_files_query)
            total_files = total_files_result.scalar()

            # Get storage usage
            storage_query = select(func.sum(File.size)).where(File.owner_id == user_id)
            storage_result = await self.db.execute(storage_query)
            total_storage = storage_result.scalar() or 0

            # Get files by type
            type_query = (
                select(File.type, func.count(File.id))
                .where(File.owner_id == user_id)
                .group_by(File.type)
            )
            type_result = await self.db.execute(type_query)
            files_by_type = dict(type_result.all())

            # Get files by status
            status_query = (
                select(File.status, func.count(File.id))
                .where(File.owner_id == user_id)
                .group_by(File.status)
            )
            status_result = await self.db.execute(status_query)
            files_by_status = dict(status_result.all())

            return {
                "total_files": total_files,
                "total_storage": total_storage,
                "total_storage_formatted": format_file_size(total_storage),
                "files_by_type": files_by_type,
                "files_by_status": files_by_status,
            }

        except Exception as e:
            logger.error(f"Error getting file statistics: {str(e)}")
            raise

    # Helper methods

    async def _get_file_by_id(self, file_id: UUID) -> Optional[File]:
        """Get file by ID (internal method)."""
        query = select(File).where(File.id == file_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_file_by_path(self, storage_key: str) -> Optional[File]:
        """Get file by storage path."""
        query = select(File).where(File.storage_key == storage_key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _apply_filters(self, query, filters: FileFilter):
        """Apply filters to query."""
        if filters.name:
            query = query.filter(File.name.ilike(f"%{filters.name}%"))

        if filters.type:
            query = query.filter(File.type == filters.type)

        if filters.status:
            query = query.filter(File.status == filters.status)

        if filters.owner_id:
            query = query.filter(File.owner_id == filters.owner_id)

        if filters.folder_id:
            query = query.filter(File.folder_id == filters.folder_id)

        if filters.parent_id:
            query = query.filter(File.parent_id == filters.parent_id)

        if filters.mime_type:
            query = query.filter(File.mime_type.ilike(f"%{filters.mime_type}%"))

        if filters.extension:
            query = query.filter(File.extension == filters.extension)

        if filters.is_public is not None:
            query = query.filter(File.is_public == filters.is_public)

        if filters.tags:
            for tag in filters.tags:
                query = query.filter(File.tags.contains(tag))

        if filters.created_after:
            query = query.filter(File.created_at >= filters.created_after)

        if filters.created_before:
            query = query.filter(File.created_at <= filters.created_before)

        if filters.updated_after:
            query = query.filter(File.updated_at >= filters.updated_after)

        if filters.updated_before:
            query = query.filter(File.updated_at <= filters.updated_before)

        if filters.size_min is not None:
            query = query.filter(File.size >= filters.size_min)

        if filters.size_max is not None:
            query = query.filter(File.size <= filters.size_max)

        return query

    async def _check_file_permission(self, file: File, user_id: str, required_permission: PermissionType) -> bool:
        """Check if user has required permission for file."""
        # Owner always has permission
        if file.owner_id == user_id:
            return True

        # Check explicit permissions
        query = select(FilePermission).where(
            and_(
                FilePermission.file_id == file.id,
                FilePermission.is_active == True,
                or_(
                    FilePermission.user_id == user_id,
                    FilePermission.group_id.in_(await self._get_user_groups(user_id))
                )
            )
        )

        result = await self.db.execute(query)
        permissions = result.scalars().all()

        for permission in permissions:
            if permission.permission_type == required_permission.value:
                return True

        # Check if file is public
        if file.is_public and required_permission == PermissionType.READ:
            return True

        return False

    async def _get_user_groups(self, user_id: str) -> List[str]:
        """Get user groups (placeholder implementation)."""
        # In a real implementation, this would query user groups
        return []

    async def _get_user_file_filter(self, user_id: str):
        """Get filter for user's accessible files."""
        # User can see their own files and public files
        return or_(
            File.owner_id == user_id,
            File.is_public == True
        )

    async def _process_batch(self, operation: FileBulkOperation, file_ids: List[UUID], user_id: str):
        """Process a batch of files for bulk operation."""
        results = []
        errors = []

        for file_id in file_ids:
            try:
                if operation.operation == "delete":
                    success = await self.delete_file(file_id, user_id, FileDelete())
                elif operation.operation == "move":
                    success = await self.move_file(file_id, FileMove(**operation.target_folder_id), user_id)
                elif operation.operation == "copy":
                    success = await self.copy_file(file_id, FileCopy(**operation.target_folder_id), user_id)
                else:
                    raise ValueError(f"Unsupported operation: {operation.operation}")

                results.append({
                    "file_id": str(file_id),
                    "status": "success",
                    "message": "Operation completed successfully"
                })
            except Exception as e:
                errors.append({
                    "file_id": str(file_id),
                    "status": "error",
                    "message": str(e)
                })

        return results, errors

    async def get_user_file_count(self, user_id: str) -> int:
        """Get total file count for user."""
        query = select(func.count(File.id)).where(File.owner_id == user_id)
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_user_storage_used(self, user_id: str) -> int:
        """Get total storage used by user."""
        query = select(func.sum(File.size)).where(File.owner_id == user_id)
        result = await self.db.execute(query)
        return result.scalar() or 0
