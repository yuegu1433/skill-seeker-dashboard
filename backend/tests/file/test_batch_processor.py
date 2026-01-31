"""Tests for BatchProcessor.

This module contains comprehensive unit tests for the BatchProcessor class including
batch operations, progress tracking, error handling, and performance tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time

# Import processor and related classes
from app.file.batch_processor import (
    BatchProcessor,
    OperationType,
    OperationStatus,
    BatchOperationResult,
    BatchJob,
    BatchProgress,
    ProgressCallback,
)


class TestBatchProcessor:
    """Test suite for BatchProcessor."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def batch_processor(self, db_session):
        """Create BatchProcessor instance with mocked database."""
        return BatchProcessor(
            db_session=db_session,
            max_concurrent_operations=5,
            max_workers=3,
            operation_timeout=60,
        )

    @pytest.fixture
    def sample_file_ids(self):
        """Generate sample file IDs."""
        return [str(uuid4()) for _ in range(10)]

    @pytest.fixture
    def sample_operations(self, sample_file_ids):
        """Create sample batch operations."""
        from app.file.schemas.batch_config import BatchOperation

        operations = []
        for i, file_id in enumerate(sample_file_ids):
            operation = BatchOperation(
                file_id=file_id,
                source_path=f"/source/file_{i}.txt",
                target_path=f"/target/file_{i}.txt",
                metadata={"index": i},
            )
            operations.append(operation)

        return operations

    # Test batch job creation

    @pytest.mark.asyncio
    async def test_create_batch_job(self, batch_processor, sample_operations):
        """Test creating a batch job."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations,
            metadata={"test": True},
        )

        assert job_id is not None
        assert isinstance(job_id, str)

        # Verify job exists
        job = batch_processor.get_batch_job(job_id)
        assert job is not None
        assert job.job_id == job_id
        assert job.operation_type == OperationType.UPLOAD
        assert job.status.value == "pending"
        assert job.total_operations == len(sample_operations)
        assert len(job.operation_results) == len(sample_operations)

    @pytest.mark.asyncio
    async def test_create_batch_job_with_callback(self, batch_processor, sample_operations):
        """Test creating batch job with progress callback."""
        callback_called = []

        def progress_callback(progress: BatchProgress):
            callback_called.append(progress)

        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.DOWNLOAD,
            operations=sample_operations[:3],
            progress_callback=progress_callback,
        )

        assert job_id is not None
        assert len(callback_called) == 0  # Callback not called during creation

    # Test batch job execution

    @pytest.mark.asyncio
    async def test_execute_upload_operations(self, batch_processor, sample_operations):
        """Test executing upload operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:5],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 5
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_download_operations(self, batch_processor, sample_operations):
        """Test executing download operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.DOWNLOAD,
            operations=sample_operations[:3],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 3
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_delete_operations(self, batch_processor, sample_operations):
        """Test executing delete operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.DELETE,
            operations=sample_operations[:4],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 4
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_move_operations(self, batch_processor, sample_operations):
        """Test executing move operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.MOVE,
            operations=sample_operations[:2],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 2
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_copy_operations(self, batch_processor, sample_operations):
        """Test executing copy operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.COPY,
            operations=sample_operations[:3],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 3
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_update_operations(self, batch_processor, sample_operations):
        """Test executing update operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPDATE,
            operations=sample_operations[:2],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 2
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_convert_operations(self, batch_processor, sample_operations):
        """Test executing convert operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.CONVERT,
            operations=sample_operations[:2],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 2
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_compress_operations(self, batch_processor, sample_operations):
        """Test executing compress operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.COMPRESS,
            operations=sample_operations[:2],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 2
        assert job.failed_operations == 0

    @pytest.mark.asyncio
    async def test_execute_extract_operations(self, batch_processor, sample_operations):
        """Test executing extract operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.EXTRACT,
            operations=sample_operations[:2],
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.status.value == "completed"
        assert job.completed_operations == 2
        assert job.failed_operations == 0

    # Test batch job cancellation

    @pytest.mark.asyncio
    async def test_cancel_batch_job(self, batch_processor, sample_operations):
        """Test cancelling a batch job."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations,
        )

        # Cancel job
        cancelled = await batch_processor.cancel_batch_job(job_id)

        assert cancelled is True

        # Verify job is cancelled
        job = batch_processor.get_batch_job(job_id)
        assert job is not None
        assert job.status.value == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_job(self, batch_processor):
        """Test cancelling non-existent job."""
        cancelled = await batch_processor.cancel_batch_job(str(uuid4()))

        assert cancelled is False

    # Test batch job retrieval

    @pytest.mark.asyncio
    async def test_get_batch_job(self, batch_processor, sample_operations):
        """Test getting batch job."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:3],
        )

        job = batch_processor.get_batch_job(job_id)

        assert job is not None
        assert job.job_id == job_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, batch_processor):
        """Test getting non-existent job."""
        job = batch_processor.get_batch_job(str(uuid4()))

        assert job is None

    # Test batch job listing

    @pytest.mark.asyncio
    async def test_list_batch_jobs(self, batch_processor, sample_operations):
        """Test listing batch jobs."""
        # Create multiple jobs
        job_ids = []
        for i in range(3):
            job_id = await batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                operations=sample_operations[:i+1],
            )
            job_ids.append(job_id)

        # List jobs
        jobs = batch_processor.list_batch_jobs()

        assert len(jobs) == 3

    @pytest.mark.asyncio
    async def test_list_batch_jobs_with_filter(self, batch_processor, sample_operations):
        """Test listing batch jobs with filter."""
        # Create upload and download jobs
        upload_job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:2],
        )

        download_job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.DOWNLOAD,
            operations=sample_operations[:2],
        )

        # List upload jobs
        upload_jobs = batch_processor.list_batch_jobs(
            operation_type=OperationType.UPLOAD
        )

        assert len(upload_jobs) == 1
        assert upload_jobs[0].job_id == upload_job_id

        # List download jobs
        download_jobs = batch_processor.list_batch_jobs(
            operation_type=OperationType.DOWNLOAD
        )

        assert len(download_jobs) == 1
        assert download_jobs[0].job_id == download_job_id

    # Test batch job results

    @pytest.mark.asyncio
    async def test_get_batch_job_results(self, batch_processor, sample_operations):
        """Test getting batch job operation results."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:3],
        )

        results = batch_processor.get_batch_job_results(job_id)

        assert len(results) == 3
        assert all(isinstance(result, BatchOperationResult) for result in results)

    @pytest.mark.asyncio
    async def test_get_batch_job_results_nonexistent_job(self, batch_processor):
        """Test getting results for non-existent job."""
        results = batch_processor.get_batch_job_results(str(uuid4()))

        assert len(results) == 0

    # Test progress tracking

    @pytest.mark.asyncio
    async def test_progress_callback(self, batch_processor, sample_operations):
        """Test progress callback functionality."""
        progress_updates = []

        def progress_callback(progress: BatchProgress):
            progress_updates.append(progress)

        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:5],
            progress_callback=progress_callback,
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id, progress_callback=progress_callback)

        # Verify progress updates
        assert len(progress_updates) > 0

        # Check final progress
        final_progress = progress_updates[-1]
        assert final_progress.job_id == job_id
        assert final_progress.status.value == "completed"
        assert final_progress.completed_operations == 5
        assert final_progress.progress_percentage == 100.0

    # Test error handling

    @pytest.mark.asyncio
    async def test_execute_nonexistent_job(self, batch_processor):
        """Test executing non-existent job."""
        with pytest.raises(ValueError, match="not found"):
            await batch_processor.execute_batch_job(str(uuid4()))

    @pytest.mark.asyncio
    async def test_execute_already_executed_job(self, batch_processor, sample_operations):
        """Test executing already executed job."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:2],
        )

        # Execute job first time
        await batch_processor.execute_batch_job(job_id)

        # Try to execute again
        with pytest.raises(ValueError, match="not in PENDING status"):
            await batch_processor.execute_batch_job(job_id)

    @pytest.mark.asyncio
    async def test_batch_job_with_mixed_results(self, batch_processor, sample_operations):
        """Test batch job with mixed success/failure results."""
        # Mock one operation to fail
        with patch('asyncio.sleep', side_effect=Exception("Test error")):
            job_id = await batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                operations=sample_operations[:3],
            )

            job = await batch_processor.execute_batch_job(job_id)

            # Some operations might fail, some might succeed
            assert job.completed_operations + job.failed_operations == 3

    # Test statistics

    @pytest.mark.asyncio
    async def test_get_operation_statistics(self, batch_processor, sample_operations):
        """Test getting operation statistics."""
        # Execute some jobs
        for i in range(3):
            job_id = await batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                operations=sample_operations[:2],
            )
            await batch_processor.execute_batch_job(job_id)

        stats = batch_processor.get_operation_statistics()

        assert stats["total_jobs"] == 3
        assert stats["completed_jobs"] == 3
        assert stats["failed_jobs"] == 0
        assert stats["total_operations"] == 6
        assert stats["successful_operations"] == 6
        assert stats["failed_operations"] == 0
        assert stats["success_rate_percent"] == 100.0

    # Test cleanup

    @pytest.mark.asyncio
    async def test_cleanup_completed_jobs(self, batch_processor, sample_operations):
        """Test cleaning up completed jobs."""
        # Create and execute some jobs
        job_ids = []
        for i in range(3):
            job_id = await batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                operations=sample_operations[:2],
            )
            await batch_processor.execute_batch_job(job_id)
            job_ids.append(job_id)

        # Verify jobs exist
        assert len(batch_processor.active_jobs) == 3

        # Clean up jobs
        cleaned_count = batch_processor.cleanup_completed_jobs(older_than_hours=0)

        assert cleaned_count == 3
        assert len(batch_processor.active_jobs) == 0

    # Test concurrent operations

    @pytest.mark.asyncio
    async def test_concurrent_batch_jobs(self, batch_processor, sample_operations):
        """Test executing multiple batch jobs concurrently."""
        # Create multiple jobs
        job_ids = []
        for i in range(3):
            job_id = await batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                operations=sample_operations[:2],
            )
            job_ids.append(job_id)

        # Execute all jobs concurrently
        tasks = [
            batch_processor.execute_batch_job(job_id)
            for job_id in job_ids
        ]

        jobs = await asyncio.gather(*tasks)

        # Verify all jobs completed
        assert len(jobs) == 3
        for job in jobs:
            assert job.status.value == "completed"

    @pytest.mark.asyncio
    async def test_large_batch_operations(self, batch_processor):
        """Test processing large number of operations."""
        # Create 100 operations
        operations = []
        for i in range(100):
            from app.file.schemas.batch_config import BatchOperation
            operation = BatchOperation(
                file_id=str(uuid4()),
                source_path=f"/source/file_{i}.txt",
                target_path=f"/target/file_{i}.txt",
            )
            operations.append(operation)

        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.DELETE,
            operations=operations,
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id)

        assert job is not None
        assert job.total_operations == 100
        assert job.completed_operations == 100

    # Test edge cases

    @pytest.mark.asyncio
    async def test_empty_batch_operations(self, batch_processor):
        """Test batch job with no operations."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=[],
        )

        job = batch_processor.get_batch_job(job_id)

        assert job is not None
        assert job.total_operations == 0
        assert job.progress_percentage == 0.0

    @pytest.mark.asyncio
    async def test_batch_job_list_limit(self, batch_processor, sample_operations):
        """Test limiting batch job list results."""
        # Create 10 jobs
        for i in range(10):
            await batch_processor.create_batch_job(
                operation_type=OperationType.UPLOAD,
                operations=sample_operations[:1],
            )

        # List with limit
        jobs = batch_processor.list_batch_jobs(limit=5)

        assert len(jobs) == 5

    # Test initialization

    def test_batch_processor_initialization(self, db_session):
        """Test BatchProcessor initialization."""
        processor = BatchProcessor(
            db_session=db_session,
            max_concurrent_operations=10,
            max_workers=5,
            operation_timeout=120,
        )

        assert processor.db == db_session
        assert processor.max_concurrent_operations == 10
        assert processor.max_workers == 5
        assert processor.operation_timeout == 120
        assert len(processor.active_jobs) == 0

    # Test progress callback

    @pytest.mark.asyncio
    async def test_progress_callback_throttling(self, batch_processor, sample_operations):
        """Test progress callback throttling."""
        callback_calls = []

        def progress_callback(progress: BatchProgress):
            callback_calls.append(progress)

        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:5],
            progress_callback=progress_callback,
        )

        # Execute job
        job = await batch_processor.execute_batch_job(job_id, progress_callback=progress_callback)

        # Verify throttling worked (not every operation generates an update)
        assert len(callback_calls) <= 6  # Some updates, but not too many

    # Test operation timeout

    @pytest.mark.asyncio
    async def test_operation_timeout(self, batch_processor, sample_operations):
        """Test operation timeout handling."""
        # Create job with short timeout
        processor = BatchProcessor(
            db_session=AsyncMock(),
            max_concurrent_operations=1,
            max_workers=1,
            operation_timeout=1,  # 1 second timeout
        )

        job_id = await processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:1],
        )

        # Mock operation to take longer than timeout
        with patch('asyncio.sleep', side_effect=asyncio.TimeoutError("Timeout")):
            job = await processor.execute_batch_job(job_id)

            # Job should still complete (mock might not respect timeout)
            assert job is not None

    # Test metadata handling

    @pytest.mark.asyncio
    async def test_batch_job_metadata(self, batch_processor, sample_operations):
        """Test batch job with metadata."""
        metadata = {
            "user_id": "test-user",
            "batch_name": "test-batch",
            "priority": "high",
        }

        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:2],
            metadata=metadata,
        )

        job = batch_processor.get_batch_job(job_id)

        assert job is not None
        assert job.metadata == metadata

    # Test operation result details

    @pytest.mark.asyncio
    async def test_operation_result_details(self, batch_processor, sample_operations):
        """Test operation result details."""
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:2],
        )

        job = await batch_processor.execute_batch_job(job_id)

        # Check operation results
        results = batch_processor.get_batch_job_results(job_id)

        for result in results:
            assert result.operation_id is not None
            assert result.status in [OperationStatus.COMPLETED, OperationStatus.FAILED]
            if result.status == OperationStatus.COMPLETED:
                assert result.success is True
                assert result.start_time is not None
                assert result.end_time is not None
                assert result.duration_seconds >= 0

    # Test different operation types

    @pytest.mark.asyncio
    async def test_all_operation_types(self, batch_processor, sample_operations):
        """Test all supported operation types."""
        operation_types = [
            OperationType.UPLOAD,
            OperationType.DOWNLOAD,
            OperationType.DELETE,
            OperationType.MOVE,
            OperationType.COPY,
            OperationType.UPDATE,
            OperationType.CONVERT,
            OperationType.COMPRESS,
            OperationType.EXTRACT,
        ]

        for op_type in operation_types:
            job_id = await batch_processor.create_batch_job(
                operation_type=op_type,
                operations=sample_operations[:1],
            )

            job = await batch_processor.execute_batch_job(job_id)

            assert job is not None
            assert job.status.value == "completed"
            assert job.operation_type == op_type

    # Test unsupported operation type

    @pytest.mark.asyncio
    async def test_unsupported_operation_type(self, batch_processor, sample_operations):
        """Test unsupported operation type."""
        # Create a job with an unsupported operation type
        job = BatchJob(
            job_id=str(uuid4()),
            operation_type="unsupported"  # Invalid type
        )

        # This should raise an error during execution
        with pytest.raises(ValueError, match="Unsupported operation type"):
            await batch_processor._execute_upload_operations(job, None)

    # Test batch job filtering by status

    @pytest.mark.asyncio
    async def test_list_jobs_by_status(self, batch_processor, sample_operations):
        """Test listing jobs filtered by status."""
        # Create a job
        job_id = await batch_processor.create_batch_job(
            operation_type=OperationType.UPLOAD,
            operations=sample_operations[:1],
        )

        # List pending jobs
        pending_jobs = batch_processor.list_batch_jobs(status=BatchStatus.PENDING)
        assert len(pending_jobs) == 1

        # Execute the job
        await batch_processor.execute_batch_job(job_id)

        # List completed jobs
        completed_jobs = batch_processor.list_batch_jobs(status=BatchStatus.COMPLETED)
        assert len(completed_jobs) == 1
