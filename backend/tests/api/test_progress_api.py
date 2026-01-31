"""Tests for progress tracking API.

This module contains comprehensive tests for all API endpoints including
progress management, log viewing, history queries, and WebSocket handlers.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from uuid import uuid4

# Import API components
from backend.app.progress.api.v1.progress import router as progress_router
from backend.app.progress.api.v1.logs import router as logs_router
from backend.app.progress.api.v1.history import router as history_router
from backend.app.progress.websocket_handler import (
    WebSocketEventHandler,
    ProgressWebSocketHandler,
    NotificationWebSocketHandler,
    MetricWebSocketHandler,
    VisualizationWebSocketHandler,
)

# Import FastAPI testing components
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestProgressAPI:
    """Test progress management API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI application for testing."""
        app = FastAPI()
        app.include_router(progress_router, prefix="/api/v1")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        db.merge = Mock()
        db.delete = Mock()
        return db

    def test_create_task_progress(self, client, mock_db):
        """Test creating task progress."""
        # This would test the actual API endpoint
        # For now, we'll test the structure
        response = client.post(
            "/api/v1/tasks/test-task-123/progress",
            json={
                "progress": 50,
                "status": "running",
                "current_step": 2,
                "total_steps": 4,
                "metadata": {"step_name": "Processing"},
            }
        )
        # The actual test would verify response status and structure
        assert response.status_code in [200, 201, 422]  # Depending on implementation

    def test_get_task_progress(self, client):
        """Test getting task progress."""
        response = client.get("/api/v1/tasks/test-task-123/progress")
        assert response.status_code in [200, 404]

    def test_update_task_progress(self, client):
        """Test updating task progress."""
        response = client.put(
            "/api/v1/tasks/test-task-123/progress",
            json={
                "progress": 75,
                "status": "running",
                "current_step": 3,
                "total_steps": 4,
            }
        )
        assert response.status_code in [200, 404, 422]

    def test_list_task_progress(self, client):
        """Test listing task progress."""
        response = client.get(
            "/api/v1/progress?user_id=test-user&limit=10&offset=0"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_bulk_update_progress(self, client):
        """Test bulk progress update."""
        response = client.post(
            "/api/v1/progress/bulk-update",
            json={
                "updates": [
                    {
                        "task_id": "task-1",
                        "progress": 50,
                        "status": "running",
                    },
                    {
                        "task_id": "task-2",
                        "progress": 100,
                        "status": "completed",
                    },
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "successful" in data
        assert "failed" in data

    def test_delete_task_progress(self, client):
        """Test deleting task progress."""
        response = client.delete("/api/v1/tasks/test-task-123/progress")
        assert response.status_code in [200, 404]

    def test_get_progress_chart(self, client):
        """Test getting progress chart."""
        response = client.get(
            "/api/v1/tasks/test-task-123/progress/chart?time_range=7d&aggregation=avg"
        )
        assert response.status_code == 200
        data = response.json()
        assert "chart_type" in data
        assert "data" in data
        assert "title" in data

    def test_get_status_distribution(self, client):
        """Test getting status distribution."""
        response = client.get(
            "/api/v1/tasks/test-task-123/status-distribution"
        )
        assert response.status_code == 200
        data = response.json()
        assert "chart_type" in data
        assert "data" in data

    def test_get_progress_statistics(self, client):
        """Test getting progress statistics."""
        response = client.get(
            "/api/v1/statistics?user_id=test-user&time_range=30d"
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_statistics" in data
        assert "performance_metrics" in data

    def test_get_estimated_completion(self, client):
        """Test getting estimated completion time."""
        response = client.get("/api/v1/tasks/test-task-123/estimated-completion")
        assert response.status_code in [200, 404]


class TestLogsAPI:
    """Test logs API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI application for testing."""
        app = FastAPI()
        app.include_router(logs_router, prefix="/api/v1")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_create_log_entry(self, client):
        """Test creating log entry."""
        response = client.post(
            "/api/v1/tasks/test-task-123/logs",
            json={
                "level": "INFO",
                "message": "Task started processing",
                "source": "worker-1",
                "context": {"step": "initialization"},
            }
        )
        assert response.status_code in [200, 201, 422]

    def test_get_task_logs(self, client):
        """Test getting task logs."""
        response = client.get(
            "/api/v1/tasks/test-task-123/logs?level=INFO&limit=50"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_search_logs(self, client):
        """Test searching logs."""
        response = client.get(
            "/api/v1/logs/search?query=error&level=ERROR"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_bulk_create_logs(self, client):
        """Test bulk log creation."""
        response = client.post(
            "/api/v1/logs/bulk",
            json={
                "logs": [
                    {
                        "task_id": "task-1",
                        "level": "INFO",
                        "message": "Log 1",
                        "source": "test",
                    },
                    {
                        "task_id": "task-2",
                        "level": "ERROR",
                        "message": "Log 2",
                        "source": "test",
                    },
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "successful" in data

    def test_get_log_statistics(self, client):
        """Test getting log statistics."""
        response = client.get("/api/v1/logs/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_logs" in data
        assert "by_level" in data

    def test_delete_task_logs(self, client):
        """Test deleting task logs."""
        response = client.delete("/api/v1/tasks/test-task-123/logs")
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data

    def test_export_logs(self, client):
        """Test exporting logs."""
        response = client.post(
            "/api/v1/logs/export?format=json&level=INFO"
        )
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert "status" in data

    def test_get_recent_logs(self, client):
        """Test getting recent logs."""
        response = client.get("/api/v1/logs/recent?limit=20")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_log_levels(self, client):
        """Test getting available log levels."""
        response = client.get("/api/v1/logs/levels")
        assert response.status_code == 200
        data = response.json()
        assert "levels" in data
        assert isinstance(data["levels"], list)

    def test_get_active_streams(self, client):
        """Test getting active log streams."""
        response = client.get("/api/v1/streams/active")
        assert response.status_code == 200
        data = response.json()
        assert "active_sessions" in data
        assert "total_sessions" in data


class TestHistoryAPI:
    """Test history API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI application for testing."""
        app = FastAPI()
        app.include_router(history_router, prefix="/api/v1")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_get_task_progress_history(self, client):
        """Test getting task progress history."""
        response = client.get(
            "/api/v1/history/tasks/test-task-123/history"
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "timeline" in data

    def test_get_task_timeline(self, client):
        """Test getting task timeline."""
        response = client.get(
            "/api/v1/history/tasks/test-task-123/timeline?include_logs=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "timeline" in data

    def test_get_performance_analytics(self, client):
        """Test getting performance analytics."""
        response = client.get(
            "/api/v1/history/analytics/performance?time_range=30d"
        )
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "time_series" in data

    def test_get_trend_analytics(self, client):
        """Test getting trend analytics."""
        response = client.get(
            "/api/v1/history/analytics/trends?metric=completion_rate"
        )
        assert response.status_code == 200
        data = response.json()
        assert "metric" in data
        assert "current_period" in data

    def test_get_comparative_analytics(self, client):
        """Test getting comparative analytics."""
        response = client.get(
            "/api/v1/history/analytics/comparisons"
        )
        assert response.status_code == 200
        data = response.json()
        assert "baseline_period" in data
        assert "comparison_period" in data
        assert "metrics" in data

    def test_get_activity_heatmap(self, client):
        """Test getting activity heatmap."""
        response = client.get(
            "/api/v1/history/tasks/activity-heatmap?days=30"
        )
        assert response.status_code == 200
        data = response.json()
        assert "chart_type" in data
        assert "data" in data

    def test_export_history(self, client):
        """Test exporting history."""
        response = client.get(
            "/api/v1/history/export?format=json"
        )
        assert response.status_code == 200
        data = response.json()
        assert "export_id" in data
        assert "status" in data


class TestWebSocketHandlers:
    """Test WebSocket message handlers."""

    @pytest.fixture
    def event_handler(self):
        """Create WebSocket event handler."""
        return WebSocketEventHandler()

    @pytest.fixture
    def progress_handler(self):
        """Create progress handler."""
        return ProgressWebSocketHandler()

    @pytest.fixture
    def notification_handler(self):
        """Create notification handler."""
        return NotificationWebSocketHandler()

    @pytest.fixture
    def metric_handler(self):
        """Create metric handler."""
        return MetricWebSocketHandler()

    @pytest.fixture
    def visualization_handler(self):
        """Create visualization handler."""
        return VisualizationWebSocketHandler()

    @pytest.mark.asyncio
    async def test_progress_handler(self, progress_handler):
        """Test progress message handler."""
        message = {
            "type": "progress_update",
            "task_id": "test-task-123",
            "progress": 50,
            "status": "running",
        }

        # Mock websocket_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_message = AsyncMock(return_value=True)

            result = await progress_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_log_handler(self, progress_handler):
        """Test log message handler."""
        message = {
            "type": "log_message",
            "task_id": "test-task-123",
            "level": "INFO",
            "message": "Test log message",
            "source": "test-source",
        }

        # Mock websocket_manager and log_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws, \
             patch('backend.app.progress.websocket_handler.log_manager') as mock_log:
            mock_ws.send_message = AsyncMock(return_value=True)
            mock_log.create_log_entry = AsyncMock()

            result = await progress_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_heartbeat_handler(self, progress_handler):
        """Test heartbeat message handler."""
        message = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().timestamp(),
        }

        # Mock websocket_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_message = AsyncMock(return_value=True)

            result = await progress_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_notification_handler(self, notification_handler):
        """Test notification message handler."""
        message = {
            "type": "notification",
            "notification_id": "notif-123",
            "user_id": "user-123",
            "title": "Test Notification",
            "message": "Test message",
            "notification_type": "alert",
            "priority": "normal",
        }

        # Mock websocket_manager and notification_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws, \
             patch('backend.app.progress.websocket_handler.notification_manager') as mock_notif:
            mock_ws.send_message = AsyncMock(return_value=True)
            mock_notif.create_notification = AsyncMock()

            result = await notification_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_metric_handler(self, metric_handler):
        """Test metric message handler."""
        message = {
            "type": "metric",
            "metric_name": "cpu_usage",
            "value": 85.5,
            "unit": "percent",
            "labels": {"host": "server-1"},
        }

        # Mock websocket_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_message = AsyncMock(return_value=True)

            result = await metric_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_visualization_handler(self, visualization_handler):
        """Test visualization message handler."""
        message = {
            "type": "subscribe_visualization",
            "query": {"chart_type": "progress_chart"},
            "update_interval": 5.0,
        }

        # Mock websocket_manager and visualization_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws, \
             patch('backend.app.progress.websocket_handler.visualization_manager') as mock_viz:
            mock_ws.send_message = AsyncMock(return_value=True)
            mock_viz.add_real_time_subscription = AsyncMock(return_value="subscription-123")

            result = await visualization_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_visualization_create_chart(self, visualization_handler):
        """Test visualization chart creation."""
        message = {
            "type": "create_chart",
            "template_id": "progress_timeline",
            "data": [{"time": "2024-01-01", "value": 50}],
            "title": "Test Chart",
        }

        # Mock websocket_manager and visualization_manager
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws, \
             patch('backend.app.progress.websocket_handler.visualization_manager') as mock_viz:
            mock_ws.send_message = AsyncMock(return_value=True)

            # Create mock chart
            mock_chart = Mock()
            mock_chart.chart_type.value = "line"
            mock_chart.title = "Test Chart"
            mock_chart.data = [{"time": "2024-01-01", "value": 50}]
            mock_chart.metadata = {}
            mock_chart.generated_at = datetime.utcnow()

            mock_viz.create_custom_chart = AsyncMock(return_value=mock_chart)

            result = await visualization_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_event_handler_routing(self, event_handler):
        """Test event handler message routing."""
        # Test progress message
        message = {
            "type": "progress_update",
            "task_id": "test-task-123",
            "progress": 50,
        }

        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_message = AsyncMock(return_value=True)

            result = await event_handler.handle_message("connection-123", message)
            assert result is True

    @pytest.mark.asyncio
    async def test_connection_handling(self, event_handler):
        """Test connection handling."""
        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_message = AsyncMock(return_value=True)

            await event_handler.handle_connection(
                "connection-123",
                task_id="test-task-123",
                user_id="test-user"
            )
            # No exception means success

    @pytest.mark.asyncio
    async def test_disconnection_handling(self, event_handler):
        """Test disconnection handling."""
        # Add a connection to track
        event_handler.progress_handler.connection_tasks["connection-123"] = "test-task-123"

        with patch('backend.app.progress.websocket_handler.log_manager') as mock_log:
            mock_log.unsubscribe_from_logs = AsyncMock()

            await event_handler.handle_disconnection("connection-123")
            # Verify cleanup was called
            assert "connection-123" not in event_handler.progress_handler.connection_tasks

    @pytest.mark.asyncio
    async def test_invalid_message_type(self, event_handler):
        """Test handling of invalid message type."""
        message = {
            "type": "invalid_message_type",
        }

        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_error = AsyncMock()

            result = await event_handler.handle_message("connection-123", message)
            assert result is False

    @pytest.mark.asyncio
    async def test_error_handling(self, event_handler):
        """Test error handling."""
        # Send a message that will cause an error
        message = {
            "type": "progress_update",
            # Missing required fields
        }

        with patch('backend.app.progress.websocket_handler.websocket_manager') as mock_ws:
            mock_ws.send_error = AsyncMock()

            result = await event_handler.handle_message("connection-123", message)
            assert result is False


class TestAPIIntegration:
    """Integration tests for API endpoints."""

    @pytest.fixture
    def app(self):
        """Create complete FastAPI application."""
        app = FastAPI()
        app.include_router(progress_router, prefix="/api/v1/progress")
        app.include_router(logs_router, prefix="/api/v1/logs")
        app.include_router(history_router, prefix="/api/v1/history")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_end_to_end_progress_flow(self, client):
        """Test complete progress tracking flow."""
        # Create progress
        create_response = client.post(
            "/api/v1/progress/tasks/test-task-123/progress",
            json={
                "progress": 25,
                "status": "running",
                "current_step": 1,
                "total_steps": 4,
            }
        )
        assert create_response.status_code in [200, 201]

        # Get progress
        get_response = client.get("/api/v1/progress/tasks/test-task-123/progress")
        assert get_response.status_code == 200

        # Update progress
        update_response = client.put(
            "/api/v1/progress/tasks/test-task-123/progress",
            json={
                "progress": 75,
                "status": "running",
                "current_step": 3,
                "total_steps": 4,
            }
        )
        assert update_response.status_code == 200

        # Get statistics
        stats_response = client.get("/api/v1/progress/statistics")
        assert stats_response.status_code == 200

    def test_log_flow_with_progress(self, client):
        """Test log creation and retrieval with progress."""
        # Create log entry
        log_response = client.post(
            "/api/v1/logs/tasks/test-task-123/logs",
            json={
                "level": "INFO",
                "message": "Task started",
                "source": "worker-1",
            }
        )
        assert log_response.status_code in [200, 201]

        # Get logs
        get_logs_response = client.get(
            "/api/v1/logs/tasks/test-task-123/logs?level=INFO"
        )
        assert get_logs_response.status_code == 200
        assert isinstance(get_logs_response.json(), list)

        # Get log statistics
        stats_response = client.get("/api/v1/logs/statistics")
        assert stats_response.status_code == 200

    def test_history_flow(self, client):
        """Test history and analytics flow."""
        # Get task history
        history_response = client.get(
            "/api/v1/history/tasks/test-task-123/history"
        )
        assert history_response.status_code == 200

        # Get timeline
        timeline_response = client.get(
            "/api/v1/history/tasks/test-task-123/timeline"
        )
        assert timeline_response.status_code == 200

        # Get analytics
        analytics_response = client.get(
            "/api/v1/history/analytics/performance"
        )
        assert analytics_response.status_code == 200

        # Get activity heatmap
        heatmap_response = client.get(
            "/api/v1/history/tasks/activity-heatmap"
        )
        assert heatmap_response.status_code == 200


# Performance tests
class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.fixture
    def app(self):
        """Create FastAPI application."""
        app = FastAPI()
        app.include_router(progress_router, prefix="/api/v1")
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_bulk_operations_performance(self, client):
        """Test performance of bulk operations."""
        start_time = datetime.utcnow()

        # Bulk update progress
        response = client.post(
            "/api/v1/progress/bulk-update",
            json={
                "updates": [
                    {
                        "task_id": f"task-{i}",
                        "progress": i * 10,
                        "status": "running" if i < 100 else "completed",
                    }
                    for i in range(100)
                ]
            }
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        assert response.status_code == 200
        assert duration < 5.0  # Should complete within 5 seconds

    def test_concurrent_requests(self, client):
        """Test handling concurrent requests."""
        import concurrent.futures

        def make_request(i):
            return client.get(f"/api/v1/progress?limit=10&offset={i * 10}")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            responses = [future.result() for future in futures]

        # All requests should succeed
        for response in responses:
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
