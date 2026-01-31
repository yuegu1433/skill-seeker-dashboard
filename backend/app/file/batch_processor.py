"""Batch Processor.

This module contains the BatchProcessor class which provides efficient batch
file operations including upload, download, delete, move with progress tracking
and concurrent control.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Callable, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from sqlalchemy.ext.asyncio import AsyncSession

# Import managers and schemas
from app.file.manager import FileManager
from app.file.schemas.file_operations import FileResponse, FileOperation
from app.file.schemas.batch_config import BatchOperation, BatchStatus, BatchProgress

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Batch operation type enumeration."""
    UPLOAD = "upload"
    DOWNLOAD = "download"
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    UPDATE = "update"
    CONVERT = "convert"
    COMPRESS = "compress"
    EXTRACT = "extract"


class OperationStatus(str, Enum):
    """Operation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class BatchOperationResult:
    """Result of a batch operation."""

    operation_id: str
    file_id: Optional[str] = None
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    status: OperationStatus = OperationStatus.PENDING
    success: bool = False
    error_message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    bytes_processed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "file_id": self.file_id,
            "source_path": self.source_path,
            "target_path": self.target_path,
            "status": self.status.value,
            "success": self.success,
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "bytes_processed": self.bytes_processed,
            "metadata": self.metadata,
        }


@dataclass
class BatchJob:
    """Batch job information."""

    job_id: str
    operation_type: OperationType
    status: BatchStatus
    total_operations: int = 0
    completed_operations: int = 0
    failed_operations: int = 0
    skipped_operations: int = 0
    progress_percentage: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    operation_results: List[BatchOperationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def update_progress(self):
        """Update job progress."""
        if self.total_operations > 0:
            self.progress_percentage = (self.completed_operations / self.total_operations) * 100
        else:
            self.progress_percentage = 0.0

        self.updated_at = datetime.utcnow()

        if self.status == BatchStatus.RUNNING and self.progress_percentage >= 100.0:
            self.status = BatchStatus.COMPLETED
            self.end_time = datetime.utcnow()
            if self.start_time:
                self.duration_seconds = (self.end_time - self.start_time).total_seconds()


class ProgressCallback:
    """Progress callback for batch operations."""

    def __init__(self, callback: Callable[[BatchProgress], None]):
        self.callback = callback
        self.last_update = datetime.utcnow()

    async def __call__(self, job: BatchJob):
        """Call the callback with job progress."""
        current_time = datetime.utcnow()

        # Throttle updates to avoid overwhelming the callback
        if (current_time - self.last_update).total_seconds() >= 1.0 or job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]:
            try:
                progress = BatchProgress(
                    job_id=job.job_id,
                    status=job.status,
                    total_operations=job.total_operations,
                    completed_operations=job.completed_operations,
                    failed_operations=job.failed_operations,
                    skipped_operations=job.skipped_operations,
                    progress_percentage=job.progress_percentage,
                    start_time=job.start_time,
                    end_time=job.end_time,
                    duration_seconds=job.duration_seconds,
                )
                await asyncio.get_event_loop().run_in_executor(None, self.callback, progress)
                self.last_update = current_time
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")


class BatchProcessor:
    """Batch file processing system."""

    def __init__(
        self,
        db_session: AsyncSession,
        max_concurrent_operations: int = 10,
        max_workers: int = 5,
        operation_timeout: int = 300,  # 5 minutes
    ):
        """Initialize batch processor.

        Args:
            db_session: Database session
            max_concurrent_operations: Maximum concurrent operations
            max_workers: Thread pool size
            operation_timeout: Operation timeout in seconds
        """
        self.db = db_session
        self.file_manager = FileManager(db_session)
        self.max_concurrent_operations = max_concurrent_operations
        self.max_workers = max_workers
        self.operation_timeout = operation_timeout

        # Active batch jobs
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_lock = threading.RLock()

        # Operation statistics
        self.operation_stats = {
            "total_jobs": 0,
            "completed_jobs": 0,
            "failed_jobs": 0,
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
        }

    async def create_batch_job(
        self,
        operation_type: OperationType,
        operations: List[BatchOperation],
        metadata: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> str:
        """Create a new batch job.

        Args:
            operation_type: Type of operation
            operations: List of operations to perform
            metadata: Additional metadata
            progress_callback: Progress callback function

        Returns:
            Job ID
        """
        job_id = str(uuid4())

        # Create job
        job = BatchJob(
            job_id=job_id,
            operation_type=operation_type,
            status=BatchStatus.PENDING,
            total_operations=len(operations),
            metadata=metadata or {},
        )

        # Create operation results
        for operation in operations:
            result = BatchOperationResult(
                operation_id=str(uuid4()),
                file_id=operation.file_id,
                source_path=operation.source_path,
                target_path=operation.target_path,
            )
            job.operation_results.append(result)

        # Store job
        with self.job_lock:
            self.active_jobs[job_id] = job

        # Update stats
        self.operation_stats["total_jobs"] += 1
        self.operation_stats["total_operations"] += len(operations)

        logger.info(f"Created batch job {job_id} with {len(operations)} operations")
        return job_id

    async def execute_batch_job(
        self,
        job_id: str,
        progress_callback: Optional[Callable[[BatchProgress], None]] = None,
    ) -> BatchJob:
        """Execute a batch job.

        Args:
            job_id: Job ID
            progress_callback: Progress callback function

        Returns:
            Completed batch job
        """
        # Get job
        job = self._get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        if job.status != BatchStatus.PENDING:
            raise ValueError(f"Job {job_id} is not in PENDING status")

        # Create progress callback
        callback = None
        if progress_callback:
            callback = ProgressCallback(progress_callback)

        # Update job status
        job.status = BatchStatus.RUNNING
        job.start_time = datetime.utcnow()
        job.update_progress()

        if callback:
            await callback(job)

        try:
            # Execute operations based on type
            if job.operation_type == OperationType.UPLOAD:
                await self._execute_upload_operations(job, callback)
            elif job.operation_type == OperationType.DOWNLOAD:
                await self._execute_download_operations(job, callback)
            elif job.operation_type == OperationType.DELETE:
                await self._execute_delete_operations(job, callback)
            elif job.operation_type == OperationType.MOVE:
                await self._execute_move_operations(job, callback)
            elif job.operation_type == OperationType.COPY:
                await self._execute_copy_operations(job, callback)
            elif job.operation_type == OperationType.UPDATE:
                await self._execute_update_operations(job, callback)
            elif job.operation_type == OperationType.CONVERT:
                await self._execute_convert_operations(job, callback)
            elif job.operation_type == OperationType.COMPRESS:
                await self._execute_compress_operations(job, callback)
            elif job.operation_type == OperationType.EXTRACT:
                await self._execute_extract_operations(job, callback)
            else:
                raise ValueError(f"Unsupported operation type: {job.operation_type}")

            # Update final job status
            job.end_time = datetime.utcnow()
            if job.start_time:
                job.duration_seconds = (job.end_time - job.start_time).total_seconds()

            job.update_progress()

            # Update stats
            if job.status == BatchStatus.COMPLETED:
                self.operation_stats["completed_jobs"] += 1
                self.operation_stats["successful_operations"] += job.completed_operations
            else:
                self.operation_stats["failed_jobs"] += 1
                self.operation_stats["failed_operations"] += job.failed_operations

            if callback:
                await callback(job)

            logger.info(f"Completed batch job {job_id} with status {job.status.value}")
            return job

        except Exception as e:
            logger.error(f"Error executing batch job {job_id}: {str(e)}")
            job.status = BatchStatus.FAILED
            job.end_time = datetime.utcnow()
            job.update_progress()

            self.operation_stats["failed_jobs"] += 1
            self.operation_stats["failed_operations"] += job.failed_operations

            if callback:
                await callback(job)

            raise

    async def cancel_batch_job(self, job_id: str) -> bool:
        """Cancel a batch job.

        Args:
            job_id: Job ID

        Returns:
            True if cancelled successfully
        """
        job = self._get_job(job_id)
        if not job:
            return False

        if job.status not in [BatchStatus.PENDING, BatchStatus.RUNNING]:
            return False

        job.status = BatchStatus.CANCELLED
        job.end_time = datetime.utcnow()
        job.update_progress()

        logger.info(f"Cancelled batch job {job_id}")
        return True

    def get_batch_job(self, job_id: str) -> Optional[BatchJob]:
        """Get batch job information.

        Args:
            job_id: Job ID

        Returns:
            Batch job or None if not found
        """
        return self._get_job(job_id)

    def list_batch_jobs(
        self,
        status: Optional[BatchStatus] = None,
        operation_type: Optional[OperationType] = None,
        limit: int = 100,
    ) -> List[BatchJob]:
        """List batch jobs.

        Args:
            status: Filter by status
            operation_type: Filter by operation type
            limit: Maximum number of jobs to return

        Returns:
            List of batch jobs
        """
        with self.job_lock:
            jobs = list(self.active_jobs.values())

        # Apply filters
        if status:
            jobs = [job for job in jobs if job.status == status]

        if operation_type:
            jobs = [job for job in jobs if job.operation_type == operation_type]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit
        return jobs[:limit]

    def get_batch_job_results(self, job_id: str) -> List[BatchOperationResult]:
        """Get batch job operation results.

        Args:
            job_id: Job ID

        Returns:
            List of operation results
        """
        job = self._get_job(job_id)
        if not job:
            return []

        return job.operation_results

    def cleanup_completed_jobs(self, older_than_hours: int = 24) -> int:
        """Clean up completed jobs.

        Args:
            older_than_hours: Remove jobs older than this many hours

        Returns:
            Number of jobs cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        jobs_to_remove = []

        with self.job_lock:
            for job_id, job in self.active_jobs.items():
                if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
                    if job.updated_at < cutoff_time:
                        jobs_to_remove.append(job_id)

        for job_id in jobs_to_remove:
            with self.job_lock:
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]

        logger.info(f"Cleaned up {len(jobs_to_remove)} completed jobs")
        return len(jobs_to_remove)

    def get_operation_statistics(self) -> Dict[str, Any]:
        """Get operation statistics.

        Returns:
            Dictionary with operation statistics
        """
        with self.job_lock:
            active_count = len([job for job in self.active_jobs.values() if job.status == BatchStatus.RUNNING])

        success_rate = 0.0
        if self.operation_stats["total_operations"] > 0:
            success_rate = (
                self.operation_stats["successful_operations"] / self.operation_stats["total_operations"]
            ) * 100

        return {
            **self.operation_stats,
            "active_jobs": active_count,
            "success_rate_percent": round(success_rate, 2),
        }

    # Private methods

    def _get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job from active jobs."""
        with self.job_lock:
            return self.active_jobs.get(job_id)

    async def _execute_operation_with_limit(
        self,
        operations: List[BatchOperationResult],
        operation_func: Callable,
        job: BatchJob,
        callback: Optional[ProgressCallback],
        max_concurrent: Optional[int] = None,
    ):
        """Execute operations with concurrency limit.

        Args:
            operations: List of operation results
            operation_func: Function to execute for each operation
            job: Batch job
            callback: Progress callback
            max_concurrent: Maximum concurrent operations
        """
        semaphore = asyncio.Semaphore(max_concurrent or self.max_concurrent_operations)

        async def execute_with_semaphore(operation: BatchOperationResult):
            async with semaphore:
                return await operation_func(operation)

        # Execute operations concurrently
        tasks = [execute_with_semaphore(op) for op in operations]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_upload_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute upload operations."""
        async def upload_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock upload logic
                await asyncio.sleep(0.1)  # Simulate upload time

                operation.status = OperationStatus.COMPLETED
                operation.success = True
                operation.bytes_processed = 1024 * 1024  # 1 MB

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            upload_operation,
            job,
            callback,
        )

    async def _execute_download_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute download operations."""
        async def download_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock download logic
                await asyncio.sleep(0.1)  # Simulate download time

                operation.status = OperationStatus.COMPLETED
                operation.success = True
                operation.bytes_processed = 512 * 1024  # 512 KB

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            download_operation,
            job,
            callback,
        )

    async def _execute_delete_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute delete operations."""
        async def delete_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock delete logic
                await asyncio.sleep(0.05)  # Simulate delete time

                operation.status = OperationStatus.COMPLETED
                operation.success = True

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            delete_operation,
            job,
            callback,
            max_concurrent=self.max_concurrent_operations * 2,  # Delete can be faster
        )

    async def _execute_move_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute move operations."""
        async def move_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock move logic
                await asyncio.sleep(0.1)  # Simulate move time

                operation.status = OperationStatus.COMPLETED
                operation.success = True

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            move_operation,
            job,
            callback,
        )

    async def _execute_copy_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute copy operations."""
        async def copy_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock copy logic
                await asyncio.sleep(0.2)  # Simulate copy time

                operation.status = OperationStatus.COMPLETED
                operation.success = True
                operation.bytes_processed = 2 * 1024 * 1024  # 2 MB

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            copy_operation,
            job,
            callback,
        )

    async def _execute_update_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute update operations."""
        async def update_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock update logic
                await asyncio.sleep(0.1)  # Simulate update time

                operation.status = OperationStatus.COMPLETED
                operation.success = True

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            update_operation,
            job,
            callback,
        )

    async def _execute_convert_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute convert operations."""
        async def convert_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock convert logic
                await asyncio.sleep(0.5)  # Simulate conversion time

                operation.status = OperationStatus.COMPLETED
                operation.success = True

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            convert_operation,
            job,
            callback,
            max_concurrent=max(1, self.max_concurrent_operations // 2),  # Conversion is CPU-intensive
        )

    async def _execute_compress_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute compress operations."""
        async def compress_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock compress logic
                await asyncio.sleep(0.3)  # Simulate compression time

                operation.status = OperationStatus.COMPLETED
                operation.success = True

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            compress_operation,
            job,
            callback,
        )

    async def _execute_extract_operations(
        self,
        job: BatchJob,
        callback: Optional[ProgressCallback],
    ):
        """Execute extract operations."""
        async def extract_operation(operation: BatchOperationResult):
            try:
                operation.status = OperationStatus.RUNNING
                operation.start_time = datetime.utcnow()

                # Mock extract logic
                await asyncio.sleep(0.4)  # Simulate extraction time

                operation.status = OperationStatus.COMPLETED
                operation.success = True

                job.completed_operations += 1

            except Exception as e:
                operation.status = OperationStatus.FAILED
                operation.success = False
                operation.error_message = str(e)
                job.failed_operations += 1

            finally:
                operation.end_time = datetime.utcnow()
                if operation.start_time:
                    operation.duration_seconds = (operation.end_time - operation.start_time).total_seconds()

                job.update_progress()
                if callback:
                    await callback(job)

        await self._execute_operation_with_limit(
            job.operation_results,
            extract_operation,
            job,
            callback,
        )
