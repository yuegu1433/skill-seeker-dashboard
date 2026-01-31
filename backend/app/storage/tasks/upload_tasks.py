"""Upload tasks for asynchronous file uploads.

This module contains Celery tasks for handling file upload operations
asynchronously, including single file uploads and batch uploads.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from celery import Task

from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.versioning import VersionManager
from backend.app.storage.cache import CacheManager
from backend.app.storage.websocket import StorageWebSocketHandler

logger = logging.getLogger(__name__)


class UploadTask(Task):
    """Base task class for upload operations."""

    def __init__(self):
        """Initialize upload task."""
        self.storage_manager = None
        self.version_manager = None
        self.cache_manager = None
        self.websocket_handler = None

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(
            f"Upload task {task_id} retrying: {exc}"
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        skill_id = args[0] if args else None
        file_path = args[1] if len(args) > 1 else None

        logger.error(
            f"Upload task {task_id} failed: {exc}"
        )

        # Notify via WebSocket if available
        if self.websocket_handler and skill_id:
            try:
                self.websocket_handler.notify_skill_update(
                    str(skill_id),
                    "upload.failed",
                    {
                        "file_path": file_path,
                        "task_id": task_id,
                        "error": str(exc),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket: {e}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        skill_id = args[0] if args else None
        file_path = args[1] if len(args) > 1 else None

        logger.info(
            f"Upload task {task_id} completed successfully"
        )

        # Notify via WebSocket if available
        if self.websocket_handler and skill_id:
            try:
                self.websocket_handler.notify_skill_update(
                    str(skill_id),
                    "upload.completed",
                    {
                        "file_path": file_path,
                        "task_id": task_id,
                        "result": retval,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket: {e}")


def init_managers():
    """Initialize storage managers for tasks.

    In a real application, this would use proper dependency injection.
    For now, we create instances as needed.
    """
    from backend.app.storage.manager import SkillStorageManager
    from backend.app.storage.versioning import VersionManager
    from backend.app.storage.cache import CacheManager
    from backend.app.storage.client import MinIOClient
    from backend.app.storage.schemas.storage_config import MinIOConfig

    # This is a placeholder - in production, use proper configuration
    config = MinIOConfig(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False,
    )

    minio_client = MinIOClient(config)

    # Note: In production, use proper database session management
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine("sqlite:///test.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    storage_manager = SkillStorageManager(
        minio_client=minio_client,
        database_session=db_session,
    )

    version_manager = VersionManager(
        minio_client=minio_client,
        storage_manager=storage_manager,
        database_session=db_session,
    )

    cache_manager = CacheManager(
        redis_url="redis://localhost:6379",
    )

    return storage_manager, version_manager, cache_manager


# Celery app will be configured elsewhere
celery_app = None


@celery_app.task(
    bind=True,
    base=UploadTask,
    name="storage.upload_file",
    max_retries=3,
    default_retry_delay=60,
)
def upload_file_task(
    self,
    skill_id: UUID,
    file_path: str,
    file_data: bytes,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Upload a single file asynchronously.

    Args:
        skill_id: Skill ID
        file_path: File path
        file_data: File content
        content_type: Optional content type
        metadata: Optional metadata

    Returns:
        Upload result dictionary

    Raises:
        Exception: If upload fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting file upload task {task_id}: skill={skill_id}, path={file_path}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'uploading', 'percent': 10}
        )

        # Create upload request
        from backend.app.storage.schemas.file_operations import FileUploadRequest

        upload_request = FileUploadRequest(
            skill_id=skill_id,
            file_path=file_path,
            content_type=content_type,
            metadata=metadata or {},
        )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'processing', 'percent': 30}
        )

        # Upload file
        result = self.storage_manager.upload_file(upload_request, file_data)

        if not result.success:
            raise Exception(result.error_message or "Upload failed")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'caching', 'percent': 70}
        )

        # Invalidate cache
        if self.cache_manager:
            try:
                self.cache_manager.invalidate_file_cache(skill_id, file_path)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'skill_id': str(skill_id),
            'file_path': file_path,
            'file_size': result.file_size,
            'checksum': result.checksum,
            'uploaded_at': result.uploaded_at.isoformat() if result.uploaded_at else None,
        }

    except Exception as exc:
        logger.error(
            f"File upload task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying upload task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    base=UploadTask,
    name="storage.batch_upload",
    max_retries=3,
    default_retry_delay=120,
)
def batch_upload_task(
    self,
    skill_id: UUID,
    files: List[Dict[str, Any]],
):
    """Upload multiple files in batch asynchronously.

    Args:
        skill_id: Skill ID
        files: List of file dictionaries with 'path', 'data', 'content_type', 'metadata'

    Returns:
        Batch upload result dictionary

    Raises:
        Exception: If batch upload fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting batch upload task {task_id}: skill={skill_id}, files={len(files)}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        total_files = len(files)
        successful_uploads = 0
        failed_uploads = 0
        results = []

        # Process each file
        for index, file_info in enumerate(files):
            try:
                file_path = file_info['path']
                file_data = file_info['data']
                content_type = file_info.get('content_type')
                metadata = file_info.get('metadata', {})

                # Update progress
                percent = int((index / total_files) * 80)  # 80% for uploads
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'uploaded {index}/{total_files}',
                        'percent': percent,
                        'current_file': file_path,
                    }
                )

                # Create upload request
                from backend.app.storage.schemas.file_operations import FileUploadRequest

                upload_request = FileUploadRequest(
                    skill_id=skill_id,
                    file_path=file_path,
                    content_type=content_type,
                    metadata=metadata,
                )

                # Upload file
                result = self.storage_manager.upload_file(upload_request, file_data)

                if result.success:
                    successful_uploads += 1
                    results.append({
                        'file_path': file_path,
                        'success': True,
                        'file_size': result.file_size,
                        'checksum': result.checksum,
                    })
                else:
                    failed_uploads += 1
                    results.append({
                        'file_path': file_path,
                        'success': False,
                        'error': result.error_message,
                    })

            except Exception as file_exc:
                failed_uploads += 1
                logger.error(
                    f"Batch upload failed for file {file_info.get('path', 'unknown')}: {file_exc}"
                )
                results.append({
                    'file_path': file_info.get('path', 'unknown'),
                    'success': False,
                    'error': str(file_exc),
                })

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'invalidating_cache', 'percent': 90}
        )

        # Invalidate cache
        if self.cache_manager:
            try:
                self.cache_manager.invalidate_file_cache(skill_id)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return batch result
        return {
            'success': True,
            'task_id': task_id,
            'skill_id': str(skill_id),
            'total_files': total_files,
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'results': results,
            'completed_at': None,  # Would be set in production
        }

    except Exception as exc:
        logger.error(
            f"Batch upload task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying batch upload task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    name="storage.get_upload_status",
)
def get_upload_status(self, task_id: str):
    """Get status of an upload task.

    Args:
        task_id: Celery task ID

    Returns:
        Task status dictionary
    """
    try:
        # Get task result
        result = celery_app.AsyncResult(task_id)

        return {
            'task_id': task_id,
            'status': result.status,
            'result': result.result if result.ready() else None,
            'traceback': result.traceback if result.failed() else None,
        }

    except Exception as exc:
        logger.error(f"Failed to get upload status for task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }


@celery_app.task(
    bind=True,
    name="storage.cancel_upload",
)
def cancel_upload(self, task_id: str):
    """Cancel an upload task.

    Args:
        task_id: Celery task ID

    Returns:
        Cancellation result
    """
    try:
        # Revoke task
        celery_app.control.revoke(task_id, terminate=True)

        return {
            'task_id': task_id,
            'status': 'REVOKED',
            'message': 'Task cancelled successfully',
        }

    except Exception as exc:
        logger.error(f"Failed to cancel upload task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }


@celery_app.task(
    bind=True,
    name="storage.retry_upload",
)
def retry_upload(self, task_id: str):
    """Retry a failed upload task.

    Args:
        task_id: Original task ID

    Returns:
        New task ID
    """
    try:
        # Get original task
        original_result = celery_app.AsyncResult(task_id)

        if not original_result.failed():
            raise Exception("Task is not in failed state")

        # Get task args from meta
        if hasattr(original_result, 'info') and original_result.info:
            args = original_result.info.get('args', [])
            kwargs = original_result.info.get('kwargs', {})

            # Create new task
            new_task = upload_file_task.apply_async(args=args, kwargs=kwargs)

            return {
                'original_task_id': task_id,
                'new_task_id': new_task.id,
                'status': 'RETRY',
                'message': 'Task retry created',
            }
        else:
            raise Exception("Cannot retrieve original task arguments")

    except Exception as exc:
        logger.error(f"Failed to retry upload task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }
