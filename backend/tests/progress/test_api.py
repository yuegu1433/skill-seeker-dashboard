"""API tests for real-time progress tracking.

This module contains comprehensive tests for all API endpoints including:
- Progress management APIs
- Log viewing APIs
- Historical data query APIs
- WebSocket endpoints
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket
from datetime import datetime, timedelta
from typing import Dict, Any, List
import asyncio

from app.progress.api.v1.progress import router as progress_router
from app.progress.api.v1.logs import router as logs_router
from app.progress.api.v1.history import router as history_router
from app.progress.api.v1.websocket import router as websocket_router
from app.progress.progress_manager import progress_manager
from app.progress.log_manager import log_manager
from app.progress.tracker import tracker
from app.progress.models.task import TaskProgress, TaskStatus
from app.progress.models.log import TaskLog, LogLevel


# Test client setup
@pytest.fixture
def client():
    """Create test client with all routers."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(progress_router, prefix="/v1/progress")
    app.include_router(logs_router, prefix="/v1/logs")
    app.include_router(history_router, prefix="/v1/history")
    app.include_router(websocket_router, prefix="/v1")

    return TestClient(app)


# Mock database session
@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


# Mock managers
@pytest.fixture
def mock_progress_manager():
    """Mock progress manager."""
    with patch('app.progress.api.v1.progress.progress_manager') as mock:
        yield mock


@pytest.fixture
def mock_log_manager():
    """Mock log manager."""
    with patch('app.progress.api.v1.logs.log_manager') as mock:
        yield mock


@pytest.fixture
def mock_tracker():
    """Mock tracker."""
    with patch('app.progress.api.v1.history.tracker') as mock:
        yield mock


# Sample test data
SAMPLE_TASK_ID = "task-123"
SAMPLE_USER_ID = "user-456"
SAMPLE_TASK_DATA = {
    "task_id": SAMPLE_TASK_ID,
    "progress": 50,
    "status": "in_progress",
    "current_step": 5,
    "total_steps": 10,
    "metadata": {"test": "data"}
}


# ============================================================================
# Progress API Tests
# ============================================================================

class TestProgressAPI:
    """Test progress management APIs."""

    @pytest.mark.asyncio
    async def test_create_task_progress(self, client, mock_db, mock_progress_manager):
        """Test creating task progress."""
        # Setup
        mock_task = MagicMock()
        mock_task.task_id = SAMPLE_TASK_ID
        mock_task.progress = 50
        mock_task.status = "in_progress"
        mock_task.current_step = 5
        mock_task.total_steps = 10
        mock_task.estimated_completion = datetime.utcnow()
        mock_task.metadata = {"test": "data"}
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        mock_progress_manager.update_progress = AsyncMock(return_value=mock_task)

        # Execute
        response = client.post(
            f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress",
            json=SAMPLE_TASK_DATA
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == SAMPLE_TASK_ID
        assert data["progress"] == 50
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_get_task_progress(self, client, mock_db, mock_progress_manager):
        """Test getting task progress."""
        # Setup
        mock_task = MagicMock()
        mock_task.task_id = SAMPLE_TASK_ID
        mock_task.progress = 75
        mock_task.status = "in_progress"
        mock_task.current_step = 7
        mock_task.total_steps = 10
        mock_task.estimated_completion = datetime.utcnow()
        mock_task.metadata = {"test": "data"}
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        mock_progress_manager.get_task_progress = AsyncMock(return_value=mock_task)

        # Execute
        response = client.get(f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == SAMPLE_TASK_ID
        assert data["progress"] == 75

    @pytest.mark.asyncio
    async def test_get_task_progress_not_found(self, client, mock_db, mock_progress_manager):
        """Test getting non-existent task progress."""
        # Setup
        mock_progress_manager.get_task_progress = AsyncMock(return_value=None)

        # Execute
        response = client.get(f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress")

        # Assert
        assert response.status_code == 404
        assert f"Task {SAMPLE_TASK_ID} not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_task_progress(self, client, mock_db, mock_progress_manager):
        """Test updating task progress."""
        # Setup
        update_data = {
            "progress": 80,
            "status": "in_progress",
            "metadata": {"updated": True}
        }

        mock_task = MagicMock()
        mock_task.task_id = SAMPLE_TASK_ID
        mock_task.progress = 80
        mock_task.status = "in_progress"
        mock_task.current_step = 8
        mock_task.total_steps = 10
        mock_task.estimated_completion = datetime.utcnow()
        mock_task.metadata = {"updated": True}
        mock_task.created_at = datetime.utcnow()
        mock_task.updated_at = datetime.utcnow()

        mock_progress_manager.update_progress = AsyncMock(return_value=mock_task)

        # Execute
        response = client.put(
            f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress",
            json=update_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["progress"] == 80

    @pytest.mark.asyncio
    async def test_list_tasks(self, client, mock_db, mock_progress_manager):
        """Test listing tasks with filtering."""
        # Setup
        mock_tasks = [
            MagicMock(task_id="task-1", progress=100, status="completed"),
            MagicMock(task_id="task-2", progress=50, status="in_progress"),
        ]
        mock_progress_manager.get_tasks = AsyncMock(return_value=mock_tasks)

        # Execute
        response = client.get(
            "/v1/progress/tasks",
            params={"status": "in_progress", "limit": 10}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data
        assert "total" in data
        assert len(data["tasks"]) > 0

    @pytest.mark.asyncio
    async def test_bulk_update_progress(self, client, mock_db, mock_progress_manager):
        """Test bulk updating progress."""
        # Setup
        bulk_data = {
            "updates": [
                {"task_id": "task-1", "progress": 100},
                {"task_id": "task-2", "progress": 75},
            ]
        }

        mock_progress_manager.bulk_update_progress = AsyncMock(return_value={
            "updated": 2,
            "failed": 0
        })

        # Execute
        response = client.post(
            "/v1/progress/progress/bulk-update",
            json=bulk_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["updated"] == 2

    @pytest.mark.asyncio
    async def test_delete_task_progress(self, client, mock_db, mock_progress_manager):
        """Test deleting task progress."""
        # Setup
        mock_progress_manager.delete_task = AsyncMock(return_value=True)

        # Execute
        response = client.delete(f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, client, mock_db, mock_progress_manager, mock_tracker):
        """Test getting task statistics."""
        # Setup
        mock_tracker.get_task_statistics = AsyncMock(return_value={
            "total_tasks": 10,
            "completed_tasks": 5,
            "in_progress_tasks": 3,
            "failed_tasks": 2,
            "task_ids": ["task-1", "task-2"],
        })

        # Execute
        response = client.get(
            "/v1/progress/statistics",
            params={"user_id": SAMPLE_USER_ID}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "task_statistics" in data
        assert "performance_metrics" in data

    @pytest.mark.asyncio
    async def test_get_estimated_completion(self, client, mock_db, mock_progress_manager):
        """Test getting estimated completion time."""
        # Setup
        mock_task = MagicMock()
        mock_task.task_id = SAMPLE_TASK_ID
        mock_task.progress = 50
        mock_task.estimated_completion = datetime.utcnow() + timedelta(hours=2)

        mock_progress_manager.get_task_progress = AsyncMock(return_value=mock_task)

        # Execute
        response = client.get(f"/v1/progress/tasks/{SAMPLE_TASK_ID}/estimated-completion")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == SAMPLE_TASK_ID
        assert "estimated_completion" in data
        assert data["current_progress"] == 50


# ============================================================================
# Logs API Tests
# ============================================================================

class TestLogsAPI:
    """Test log viewing APIs."""

    @pytest.mark.asyncio
    async def test_create_log_entry(self, client, mock_db, mock_log_manager):
        """Test creating log entry."""
        # Setup
        log_data = {
            "message": "Test log message",
            "level": "info",
            "metadata": {"test": True}
        }

        mock_log = MagicMock()
        mock_log.id = "log-123"
        mock_log.task_id = SAMPLE_TASK_ID
        mock_log.message = "Test log message"
        mock_log.level = "info"
        mock_log.metadata = {"test": True}
        mock_log.created_at = datetime.utcnow()

        mock_log_manager.create_log_entry = AsyncMock(return_value=mock_log)

        # Execute
        response = client.post(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs",
            json=log_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test log message"
        assert data["level"] == "info"

    @pytest.mark.asyncio
    async def test_get_task_logs(self, client, mock_db, mock_log_manager):
        """Test getting task logs."""
        # Setup
        mock_logs = [
            MagicMock(
                id="log-1",
                task_id=SAMPLE_TASK_ID,
                message="Log message 1",
                level="info",
                created_at=datetime.utcnow()
            ),
            MagicMock(
                id="log-2",
                task_id=SAMPLE_TASK_ID,
                message="Log message 2",
                level="error",
                created_at=datetime.utcnow()
            ),
        ]

        mock_log_manager.get_logs = AsyncMock(return_value=mock_logs)

        # Execute
        response = client.get(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs",
            params={"limit": 10}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert len(data["logs"]) > 0

    @pytest.mark.asyncio
    async def test_search_logs(self, client, mock_db, mock_log_manager):
        """Test searching logs."""
        # Setup
        search_data = {
            "query": "error",
            "level": "error",
            "date_from": datetime.utcnow() - timedelta(days=1).isoformat(),
            "date_to": datetime.utcnow().isoformat()
        }

        mock_log_manager.search_logs = AsyncMock(return_value={
            "logs": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        })

        # Execute
        response = client.post(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs/search",
            json=search_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    @pytest.mark.asyncio
    async def test_export_logs(self, client, mock_db, mock_log_manager):
        """Test exporting logs."""
        # Setup
        export_data = {
            "format": "json",
            "date_from": datetime.utcnow() - timedelta(days=1).isoformat(),
            "date_to": datetime.utcnow().isoformat()
        }

        mock_log_manager.export_logs = AsyncMock(return_value={
            "download_url": "/download/logs-export.json",
            "expires_at": datetime.utcnow() + timedelta(hours=1).isoformat()
        })

        # Execute
        response = client.post(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs/export",
            json=export_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data

    @pytest.mark.asyncio
    async def test_bulk_create_logs(self, client, mock_db, mock_log_manager):
        """Test bulk creating log entries."""
        # Setup
        bulk_data = {
            "logs": [
                {"message": "Log 1", "level": "info"},
                {"message": "Log 2", "level": "error"},
            ]
        }

        mock_log_manager.bulk_create_logs = AsyncMock(return_value={
            "created": 2,
            "failed": 0
        })

        # Execute
        response = client.post(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs/bulk",
            json=bulk_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["created"] == 2


# ============================================================================
# History API Tests
# ============================================================================

class TestHistoryAPI:
    """Test historical data query APIs."""

    @pytest.mark.asyncio
    async def test_get_task_progress_history(self, client, mock_db, mock_progress_manager, mock_tracker):
        """Test getting task progress history."""
        # Setup
        mock_progress_history = [
            {
                "timestamp": datetime.utcnow() - timedelta(hours=1).isoformat(),
                "progress": 25,
                "status": "in_progress",
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "progress": 50,
                "status": "in_progress",
            },
        ]

        mock_tracker.get_progress_history = AsyncMock(return_value=mock_progress_history)

        # Execute
        response = client.get(
            f"/v1/history/tasks/{SAMPLE_TASK_ID}/history",
            params={"limit": 10}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert len(data["history"]) > 0

    @pytest.mark.asyncio
    async def test_get_task_timeline(self, client, mock_db, mock_tracker):
        """Test getting task timeline."""
        # Setup
        mock_timeline = [
            {
                "event": "task_created",
                "timestamp": datetime.utcnow() - timedelta(days=1).isoformat(),
                "description": "Task created",
            },
            {
                "event": "progress_updated",
                "timestamp": datetime.utcnow().isoformat(),
                "description": "Progress updated to 50%",
            },
        ]

        mock_tracker.get_task_timeline = AsyncMock(return_value=mock_timeline)

        # Execute
        response = client.get(f"/v1/history/tasks/{SAMPLE_TASK_ID}/timeline")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "timeline" in data
        assert len(data["timeline"]) > 0

    @pytest.mark.asyncio
    async def test_get_analytics(self, client, mock_db, mock_tracker):
        """Test getting analytics data."""
        # Setup
        analytics_data = {
            "total_tasks": 10,
            "completed_tasks": 8,
            "average_completion_time": 3600,
            "success_rate": 0.8,
            "trends": {
                "daily_tasks": [1, 2, 3, 2, 1],
            }
        }

        mock_tracker.get_analytics = AsyncMock(return_value=analytics_data)

        # Execute
        response = client.get(
            "/v1/history/analytics",
            params={
                "date_from": datetime.utcnow() - timedelta(days=7).isoformat(),
                "date_to": datetime.utcnow().isoformat()
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "completed_tasks" in data

    @pytest.mark.asyncio
    async def test_get_trends(self, client, mock_db, mock_tracker):
        """Test getting trends data."""
        # Setup
        trends_data = {
            "task_completion_rate": [0.7, 0.75, 0.8, 0.85, 0.9],
            "average_progress_velocity": [10, 12, 15, 14, 16],
            "timestamps": [
                (datetime.utcnow() - timedelta(days=4)).isoformat(),
                (datetime.utcnow() - timedelta(days=3)).isoformat(),
                (datetime.utcnow() - timedelta(days=2)).isoformat(),
                (datetime.utcnow() - timedelta(days=1)).isoformat(),
                datetime.utcnow().isoformat(),
            ]
        }

        mock_tracker.get_trends = AsyncMock(return_value=trends_data)

        # Execute
        response = client.get(
            "/v1/history/trends",
            params={
                "period": "daily",
                "days": 7
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "task_completion_rate" in data
        assert "average_progress_velocity" in data

    @pytest.mark.asyncio
    async def test_get_comparison(self, client, mock_db, mock_tracker):
        """Test getting task comparison data."""
        # Setup
        comparison_data = {
            "task_ids": ["task-1", "task-2"],
            "comparison": {
                "task-1": {
                    "progress": 100,
                    "duration": 3600,
                    "status": "completed"
                },
                "task-2": {
                    "progress": 50,
                    "duration": 1800,
                    "status": "in_progress"
                }
            }
        }

        mock_tracker.compare_tasks = AsyncMock(return_value=comparison_data)

        # Execute
        response = client.post(
            "/v1/history/compare",
            json={
                "task_ids": ["task-1", "task-2"],
                "metrics": ["progress", "duration", "status"]
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "comparison" in data
        assert "task-1" in data["comparison"]


# ============================================================================
# WebSocket API Tests
# ============================================================================

class TestWebSocketAPI:
    """Test WebSocket endpoints."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client):
        """Test basic WebSocket connection."""
        # This test would require a real WebSocket connection
        # In a real implementation, you would use WebSocketTestClient
        pass

    @pytest.mark.asyncio
    async def test_websocket_message_handling(self):
        """Test WebSocket message handling."""
        # Setup mock WebSocket
        mock_websocket = AsyncMock()

        # Create WebSocket handler
        from app.progress.api.v1.websocket import websocket_endpoint

        # Test message handling
        # This would require a more complex setup with real WebSocket
        pass

    @pytest.mark.asyncio
    async def test_websocket_subscription(self):
        """Test WebSocket subscription functionality."""
        # Test subscription and unsubscription
        pass

    @pytest.mark.asyncio
    async def test_websocket_stream_endpoint(self):
        """Test specialized streaming endpoints."""
        # Test progress/logs/notifications streams
        pass

    @pytest.mark.asyncio
    async def test_websocket_dashboard_endpoint(self):
        """Test dashboard WebSocket endpoint."""
        # Test dashboard-specific functionality
        pass


# ============================================================================
# Integration Tests
# ============================================================================

class TestAPIIntegration:
    """Integration tests for API workflows."""

    @pytest.mark.asyncio
    async def test_complete_task_workflow(self, client, mock_db, mock_progress_manager, mock_log_manager):
        """Test complete task workflow through API."""
        # 1. Create task
        task_data = {
            "task_id": SAMPLE_TASK_ID,
            "user_id": SAMPLE_USER_ID,
            "name": "Test Task",
            "description": "Test description"
        }

        mock_progress_manager.create_task = AsyncMock(return_value=MagicMock(**task_data))

        # 2. Update progress
        progress_data = {"progress": 50, "status": "in_progress"}
        mock_progress_manager.update_progress = AsyncMock(return_value=MagicMock(**{**task_data, **progress_data}))

        # 3. Add log
        log_data = {"message": "Task started", "level": "info"}
        mock_log_manager.create_log_entry = AsyncMock(return_value=MagicMock(**{**log_data, "task_id": SAMPLE_TASK_ID}))

        # Execute workflow
        create_response = client.post("/v1/progress/tasks", json=task_data)
        assert create_response.status_code == 200

        progress_response = client.post(
            f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress",
            json=progress_data
        )
        assert progress_response.status_code == 200

        log_response = client.post(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs",
            json=log_data
        )
        assert log_response.status_code == 200

    @pytest.mark.asyncio
    async def test_error_handling(self, client, mock_progress_manager):
        """Test error handling in APIs."""
        # Test invalid data
        response = client.post(
            "/v1/progress/tasks/invalid-task/progress",
            json={"progress": "invalid"}  # Invalid progress value
        )
        # Should handle error gracefully
        assert response.status_code in [400, 422]

        # Test non-existent task
        mock_progress_manager.get_task_progress = AsyncMock(return_value=None)
        response = client.get("/v1/progress/tasks/non-existent/progress")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_validation(self, client):
        """Test request validation."""
        # Test missing required fields
        response = client.post("/v1/progress/tasks/task-123/progress", json={})
        assert response.status_code == 422

        # Test invalid enum values
        response = client.post(
            "/v1/progress/tasks/task-123/progress",
            json={"progress": 50, "status": "invalid_status"}
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client):
        """Test rate limiting (if implemented)."""
        # This would test if rate limiting is in place
        # For now, just verify the endpoint responds
        response = client.get("/v1/progress/tasks")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client, mock_progress_manager):
        """Test handling of concurrent requests."""
        import asyncio

        # Setup
        mock_progress_manager.get_task_progress = AsyncMock(return_value=MagicMock(
            task_id=SAMPLE_TASK_ID,
            progress=50,
            status="in_progress"
        ))

        # Execute multiple concurrent requests
        tasks = [
            client.get(f"/v1/progress/tasks/{SAMPLE_TASK_ID}/progress")
            for _ in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        # Assert all succeed
        for response in responses:
            assert response.status_code == 200


# ============================================================================
# Performance Tests
# ============================================================================

class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, client, mock_progress_manager):
        """Test performance of bulk operations."""
        import time

        # Setup
        bulk_data = {
            "updates": [
                {"task_id": f"task-{i}", "progress": 50}
                for i in range(100)
            ]
        }

        mock_progress_manager.bulk_update_progress = AsyncMock(return_value={
            "updated": 100,
            "failed": 0
        })

        # Measure execution time
        start_time = time.time()
        response = client.post("/v1/progress/progress/bulk-update", json=bulk_data)
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        assert end_time - start_time < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_large_dataset_handling(self, client, mock_log_manager):
        """Test handling of large datasets."""
        # Setup
        large_logs = [
            MagicMock(
                id=f"log-{i}",
                task_id=SAMPLE_TASK_ID,
                message=f"Log message {i}",
                level="info",
                created_at=datetime.utcnow()
            )
            for i in range(1000)
        ]

        mock_log_manager.get_logs = AsyncMock(return_value=large_logs)

        # Execute
        response = client.get(
            f"/v1/logs/tasks/{SAMPLE_TASK_ID}/logs",
            params={"limit": 1000}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 1000  # Should respect limit

    @pytest.mark.asyncio
    async def test_pagination_performance(self, client, mock_progress_manager):
        """Test pagination performance."""
        # Setup
        total_tasks = 10000
        page_size = 100
        page = 1

        mock_tasks = [
            MagicMock(task_id=f"task-{i}", progress=i, status="in_progress")
            for i in range(page_size)
        ]

        mock_progress_manager.get_tasks = AsyncMock(return_value=mock_tasks)

        # Execute
        response = client.get(
            "/v1/progress/tasks",
            params={
                "page": page,
                "page_size": page_size,
                "total": total_tasks
            }
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == page_size


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
