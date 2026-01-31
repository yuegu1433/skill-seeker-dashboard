"""Batch Operation Configuration Schemas.

This module contains Pydantic schemas for batch file operations,
including upload, download, delete, move, copy, and processing.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from enum import Enum
from pydantic import BaseModel, Field, validator, ConfigDict
from uuid import UUID

# Import enums
try:
    from app.file.models.file import FileStatus, FileType
except ImportError:
    FileStatus = Enum("FileStatus", {"ACTIVE": "active", "ARCHIVED": "archived", "DELETED": "deleted", "PENDING": "pending", "PROCESSING": "processing", "ERROR": "error"})
    FileType = Enum("FileType", {"DOCUMENT": "document", "IMAGE": "image", "VIDEO": "video", "AUDIO": "audio", "CODE": "code", "ARCHIVE": "archive", "OTHER": "other"})


class BatchOperationType(str, Enum):
    """Batch operation type enumeration."""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    UPDATE = "update"
    TAG = "tag"
    PERMISSION = "permission"
    BACKUP = "backup"
    RESTORE = "restore"
    COMPRESS = "compress"
    DECOMPRESS = "decompress"
    CONVERT = "convert"


class BatchOperationStatus(str, Enum):
    """Batch operation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"
    SCHEDULED = "scheduled"


class BatchPriority(str, Enum):
    """Batch operation priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class BatchFileItem(BaseModel):
    """Schema for individual file in batch operation."""

    file_id: Optional[UUID] = Field(None, description="File ID")
    file_name: str = Field(..., description="File name")
    file_path: str = Field(..., description="File path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="File MIME type")
    source_path: Optional[str] = Field(None, description="Source path")
    target_path: Optional[str] = Field(None, description="Target path")
    status: Literal["pending", "processing", "completed", "failed", "skipped"] = Field(default="pending", description="File processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    start_time: Optional[datetime] = Field(None, description="Processing start time")
    end_time: Optional[datetime] = Field(None, description="Processing end time")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing result")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchProgress(BaseModel):
    """Schema for batch operation progress."""

    total_files: int = Field(..., description="Total number of files")
    processed_files: int = Field(default=0, description="Number of processed files")
    successful_files: int = Field(default=0, description="Number of successful files")
    failed_files: int = Field(default=0, description="Number of failed files")
    skipped_files: int = Field(default=0, description="Number of skipped files")
    current_file: Optional[str] = Field(None, description="Currently processing file")
    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated time remaining in seconds")
    bytes_processed: int = Field(default=0, description="Bytes processed")
    bytes_total: int = Field(default=0, description="Total bytes")
    start_time: Optional[datetime] = Field(None, description="Operation start time")
    last_update: datetime = Field(default_factory=datetime.now, description="Last progress update")


class BatchOperationConfig(BaseModel):
    """Schema for batch operation configuration."""

    operation_type: BatchOperationType = Field(..., description="Type of batch operation")
    file_items: List[BatchFileItem] = Field(..., min_items=1, max_items=10000, description="List of files to process")
    priority: BatchPriority = Field(default=BatchPriority.NORMAL, description="Operation priority")
    max_concurrent: int = Field(default=10, ge=1, le=100, description="Maximum concurrent operations")
    chunk_size: int = Field(default=100, ge=1, le=1000, description="Processing chunk size")
    retry_attempts: int = Field(default=3, ge=0, le=10, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="Retry delay in seconds")
    timeout: int = Field(default=300, ge=10, le=3600, description="Operation timeout in seconds")
    validate_files: bool = Field(default=True, description="Whether to validate files before processing")
    continue_on_error: bool = Field(default=False, description="Continue processing on error")
    overwrite_existing: bool = Field(default=False, description="Overwrite existing files")
    preserve_structure: bool = Field(default=True, description="Preserve directory structure")
    create_backups: bool = Field(default=False, description="Create backups before modifications")
    notification_enabled: bool = Field(default=True, description="Enable notifications")
    schedule_time: Optional[datetime] = Field(None, description="Scheduled execution time")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @validator("file_items")
    def validate_file_items(cls, v):
        """Validate file items."""
        # Check for duplicate file IDs
        file_ids = [item.file_id for item in v if item.file_id]
        if len(file_ids) != len(set(file_ids)):
            raise ValueError("Duplicate file IDs in batch operation")
        return v


class BatchUploadConfig(BatchOperationConfig):
    """Schema for batch upload configuration."""

    operation_type: Literal[BatchOperationType.UPLOAD] = Field(BatchOperationType.UPLOAD)
    target_folder_id: Optional[str] = Field(None, description="Target folder ID")
    target_path: Optional[str] = Field(None, description="Target path")
    create_directories: bool = Field(default=True, description="Create missing directories")
    generate_checksums: bool = Field(default=True, description="Generate file checksums")
    virus_scan: bool = Field(default=True, description="Scan files for viruses")
    extract_archives: bool = Field(default=False, description="Extract archive files")
    generate_previews: bool = Field(default=False, description="Generate file previews")


class BatchDownloadConfig(BatchOperationConfig):
    """Schema for batch download configuration."""

    operation_type: Literal[BatchOperationType.DOWNLOAD] = Field(BatchOperationType.DOWNLOAD)
    download_path: str = Field(..., description="Local download path")
    create_zip: bool = Field(default=False, description="Create ZIP archive")
    zip_name: Optional[str] = Field(None, description="ZIP archive name")
    include_metadata: bool = Field(default=True, description="Include file metadata")
    preserve_timestamps: bool = Field(default=True, description="Preserve file timestamps")
    compress_files: bool = Field(default=False, description="Compress files during download")


class BatchDeleteConfig(BatchOperationConfig):
    """Schema for batch delete configuration."""

    operation_type: Literal[BatchOperationType.DELETE] = Field(BatchOperationType.DELETE)
    permanent: bool = Field(default=False, description="Permanent delete (bypass trash)")
    force: bool = Field(default=False, description="Force delete without confirmation")
    backup_before_delete: bool = Field(default=True, description="Backup files before deletion")
    delete_versions: bool = Field(default=True, description="Delete all versions")
    delete_permissions: bool = Field(default=True, description="Delete permissions")


class BatchMoveConfig(BatchOperationConfig):
    """Schema for batch move configuration."""

    operation_type: Literal[BatchOperationType.MOVE] = Field(BatchOperationType.MOVE)
    target_folder_id: Optional[str] = Field(None, description="Target folder ID")
    target_path: Optional[str] = Field(None, description="Target path")
    conflict_resolution: Literal["skip", "overwrite", "rename", "error"] = Field(default="rename", description="Conflict resolution strategy")
    preserve_structure: bool = Field(default=True, description="Preserve directory structure")


class BatchCopyConfig(BatchOperationConfig):
    """Schema for batch copy configuration."""

    operation_type: Literal[BatchOperationType.COPY] = Field(BatchOperationType.COPY)
    target_folder_id: Optional[str] = Field(None, description="Target folder ID")
    target_path: Optional[str] = Field(None, description="Target path")
    conflict_resolution: Literal["skip", "overwrite", "rename", "error"] = Field(default="rename", description="Conflict resolution strategy")
    preserve_structure: bool = Field(default=True, description="Preserve directory structure")
    copy_permissions: bool = Field(default=True, description="Copy file permissions")
    copy_metadata: bool = Field(default=True, description="Copy file metadata")


class BatchProcessResult(BaseModel):
    """Schema for batch operation result."""

    operation_id: UUID = Field(..., description="Batch operation ID")
    operation_type: BatchOperationType = Field(..., description="Type of operation")
    status: BatchOperationStatus = Field(..., description="Operation status")
    progress: BatchProgress = Field(..., description="Operation progress")
    config: BatchOperationConfig = Field(..., description="Operation configuration")
    start_time: datetime = Field(..., description="Operation start time")
    end_time: Optional[datetime] = Field(None, description="Operation end time")
    duration: Optional[int] = Field(None, description="Operation duration in seconds")
    total_bytes_processed: int = Field(default=0, description="Total bytes processed")
    average_speed: Optional[float] = Field(None, description="Average processing speed in bytes/second")
    peak_memory_usage: Optional[int] = Field(None, description="Peak memory usage in bytes")
    error_summary: Optional[str] = Field(None, description="Summary of errors")
    warning_summary: Optional[str] = Field(None, description="Summary of warnings")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed results")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Error details")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="Warning details")
    created_by: str = Field(..., description="User who initiated the operation")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


class BatchSchedule(BaseModel):
    """Schema for batch operation scheduling."""

    schedule_id: UUID = Field(default_factory=UUID, description="Schedule ID")
    operation_config: BatchOperationConfig = Field(..., description="Operation configuration")
    cron_expression: Optional[str] = Field(None, description="Cron expression for recurring operations")
    interval_seconds: Optional[int] = Field(None, description="Interval in seconds for recurring operations")
    max_runs: Optional[int] = Field(None, description="Maximum number of runs")
    run_count: int = Field(default=0, description="Number of times executed")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run")
    last_run: Optional[datetime] = Field(None, description="Last run time")
    is_active: bool = Field(default=True, description="Whether schedule is active")
    created_by: str = Field(..., description="User who created the schedule")
    created_at: datetime = Field(default_factory=datetime.now, description="Schedule creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update time")


class BatchNotification(BaseModel):
    """Schema for batch operation notifications."""

    notification_id: UUID = Field(default_factory=UUID, description="Notification ID")
    operation_id: UUID = Field(..., description="Batch operation ID")
    user_id: str = Field(..., description="User ID to notify")
    notification_type: Literal["start", "progress", "complete", "error"] = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional notification data")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")


class BatchStatistics(BaseModel):
    """Schema for batch operation statistics."""

    total_operations: int = Field(..., description="Total number of operations")
    successful_operations: int = Field(..., description="Number of successful operations")
    failed_operations: int = Field(..., description="Number of failed operations")
    total_files_processed: int = Field(..., description="Total files processed")
    total_bytes_processed: int = Field(..., description="Total bytes processed")
    average_duration: float = Field(..., description="Average operation duration in seconds")
    most_common_operation: BatchOperationType = Field(..., description="Most common operation type")
    peak_concurrent_operations: int = Field(..., description="Peak concurrent operations")
    created_at: datetime = Field(..., description="Statistics creation time")


# Utility functions
def calculate_progress(processed: int, total: int) -> float:
    """Calculate progress percentage."""
    if total == 0:
        return 0.0
    return round((processed / total) * 100, 2)


def estimate_time_remaining(processed: int, total: int, start_time: datetime) -> Optional[int]:
    """Estimate time remaining for batch operation."""
    if processed == 0:
        return None

    elapsed = (datetime.now() - start_time).total_seconds()
    rate = processed / elapsed
    remaining = total - processed

    return int(remaining / rate) if rate > 0 else None


def get_operation_summary(operation: BatchProcessResult) -> Dict[str, Any]:
    """Get operation summary."""
    return {
        "operation_id": str(operation.operation_id),
        "operation_type": operation.operation_type.value,
        "status": operation.status.value,
        "progress": {
            "percentage": operation.progress.percentage,
            "processed": operation.progress.processed_files,
            "total": operation.progress.total_files,
            "successful": operation.progress.successful_files,
            "failed": operation.progress.failed_files,
        },
        "duration": operation.duration,
        "created_by": operation.created_by,
        "start_time": operation.start_time.isoformat(),
        "end_time": operation.end_time.isoformat() if operation.end_time else None,
    }


def validate_batch_config(config: BatchOperationConfig) -> bool:
    """Validate batch operation configuration."""
    try:
        # Validate concurrent operations
        if config.max_concurrent > 100:
            return False

        # Validate chunk size
        if config.chunk_size > len(config.file_items):
            return False

        # Validate timeout
        if config.timeout < 10:
            return False

        # Validate file items
        for item in config.file_items:
            if item.file_size and item.file_size < 0:
                return False

        return True
    except Exception:
        return False
