"""File operation schemas for MinIO storage API.

This module contains Pydantic models for validating file upload, download,
list, delete, and other file operations in the MinIO storage system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class FileUploadRequest(BaseModel):
    """Request model for file upload operations."""

    skill_id: UUID = Field(..., description="技能ID")
    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    content_type: str = Field(default="application/octet-stream", description="MIME类型")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, description="文件元数据")
    tags: Optional[List[str]] = Field(default_factory=list, description="文件标签")
    is_public: bool = Field(default=False, description="是否公开访问")

    @validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    @validator("content_type")
    def validate_content_type(cls, v: str) -> str:
        """Validate content type."""
        if not v or len(v) > 100:
            raise ValueError("Invalid content type")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {UUID: str}


class FileUploadResult(BaseModel):
    """Response model for file upload operations."""

    success: bool = Field(..., description="上传是否成功")
    object_name: str = Field(..., description="MinIO对象名")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    checksum: str = Field(..., description="SHA256校验和")
    version_id: Optional[str] = Field(None, description="版本ID")
    upload_url: Optional[str] = Field(None, description="上传URL(预签名)")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileDownloadRequest(BaseModel):
    """Request model for file download operations."""

    skill_id: UUID = Field(..., description="技能ID")
    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    version_id: Optional[str] = Field(None, description="版本ID(可选)")

    @validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileDownloadResult(BaseModel):
    """Response model for file download operations."""

    success: bool = Field(..., description="下载是否成功")
    file_path: str = Field(..., description="文件路径")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    content_type: str = Field(..., description="MIME类型")
    checksum: str = Field(..., description="SHA256校验和")
    download_url: Optional[str] = Field(None, description="下载URL(预签名)")
    expires_at: Optional[datetime] = Field(None, description="URL过期时间")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}


class FileInfo(BaseModel):
    """Model for file information."""

    id: UUID = Field(..., description="文件ID")
    skill_id: UUID = Field(..., description="技能ID")
    object_name: str = Field(..., description="MinIO对象名")
    file_path: str = Field(..., description="文件路径")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    content_type: str = Field(..., description="MIME类型")
    checksum: str = Field(..., description="SHA256校验和")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="文件元数据")
    tags: List[str] = Field(default_factory=list, description="文件标签")
    is_public: bool = Field(..., description="是否公开访问")
    version_count: int = Field(default=0, ge=0, description="版本数量")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_accessed_at: Optional[datetime] = Field(None, description="最后访问时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}


class FileDeleteRequest(BaseModel):
    """Request model for file delete operations."""

    skill_id: UUID = Field(..., description="技能ID")
    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    version_id: Optional[str] = Field(None, description="版本ID(删除特定版本)")

    @validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileDeleteResult(BaseModel):
    """Response model for file delete operations."""

    success: bool = Field(..., description="删除是否成功")
    file_path: str = Field(..., description="文件路径")
    version_id: Optional[str] = Field(None, description="删除的版本ID")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileListRequest(BaseModel):
    """Request model for file list operations."""

    skill_id: UUID = Field(..., description="技能ID")
    prefix: Optional[str] = Field(None, max_length=500, description="文件路径前缀")
    file_type: Optional[str] = Field(None, description="文件类型过滤")
    is_public: Optional[bool] = Field(None, description="公开状态过滤")
    limit: int = Field(default=50, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileListResult(BaseModel):
    """Response model for file list operations."""

    files: List[FileInfo] = Field(..., description="文件列表")
    total: int = Field(..., ge=0, description="总数量")
    has_more: bool = Field(..., description="是否还有更多")
    limit: int = Field(..., description="请求的限制")
    offset: int = Field(..., description="请求的偏移量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileMoveRequest(BaseModel):
    """Request model for file move operations."""

    skill_id: UUID = Field(..., description="技能ID")
    source_path: str = Field(..., min_length=1, max_length=500, description="源文件路径")
    target_path: str = Field(..., min_length=1, max_length=500, description="目标文件路径")

    @validator("source_path", "target_path")
    def validate_paths(cls, v: str) -> str:
        """Validate file paths for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileMoveResult(BaseModel):
    """Response model for file move operations."""

    success: bool = Field(..., description="移动是否成功")
    source_path: str = Field(..., description="源文件路径")
    target_path: str = Field(..., description="目标文件路径")
    new_object_name: str = Field(..., description="新的对象名")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# Version control schemas
class FileVersionInfo(BaseModel):
    """Model for file version information."""

    id: UUID = Field(..., description="版本ID")
    version_id: str = Field(..., description="版本标识")
    version_number: int = Field(..., ge=1, description="版本号")
    file_size: int = Field(..., ge=0, description="文件大小(字节)")
    checksum: str = Field(..., description="SHA256校验和")
    comment: Optional[str] = Field(None, description="版本说明")
    created_at: datetime = Field(..., description="创建时间")
    created_by: Optional[str] = Field(None, description="创建者")
    is_latest: bool = Field(..., description="是否最新版本")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {UUID: str, datetime: lambda v: v.isoformat()}


class FileVersionCreateRequest(BaseModel):
    """Request model for creating file versions."""

    skill_id: UUID = Field(..., description="技能ID")
    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    comment: Optional[str] = Field(None, description="版本说明")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="版本元数据")

    @validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class FileVersionRestoreRequest(BaseModel):
    """Request model for restoring file versions."""

    skill_id: UUID = Field(..., description="技能ID")
    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    version_id: str = Field(..., description="要恢复的版本ID")

    @validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# Batch operation schemas
class BatchFileOperation(BaseModel):
    """Model for batch file operations."""

    file_path: str = Field(..., min_length=1, max_length=500, description="文件路径")
    operation: str = Field(..., description="操作类型(upload, download, delete)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="操作元数据")

    @validator("operation")
    def validate_operation(cls, v: str) -> str:
        """Validate operation type."""
        allowed_operations = {"upload", "download", "delete"}
        if v not in allowed_operations:
            raise ValueError(f"Operation must be one of {allowed_operations}")
        return v

    @validator("file_path")
    def validate_file_path(cls, v: str) -> str:
        """Validate file path for security."""
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid file path")
        return v

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BatchFileOperationRequest(BaseModel):
    """Request model for batch file operations."""

    skill_id: UUID = Field(..., description="技能ID")
    operations: List[BatchFileOperation] = Field(
        ..., min_items=1, max_items=100, description="操作列表"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BatchFileOperationResult(BaseModel):
    """Response model for batch file operations."""

    success: bool = Field(..., description="批处理是否成功")
    total_operations: int = Field(..., ge=0, description="总操作数")
    successful_operations: int = Field(..., ge=0, description="成功操作数")
    failed_operations: int = Field(..., ge=0, description="失败操作数")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="操作结果")
    errors: List[str] = Field(default_factory=list, description="错误列表")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
