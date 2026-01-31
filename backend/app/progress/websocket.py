"""WebSocket connection management for real-time progress tracking.

This module provides WebSocketManager for handling WebSocket connections,
message routing, broadcasting, and connection pooling with support for
1000+ concurrent connections.
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Callable, Union
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from .schemas.websocket_messages import (
    WebSocketMessage,
    MessageType,
    ProgressUpdateMessage,
    LogMessage,
    NotificationMessage,
    MetricMessage,
    ConnectionMessage,
    HeartbeatMessage,
    ErrorMessage,
)
from .utils.serializers import serialize_websocket_message, deserialize_websocket_message
from .utils.validators import validate_task_id, validate_user_id

logger = logging.getLogger(__name__)


class ConnectionPool:
    """Manages a pool of WebSocket connections."""

    def __init__(self, max_size: int = 1000):
        """Initialize connection pool.

        Args:
            max_size: Maximum number of concurrent connections
        """
        self.max_size = max_size
        self.connections: Dict[str, WebSocketConnection] = {}
        self.task_connections: Dict[str, Set[str]] = defaultdict(set)
        self.user_connections: Dict[str, Set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add_connection(self, connection: "WebSocketConnection") -> bool:
        """Add connection to pool.

        Args:
            connection: WebSocketConnection to add

        Returns:
            True if added successfully, False if pool is full
        """
        async with self._lock:
            if len(self.connections) >= self.max_size:
                return False

            self.connections[connection.id] = connection

            # Track task-specific connections
            if connection.task_id:
                self.task_connections[connection.task_id].add(connection.id)

            # Track user-specific connections
            if connection.user_id:
                self.user_connections[connection.user_id].add(connection.id)

            return True

    async def remove_connection(self, connection_id: str) -> Optional["WebSocketConnection"]:
        """Remove connection from pool.

        Args:
            connection_id: ID of connection to remove

        Returns:
            Removed connection or None
        """
        async with self._lock:
            connection = self.connections.pop(connection_id, None)

            if connection:
                # Remove from task-specific tracking
                if connection.task_id:
                    self.task_connections[connection.task_id].discard(connection_id)
                    if not self.task_connections[connection.task_id]:
                        del self.task_connections[connection.task_id]

                # Remove from user-specific tracking
                if connection.user_id:
                    self.user_connections[connection.user_id].discard(connection_id)
                    if not self.user_connections[connection.user_id]:
                        del self.user_connections[connection.user_id]

            return connection

    async def get_connections_by_task(self, task_id: str) -> List["WebSocketConnection"]:
        """Get all connections for a specific task.

        Args:
            task_id: Task ID to filter by

        Returns:
            List of WebSocketConnection objects
        """
        async with self._lock:
            connection_ids = self.task_connections.get(task_id, set())
            return [self.connections[cid] for cid in connection_ids if cid in self.connections]

    async def get_connections_by_user(self, user_id: str) -> List["WebSocketConnection"]:
        """Get all connections for a specific user.

        Args:
            user_id: User ID to filter by

        Returns:
            List of WebSocketConnection objects
        """
        async with self._lock:
            connection_ids = self.user_connections.get(user_id, set())
            return [self.connections[cid] for cid in connection_ids if cid in self.connections]

    def get_connection_count(self) -> int:
        """Get current number of active connections.

        Returns:
            Number of active connections
        """
        return len(self.connections)

    def get_task_connection_count(self, task_id: str) -> int:
        """Get number of connections for a specific task.

        Args:
            task_id: Task ID

        Returns:
            Number of connections for the task
        """
        return len(self.task_connections.get(task_id, set()))

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a specific user.

        Args:
            user_id: User ID

        Returns:
            Number of connections for the user
        """
        return len(self.user_connections.get(user_id, set()))


class WebSocketConnection:
    """Represents a single WebSocket connection with metadata."""

    def __init__(
        self,
        websocket: WebSocket,
        connection_id: Optional[str] = None,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            connection_id: Unique connection ID (generated if not provided)
            task_id: Associated task ID (optional)
            user_id: Associated user ID (optional)
            metadata: Additional metadata
        """
        self.websocket = websocket
        self.id = connection_id or str(uuid4())
        self.task_id = task_id
        self.user_id = user_id
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_heartbeat = time.time()
        self.is_alive = True
        self.reconnect_count = 0
        self.max_reconnect_attempts = 5
        self.message_queue = deque(maxlen=1000)  # Store last 1000 messages

    async def send_message(self, message: Union[Dict[str, Any], WebSocketMessage]) -> bool:
        """Send message to this connection.

        Args:
            message: Message to send

        Returns:
            True if sent successfully, False otherwise
        """
        if self.websocket.application_state != WebSocketState.CONNECTED:
            return False

        try:
            if isinstance(message, dict):
                serialized = json.dumps(message)
            else:
                serialized = serialize_websocket_message(message.dict())

            await self.websocket.send_text(serialized)
            self.message_queue.append(serialized)
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {self.id}: {e}")
            self.is_alive = False
            return False

    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive message from this connection.

        Returns:
            Received message or None if failed
        """
        try:
            data = await self.websocket.receive_text()
            return deserialize_websocket_message(data)
        except WebSocketDisconnect:
            self.is_alive = False
            return None
        except Exception as e:
            logger.error(f"Failed to receive message from connection {self.id}: {e}")
            self.is_alive = False
            return None

    async def close(self, code: int = 1000, reason: str = ""):
        """Close the WebSocket connection.

        Args:
            code: Close code
            reason: Close reason
        """
        try:
            if self.websocket.application_state == WebSocketState.CONNECTED:
                await self.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.error(f"Error closing connection {self.id}: {e}")
        finally:
            self.is_alive = False

    def get_age(self) -> float:
        """Get connection age in seconds.

        Returns:
            Age in seconds
        """
        return time.time() - self.created_at

    def get_idle_time(self) -> float:
        """Get idle time since last heartbeat in seconds.

        Returns:
            Idle time in seconds
        """
        return time.time() - self.last_heartbeat

    def update_heartbeat(self):
        """Update last heartbeat timestamp."""
        self.last_heartbeat = time.time()
        self.is_alive = True


class WebSocketManager:
    """Manages WebSocket connections, routing, and broadcasting."""

    def __init__(
        self,
        max_connections: int = 1000,
        heartbeat_interval: float = 30.0,
        connection_timeout: float = 300.0,
        max_message_size: int = 1024 * 1024,  # 1MB
    ):
        """Initialize WebSocket manager.

        Args:
            max_connections: Maximum concurrent connections
            heartbeat_interval: Heartbeat interval in seconds
            connection_timeout: Connection timeout in seconds
            max_message_size: Maximum message size in bytes
        """
        self.connection_pool = ConnectionPool(max_size=max_connections)
        self.heartbeat_interval = heartbeat_interval
        self.connection_timeout = connection_timeout
        self.max_message_size = max_message_size
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        self.broadcast_subscribers: Dict[str, Set[str]] = defaultdict(set)
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "failed_sends": 0,
            "reconnections": 0,
        }

    async def start(self):
        """Start the WebSocket manager."""
        if self._is_running:
            return

        self._is_running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop the WebSocket manager."""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        connections = list(self.connection_pool.connections.values())
        for connection in connections:
            await connection.close()

        logger.info("WebSocket manager stopped")

    async def connect(
        self,
        websocket: WebSocket,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Accept a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance
            task_id: Associated task ID (optional)
            user_id: Associated user ID (optional)
            metadata: Additional metadata

        Returns:
            Connection ID if successful, None otherwise

        Raises:
            ValueError: If task_id or user_id is invalid
        """
        # Validate IDs if provided
        if task_id and not validate_task_id(task_id):
            raise ValueError(f"Invalid task_id: {task_id}")

        if user_id and not validate_user_id(user_id):
            raise ValueError(f"Invalid user_id: {user_id}")

        # Accept the connection
        await websocket.accept()

        # Create connection
        connection = WebSocketConnection(
            websocket=websocket,
            task_id=task_id,
            user_id=user_id,
            metadata=metadata,
        )

        # Add to pool
        added = await self.connection_pool.add_connection(connection)
        if not added:
            await connection.close(code=1008, reason="Connection pool full")
            logger.warning(f"Connection pool full, rejected connection")
            return None

        # Send welcome message
        welcome_message = ConnectionMessage(
            type=MessageType.CONNECTION,
            connection_id=connection.id,
            status="connected",
            timestamp=time.time(),
        )
        await connection.send_message(welcome_message.dict())

        # Update statistics
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = self.connection_pool.get_connection_count()

        logger.info(f"New WebSocket connection: {connection.id} (task={task_id}, user={user_id})")
        return connection.id

    async def disconnect(self, connection_id: str, code: int = 1000, reason: str = ""):
        """Disconnect a WebSocket connection.

        Args:
            connection_id: Connection ID to disconnect
            code: Close code
            reason: Close reason
        """
        connection = await self.connection_pool.remove_connection(connection_id)
        if connection:
            await connection.close(code=code, reason=reason)
            self.stats["active_connections"] = self.connection_pool.get_connection_count()
            logger.info(f"Disconnected WebSocket: {connection_id}")

    async def send_message(
        self,
        connection_id: str,
        message: Union[Dict[str, Any], WebSocketMessage],
    ) -> bool:
        """Send message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message to send

        Returns:
            True if sent successfully, False otherwise
        """
        connection = self.connection_pool.connections.get(connection_id)
        if not connection:
            return False

        success = await connection.send_message(message)
        if success:
            self.stats["total_messages_sent"] += 1
        else:
            self.stats["failed_sends"] += 1
            await self.disconnect(connection_id)

        return success

    async def broadcast_to_task(
        self,
        task_id: str,
        message: Union[Dict[str, Any], WebSocketMessage],
    ) -> int:
        """Broadcast message to all connections for a specific task.

        Args:
            task_id: Target task ID
            message: Message to broadcast

        Returns:
            Number of connections that received the message
        """
        connections = await self.connection_pool.get_connections_by_task(task_id)
        sent_count = 0

        for connection in connections:
            if await connection.send_message(message):
                sent_count += 1
                self.stats["total_messages_sent"] += 1
            else:
                await self.disconnect(connection.id)

        logger.debug(f"Broadcast to task {task_id}: {sent_count}/{len(connections)} connections")
        return sent_count

    async def broadcast_to_user(
        self,
        user_id: str,
        message: Union[Dict[str, Any], WebSocketMessage],
    ) -> int:
        """Broadcast message to all connections for a specific user.

        Args:
            user_id: Target user ID
            message: Message to broadcast

        Returns:
            Number of connections that received the message
        """
        connections = await self.connection_pool.get_connections_by_user(user_id)
        sent_count = 0

        for connection in connections:
            if await connection.send_message(message):
                sent_count += 1
                self.stats["total_messages_sent"] += 1
            else:
                await self.disconnect(connection.id)

        logger.debug(f"Broadcast to user {user_id}: {sent_count}/{len(connections)} connections")
        return sent_count

    async def broadcast_global(
        self,
        message: Union[Dict[str, Any], WebSocketMessage],
    ) -> int:
        """Broadcast message to all connected clients.

        Args:
            message: Message to broadcast

        Returns:
            Number of connections that received the message
        """
        connections = list(self.connection_pool.connections.values())
        sent_count = 0

        for connection in connections:
            if await connection.send_message(message):
                sent_count += 1
                self.stats["total_messages_sent"] += 1
            else:
                await self.disconnect(connection.id)

        logger.debug(f"Global broadcast: {sent_count}/{len(connections)} connections")
        return sent_count

    async def handle_message(
        self,
        connection_id: str,
        message: Union[Dict[str, Any], WebSocketMessage],
    ) -> bool:
        """Handle incoming message from a connection.

        Args:
            connection_id: Source connection ID
            message: Received message

        Returns:
            True if handled successfully, False otherwise
        """
        self.stats["total_messages_received"] += 1

        try:
            # Parse message if it's a dict
            if isinstance(message, dict):
                msg_type = message.get("type")
                if not msg_type or not MessageType.has_value(msg_type):
                    await self.send_error(connection_id, "Invalid message type")
                    return False

                msg_type_enum = MessageType(msg_type)

                # Create appropriate message object
                if msg_type_enum == MessageType.PROGRESS_UPDATE:
                    parsed_message = ProgressUpdateMessage(**message)
                elif msg_type_enum == MessageType.LOG_MESSAGE:
                    parsed_message = LogMessage(**message)
                elif msg_type_enum == MessageType.NOTIFICATION:
                    parsed_message = NotificationMessage(**message)
                elif msg_type_enum == MessageType.METRIC:
                    parsed_message = MetricMessage(**message)
                elif msg_type_enum == MessageType.HEARTBEAT:
                    parsed_message = HeartbeatMessage(**message)
                else:
                    parsed_message = WebSocketMessage(**message)
            else:
                parsed_message = message
                msg_type_enum = message.type

            # Call registered handlers
            handlers = self.message_handlers.get(msg_type_enum, [])
            for handler in handlers:
                try:
                    await handler(connection_id, parsed_message)
                except Exception as e:
                    logger.error(f"Error in message handler: {e}")

            return True

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self.send_error(connection_id, f"Message handling error: {str(e)}")
            return False

    async def send_error(self, connection_id: str, error_message: str, error_code: str = "ERROR"):
        """Send error message to a connection.

        Args:
            connection_id: Target connection ID
            error_message: Error message
            error_code: Error code
        """
        error_msg = ErrorMessage(
            type=MessageType.ERROR,
            error_code=error_code,
            message=error_message,
            timestamp=time.time(),
        )
        await self.send_message(connection_id, error_msg.dict())

    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a message handler.

        Args:
            message_type: Type of message to handle
            handler: Async handler function(connection_id, message)
        """
        self.message_handlers[message_type].append(handler)

    def unregister_handler(self, message_type: MessageType, handler: Callable):
        """Unregister a message handler.

        Args:
            message_type: Type of message
            handler: Handler to remove
        """
        if handler in self.message_handlers[message_type]:
            self.message_handlers[message_type].remove(handler)

    async def _heartbeat_loop(self):
        """Background task to send heartbeats and check connection health."""
        while self._is_running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Send heartbeat to all connections
                heartbeat = HeartbeatMessage(
                    type=MessageType.HEARTBEAT,
                    timestamp=time.time(),
                )

                connections = list(self.connection_pool.connections.values())
                for connection in connections:
                    connection.update_heartbeat()
                    await connection.send_message(heartbeat.dict())

                logger.debug(f"Heartbeat sent to {len(connections)} connections")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")

    async def _cleanup_loop(self):
        """Background task to clean up dead connections."""
        while self._is_running:
            try:
                await asyncio.sleep(self.heartbeat_interval * 2)

                # Find dead connections
                dead_connections = []
                for connection in self.connection_pool.connections.values():
                    idle_time = connection.get_idle_time()
                    if idle_time > self.connection_timeout:
                        dead_connections.append(connection.id)

                # Remove dead connections
                for connection_id in dead_connections:
                    await self.disconnect(connection_id, code=1001, reason="Connection timeout")

                if dead_connections:
                    logger.info(f"Cleaned up {len(dead_connections)} dead connections")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **self.stats,
            "connection_pool_size": self.connection_pool.get_connection_count(),
            "max_connections": self.connection_pool.max_size,
            "heartbeat_interval": self.heartbeat_interval,
            "connection_timeout": self.connection_timeout,
        }

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection.

        Args:
            connection_id: Connection ID

        Returns:
            Connection information or None
        """
        connection = self.connection_pool.connections.get(connection_id)
        if not connection:
            return None

        return {
            "id": connection.id,
            "task_id": connection.task_id,
            "user_id": connection.user_id,
            "created_at": connection.created_at,
            "age": connection.get_age(),
            "last_heartbeat": connection.last_heartbeat,
            "idle_time": connection.get_idle_time(),
            "is_alive": connection.is_alive,
            "reconnect_count": connection.reconnect_count,
            "metadata": connection.metadata,
        }

    def get_task_connections_info(self, task_id: str) -> List[Dict[str, Any]]:
        """Get information about all connections for a specific task.

        Args:
            task_id: Task ID

        Returns:
            List of connection information
        """
        return [
            self.get_connection_info(cid)
            for cid in self.connection_pool.task_connections.get(task_id, set())
            if self.get_connection_info(cid)
        ]

    def get_user_connections_info(self, user_id: str) -> List[Dict[str, Any]]:
        """Get information about all connections for a specific user.

        Args:
            user_id: User ID

        Returns:
            List of connection information
        """
        return [
            self.get_connection_info(cid)
            for cid in self.connection_pool.user_connections.get(user_id, set())
            if self.get_connection_info(cid)
        ]

    def _get_timestamp(self) -> float:
        """Get current timestamp.

        Returns:
            Current timestamp as float
        """
        return time.time()

    async def subscribe(
        self,
        connection_id: str,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Subscribe a connection to task or user updates.

        Args:
            connection_id: Connection ID
            task_id: Task ID to subscribe to (optional)
            user_id: User ID to subscribe to (optional)
        """
        connection = self.connection_pool.connections.get(connection_id)
        if not connection:
            return

        if task_id:
            self.connection_pool.task_connections[task_id].add(connection_id)
            logger.info(f"Connection {connection_id} subscribed to task {task_id}")

        if user_id:
            self.connection_pool.user_connections[user_id].add(connection_id)
            logger.info(f"Connection {connection_id} subscribed to user {user_id}")

    async def unsubscribe(
        self,
        connection_id: str,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Unsubscribe a connection from task or user updates.

        Args:
            connection_id: Connection ID
            task_id: Task ID to unsubscribe from (optional)
            user_id: User ID to unsubscribe from (optional)
        """
        connection = self.connection_pool.connections.get(connection_id)
        if not connection:
            return

        if task_id:
            self.connection_pool.task_connections[task_id].discard(connection_id)
            logger.info(f"Connection {connection_id} unsubscribed from task {task_id}")

        if user_id:
            self.connection_pool.user_connections[user_id].discard(connection_id)
            logger.info(f"Connection {connection_id} unsubscribed from user {user_id}")

    async def subscribe_to_tasks(self, connection_id: str, task_ids: List[str]):
        """Subscribe a connection to multiple tasks.

        Args:
            connection_id: Connection ID
            task_ids: List of task IDs
        """
        for task_id in task_ids:
            await self.subscribe(connection_id, task_id=task_id)
        logger.info(f"Connection {connection_id} subscribed to {len(task_ids)} tasks")


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
