"""File Operations Schemas.

This module contains Pydantic schemas for file CRUD operations,
search, filtering, bulk operations, and permissions.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict
from uuid import UUID

# Import enums from models
try:
    from app.file.models.file import FileStatus, FileType
    from app.file.models.file_permission import PermissionType, PermissionScope
except ImportError:
    # Fallback definitions for standalone usage
    FileStatus = Enum("FileStatus", {"ACTIVE": "active", "ARCHIVED": "archived", "DELETED": "deleted", "PENDING": "pending", "PROCESSING": "processing", "ERROR": "error"})
    FileType = Enum("FileType", {"DOCUMENT": "document", "IMAGE": "image", "VIDEO": "video", "AUDIO": "audio", "CODE": "code", "ARCHIVE": "archive", "OTHER": "other"})
    PermissionType = Enum("PermissionType", {"READ": "read", "WRITE": "write", "DELETE": "delete", "SHARE": "share", "ADMIN": "admin"})
    PermissionScope = Enum("PermissionScope", {"OWNER": "owner", "GROUP": "group", "PUBLIC": "public", "SPECIFIC": "specific"})


class FileCreate(BaseModel):
    """Schema for creating a new file."""

    name: str = Field(..., min_length=1, max_length=255, description="File name")
    content: Optional[bytes] = Field(None, description="File content")
    mime_type: str = Field(..., min_length=1, max_length=100, description="MIME type")
    size: int = Field(..., ge=0, description="File size in bytes")
    owner_id: str = Field(..., min_length=1, max_length=100, description="File owner ID")
    folder_id: Optional[str] = Field(None, description="Parent folder ID")
    parent_id: Optional[UUID] = Field(None, description="Parent file ID")
    description: Optional[str] = Field(None, max_length=1000, description="File description")
    tags: Optional[List[str]] = Field(default_factory=list, description="File tags")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    is_public: bool = Field(default=False, description="Whether file is publicly accessible")
    storage_key: str = Field(..., min_length=1, max_length=500, description="Storage key in bucket")
    bucket: str = Field(default="files", min_length=1, max_length=100, description="Storage bucket name")
    checksum: Optional[str] = Field(None, description="File checksum")

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags list."""
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        for tag in v:
            if len(tag) > 50:
                raise ValueError("Tag length cannot exceed 50 characters")
        return v

    @validator("metadata")
    def validate_metadata(cls, v):
        """Validate metadata size."""
        import json
        if len(json.dumps(v)) > 10000:
            raise ValueError("Metadata size cannot exceed 10KB")
        return v


class FileUpdate(BaseModel):
    """Schema for updating an existing file."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="File name")
    description: Optional[str] = Field(None, max_length=1000, description="File description")
    tags: Optional[List[str]] = Field(None, description="File tags")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    is_public: Optional[bool] = Field(None, description="Whether file is publicly accessible")
    status: Optional[FileStatus] = Field(None, description="File status")

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags list."""
        if v is not None:
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Tag length cannot exceed 50 characters")
        return v

    @validator("metadata")
    def validate_metadata(cls, v):
        """Validate metadata size."""
        if v is not None:
            import json
            if len(json.dumps(v)) > 10000:
                raise ValueError("Metadata size cannot exceed 10KB")
        return v


class FileResponse(BaseModel):
    """Schema for file response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    original_name: str
    path: str
    size: int
    size_mb: float
    human_readable_size: str
    mime_type: str
    extension: str
    type: FileType
    status: FileStatus
    owner_id: str
    parent_id: Optional[UUID]
    folder_id: Optional[str]
    bucket: str
    storage_key: str
    checksum: Optional[str]
    description: Optional[str]
    tags: List[str]
    metadata: Dict[str, Any]
    is_public: bool
    is_deleted: bool
    is_folder: bool
    is_file: bool
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime]
    version_count: int
    download_count: int
    preview_count: int
    age_days: int


class FileListResponse(BaseModel):
    """Schema for file list response."""

    files: List[FileResponse]
    total: int
    page: int
    page_size: int
    pages: int
    has_next: bool
    has_prev: bool


class FileFilter(BaseModel):
    """Schema for filtering files."""

    name: Optional[str] = Field(None, description="Filter by name (partial match)")
    type: Optional[FileType] = Field(None, description="Filter by file type")
    status: Optional[FileStatus] = Field(None, description="Filter by status")
    owner_id: Optional[str] = Field(None, description="Filter by owner ID")
    folder_id: Optional[str] = Field(None, description="Filter by folder ID")
    parent_id: Optional[UUID] = Field(None, description="Filter by parent ID")
    mime_type: Optional[str] = Field(None, description="Filter by MIME type")
    extension: Optional[str] = Field(None, description="Filter by extension")
    is_public: Optional[bool] = Field(None, description="Filter by public status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (must contain all)")
    created_after: Optional[datetime] = Field(None, description="Filter by creation date (after)")
    created_before: Optional[datetime] = Field(None, description="Filter by creation date (before)")
    updated_after: Optional[datetime] = Field(None, description="Filter by update date (after)")
    updated_before: Optional[datetime] = Field(None, description="Filter by update date (before)")
    size_min: Optional[int] = Field(None, ge=0, description="Minimum file size")
    size_max: Optional[int] = Field(None, ge=0, description="Maximum file size")


class FileSearch(BaseModel):
    """Schema for searching files."""

    query: str = Field(..., min_length=1, description="Search query")
    filters: Optional[FileFilter] = Field(None, description="Additional filters")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("desc", regex="^(asc|desc)$", description="Sort order")


class FileSearchResult(BaseModel):
    """Schema for file search results."""

    files: List[FileResponse]
    total: int
    page: int
    page_size: int
    pages: int
    query: str
    search_time: float


class FileBulkOperation(BaseModel):
    """Schema for bulk file operations."""

    operation: str = Field(..., regex="^(delete|move|copy|update|tag)$", description="Operation type")
    file_ids: List[UUID] = Field(..., min_items=1, max_items=1000, description="File IDs")
    target_folder_id: Optional[str] = Field(None, description="Target folder for move/copy")
    target_path: Optional[str] = Field(None, description="Target path for move/copy")
    update_data: Optional[FileUpdate] = Field(None, description="Data for update operation")
    tags_to_add: Optional[List[str]] = Field(None, description="Tags to add")
    tags_to_remove: Optional[List[str]] = Field(None, description="Tags to remove")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing files")


class FileBulkResult(BaseModel):
    """Schema for bulk operation results."""

    operation: str
    total_files: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    execution_time: float


class FileDelete(BaseModel):
    """Schema for file deletion."""

    permanent: bool = Field(default=False, description="Whether to permanently delete")
    reason: Optional[str] = Field(None, max_length=500, description="Deletion reason")


class FileRestore(BaseModel):
    """Schema for file restoration."""

    target_folder_id: Optional[str] = Field(None, description="Target folder for restore")


class FileMove(BaseModel):
    """Schema for file move operation."""

    target_folder_id: Optional[str] = Field(None, description="Target folder ID")
    target_path: Optional[str] = Field(None, max_length=500, description="Target path")
    new_name: Optional[str] = Field(None, min_length=1, max_length=255, description="New file name")


class FileCopy(BaseModel):
    """Schema for file copy operation."""

    target_folder_id: Optional[str] = Field(None, description="Target folder ID")
    target_path: Optional[str] = Field(None, max_length=500, description="Target path")
    new_name: Optional[str] = Field(None, min_length=1, max_length=255, description="New file name")
    overwrite: bool = Field(default=False, description="Whether to overwrite existing file")


class FilePermissionGrant(BaseModel):
    """Schema for granting file permissions."""

    user_id: Optional[str] = Field(None, description="User ID (for specific permission)")
    group_id: Optional[str] = Field(None, description="Group ID (for group permission)")
    permission_type: PermissionType = Field(..., description="Type of permission")
    scope: PermissionScope = Field(default=PermissionScope.SPECIFIC, description="Permission scope")
    expires_at: Optional[datetime] = Field(None, description="Permission expiration date")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Permission conditions")


class FilePermissionRevoke(BaseModel):
    """Schema for revoking file permissions."""

    user_id: Optional[str] = Field(None, description="User ID")
    group_id: Optional[str] = Field(None, description="Group ID")
    permission_type: Optional[PermissionType] = Field(None, description="Type of permission to revoke")


class FilePermissionResponse(BaseModel):
    """Schema for permission response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_id: UUID
    user_id: Optional[str]
    group_id: Optional[str]
    permission_type: PermissionType
    scope: PermissionScope
    is_active: bool
    granted_by: str
    granted_at: datetime
    expires_at: Optional[datetime]
    conditions: Dict[str, Any]
    is_expired: bool
    days_until_expiry: Optional[int]
    is_effective: bool
    created_at: datetime
    updated_at: datetime


# Utility functions
def validate_file_operation(operation: str, data: Dict[str, Any]) -> bool:
    """Validate file operation data."""
    operation_map = {
        "create": FileCreate,
        "update": FileUpdate,
        "delete": FileDelete,
        "restore": FileRestore,
        "move": FileMove,
        "copy": FileCopy,
    }

    if operation not in operation_map:
        return False

    try:
        operation_map[operation].model_validate(data)
        return True
    except Exception:
        return False


def format_file_size(size_bytes: int) -> str:
    """Format file size to human-readable string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def validate_file_permissions(user_id: str, file_owner_id: str, permissions: List[PermissionType]) -> bool:
    """Validate user permissions for file operation."""
    # Owner has all permissions
    if user_id == file_owner_id:
        return True

    # Check specific permissions
    required_permissions = set(permissions)
    # In a real implementation, this would check against database
    # For now, return False as placeholder
    return False
