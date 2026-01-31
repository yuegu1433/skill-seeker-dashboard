"""Skill Status WebSocket Handler.

This module provides WebSocket endpoints for real-time skill status updates,
including execution status, import/export progress, and system events.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
import asyncio
import logging
from datetime import datetime
import uuid

from app.skill.event_manager import SkillEventManager, EventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])


class MessageType(Enum):
    """WebSocket message type enumeration."""
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    HEARTBEAT = "heartbeat"
    STATUS_UPDATE = "status_update"
    EVENT = "event"
    ERROR = "error"
    PROGRESS = "progress"
    NOTIFICATION = "notification"


class SubscriptionType(Enum):
    """Subscription type enumeration."""
    SKILL_EXECUTION = "skill_execution"
    SKILL_STATUS = "skill_status"
    IMPORT_EXPORT = "import_export"
    SYSTEM_EVENTS = "system_events"
    VERSION_CHANGES = "version_changes"
    QUALITY_SCORES = "quality_scores"
    ALL = "all"


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message."""

    type: MessageType
    id: str
    timestamp: str
    data: Dict[str, Any]
    subscription: Optional[SubscriptionType] = None
    skill_id: Optional[str] = None
    user_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "id": self.id,
            "timestamp": self.timestamp,
            "data": self.data,
            "subscription": self.subscription.value if self.subscription else None,
            "skill_id": self.skill_id,
            "user_id": self.user_id,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ClientConnection:
    """Represents a client WebSocket connection."""

    connection_id: str
    websocket: WebSocket
    user_id: str
    subscriptions: Set[SubscriptionType]
    skill_ids: Set[str]
    connected_at: datetime
    last_heartbeat: datetime
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connection_id": self.connection_id,
            "user_id": self.user_id,
            "subscriptions": [s.value for s in self.subscriptions],
            "skill_ids": list(self.skill_ids),
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_active": self.is_active,
        }


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, ClientConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.skill_subscriptions: Dict[str, Set[str]] = {}  # skill_id -> connection_ids

    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        connection_id: str,
    ) -> ClientConnection:
        """Accept a new WebSocket connection.

        Args:
            websocket: WebSocket instance
            user_id: User identifier
            connection_id: Unique connection ID

        Returns:
            ClientConnection instance
        """
        await websocket.accept()

        connection = ClientConnection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            subscriptions=set(),
            skill_ids=set(),
            connected_at=datetime.now(),
            last_heartbeat=datetime.now(),
        )

        self.active_connections[connection_id] = connection

        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)

        logger.info(f"WebSocket connected: {connection_id} (user: {user_id})")

        return connection

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection.

        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            user_id = connection.user_id

            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from skill subscriptions
            for skill_id in connection.skill_ids:
                self._unsubscribe_from_skill(connection_id, skill_id)

            # Remove connection
            del self.active_connections[connection_id]

            logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_message(
        self,
        connection_id: str,
        message: WebSocketMessage,
    ):
        """Send a message to a specific connection.

        Args:
            connection_id: Target connection ID
            message: Message to send
        """
        connection = self.active_connections.get(connection_id)
        if connection and connection.is_active:
            try:
                await connection.websocket.send_text(message.to_json())
            except Exception as e:
                logger.error(f"Error sending message to {connection_id}: {e}")
                connection.is_active = False

    async def broadcast_message(
        self,
        message: WebSocketMessage,
        connection_ids: Optional[List[str]] = None,
    ):
        """Broadcast a message to multiple connections.

        Args:
            message: Message to broadcast
            connection_ids: Optional list of connection IDs (broadcast to all if None)
        """
        if connection_ids is None:
            connection_ids = list(self.active_connections.keys())

        await asyncio.gather(
            *[self.send_message(conn_id, message) for conn_id in connection_ids],
            return_exceptions=True,
        )

    async def broadcast_to_subscribers(
        self,
        subscription_type: SubscriptionType,
        message: WebSocketMessage,
        skill_id: Optional[str] = None,
    ):
        """Broadcast a message to subscribers of a specific type.

        Args:
            subscription_type: Subscription type
            message: Message to broadcast
            skill_id: Optional skill ID for skill-specific subscriptions
        """
        # Get all connections with this subscription
        target_connections = [
            conn_id
            for conn_id, connection in self.active_connections.items()
            if subscription_type in connection.subscriptions
        ]

        # Filter by skill_id if specified
        if skill_id:
            target_connections = [
                conn_id for conn_id in target_connections
                if skill_id in self.active_connections[conn_id].skill_ids
            ]

        await self.broadcast_message(message, target_connections)

    def subscribe(
        self,
        connection_id: str,
        subscription_type: SubscriptionType,
        skill_id: Optional[str] = None,
    ):
        """Subscribe a connection to a subscription type.

        Args:
            connection_id: Connection ID
            subscription_type: Subscription type
            skill_id: Optional skill ID
        """
        connection = self.active_connections.get(connection_id)
        if connection:
            connection.subscriptions.add(subscription_type)

            if skill_id:
                connection.skill_ids.add(skill_id)
                self._subscribe_to_skill(connection_id, skill_id)

    def unsubscribe(
        self,
        connection_id: str,
        subscription_type: SubscriptionType,
        skill_id: Optional[str] = None,
    ):
        """Unsubscribe a connection from a subscription type.

        Args:
            connection_id: Connection ID
            subscription_type: Subscription type
            skill_id: Optional skill ID
        """
        connection = self.active_connections.get(connection_id)
        if connection:
            connection.subscriptions.discard(subscription_type)

            if skill_id:
                connection.skill_ids.discard(skill_id)
                self._unsubscribe_from_skill(connection_id, skill_id)

    def _subscribe_to_skill(self, connection_id: str, skill_id: str):
        """Subscribe connection to a skill.

        Args:
            connection_id: Connection ID
            skill_id: Skill ID
        """
        if skill_id not in self.skill_subscriptions:
            self.skill_subscriptions[skill_id] = set()
        self.skill_subscriptions[skill_id].add(connection_id)

    def _unsubscribe_from_skill(self, connection_id: str, skill_id: str):
        """Unsubscribe connection from a skill.

        Args:
            connection_id: Connection ID
            skill_id: Skill ID
        """
        if skill_id in self.skill_subscriptions:
            self.skill_subscriptions[skill_id].discard(connection_id)
            if not self.skill_subscriptions[skill_id]:
                del self.skill_subscriptions[skill_id]

    def update_heartbeat(self, connection_id: str):
        """Update last heartbeat for a connection.

        Args:
            connection_id: Connection ID
        """
        connection = self.active_connections.get(connection_id)
        if connection:
            connection.last_heartbeat = datetime.now()

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "total_connections": len(self.active_connections),
            "active_users": len(self.user_connections),
            "total_subscriptions": sum(
                len(conn.subscriptions)
                for conn in self.active_connections.values()
            ),
            "skill_subscriptions": {
                skill_id: len(conn_ids)
                for skill_id, conn_ids in self.skill_subscriptions.items()
            },
        }


# Global connection manager instance
connection_manager = ConnectionManager()


async def get_event_manager() -> SkillEventManager:
    """Get event manager instance."""
    # In a real application, this would be injected
    from unittest.mock import Mock
    manager = Mock(spec=SkillEventManager)
    manager.subscribe = Mock()
    manager.publish_event = Mock(return_value="event_id")
    return manager


@router.websocket("/skills/status")
async def skill_status_websocket(
    websocket: WebSocket,
    user_id: str = Query(..., description="User ID"),
    token: Optional[str] = Query(None, description="Auth token"),
):
    """WebSocket endpoint for skill status updates.

    Args:
        websocket: WebSocket instance
        user_id: User identifier
        token: Optional authentication token
    """
    connection_id = str(uuid.uuid4())

    try:
        # Connect
        connection = await connection_manager.connect(websocket, user_id, connection_id)

        # Send welcome message
        welcome_message = WebSocketMessage(
            type=MessageType.CONNECT,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={
                "message": "Connected to skill status service",
                "connection_id": connection_id,
                "features": [
                    "skill_execution",
                    "skill_status",
                    "import_export",
                    "system_events",
                    "version_changes",
                    "quality_scores",
                ],
            },
            user_id=user_id,
        )
        await connection_manager.send_message(connection_id, welcome_message)

        # Listen for messages
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Process message
            message_type = MessageType(message_data.get("type"))

            if message_type == MessageType.HEARTBEAT:
                # Update heartbeat
                connection_manager.update_heartbeat(connection_id)

                # Send heartbeat response
                heartbeat_response = WebSocketMessage(
                    type=MessageType.HEARTBEAT,
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    data={"status": "ok"},
                    user_id=user_id,
                )
                await connection_manager.send_message(connection_id, heartbeat_response)

            elif message_type == MessageType.SUBSCRIBE:
                # Subscribe to events
                subscription_type = SubscriptionType(message_data.get("subscription"))
                skill_id = message_data.get("skill_id")

                connection_manager.subscribe(connection_id, subscription_type, skill_id)

                # Send subscription confirmation
                confirm_message = WebSocketMessage(
                    type=MessageType.SUBSCRIBE,
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    data={
                        "subscription": subscription_type.value,
                        "skill_id": skill_id,
                        "status": "subscribed",
                    },
                    subscription=subscription_type,
                    skill_id=skill_id,
                    user_id=user_id,
                )
                await connection_manager.send_message(connection_id, confirm_message)

            elif message_type == MessageType.UNSUBSCRIBE:
                # Unsubscribe from events
                subscription_type = SubscriptionType(message_data.get("subscription"))
                skill_id = message_data.get("skill_id")

                connection_manager.unsubscribe(connection_id, subscription_type, skill_id)

                # Send unsubscription confirmation
                confirm_message = WebSocketMessage(
                    type=MessageType.UNSUBSCRIBE,
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    data={
                        "subscription": subscription_type.value,
                        "skill_id": skill_id,
                        "status": "unsubscribed",
                    },
                    subscription=subscription_type,
                    skill_id=skill_id,
                    user_id=user_id,
                )
                await connection_manager.send_message(connection_id, confirm_message)

            else:
                # Unknown message type
                error_message = WebSocketMessage(
                    type=MessageType.ERROR,
                    id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    data={
                        "error": "Unknown message type",
                        "message_type": message_type.value,
                    },
                    user_id=user_id,
                )
                await connection_manager.send_message(connection_id, error_message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        error_message = WebSocketMessage(
            type=MessageType.ERROR,
            id=str(uuid.uuid4()),
            timestamp=datetime.now().isoformat(),
            data={"error": str(e)},
            user_id=user_id,
        )
        try:
            await connection_manager.send_message(connection_id, error_message)
        except:
            pass
    finally:
        # Cleanup
        connection_manager.disconnect(connection_id)


async def broadcast_skill_execution(
    skill_id: str,
    status: str,
    execution_time: Optional[float] = None,
    error_message: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Broadcast skill execution status.

    Args:
        skill_id: Skill identifier
        status: Execution status
        execution_time: Optional execution time
        error_message: Optional error message
        user_id: Optional user ID
    """
    message = WebSocketMessage(
        type=MessageType.STATUS_UPDATE,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "skill_id": skill_id,
            "status": status,
            "execution_time": execution_time,
            "error_message": error_message,
        },
        subscription=SubscriptionType.SKILL_EXECUTION,
        skill_id=skill_id,
        user_id=user_id,
    )

    await connection_manager.broadcast_to_subscribers(
        SubscriptionType.SKILL_EXECUTION,
        message,
        skill_id,
    )


async def broadcast_import_export_progress(
    operation_id: str,
    operation_type: str,
    status: str,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Broadcast import/export progress.

    Args:
        operation_id: Operation ID
        operation_type: Type of operation (import/export)
        status: Current status
        progress: Optional progress percentage
        message: Optional status message
        user_id: Optional user ID
    """
    message = WebSocketMessage(
        type=MessageType.PROGRESS,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "operation_id": operation_id,
            "operation_type": operation_type,
            "status": status,
            "progress": progress,
            "message": message,
        },
        subscription=SubscriptionType.IMPORT_EXPORT,
        user_id=user_id,
    )

    await connection_manager.broadcast_to_subscribers(
        SubscriptionType.IMPORT_EXPORT,
        message,
    )


async def broadcast_system_event(
    event_type: str,
    data: Dict[str, Any],
    user_id: Optional[str] = None,
):
    """Broadcast system event.

    Args:
        event_type: Type of event
        data: Event data
        user_id: Optional user ID
    """
    message = WebSocketMessage(
        type=MessageType.EVENT,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "event_type": event_type,
            **data,
        },
        subscription=SubscriptionType.SYSTEM_EVENTS,
        user_id=user_id,
    )

    await connection_manager.broadcast_to_subscribers(
        SubscriptionType.SYSTEM_EVENTS,
        message,
    )


async def broadcast_version_change(
    skill_id: str,
    version: str,
    change_type: str,
    user_id: Optional[str] = None,
):
    """Broadcast version change.

    Args:
        skill_id: Skill identifier
        version: Version string
        change_type: Type of change (created, updated, tagged, etc.)
        user_id: Optional user ID
    """
    message = WebSocketMessage(
        type=MessageType.EVENT,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "skill_id": skill_id,
            "version": version,
            "change_type": change_type,
        },
        subscription=SubscriptionType.VERSION_CHANGES,
        skill_id=skill_id,
        user_id=user_id,
    )

    await connection_manager.broadcast_to_subscribers(
        SubscriptionType.VERSION_CHANGES,
        message,
        skill_id,
    )


async def broadcast_quality_score_update(
    skill_id: str,
    quality_score: float,
    previous_score: Optional[float] = None,
    user_id: Optional[str] = None,
):
    """Broadcast quality score update.

    Args:
        skill_id: Skill identifier
        quality_score: New quality score
        previous_score: Optional previous score
        user_id: Optional user ID
    """
    message = WebSocketMessage(
        type=MessageType.STATUS_UPDATE,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data={
            "skill_id": skill_id,
            "quality_score": quality_score,
            "previous_score": previous_score,
        },
        subscription=SubscriptionType.QUALITY_SCORES,
        skill_id=skill_id,
        user_id=user_id,
    )

    await connection_manager.broadcast_to_subscribers(
        SubscriptionType.QUALITY_SCORES,
        message,
        skill_id,
    )


@router.get("/connections/stats")
async def get_connection_stats():
    """Get WebSocket connection statistics.

    Returns:
        Connection statistics
    """
    stats = connection_manager.get_connection_stats()
    return JSONResponse(stats)


@router.get("/connections")
async def list_connections():
    """List active WebSocket connections.

    Returns:
        List of connections
    """
    connections = [
        conn.to_dict()
        for conn in connection_manager.active_connections.values()
    ]
    return JSONResponse({"connections": connections})


@router.post("/broadcast")
async def broadcast_message(
    subscription_type: SubscriptionType,
    message_type: MessageType,
    data: Dict[str, Any],
    skill_id: Optional[str] = None,
):
    """Broadcast a message to subscribers.

    Args:
        subscription_type: Subscription type
        message_type: Message type
        data: Message data
        skill_id: Optional skill ID

    Returns:
        Success response
    """
    message = WebSocketMessage(
        type=message_type,
        id=str(uuid.uuid4()),
        timestamp=datetime.now().isoformat(),
        data=data,
        subscription=subscription_type,
        skill_id=skill_id,
    )

    await connection_manager.broadcast_to_subscribers(
        subscription_type,
        message,
        skill_id,
    )

    return {"success": True, "message": "Broadcast sent"}


# Background task for heartbeat monitoring
async def monitor_heartbeats():
    """Monitor WebSocket connection heartbeats."""
    while True:
        await asyncio.sleep(30)  # Check every 30 seconds

        current_time = datetime.now()
        timeout = 120  # 2 minutes timeout

        # Check for stale connections
        stale_connections = [
            conn_id
            for conn_id, connection in connection_manager.active_connections.items()
            if (current_time - connection.last_heartbeat).total_seconds() > timeout
        ]

        # Close stale connections
        for conn_id in stale_connections:
            logger.warning(f"Closing stale connection: {conn_id}")
            connection_manager.disconnect(conn_id)


# Start heartbeat monitor
asyncio.create_task(monitor_heartbeats())
