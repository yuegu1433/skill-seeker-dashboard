"""Tests for Celery storage tasks.

This module contains unit tests for the Celery tasks used in storage operations,
testing task execution, status tracking, and error handling.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from celery import Celery
from celery.result import AsyncResult

from backend.app.storage.tasks.monitor import (
    StorageTaskMonitor,
    TaskStatus,
    TaskMetrics,
)


class TestTaskMetrics:
    """Test suite for TaskMetrics."""

    def test_initialization(self):
        """Test task metrics initialization."""
        metrics = TaskMetrics()

        assert metrics.total_tasks == 0
        assert metrics.successful_tasks == 0
        assert metrics.failed_tasks == 0
        assert metrics.retried_tasks == 0
        assert metrics.revoked_tasks == 0
        assert len(metrics.start_times) == 0
        assert len(metrics.end_times) == 0
        assert len(metrics.durations) == 0
        assert len(metrics.error_counts) == 0
        assert len(metrics.task_types) == 0

    def test_record_task_start(self):
        """Test recording task start."""
        metrics = TaskMetrics()

        metrics.record_task_start("task1", "upload")

        assert "task1" in metrics.start_times
        assert metrics.task_types["upload"] == 1

    def test_record_task_end_success(self):
        """Test recording successful task end."""
        metrics = TaskMetrics()

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=10)

        metrics.record_task_start("task1", "upload")
        metrics.record_task_end("task1", TaskStatus.SUCCESS, 10.0)

        assert metrics.total_tasks == 1
        assert metrics.successful_tasks == 1
        assert metrics.failed_tasks == 0
        assert metrics.durations["task1"] == 10.0

    def test_record_task_end_failure(self):
        """Test recording failed task end."""
        metrics = TaskMetrics()

        metrics.record_task_start("task1", "upload")
        metrics.record_task_end("task1", TaskStatus.FAILURE, 10.0, "Test error")

        assert metrics.total_tasks == 1
        assert metrics.successful_tasks == 0
        assert metrics.failed_tasks == 1
        assert metrics.error_counts["Test error"] == 1

    def test_get_success_rate(self):
        """Test getting success rate."""
        metrics = TaskMetrics()

        # No tasks
        assert metrics.get_success_rate() == 0.0

        # All successful
        metrics.total_tasks = 5
        metrics.successful_tasks = 5
        assert metrics.get_success_rate() == 100.0

        # Partial success
        metrics.total_tasks = 10
        metrics.successful_tasks = 7
        assert metrics.get_success_rate() == 70.0

    def test_get_average_duration(self):
        """Test getting average duration."""
        metrics = TaskMetrics()

        # No durations
        assert metrics.get_average_duration() == 0.0

        # With durations
        metrics.durations["task1"] = 10.0
        metrics.durations["task2"] = 20.0
        metrics.durations["task3"] = 30.0

        assert metrics.get_average_duration() == 20.0

    def test_get_median_duration(self):
        """Test getting median duration."""
        metrics = TaskMetrics()

        # No durations
        assert metrics.get_median_duration() == 0.0

        # Odd number of durations
        metrics.durations["task1"] = 10.0
        metrics.durations["task2"] = 20.0
        metrics.durations["task3"] = 30.0

        assert metrics.get_median_duration() == 20.0

        # Even number of durations
        metrics.durations["task4"] = 40.0
        assert metrics.get_median_duration() == 25.0

    def test_get_error_summary(self):
        """Test getting error summary."""
        metrics = TaskMetrics()

        metrics.error_counts["Error A"] = 5
        metrics.error_counts["Error B"] = 3
        metrics.error_counts["Error C"] = 1

        summary = metrics.get_error_summary()

        assert len(summary) == 3
        assert summary[0]["error"] == "Error A"
        assert summary[0]["count"] == 5
        assert summary[1]["error"] == "Error B"
        assert summary[2]["error"] == "Error C"

    def test_get_task_type_summary(self):
        """Test getting task type summary."""
        metrics = TaskMetrics()

        metrics.task_types["upload"] = 10
        metrics.task_types["backup"] = 5
        metrics.task_types["cleanup"] = 3

        summary = metrics.get_task_type_summary()

        assert len(summary) == 3
        assert summary[0]["task_type"] == "upload"
        assert summary[0]["count"] == 10


class TestStorageTaskMonitor:
    """Test suite for StorageTaskMonitor."""

    @pytest.fixture
    def mock_celery_app(self):
        """Create mock Celery app."""
        app = Mock(spec=Celery)
        app.control = Mock()
        return app

    @pytest.fixture
    def monitor(self, mock_celery_app):
        """Create task monitor."""
        return StorageTaskMonitor(celery_app=mock_celery_app)

    @pytest.fixture
    def test_task_id(self):
        """Create test task ID."""
        return "test-task-id-123"

    def test_initialization(self, mock_celery_app):
        """Test monitor initialization."""
        monitor = StorageTaskMonitor(celery_app=mock_celery_app)

        assert monitor.celery_app == mock_celery_app
        assert isinstance(monitor.metrics, TaskMetrics)
        assert len(monitor.task_history) == 0
        assert len(monitor.active_tasks) == 0
        assert monitor.max_history_size == 10000

    def test_get_task_status(self, monitor, mock_celery_app, test_task_id):
        """Test getting task status."""
        # Mock AsyncResult
        mock_result = Mock(spec=AsyncResult)
        mock_result.status = TaskStatus.SUCCESS
        mock_result.ready.return_value = True
        mock_result.result = {"file_path": "test.txt"}
        mock_result.failed.return_value = False
        mock_result.traceback = None
        mock_result.info = {}

        with patch.object(monitor.celery_app, 'AsyncResult', return_value=mock_result):
            status = monitor.get_task_status(test_task_id)

            assert status["task_id"] == test_task_id
            assert status["status"] == TaskStatus.SUCCESS
            assert status["result"]["file_path"] == "test.txt"

    def test_get_task_status_error(self, monitor, mock_celery_app, test_task_id):
        """Test getting task status with error."""
        # Mock AsyncResult to raise exception
        with patch.object(monitor.celery_app, 'AsyncResult', side_effect=Exception("Test error")):
            status = monitor.get_task_status(test_task_id)

            assert status["task_id"] == test_task_id
            assert status["status"] == TaskStatus.UNKNOWN
            assert "Test error" in status["error"]

    def test_get_active_tasks(self, monitor, mock_celery_app):
        """Test getting active tasks."""
        # Add active task
        monitor.active_tasks["task1"] = {
            "task_id": "task1",
            "task_type": "upload",
            "start_time": datetime.utcnow(),
            "status": TaskStatus.RUNNING,
        }

        # Mock AsyncResult to return running status
        mock_result = Mock(spec=AsyncResult)
        mock_result.status = TaskStatus.RUNNING
        mock_result.ready.return_value = False
        mock_result.result = None
        mock_result.failed.return_value = False
        mock_result.traceback = None
        mock_result.info = {}

        with patch.object(monitor.celery_app, 'AsyncResult', return_value=mock_result):
            active = monitor.get_active_tasks()

            assert len(active) == 1
            assert active[0]["task_id"] == "task1"
            assert active[0]["task_type"] == "upload"

    def test_get_active_tasks_finished(self, monitor, mock_celery_app):
        """Test getting active tasks with finished tasks."""
        # Add finished task
        monitor.active_tasks["task1"] = {
            "task_id": "task1",
            "task_type": "upload",
            "start_time": datetime.utcnow(),
            "status": TaskStatus.SUCCESS,
        }

        # Mock AsyncResult to return success status
        mock_result = Mock(spec=AsyncResult)
        mock_result.status = TaskStatus.SUCCESS
        mock_result.ready.return_value = True
        mock_result.result = {"file_path": "test.txt"}
        mock_result.failed.return_value = True
        mock_result.traceback = None
        mock_result.info = {}

        with patch.object(monitor.celery_app, 'AsyncResult', return_value=mock_result):
            active = monitor.get_active_tasks()

            assert len(active) == 0  # Finished task removed
            assert "task1" not in monitor.active_tasks

    def test_get_task_history(self, monitor):
        """Test getting task history."""
        # Add history records
        history_record = {
            "task_id": "task1",
            "task_type": "upload",
            "status": TaskStatus.SUCCESS,
            "start_time": datetime.utcnow(),
            "end_time": datetime.utcnow(),
            "duration_seconds": 10.0,
        }
        monitor.add_to_history(history_record)

        # Get history
        history = monitor.get_task_history()

        assert len(history) == 1
        assert history[0]["task_id"] == "task1"

    def test_get_task_history_with_filters(self, monitor):
        """Test getting task history with filters."""
        # Add history records
        monitor.add_to_history({
            "task_id": "task1",
            "task_type": "upload",
            "status": TaskStatus.SUCCESS,
            "start_time": datetime.utcnow(),
        })

        monitor.add_to_history({
            "task_id": "task2",
            "task_type": "backup",
            "status": TaskStatus.FAILURE,
            "start_time": datetime.utcnow(),
        })

        # Filter by task type
        upload_history = monitor.get_task_history(task_type="upload")
        assert len(upload_history) == 1
        assert upload_history[0]["task_type"] == "upload"

        # Filter by status
        success_history = monitor.get_task_history(status=TaskStatus.SUCCESS)
        assert len(success_history) == 1
        assert success_history[0]["status"] == TaskStatus.SUCCESS

    def test_get_metrics(self, monitor):
        """Test getting metrics."""
        # Record some tasks
        monitor.metrics.record_task_start("task1", "upload")
        monitor.metrics.record_task_end("task1", TaskStatus.SUCCESS, 10.0)

        monitor.metrics.record_task_start("task2", "backup")
        monitor.metrics.record_task_end("task2", TaskStatus.FAILURE, 20.0, "Test error")

        metrics = monitor.get_metrics()

        assert metrics["total_tasks"] == 2
        assert metrics["successful_tasks"] == 1
        assert metrics["failed_tasks"] == 1
        assert metrics["success_rate_percent"] == 50.0
        assert metrics["average_duration_seconds"] == 15.0

    def test_monitor_task(self, monitor, test_task_id):
        """Test monitoring a task."""
        monitor.monitor_task(test_task_id, "upload", datetime.utcnow())

        assert test_task_id in monitor.active_tasks
        assert monitor.active_tasks[test_task_id]["task_type"] == "upload"
        assert monitor.active_tasks[test_task_id]["status"] == TaskStatus.RUNNING
        assert "task1" in monitor.metrics.start_times

    def test_update_task_status(self, monitor, test_task_id):
        """Test updating task status."""
        # Start monitoring
        monitor.monitor_task(test_task_id, "upload", datetime.utcnow())

        # Update status
        monitor.update_task_status(
            test_task_id,
            TaskStatus.SUCCESS,
            result={"file_path": "test.txt"},
            duration=10.0,
        )

        # Check metrics
        assert monitor.metrics.total_tasks == 1
        assert monitor.metrics.successful_tasks == 1
        assert monitor.metrics.durations[test_task_id] == 10.0

        # Check history
        assert len(monitor.task_history) == 1
        assert monitor.task_history[0]["task_id"] == test_task_id
        assert monitor.task_history[0]["status"] == TaskStatus.SUCCESS

        # Check active tasks
        assert test_task_id not in monitor.active_tasks

    def test_add_to_history(self, monitor):
        """Test adding to history."""
        record = {
            "task_id": "task1",
            "task_type": "upload",
            "status": TaskStatus.SUCCESS,
            "start_time": datetime.utcnow(),
        }

        monitor.add_to_history(record)

        assert len(monitor.task_history) == 1
        assert monitor.task_history[0]["task_id"] == "task1"

    def test_add_to_history_max_size(self, monitor):
        """Test history size limit."""
        # Add many records
        for i in range(monitor.max_history_size + 10):
            record = {
                "task_id": f"task{i}",
                "task_type": "upload",
                "status": TaskStatus.SUCCESS,
                "start_time": datetime.utcnow(),
            }
            monitor.add_to_history(record)

        # Should be limited to max size
        assert len(monitor.task_history) == monitor.max_history_size

    def test_get_pending_tasks(self, monitor, mock_celery_app):
        """Test getting pending tasks."""
        # Mock inspect
        mock_inspect = Mock()
        mock_inspect.active.return_value = {
            "worker1": [
                {
                    "id": "task1",
                    "name": "storage.upload_file",
                    "args": [],
                    "kwargs": {},
                    "time_start": 1234567890.0,
                    "hostname": "worker1@hostname",
                }
            ]
        }

        mock_celery_app.control.inspect.return_value = mock_inspect

        pending = monitor.get_pending_tasks()

        assert len(pending) == 1
        assert pending[0]["task_id"] == "task1"
        assert pending[0]["task_name"] == "storage.upload_file"

    def test_get_worker_status(self, monitor, mock_celery_app):
        """Test getting worker status."""
        # Mock inspect
        mock_inspect = Mock()
        mock_inspect.stats.return_value = {
            "worker1": {
                "total": {"tasks": 100},
                "pool": {"processes": 4},
            }
        }
        mock_inspect.active.return_value = {"worker1": []}
        mock_inspect.scheduled.return_value = {"worker1": []}
        mock_inspect.reserved.return_value = {"worker1": []}

        mock_celery_app.control.inspect.return_value = mock_inspect

        status = monitor.get_worker_status()

        assert "worker1" in status
        assert status["worker1"]["status"] == "online"
        assert status["worker1"]["active_count"] == 0

    def test_get_task_statistics(self, monitor):
        """Test getting task statistics."""
        # Add recent history
        now = datetime.utcnow()

        for i in range(10):
            record = {
                "task_id": f"task{i}",
                "task_type": "upload",
                "status": TaskStatus.SUCCESS if i < 7 else TaskStatus.FAILURE,
                "start_time": now - timedelta(minutes=i),
                "end_time": now - timedelta(minutes=i) + timedelta(seconds=10),
                "duration_seconds": 10.0,
            }
            monitor.add_to_history(record)

        stats = monitor.get_task_statistics(time_range_hours=1)

        assert stats["time_range_hours"] == 1
        assert stats["total_tasks"] == 10
        assert stats["successful_tasks"] == 7
        assert stats["failed_tasks"] == 3
        assert stats["success_rate_percent"] == 70.0

    def test_cleanup_finished_tasks(self, monitor):
        """Test cleaning up finished tasks."""
        # Add old finished task
        old_time = datetime.utcnow() - timedelta(hours=200)
        monitor.active_tasks["old_task"] = {
            "task_id": "old_task",
            "task_type": "upload",
            "start_time": old_time,
            "status": TaskStatus.SUCCESS,
        }

        # Add recent task
        recent_time = datetime.utcnow() - timedelta(hours=1)
        monitor.active_tasks["recent_task"] = {
            "task_id": "recent_task",
            "task_type": "backup",
            "start_time": recent_time,
            "status": TaskStatus.RUNNING,
        }

        # Cleanup
        cleaned_count = monitor.cleanup_finished_tasks(max_age_hours=168)

        assert cleaned_count == 1
        assert "old_task" not in monitor.active_tasks
        assert "recent_task" in monitor.active_tasks

    def test_reset_metrics(self, monitor):
        """Test resetting metrics."""
        # Add some metrics
        monitor.metrics.record_task_start("task1", "upload")
        monitor.metrics.record_task_end("task1", TaskStatus.SUCCESS, 10.0)

        assert monitor.metrics.total_tasks == 1

        # Reset
        monitor.reset_metrics()

        assert monitor.metrics.total_tasks == 0

    def test_export_metrics(self, monitor):
        """Test exporting metrics."""
        # Add some data
        monitor.metrics.record_task_start("task1", "upload")
        monitor.metrics.record_task_end("task1", TaskStatus.SUCCESS, 10.0)

        exported = monitor.export_metrics()

        assert "metrics" in exported
        assert "active_tasks" in exported
        assert "recent_history" in exported
        assert "worker_status" in exported
        assert "statistics_24h" in exported
        assert "statistics_7d" in exported

        assert exported["metrics"]["total_tasks"] == 1

    # Test global monitor functions
    def test_get_task_monitor(self):
        """Test getting global task monitor."""
        from backend.app.storage.tasks.monitor import get_task_monitor

        monitor = get_task_monitor()

        assert isinstance(monitor, StorageTaskMonitor)

    def test_set_task_monitor(self):
        """Test setting global task monitor."""
        from backend.app.storage.tasks.monitor import get_task_monitor, set_task_monitor

        custom_monitor = StorageTaskMonitor()
        set_task_monitor(custom_monitor)

        retrieved_monitor = get_task_monitor()

        assert retrieved_monitor is custom_monitor

    # Test task status constants
    def test_task_status_constants(self):
        """Test task status constants."""
        assert TaskStatus.PENDING == "PENDING"
        assert TaskStatus.RUNNING == "RUNNING"
        assert TaskStatus.SUCCESS == "SUCCESS"
        assert TaskStatus.FAILURE == "FAILURE"
        assert TaskStatus.RETRY == "RETRY"
        assert TaskStatus.REVOKED == "REVOKED"
        assert TaskStatus.UNKNOWN == "UNKNOWN"

    # Test edge cases
    def test_empty_metrics(self, monitor):
        """Test with empty metrics."""
        metrics = monitor.get_metrics()

        assert metrics["total_tasks"] == 0
        assert metrics["successful_tasks"] == 0
        assert metrics["failed_tasks"] == 0
        assert metrics["success_rate_percent"] == 0.0
        assert metrics["average_duration_seconds"] == 0.0

    def test_large_duration_values(self, monitor):
        """Test with large duration values."""
        monitor.metrics.record_task_start("task1", "upload")
        monitor.metrics.record_task_end("task1", TaskStatus.SUCCESS, 999999.0)

        assert monitor.metrics.durations["task1"] == 999999.0
        assert monitor.metrics.get_average_duration() == 999999.0

    def test_many_error_types(self, monitor):
        """Test with many different error types."""
        for i in range(100):
            monitor.metrics.record_task_start(f"task{i}", "upload")
            monitor.metrics.record_task_end(f"task{i}", TaskStatus.FAILURE, 10.0, f"Error {i}")

        error_summary = monitor.metrics.get_error_summary()

        assert len(error_summary) == 100
        assert all("Error" in error["error"] for error in error_summary)

    def test_concurrent_task_tracking(self, monitor):
        """Test tracking many concurrent tasks."""
        for i in range(1000):
            task_id = f"task{i}"
            monitor.monitor_task(task_id, "upload", datetime.utcnow())
            monitor.update_task_status(
                task_id,
                TaskStatus.SUCCESS if i % 2 == 0 else TaskStatus.FAILURE,
                duration=10.0,
            )

        assert monitor.metrics.total_tasks == 1000
        assert monitor.metrics.successful_tasks == 500
        assert monitor.metrics.failed_tasks == 500
        assert len(monitor.task_history) == 1000
