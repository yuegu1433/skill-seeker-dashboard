"""WebSocket handler for real-time storage status updates.

This module provides WebSocket handlers for real-time communication with storage
clients, including connection management, message broadcasting, and status updates.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Any, Callable
from uuid import UUID, uuid4

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.versioning import VersionManager
from backend.app.storage.cache import CacheManager
from backend.app.storage.backup import BackupManager

logger = logging.getLogger(__name__)


class WebSocketConnectionError(Exception):
    """Raised when WebSocket connection fails."""
    pass


class MessageTooLargeError(Exception):
    """Raised when message is too large to send."""
    pass


class ConnectionState:
    """WebSocket connection state."""

    def __init__(self, connection_id: str, websocket: WebSocket):
        """Initialize connection state.

        Args:
            connection_id: Unique connection identifier
            websocket: WebSocket connection
        """
        self.connection_id = connection_id
        self.websocket = websocket
        self.client_id: Optional[str] = None
        self.subscribed_skills: Set[str] = set()
        self.subscribed_events: Set[str] = set()
        self.last_ping = time.time()
        self.is_alive = True
        self.created_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert connection state to dictionary.

        Returns:
            Dictionary representation of connection state
        """
        return {
            "connection_id": self.connection_id,
            "client_id": self.client_id,
            "subscribed_skills": list(self.subscribed_skills),
            "subscribed_events": list(self.subscribed_events),
            "is_alive": self.is_alive,
            "uptime_seconds": time.time() - self.created_at,
        }


class StatusMessage(BaseModel):
    """WebSocket status message."""

    type: str
    event: str
    data: Dict[str, Any]
    timestamp: str
    connection_id: Optional[str] = None


class StorageWebSocketHandler:
    """WebSocket handler for storage system real-time updates.

    Manages WebSocket connections, message broadcasting, and real-time
    status updates for storage operations.
    """

    def __init__(
        self,
        storage_manager: Optional[SkillStorageManager] = None,
        version_manager: Optional[VersionManager] = None,
        cache_manager: Optional[CacheManager] = None,
        backup_manager: Optional[BackupManager] = None,
        max_connections: int = 1000,
        max_message_size: int = 1024 * 1024,  # 1MB
        ping_interval: int = 30,
        ping_timeout: int = 10,
    ):
        """Initialize WebSocket handler.

        Args:
            storage_manager: Storage manager instance
            version_manager: Version manager instance
            cache_manager: Cache manager instance
            backup_manager: Backup manager instance
            max_connections: Maximum number of concurrent connections
            max_message_size: Maximum message size in bytes
            ping_interval: Ping interval in seconds
            ping_timeout: Ping timeout in seconds
        """
        self.storage_manager = storage_manager
        self.version_manager = version_manager
        self.cache_manager = cache_manager
        self.backup_manager = backup_manager

        # Connection management
        self.max_connections = max_connections
        self.max_message_size = max_message_size
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout

        # Active connections
        self.connections: Dict[str, ConnectionState] = {}
        self.connection_locks: Dict[str, asyncio.Lock] = {}

        # Subscriptions
        self.skill_subscriptions: Dict[str, Set[str]] = {}  # skill_id -> connection_ids
        self.event_subscriptions: Dict[str, Set[str]] = {}  # event_type -> connection_ids

        # Task management
        self.background_tasks: Set[asyncio.Task] = set()

        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "total_messages_sent": 0,
            "total_messages_received": 0,
            "total_errors": 0,
            "connection_timeouts": 0,
        }

        # Event handlers
        self.event_handlers: Dict[str, Callable] = {
            "file.upload": self._handle_file_upload,
            "file.delete": self._handle_file_delete,
            "file.move": self._handle_file_move,
            "version.create": self._handle_version_create,
            "version.restore": self._handle_version_restore,
            "backup.create": self._handle_backup_create,
            "backup.restore": self._handle_backup_restore,
            "cache.invalidate": self._handle_cache_invalidate,
        }

        logger.info("StorageWebSocketHandler initialized")

    async def connect(self, websocket: WebSocket, connection_id: Optional[str] = None) -> str:
        """Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            connection_id: Optional connection ID

        Returns:
            Connection ID

        Raises:
            WebSocketConnectionError: If connection limit exceeded
        """
        if len(self.connections) >= self.max_connections:
            raise WebSocketConnectionError(f"Connection limit exceeded: {self.max_connections}")

        # Generate connection ID if not provided
        if connection_id is None:
            connection_id = str(uuid4())

        # Accept connection
        await websocket.accept()

        # Create connection state
        connection_state = ConnectionState(connection_id, websocket)
        self.connections[connection_id] = connection_state
        self.connection_locks[connection_id] = asyncio.Lock()

        # Update statistics
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.connections)

        # Start background tasks
        task = asyncio.create_task(self._connection_handler(connection_id))
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)

        logger.info(f"WebSocket connected: {connection_id}")

        # Send welcome message
        await self.send_message(
            connection_id,
            StatusMessage(
                type="status",
                event="connected",
                data={
                    "connection_id": connection_id,
                    "message": "Connected to storage system",
                    "server_time": datetime.utcnow().isoformat(),
                },
                timestamp=datetime.utcnow().isoformat(),
                connection_id=connection_id,
            ),
        )

        return connection_id

    async def disconnect(self, connection_id: str, reason: Optional[str] = None):
        """Disconnect a WebSocket connection.

        Args:
            connection_id: Connection ID to disconnect
            reason: Optional disconnection reason
        """
        if connection_id not in self.connections:
            return

        connection_state = self.connections[connection_id]

        # Remove from subscriptions
        await self._remove_from_subscriptions(connection_id)

        # Close connection
        try:
            await connection_state.websocket.close()
        except Exception:
            pass  # Connection already closed

        # Remove from active connections
        del self.connections[connection_id]
        if connection_id in self.connection_locks:
            del self.connection_locks[connection_id]

        # Update statistics
        self.stats["active_connections"] = len(self.connections)

        logger.info(f"WebSocket disconnected: {connection_id}, reason: {reason}")

    async def send_message(
        self,
        connection_id: str,
        message: StatusMessage,
    ) -> bool:
        """Send a message to a specific connection.

        Args:
            connection_id: Connection ID
            message: Message to send

        Returns:
            True if sent successfully, False otherwise

        Raises:
            MessageTooLargeError: If message is too large
        """
        if connection_id not in self.connections:
            return False

        # Check message size
        message_json = json.dumps(message.dict())
        if len(message_json) > self.max_message_size:
            raise MessageTooLargeError(f"Message size exceeds limit: {self.max_message_size}")

        try:
            connection_state = self.connections[connection_id]
            await connection_state.websocket.send_text(message_json)
            self.stats["total_messages_sent"] += 1
            return True

        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {e}")
            self.stats["total_errors"] += 1
            return False

    async def broadcast_message(
        self,
        message: StatusMessage,
        connection_ids: Optional[List[str]] = None,
    ) -> int:
        """Broadcast a message to multiple connections.

        Args:
            message: Message to broadcast
            connection_ids: Optional list of connection IDs (broadcast to all if None)

        Returns:
            Number of connections that received the message
        """
        if connection_ids is None:
            connection_ids = list(self.connections.keys())

        success_count = 0
        for connection_id in connection_ids:
            if await self.send_message(connection_id, message):
                success_count += 1

        return success_count

    async def subscribe_skill(self, connection_id: str, skill_id: str) -> bool:
        """Subscribe a connection to skill updates.

        Args:
            connection_id: Connection ID
            skill_id: Skill ID to subscribe

        Returns:
            True if subscribed successfully
        """
        if connection_id not in self.connections:
            return False

        connection_state = self.connections[connection_id]
        connection_state.subscribed_skills.add(skill_id)

        # Add to skill subscriptions
        if skill_id not in self.skill_subscriptions:
            self.skill_subscriptions[skill_id] = set()
        self.skill_subscriptions[skill_id].add(connection_id)

        logger.debug(f"Subscribed connection {connection_id} to skill {skill_id}")

        # Send subscription confirmation
        await self.send_message(
            connection_id,
            StatusMessage(
                type="subscription",
                event="skill_subscribed",
                data={"skill_id": skill_id},
                timestamp=datetime.utcnow().isoformat(),
                connection_id=connection_id,
            ),
        )

        return True

    async def unsubscribe_skill(self, connection_id: str, skill_id: str) -> bool:
        """Unsubscribe a connection from skill updates.

        Args:
            connection_id: Connection ID
            skill_id: Skill ID to unsubscribe

        Returns:
            True if unsubscribed successfully
        """
        if connection_id not in self.connections:
            return False

        connection_state = self.connections[connection_id]
        connection_state.subscribed_skills.discard(skill_id)

        # Remove from skill subscriptions
        if skill_id in self.skill_subscriptions:
            self.skill_subscriptions[skill_id].discard(connection_id)
            if not self.skill_subscriptions[skill_id]:
                del self.skill_subscriptions[skill_id]

        logger.debug(f"Unsubscribed connection {connection_id} from skill {skill_id}")

        return True

    async def subscribe_events(self, connection_id: str, event_types: List[str]) -> bool:
        """Subscribe a connection to event updates.

        Args:
            connection_id: Connection ID
            event_types: List of event types to subscribe

        Returns:
            True if subscribed successfully
        """
        if connection_id not in self.connections:
            return False

        connection_state = self.connections[connection_id]
        connection_state.subscribed_events.update(event_types)

        # Add to event subscriptions
        for event_type in event_types:
            if event_type not in self.event_subscriptions:
                self.event_subscriptions[event_type] = set()
            self.event_subscriptions[event_type].add(connection_id)

        logger.debug(f"Subscribed connection {connection_id} to events: {event_types}")

        return True

    async def notify_skill_update(self, skill_id: str, event_type: str, data: Dict[str, Any]):
        """Notify all connections subscribed to a skill.

        Args:
            skill_id: Skill ID
            event_type: Type of event
            data: Event data
        """
        if skill_id not in self.skill_subscriptions:
            return

        connection_ids = list(self.skill_subscriptions[skill_id])

        message = StatusMessage(
            type="skill_update",
            event=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
        )

        await self.broadcast_message(message, connection_ids)

    async def notify_event(self, event_type: str, data: Dict[str, Any]):
        """Notify all connections subscribed to an event type.

        Args:
            event_type: Type of event
            data: Event data
        """
        if event_type not in self.event_subscriptions:
            return

        connection_ids = list(self.event_subscriptions[event_type])

        message = StatusMessage(
            type="event",
            event=event_type,
            data=data,
            timestamp=datetime.utcnow().isoformat(),
        )

        await self.broadcast_message(message, connection_ids)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket handler statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "connections": {
                "total": self.stats["total_connections"],
                "active": self.stats["active_connections"],
                "max": self.max_connections,
                "subscribed_skills": len(self.skill_subscriptions),
                "subscribed_events": len(self.event_subscriptions),
            },
            "messages": {
                "sent": self.stats["total_messages_sent"],
                "received": self.stats["total_messages_received"],
                "errors": self.stats["total_errors"],
                "timeouts": self.stats["connection_timeouts"],
            },
            "configuration": {
                "max_message_size": self.max_message_size,
                "ping_interval": self.ping_interval,
                "ping_timeout": self.ping_timeout,
            },
            "connections_detail": [
                conn.to_dict() for conn in self.connections.values()
            ],
        }

    async def _connection_handler(self, connection_id: str):
        """Handle a WebSocket connection.

        Args:
            connection_id: Connection ID
        """
        try:
            connection_state = self.connections.get(connection_id)
            if not connection_state:
                return

            while connection_state.is_alive:
                try:
                    # Set timeout for receive
                    message = await asyncio.wait_for(
                        connection_state.websocket.receive_text(),
                        timeout=self.ping_interval,
                    )

                    # Process message
                    self.stats["total_messages_received"] += 1
                    await self._process_message(connection_id, message)

                except asyncio.TimeoutError:
                    # Check if connection is still alive
                    if connection_state.is_alive:
                        # Send ping
                        try:
                            await connection_state.websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "ping",
                                        "timestamp": datetime.utcnow().isoformat(),
                                    }
                                )
                            )
                        except Exception:
                            # Connection is dead
                            connection_state.is_alive = False
                            break

                except WebSocketDisconnect:
                    connection_state.is_alive = False
                    break

                except Exception as e:
                    logger.error(f"Error in connection handler {connection_id}: {e}")
                    self.stats["total_errors"] += 1
                    break

        finally:
            # Disconnect
            await self.disconnect(connection_id, "Connection handler ended")

    async def _process_message(self, connection_id: str, message_text: str):
        """Process a received message.

        Args:
            connection_id: Connection ID
            message_text: Raw message text
        """
        try:
            message_data = json.loads(message_text)
            message_type = message_data.get("type")

            if message_type == "ping":
                # Respond to ping
                await self.send_message(
                    connection_id,
                    StatusMessage(
                        type="pong",
                        event="ping",
                        data={"timestamp": message_data.get("timestamp")},
                        timestamp=datetime.utcnow().isoformat(),
                        connection_id=connection_id,
                    ),
                )

            elif message_type == "subscribe":
                # Handle subscription
                event = message_data.get("event")
                if event == "skill":
                    skill_id = message_data.get("skill_id")
                    if skill_id:
                        await self.subscribe_skill(connection_id, skill_id)

            elif message_type == "unsubscribe":
                # Handle unsubscription
                event = message_data.get("event")
                if event == "skill":
                    skill_id = message_data.get("skill_id")
                    if skill_id:
                        await self.unsubscribe_skill(connection_id, skill_id)

            elif message_type == "event_subscribe":
                # Handle event subscription
                event_types = message_data.get("event_types", [])
                await self.subscribe_events(connection_id, event_types)

            elif message_type == "ping":
                # Handle ping
                connection_state = self.connections.get(connection_id)
                if connection_state:
                    connection_state.last_ping = time.time()

            else:
                # Unknown message type
                logger.warning(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            logger.error(f"Invalid JSON from {connection_id}: {message_text}")
        except Exception as e:
            logger.error(f"Error processing message from {connection_id}: {e}")
            self.stats["total_errors"] += 1

    async def _remove_from_subscriptions(self, connection_id: str):
        """Remove connection from all subscriptions.

        Args:
            connection_id: Connection ID
        """
        # Remove from skill subscriptions
        for skill_id, connection_ids in list(self.skill_subscriptions.items()):
            connection_ids.discard(connection_id)
            if not connection_ids:
                del self.skill_subscriptions[skill_id]

        # Remove from event subscriptions
        for event_type, connection_ids in list(self.event_subscriptions.items()):
            connection_ids.discard(connection_id)
            if not connection_ids:
                del self.event_subscriptions[event_type]

        # Remove from connection subscriptions
        connection_state = self.connections.get(connection_id)
        if connection_state:
            connection_state.subscribed_skills.clear()
            connection_state.subscribed_events.clear()

    # Event handlers

    async def _handle_file_upload(self, data: Dict[str, Any]):
        """Handle file upload event.

        Args:
            data: Event data
        """
        skill_id = data.get("skill_id")
        if skill_id:
            await self.notify_skill_update(skill_id, "file.upload", data)

    async def _handle_file_delete(self, data: Dict[str, Any]):
        """Handle file delete event.

        Args:
            data: Event data
        """
        skill_id = data.get("skill_id")
        if skill_id:
            await self.notify_skill_update(skill_id, "file.delete", data)

    async def _handle_file_move(self, data: Dict[str, Any]):
        """Handle file move event.

        Args:
            data: Event data
        """
        skill_id = data.get("skill_id")
        if skill_id:
            await self.notify_skill_update(skill_id, "file.move", data)

    async def _handle_version_create(self, data: Dict[str, Any]):
        """Handle version create event.

        Args:
            data: Event data
        """
        skill_id = data.get("skill_id")
        if skill_id:
            await self.notify_skill_update(skill_id, "version.create", data)

    async def _handle_version_restore(self, data: Dict[str, Any]):
        """Handle version restore event.

        Args:
            data: Event data
        """
        skill_id = data.get("skill_id")
        if skill_id:
            await self.notify_skill_update(skill_id, "version.restore", data)

    async def _handle_backup_create(self, data: Dict[str, Any]):
        """Handle backup create event.

        Args:
            data: Event data
        """
        await self.notify_event("backup.create", data)

    async def _handle_backup_restore(self, data: Dict[str, Any]):
        """Handle backup restore event.

        Args:
            data: Event data
        """
        await self.notify_event("backup.restore", data)

    async def _handle_cache_invalidate(self, data: Dict[str, Any]):
        """Handle cache invalidate event.

        Args:
            data: Event data
        """
        skill_id = data.get("skill_id")
        if skill_id:
            await self.notify_skill_update(skill_id, "cache.invalidate", data)

    async def cleanup(self):
        """Cleanup WebSocket handler.

        Closes all connections and cancels background tasks.
        """
        # Cancel background tasks
        for task in self.background_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        # Close all connections
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id, "Handler cleanup")

        logger.info("WebSocket handler cleaned up")
