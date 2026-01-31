"""Integration tests for real-time progress tracking system.

This module provides comprehensive integration tests for the entire
progress tracking system including all managers, WebSocket, and API.
"""

import asyncio
import pytest
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.progress.models.task import TaskProgress, TaskStatus
from app.progress.models.log import TaskLog, LogLevel
from app.progress.models.notification import Notification, NotificationType, NotificationPriority
from app.progress.models.metric import ProgressMetric

from app.progress.schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
    UpdateStatusRequest,
    CreateLogEntryRequest,
    CreateNotificationRequest,
)

from app.progress.progress_manager import ProgressManager
from app.progress.log_manager import LogManager
from app.progress.notification_manager import NotificationManager
from app.progress.visualization_manager import VisualizationManager
from app.progress.websocket_manager import WebSocketManager
from app.progress.resource_manager import ResourceManager, ResourceType

from app.progress.websocket_handler import WebSocketEventHandler

# Import API router for testing
from app.progress.api import router


class TestProgressTrackingIntegration:
    """Integration tests for progress tracking system."""

    @pytest.fixture
    async def managers(self):
        """Create manager instances for testing."""
        # Create managers (without database for testing)
        progress_mgr = ProgressManager()
        log_mgr = LogManager()
        notification_mgr = NotificationManager()
        visualization_mgr = VisualizationManager()
        websocket_mgr = WebSocketManager()
        resource_mgr = ResourceManager()

        # Start WebSocket manager
        await websocket_mgr.start()

        # Start resource monitoring
        await resource_mgr.start_monitoring()

        yield {
            "progress": progress_mgr,
            "log": log_mgr,
            "notification": notification_mgr,
            "visualization": visualization_mgr,
            "websocket": websocket_mgr,
            "resource": resource_mgr,
        }

        # Cleanup
        await websocket_mgr.stop()
        await resource_mgr.stop_monitoring()

    @pytest.mark.asyncio
    async def test_complete_task_workflow(self, managers):
        """Test complete task lifecycle workflow."""
        # Create task
        task_request = CreateTaskRequest(
            task_id="integration-test-task",
            user_id="test-user",
            task_type="skill_creation",
            task_name="Integration Test Task",
            description="Testing complete workflow",
            progress=0.0,
            status="pending",
        )

        task = await managers["progress"].create_task(task_request)
        assert task.task_id == "integration-test-task"
        assert task.progress == 0.0
        assert task.status == "pending"

        # Update progress
        await managers["progress"].update_progress(
            task_id="integration-test-task",
            progress=25.0,
            current_step="Initializing",
        )

        task = await managers["progress"].get_task("integration-test-task")
        assert task.progress == 25.0
        assert task.current_step == "Initializing"

        # Add log entries
        log_request = CreateLogEntryRequest(
            task_id="integration-test-task",
            level="INFO",
            message="Task started successfully",
            source="test",
        )

        log_entry = await managers["log"].create_log_entry(log_request)
        assert log_entry.task_id == "integration-test-task"
        assert log_entry.level == "INFO"

        # Update status to running
        await managers["progress"].update_status(
            task_id="integration-test-task",
            status="running",
        )

        task = await managers["progress"].get_task("integration-test-task")
        assert task.status == "running"

        # Add more logs
        for i in range(5):
            await managers["log"].create_log_entry(
                CreateLogEntryRequest(
                    task_id="integration-test-task",
                    level="DEBUG",
                    message=f"Processing step {i+1}",
                    source="test",
                )
            )

        # Complete task
        await managers["progress"].complete_task(
            task_id="integration-test-task",
            result={"output": "Task completed successfully"},
        )

        task = await managers["progress"].get_task("integration-test-task")
        assert task.status == "completed"
        assert task.progress == 100.0

        # Verify logs
        logs = await managers["log"].get_task_logs("integration-test-task")
        assert len(logs) >= 6  # Initial log + 5 debug logs

        print("✓ Complete task workflow test passed")

    @pytest.mark.asyncio
    async def test_websocket_integration(self, managers):
        """Test WebSocket functionality."""
        # Create mock WebSocket
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.application_state = "CONNECTED"
        mock_websocket.query_params = {"task_id": "ws-test-task", "user_id": "test-user"}

        # Connect WebSocket
        connection_id = await managers["websocket"].connect(
            mock_websocket,
            task_id="ws-test-task",
            user_id="test-user",
        )

        assert connection_id is not None
        assert len(managers["websocket"].connection_pool.connections) == 1

        # Send test message
        test_message = {
            "type": "progress_update",
            "task_id": "ws-test-task",
            "progress": 50.0,
            "current_step": "Testing WebSocket",
        }

        result = await managers["websocket"].handle_message(connection_id, test_message)
        assert result is True

        # Test broadcast
        await managers["progress"].create_task(
            CreateTaskRequest(
                task_id="broadcast-test-task",
                user_id="test-user",
                task_type="skill_creation",
                task_name="Broadcast Test",
                progress=0.0,
                status="running",
            )
        )

        # Update progress (should broadcast)
        await managers["progress"].update_progress(
            task_id="broadcast-test-task",
            progress=100.0,
        )

        # Check stats
        stats = managers["websocket"].get_stats()
        assert stats["total_messages_sent"] > 0

        print("✓ WebSocket integration test passed")

    @pytest.mark.asyncio
    async def test_notification_integration(self, managers):
        """Test notification system integration."""
        # Create task first
        await managers["progress"].create_task(
            CreateTaskRequest(
                task_id="notify-test-task",
                user_id="test-user",
                task_type="skill_creation",
                task_name="Notification Test",
                progress=0.0,
                status="running",
            )
        )

        # Create notification
        notification_request = CreateNotificationRequest(
            user_id="test-user",
            title="Task Progress Update",
            message="Your task has made progress",
            notification_type=NotificationType.PROGRESS,
            priority=NotificationPriority.NORMAL,
            related_task_id="notify-test-task",
        )

        notification = await managers["notification"].create_notification(notification_request)
        assert notification.user_id == "test-user"
        assert notification.related_task_id == "notify-test-task"

        # Get user notifications
        notifications = await managers["notification"].get_user_notifications("test-user")
        assert len(notifications) >= 1

        # Mark as read
        success = await managers["notification"].mark_as_read(notification.id)
        assert success is True

        # Get statistics
        stats = await managers["notification"].get_notification_statistics("test-user")
        assert stats["total"] > 0

        print("✓ Notification integration test passed")

    @pytest.mark.asyncio
    async def test_visualization_integration(self, managers):
        """Test visualization system integration."""
        # Create multiple tasks
        for i in range(5):
            await managers["progress"].create_task(
                CreateTaskRequest(
                    task_id=f"viz-test-task-{i}",
                    user_id="test-user",
                    task_type="skill_creation",
                    task_name=f"Visualization Test {i}",
                    progress=0.0,
                    status="running",
                )
            )

            # Update progress
            await managers["progress"].update_progress(
                task_id=f"viz-test-task-{i}",
                progress=50.0 + i * 10,
            )

        # Create progress chart
        task_ids = [f"viz-test-task-{i}" for i in range(5)]
        chart = await managers["visualization"].create_progress_chart(task_ids)

        assert chart.title == "Task Progress Over Time"
        assert len(chart.data) > 0

        # Create status distribution chart
        distribution = await managers["visualization"].create_status_distribution_chart(
            user_id="test-user"
        )

        assert distribution.chart_type.value == "pie"
        assert len(distribution.data) > 0

        # Create performance metrics
        metrics = await managers["visualization"].create_performance_metrics_chart(task_ids)

        assert metrics.title == "Performance Metrics"
        assert len(metrics.data) > 0

        # Create dashboard
        dashboard = await managers["visualization"].create_dashboard(
            dashboard_id="test-dashboard",
            title="Test Dashboard",
            widgets=[
                {
                    "widget_id": "widget-1",
                    "title": "Progress Chart",
                    "chart_type": "line",
                    "query": {
                        "task_ids": task_ids,
                        "time_range": "1d",
                    },
                    "position": {"x": 0, "y": 0},
                    "size": {"width": 6, "height": 4},
                }
            ],
        )

        assert dashboard["dashboard_id"] == "test-dashboard"
        assert len(dashboard["widgets"]) == 1

        print("✓ Visualization integration test passed")

    @pytest.mark.asyncio
    async def test_resource_management_integration(self, managers):
        """Test resource management integration."""
        # Check initial stats
        stats = managers["resource"].get_comprehensive_stats()
        assert "pools" in stats
        assert "system" in stats

        # Test memory cache pool
        cache_pool = managers["resource"].get_pool(ResourceType.MEMORY_CACHE)
        assert cache_pool is not None

        # Acquire and release cache entries
        cache_pool.acquire("test-key-1", "test-value-1", 1024)
        cache_pool.release("test-key-1")

        # Check pool stats
        cache_stats = cache_pool.get_stats()
        assert cache_stats["total_allocated"] > 0

        # Optimize resources
        managers["resource"].optimize_resources()

        # Get updated stats
        updated_stats = managers["resource"].get_comprehensive_stats()
        assert "pools" in updated_stats

        print("✓ Resource management integration test passed")

    @pytest.mark.asyncio
    async def test_bulk_operations(self, managers):
        """Test bulk operations across managers."""
        # Bulk create tasks
        task_requests = [
            CreateTaskRequest(
                task_id=f"bulk-task-{i}",
                user_id="bulk-user",
                task_type="skill_creation",
                task_name=f"Bulk Task {i}",
                progress=0.0,
                status="pending",
            )
            for i in range(10)
        ]

        created_tasks = []
        for request in task_requests:
            task = await managers["progress"].create_task(request)
            created_tasks.append(task)

        assert len(created_tasks) == 10

        # Bulk update progress
        from app.progress.schemas.progress_operations import BulkUpdateRequest

        bulk_request = BulkUpdateRequest(
            task_ids=[f"bulk-task-{i}" for i in range(10)],
            progress=75.0,
        )

        results = await managers["progress"].bulk_update(bulk_request)
        assert results["total"] == 10
        assert len(results["successful"]) == 10

        # Verify updates
        for i in range(10):
            task = await managers["progress"].get_task(f"bulk-task-{i}")
            assert task.progress == 75.0

        print("✓ Bulk operations test passed")

    @pytest.mark.asyncio
    async def test_error_handling(self, managers):
        """Test error handling across the system."""
        # Test invalid task creation
        with pytest.raises(Exception):  # Should raise validation error
            await managers["progress"].create_task(
                CreateTaskRequest(
                    task_id="",  # Invalid: empty task_id
                    user_id="test-user",
                    task_type="skill_creation",
                    task_name="Invalid Task",
                    progress=0.0,
                    status="pending",
                )
            )

        # Test non-existent task
        task = await managers["progress"].get_task("non-existent-task")
        assert task is None

        # Test invalid progress update
        with pytest.raises(Exception):  # Should raise validation error
            await managers["progress"].update_progress(
                task_id="non-existent-task",
                progress=150.0,  # Invalid: > 100
            )

        # Test invalid log creation
        with pytest.raises(Exception):  # Should raise validation error
            await managers["log"].create_log_entry(
                CreateLogEntryRequest(
                    task_id="",
                    level="INVALID",
                    message="Test log",
                )
            )

        # Test invalid notification
        with pytest.raises(Exception):  # Should raise validation error
            await managers["notification"].create_notification(
                CreateNotificationRequest(
                    user_id="",
                    title="Invalid Notification",
                    message="Test",
                )
            )

        print("✓ Error handling test passed")

    @pytest.mark.asyncio
    async def test_statistics_and_monitoring(self, managers):
        """Test statistics and monitoring functionality."""
        # Create some test data
        await managers["progress"].create_task(
            CreateTaskRequest(
                task_id="stats-task",
                user_id="stats-user",
                task_type="skill_creation",
                task_name="Stats Test",
                progress=0.0,
                status="running",
            )
        )

        await managers["progress"].update_progress("stats-task", 50.0)
        await managers["progress"].update_progress("stats-task", 100.0)

        await managers["log"].create_log_entry(
            CreateLogEntryRequest(
                task_id="stats-task",
                level="INFO",
                message="Stats test log",
                source="test",
            )
        )

        # Get statistics
        task_stats = managers["progress"].get_stats()
        assert "total_tasks_created" in task_stats

        log_stats = managers["log"].get_stats()
        assert "total_logs_created" in log_stats

        notification_stats = managers["notification"].get_stats()
        assert "total_created" in notification_stats

        visualization_stats = managers["visualization"].get_stats()
        assert "total_visualizations_created" in visualization_stats

        websocket_stats = managers["websocket"].get_stats()
        assert "total_connections" in websocket_stats

        # Overall stats
        # This would require API endpoint in real implementation
        print("✓ Statistics and monitoring test passed")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, managers):
        """Test concurrent operations."""
        # Create multiple tasks concurrently
        async def create_and_update_task(task_id: str):
            await managers["progress"].create_task(
                CreateTaskRequest(
                    task_id=task_id,
                    user_id="concurrent-user",
                    task_type="skill_creation",
                    task_name=f"Concurrent Task {task_id}",
                    progress=0.0,
                    status="running",
                )
            )

            # Update progress multiple times
            for progress in [25, 50, 75, 100]:
                await managers["progress"].update_progress(task_id, progress)

            # Add logs
            for i in range(3):
                await managers["log"].create_log_entry(
                    CreateLogEntryRequest(
                        task_id=task_id,
                        level="INFO",
                        message=f"Concurrent log {i}",
                        source="test",
                    )
                )

        # Run concurrent operations
        tasks = [
            create_and_update_task(f"concurrent-task-{i}")
            for i in range(10)
        ]

        await asyncio.gather(*tasks)

        # Verify all tasks were created and updated
        for i in range(10):
            task = await managers["progress"].get_task(f"concurrent-task-{i}")
            assert task is not None
            assert task.progress == 100.0

            logs = await managers["log"].get_task_logs(f"concurrent-task-{i}")
            assert len(logs) >= 3

        print("✓ Concurrent operations test passed")


async def run_integration_tests():
    """Run all integration tests."""
    print("Running Progress Tracking System Integration Tests\n")
    print("=" * 60)

    test_instance = TestProgressTrackingIntegration()

    # Create managers
    managers = {
        "progress": ProgressManager(),
        "log": LogManager(),
        "notification": NotificationManager(),
        "visualization": VisualizationManager(),
        "websocket": WebSocketManager(),
        "resource": ResourceManager(),
    }

    # Start required services
    await managers["websocket"].start()
    await managers["resource"].start_monitoring()

    try:
        # Run all tests
        tests = [
            ("Complete Task Workflow", test_instance.test_complete_task_workflow),
            ("WebSocket Integration", test_instance.test_websocket_integration),
            ("Notification Integration", test_instance.test_notification_integration),
            ("Visualization Integration", test_instance.test_visualization_integration),
            ("Resource Management Integration", test_instance.test_resource_management_integration),
            ("Bulk Operations", test_instance.test_bulk_operations),
            ("Error Handling", test_instance.test_error_handling),
            ("Statistics and Monitoring", test_instance.test_statistics_and_monitoring),
            ("Concurrent Operations", test_instance.test_concurrent_operations),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            try:
                print(f"\nRunning: {test_name}")
                await test_func(managers)
                print(f"✓ {test_name} PASSED")
                passed += 1
            except Exception as e:
                print(f"✗ {test_name} FAILED: {e}")
                failed += 1

        print("\n" + "=" * 60)
        print(f"\nTest Results: {passed} passed, {failed} failed")
        print(f"Success Rate: {(passed / (passed + failed) * 100):.1f}%")

        if failed == 0:
            print("\n🎉 All integration tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")

    finally:
        # Cleanup
        await managers["websocket"].stop()
        await managers["resource"].stop_monitoring()


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
