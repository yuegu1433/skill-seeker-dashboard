"""WebSocket API tests for real-time progress tracking.

This module contains comprehensive tests for WebSocket endpoints including:
- Connection management
- Message routing
- Real-time updates
- Subscription handling
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch, call
from fastapi import WebSocket
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any
import asyncio

from app.progress.api.v1.websocket import (
    router as websocket_router,
    websocket_endpoint,
    stream_endpoint,
    dashboard_endpoint,
)
from app.progress.websocket import websocket_manager
from app.progress.schemas.websocket_messages import MessageType


# Test client setup
@pytest.fixture
def websocket_client():
    """Create test client with WebSocket router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(websocket_router, prefix="/v1")

    return TestClient(app)


# Mock WebSocket connection
@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    websocket = AsyncMock(spec=WebSocket)
    websocket.query_params = {}
    websocket.receive_text = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.close = AsyncMock()
    return websocket


# Mock data
@pytest.fixture
def sample_connection_id():
    """Sample connection ID."""
    return "conn-123"


@pytest.fixture
def sample_task_id():
    """Sample task ID."""
    return "task-456"


@pytest.fixture
def sample_user_id():
    """Sample user ID."""
    return "user-789"


# ============================================================================
# WebSocket Connection Tests
# ============================================================================

class TestWebSocketConnection:
    """Test WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_websocket_basic_connection(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id,
        sample_user_id
    ):
        """Test basic WebSocket connection."""
        # Setup
        mock_websocket.query_params = {
            "task_id": sample_task_id,
            "user_id": sample_user_id
        }

        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/ws",
                task_id=sample_task_id,
                user_id=sample_user_id
            ) as websocket:
                # Assert connection was established
                mock_connect.assert_called_once()

                # Receive welcome message
                data = json.loads(websocket.receive_text())
                assert data["type"] == "connection"
                assert data["status"] == "connected"

    @pytest.mark.asyncio
    async def test_websocket_connection_rejection(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test WebSocket connection rejection."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = None  # Reject connection

            # Execute
            with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                # Connection should be closed
                pass

    @pytest.mark.asyncio
    async def test_websocket_connection_with_stream_type(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test WebSocket connection with stream type."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/ws",
                task_id=sample_task_id,
                stream_type="progress"
            ) as websocket:
                # Receive subscription message
                data = json.loads(websocket.receive_text())
                assert data["type"] == "subscription"
                assert data["stream_type"] == "progress"

    @pytest.mark.asyncio
    async def test_websocket_all_streams_subscription(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test WebSocket subscription to all streams."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/ws",
                task_id=sample_task_id,
                stream_type="all"
            ) as websocket:
                # Should receive multiple subscription messages
                subscriptions = []
                for _ in range(3):
                    data = json.loads(websocket.receive_text())
                    if data["type"] == "subscription":
                        subscriptions.append(data["stream_type"])

                assert "progress" in subscriptions
                assert "logs" in subscriptions
                assert "notifications" in subscriptions


# ============================================================================
# WebSocket Message Handling Tests
# ============================================================================

class TestWebSocketMessages:
    """Test WebSocket message handling."""

    @pytest.mark.asyncio
    async def test_ping_pong_message(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test ping/pong message handling."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                # Send ping
                websocket.send_text(json.dumps({"type": "ping"}))

                # Receive pong
                data = json.loads(websocket.receive_text())
                assert data["type"] == "pong"
                assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_subscribe_message(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id,
        sample_user_id
    ):
        """Test subscribe message handling."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            with patch.object(websocket_manager, 'subscribe', new_callable=AsyncMock) as mock_subscribe:
                # Execute
                with websocket_client.websocket_connect("/v1/ws") as websocket:
                    # Send subscribe message
                    websocket.send_text(json.dumps({
                        "type": "subscribe",
                        "task_id": sample_task_id,
                        "user_id": sample_user_id
                    }))

                    # Receive confirmation
                    data = json.loads(websocket.receive_text())
                    assert data["type"] == "subscribed"
                    assert data["task_id"] == sample_task_id
                    assert data["user_id"] == sample_user_id

                    # Verify subscribe was called
                    mock_subscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_unsubscribe_message(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id,
        sample_user_id
    ):
        """Test unsubscribe message handling."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            with patch.object(websocket_manager, 'unsubscribe', new_callable=AsyncMock) as mock_unsubscribe:
                # Execute
                with websocket_client.websocket_connect("/v1/ws") as websocket:
                    # Send unsubscribe message
                    websocket.send_text(json.dumps({
                        "type": "unsubscribe",
                        "task_id": sample_task_id,
                        "user_id": sample_user_id
                    }))

                    # Receive confirmation
                    data = json.loads(websocket.receive_text())
                    assert data["type"] == "unsubscribed"
                    assert data["task_id"] == sample_task_id
                    assert data["user_id"] == sample_user_id

                    # Verify unsubscribe was called
                    mock_unsubscribe.assert_called_once()

    @pytest.mark.asyncio
    async def test_progress_request_message(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test progress request message handling."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                # Send progress request
                websocket.send_text(json.dumps({
                    "type": "progress_request"
                }))

                # Receive progress data
                data = json.loads(websocket.receive_text())
                assert data["type"] == "progress_data"
                assert data["task_id"] == sample_task_id

    @pytest.mark.asyncio
    async def test_logs_request_message(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test logs request message handling."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                # Send logs request
                websocket.send_text(json.dumps({
                    "type": "logs_request"
                }))

                # Receive logs data
                data = json.loads(websocket.receive_text())
                assert data["type"] == "logs_data"
                assert data["task_id"] == sample_task_id

    @pytest.mark.asyncio
    async def test_notification_request_message(
        self,
        websocket_client,
        mock_websocket,
        sample_user_id
    ):
        """Test notification request message handling."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect("/v1/ws", user_id=sample_user_id) as websocket:
                # Send notification request
                websocket.send_text(json.dumps({
                    "type": "notification_request"
                }))

                # Receive notifications data
                data = json.loads(websocket.receive_text())
                assert data["type"] == "notifications_data"
                assert data["user_id"] == sample_user_id

    @pytest.mark.asyncio
    async def test_invalid_json_message(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test handling of invalid JSON messages."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            with patch.object(websocket_manager, 'send_error', new_callable=AsyncMock) as mock_send_error:
                # Execute
                with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                    # Send invalid JSON
                    websocket.send_text("invalid json")

                    # Receive error message
                    data = json.loads(websocket.receive_text())
                    assert data["type"] == "error"
                    assert "Invalid JSON" in data["error"]

                    # Verify error was sent
                    mock_send_error.assert_called_once()


# ============================================================================
# Stream Endpoint Tests
# ============================================================================

class TestStreamEndpoints:
    """Test specialized stream endpoints."""

    @pytest.mark.asyncio
    async def test_progress_stream_endpoint(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test progress stream endpoint."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/stream/progress",
                task_id=sample_task_id
            ) as websocket:
                # Receive stream status
                data = json.loads(websocket.receive_text())
                assert data["type"] == "stream_status"
                assert data["stream_type"] == "progress"

                # Send start stream
                websocket.send_text(json.dumps({
                    "type": "start_stream",
                    "task_id": sample_task_id
                }))

                # Receive confirmation
                data = json.loads(websocket.receive_text())
                assert data["type"] == "stream_started"
                assert data["task_id"] == sample_task_id

    @pytest.mark.asyncio
    async def test_logs_stream_endpoint(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test logs stream endpoint."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/stream/logs",
                task_id=sample_task_id
            ) as websocket:
                # Receive stream status
                data = json.loads(websocket.receive_text())
                assert data["stream_type"] == "logs"

    @pytest.mark.asyncio
    async def test_notifications_stream_endpoint(
        self,
        websocket_client,
        mock_websocket,
        sample_user_id
    ):
        """Test notifications stream endpoint."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/stream/notifications",
                user_id=sample_user_id
            ) as websocket:
                # Receive stream status
                data = json.loads(websocket.receive_text())
                assert data["stream_type"] == "notifications"


# ============================================================================
# Dashboard Endpoint Tests
# ============================================================================

class TestDashboardEndpoint:
    """Test dashboard-specific WebSocket endpoint."""

    @pytest.mark.asyncio
    async def test_dashboard_connection(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test dashboard WebSocket connection."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/dashboard",
                dashboard_id="dashboard-1"
            ) as websocket:
                # Receive welcome message
                data = json.loads(websocket.receive_text())
                assert data["type"] == "dashboard_status"
                assert data["dashboard_id"] == "dashboard-1"
                assert data["status"] == "connected"

    @pytest.mark.asyncio
    async def test_dashboard_subscribe_tasks(
        self,
        websocket_client,
        mock_websocket
    ):
        """Test dashboard task subscription."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            with patch.object(
                websocket_manager,
                'subscribe_to_tasks',
                new_callable=AsyncMock
            ) as mock_subscribe_to_tasks:
                # Execute
                with websocket_client.websocket_connect("/v1/dashboard") as websocket:
                    # Send subscribe tasks message
                    task_ids = ["task-1", "task-2", "task-3"]
                    websocket.send_text(json.dumps({
                        "type": "subscribe_tasks",
                        "task_ids": task_ids
                    }))

                    # Receive confirmation
                    data = json.loads(websocket.receive_text())
                    assert data["type"] == "tasks_subscribed"
                    assert data["task_ids"] == task_ids

                    # Verify subscribe was called
                    mock_subscribe_to_tasks.assert_called_once_with("conn-123", task_ids)

    @pytest.mark.asyncio
    async def test_dashboard_get_data(
        self,
        websocket_client,
        mock_websocket
    ):
        """Test dashboard data request."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect("/v1/dashboard") as websocket:
                # Send get dashboard data message
                task_ids = ["task-1", "task-2"]
                websocket.send_text(json.dumps({
                    "type": "get_dashboard_data",
                    "task_ids": task_ids
                }))

                # Receive dashboard data
                data = json.loads(websocket.receive_text())
                assert data["type"] == "dashboard_data"
                assert data["task_ids"] == task_ids
                assert "total_tasks" in data["data"]
                assert "active_tasks" in data["data"]
                assert "completed_tasks" in data["data"]


# ============================================================================
# WebSocket Disconnection Tests
# ============================================================================

class TestWebSocketDisconnection:
    """Test WebSocket disconnection handling."""

    @pytest.mark.asyncio
    async def test_normal_disconnection(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test normal WebSocket disconnection."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            with patch.object(websocket_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                # Execute
                with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                    pass  # Connection closes normally

                # Verify disconnect was called
                mock_disconnect.assert_called_once_with("conn-123")

    @pytest.mark.asyncio
    async def test_error_handling(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test error handling during WebSocket connection."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                # Simulate error
                websocket.send_text(json.dumps({"type": "invalid_type"}))
                # Connection should handle error gracefully

    @pytest.mark.asyncio
    async def test_connection_id_cleanup(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test connection ID cleanup on disconnect."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            with patch.object(websocket_manager, 'disconnect', new_callable=AsyncMock) as mock_disconnect:
                # Execute
                with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                    pass

                # Verify disconnect was called with correct connection ID
                mock_disconnect.assert_called_once_with("conn-123")


# ============================================================================
# Integration Tests
# ============================================================================

class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_full_workflow(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test complete WebSocket workflow."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute workflow
            with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                # 1. Receive welcome message
                data = json.loads(websocket.receive_text())
                assert data["status"] == "connected"

                # 2. Subscribe to updates
                websocket.send_text(json.dumps({
                    "type": "subscribe",
                    "task_id": sample_task_id
                }))
                data = json.loads(websocket.receive_text())
                assert data["type"] == "subscribed"

                # 3. Request progress data
                websocket.send_text(json.dumps({"type": "progress_request"}))
                data = json.loads(websocket.receive_text())
                assert data["type"] == "progress_data"

                # 4. Ping/pong
                websocket.send_text(json.dumps({"type": "ping"}))
                data = json.loads(websocket.receive_text())
                assert data["type"] == "pong"

    @pytest.mark.asyncio
    async def test_multiple_streams(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id,
        sample_user_id
    ):
        """Test multiple stream types."""
        # Setup
        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = "conn-123"

            # Execute
            with websocket_client.websocket_connect(
                "/v1/ws",
                task_id=sample_task_id,
                user_id=sample_user_id,
                stream_type="all"
            ) as websocket:
                # Should receive subscription for all streams
                subscriptions = []
                for _ in range(3):
                    data = json.loads(websocket.receive_text())
                    if data["type"] == "subscription":
                        subscriptions.append(data["stream_type"])

                assert len(subscriptions) == 3
                assert "progress" in subscriptions
                assert "logs" in subscriptions
                assert "notifications" in subscriptions

    @pytest.mark.asyncio
    async def test_concurrent_connections(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test handling multiple concurrent connections."""
        # Setup
        connection_ids = ["conn-1", "conn-2", "conn-3"]

        with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
            # Mock different connection IDs
            mock_connect.side_effect = connection_ids

            # Execute multiple connections
            async def test_connection(idx):
                with websocket_client.websocket_connect("/v1/ws", task_id=sample_task_id) as websocket:
                    data = json.loads(websocket.receive_text())
                    assert data["status"] == "connected"
                    return True

            # Test concurrent connections
            results = await asyncio.gather(
                test_connection(0),
                test_connection(1),
                test_connection(2)
            )

            # All connections should succeed
            assert all(results)

    @pytest.mark.asyncio
    async def test_stream_endpoint_selection(
        self,
        websocket_client,
        mock_websocket,
        sample_task_id
    ):
        """Test selecting different stream endpoints."""
        stream_types = ["progress", "logs", "notifications"]

        for stream_type in stream_types:
            # Setup
            with patch.object(websocket_manager, 'connect', new_callable=AsyncMock) as mock_connect:
                mock_connect.return_value = f"conn-{stream_type}"

                # Execute
                with websocket_client.websocket_connect(
                    f"/v1/stream/{stream_type}",
                    task_id=sample_task_id
                ) as websocket:
                    # Verify stream type
                    data = json.loads(websocket.receive_text())
                    assert data["stream_type"] == stream_type


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
