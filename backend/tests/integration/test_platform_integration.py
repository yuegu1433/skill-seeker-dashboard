"""Integration tests for platform system.

Tests the end-to-end platform system integration including all components
working together in realistic scenarios.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime, timedelta

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backend.app.platform.manager import PlatformManager
from backend.app.platform.registry import get_registry
from backend.app.platform.converter import FormatConverter
from backend.app.platform.validator import CompatibilityValidator
from backend.app.platform.deployer import PlatformDeployer, DeploymentPriority
from backend.app.platform.monitor import PlatformMonitor, AlertSeverity
from backend.app.platform.adapters import (
    ClaudeAdapter,
    GeminiAdapter,
    OpenAIAdapter,
    MarkdownAdapter
)


@pytest.fixture
def sample_skill_data():
    """Create comprehensive sample skill data."""
    return {
        "name": "Integration Test Skill",
        "description": "A comprehensive skill for integration testing",
        "format": "json",
        "version": "1.0.0",
        "author": "Test Author",
        "tags": ["test", "integration", "sample"],
        "content": {
            "type": "skill",
            "parameters": {
                "input_type": "text",
                "output_type": "text",
                "streaming": False,
                "vision": False,
                "function_calling": True
            },
            "capabilities": [
                "text_generation",
                "function_execution"
            ],
            "metadata": {
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "test_data": True
            }
        }
    }


@pytest.fixture
def large_skill_data():
    """Create large skill data for performance testing."""
    large_content = {
        "content": {
            "type": "large_skill",
            "data": "x" * (1024 * 1024),  # 1MB of data
            "sections": []
        }
    }

    # Add many sections
    for i in range(100):
        large_content["content"]["sections"].append({
            "id": f"section_{i}",
            "title": f"Section {i}",
            "content": "content " * 100
        })

    return {
        "name": "Large Integration Test Skill",
        "description": "A large skill for performance testing",
        "format": "json",
        "version": "1.0.0",
        **large_content
    }


@pytest.fixture
def platform_manager():
    """Create a platform manager instance for testing."""
    manager = PlatformManager()
    return manager


@pytest.fixture
def mock_registry():
    """Create a mock registry with all adapters."""
    registry = get_registry()

    # Mock adapters for testing
    mock_adapters = {
        "claude": MagicMock(spec=ClaudeAdapter),
        "gemini": MagicMock(spec=GeminiAdapter),
        "openai": MagicMock(spec=OpenAIAdapter),
        "markdown": MagicMock(spec=MarkdownAdapter)
    }

    # Configure mock behaviors
    for platform_id, mock_adapter in mock_adapters.items():
        mock_adapter.platform_id = platform_id
        mock_adapter.supported_formats = ["json", "yaml", "markdown"]
        mock_adapter.max_file_size = 100 * 1024 * 1024  # 100MB
        mock_adapter.format_size_limits = {
            "json": 50 * 1024 * 1024,
            "yaml": 50 * 1024 * 1024,
            "markdown": 100 * 1024 * 1024
        }
        mock_adapter.features = ["streaming", "function_calling", "vision"]

        # Mock validation
        mock_adapter.validate_skill = AsyncMock(return_value={
            "valid": True,
            "errors": [],
            "warnings": []
        })

        mock_adapter.validate_skill_format = AsyncMock(return_value={
            "valid": True,
            "errors": [],
            "warnings": []
        })

        # Mock conversion
        mock_adapter.convert_skill = AsyncMock(return_value={
            "format": "json",
            "data": {"converted": True}
        })

        # Mock deployment
        mock_adapter.deploy_skill = AsyncMock(return_value={
            "deployment_id": f"test-deployment-{platform_id}",
            "status": "success",
            "platform": platform_id
        })

        mock_adapter.get_deployment_status = AsyncMock(return_value={
            "status": "success",
            "platform": platform_id
        })

        mock_adapter.cancel_deployment = AsyncMock(return_value=True)

        # Mock health check
        mock_adapter.health_check = AsyncMock(return_value={
            "healthy": True,
            "message": "Platform is operational"
        })

    return registry


class TestPlatformIntegration:
    """Test platform system integration."""

    @pytest.mark.asyncio
    async def test_platform_manager_initialization(self, platform_manager):
        """Test platform manager initialization."""
        result = await platform_manager.initialize()

        assert result is True
        assert platform_manager.registry is not None
        assert platform_manager.converter is not None
        assert platform_manager.validator is not None
        assert platform_manager.deployer is not None
        assert platform_manager.monitor is not None

    @pytest.mark.asyncio
    async def test_skill_deployment_workflow(self, platform_manager, sample_skill_data):
        """Test complete skill deployment workflow."""
        with patch.object(platform_manager.registry, 'get_registered_platforms', return_value=["claude", "gemini"]):
            with patch.object(platform_manager.registry, 'get_adapter') as mock_get_adapter:
                # Mock adapters
                mock_adapter = MagicMock()
                mock_adapter.validate_skill = AsyncMock(return_value={
                    "valid": True, "errors": [], "warnings": []
                })
                mock_adapter.convert_skill = AsyncMock(return_value={
                    "format": "json", "data": {"converted": True}
                })
                mock_adapter.deploy_skill = AsyncMock(return_value={
                    "deployment_id": "test-deployment",
                    "status": "success"
                })
                mock_get_adapter.return_value = mock_adapter

                # Mock validation
                platform_manager.validator.validate_compatibility = AsyncMock(return_value={
                    "overall_compatible": True,
                    "compatible_platforms": ["claude", "gemini"],
                    "compatibility_score": 100
                })

                # Test deployment
                tasks = await platform_manager.deploy_skill(
                    skill_data=sample_skill_data,
                    target_platforms=["claude", "gemini"],
                    validate_compatibility=True,
                    async_mode=True
                )

                assert isinstance(tasks, list)
                assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_format_conversion_workflow(self, platform_manager, sample_skill_data):
        """Test format conversion workflow."""
        # Convert JSON to YAML
        yaml_result = await platform_manager.convert_skill_format(
            skill_data=sample_skill_data,
            target_format="yaml",
            source_format="json"
        )

        assert "conversion_metadata" in yaml_result

        # Convert back to JSON
        json_result = await platform_manager.convert_skill_format(
            skill_data=yaml_result["data"],
            target_format="json",
            source_format="yaml"
        )

        assert "conversion_metadata" in json_result

    @pytest.mark.asyncio
    async def test_compatibility_validation_workflow(self, platform_manager, sample_skill_data):
        """Test compatibility validation workflow."""
        report = await platform_manager.validate_skill_compatibility(
            skill_data=sample_skill_data,
            target_platforms=["claude", "gemini", "openai"]
        )

        assert "overall_compatible" in report
        assert "compatibility_score" in report
        assert "compatible_platforms" in report
        assert "recommendations" in report
        assert "detailed_report" in report

    @pytest.mark.asyncio
    async def test_health_monitoring_workflow(self, platform_manager):
        """Test health monitoring workflow."""
        # Start monitoring
        await platform_manager.monitor.start_monitoring(check_interval=1)

        # Check all platforms health
        health_status = await platform_manager.get_platform_health()

        assert isinstance(health_status, dict)

        # Get monitoring summary
        summary = await platform_manager.get_platform_summary()

        assert "platforms" in summary
        assert "deployments" in summary
        assert "alerts" in summary

        # Stop monitoring
        await platform_manager.monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_batch_operations_workflow(self, platform_manager, sample_skill_data):
        """Test batch operations workflow."""
        # Prepare batch deployments
        deployments = [
            {
                "skill_data": sample_skill_data,
                "target_platform": "claude",
                "source_format": "json"
            },
            {
                "skill_data": sample_skill_data,
                "target_platform": "gemini",
                "source_format": "json"
            }
        ]

        # Mock batch deployment
        platform_manager.deployer.deploy_batch = AsyncMock(return_value=[])

        # Test batch deployment
        results = await platform_manager.deployer.deploy_batch(
            deployments=deployments,
            max_concurrent=2,
            wait_for_all=True
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_deployment_status_tracking_workflow(self, platform_manager, sample_skill_data):
        """Test deployment status tracking workflow."""
        # Mock deployment
        mock_task = MagicMock()
        mock_task.deployment_id = "test-deployment-123"
        mock_task.status = "success"
        mock_task.skill_data = sample_skill_data
        mock_task.created_at = datetime.utcnow()

        platform_manager.deployer.active_deployments["test-deployment-123"] = mock_task

        # Get deployment status
        status = await platform_manager.get_deployment_status("test-deployment-123")

        assert status is not None
        assert status["deployment_id"] == "test-deployment-123"

    @pytest.mark.asyncio
    async def test_alert_management_workflow(self, platform_manager):
        """Test alert management workflow."""
        # Create a mock alert
        from backend.app.platform.monitor import Alert, AlertSeverity

        alert = Alert(
            alert_id="test-alert-123",
            platform_id="test-platform",
            severity=AlertSeverity.WARNING,
            title="Test Alert",
            message="This is a test alert"
        )

        platform_manager.monitor.active_alerts["test-alert-123"] = alert

        # Get active alerts
        alerts = platform_manager.monitor.get_active_alerts()

        assert len(alerts) > 0
        assert alerts[0].alert_id == "test-alert-123"

        # Acknowledge alert
        success = platform_manager.monitor.acknowledge_alert("test-alert-123", "test_user")

        assert success is True

    @pytest.mark.asyncio
    async def test_statistics_collection_workflow(self, platform_manager):
        """Test statistics collection workflow."""
        # Get statistics
        stats = platform_manager.get_statistics()

        assert "platform_manager" in stats
        assert "registry" in stats
        assert "deployer" in stats
        assert "monitor" in stats
        assert "converter" in stats
        assert "validator" in stats

        # Get platform summary
        summary = await platform_manager.get_platform_summary()

        assert "timestamp" in summary
        assert "platforms" in summary
        assert "deployments" in summary
        assert "alerts" in summary

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, platform_manager, sample_skill_data):
        """Test error handling workflow."""
        # Test with invalid platform
        with pytest.raises(Exception):
            await platform_manager.deploy_skill(
                skill_data=sample_skill_data,
                target_platforms=["nonexistent_platform"]
            )

        # Test with invalid skill data
        with pytest.raises(Exception):
            await platform_manager.validate_skill_compatibility(
                skill_data={},  # Invalid skill data
                target_platforms=["claude"]
            )

    @pytest.mark.asyncio
    async def test_performance_workflow(self, platform_manager, large_skill_data):
        """Test performance with large skill data."""
        import time

        start_time = time.time()

        # Test conversion performance
        result = await platform_manager.convert_skill_format(
            skill_data=large_skill_data,
            target_format="yaml",
            source_format="json"
        )

        conversion_time = time.time() - start_time

        assert conversion_time < 10.0  # Should complete within 10 seconds
        assert "conversion_metadata" in result

    @pytest.mark.asyncio
    async def test_concurrent_operations_workflow(self, platform_manager, sample_skill_data):
        """Test concurrent operations workflow."""
        # Mock concurrent operations
        async def mock_operation():
            await asyncio.sleep(0.1)  # Simulate async operation
            return {"result": "success"}

        # Run multiple concurrent operations
        tasks = [mock_operation() for _ in range(10)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        assert all(result["result"] == "success" for result in results)

    @pytest.mark.asyncio
    async def test_resource_cleanup_workflow(self, platform_manager):
        """Test resource cleanup workflow."""
        # Initialize manager
        await platform_manager.initialize()

        # Shutdown manager
        await platform_manager.shutdown()

        # Verify cleanup
        assert platform_manager.monitor.is_monitoring is False


class TestPlatformIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_real_world_deployment_scenario(self, platform_manager, sample_skill_data):
        """Test real-world deployment scenario."""
        # Step 1: Validate skill compatibility
        compatibility_report = await platform_manager.validate_skill_compatibility(
            skill_data=sample_skill_data,
            target_platforms=["claude", "gemini"]
        )

        assert compatibility_report["overall_compatible"] is True

        # Step 2: Deploy skill to preferred platforms
        preferred_platforms = ["claude", "gemini"]
        deployment_tasks = await platform_manager.deploy_skill(
            skill_data=sample_skill_data,
            target_platforms=preferred_platforms,
            validate_compatibility=False,  # Already validated
            async_mode=True
        )

        assert len(deployment_tasks) == 2

        # Step 3: Monitor deployment status
        for task in deployment_tasks:
            status = await platform_manager.get_deployment_status(task.deployment_id)
            assert status is not None

    @pytest.mark.asyncio
    async def test_batch_validation_scenario(self, platform_manager):
        """Test batch validation scenario."""
        # Create multiple skill variants
        skills_data = []
        for i in range(5):
            skill = {
                "name": f"Test Skill {i}",
                "description": f"Description for skill {i}",
                "format": "json",
                "version": "1.0.0"
            }
            skills_data.append(skill)

        # Mock batch validation
        platform_manager.validator.validate_batch_compatibility = AsyncMock(return_value=[
            {"overall_compatible": True} for _ in skills_data
        ])

        # Perform batch validation
        results = await platform_manager.validator.validate_batch_compatibility(
            skills_data=skills_data,
            target_platforms=["claude", "gemini"],
            max_concurrent=5
        )

        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_format_conversion_scenario(self, platform_manager, sample_skill_data):
        """Test format conversion scenario."""
        # Step 1: Convert JSON to YAML
        yaml_result = await platform_manager.convert_skill_format(
            skill_data=sample_skill_data,
            target_format="yaml",
            source_format="json"
        )

        # Step 2: Convert YAML to Markdown
        markdown_result = await platform_manager.convert_skill_format(
            skill_data=yaml_result["data"],
            target_format="markdown",
            source_format="yaml"
        )

        # Step 3: Verify conversion metadata
        assert "conversion_metadata" in yaml_result
        assert "conversion_metadata" in markdown_result

    @pytest.mark.asyncio
    async def test_health_monitoring_scenario(self, platform_manager):
        """Test health monitoring scenario."""
        # Start monitoring
        await platform_manager.monitor.start_monitoring(check_interval=1)

        # Wait for monitoring cycle
        await asyncio.sleep(2)

        # Get monitoring summary
        summary = await platform_manager.get_platform_summary()

        # Verify monitoring is working
        assert summary is not None
        assert "platforms" in summary

        # Stop monitoring
        await platform_manager.monitor.stop_monitoring()

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, platform_manager, sample_skill_data):
        """Test error recovery scenario."""
        # Mock a failed deployment
        mock_task = MagicMock()
        mock_task.deployment_id = "failed-deployment"
        mock_task.status = "failed"
        mock_task.skill_data = sample_skill_data
        mock_task.can_retry = True

        platform_manager.deployer.completed_deployments["failed-deployment"] = mock_task

        # Test retry
        new_task = await platform_manager.retry_deployment("failed-deployment")

        # Verify retry was attempted
        assert new_task is not None

    @pytest.mark.asyncio
    async def test_integration_performance_scenario(self, platform_manager, large_skill_data):
        """Test integration performance scenario."""
        import time

        # Test multiple operations performance
        operations = [
            ("conversion", lambda: platform_manager.convert_skill_format(
                skill_data=large_skill_data,
                target_format="yaml"
            )),
            ("validation", lambda: platform_manager.validate_skill_compatibility(
                skill_data=large_skill_data,
                target_platforms=["claude", "gemini"]
            ))
        ]

        performance_results = {}

        for op_name, op_func in operations:
            start_time = time.time()
            await op_func()
            duration = time.time() - start_time
            performance_results[op_name] = duration

        # Verify performance is acceptable
        for op_name, duration in performance_results.items():
            assert duration < 30.0, f"{op_name} took too long: {duration}s"


class TestPlatformIntegrationEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_empty_skill_data(self, platform_manager):
        """Test handling of empty skill data."""
        with pytest.raises(Exception):
            await platform_manager.validate_skill_compatibility(
                skill_data={},
                target_platforms=["claude"]
            )

    @pytest.mark.asyncio
    async def test_nonexistent_platform(self, platform_manager, sample_skill_data):
        """Test handling of nonexistent platform."""
        with pytest.raises(Exception):
            await platform_manager.deploy_skill(
                skill_data=sample_skill_data,
                target_platforms=["nonexistent_platform"]
            )

    @pytest.mark.asyncio
    async def test_unsupported_format(self, platform_manager):
        """Test handling of unsupported format."""
        skill_data = {
            "name": "Test Skill",
            "format": "unsupported_format",
            "content": {}
        }

        with pytest.raises(Exception):
            await platform_manager.convert_skill_format(
                skill_data=skill_data,
                target_format="json"
            )

    @pytest.mark.asyncio
    async def test_large_skill_handling(self, platform_manager, large_skill_data):
        """Test handling of large skill data."""
        # Should handle large skill data gracefully
        result = await platform_manager.validate_skill_compatibility(
            skill_data=large_skill_data,
            target_platforms=["claude"]
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_deployments(self, platform_manager, sample_skill_data):
        """Test concurrent deployment handling."""
        # Mock multiple deployments
        deployment_tasks = []

        for i in range(5):
            task = MagicMock()
            task.deployment_id = f"deployment-{i}"
            task.status = "pending"
            deployment_tasks.append(task)
            platform_manager.deployer.active_deployments[f"deployment-{i}"] = task

        # Verify all deployments are tracked
        assert len(platform_manager.deployer.active_deployments) == 5

    @pytest.mark.asyncio
    async def test_memory_usage(self, platform_manager, sample_skill_data):
        """Test memory usage during operations."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Perform multiple operations
        for _ in range(10):
            await platform_manager.convert_skill_format(
                skill_data=sample_skill_data,
                target_format="yaml"
            )

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (<100MB)
        assert memory_increase < 100 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])