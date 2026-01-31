"""Backup tasks for asynchronous backup operations.

This module contains Celery tasks for handling backup operations
asynchronously, including backup creation, restoration, and verification.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID

from celery import Task

from backend.app.storage.backup import BackupManager
from backend.app.storage.websocket import StorageWebSocketHandler

logger = logging.getLogger(__name__)


class BackupTask(Task):
    """Base task class for backup operations."""

    def __init__(self):
        """Initialize backup task."""
        self.backup_manager = None
        self.websocket_handler = None

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(
            f"Backup task {task_id} retrying: {exc}"
        )

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        skill_id = args[0] if args else None
        backup_type = kwargs.get('backup_type', 'unknown')

        logger.error(
            f"Backup task {task_id} failed: {exc}"
        )

        # Notify via WebSocket if available
        if self.websocket_handler and skill_id:
            try:
                self.websocket_handler.notify_skill_update(
                    str(skill_id),
                    "backup.failed",
                    {
                        "backup_type": backup_type,
                        "task_id": task_id,
                        "error": str(exc),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket: {e}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        skill_id = args[0] if args else None
        backup_type = kwargs.get('backup_type', 'unknown')

        logger.info(
            f"Backup task {task_id} completed successfully"
        )

        # Notify via WebSocket if available
        if self.websocket_handler and skill_id:
            try:
                self.websocket_handler.notify_skill_update(
                    str(skill_id),
                    "backup.completed",
                    {
                        "backup_type": backup_type,
                        "task_id": task_id,
                        "result": retval,
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to notify WebSocket: {e}")


def init_backup_manager():
    """Initialize backup manager for tasks.

    In a real application, this would use proper dependency injection.
    """
    from backend.app.storage.manager import SkillStorageManager
    from backend.app.storage.client import MinIOClient
    from backend.app.storage.schemas.storage_config import MinIOConfig
    from backend.app.storage.backup import BackupManager
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

    backup_manager = BackupManager(
        minio_client=minio_client,
        storage_manager=storage_manager,
        database_session=db_session,
    )

    return backup_manager


# Celery app will be configured elsewhere
celery_app = None


@celery_app.task(
    bind=True,
    base=BackupTask,
    name="storage.create_backup",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def create_backup_task(
    self,
    skill_id: Optional[UUID] = None,
    backup_type: str = "full",
    verify: bool = True,
):
    """Create a backup asynchronously.

    Args:
        skill_id: Optional skill ID (creates full backup if None)
        backup_type: Type of backup (full/incremental)
        verify: Whether to verify backup

    Returns:
        Backup result dictionary

    Raises:
        Exception: If backup creation fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting backup creation task {task_id}: skill={skill_id}, type={backup_type}"
    )

    try:
        # Initialize backup manager if not already done
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = init_backup_manager()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'initializing', 'percent': 5}
        )

        # Initialize backup manager
        self.backup_manager.initialize()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'creating', 'percent': 20}
        )

        # Create backup
        backup_id = self.backup_manager.create_backup(
            skill_id=skill_id,
            backup_type=backup_type,
            verify=verify,
        )

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'verifying', 'percent': 80}
        )

        # Verify backup if requested
        verification_result = None
        if verify:
            verification_result = self.backup_manager.verify_backup(backup_id)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'backup_id': backup_id,
            'skill_id': str(skill_id) if skill_id else None,
            'backup_type': backup_type,
            'verification_result': verification_result,
            'created_at': None,  # Would be set in production
        }

    except Exception as exc:
        logger.error(
            f"Backup creation task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying backup task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    base=BackupTask,
    name="storage.restore_backup",
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def restore_backup_task(
    self,
    backup_id: str,
    skill_id: Optional[UUID] = None,
    target_skill_id: Optional[UUID] = None,
    verify: bool = True,
):
    """Restore from backup asynchronously.

    Args:
        backup_id: Backup ID to restore
        skill_id: Optional skill ID to restore (restores all if None)
        target_skill_id: Optional target skill ID (uses original if None)
        verify: Whether to verify restore

    Returns:
        Restore result dictionary

    Raises:
        Exception: If restore fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting backup restore task {task_id}: backup={backup_id}, skill={skill_id}"
    )

    try:
        # Initialize backup manager if not already done
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = init_backup_manager()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'initializing', 'percent': 5}
        )

        # Initialize backup manager
        self.backup_manager.initialize()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'verifying', 'percent': 20}
        )

        # Verify backup if requested
        if verify:
            verification_result = self.backup_manager.verify_backup(backup_id)
            if not verification_result.get('overall_status') == 'passed':
                raise Exception("Backup verification failed")

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'restoring', 'percent': 50}
        )

        # Restore backup
        restore_result = self.backup_manager.restore_backup(
            backup_id=backup_id,
            skill_id=skill_id,
            target_skill_id=target_skill_id,
            verify=False,  # Already verified above
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
            'backup_id': backup_id,
            'skill_id': str(skill_id) if skill_id else None,
            'target_skill_id': str(target_skill_id) if target_skill_id else None,
            'restore_result': restore_result,
            'restored_at': None,  # Would be set in production
        }

    except Exception as exc:
        logger.error(
            f"Backup restore task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying restore task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    base=BackupTask,
    name="storage.verify_backup",
    max_retries=2,
    default_retry_delay=180,  # 3 minutes
)
def verify_backup_task(
    self,
    backup_id: str,
):
    """Verify backup integrity asynchronously.

    Args:
        backup_id: Backup ID to verify

    Returns:
        Verification result dictionary

    Raises:
        Exception: If verification fails
    """
    task_id = self.request.id

    logger.info(
        f"Starting backup verification task {task_id}: backup={backup_id}"
    )

    try:
        # Initialize backup manager if not already done
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = init_backup_manager()

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'verifying', 'percent': 50}
        )

        # Verify backup
        verification_result = self.backup_manager.verify_backup(backup_id)

        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'step': 'completed', 'percent': 100}
        )

        # Return result
        return {
            'success': True,
            'task_id': task_id,
            'backup_id': backup_id,
            'verification_result': verification_result,
            'verified_at': None,  # Would be set in production
        }

    except Exception as exc:
        logger.error(
            f"Backup verification task {task_id} failed: {exc}"
        )

        # Retry if configured
        if self.request.retries < self.max_retries:
            logger.info(
                f"Retrying verification task {task_id} (attempt {self.request.retries + 1}/{self.max_retries})"
            )
            raise self.retry(exc=exc)

        # Final failure
        raise


@celery_app.task(
    bind=True,
    name="storage.schedule_backup",
)
def schedule_backup_task(
    self,
    schedule_config: Dict[str, Any],
):
    """Schedule a backup.

    Args:
        schedule_config: Backup schedule configuration

    Returns:
        Scheduling result
    """
    task_id = self.request.id

    logger.info(
        f"Starting backup scheduling task {task_id}"
    )

    try:
        # Initialize backup manager if not already done
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = init_backup_manager()

        # Create schedule
        from backend.app.storage.backup import BackupSchedule

        schedule = BackupSchedule(
            name=schedule_config['name'],
            backup_type=schedule_config['backup_type'],
            frequency=schedule_config['frequency'],
            time=schedule_config['time'],
            retention_days=schedule_config.get('retention_days', 30),
            enabled=schedule_config.get('enabled', True),
            skills=schedule_config.get('skills', []),
        )

        # Schedule backup
        result = self.backup_manager.schedule_backup(schedule)

        return {
            'success': result,
            'task_id': task_id,
            'schedule_name': schedule.name,
            'message': 'Backup scheduled successfully' if result else 'Failed to schedule backup',
        }

    except Exception as exc:
        logger.error(
            f"Backup scheduling task {task_id} failed: {exc}"
        )
        raise


@celery_app.task(
    bind=True,
    name="storage.list_backups",
)
def list_backups_task(
    self,
    skill_id: Optional[UUID] = None,
    backup_type: Optional[str] = None,
    limit: int = 50,
):
    """List available backups.

    Args:
        skill_id: Optional skill ID filter
        backup_type: Optional backup type filter
        limit: Maximum number of backups to return

    Returns:
        List of backups
    """
    task_id = self.request.id

    logger.info(
        f"Starting list backups task {task_id}"
    )

    try:
        # Initialize backup manager if not already done
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = init_backup_manager()

        # List backups
        backups = self.backup_manager.list_backups(
            skill_id=skill_id,
            backup_type=backup_type,
            limit=limit,
        )

        return {
            'success': True,
            'task_id': task_id,
            'backups': backups,
            'total': len(backups),
        }

    except Exception as exc:
        logger.error(
            f"List backups task {task_id} failed: {exc}"
        )
        raise


@celery_app.task(
    bind=True,
    name="storage.delete_backup",
)
def delete_backup_task(
    self,
    backup_id: str,
):
    """Delete a backup.

    Args:
        backup_id: Backup ID to delete

    Returns:
        Deletion result
    """
    task_id = self.request.id

    logger.info(
        f"Starting delete backup task {task_id}: backup={backup_id}"
    )

    try:
        # Initialize backup manager if not already done
        if not hasattr(self, 'backup_manager') or self.backup_manager is None:
            self.backup_manager = init_backup_manager()

        # Delete backup
        result = self.backup_manager.delete_backup(backup_id)

        return {
            'success': result,
            'task_id': task_id,
            'backup_id': backup_id,
            'deleted_at': None,  # Would be set in production
        }

    except Exception as exc:
        logger.error(
            f"Delete backup task {task_id} failed: {exc}"
        )
        raise


@celery_app.task(
    bind=True,
    name="storage.get_backup_status",
)
def get_backup_status(self, task_id: str):
    """Get status of a backup task.

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
        logger.error(f"Failed to get backup status for task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }


@celery_app.task(
    bind=True,
    name="storage.cancel_backup",
)
def cancel_backup(self, task_id: str):
    """Cancel a backup task.

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
            'message': 'Backup task cancelled successfully',
        }

    except Exception as exc:
        logger.error(f"Failed to cancel backup task {task_id}: {exc}")
        return {
            'task_id': task_id,
            'status': 'ERROR',
            'error': str(exc),
        }
