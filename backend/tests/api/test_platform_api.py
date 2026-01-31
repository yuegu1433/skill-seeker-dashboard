"""API tests for platform management endpoints.

Tests the RESTful API endpoints for platform management,
deployment operations, and compatibility validation.
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

from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.app.platform.api.v1.platforms import router as platforms_router
from backend.app.platform.api.v1.deployment import router as deployment_router
from backend.app.platform.api.v1.compatibility import router as compatibility_router


# Create test application
app = FastAPI(title="Platform Management API")
app.include_router(platforms_router)
app.include_router(deployment_router)
app.include_router(compatibility_router)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_platform_manager():
    """Create mock platform manager."""
    manager = MagicMock()
    manager.get_platform_health = AsyncMock(return_value={
        "test_platform": MagicMock(
            status=MagicMock(value="healthy"),
            is_healthy=True,
            last_check=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
            consecutive_failures=0,
            health_checks=[],
            metrics={}
        )
    })
    manager.monitor.check_platform_health = AsyncMock(return_value=MagicMock(
        status=MagicMock(value="healthy"),
        is_healthy=True,
        last_check=MagicMock(isoformat=lambda: "2024-01-01T00:00:00"),
        health_checks=[]
    ))
    manager.get_statistics = MagicMock(return_value={
        "platforms": {"total": 1, "healthy": 1},
        "deployments": {"total": 0, "success": 0}
    })
    manager.deployer.get_statistics = MagicMock(return_value={
        "total_deployments": 0,
        "successful_deployments": 0,
        "failed_deployments": 0
    })
    return manager


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


class TestPlatformAPI:
    """Test platform management API endpoints."""

    def test_list_platforms(self, client, mock_platform_manager):
        """Test listing all platforms."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/")
            assert response.status_code == 200
            data = response.json()
            assert "platforms" in data
            assert "total" in data

    def test_get_platform(self, client, mock_platform_manager):
        """Test getting specific platform."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/test_platform")
            assert response.status_code == 200
            data = response.json()
            assert data["platform_id"] == "test_platform"
            assert "status" in data
            assert "health_checks" in data

    def test_get_platform_not_found(self, client, mock_platform_manager):
        """Test getting non-existent platform."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/nonexistent")
            assert response.status_code == 404

    def test_trigger_health_check(self, client, mock_platform_manager):
        """Test triggering health check."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.post("/platforms/test_platform/health-check")
            assert response.status_code == 200
            data = response.json()
            assert data["platform_id"] == "test_platform"
            assert "status" in data
            assert "healthy" in data

    def test_check_all_platforms_health(self, client, mock_platform_manager):
        """Test checking all platforms health."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/health-check/all")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

    def test_get_platform_statistics(self, client, mock_platform_manager):
        """Test getting platform statistics."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/statistics")
            assert response.status_code == 200
            data = response.json()
            assert "platforms" in data
            assert "deployments" in data
            assert "alerts" in data

    def test_get_platform_summary(self, client, mock_platform_manager):
        """Test getting platform summary."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/summary")
            assert response.status_code == 200
            data = response.json()
            assert "platforms" in data
            assert "deployments" in data

    def test_get_platform_capabilities(self, client, mock_platform_manager):
        """Test getting platform capabilities."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/test_platform/capabilities")
            assert response.status_code == 200
            data = response.json()
            assert data["platform_id"] == "test_platform"
            assert "capabilities" in data

    def test_get_active_alerts(self, client, mock_platform_manager):
        """Test getting active alerts."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/platforms/alerts/active")
            assert response.status_code == 200
            data = response.json()
            assert "alerts" in data
            assert "total" in data

    def test_acknowledge_alert(self, client, mock_platform_manager):
        """Test acknowledging an alert."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.monitor.acknowledge_alert.return_value = True
            response = client.post(
                "/platforms/alerts/test-alert/acknowledge",
                params={"user": "test_user"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["acknowledged"] is True

    def test_resolve_alert(self, client, mock_platform_manager):
        """Test resolving an alert."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.monitor.resolve_alert.return_value = True
            response = client.post(
                "/platforms/alerts/test-alert/resolve",
                params={"user": "test_user"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["resolved"] is True

    def test_overall_health_check(self, client, mock_platform_manager):
        """Test overall health check."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.health_check = AsyncMock(return_value={"healthy": True})
            response = client.get("/platforms/health")
            assert response.status_code == 200
            data = response.json()
            assert "healthy" in data


class TestDeploymentAPI:
    """Test deployment API endpoints."""

    def test_deploy_skill(self, client, mock_platform_manager, sample_skill_data):
        """Test deploying a skill."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.deploy_skill = AsyncMock(return_value=[])

            deployment_data = {
                "skill_data": sample_skill_data,
                "target_platforms": ["test_platform"],
                "source_format": "json",
                "validate_compatibility": True
            }

            response = client.post("/deployments/", json=deployment_data)
            assert response.status_code == 200
            data = response.json()
            assert "deployments" in data

    def test_get_deployment_status(self, client, mock_platform_manager):
        """Test getting deployment status."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.get_deployment_status = AsyncMock(return_value={
                "deployment_id": "test-deployment",
                "skill_name": "Test Skill",
                "status": "pending",
                "platform": "test_platform"
            })

            response = client.get("/deployments/test-deployment")
            assert response.status_code == 200
            data = response.json()
            assert data["deployment_id"] == "test-deployment"

    def test_get_deployment_status_not_found(self, client, mock_platform_manager):
        """Test getting non-existent deployment."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.get_deployment_status = AsyncMock(return_value=None)

            response = client.get("/deployments/nonexistent")
            assert response.status_code == 404

    def test_list_deployments(self, client, mock_platform_manager):
        """Test listing deployments."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.list_deployments = AsyncMock(return_value=[])

            response = client.get("/deployments/")
            assert response.status_code == 200
            data = response.json()
            assert "deployments" in data

    def test_cancel_deployment(self, client, mock_platform_manager):
        """Test cancelling a deployment."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.cancel_deployment = AsyncMock(return_value=True)

            response = client.post(
                "/deployments/test-deployment/cancel",
                json={"force": False}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["cancelled"] is True

    def test_retry_deployment(self, client, mock_platform_manager):
        """Test retrying a deployment."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.retry_deployment = AsyncMock(return_value={
                "deployment_id": "new-deployment",
                "status": "pending"
            })

            response = client.post(
                "/deployments/test-deployment/retry",
                json={}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["deployment_id"] == "new-deployment"

    def test_get_deployment_statistics(self, client, mock_platform_manager):
        """Test getting deployment statistics."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/deployments/statistics")
            assert response.status_code == 200

    def test_get_active_deployment_count(self, client, mock_platform_manager):
        """Test getting active deployment count."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.deployer.get_active_deployment_count.return_value = 5
            response = client.get("/deployments/active/count")
            assert response.status_code == 200
            data = response.json()
            assert data["active_deployments"] == 5

    def test_cleanup_completed_deployments(self, client, mock_platform_manager):
        """Test cleaning up completed deployments."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.deployer.cleanup_completed_deployments = AsyncMock(return_value=10)
            response = client.post("/deployments/cleanup?older_than_hours=24")
            assert response.status_code == 200
            data = response.json()
            assert data["removed_deployments"] == 10

    def test_get_deployment_queue_size(self, client, mock_platform_manager):
        """Test getting deployment queue size."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.deployer.get_queue_size.return_value = 3
            response = client.get("/deployments/queue/size")
            assert response.status_code == 200
            data = response.json()
            assert data["queue_size"] == 3

    def test_deploy_with_fallback(self, client, mock_platform_manager, sample_skill_data):
        """Test deploying with fallback strategy."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.deploy_with_fallback = AsyncMock(return_value={
                "successful_deployments": [{"platform": "fallback"}],
                "failed_deployments": []
            })

            request_data = {
                "skill_data": sample_skill_data,
                "preferred_platforms": ["platform1", "platform2"],
                "fallback_platforms": ["fallback"]
            }

            response = client.post("/deployments/deploy-with-fallback", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "successful_deployments" in data


class TestCompatibilityAPI:
    """Test compatibility validation API endpoints."""

    def test_validate_skill_compatibility(self, client, mock_platform_manager, sample_skill_data):
        """Test validating skill compatibility."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.validate_skill_compatibility = AsyncMock(return_value={
                "overall_compatible": True,
                "compatibility_score": 85.0,
                "compatible_platforms": ["test_platform"],
                "incompatible_platforms": [],
                "platform_results": {},
                "recommendations": []
            })

            request_data = {
                "skill_data": sample_skill_data,
                "target_platforms": ["test_platform"]
            }

            response = client.post("/compatibility/validate", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert data["overall_compatible"] is True
            assert "compatibility_score" in data

    def test_check_format_compatibility(self, client, mock_platform_manager):
        """Test checking format compatibility."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            response = client.post(
                "/compatibility/check-format",
                json={"test": "data"},
                params={
                    "source_format": "json",
                    "target_platforms": ["test_platform"]
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert "compatible" in data

    def test_get_supported_platforms(self, client, mock_platform_manager):
        """Test getting supported platforms for a format."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/compatibility/supported-platforms?format=json")
            assert response.status_code == 200
            data = response.json()
            assert data["format"] == "json"
            assert "supported_platforms" in data

    def test_get_compatibility_statistics(self, client, mock_platform_manager):
        """Test getting compatibility statistics."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            response = client.get("/compatibility/statistics")
            assert response.status_code == 200

    def test_get_compatibility_recommendations(self, client, mock_platform_manager, sample_skill_data):
        """Test getting compatibility recommendations."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.validate_skill_compatibility = AsyncMock(return_value={
                "recommendations": [{"type": "format_conversion", "priority": "high"}]
            })

            request_data = {
                "skill_data": sample_skill_data,
                "target_platforms": ["test_platform"]
            }

            response = client.post("/compatibility/recommendations", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "recommendations" in data

    def test_find_best_platform(self, client, mock_platform_manager, sample_skill_data):
        """Test finding best compatible platform."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.validate_skill_compatibility = AsyncMock(return_value={
                "platform_results": {
                    "test_platform": MagicMock(valid=True, issues=[], warnings=[])
                },
                "overall_compatible": True
            })

            request_data = {
                "skill_data": sample_skill_data,
                "target_platforms": ["test_platform"]
            }

            response = client.post("/compatibility/best-platform", json=request_data)
            assert response.status_code == 200
            data = response.json()
            assert "best_platform" in data

    def test_get_format_compatibility_matrix(self, client, mock_platform_manager):
        """Test getting format compatibility matrix."""
        with patch('backend.app.platform.api.v1.compatibility.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.converter.get_supported_formats.return_value = {"json", "yaml"}

            response = client.get("/compatibility/formats/compatibility-matrix")
            assert response.status_code == 200
            data = response.json()
            assert "formats" in data
            assert "platforms" in data
            assert "compatibility_matrix" in data


class TestAPIErrorHandling:
    """Test API error handling."""

    def test_platform_not_found_error(self, client, mock_platform_manager):
        """Test platform not found error."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.get_platform_health = AsyncMock(return_value={})

            response = client.get("/platforms/nonexistent")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_deployment_not_found_error(self, client, mock_platform_manager):
        """Test deployment not found error."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.get_deployment_status = AsyncMock(return_value=None)

            response = client.get("/deployments/nonexistent")
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_invalid_request_data(self, client):
        """Test invalid request data."""
        response = client.post("/deployments/", json={})
        assert response.status_code == 422  # Validation error

    def test_server_error_handling(self, client, mock_platform_manager):
        """Test server error handling."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.get_platform_health = AsyncMock(side_effect=Exception("Test error"))

            response = client.get("/platforms/")
            assert response.status_code == 500
            assert "error" in response.json()["detail"].lower()


class TestAPIIntegration:
    """Test API integration scenarios."""

    def test_full_deployment_workflow(self, client, mock_platform_manager, sample_skill_data):
        """Test complete deployment workflow via API."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            # Step 1: Validate compatibility
            mock_platform_manager.validate_skill_compatibility = AsyncMock(return_value={
                "overall_compatible": True,
                "compatible_platforms": ["test_platform"]
            })

            # Step 2: Deploy skill
            mock_platform_manager.deploy_skill = AsyncMock(return_value=[])

            # Step 3: Check deployment status
            mock_platform_manager.get_deployment_status = AsyncMock(return_value={
                "deployment_id": "test-deployment",
                "status": "success"
            })

            # Perform workflow
            validation_response = client.post("/compatibility/validate", json={
                "skill_data": sample_skill_data,
                "target_platforms": ["test_platform"]
            })
            assert validation_response.status_code == 200

            deployment_response = client.post("/deployments/", json={
                "skill_data": sample_skill_data,
                "target_platforms": ["test_platform"]
            })
            assert deployment_response.status_code == 200

            status_response = client.get("/deployments/test-deployment")
            assert status_response.status_code == 200

    def test_batch_operations(self, client, mock_platform_manager, sample_skill_data):
        """Test batch operations via API."""
        with patch('backend.app.platform.api.v1.deployment.get_platform_manager', return_value=mock_platform_manager):
            mock_platform_manager.deployer.deploy_batch = AsyncMock(return_value=[])

            batch_request = {
                "deployments": [
                    {
                        "skill_data": sample_skill_data,
                        "target_platform": "test_platform"
                    }
                ],
                "max_concurrent": 5,
                "wait_for_all": True
            }

            response = client.post("/deployments/batch", json=batch_request)
            assert response.status_code == 200
            data = response.json()
            assert "total" in data
            assert "successful" in data

    def test_alert_management_workflow(self, client, mock_platform_manager):
        """Test alert management workflow."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            # Get active alerts
            mock_platform_manager.monitor.get_active_alerts.return_value = []
            response = client.get("/platforms/alerts/active")
            assert response.status_code == 200

            # Acknowledge alert
            mock_platform_manager.monitor.acknowledge_alert.return_value = True
            response = client.post(
                "/platforms/alerts/test-alert/acknowledge",
                params={"user": "test_user"}
            )
            assert response.status_code == 200

            # Resolve alert
            mock_platform_manager.monitor.resolve_alert.return_value = True
            response = client.post(
                "/platforms/alerts/test-alert/resolve",
                params={"user": "test_user"}
            )
            assert response.status_code == 200

    def test_health_monitoring_workflow(self, client, mock_platform_manager):
        """Test health monitoring workflow."""
        with patch('backend.app.platform.api.v1.platforms.get_platform_manager', return_value=mock_platform_manager):
            # Check overall health
            mock_platform_manager.health_check = AsyncMock(return_value={"healthy": True})
            response = client.get("/platforms/health")
            assert response.status_code == 200

            # Get platform summary
            response = client.get("/platforms/summary")
            assert response.status_code == 200

            # Trigger health check
            response = client.post("/platforms/test_platform/health-check")
            assert response.status_code == 200

            # Check all platforms
            response = client.get("/platforms/health-check/all")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])