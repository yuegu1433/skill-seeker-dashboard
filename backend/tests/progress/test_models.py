"""Test cases for progress tracking data models.

This module contains comprehensive unit tests for all progress tracking
data models including TaskProgress, TaskLog, Notification, and ProgressMetric.
"""

import pytest
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from backend.app.progress.models.task import TaskProgress
from backend.app.progress.models.log import TaskLog
from backend.app.progress.models.notification import Notification
from backend.app.progress.models.metric import ProgressMetric


class TestTaskProgress:
    """Test cases for TaskProgress model."""

    def test_task_progress_creation(self):
        """Test TaskProgress model creation."""
        task_progress = TaskProgress(
            task_id="test-task-001",
            user_id="test-user-001",
            task_type="skill_creation",
            task_name="Test Skill Creation",
            description="Test task for skill creation",
            progress=25.0,
            status="running",
            current_step="initializing",
            total_steps=4,
            estimated_duration=300,
            task_metadata={"priority": "high", "tags": ["test", "skill"]},
            tags=["test", "automation"]
        )

        assert task_progress.task_id == "test-task-001"
        assert task_progress.user_id == "test-user-001"
        assert task_progress.task_type == "skill_creation"
        assert task_progress.task_name == "Test Skill Creation"
        assert task_progress.description == "Test task for skill creation"
        assert task_progress.progress == 25.0
        assert task_progress.status == "running"
        assert task_progress.current_step == "initializing"
        assert task_progress.total_steps == 4
        assert task_progress.estimated_duration == 300
        assert task_progress.task_metadata["priority"] == "high"
        assert "test" in task_progress.tags
        assert "automation" in task_progress.tags

    def test_task_progress_default_values(self):
        """Test TaskProgress model default values."""
        task_progress = TaskProgress(
            task_id="test-task-002",
            user_id="test-user-002",
            task_type="file_processing",
            task_name="Test File Processing"
        )

        assert task_progress.progress == 0.0
        assert task_progress.status == "pending"
        assert task_progress.total_steps == 0
        assert task_progress.retry_count == 0
        assert task_progress.view_count == 0
        assert isinstance(task_progress.task_metadata, dict)
        assert isinstance(task_progress.tags, list)
        assert task_progress.result == {}

    def test_task_progress_repr(self):
        """Test TaskProgress string representation."""
        task_progress = TaskProgress(
            task_id="test-task-003",
            user_id="test-user-003",
            task_type="skill_deployment",
            task_name="Test Deployment",
            progress=50.0,
            status="running"
        )

        repr_str = repr(task_progress)
        assert "TaskProgress" in repr_str
        assert "test-task-003" in repr_str
        assert "skill_deployment" in repr_str
        assert "50.0%" in repr_str
        assert "running" in repr_str

    def test_task_progress_status_properties(self):
        """Test TaskProgress status property methods."""
        # Test pending status
        task_pending = TaskProgress(
            task_id="test-task-004",
            user_id="test-user-004",
            task_type="data_analysis",
            task_name="Test Analysis",
            status="pending"
        )
        assert task_pending.is_pending is True
        assert task_pending.is_running is False
        assert task_pending.is_completed is False

        # Test running status
        task_running = TaskProgress(
            task_id="test-task-005",
            user_id="test-user-005",
            task_type="data_analysis",
            task_name="Test Analysis",
            status="running"
        )
        assert task_running.is_pending is False
        assert task_running.is_running is True
        assert task_running.is_completed is False

        # Test completed status
        task_completed = TaskProgress(
            task_id="test-task-006",
            user_id="test-user-006",
            task_type="data_analysis",
            task_name="Test Analysis",
            status="completed"
        )
        assert task_completed.is_pending is False
        assert task_completed.is_running is False
        assert task_completed.is_completed is True

    def test_task_progress_failed_status(self):
        """Test TaskProgress failed status property."""
        task_failed = TaskProgress(
            task_id="test-task-007",
            user_id="test-user-007",
            task_type="data_analysis",
            task_name="Test Analysis",
            status="failed"
        )

        assert task_failed.is_failed is True
        assert task_failed.is_cancelled is False

    def test_task_progress_cancelled_status(self):
        """Test TaskProgress cancelled status property."""
        task_cancelled = TaskProgress(
            task_id="test-task-008",
            user_id="test-user-008",
            task_type="data_analysis",
            task_name="Test Analysis",
            status="cancelled"
        )

        assert task_cancelled.is_cancelled is True
        assert task_cancelled.is_failed is False

    def test_task_progress_paused_status(self):
        """Test TaskProgress paused status property."""
        task_paused = TaskProgress(
            task_id="test-task-009",
            user_id="test-user-009",
            task_type="data_analysis",
            task_name="Test Analysis",
            status="paused"
        )

        assert task_paused.is_paused is True
        assert task_paused.is_running is False

    def test_task_progress_completion_percentage(self):
        """Test TaskProgress completion percentage calculation."""
        # Test with 0 steps
        task_no_steps = TaskProgress(
            task_id="test-task-010",
            user_id="test-user-010",
            task_type="simple_task",
            task_name="Simple Task",
            total_steps=0
        )
        assert task_no_steps.completion_percentage == 0.0

        # Test with 4 steps, current step 2
        task_partial = TaskProgress(
            task_id="test-task-011",
            user_id="test-user-011",
            task_type="step_task",
            task_name="Step Task",
            current_step="step_2",
            total_steps=4
        )
        assert task_partial.completion_percentage == 50.0

        # Test with 10 steps, current step 10
        task_complete = TaskProgress(
            task_id="test-task-012",
            user_id="test-user-012",
            task_type="step_task",
            task_name="Step Task",
            current_step="step_10",
            total_steps=10
        )
        assert task_complete.completion_percentage == 100.0

    def test_task_progress_duration_calculation(self):
        """Test TaskProgress duration calculation."""
        # Test with no start time
        task_no_time = TaskProgress(
            task_id="test-task-013",
            user_id="test-user-013",
            task_type="quick_task",
            task_name="Quick Task"
        )
        assert task_no_time.duration_seconds is None

        # Test with start time but no completion time
        start_time = datetime.now(timezone.utc)
        task_running = TaskProgress(
            task_id="test-task-014",
            user_id="test-user-014",
            task_type="long_task",
            task_name="Long Task",
            started_at=start_time,
            status="running"
        )
        duration = task_running.duration_seconds
        assert duration is not None
        assert duration >= 0

    def test_task_progress_result_storage(self):
        """Test TaskProgress result storage."""
        result_data = {
            "output_file": "/path/to/output.json",
            "processed_items": 150,
            "success_count": 145,
            "error_count": 5,
            "execution_time": 125.6
        }

        task_with_result = TaskProgress(
            task_id="test-task-015",
            user_id="test-user-015",
            task_type="batch_processing",
            task_name="Batch Processing",
            result=result_data,
            status="completed"
        )

        assert task_with_result.result["output_file"] == "/path/to/output.json"
        assert task_with_result.result["processed_items"] == 150
        assert task_with_result.result["success_count"] == 145

    def test_task_progress_error_storage(self):
        """Test TaskProgress error information storage."""
        error_info = {
            "error_type": "ValidationError",
            "error_code": "VAL_001",
            "field": "input_data",
            "details": "Missing required field 'name'"
        }

        task_with_error = TaskProgress(
            task_id="test-task-016",
            user_id="test-user-016",
            task_type="validation",
            task_name="Validation Task",
            status="failed",
            error_message="Validation failed for input data",
            error_details=error_info
        )

        assert task_with_error.error_message == "Validation failed for input data"
        assert task_with_error.error_details["error_type"] == "ValidationError"
        assert task_with_error.error_details["error_code"] == "VAL_001"

    def test_task_progress_metadata_storage(self):
        """Test TaskProgress metadata storage."""
        metadata = {
            "priority": "high",
            "department": "engineering",
            "project": "skill-system",
            "cost_center": "CC_123",
            "compliance": ["GDPR", "SOC2"],
            "custom_tags": ["urgent", "automation"]
        }

        task_with_metadata = TaskProgress(
            task_id="test-task user_id="test-017",
           -user-017",
            task_type="compliance_check",
            task_name="Compliance Check",
            task_metadata=metadata
        )

        assert task_with_metadata.task_metadata["priority"] == "high"
        assert task_with_metadata.task_metadata["department"] == "engineering"
        assert "SOC2" in task_with_metadata.task_metadata["compliance"]
        assert "urgent" in task_with_metadata.task_metadata["custom_tags"]


class TestTaskLog:
    """Test cases for TaskLog model."""

    def test_task_log_creation(self):
        """Test TaskLog model creation."""
        timestamp = datetime.now(timezone.utc)
        task_log = TaskLog(
            task_id="test-task-001",
            level="INFO",
            message="Task execution started",
            source="task_executor",
            timestamp=timestamp,
            context={
                "operation": "start",
                "resource_id": "res_123",
                "environment": "production"
            },
            stack_trace=None,
            log_file_path="/logs/task_001.log",
            attachments=["screenshot.png", "output.json"]
        )

        assert task_log.task_id == "test-task-001"
        assert task_log.level == "INFO"
        assert task_log.message == "Task execution started"
        assert task_log.source == "task_executor"
        assert task_log.timestamp == timestamp
        assert task_log.context["operation"] == "start"
        assert task_log.log_file_path == "/logs/task_001.log"
        assert "screenshot.png" in task_log.attachments
        assert "output.json" in task_log.attachments

    def test_task_log_default_values(self):
        """Test TaskLog model default values."""
        task_log = TaskLog(
            task_id="test-task-002",
            level="DEBUG",
            message="Debug message"
        )

        assert isinstance(task_log.id, uuid.UUID)
        assert isinstance(task_log.context, dict)
        assert task_log.stack_trace is None
        assert task_log.log_file_path is None
        assert isinstance(task_log.attachments, list)

    def test_task_log_repr(self):
        """Test TaskLog string representation."""
        timestamp = datetime.now(timezone.utc)
        task_log = TaskLog(
            task_id="test-task-003",
            level="ERROR",
            message="Critical error occurred",
            timestamp=timestamp
        )

        repr_str = repr(task_log)
        assert "TaskLog" in repr_str
        assert "test-task-003" in repr_str
        assert "ERROR" in repr_str

    def test_task_log_all_levels(self):
        """Test TaskLog with all log levels."""
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            task_log = TaskLog(
                task_id=f"test-task-{level.lower()}",
                level=level,
                message=f"Test message for {level} level"
            )
            assert task_log.level == level

    def test_task_log_context_storage(self):
        """Test TaskLog context information storage."""
        context = {
            "user_id": "user_123",
            "session_id": "sess_456",
            "request_id": "req_789",
            "operation": "upload_file",
            "file_size": 1024000,
            "file_type": "application/json",
            "processing_time": 2.5,
            "memory_usage": 256,
            "cpu_percent": 45.2
        }

        task_log = TaskLog(
            task_id="test-task-context",
            level="INFO",
            message="File processing completed",
            context=context
        )

        assert task_log.context["user_id"] == "user_123"
        assert task_log.context["session_id"] == "sess_456"
        assert task_log.context["file_size"] == 1024000
        assert task_log.context["processing_time"] == 2.5

    def test_task_log_stack_trace(self):
        """Test TaskLog with stack trace."""
        stack_trace = """Traceback (most recent call last):
  File "/app/task_executor.py", line 123, in execute
    result = process_data(input_data)
  File "/app/data_processor.py", line 45, in process_data
    validate_input(data)
  File "/app/validators.py", line 78, in validate_input
    raise ValueError("Invalid input data")
ValueError: Invalid input data"""

        task_log = TaskLog(
            task_id="test-task-stack",
            level="ERROR",
            message="Error during data processing",
            stack_trace=stack_trace
        )

        assert "Traceback" in task_log.stack_trace
        assert "ValueError" in task_log.stack_trace
        assert "Invalid input data" in task_log.stack_trace

    def test_task_log_attachments(self):
        """Test TaskLog with attachments."""
        attachments = [
            "input_data.json",
            "processed_output.csv",
            "error_report.pdf",
            "performance_metrics.json",
            "debug_logs.txt"
        ]

        task_log = TaskLog(
            task_id="test-task-attachments",
            level="INFO",
            message="Task completed with attachments",
            attachments=attachments
        )

        assert len(task_log.attachments) == 5
        assert "input_data.json" in task_log.attachments
        assert "error_report.pdf" in task_log.attachments
        assert "performance_metrics.json" in task_log.attachments


class TestNotification:
    """Test cases for Notification model."""

    def test_notification_creation(self):
        """Test Notification model creation."""
        notification = Notification(
            user_id="test-user-001",
            title="Task Completed",
            message="Your skill creation task has been completed successfully",
            notification_type="success",
            priority="normal",
            channels=["websocket", "email"],
            related_task_id="task-123",
            action_url="/tasks/task-123"
        )

        assert notification.user_id == "test-user-001"
        assert notification.title == "Task Completed"
        assert notification.message == "Your skill creation task has been completed successfully"
        assert notification.notification_type == "success"
        assert notification.priority == "normal"
        assert "websocket" in notification.channels
        assert "email" in notification.channels
        assert notification.related_task_id == "task-123"
        assert notification.action_url == "/tasks/task-123"
        assert notification.is_read is False

    def test_notification_default_values(self):
        """Test Notification model default values."""
        notification = Notification(
            user_id="test-user-002",
            title="System Notification",
            message="System maintenance scheduled"
        )

        assert notification.notification_type == "info"
        assert notification.priority == "normal"
        assert notification.is_read is False
        assert isinstance(notification.channels, list)
        assert notification.related_task_id is None
        assert notification.action_url is None

    def test_notification_repr(self):
        """Test Notification string representation."""
        notification = Notification(
            user_id="test-user-003",
            title="Error Alert",
            message="Task failed with critical error",
            notification_type="error"
        )

        repr_str = repr(notification)
        assert "Notification" in repr_str
        assert "test-user-003" in repr_str
        assert "Error Alert" in repr_str

    def test_notification_priority_levels(self):
        """Test Notification with different priority levels."""
        priorities = ["low", "normal", "high", "urgent"]

        for priority in priorities:
            notification = Notification(
                user_id=f"test-user-{priority}",
                title=f"Priority {priority} Notification",
                message=f"This is a {priority} priority message",
                priority=priority
            )
            assert notification.priority == priority

    def test_notification_types(self):
        """Test Notification with different types."""
        types = ["info", "success", "warning", "error", "progress"]

        for notif_type in types:
            notification = Notification(
                user_id=f"test-user-{notif_type}",
                title=f"{notif_type.title()} Notification",
                message=f"This is a {notif_type} notification",
                notification_type=notif_type
            )
            assert notification.notification_type == notif_type

    def test_notification_channels(self):
        """Test Notification with different channels."""
        channel_combinations = [
            ["websocket"],
            ["email"],
            ["push"],
            ["slack"],
            ["websocket", "email"],
            ["email", "push", "slack"],
            ["websocket", "email", "push", "slack"]
        ]

        for channels in channel_combinations:
            notification = Notification(
                user_id="test-user-channels",
                title="Multi-Channel Notification",
                message="Testing multiple channels",
                channels=channels
            )
            assert notification.channels == channels

    def test_notification_read_status(self):
        """Test Notification read status."""
        # Test unread notification
        unread_notification = Notification(
            user_id="test-user-unread",
            title="Unread Notification",
            message="This notification is unread",
            is_read=False
        )
        assert unread_notification.is_read is False
        assert unread_notification.read_at is None

        # Test read notification
        read_time = datetime.now(timezone.utc)
        read_notification = Notification(
            user_id="test-user-read",
            title="Read Notification",
            message="This notification has been read",
            is_read=True,
            read_at=read_time
        )
        assert read_notification.is_read is True
        assert read_notification.read_at == read_time

    def test_notification_related_task(self):
        """Test Notification with related task."""
        notification = Notification(
            user_id="test-user-task",
            title="Task Status Update",
            message="Your task has been updated",
            related_task_id="task-789",
            action_url="/dashboard/tasks/task-789"
        )

        assert notification.related_task_id == "task-789"
        assert notification.action_url == "/dashboard/tasks/task-789"


class TestProgressMetric:
    """Test cases for ProgressMetric model."""

    def test_progress_metric_creation(self):
        """Test ProgressMetric model creation."""
        timestamp = datetime.now(timezone.utc)
        metric = ProgressMetric(
            metric_name="task_completion_rate",
            value=85.5,
            unit="percentage",
            labels={
                "task_type": "skill_creation",
                "department": "engineering",
                "environment": "production"
            },
            dimensions={
                "time_window": "24h",
                "aggregation": "hourly",
                "region": "us-east-1"
            },
            timestamp=timestamp,
            metadata={
                "source": "analytics_service",
                "collection_method": "real_time",
                "confidence": 0.95
            }
        )

        assert metric.metric_name == "task_completion_rate"
        assert metric.value == 85.5
        assert metric.unit == "percentage"
        assert metric.labels["task_type"] == "skill_creation"
        assert metric.labels["department"] == "engineering"
        assert metric.dimensions["time_window"] == "24h"
        assert metric.timestamp == timestamp
        assert metric.metadata["source"] == "analytics_service"

    def test_progress_metric_default_values(self):
        """Test ProgressMetric model default values."""
        metric = ProgressMetric(
            metric_name="simple_metric",
            value=100.0
        )

        assert metric.unit is None
        assert isinstance(metric.labels, dict)
        assert isinstance(metric.dimensions, dict)
        assert isinstance(metric.metadata, dict)

    def test_progress_metric_repr(self):
        """Test ProgressMetric string representation."""
        timestamp = datetime.now(timezone.utc)
        metric = ProgressMetric(
            metric_name="response_time",
            value=250.0,
            unit="milliseconds",
            timestamp=timestamp
        )

        repr_str = repr(metric)
        assert "ProgressMetric" in repr_str
        assert "response_time" in repr_str
        assert "250.0" in repr_str
        assert "milliseconds" in repr_str

    def test_progress_metric_different_value_types(self):
        """Test ProgressMetric with different value types."""
        # Integer value
        metric_int = ProgressMetric(
            metric_name="task_count",
            value=150,
            unit="count"
        )
        assert metric_int.value == 150
        assert isinstance(metric_int.value, int)

        # Float value
        metric_float = ProgressMetric(
            metric_name="cpu_usage",
            value=67.8,
            unit="percentage"
        )
        assert metric_float.value == 67.8
        assert isinstance(metric_float.value, float)

        # Decimal value
        metric_decimal = ProgressMetric(
            metric_name="cost",
            value=Decimal("123.45"),
            unit="USD"
        )
        assert metric_decimal.value == Decimal("123.45")

    def test_progress_metric_labels(self):
        """Test ProgressMetric with various labels."""
        labels = {
            "service": "skill-management",
            "version": "1.2.3",
            "region": "eu-west-1",
            "environment": "staging",
            "team": "platform",
            "component": "progress-tracker"
        }

        metric = ProgressMetric(
            metric_name="service_health",
            value=1.0,
            unit="score",
            labels=labels
        )

        for key, value in labels.items():
            assert metric.labels[key] == value

    def test_progress_metric_dimensions(self):
        """Test ProgressMetric with various dimensions."""
        dimensions = {
            "time_granularity": "hour",
            "aggregation_method": "average",
            "retention_period": "90d",
            "sampling_rate": "1m"
        }

        metric = ProgressMetric(
            metric_name="memory_usage",
            value=512.0,
            unit="MB",
            dimensions=dimensions
        )

        for key, value in dimensions.items():
            assert metric.dimensions[key] == value

    def test_progress_metric_metadata(self):
        """Test ProgressMetric with metadata."""
        metadata = {
            "collector": "prometheus",
            "scrape_interval": "30s",
            "last_updated": "2024-01-15T10:30:00Z",
            "quality_score": 0.98,
            "anomaly_detected": False,
            "tags": ["production", "critical", "24x7"]
        }

        metric = ProgressMetric(
            metric_name="uptime",
            value=99.9,
            unit="percentage",
            metadata=metadata
        )

        assert metric.metadata["collector"] == "prometheus"
        assert metric.metadata["quality_score"] == 0.98
        assert metric.metadata["anomaly_detected"] is False
        assert "production" in metric.metadata["tags"]


class TestModelIntegration:
    """Integration tests for progress tracking models."""

    def test_task_progress_with_logs(self):
        """Test TaskProgress model interaction with TaskLog."""
        # Create a task
        task = TaskProgress(
            task_id="integration-task-001",
            user_id="integration-user-001",
            task_type="data_processing",
            task_name="Integration Test Task"
        )

        # Create associated logs
        logs = [
            TaskLog(
                task_id="integration-task-001",
                level="INFO",
                message="Task started",
                context={"start_time": "2024-01-15T10:00:00Z"}
            ),
            TaskLog(
                task_id="integration-task-001",
                level="DEBUG",
                message="Processing data chunk 1/10",
                context={"chunk": 1, "total_chunks": 10}
            ),
            TaskLog(
                task_id="integration-task-001",
                level="INFO",
                message="Task completed successfully",
                context={"end_time": "2024-01-15T10:05:00Z", "duration": 300}
            )
        ]

        # Verify task
        assert task.task_id == "integration-task-001"
        assert task.user_id == "integration-user-001"
        assert task.task_type == "data_processing"
        assert task.status == "pending"

        # Verify logs
        assert len(logs) == 3
        assert logs[0].level == "INFO"
        assert logs[1].level == "DEBUG"
        assert logs[2].level == "INFO"

    def test_notification_for_task_completion(self):
        """Test Notification creation for task completion."""
        # Create a completed task
        completed_task = TaskProgress(
            task_id="completion-task-001",
            user_id="completion-user-001",
            task_type="skill_deployment",
            task_name="Skill Deployment",
            status="completed",
            result={"deployed_url": "https://example.com/skill/123"}
        )

        # Create completion notification
        notification = Notification(
            user_id="completion-user-001",
            title="Task Completed Successfully",
            message=f"Task '{completed_task.task_name}' has been completed",
            notification_type="success",
            priority="normal",
            related_task_id="completion-task-001",
            action_url=f"/tasks/completion-task-001"
        )

        assert notification.related_task_id == completed_task.task_id
        assert notification.notification_type == "success"
        assert completed_task.status == "completed"

    def test_metrics_collection_for_tasks(self):
        """Test ProgressMetric collection for task monitoring."""
        # Create multiple tasks
        tasks = [
            TaskProgress(
                task_id=f"metric-task-{i}",
                user_id=f"metric-user-{i % 3}",
                task_type="analysis",
                task_name=f"Analysis Task {i}",
                status="completed" if i % 2 == 0 else "failed"
            )
            for i in range(10)
        ]

        # Create metrics for these tasks
        metrics = [
            ProgressMetric(
                metric_name="task_completion",
                value=1.0 if task.status == "completed" else 0.0,
                unit="boolean",
                labels={"task_id": task.task_id, "user_id": task.user_id}
            )
            for task in tasks
        ]

        assert len(metrics) == 10
        assert metrics[0].value == 1.0  # task-0 is completed
        assert metrics[1].value == 0.0  # task-1 is failed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
