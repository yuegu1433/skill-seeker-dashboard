"""Tests for Skill Celery Tasks.

This module contains comprehensive unit tests for skill-related
Celery tasks including monitoring, retries, and async operations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from celery.exceptions import Retry
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.tasks.skill_tasks import (
    celery_app,
    import_skills_async,
    export_skills_async,
    bulk_activate_skills,
    bulk_deactivate_skills,
    bulk_delete_skills,
    calculate_quality_score_async,
    recalculate_quality_scores,
    generate_usage_report_async,
    generate_daily_analytics_report,
    create_version_snapshot,
    cleanup_old_versions,
    cleanup_old_analytics,
    check_inactive_skills,
    send_notification,
    monitor_skill_health,
    collect_system_metrics,
)


class TestImportExportTasks:
    """Test import/export Celery tasks."""

    @pytest.mark.asyncio
    async def test_import_skills_async_success(self):
        """Test successful async import."""
        # Mock the import process
        with patch('app.tasks.skill_tasks.Mock') as mock_importer:
            mock_importer.return_value.import_skills.return_value = Mock(
                import_id="import_123",
                total_files=5,
                successful_imports=5,
            )

            # Execute task
            result = import_skills_async.delay(
                source_path="/tmp/import.yaml",
                format="yaml",
                user_id="test_user",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["import_id"] == "import_123"
            assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_import_skills_async_failure(self):
        """Test failed async import."""
        # Mock failed import
        with patch('app.tasks.skill_tasks.Mock') as mock_importer:
            mock_importer.return_value.import_skills.return_value = None

            # Execute task
            result = import_skills_async.delay(
                source_path="/tmp/invalid.yaml",
                format="yaml",
                user_id="test_user",
            )

            # Should fail
            with pytest.raises(Exception):
                result.get()

    @pytest.mark.asyncio
    async def test_import_skills_async_retry(self):
        """Test import task retry mechanism."""
        # Mock importer that raises exception
        with patch('app.tasks.skill_tasks.Mock') as mock_importer:
            mock_importer.return_value.import_skills.side_effect = Exception("Temporary error")

            # Execute task
            result = import_skills_async.delay(
                source_path="/tmp/import.yaml",
                format="yaml",
                user_id="test_user",
            )

            # Should retry
            with pytest.raises(Exception):
                result.get()

    @pytest.mark.asyncio
    async def test_export_skills_async_success(self):
        """Test successful async export."""
        # Mock the export process
        with patch('app.tasks.skill_tasks.Mock') as mock_exporter:
            mock_exporter.return_value.export_skills.return_value = Mock(
                export_id="export_123",
                format="json",
                file_path="/tmp/export.json",
            )

            # Execute task
            result = export_skills_async.delay(
                skill_ids=["skill1", "skill2"],
                destination_path="/tmp/export.json",
                format="json",
                user_id="test_user",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["export_id"] == "export_123"
            assert data["status"] == "started"

    @pytest.mark.asyncio
    async def test_export_skills_async_failure(self):
        """Test failed async export."""
        # Mock failed export
        with patch('app.tasks.skill_tasks.Mock') as mock_exporter:
            mock_exporter.return_value.export_skills.return_value = None

            # Execute task
            result = export_skills_async.delay(
                skill_ids=["skill1"],
                destination_path="/tmp/export.json",
                format="json",
                user_id="test_user",
            )

            # Should fail
            with pytest.raises(Exception):
                result.get()


class TestBulkOperationsTasks:
    """Test bulk operations Celery tasks."""

    @pytest.mark.asyncio
    async def test_bulk_activate_skills_success(self):
        """Test successful bulk activate."""
        # Mock the bulk operation
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.return_value = Mock(
                successful=5,
                failed=0,
                processed=5,
            )

            # Execute task
            result = bulk_activate_skills.delay(
                skill_ids=["skill1", "skill2", "skill3", "skill4", "skill5"],
                user_id="test_user",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["operation"] == "activate"
            assert data["total"] == 5
            assert data["successful"] == 5
            assert data["failed"] == 0

    @pytest.mark.asyncio
    async def test_bulk_deactivate_skills_success(self):
        """Test successful bulk deactivate."""
        # Mock the bulk operation
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.return_value = Mock(
                successful=3,
                failed=0,
                processed=3,
            )

            # Execute task
            result = bulk_deactivate_skills.delay(
                skill_ids=["skill1", "skill2", "skill3"],
                user_id="test_user",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["operation"] == "deactivate"
            assert data["total"] == 3
            assert data["successful"] == 3

    @pytest.mark.asyncio
    async def test_bulk_delete_skills_success(self):
        """Test successful bulk delete."""
        # Mock the bulk operation
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.return_value = Mock(
                successful=2,
                failed=0,
                processed=2,
            )

            # Execute task
            result = bulk_delete_skills.delay(
                skill_ids=["skill1", "skill2"],
                user_id="test_user",
                confirm_deletion=True,
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["operation"] == "delete"
            assert data["total"] == 2
            assert data["successful"] == 2

    @pytest.mark.asyncio
    async def test_bulk_delete_skills_without_confirmation(self):
        """Test bulk delete without confirmation."""
        # Execute task without confirmation
        result = bulk_delete_skills.delay(
            skill_ids=["skill1"],
            user_id="test_user",
            confirm_deletion=False,
        )

        # Should fail
        with pytest.raises(Exception):
            result.get()

    @pytest.mark.asyncio
    async def test_bulk_operations_partial_failure(self):
        """Test bulk operation with partial failures."""
        # Mock partial failure
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.return_value = Mock(
                successful=4,
                failed=1,
                processed=5,
            )

            # Execute task
            result = bulk_activate_skills.delay(
                skill_ids=["skill1", "skill2", "skill3", "skill4", "skill5"],
                user_id="test_user",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["successful"] == 4
            assert data["failed"] == 1


class TestQualityScoreTasks:
    """Test quality score Celery tasks."""

    @pytest.mark.asyncio
    async def test_calculate_quality_score_success(self):
        """Test successful quality score calculation."""
        # Mock quality calculation
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.calculate_quality_score.return_value = Mock(
                skill_id="test-skill",
                overall_score=85.5,
            )

            # Execute task
            result = calculate_quality_score_async.delay(skill_id="test-skill")

            # Check result
            assert result.successful()
            data = result.get()
            assert data["skill_id"] == "test-skill"
            assert data["quality_score"] == 85.5

    @pytest.mark.asyncio
    async def test_calculate_quality_score_failure(self):
        """Test failed quality score calculation."""
        # Mock failed calculation
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.calculate_quality_score.return_value = None

            # Execute task
            result = calculate_quality_score_async.delay(skill_id="nonexistent")

            # Should fail
            with pytest.raises(Exception):
                result.get()

    @pytest.mark.asyncio
    async def test_recalculate_quality_scores_success(self):
        """Test successful recalculation of all quality scores."""
        # Mock skills list
        skills = [
            Mock(id=f"skill{i}", name=f"Skill {i}")
            for i in range(1, 11)
        ]

        # Mock the recalculation process
        with patch('app.tasks.skill_tasks.Mock') as mock_manager, \
             patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_manager.return_value.list_skills.return_value = Mock(
                items=skills,
                total=10,
            )
            mock_analytics.return_value.calculate_quality_score.return_value = Mock(
                overall_score=80.0,
            )

            # Execute task
            result = recalculate_quality_scores.delay(batch_size=100)

            # Check result
            assert result.successful()
            data = result.get()
            assert data["total_skills"] == 10
            assert data["processed"] == 10
            assert data["failed"] == 0

    @pytest.mark.asyncio
    async def test_recalculate_quality_scores_with_failures(self):
        """Test recalculation with some failures."""
        # Mock skills list
        skills = [
            Mock(id=f"skill{i}", name=f"Skill {i}")
            for i in range(1, 11)
        ]

        # Mock partial failure
        with patch('app.tasks.skill_tasks.Mock') as mock_manager, \
             patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_manager.return_value.list_skills.return_value = Mock(
                items=skills,
                total=10,
            )
            # First 5 succeed, next 5 fail
            mock_analytics.return_value.calculate_quality_score.side_effect = [
                Mock(overall_score=80.0) if i <= 5 else None
                for i in range(1, 11)
            ]

            # Execute task
            result = recalculate_quality_scores.delay(batch_size=100)

            # Check result
            assert result.successful()
            data = result.get()
            assert data["total_skills"] == 10
            assert data["processed"] == 5
            assert data["failed"] == 5


class TestAnalyticsTasks:
    """Test analytics Celery tasks."""

    @pytest.mark.asyncio
    async def test_generate_usage_report_success(self):
        """Test successful usage report generation."""
        # Mock report generation
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.generate_usage_report.return_value = Mock(
                report_id="report_123",
                title="Usage Report",
                summary={
                    "total_skills": 100,
                    "active_skills": 85,
                    "total_executions": 5000,
                },
            )

            # Execute task
            result = generate_usage_report_async.delay(
                skill_ids=["skill1", "skill2"],
                time_range="LAST_MONTH",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["report_id"] == "report_123"
            assert data["summary"]["total_skills"] == 100

    @pytest.mark.asyncio
    async def test_generate_daily_analytics_report_success(self):
        """Test successful daily analytics report."""
        # Mock skills list
        skills = [
            Mock(id=f"skill{i}", name=f"Skill {i}")
            for i in range(1, 101)
        ]

        # Mock daily report generation
        with patch('app.tasks.skill_tasks.Mock') as mock_manager, \
             patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_manager.return_value.list_skills.return_value = Mock(
                items=skills,
                total=100,
            )
            mock_analytics.return_value.generate_usage_report.return_value = Mock(
                report_id=f"daily_report_{datetime.now().strftime('%Y%m%d')}",
                title=f"Daily Analytics Report - {datetime.now().strftime('%Y-%m-%d')}",
                summary={
                    "total_skills": 100,
                    "active_skills": 90,
                    "total_executions": 10000,
                },
            )

            # Execute task
            result = generate_daily_analytics_report.delay()

            # Check result
            assert result.successful()
            data = result.get()
            assert "date" in data
            assert data["summary"]["total_skills"] == 100

    @pytest.mark.asyncio
    async def test_generate_report_without_skill_ids(self):
        """Test report generation without specific skill IDs."""
        # Mock report generation
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.generate_usage_report.return_value = Mock(
                report_id="report_all",
                title="All Skills Report",
                summary={"total_skills": 200},
            )

            # Execute task without skill IDs
            result = generate_usage_report_async.delay(
                skill_ids=None,
                time_range="LAST_MONTH",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["report_id"] == "report_all"


class TestVersionControlTasks:
    """Test version control Celery tasks."""

    @pytest.mark.asyncio
    async def test_create_version_snapshot_success(self):
        """Test successful version snapshot creation."""
        # Mock version creation
        with patch('app.tasks.skill_tasks.Mock') as mock_version_manager:
            mock_version_manager.return_value.create_version.return_value = Mock(
                commit_id="commit_123",
                version="1.0.0",
            )

            # Execute task
            result = create_version_snapshot.delay(
                skill_id="test-skill",
                version="1.0.0",
                author="Test Author",
                message="Initial version",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["skill_id"] == "test-skill"
            assert data["version"] == "1.0.0"
            assert data["commit_id"] == "commit_123"

    @pytest.mark.asyncio
    async def test_create_version_snapshot_failure(self):
        """Test failed version snapshot creation."""
        # Mock failed version creation
        with patch('app.tasks.skill_tasks.Mock') as mock_version_manager:
            mock_version_manager.return_value.create_version.return_value = None

            # Execute task
            result = create_version_snapshot.delay(
                skill_id="test-skill",
                version="1.0.0",
                author="Test Author",
                message="Initial version",
            )

            # Should fail
            with pytest.raises(Exception):
                result.get()

    @pytest.mark.asyncio
    async def test_cleanup_old_versions_success(self):
        """Test successful version cleanup."""
        # Mock version cleanup
        with patch('app.tasks.skill_tasks.Mock') as mock_version_manager:
            mock_version_manager.return_value.cleanup_old_versions.return_value = 15

            # Execute task
            result = cleanup_old_versions.delay(
                skill_id="test-skill",
                keep_count=50,
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["skill_id"] == "test-skill"
            assert data["cleaned_versions"] == 15

    @pytest.mark.asyncio
    async def test_cleanup_old_versions_failure(self):
        """Test failed version cleanup."""
        # Mock failed cleanup
        with patch('app.tasks.skill_tasks.Mock') as mock_version_manager:
            mock_version_manager.return_value.cleanup_old_versions.side_effect = Exception("Cleanup failed")

            # Execute task
            result = cleanup_old_versions.delay(
                skill_id="test-skill",
                keep_count=50,
            )

            # Should fail
            with pytest.raises(Exception):
                result.get()


class TestScheduledTasks:
    """Test scheduled Celery tasks."""

    @pytest.mark.asyncio
    async def test_cleanup_old_analytics_success(self):
        """Test successful analytics cleanup."""
        # Mock cleanup
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.cleanup_old_data = Mock()

            # Execute task
            result = cleanup_old_analytics.delay(days_old=30)

            # Check result
            assert result.successful()
            data = result.get()
            assert data["days_old"] == 30

    @pytest.mark.asyncio
    async def test_cleanup_old_analytics_failure(self):
        """Test failed analytics cleanup."""
        # Mock failed cleanup
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.cleanup_old_data.side_effect = Exception("Cleanup failed")

            # Execute task
            result = cleanup_old_analytics.delay(days_old=30)

            # Should fail
            with pytest.raises(Exception):
                result.get()

    @pytest.mark.asyncio
    async def test_check_inactive_skills_success(self):
        """Test successful inactive skills check."""
        # Mock inactive skills
        inactive_skills = [
            Mock(
                id=f"inactive_skill{i}",
                name=f"Inactive Skill {i}",
                last_executed=datetime.now() - timedelta(days=35)
            )
            for i in range(1, 11)
        ]

        # Mock the check
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.list_skills.return_value = Mock(
                items=inactive_skills,
                total=10,
            )

            # Execute task
            result = check_inactive_skills.delay(days_inactive=30)

            # Check result
            assert result.successful()
            data = result.get()
            assert data["inactive_count"] == 10
            assert data["days_inactive"] == 30

    @pytest.mark.asyncio
    async def test_check_inactive_skills_no_inactive(self):
        """Test inactive skills check with no inactive skills."""
        # Mock active skills
        active_skills = [
            Mock(
                id=f"active_skill{i}",
                name=f"Active Skill {i}",
                last_executed=datetime.now() - timedelta(days=5)
            )
            for i in range(1, 11)
        ]

        # Mock the check
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.list_skills.return_value = Mock(
                items=active_skills,
                total=10,
            )

            # Execute task
            result = check_inactive_skills.delay(days_inactive=30)

            # Check result
            assert result.successful()
            data = result.get()
            assert data["inactive_count"] == 0


class TestNotificationTasks:
    """Test notification Celery tasks."""

    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending."""
        # Mock notification service
        with patch('app.tasks.skill_tasks.Mock') as mock_service:
            mock_service.return_value.send.return_value = True

            # Execute task
            result = send_notification.delay(
                user_id="test_user",
                notification_type="info",
                title="Test Notification",
                message="This is a test notification",
                skill_id="test-skill",
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["user_id"] == "test_user"
            assert data["type"] == "info"

    @pytest.mark.asyncio
    async def test_send_notification_failure(self):
        """Test failed notification sending."""
        # Mock failed notification
        with patch('app.tasks.skill_tasks.Mock') as mock_service:
            mock_service.return_value.send.return_value = False

            # Execute task
            result = send_notification.delay(
                user_id="test_user",
                notification_type="info",
                title="Test",
                message="Test message",
            )

            # Should fail
            with pytest.raises(Exception):
                result.get()

    @pytest.mark.asyncio
    async def test_send_notification_without_skill(self):
        """Test notification without skill ID."""
        # Mock notification service
        with patch('app.tasks.skill_tasks.Mock') as mock_service:
            mock_service.return_value.send.return_value = True

            # Execute task without skill ID
            result = send_notification.delay(
                user_id="test_user",
                notification_type="info",
                title="Test Notification",
                message="This is a test notification",
                skill_id=None,
            )

            # Check result
            assert result.successful()
            data = result.get()
            assert data["user_id"] == "test_user"


class TestMonitoringTasks:
    """Test monitoring Celery tasks."""

    @pytest.mark.asyncio
    async def test_monitor_skill_health_success(self):
        """Test successful health monitoring."""
        # Execute task
        result = monitor_skill_health.delay()

        # Check result
        assert result.successful()
        data = result.get()
        assert "timestamp" in data
        assert "services" in data
        assert "metrics" in data
        assert data["services"]["database"] == "healthy"
        assert data["services"]["cache"] == "healthy"
        assert data["services"]["queue"] == "healthy"

    @pytest.mark.asyncio
    async def test_collect_system_metrics_success(self):
        """Test successful metrics collection."""
        # Mock metrics collection
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.record_metric = Mock()

            # Execute task
            result = collect_system_metrics.delay()

            # Check result
            assert result.successful()
            data = result.get()
            assert data["metrics_count"] == 5
            assert data["message"] == "System metrics collected successfully"

    @pytest.mark.asyncio
    async def test_collect_system_metrics_failure(self):
        """Test failed metrics collection."""
        # Mock failed metrics collection
        with patch('app.tasks.skill_tasks.Mock') as mock_analytics:
            mock_analytics.return_value.record_metric.side_effect = Exception("Collection failed")

            # Execute task
            result = collect_system_metrics.delay()

            # Should fail
            with pytest.raises(Exception):
                result.get()


class TestTaskRetryMechanism:
    """Test task retry mechanisms."""

    @pytest.mark.asyncio
    async def test_retry_on_temporary_failure(self):
        """Test retry on temporary failure."""
        # Mock temporary failure
        call_count = 0

        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"

        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.side_effect = [
                Exception("Temp error"),
                Exception("Temp error"),
                Mock(successful=1, failed=0, processed=1),
            ]

            # Execute task
            result = bulk_activate_skills.delay(
                skill_ids=["skill1"],
                user_id="test_user",
            )

            # Should succeed after retries
            assert result.successful()

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test max retries exceeded."""
        # Mock permanent failure
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.side_effect = Exception("Permanent error")

            # Execute task
            result = bulk_activate_skills.delay(
                skill_ids=["skill1"],
                user_id="test_user",
            )

            # Should fail after max retries
            with pytest.raises(Exception):
                result.get()


class TestTaskStatusAndProgress:
    """Test task status and progress tracking."""

    @pytest.mark.asyncio
    async def test_task_status_tracking(self):
        """Test that task status is properly tracked."""
        # Mock operation
        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.return_value = Mock(
                successful=5,
                failed=0,
                processed=5,
            )

            # Execute task
            result = bulk_activate_skills.delay(
                skill_ids=["skill1", "skill2", "skill3", "skill4", "skill5"],
                user_id="test_user",
            )

            # Check task info
            assert result.state == "SUCCESS"
            assert result.successful()

    @pytest.mark.asyncio
    async def test_task_progress_updates(self):
        """Test that task progress is properly updated."""
        # Mock progress tracking
        progress_updates = []

        def mock_bulk_operation(operation):
            # Simulate progress
            progress_updates.append(f"Processing {len(operation.skill_ids)} skills")
            return Mock(
                successful=len(operation.skill_ids),
                failed=0,
                processed=len(operation.skill_ids),
            )

        with patch('app.tasks.skill_tasks.Mock') as mock_manager:
            mock_manager.return_value.bulk_operation.side_effect = mock_bulk_operation

            # Execute task
            result = bulk_activate_skills.delay(
                skill_ids=["skill1", "skill2"],
                user_id="test_user",
            )

            # Check result
            assert result.successful()
            assert len(progress_updates) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
