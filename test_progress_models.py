"""Test script to verify progress tracking models.

This script tests the basic functionality of the progress tracking models
including model creation, properties, and serialization.
"""

import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.progress.models import (
    TaskProgress,
    TaskLog,
    Notification,
    ProgressMetric,
    Base,
)


def test_task_progress_model():
    """Test TaskProgress model functionality."""
    print("Testing TaskProgress model...")

    # Create a task progress instance
    task = TaskProgress(
        task_id="test-task-001",
        user_id="user-123",
        task_type="skill_creation",
        task_name="Test Skill Creation",
        description="Testing task progress model",
        progress=50.0,
        status="running",
        current_step="Processing files",
        total_steps=4,
        estimated_duration=300,
    )

    # Test properties
    assert task.is_running == True
    assert task.is_active == True
    assert task.is_finished == False
    assert task.progress_percentage == "50.0%"

    # Test progress update
    task.update_progress(75.0, current_step="Validating output")
    assert task.progress == 75.0
    assert task.current_step == "Validating output"

    # Test to_dict
    task_dict = task.to_dict()
    assert "id" in task_dict
    assert task_dict["progress"] == 75.0
    assert task_dict["status"] == "running"

    print("✓ TaskProgress model tests passed")


def test_task_log_model():
    """Test TaskLog model functionality."""
    print("Testing TaskLog model...")

    # Test log creation using class methods
    debug_log = TaskLog.create_debug_log(
        task_id="test-task-001",
        message="Starting task execution",
        source="task_tracker",
        context={"step": 1}
    )

    info_log = TaskLog.create_info_log(
        task_id="test-task-001",
        message="Task completed successfully",
        source="task_tracker"
    )

    error_log = TaskLog.create_error_log(
        task_id="test-task-001",
        message="An error occurred",
        source="progress_manager",
        stack_trace="Traceback..."
    )

    # Test properties
    assert debug_log.is_debug == True
    assert debug_log.is_info == False
    assert info_log.is_info == True
    assert error_log.is_error == True
    assert error_log.is_error_level == True

    # Test level priorities
    assert debug_log.level_priority == 10
    assert info_log.level_priority == 20
    assert error_log.level_priority == 40

    # Test to_dict
    debug_dict = debug_log.to_dict()
    assert "id" in debug_dict
    assert debug_dict["level"] == "DEBUG"
    assert debug_dict["message"] == "Starting task execution"

    print("✓ TaskLog model tests passed")


def test_notification_model():
    """Test Notification model functionality."""
    print("Testing Notification model...")

    # Create notifications
    progress_notif = Notification.create_progress_notification(
        user_id="user-123",
        task_id="test-task-001",
        title="Task Progress Update",
        message="Task is 75% complete",
        progress=75.0,
        current_step="Validating output"
    )

    success_notif = Notification.create_success_notification(
        user_id="user-123",
        task_id="test-task-001",
        title="Task Completed",
        message="Your task has completed successfully"
    )

    error_notif = Notification.create_error_notification(
        user_id="user-123",
        task_id="test-task-001",
        title="Task Failed",
        message="An error occurred during task execution",
        error_details={"error_code": "500", "error_type": "InternalServerError"}
    )

    # Test properties
    assert progress_notif.is_progress == True
    assert progress_notif.is_unread == True
    assert success_notif.is_success == True
    assert error_notif.is_error == True
    assert error_notif.is_high_priority == True

    # Test channel management
    progress_notif.add_channel("email")
    assert "email" in progress_notif.channels
    assert progress_notif.channel_count == 2

    # Test delivery status
    progress_notif.update_delivery_status("websocket", "sent")
    assert progress_notif.successful_deliveries == 1

    # Test to_dict
    notif_dict = progress_notif.to_dict()
    assert "id" in notif_dict
    assert notif_dict["notification_type"] == "progress"
    assert notif_dict["priority"] in [None, "normal"]  # Handle None case

    print("✓ Notification model tests passed")


def test_progress_metric_model():
    """Test ProgressMetric model functionality."""
    print("Testing ProgressMetric model...")

    # Create metrics
    response_time = ProgressMetric.create_response_time_metric(
        metric_name="api_response_time",
        response_time_ms=125.5,
        task_id="test-task-001",
        user_id="user-123",
        labels={"endpoint": "/api/tasks", "method": "POST"}
    )

    throughput = ProgressMetric.create_throughput_metric(
        metric_name="task_throughput",
        count=150,
        time_period="1m",
        labels={"task_type": "skill_creation"}
    )

    error_rate = ProgressMetric.create_error_rate_metric(
        error_count=5,
        total_count=100,
        time_period="1m",
        task_type="skill_creation"
    )

    # Test properties
    assert response_time.is_response_time == True
    assert response_time.value_as_string == "125.50ms"
    assert throughput.is_throughput == True
    assert throughput.value_as_integer == 150
    assert error_rate.is_percentage == True
    assert error_rate.value_as_string == "5.0%"

    # Test label management
    response_time.add_label("environment", "production")
    assert "environment" in response_time.labels
    assert response_time.label_count == 3  # 2 original + 1 added

    # Test to_dict
    metric_dict = response_time.to_dict()
    assert "id" in metric_dict
    assert metric_dict["metric_name"] == "api_response_time"
    assert metric_dict["unit"] == "ms"

    print("✓ ProgressMetric model tests passed")


def test_model_relationships():
    """Test model relationships and integration."""
    print("Testing model relationships...")

    # Create a complete task with logs, notifications, and metrics
    task = TaskProgress(
        task_id="integration-test-001",
        user_id="user-123",
        task_type="skill_creation",
        task_name="Integration Test Task",
        description="Testing model integration",
        progress=0.0,
        status="pending",
    )

    # Create logs
    logs = [
        TaskLog.create_info_log(task_id=task.task_id, message="Task started"),
        TaskLog.create_debug_log(task_id=task.task_id, message="Initializing", context={"step": 1}),
        TaskLog.create_warning_log(task_id=task.task_id, message="Slow operation detected", source="performance_monitor"),
    ]

    # Create notifications
    notifications = [
        Notification.create_progress_notification(
            user_id=task.user_id,
            task_id=task.task_id,
            title="Task Started",
            message="Your task has started processing"
        ),
        Notification.create_progress_notification(
            user_id=task.user_id,
            task_id=task.task_id,
            title="Task Progress",
            message="Task is 50% complete",
            progress=50.0
        ),
    ]

    # Create metrics
    metrics = [
        ProgressMetric.create_response_time_metric(
            metric_name="task_startup_time",
            response_time_ms=250.0,
            task_id=task.task_id
        ),
        ProgressMetric.create_throughput_metric(
            metric_name="task_completion_rate",
            count=1,
            time_period="1h",
            labels={"task_type": task.task_type}
        ),
    ]

    # Verify all models can be serialized
    task_dict = task.to_dict()
    assert len(logs) == len([log.to_dict() for log in logs])
    assert len(notifications) == len([notif.to_dict() for notif in notifications])
    assert len(metrics) == len([metric.to_dict() for metric in metrics])

    print("✓ Model integration tests passed")


def main():
    """Run all model tests."""
    print("=" * 60)
    print("Progress Tracking Models Test Suite")
    print("=" * 60)
    print()

    try:
        test_task_progress_model()
        test_task_log_model()
        test_notification_model()
        test_progress_metric_model()
        test_model_relationships()

        print()
        print("=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1

    except Exception as e:
        print()
        print("=" * 60)
        print(f"✗ Unexpected error: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
