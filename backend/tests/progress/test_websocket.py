"""Test cases for WebSocket connection management.

This module contains comprehensive unit tests for WebSocketManager including
connection management, message routing, broadcasting, and error handling.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime, timezone

from backend.app.progress.websocket import (
    WebSocketManager,
    ConnectionPool,
    WebSocketConnection,
)
from backend.app.progress.schemas.websocket_messages import (
    ProgressUpdateMessage,
    LogMessage,
    NotificationMessage,
    ConnectionMessage,
    HeartbeatMessage,
)


class TestConnectionPool:
    """Test cases for ConnectionPool."""

    def test_connection_pool_initialization(self):
        """Test ConnectionPool initialization."""
        pool = ConnectionPool(max_size=500)
        assert pool.max_size == 500
        assert len(pool.connections) == 0
        assert len(pool.task_connections) == 0
        assert len(pool.user_connections) == 0

    def test_connection_pool_default_size(self):
        """Test ConnectionPool with default size."""
        pool = ConnectionPool()
        assert pool.max_size == 1000

    @pytest.mark.asyncio
    async def test_add_connection_success(self):
        """Test adding connection successfully."""
        pool = ConnectionPool(max_size=100)

        # Create mock connection
        mock_connection = MagicMock()
        mock_connection.id = "conn-001"
        mock_connection.task_id = "task-001"
        mock_connection.user_id = "user-001"

        result = await pool.add_connection(mock_connection)
        assert result is True
        assert "conn-001" in pool.connections
        assert "task-001" in pool.task_connections
        assert "user-001" in pool.user_connections

    @pytest.mark.asyncio
    async def test_add_connection_pool_full(self):
        """Test adding connection when pool is full."""
        pool = ConnectionPool(max_size=1)

        # Add first connection
        mock_connection1 = MagicMock()
        mock_connection1.id = "conn-001"
        mock_connection1.task_id = "task-001"
        mock_connection1.user_id = "user-001"

        result1 = await pool.add_connection(mock_connection1)
        assert result1 is True

        # Try to add second connection (should fail)
        mock_connection2 = MagicMock()
        mock_connection2.id = "conn-002"
        mock_connection2.task_id = "task-002"
        mock_connection2.user_id = "user-002"

        result2 = await pool.add_connection(mock_connection2)
        assert result2 is False
        assert len(pool.connections) == 1

    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """Test removing connection."""
        pool = ConnectionPool(max_size=100)

        # Add connection
        mock_connection = MagicMock()
        mock_connection.id = "conn-001"
        mock_connection.task_id = "task-001"
        mock_connection.user_id = "user-001"

        await pool.add_connection(mock_connection)
        assert "conn-001" in pool.connections

        # Remove connection
        removed_connection = await pool.remove_connection("conn-001")
        assert removed_connection == mock_connection
        assert "conn-001" not in pool.connections
        assert "task-001" not in pool.task_connections
        assert "user-001" not in pool.user_connections

    @pytest.mark.asyncio
    async def test_remove_nonexistent_connection(self):
        """Test removing nonexistent connection."""
        pool = ConnectionPool()
        removed_connection = await pool.remove_connection("nonexistent")
        assert removed_connection is None

    @pytest.mark.asyncio
    async def test_get_connections_by_task(self):
        """Test getting connections by task ID."""
        pool = ConnectionPool(max_size=100)

        # Add multiple connections for same task
        for i in range(3):
            mock_connection = MagicMock()
            mock_connection.id = f"conn-{i:03d}"
            mock_connection.task_id = "task-001"
            mock_connection.user_id = f"user-{i:03d}"
            await pool.add_connection(mock_connection)

        # Add connection for different task
        mock_connection2 = MagicMock()
        mock_connection2.id = "conn-999"
        mock_connection2.task_id = "task-002"
        mock_connection2.user_id = "user-999"
        await pool.add_connection(mock_connection2)

        # Get connections for task-001
        task_connections = await pool.get_connections_by_task("task-001")
        assert len(task_connections) == 3
        for conn in task_connections:
            assert conn.task_id == "task-001"

        # Get connections for task-002
        task_connections2 = await pool.get_connections_by_task("task-002")
        assert len(task_connections2) == 1
        assert task_connections2[0].task_id == "task-002"

    @pytest.mark.asyncio
    async def test_get_connections_by_user(self):
        """Test getting connections by user ID."""
        pool = ConnectionPool(max_size=100)

        # Add multiple connections for same user
        for i in range(2):
            mock_connection = MagicMock()
            mock_connection.id = f"conn-{i:03d}"
            mock_connection.task_id = f"task-{i:03d}"
            mock_connection.user_id = "user-001"
            await pool.add_connection(mock_connection)

        # Add connection for different user
        mock_connection2 = MagicMock()
        mock_connection2.id = "conn-999"
        mock_connection2.task_id = "task-999"
        mock_connection2.user_id = "user-002"
        await pool.add_connection(mock_connection2)

        # Get connections for user-001
        user_connections = await pool.get_connections_by_user("user-001")
        assert len(user_connections) == 2
        for conn in user_connections:
            assert conn.user_id == "user-001"

    def test_get_connection_count(self):
        """Test getting connection count."""
        pool = ConnectionPool()
        assert pool.get_connection_count() == 0

        # Can't test with async add_connection here, so just check empty count
        pool.connections["conn-001"] = MagicMock()
        assert pool.get_connection_count() == 1


class TestWebSocketConnection:
    """Test cases for WebSocketConnection."""

    def test_websocket_connection_initialization(self):
        """Test WebSocketConnection initialization."""
        mock_websocket = MagicMock()
        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001",
            metadata={"source": "test"}
        )

        assert connection.id == "conn-001"
        assert connection.task_id == "task-001"
        assert connection.user_id == "user-001"
        assert connection.metadata["source"] == "test"
        assert connection.is_alive is True
        assert connection.reconnect_count == 0

    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Test sending message successfully."""
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock(return_value=True)

        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001"
        )

        message = {"type": "progress_update", "progress": 50.0}
        result = await connection.send_message(message)

        assert result is True
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Test sending message failure."""
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))

        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001"
        )

        message = {"type": "progress_update", "progress": 50.0}
        result = await connection.send_message(message)

        assert result is False
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_invalid_connection(self):
        """Test sending message with invalid connection state."""
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock(return_value=True)
        mock_websocket.application_state = "DISCONNECTED"

        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001"
        )

        # Simulate disconnected state
        connection.is_alive = False

        message = {"type": "progress_update", "progress": 50.0}
        result = await connection.send_message(message)

        assert result is False

    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing connection."""
        mock_websocket = MagicMock()
        mock_websocket.close = AsyncMock()

        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001"
        )

        await connection.close(code=1000, reason="Normal closure")

        assert connection.is_alive is False
        mock_websocket.close.assert_called_once_with(code=1000, reason="Normal closure")

    def test_get_age(self):
        """Test getting connection age."""
        mock_websocket = MagicMock()
        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001"
        )

        age = connection.get_age()
        assert age >= 0
        assert isinstance(age, float)

    def test_get_idle_time(self):
        """Test getting idle time."""
        mock_websocket = MagicMock()
        connection = WebSocketConnection(
            websocket=mock_websocket,
            connection_id="conn-001",
            task_id="task-001",
            user_id="user-001"
        )

        idle_time = connection.get_idle_time()
        assert idle_time >= 0
        assert isinstance(idle_time, float)


class TestWebSocketManager:
    """Test cases for WebSocketManager."""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager(
            max_connections=100,
            heartbeat_interval=30,
            connection_timeout=300
        )

    def test_websocket_manager_initialization(self, websocket_manager):
        """Test WebSocketManager initialization."""
        assert websocket_manager.max_connections == 100
        assert websocket_manager.heartbeat_interval == 30
        assert websocket_manager.connection_timeout == 300
        assert websocket_manager._is_running is False
        assert "total_connections" in websocket_manager.stats
        assert "active_connections" in websocket_manager.stats

    @pytest.mark.asyncio
    async def test_start_and_stop(self, websocket_manager):
        """Test starting and stopping WebSocketManager."""
        await websocket_manager.start()

        assert websocket_manager._is_running is True
        assert websocket_manager._heartbeat_task is not None
        assert websocket_manager._cleanup_task is not None

        await websocket_manager.stop()

        assert websocket_manager._is_running is False
        assert websocket_manager._heartbeat_task.done()
        assert websocket_manager._cleanup_task.done()

    @pytest.mark.asyncio
    async def test_connect_success(self, websocket_manager):
        """Test successful connection."""
        # Mock WebSocket
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        # Connect
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        assert connection_id is not None
        assert connection_id in websocket_manager.connection_pool.connections
        assert websocket_manager.stats["total_connections"] == 1

    @pytest.mark.asyncio
    async def test_connect_max_connections(self, websocket_manager):
        """Test connection when at max capacity."""
        # Set max connections to 1
        websocket_manager.max_connections = 1

        # First connection should succeed
        mock_websocket1 = MagicMock()
        mock_websocket1.send_text = AsyncMock()

        connection_id1 = await websocket_manager.connect(
            websocket=mock_websocket1,
            task_id="task-001",
            user_id="user-001"
        )
        assert connection_id1 is not None

        # Second connection should fail
        mock_websocket2 = MagicMock()
        mock_websocket2.send_text = AsyncMock()

        connection_id2 = await websocket_manager.connect(
            websocket=mock_websocket2,
            task_id="task-002",
            user_id="user-002"
        )
        assert connection_id2 is None

    @pytest.mark.asyncio
    async def test_disconnect(self, websocket_manager):
        """Test disconnection."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.close = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Disconnect
        await websocket_manager.disconnect(connection_id, code=1000, reason="Normal closure")

        assert connection_id not in websocket_manager.connection_pool.connections
        assert websocket_manager.stats["active_connections"] == 0

    @pytest.mark.asyncio
    async def test_send_message_success(self, websocket_manager):
        """Test sending message successfully."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Send message
        message = {"type": "progress_update", "progress": 50.0}
        result = await websocket_manager.send_message(connection_id, message)

        assert result is True
        mock_websocket.send_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_nonexistent_connection(self, websocket_manager):
        """Test sending message to nonexistent connection."""
        message = {"type": "progress_update", "progress": 50.0}
        result = await websocket_manager.send_message("nonexistent", message)

        assert result is False

    @pytest.mark.asyncio
    async def test_broadcast_to_task(self, websocket_manager):
        """Test broadcasting message to task."""
        # Connect multiple clients for same task
        mock_websocket1 = MagicMock()
        mock_websocket1.send_text = AsyncMock()

        mock_websocket2 = MagicMock()
        mock_websocket2.send_text = AsyncMock()

        connection_id1 = await websocket_manager.connect(
            websocket=mock_websocket1,
            task_id="task-001",
            user_id="user-001"
        )

        connection_id2 = await websocket_manager.connect(
            websocket=mock_websocket2,
            task_id="task-001",
            user_id="user-002"
        )

        # Broadcast to task
        message = {"type": "progress_update", "progress": 75.0}
        sent_count = await websocket_manager.broadcast_to_task("task-001", message)

        assert sent_count == 2
        assert mock_websocket1.send_text.call_count == 1
        assert mock_websocket2.send_text.call_count == 1

    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, websocket_manager):
        """Test broadcasting message to user."""
        # Connect multiple tasks for same user
        mock_websocket1 = MagicMock()
        mock_websocket1.send_text = AsyncMock()

        mock_websocket2 = MagicMock()
        mock_websocket2.send_text = AsyncMock()

        connection_id1 = await websocket_manager.connect(
            websocket=mock_websocket1,
            task_id="task-001",
            user_id="user-001"
        )

        connection_id2 = await websocket_manager.connect(
            websocket=mock_websocket2,
            task_id="task-002",
            user_id="user-001"
        )

        # Broadcast to user
        message = {"type": "notification", "title": "Task Update"}
        sent_count = await websocket_manager.broadcast_to_user("user-001", message)

        assert sent_count == 2
        assert mock_websocket1.send_text.call_count == 1
        assert mock_websocket2.send_text.call_count == 1

    @pytest.mark.asyncio
    async def test_broadcast_global(self, websocket_manager):
        """Test global broadcasting."""
        # Connect multiple clients
        mock_websocket1 = MagicMock()
        mock_websocket1.send_text = AsyncMock()

        mock_websocket2 = MagicMock()
        mock_websocket2.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_websocket1,
            task_id="task-001",
            user_id="user-001"
        )

        await websocket_manager.connect(
            websocket=mock_websocket2,
            task_id="task-002",
            user_id="user-002"
        )

        # Broadcast globally
        message = {"type": "system_alert", "message": "System maintenance"}
        sent_count = await websocket_manager.broadcast_global(message)

        assert sent_count == 2
        assert mock_websocket1.send_text.call_count == 1
        assert mock_websocket2.send_text.call_count == 1

    @pytest.mark.asyncio
    async def test_heartbeat(self, websocket_manager):
        """Test heartbeat functionality."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Send heartbeat
        await websocket_manager._send_heartbeat()

        # Verify heartbeat was sent
        mock_websocket.send_text.assert_called()

    def test_get_stats(self, websocket_manager):
        """Test getting statistics."""
        # Update some stats
        websocket_manager.stats["total_connections"] = 5
        websocket_manager.stats["total_messages_sent"] = 100
        websocket_manager.stats["failed_sends"] = 2

        stats = websocket_manager.get_stats()

        assert stats["total_connections"] == 5
        assert stats["total_messages_sent"] == 100
        assert stats["failed_sends"] == 2
        assert "connection_pool_size" in stats
        assert "max_connections" in stats

    def test_get_connection_info(self, websocket_manager):
        """Test getting connection information."""
        # Can't test without actual connection, so test with empty pool
        info = websocket_manager.get_connection_info("nonexistent")
        assert info is None

    def test_get_task_connections_info(self, websocket_manager):
        """Test getting task connections information."""
        # Test with empty pool
        info = websocket_manager.get_task_connections_info("task-001")
        assert info == []

    def test_get_user_connections_info(self, websocket_manager):
        """Test getting user connections information."""
        # Test with empty pool
        info = websocket_manager.get_user_connections_info("user-001")
        assert info == []


class TestWebSocketMessageHandling:
    """Test cases for WebSocket message handling."""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager(max_connections=100)

    @pytest.mark.asyncio
    async def test_handle_progress_update_message(self, websocket_manager):
        """Test handling progress update message."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Create progress update message
        message = ProgressUpdateMessage(
            task_id="task-001",
            user_id="user-001",
            progress=50.0,
            status="running",
            message="Processing step 2"
        )

        # Handle message
        result = await websocket_manager.handle_message(connection_id, message)

        assert result is True

    @pytest.mark.asyncio
    async def test_handle_log_message(self, websocket_manager):
        """Test handling log message."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Create log message
        message = LogMessage(
            task_id="task-001",
            user_id="user-001",
            level="INFO",
            message="Task started",
            source="task_executor"
        )

        # Handle message
        result = await websocket_manager.handle_message(connection_id, message)

        assert result is True

    @pytest.mark.asyncio
    async def test_handle_notification_message(self, websocket_manager):
        """Test handling notification message."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Create notification message
        message = NotificationMessage(
            user_id="user-001",
            title="Task Completed",
            message="Your task has been completed",
            notification_type="success"
        )

        # Handle message
        result = await websocket_manager.handle_message(connection_id, message)

        assert result is True

    @pytest.mark.asyncio
    async def test_handle_heartbeat_message(self, websocket_manager):
        """Test handling heartbeat message."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Create heartbeat message
        message = HeartbeatMessage(
            client_id=connection_id,
            server_time=datetime.now(timezone.utc),
            latency_ms=50
        )

        # Handle message
        result = await websocket_manager.handle_message(connection_id, message)

        assert result is True

    @pytest.mark.asyncio
    async def test_handle_connection_message(self, websocket_manager):
        """Test handling connection message."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Create connection message
        message = ConnectionMessage(
            action="connect",
            client_id=connection_id,
            user_id="user-001"
        )

        # Handle message
        result = await websocket_manager.handle_message(connection_id, message)

        assert result is True


class TestWebSocketErrorHandling:
    """Test cases for WebSocket error handling."""

    @pytest.fixture
    def websocket_manager(self):
        """Create WebSocketManager instance for testing."""
        return WebSocketManager(max_connections=100)

    @pytest.mark.asyncio
    async def test_connect_invalid_parameters(self, websocket_manager):
        """Test connection with invalid parameters."""
        mock_websocket = MagicMock()

        # Test with empty task_id
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="",
            user_id="user-001"
        )

        assert connection_id is None

        # Test with empty user_id
        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id=""
        )

        assert connection_id is None

    @pytest.mark.asyncio
    async def test_send_message_connection_error(self, websocket_manager):
        """Test sending message when connection has error."""
        # Connect
        mock_websocket = MagicMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))

        connection_id = await websocket_manager.connect(
            websocket=mock_websocket,
            task_id="task-001",
            user_id="user-001"
        )

        # Try to send message (should handle error and disconnect)
        message = {"type": "progress_update", "progress": 50.0}
        result = await websocket_manager.send_message(connection_id, message)

        assert result is False
        assert connection_id not in websocket_manager.connection_pool.connections

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_task(self, websocket_manager):
        """Test broadcasting to nonexistent task."""
        message = {"type": "progress_update", "progress": 50.0}
        sent_count = await websocket_manager.broadcast_to_task("nonexistent", message)

        assert sent_count == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_nonexistent_user(self, websocket_manager):
        """Test broadcasting to nonexistent user."""
        message = {"type": "notification", "title": "Test"}
        sent_count = await websocket_manager.broadcast_to_user("nonexistent", message)

        assert sent_count == 0


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    @pytest.mark.asyncio
    async def test_full_connection_lifecycle(self):
        """Test complete connection lifecycle."""
        manager = WebSocketManager(max_connections=100)

        # Start manager
        await manager.start()

        try:
            # Connect
            mock_websocket = MagicMock()
            mock_websocket.send_text = AsyncMock()

            connection_id = await manager.connect(
                websocket=mock_websocket,
                task_id="task-001",
                user_id="user-001",
                metadata={"client": "test"}
            )

            assert connection_id is not None

            # Verify connection
            connection_info = manager.get_connection_info(connection_id)
            assert connection_info is not None
            assert connection_info["task_id"] == "task-001"
            assert connection_info["user_id"] == "user-001"

            # Send message
            message = {"type": "progress_update", "progress": 25.0}
            result = await manager.send_message(connection_id, message)
            assert result is True

            # Broadcast to task
            message2 = {"type": "progress_update", "progress": 50.0}
            sent_count = await manager.broadcast_to_task("task-001", message2)
            assert sent_count == 1

            # Disconnect
            await manager.disconnect(connection_id)
            assert connection_id not in manager.connection_pool.connections

        finally:
            # Stop manager
            await manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_connections_same_user(self):
        """Test multiple connections for same user."""
        manager = WebSocketManager(max_connections=100)

        await manager.start()

        try:
            # Connect multiple tasks for same user
            connection_ids = []
            for i in range(3):
                mock_websocket = MagicMock()
                mock_websocket.send_text = AsyncMock()

                connection_id = await manager.connect(
                    websocket=mock_websocket,
                    task_id=f"task-{i:03d}",
                    user_id="user-001"
                )

                assert connection_id is not None
                connection_ids.append(connection_id)

            # Verify all connections
            assert len(manager.connection_pool.connections) == 3

            # Get user connections
            user_connections = manager.get_user_connections_info("user-001")
            assert len(user_connections) == 3

            # Broadcast to user
            message = {"type": "notification", "title": "User Update"}
            sent_count = await manager.broadcast_to_user("user-001", message)
            assert sent_count == 3

        finally:
            await manager.stop()

    @pytest.mark.asyncio
    async def test_concurrent_connections(self):
        """Test concurrent connections."""
        manager = WebSocketManager(max_connections=1000)

        await manager.start()

        try:
            # Create multiple connections concurrently
            async def create_connection(i):
                mock_websocket = MagicMock()
                mock_websocket.send_text = AsyncMock()

                connection_id = await manager.connect(
                    websocket=mock_websocket,
                    task_id=f"task-{i:03d}",
                    user_id=f"user-{i:03d}"
                )

                return connection_id

            # Create 50 connections concurrently
            tasks = [create_connection(i) for i in range(50)]
            connection_ids = await asyncio.gather(*tasks)

            # Verify all connections created
            assert len(connection_ids) == 50
            assert all(cid is not None for cid in connection_ids)
            assert len(manager.connection_pool.connections) == 50

        finally:
            await manager.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
