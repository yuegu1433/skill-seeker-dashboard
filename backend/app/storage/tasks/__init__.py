"""Celery tasks for storage operations.

This package contains Celery tasks for asynchronous storage operations
including file uploads, backups, and cleanup operations.
"""

from .upload_tasks import (
    upload_file_task,
    batch_upload_task,
)
from .backup_tasks import (
    create_backup_task,
    restore_backup_task,
    verify_backup_task,
    schedule_backup_task,
)
from .cleanup_tasks import (
    cleanup_old_files_task,
    cleanup_failed_uploads_task,
    cleanup_expired_versions_task,
    cleanup_orphaned_objects_task,
)

__all__ = [
    # Upload tasks
    "upload_file_task",
    "batch_upload_task",
    # Backup tasks
    "create_backup_task",
    "restore_backup_task",
    "verify_backup_task",
    "schedule_backup_task",
    # Cleanup tasks
    "cleanup_old_files_task",
    "cleanup_failed_uploads_task",
    "cleanup_expired_versions_task",
    "cleanup_orphaned_objects_task",
]
