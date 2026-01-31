"""Storage schemas package for Pydantic models.

This package contains Pydantic models for request/response validation
in the MinIO storage system API.
"""

from .file_operations import (
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
from .storage_config import (
    StorageConfig,
    MinIOConfig,
    CacheConfig,
    BackupConfig,
)

__all__ = [
    # File operation schemas
    "FileUploadRequest",
    "FileUploadResult",
    "FileDownloadRequest",
    "FileDownloadResult",
    "FileInfo",
    "FileDeleteRequest",
    "FileDeleteResult",
    "FileListRequest",
    "FileListResult",
    "FileMoveRequest",
    "FileMoveResult",
    # Storage configuration schemas
    "StorageConfig",
    "MinIOConfig",
    "CacheConfig",
    "BackupConfig",
]
