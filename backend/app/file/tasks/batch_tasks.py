"""Batch Operations Celery Tasks.

This module contains Celery tasks for batch file operations including
batch upload, download, delete, move, and copy operations.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
import asyncio
import json

from celery import current_task
from celery.exceptions import Retry

from app.file.tasks import celery_app, update_task_state
from app.file.batch_processor import BatchProcessor, OperationType, OperationStatus
from app.database.session import get_db

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="batch_upload_files")
def batch_upload_files(
    self,
    file_uploads: List[Dict[str, Any]],
    user_id: Optional[str] = None,
    priority: int = 0,
    **kwargs,
):
    """Batch upload multiple files.

    Args:
        self: Celery task instance
        file_uploads: List of file upload configurations
        user_id: User ID
        priority: Task priority
        **kwargs: Additional arguments

    Returns:
        Batch operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting batch upload task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", total_files=len(file_uploads))

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Create batch job
        file_ids = [f.get("file_id") for f in file_uploads if f.get("file_id")]
        job = asyncio.run(
            batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                file_ids=file_ids,
                parameters={"uploads": file_uploads},
                user_id=user_id,
                priority=priority,
            )
        )

        # Process batch job
        result = asyncio.run(batch_processor.process_batch_job(job.job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job.job_id,
            total_files=len(file_uploads),
            successful_files=result.successful_count,
            failed_files=result.failed_count,
            result=result.to_dict(),
        )

        logger.info(f"Batch upload task completed: {task_id}")

        return {
            "task_id": task_id,
            "job_id": job.job_id,
            "status": "completed",
            "total_files": len(file_uploads),
            "successful_files": result.successful_count,
            "failed_files": result.failed_count,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Batch upload task failed: {task_id}, error: {e}")

        # Update task state
        update_task_state.delay(task_id, "failed", error=str(e))

        # Retry task
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch upload task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="batch_download_files")
def batch_download_files(
    self,
    file_ids: List[str],
    download_path: str,
    user_id: Optional[str] = None,
    compress: bool = False,
    **kwargs,
):
    """Batch download multiple files.

    Args:
        self: Celery task instance
        file_ids: List of file IDs
        download_path: Download path
        user_id: User ID
        compress: Whether to compress downloads
        **kwargs: Additional arguments

    Returns:
        Batch operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting batch download task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", total_files=len(file_ids))

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Create batch job
        job = asyncio.run(
            batch_processor.create_batch_job(
                operation_type=OperationType.DOWNLOAD,
                file_ids=file_ids,
                parameters={
                    "download_path": download_path,
                    "compress": compress,
                },
                user_id=user_id,
            )
        )

        # Process batch job
        result = asyncio.run(batch_processor.process_batch_job(job.job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job.job_id,
            total_files=len(file_ids),
            successful_files=result.successful_count,
            failed_files=result.failed_count,
            download_path=download_path,
            compressed=compress,
            result=result.to_dict(),
        )

        logger.info(f"Batch download task completed: {task_id}")

        return {
            "task_id": task_id,
            "job_id": job.job_id,
            "status": "completed",
            "total_files": len(file_ids),
            "successful_files": result.successful_count,
            "failed_files": result.failed_count,
            "download_path": download_path,
            "compressed": compress,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Batch download task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch download task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="batch_delete_files")
def batch_delete_files(
    self,
    file_ids: List[str],
    user_id: Optional[str] = None,
    force: bool = False,
    backup_before_delete: bool = True,
    **kwargs,
):
    """Batch delete multiple files.

    Args:
        self: Celery task instance
        file_ids: List of file IDs
        user_id: User ID
        force: Force deletion without confirmation
        backup_before_delete: Create backup before deletion
        **kwargs: Additional arguments

    Returns:
        Batch operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting batch delete task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", total_files=len(file_ids))

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Create batch job
        job = asyncio.run(
            batch_processor.create_batch_job(
                operation_type=OperationType.DELETE,
                file_ids=file_ids,
                parameters={
                    "force": force,
                    "backup_before_delete": backup_before_delete,
                },
                user_id=user_id,
            )
        )

        # Process batch job
        result = asyncio.run(batch_processor.process_batch_job(job.job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job.job_id,
            total_files=len(file_ids),
            successful_files=result.successful_count,
            failed_files=result.failed_count,
            force=force,
            backup_created=backup_before_delete,
            result=result.to_dict(),
        )

        logger.info(f"Batch delete task completed: {task_id}")

        return {
            "task_id": task_id,
            "job_id": job.job_id,
            "status": "completed",
            "total_files": len(file_ids),
            "successful_files": result.successful_count,
            "failed_files": result.failed_count,
            "force": force,
            "backup_created": backup_before_delete,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Batch delete task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch delete task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="batch_move_files")
def batch_move_files(
    self,
    file_moves: List[Dict[str, Any]],
    user_id: Optional[str] = None,
    **kwargs,
):
    """Batch move multiple files.

    Args:
        self: Celery task instance
        file_moves: List of file move configurations
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Batch operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting batch move task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", total_files=len(file_moves))

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Create batch job
        file_ids = [m.get("file_id") for m in file_moves if m.get("file_id")]
        job = asyncio.run(
            batch_processor.create_batch_job(
                operation_type=OperationType.MOVE,
                file_ids=file_ids,
                parameters={"moves": file_moves},
                user_id=user_id,
            )
        )

        # Process batch job
        result = asyncio.run(batch_processor.process_batch_job(job.job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job.job_id,
            total_files=len(file_moves),
            successful_files=result.successful_count,
            failed_files=result.failed_count,
            result=result.to_dict(),
        )

        logger.info(f"Batch move task completed: {task_id}")

        return {
            "task_id": task_id,
            "job_id": job.job_id,
            "status": "completed",
            "total_files": len(file_moves),
            "successful_files": result.successful_count,
            "failed_files": result.failed_count,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Batch move task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch move task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="batch_copy_files")
def batch_copy_files(
    self,
    file_copies: List[Dict[str, Any]],
    user_id: Optional[str] = None,
    **kwargs,
):
    """Batch copy multiple files.

    Args:
        self: Celery task instance
        file_copies: List of file copy configurations
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Batch operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting batch copy task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", total_files=len(file_copies))

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Create batch job
        file_ids = [c.get("file_id") for c in file_copies if c.get("file_id")]
        job = asyncio.run(
            batch_processor.create_batch_job(
                operation_type=OperationType.COPY,
                file_ids=file_ids,
                parameters={"copies": file_copies},
                user_id=user_id,
            )
        )

        # Process batch job
        result = asyncio.run(batch_processor.process_batch_job(job.job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job.job_id,
            total_files=len(file_copies),
            successful_files=result.successful_count,
            failed_files=result.failed_count,
            result=result.to_dict(),
        )

        logger.info(f"Batch copy task completed: {task_id}")

        return {
            "task_id": task_id,
            "job_id": job.job_id,
            "status": "completed",
            "total_files": len(file_copies),
            "successful_files": result.successful_count,
            "failed_files": result.failed_count,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Batch copy task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch copy task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="batch_update_metadata")
def batch_update_metadata(
    self,
    metadata_updates: List[Dict[str, Any]],
    user_id: Optional[str] = None,
    **kwargs,
):
    """Batch update file metadata.

    Args:
        self: Celery task instance
        metadata_updates: List of metadata update configurations
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Batch operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting batch metadata update task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", total_files=len(metadata_updates))

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Create batch job
        file_ids = [u.get("file_id") for u in metadata_updates if u.get("file_id")]
        job = asyncio.run(
            batch_processor.create_batch_job(
                operation_type=OperationType.UPDATE,
                file_ids=file_ids,
                parameters={"updates": metadata_updates},
                user_id=user_id,
            )
        )

        # Process batch job
        result = asyncio.run(batch_processor.process_batch_job(job.job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job.job_id,
            total_files=len(metadata_updates),
            successful_files=result.successful_count,
            failed_files=result.failed_count,
            result=result.to_dict(),
        )

        logger.info(f"Batch metadata update task completed: {task_id}")

        return {
            "task_id": task_id,
            "job_id": job.job_id,
            "status": "completed",
            "total_files": len(metadata_updates),
            "successful_files": result.successful_count,
            "failed_files": result.failed_count,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Batch metadata update task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch metadata update task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="cancel_batch_operation")
def cancel_batch_operation(
    self,
    job_id: str,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Cancel a running batch operation.

    Args:
        self: Celery task instance
        job_id: Batch job ID
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Cancellation result
    """
    task_id = str(uuid4())
    logger.info(f"Cancelling batch operation: {job_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", job_id=job_id)

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Cancel batch job
        result = asyncio.run(batch_processor.cancel_batch_job(job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job_id,
            cancelled=result,
        )

        logger.info(f"Batch operation cancellation completed: {job_id}")

        return {
            "task_id": task_id,
            "job_id": job_id,
            "status": "completed",
            "cancelled": result,
        }

    except Exception as e:
        logger.error(f"Batch operation cancellation failed: {job_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying batch operation cancellation: {job_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=30, exc=e)

        raise


@celery_app.task(bind=True, name="retry_failed_batch_operations")
def retry_failed_batch_operations(
    self,
    job_id: str,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Retry failed operations in a batch job.

    Args:
        self: Celery task instance
        job_id: Batch job ID
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Retry result
    """
    task_id = str(uuid4())
    logger.info(f"Retrying failed operations for batch job: {job_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", job_id=job_id)

        # Initialize batch processor
        db_session = get_db()
        batch_processor = BatchProcessor(db_session=db_session)

        # Retry failed operations
        result = asyncio.run(batch_processor.retry_failed_operations(job_id))

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            job_id=job_id,
            retried_count=result.retried_count,
            result=result.to_dict(),
        )

        logger.info(f"Failed operations retry completed for: {job_id}")

        return {
            "task_id": task_id,
            "job_id": job_id,
            "status": "completed",
            "retried_count": result.retried_count,
            "results": result.to_dict(),
        }

    except Exception as e:
        logger.error(f"Failed operations retry failed for: {job_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying failed operations retry: {job_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise
