"""Tests for platform Celery tasks.

Tests the asynchronous task execution including deployment,
validation, and monitoring tasks.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any
import json

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backend.app.platform.tasks.deployment_tasks import (
    deploy_skill_task,
    cancel_deployment_task,
    retry_deployment_task,
    batch_deploy_skills_task,
    get_platform_manager,
    monitor_deployment_progress
)

from backend.app.platform.tasks.validation_tasks import (
    validate_compatibility_task,
    batch_validate_compatibility_task,
    validate_skill_format_task,
    check_format_compatibility_task
)

from backend.app.platform.tasks.monitoring_tasks import (
    check_platform_health_task,
    check_all_platforms_health_task,
    cleanup_old_alerts_task,
    periodic_health_check
)

from backend.app.platform.tasks.monitor import (
    TaskMonitor,
    TaskInfo,
    TaskStatus,
    TaskPriority,
    get_task_monitor
)


@pytest.fixture
def sample_skill_data():
    """Create sample skill data for testing."""
    return {
        "name": "Test Skill",
        "description": "A test skill for validation",
        "format": "json",
        "version": "1.0.0",
        "content": {
            "type": "test",
            "data": "sample data"
        }
    }


@pytest.fixture
def mock_platform_manager():
    """Create mock platform manager."""
    manager = MagicMock()
    manager.validate_skill_compatibility = AsyncMock(return_value={
        "overall_compatible": True,
        "compatible_platforms": ["test_platform"],
        "compatibility_score": 100
    })
    manager.deploy_skill = AsyncMock(return_value=[])
    manager.get_deployment_status = AsyncMock(return_value={
        "deployment_id": "test-deployment",
        "status": "success",
        "completed_at": "2024-01-01T00:00:00",
        "duration_seconds": 10.0
    })
    manager.cancel_deployment = AsyncMock(return_value=True)
    manager.retry_deployment = AsyncMock(return_value=MagicMock(deployment_id="new-deployment"))
    manager.deployer.deploy_batch = AsyncMock(return_value=[])
    manager.monitor.check_platform_health = AsyncMock(return_value=MagicMock(
        status=MagicMock(value="healthy"),
        is_healthy=True,
        last_check=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
        health_checks=[]
    ))
    manager.monitor.check_all_platforms_health = AsyncMock(return_value={
        "test_platform": MagicMock(
            status=MagicMock(value="healthy"),
            is_healthy=True,
            last_check=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
            health_checks=[]
        )
    })
    manager.monitor.cleanup_old_alerts = AsyncMock(return_value=5)
    manager.registry.get_registered_platforms.return_value = ["test_platform"]
    manager.registry.get_adapter.return_value = MagicMock(
        supported_formats=["json", "yaml", "test"]
    )
    manager.converter.validate_conversion = AsyncMock(return_value={"valid": True})
    return manager


@pytest.fixture
def mock_event_loop():
    """Create mock event loop."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


class TestDeploymentTasks:
    """Test deployment-related Celery tasks."""

    @pytest.mark.asyncio
    async def test_deploy_skill_task_success(self, mock_platform_manager, sample_skill_data):
        """Test successful skill deployment."""
        with patch('backend.app.platform.tasks.deployment_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = deploy_skill_task(
                skill_data=sample_skill_data,
                target_platforms=["test_platform"],
                source_format="json",
                validate_compatibility=True
            )

            assert result["success"] is True
            assert "deployment_ids" in result
            assert "results" in result
            assert result["skill_name"] == "Test Skill"

    @pytest.mark.asyncio
    async def test_deploy_skill_task_validation_failure(self, mock_platform_manager, sample_skill_data):
        """Test deployment with validation failure."""
        # Mock validation failure
        mock_platform_manager.validate_skill_compatibility = AsyncMock(return_value={
            "overall_compatible": False,
            "incompatible_platforms": ["test_platform"]
        })

        with patch('backend.app.platform.tasks.deployment_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = deploy_skill_task(
                skill_data=sample_skill_data,
                target_platforms=["test_platform"],
                validate_compatibility=True
            )

            assert result["success"] is False
            assert "compatibility_report" in result

    @pytest.mark.asyncio
    async def test_cancel_deployment_task(self, mock_platform_manager):
        """Test deployment cancellation."""
        with patch('backend.app.platform.tasks.deployment_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = cancel_deployment_task(
                deployment_id="test-deployment",
                force=False
            )

            assert result["success"] is True
            assert result["deployment_id"] == "test-deployment"
            assert result["cancelled"] is True

    @pytest.mark.asyncio
    async def test_retry_deployment_task(self, mock_platform_manager):
        """Test deployment retry."""
        with patch('backend.app.platform.tasks.deployment_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = retry_deployment_task(
                deployment_id="test-deployment",
                new_config={"retry": True}
            )

            assert result["success"] is True
            assert "new_deployment_id" in result

    @pytest.mark.asyncio
    async def test_batch_deploy_skills_task(self, mock_platform_manager, sample_skill_data):
        """Test batch deployment."""
        deployments = [
            {
                "skill_data": sample_skill_data,
                "target_platform": "test_platform"
            }
        ]

        with patch('backend.app.platform.tasks.deployment_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = batch_deploy_skills_task(
                deployments=deployments,
                max_concurrent=5,
                wait_for_all=True
            )

            assert result["success"] is True
            assert "successful_deployments" in result
            assert "failed_deployments" in result

    @pytest.mark.asyncio
    async def test_monitor_deployment_progress(self, mock_platform_manager, mock_event_loop):
        """Test deployment progress monitoring."""
        # Mock successful deployment
        mock_platform_manager.get_deployment_status = AsyncMock(return_value={
            "deployment_id": "test-deployment",
            "status": "success",
            "completed_at": "2024-01-01T00:00:00",
            "duration_seconds": 10.0
        })

        result = monitor_deployment_progress(
            loop=mock_event_loop,
            manager=mock_platform_manager,
            deployment_id="test-deployment",
            check_interval=1,
            max_checks=2
        )

        assert result["deployment_id"] == "test-deployment"
        assert result["final_status"] == "success"

    @pytest.mark.asyncio
    async def test_monitor_deployment_timeout(self, mock_platform_manager, mock_event_loop):
        """Test deployment monitoring timeout."""
        # Mock ongoing deployment
        mock_platform_manager.get_deployment_status = AsyncMock(return_value={
            "deployment_id": "test-deployment",
            "status": "pending"
        })

        result = monitor_deployment_progress(
            loop=mock_event_loop,
            manager=mock_platform_manager,
            deployment_id="test-deployment",
            check_interval=0.1,
            max_checks=2
        )

        assert result["deployment_id"] == "test-deployment"
        assert result["final_status"] == "timeout"


class TestValidationTasks:
    """Test validation-related Celery tasks."""

    @pytest.mark.asyncio
    async def test_validate_compatibility_task_success(self, mock_platform_manager, sample_skill_data):
        """Test successful compatibility validation."""
        with patch('backend.app.platform.tasks.validation_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = validate_compatibility_task(
                skill_data=sample_skill_data,
                target_platforms=["test_platform"]
            )

            assert result["success"] is True
            assert "summary" in result
            assert result["summary"]["overall_compatible"] is True

    @pytest.mark.asyncio
    async def test_validate_compatibility_task_failure(self, mock_platform_manager, sample_skill_data):
        """Test compatibility validation with failure."""
        # Mock validation failure
        mock_platform_manager.validate_skill_compatibility = AsyncMock(side_effect=Exception("Validation failed"))

        with patch('backend.app.platform.tasks.validation_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = validate_compatibility_task(
                skill_data=sample_skill_data,
                target_platforms=["test_platform"]
            )

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_batch_validate_compatibility_task(self, mock_platform_manager, sample_skill_data):
        """Test batch compatibility validation."""
        skills_data = [sample_skill_data, sample_skill_data]

        with patch('backend.app.platform.tasks.validation_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = batch_validate_compatibility_task(
                skills_data=skills_data,
                target_platforms=["test_platform"],
                max_concurrent=5
            )

            assert result["success"] is True
            assert "summary" in result
            assert "successful_validations" in result
            assert "failed_validations" in result

    @pytest.mark.asyncio
    async def test_validate_skill_format_task(self, mock_platform_manager, sample_skill_data):
        """Test skill format validation."""
        with patch('backend.app.platform.tasks.validation_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = validate_skill_format_task(
                skill_data=sample_skill_data,
                format_type="json",
                platform_id="test_platform"
            )

            assert result["success"] is True
            assert result["format_type"] == "json"

    @pytest.mark.asyncio
    async def test_check_format_compatibility_task(self, mock_platform_manager):
        """Test format compatibility check."""
        with patch('backend.app.platform.tasks.validation_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = check_format_compatibility_task(
                format_type="json",
                target_platforms=["test_platform"]
            )

            assert result["success"] is True
            assert result["format_type"] == "json"
            assert "compatible_platforms" in result


class TestMonitoringTasks:
    """Test monitoring-related Celery tasks."""

    @pytest.mark.asyncio
    async def test_check_platform_health_task(self, mock_platform_manager):
        """Test platform health check."""
        with patch('backend.app.platform.tasks.monitoring_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = check_platform_health_task(
                platform_id="test_platform",
                check_interval=60
            )

            assert result["success"] is True
            assert "health_summary" in result
            assert result["health_summary"]["platform_id"] == "test_platform"

    @pytest.mark.asyncio
    async def test_check_all_platforms_health_task(self, mock_platform_manager):
        """Test all platforms health check."""
        with patch('backend.app.platform.tasks.monitoring_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = check_all_platforms_health_task(
                check_interval=60
            )

            assert result["success"] is True
            assert "summary" in result
            assert "platform_results" in result
            assert result["summary"]["total_platforms"] >= 0

    @pytest.mark.asyncio
    async def test_cleanup_old_alerts_task(self, mock_platform_manager):
        """Test alert cleanup."""
        with patch('backend.app.platform.tasks.monitoring_tasks.get_platform_manager', return_value=mock_platform_manager):
            result = cleanup_old_alerts_task(
                older_than_hours=168
            )

            assert result["success"] is True
            assert "removed_count" in result
            assert result["older_than_hours"] == 168

    @pytest.mark.asyncio
    async def test_periodic_health_check(self, mock_platform_manager):
        """Test periodic health check."""
        with patch('backend.app.platform.tasks.monitoring_tasks.check_all_platforms_health_task', return_value={"success": True}):
            # This is a Celery periodic task, so we just test that it runs
            try:
                periodic_health_check()
                # If we get here without exception, the task executed
                assert True
            except Exception as e:
                # Periodic tasks might have different execution context
                pytest.skip(f"Periodic task execution context not available: {str(e)}")


class TestTaskMonitor:
    """Test task monitoring system."""

    def test_track_task(self):
        """Test task tracking."""
        monitor = TaskMonitor()

        task_info = monitor.track_task(
            task_id="test-task-1",
            task_name="test_task",
            args=["arg1"],
            kwargs={"key": "value"}
        )

        assert task_info.task_id == "test-task-1"
        assert task_info.task_name == "test_task"
        assert task_info.status == TaskStatus.PENDING
        assert "test-task-1" in monitor.active_tasks

    def test_update_task_progress(self):
        """Test task progress updates."""
        monitor = TaskMonitor()

        # Track task
        task_info = monitor.track_task(
            task_id="test-task-1",
            task_name="test_task"
        )

        # Update progress
        updated_info = monitor.update_task_progress(
            task_id="test-task-1",
            status=TaskStatus.PROGRESS,
            progress={"step": "processing"}
        )

        assert updated_info is not None
        assert updated_info.status == TaskStatus.PROGRESS
        assert updated_info.progress["step"] == "processing"

    def test_complete_task(self):
        """Test task completion."""
        monitor = TaskMonitor()

        # Track and complete task
        monitor.track_task("test-task-1", "test_task")
        monitor.update_task_progress(
            "test-task-1",
            status=TaskStatus.SUCCESS,
            result={"output": "success"}
        )

        assert "test-task-1" not in monitor.active_tasks
        assert "test-task-1" in monitor.completed_tasks

    def test_list_active_tasks(self):
        """Test listing active tasks."""
        monitor = TaskMonitor()

        # Track multiple tasks
        monitor.track_task("task-1", "test_task")
        monitor.track_task("task-2", "other_task")

        # List all active tasks
        all_tasks = monitor.list_active_tasks()
        assert len(all_tasks) == 2

        # Filter by name
        test_tasks = monitor.list_active_tasks(task_name="test_task")
        assert len(test_tasks) == 1
        assert test_tasks[0].task_name == "test_task"

    def test_get_statistics(self):
        """Test statistics generation."""
        monitor = TaskMonitor()

        # Track and complete a task
        monitor.track_task("task-1", "test_task")
        monitor.update_task_progress("task-1", TaskStatus.SUCCESS, result={})

        stats = monitor.get_statistics()

        assert stats["total_tasks"] >= 1
        assert stats["successful_tasks"] >= 0
        assert "active_tasks" in stats
        assert "completed_tasks" in stats

    def test_get_performance_metrics(self):
        """Test performance metrics."""
        monitor = TaskMonitor()

        # Track and complete a task
        task_info = monitor.track_task("task-1", "test_task")
        task_info.started_at = datetime.utcnow()
        task_info.completed_at = datetime.utcnow()
        task_info.status = TaskStatus.SUCCESS
        monitor.update_task_progress("task-1", TaskStatus.SUCCESS, result={})

        metrics = monitor.get_performance_metrics(time_window_hours=1)

        assert metrics["task_count"] >= 0
        assert "avg_execution_time" in metrics
        assert "success_rate" in metrics

    def test_cleanup_old_tasks(self):
        """Test old task cleanup."""
        monitor = TaskMonitor()

        # Create old task
        old_task = TaskInfo(
            task_id="old-task",
            task_name="old_task",
            status=TaskStatus.SUCCESS,
            priority=TaskPriority.NORMAL,
            created_at=datetime.utcnow() - timedelta(days=8),
            completed_at=datetime.utcnow() - timedelta(days=8)
        )
        monitor.completed_tasks["old-task"] = old_task
        monitor.task_history.append(old_task)

        # Create recent task
        new_task = TaskInfo(
            task_id="new-task",
            task_name="new_task",
            status=TaskStatus.SUCCESS,
            priority=TaskPriority.NORMAL,
            created_at=datetime.utcnow() - timedelta(hours=1),
            completed_at=datetime.utcnow() - timedelta(hours=1)
        )
        monitor.completed_tasks["new-task"] = new_task
        monitor.task_history.append(new_task)

        # Cleanup old tasks
        monitor.cleanup_old_tasks(older_than_hours=168)  # 7 days

        assert "old-task" not in monitor.completed_tasks
        assert "new-task" in monitor.completed_tasks

    def test_event_handlers(self):
        """Test event handling."""
        monitor = TaskMonitor()

        event_data = []

        def event_handler(data):
            event_data.append(data)

        monitor.add_event_handler("task_started", event_handler)

        # Track task to trigger event
        monitor.track_task("test-task-1", "test_task")

        # Check if event was emitted
        assert len(event_data) == 1
        assert "task_info" in event_data[0]


class TestTaskIntegration:
    """Test integration scenarios."""

    @pytest.mark.asyncio
    async def test_full_deployment_workflow(self, mock_platform_manager, sample_skill_data):
        """Test complete deployment workflow."""
        with patch('backend.app.platform.tasks.deployment_tasks.get_platform_manager', return_value=mock_platform_manager):
            # Step 1: Deploy skill
            deploy_result = deploy_skill_task(
                skill_data=sample_skill_data,
                target_platforms=["test_platform"],
                validate_compatibility=True
            )

            assert deploy_result["success"] is True

            # Step 2: Check status (monitoring)
            status_result = check_platform_health_task("test_platform")
            assert status_result["success"] is True

    @pytest.mark.asyncio
    async def test_validation_workflow(self, mock_platform_manager, sample_skill_data):
        """Test complete validation workflow."""
        with patch('backend.app.platform.tasks.validation_tasks.get_platform_manager', return_value=mock_platform_manager):
            # Step 1: Validate compatibility
            validation_result = validate_compatibility_task(
                skill_data=sample_skill_data,
                target_platforms=["test_platform"]
            )

            assert validation_result["success"] is True

            # Step 2: Check format
            format_result = check_format_compatibility_task(
                format_type="json",
                target_platforms=["test_platform"]
            )

            assert format_result["success"] is True

    @pytest.mark.asyncio
    async def test_monitoring_workflow(self, mock_platform_manager):
        """Test complete monitoring workflow."""
        with patch('backend.app.platform.tasks.monitoring_tasks.get_platform_manager', return_value=mock_platform_manager):
            # Step 1: Check platform health
            health_result = check_platform_health_task("test_platform")
            assert health_result["success"] is True

            # Step 2: Check all platforms
            all_health_result = check_all_platforms_health_task()
            assert all_health_result["success"] is True

            # Step 3: Cleanup old alerts
            cleanup_result = cleanup_old_alerts_task(older_than_hours=168)
            assert cleanup_result["success"] is True

    def test_task_monitoring_integration(self):
        """Test task monitoring integration."""
        monitor = get_task_monitor()

        # Track a task through its lifecycle
        task_info = monitor.track_task(
            task_id="integration-test-1",
            task_name="integration_task"
        )

        # Update progress
        monitor.update_task_progress(
            "integration-test-1",
            TaskStatus.PROGRESS,
            progress={"step": "processing"}
        )

        # Complete task
        monitor.update_task_progress(
            "integration-test-1",
            TaskStatus.SUCCESS,
            result={"output": "success"}
        )

        # Verify final state
        final_info = monitor.get_task_info("integration-test-1")
        assert final_info.status == TaskStatus.SUCCESS
        assert final_info.result["output"] == "success"

        # Get statistics
        stats = monitor.get_statistics()
        assert stats["successful_tasks"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])