"""Cleanup tasks for asynchronous cleanup operations.

This module contains Celery tasks for handling cleanup operations
asynchronously, including old file cleanup, failed upload cleanup, etc.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

from celery import Task

from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.versioning import VersionManager
from backend.app.storage.cache import CacheManager
from backend.app.storage.client import MinIOClient

logger = logging.getLogger(__name__)


class CleanupTask(Task):
    """Base task class for cleanup operations."""

    def __init__(self):
        """Initialize cleanup task."""
        self.storage_manager = None
        self.version_manager = None
        self.cache_manager = None

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(
            f"Cleanup task {task_id} retrying: {exc}"
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        cleanup_type = args[0] if args else 'unknown'

        logger.error(
            f"Cleanup task {task_id} failed: {exc}"
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        cleanup_type = args[0] if args else 'unknown'

        logger.info(
            f"Cleanup task {task_id} completed successfully"
        )


def init_managers():
    """Initialize storage managers for tasks.

    In a real application, this would use proper dependency injection.
    """
    from backend.app.storage.schemas.storage_config import MinIOConfig
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Configure MinIO client
    config = MinIOConfig(
        endpoint="localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin123",
        secure=False,
    )

    minio_client = MinIOClient(config)

    # Configure database
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
    base=CleanupTask,
    name="storage.cleanup_old_files",
    max_retries=2,
    default_retry_delay=600,  # 10 minutes
)
def cleanup_old_files_task(
    self,
    skill_id: Optional[UUID] = None,
    days_old: int = 90,
    min_file_size: int = 1024 * 1024,  # 1MB
):
    """Clean up old files that haven't been accessed recently.

    Args:
        skill_id: Optional skill ID to filter cleanup
        days_old: Number of days old to consider for cleanup
        min_file_size: Minimum file size to consider for cleanup

    Returns:
        Cleanup result dictionary

    Raises:
        Exception: If cleanup fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting old files cleanup task {task_id}: skill={skill_id}, days={days_old}, min_size={min_file_size}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'scanning', 'percent': 10}
        )

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Get files to cleanup
        files_to_cleanup = []

        if skill_id:
            # Get files for specific skill
            from backend.app.storage.models import SkillFile
            from sqlalchemy import and_, lt

            query = self.storage_manager.db.query(SkillFile).filter(
                and_(
                    SkillFile.skill_id == skill_id,
                    SkillFile.updated_at < cutoff_date,
                    SkillFile.file_size >= min_file_size,
                )
            )

            files_to_cleanup = query.all()
        else:
            # Get files for all skills
            from backend.app.storage.models import SkillFile
            from sqlalchemy import and_, lt

            query = self.storage_manager.db.query(SkillFile).filter(
                and_(
                    SkillFile.updated_at < cutoff_date,
                    SkillFile.file_size >= min_file_size,
                )
            )

            files_to_cleanup = query.all()

        total_files = len(files_to_cleanup)
        deleted_count = 0
        error_count = 0

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'deleting', 'percent': 30}
        )

        # Delete files
        for index, file_record in enumerate(files_to_cleanup):
            try:
                # Delete file from storage
                from backend.app.storage.schemas.file_operations import FileDeleteRequest

                delete_request = FileDeleteRequest(
                    skill_id=file_record.skill_id,
                    file_path=file_record.file_path,
                )

                result = self.storage_manager.delete_file(delete_request)

                if result.success:
                    deleted_count += 1
                else:
                    error_count += 1
                    logger.warning(
                        f"Failed to delete file {file_record.file_path}: {result.error_message}"
                    )

                # Update progress
                percent = 30 + int((index / total_files) * 60)  # 30-90% for deletion
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'deleted {index}/{total_files}',
                        'percent': percent,
                        'current_file': file_record.file_path,
                    }
                )

            except Exception as file_exc:
                error_count += 1
                logger.error(
                    f"Error deleting file {file_record.file_path}: {file_exc}"
                )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'cleaning_cache', 'percent': 95}
        )

        # Clean up cache
        if self.cache_manager:
            try:
                if skill_id:
                    self.cache_manager.invalidate_file_cache(skill_id)
                else:
                    self.cache_manager.clear_prefix("file")
            except Exception as e:
                logger.warning(f"Cache cleanup failed: {e}")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'skill_id': str(skill_id) if skill_id else None,
            'total_files_scanned': total_files,
            'files_deleted': deleted_count,
            'errors': error_count,
            'cutoff_date': cutoff_date.isoformat(),
            'min_file_size': min_file_size,
        }

    except Exception as exc:
        logger.error(
            f"Old files cleanup task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying cleanup task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    base=CleanupTask,
    name="storage.cleanup_failed_uploads",
    max_retries=2,
    default_retry_delay=300,  # 5 minutes
)
def cleanup_failed_uploads_task(
    self,
    hours_old: int = 24,
):
    """Clean up records of failed uploads.

    Args:
        hours_old: Number of hours old to consider for cleanup

    Returns:
        Cleanup result dictionary

    Raises:
        Exception: If cleanup fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting failed uploads cleanup task {task_id}: hours={hours_old}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'scanning', 'percent': 20}
        )

        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)

        # Get failed upload records
        # Note: This is a placeholder implementation
        # In production, you would have a separate table for upload attempts
        failed_uploads = []

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'cleaning', 'percent': 60}
        )

        # Clean up failed upload records
        cleaned_count = len(failed_uploads)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'failed_uploads_cleaned': cleaned_count,
            'cutoff_time': cutoff_time.isoformat(),
            'hours_old': hours_old,
        }

    except Exception as exc:
        logger.error(
            f"Failed uploads cleanup task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying cleanup task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    base=CleanupTask,
    name="storage.cleanup_expired_versions",
    max_retries=2,
    default_retry_delay=600,  # 10 minutes
)
def cleanup_expired_versions_task(
    self,
    skill_id: Optional[UUID] = None,
    days_old: int = 30,
):
    """Clean up expired file versions.

    Args:
        skill_id: Optional skill ID to filter cleanup
        days_old: Number of days old to consider for cleanup

    Returns:
        Cleanup result dictionary

    Raises:
        Exception: If cleanup fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting expired versions cleanup task {task_id}: skill={skill_id}, days={days_old}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'cleaning', 'percent': 50}
        )

        # Clean up old versions using version manager
        deleted_count = self.version_manager.cleanup_old_versions(skill_id=skill_id)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'skill_id': str(skill_id) if skill_id else None,
            'versions_deleted': deleted_count,
            'days_old': days_old,
        }

    except Exception as exc:
        logger.error(
            f"Expired versions cleanup task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying cleanup task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    base=CleanupTask,
    name="storage.cleanup_orphaned_objects",
    max_retries=2,
    default_retry_delay=900,  # 15 minutes
)
def cleanup_orphaned_objects_task(
    self,
    bucket_name: str = "skillseekers-skills",
):
    """Clean up orphaned objects in MinIO.

    Args:
        bucket_name: Bucket name to clean up

    Returns:
        Cleanup result dictionary

    Raises:
        Exception: If cleanup fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting orphaned objects cleanup task {task_id}: bucket={bucket_name}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'scanning', 'percent': 20}
        )

        # Get all objects in bucket
        minio_client = self.storage_manager.minio_client
        objects = list(minio_client.list_objects(bucket_name=bucket_name))

        total_objects = len(objects)
        orphaned_count = 0
        deleted_count = 0

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'analyzing', 'percent': 40}
        )

        # Check each object against database records
        for index, obj_info in enumerate(objects):
            object_name = obj_info['object_name']

            try:
                # Check if object exists in database
                from backend.app.storage.models import SkillFile
                from sqlalchemy import func

                # Query for this object
                file_record = self.storage_manager.db.query(SkillFile).filter(
                    SkillFile.object_name == object_name
                ).first()

                if file_record is None:
                    orphaned_count += 1

                    # Delete orphaned object
                    minio_client.remove_object(bucket_name, object_name)
                    deleted_count += 1

                # Update progress
                percent = 40 + int((index / total_objects) * 50)  # 40-90% for checking
                self.update_state(
                    state='PROGRESS',
                    meta={
                        'step': f'checked {index}/{total_objects}',
                        'percent': percent,
                        'current_object': object_name,
                    }
                )

            except Exception as obj_exc:
                logger.warning(
                    f"Error checking object {object_name}: {obj_exc}"
                )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'bucket_name': bucket_name,
            'total_objects_scanned': total_objects,
            'orphaned_objects_found': orphaned_count,
            'objects_deleted': deleted_count,
        }

    except Exception as exc:
        logger.error(
            f"Orphaned objects cleanup task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying cleanup task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    name="storage.cleanup_cache",
)
def cleanup_cache_task(
    self,
    skill_id: Optional[UUID] = None,
):
    """Clean up expired cache entries.

    Args:
        skill_id: Optional skill ID to filter cleanup

    Returns:
        Cleanup result
    """
    task_id = self.request.id

    logger.info(
        f"Starting cache cleanup task {task_id}: skill={skill_id}"
    )

    try:
        # Initialize managers if not already done
        if not hasattr(self, 'storage_manager') or self.storage_manager is None:
            self.storage_manager, self.version_manager, self.cache_manager = init_managers()

        # Clean up cache
        if self.cache_manager:
            if skill_id:
                self.cache_manager.invalidate_file_cache(skill_id)
            else:
                # Clear all cache
                self.cache_manager.clear_prefix("file")
                self.cache_manager.clear_prefix("version")
                self.cache_manager.clear_prefix("stats")

        return {
            'success': True,
            'task_id': task_id,
            'skill_id': str(skill_id) if skill_id else None,
            'message': 'Cache cleanup completed',
        }

    except Exception as exc:
        logger.error(
            f"Cache cleanup task {task_id} failed: {exc}"
        )
        raise


@celery_app.task(
    bind=True,
    name="storage.get_cleanup_status",
)
def get_cleanup_status(self, task_id: str):
    """Get status of a cleanup task.

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
        logger.error(f"Failed to get cleanup status for task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }


@celery_app.task(
    bind=True,
    name="storage.cancel_cleanup",
)
def cancel_cleanup(self, task_id: str):
    """Cancel a cleanup task.

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
            'message': 'Cleanup task cancelled successfully',
        }

    except Exception as exc:
        logger.error(f"Failed to cancel cleanup task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }


@celery_app.task(
    bind=True,
    name="storage.schedule_cleanup",
)
def schedule_cleanup_task(
    self,
    cleanup_type: str,
    schedule_config: Dict[str, Any],
):
    """Schedule a cleanup task.

    Args:
        cleanup_type: Type of cleanup
        schedule_config: Schedule configuration

    Returns:
        Scheduling result
    """
    task_id = self.request.id

    logger.info(
        f"Starting cleanup scheduling task {task_id}: type={cleanup_type}"
    )

    try:
        # Map cleanup types to task functions
        cleanup_tasks = {
            'old_files': cleanup_old_files_task,
            'failed_uploads': cleanup_failed_uploads_task,
            'expired_versions': cleanup_expired_versions_task,
            'orphaned_objects': cleanup_orphaned_objects_task,
            'cache': cleanup_cache_task,
        }

        if cleanup_type not in cleanup_tasks:
            raise ValueError(f"Unknown cleanup type: {cleanup_type}")

        # Get task function
        task_func = cleanup_tasks[cleanup_type]

        # Schedule task
        task_func.apply_async(
            kwargs=schedule_config,
            countdown=schedule_config.get('countdown', 0),  # Delay in seconds
        )

        return {
            'success': True,
            'task_id': task_id,
            'cleanup_type': cleanup_type,
            'message': f'{cleanup_type} cleanup scheduled',
        }

    except Exception as exc:
        logger.error(
            f"Cleanup scheduling task {task_id} failed: {exc}"
        )
        raise
