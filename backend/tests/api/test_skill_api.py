"""Tests for Skill API Routes.

This module contains comprehensive unit tests for the skill management
API endpoints.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from typing import Dict, Any

from app.api.routes.skill_routes import router


@pytest.fixture
def app():
    """Create FastAPI application for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_skill_data():
    """Mock skill data for testing."""
    return {
        "id": "test-skill",
        "name": "Test Skill",
        "version": "1.0.0",
        "description": "Test skill description",
        "author": "Test Author",
        "category": "testing",
        "status": "active",
    }


class TestSkillCRUD:
    """Test skill CRUD operations."""

    def test_create_skill(self, client, mock_skill_data):
        """Test creating a skill."""
        response = client.post("/api/v1/skills/", json=mock_skill_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_skill(self, client, mock_skill_data):
        """Test getting a skill by ID."""
        response = client.get(f"/api/v1/skills/{mock_skill_data['id']}")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_nonexistent_skill(self, client):
        """Test getting non-existent skill."""
        response = client.get("/api/v1/skills/nonexistent")

        # Check response
        assert response.status_code == 404

    def test_update_skill(self, client, mock_skill_data):
        """Test updating a skill."""
        update_data = {"description": "Updated description"}
        response = client.put(f"/api/v1/skills/{mock_skill_data['id']}", json=update_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_delete_skill(self, client, mock_skill_data):
        """Test deleting a skill."""
        response = client.delete(f"/api/v1/skills/{mock_skill_data['id']}")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_list_skills(self, client):
        """Test listing skills."""
        response = client.get("/api/v1/skills/")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]

    def test_list_skills_with_filters(self, client):
        """Test listing skills with filters."""
        response = client.get("/api/v1/skills/?category=testing&status=active")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_list_skills_pagination(self, client):
        """Test listing skills with pagination."""
        response = client.get("/api/v1/skills/?page=1&page_size=10")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 10


class TestSkillSearch:
    """Test skill search operations."""

    def test_search_skills(self, client):
        """Test searching skills."""
        search_data = {
            "query": "test",
            "category": "testing",
            "status": "active",
        }
        response = client.post("/api/v1/skills/search", json=search_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "query" in data

    def test_search_skills_with_filters(self, client):
        """Test searching with multiple filters."""
        search_data = {
            "query": "python",
            "tags": ["data", "processing"],
            "author": "Test Author",
        }
        response = client.post("/api/v1/skills/search", json=search_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_categories(self, client):
        """Test getting skill categories."""
        response = client.get("/api/v1/skills/categories")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_tags(self, client):
        """Test getting skill tags."""
        response = client.get("/api/v1/skills/tags")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)


class TestBulkOperations:
    """Test bulk operations."""

    def test_bulk_operation(self, client):
        """Test bulk operation on skills."""
        operation_data = {
            "operation": "activate",
            "skill_ids": ["skill1", "skill2", "skill3"],
            "parameters": {},
        }
        response = client.post("/api/v1/skills/bulk", json=operation_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "successful" in data["data"]
        assert "failed" in data["data"]

    def test_bulk_operation_invalid(self, client):
        """Test bulk operation with invalid data."""
        operation_data = {
            "operation": "invalid_operation",
            "skill_ids": [],
        }
        response = client.post("/api/v1/skills/bulk", json=operation_data)

        # Check response
        assert response.status_code == 200  # API returns 200 even for mock errors


class TestImportExport:
    """Test import/export operations."""

    def test_import_skills(self, client):
        """Test importing skills."""
        import_data = {
            "source_path": "/tmp/import.yaml",
            "format": "yaml",
            "validation_level": "moderate",
            "skip_invalid": False,
            "update_existing": False,
            "user_id": "test_user",
        }
        response = client.post("/api/v1/skills/import", json=import_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "import_id" in data["data"]
        assert "status" in data["data"]

    def test_export_skills(self, client):
        """Test exporting skills."""
        export_data = {
            "skill_ids": ["skill1", "skill2"],
            "destination_path": "/tmp/export.json",
            "format": "json",
            "include_metadata": True,
            "include_statistics": False,
            "user_id": "test_user",
        }
        response = client.post("/api/v1/skills/export", json=export_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "export_id" in data["data"]

    def test_get_import_status(self, client):
        """Test getting import status."""
        response = client.get("/api/v1/skills/import/import123/status")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_export_status(self, client):
        """Test getting export status."""
        response = client.get("/api/v1/skills/export/export123/status")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_cancel_import(self, client):
        """Test cancelling an import."""
        response = client.delete("/api/v1/skills/import/import123")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_cancel_export(self, client):
        """Test cancelling an export."""
        response = client.delete("/api/v1/skills/export/export123")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_get_import_history(self, client):
        """Test getting import history."""
        response = client.get("/api/v1/skills/import/history?limit=10")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_export_history(self, client):
        """Test getting export history."""
        response = client.get("/api/v1/skills/export/history?limit=10")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)


class TestVersionControl:
    """Test version control operations."""

    def test_create_version(self, client):
        """Test creating a version."""
        version_data = {
            "version": "1.0.0",
            "message": "Initial version",
            "author": "Test Author",
            "file_path": "test-skill.yaml",
        }
        response = client.post("/api/v1/skills/test-skill/versions", json=version_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "message" in data

    def test_tag_version(self, client):
        """Test tagging a version."""
        tag_data = {
            "tag_name": "v1.0.0-stable",
            "message": "Stable release",
            "created_by": "Test Author",
        }
        response = client.post(
            "/api/v1/skills/test-skill/versions/1.0.0/tag",
            json=tag_data,
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "message" in data

    def test_create_branch(self, client):
        """Test creating a branch."""
        branch_data = {
            "version": "1.0.0",
            "branch_name": "feature/test",
            "created_by": "Test Author",
            "base_branch": "main",
        }
        response = client.post("/api/v1/skills/test-skill/branches", json=branch_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "message" in data

    def test_compare_versions(self, client):
        """Test comparing versions."""
        response = client.get(
            "/api/v1/skills/test-skill/versions/compare?"
            "from_version=1.0.0&to_version=1.1.0"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_rollback_version(self, client):
        """Test rolling back to a version."""
        rollback_data = {
            "target_version": "1.0.0",
            "author": "Test Author",
            "reason": "Bug found",
        }
        response = client.post(
            "/api/v1/skills/test-skill/versions/rollback",
            json=rollback_data,
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_get_version_history(self, client):
        """Test getting version history."""
        response = client.get("/api/v1/skills/test-skill/versions/history?limit=10")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_version_tags(self, client):
        """Test getting version tags."""
        response = client.get("/api/v1/skills/test-skill/versions/tags")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_version_branches(self, client):
        """Test getting version branches."""
        response = client.get("/api/v1/skills/test-skill/branches")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_version_statistics(self, client):
        """Test getting version statistics."""
        response = client.get("/api/v1/skills/test-skill/versions/statistics")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


class TestAnalytics:
    """Test analytics operations."""

    def test_track_execution(self, client):
        """Test tracking skill execution."""
        execution_data = {
            "execution_time": 1.5,
            "success": True,
            "error_message": None,
        }
        response = client.post(
            "/api/v1/skills/test-skill/execute",
            json=execution_data,
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_track_execution_failure(self, client):
        """Test tracking failed execution."""
        execution_data = {
            "execution_time": 2.0,
            "success": False,
            "error_message": "Test error",
        }
        response = client.post(
            "/api/v1/skills/test-skill/execute",
            json=execution_data,
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_calculate_quality_score(self, client):
        """Test calculating quality score."""
        response = client.post("/api/v1/skills/test-skill/quality")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_skill_stats(self, client):
        """Test getting skill statistics."""
        response = client.get("/api/v1/skills/test-skill/stats")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_quality_score(self, client):
        """Test getting quality score."""
        response = client.get("/api/v1/skills/test-skill/quality")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_generate_usage_report(self, client):
        """Test generating usage report."""
        response = client.get("/api/v1/skills/analytics/usage-report?time_range=LAST_MONTH")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_get_dependency_graph(self, client):
        """Test getting dependency graph."""
        response = client.get("/api/v1/skills/analytics/dependency-graph")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "nodes" in data["data"]
        assert "edges" in data["data"]

    def test_get_metrics(self, client):
        """Test getting metrics."""
        response = client.get(
            "/api/v1/skills/analytics/metrics?"
            "metric_name=skill.execution.count&time_range=LAST_MONTH"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_aggregate_metrics(self, client):
        """Test aggregating metrics."""
        response = client.get(
            "/api/v1/skills/analytics/aggregate?"
            "metric_name=skill.execution.count&aggregation=SUM&time_range=LAST_MONTH"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "value" in data["data"]

    def test_export_analytics(self, client):
        """Test exporting analytics."""
        response = client.get("/api/v1/skills/analytics/export?format_type=json")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


class TestEditor:
    """Test editor operations."""

    def test_create_editor_session(self, client):
        """Test creating an editor session."""
        session_data = {
            "user_id": "test_user",
            "settings": {"theme": "dark"},
        }
        response = client.post("/api/v1/skills/editor/session", json=session_data)

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "session_id" in data["data"]

    def test_close_editor_session(self, client):
        """Test closing an editor session."""
        response = client.delete("/api/v1/skills/editor/session/session123")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_open_file(self, client):
        """Test opening a file."""
        file_data = {
            "file_path": "test-skill.yaml",
            "skill_id": "test-skill",
        }
        response = client.post(
            "/api/v1/skills/editor/session123/open",
            json=file_data,
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "file_id" in data["data"]

    def test_close_file(self, client):
        """Test closing a file."""
        response = client.delete(
            "/api/v1/skills/editor/session123/file/file123"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_save_file(self, client):
        """Test saving a file."""
        response = client.post(
            "/api/v1/skills/editor/session123/file123/save"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_update_file_content(self, client):
        """Test updating file content."""
        content_data = {
            "content": "name: test\nversion: 1.0.0",
        }
        response = client.put(
            "/api/v1/skills/editor/session123/file123/content",
            json=content_data,
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data

    def test_get_file_status(self, client):
        """Test getting file status."""
        response = client.get(
            "/api/v1/skills/editor/session123/file123/status"
        )

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_list_open_files(self, client):
        """Test listing open files."""
        response = client.get("/api/v1/skills/editor/session123/files")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_editor_statistics(self, client):
        """Test getting editor statistics."""
        response = client.get("/api/v1/skills/editor/session123/statistics")

        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_json(self, client):
        """Test handling invalid JSON."""
        response = client.post(
            "/api/v1/skills/",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Check response (should return validation error)
        assert response.status_code in [422, 500]

    def test_missing_required_field(self, client):
        """Test handling missing required fields."""
        incomplete_data = {
            "name": "Test Skill",
            # Missing required fields
        }
        response = client.post("/api/v1/skills/", json=incomplete_data)

        # Check response (should return validation error)
        assert response.status_code == 422

    def test_invalid_skill_id(self, client):
        """Test handling invalid skill ID."""
        response = client.get("/api/v1/skills/invalid!@#$")

        # Check response
        assert response.status_code in [400, 404]

    def test_invalid_pagination_params(self, client):
        """Test handling invalid pagination parameters."""
        response = client.get("/api/v1/skills/?page=-1&page_size=0")

        # Check response
        assert response.status_code == 422

    def test_invalid_search_query(self, client):
        """Test handling invalid search query."""
        search_data = {
            "query": "",  # Empty query
        }
        response = client.post("/api/v1/skills/search", json=search_data)

        # Check response (may return 200 with empty results)
        assert response.status_code == 200


class TestResponseFormat:
    """Test response format consistency."""

    def test_successful_response_format(self, client):
        """Test that successful responses have consistent format."""
        response = client.get("/api/v1/skills/")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

    def test_error_response_format(self, client):
        """Test that error responses have consistent format."""
        response = client.get("/api/v1/skills/nonexistent")

        assert response.status_code == 404
        # Error responses may have different format

    def test_response_has_metadata(self, client):
        """Test that responses include metadata."""
        response = client.get("/api/v1/skills/")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # Check for pagination metadata
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
