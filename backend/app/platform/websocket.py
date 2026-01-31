"""WebSocket handler for real-time platform deployment status updates.

This module provides WebSocket handlers for real-time communication
of deployment status, health updates, and platform events.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import UUID, uuid4
from fastapi import WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

from .manager import PlatformManager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket connection manager."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        client_id: str,
        subscriptions: Optional[List[str]] = None
    ):
        """Accept WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = {
            "connected_at": datetime.utcnow(),
            "subscriptions": subscriptions or [],
            "last_ping": datetime.utcnow()
        }
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        """Remove WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        client_id: str
    ):
        """Send message to specific client."""
        if client_id not in self.active_connections:
            return

        websocket = self.active_connections[client_id]
        if websocket.application_state == WebSocketState.CONNECTED:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {str(e)}")
                self.disconnect(client_id)

    async def broadcast(
        self,
        message: Dict[str, Any],
        exclude_client: Optional[str] = None,
        filter_func: Optional[Callable[[str, Dict[str, Any]], bool]] = None
    ):
        """Broadcast message to all or filtered connections."""
        disconnected_clients = []

        for client_id, websocket in self.active_connections.items():
            if exclude_client and client_id == exclude_client:
                continue

            # Apply filter if provided
            if filter_func and not filter_func(client_id, message):
                continue

            if websocket.application_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send broadcast to {client_id}: {str(e)}")
                    disconnected_clients.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

    async def send_ping(self, client_id: str):
        """Send ping to client."""
        await self.send_personal_message({
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }, client_id)

    def get_active_connections_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)


class EventBroadcaster:
    """Event broadcaster for WebSocket messages."""

    def __init__(self, manager: PlatformManager):
        """Initialize event broadcaster."""
        self.manager = manager
        self.connection_manager = ConnectionManager()
        self.subscriptions: Dict[str, Set[str]] = {}  # event_type -> set of client_ids

    def subscribe(self, client_id: str, event_types: List[str]):
        """Subscribe client to event types."""
        for event_type in event_types:
            if event_type not in self.subscriptions:
                self.subscriptions[event_type] = set()
            self.subscriptions[event_type].add(client_id)

    def unsubscribe(self, client_id: str, event_types: Optional[List[str]] = None):
        """Unsubscribe client from event types."""
        if event_types is None:
            # Unsubscribe from all
            for event_type, clients in self.subscriptions.items():
                clients.discard(client_id)
        else:
            for event_type in event_types:
                if event_type in self.subscriptions:
                    self.subscriptions[event_type].discard(client_id)

    async def broadcast_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        exclude_client: Optional[str] = None
    ):
        """Broadcast event to subscribed clients."""
        message = {
            "type": "event",
            "event_type": event_type,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # Get subscribed clients
        subscribed_clients = self.subscriptions.get(event_type, set())

        # Apply filter to send only to subscribed clients
        def filter_func(client_id: str, msg: Dict[str, Any]) -> bool:
            return client_id in subscribed_clients

        await self.connection_manager.broadcast(
            message,
            exclude_client=exclude_client,
            filter_func=filter_func
        )

    async def handle_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        subscriptions: Optional[List[str]] = None
    ):
        """Handle WebSocket connection."""
        await self.connection_manager.connect(websocket, client_id, subscriptions)

        # Subscribe to events
        if subscriptions:
            self.subscribe(client_id, subscriptions)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                await self._handle_client_message(client_id, message)

        except WebSocketDisconnect:
            self.connection_manager.disconnect(client_id)
            self.unsubscribe(client_id)
        except Exception as e:
            logger.error(f"WebSocket error for {client_id}: {str(e)}")
            self.connection_manager.disconnect(client_id)
            self.unsubscribe(client_id)

    async def _handle_client_message(self, client_id: str, message: Dict[str, Any]):
        """Handle message from client."""
        message_type = message.get("type")

        if message_type == "ping":
            await self.connection_manager.send_ping(client_id)
        elif message_type == "subscribe":
            event_types = message.get("event_types", [])
            self.subscribe(client_id, event_types)
            await self.connection_manager.send_personal_message({
                "type": "subscribed",
                "event_types": event_types,
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)
        elif message_type == "unsubscribe":
            event_types = message.get("event_types")
            self.unsubscribe(client_id, event_types)
            await self.connection_manager.send_personal_message({
                "type": "unsubscribed",
                "event_types": event_types,
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)
        elif message_type == "get_status":
            # Send current status
            status = await self._get_current_status()
            await self.connection_manager.send_personal_message({
                "type": "status",
                "data": status,
                "timestamp": datetime.utcnow().isoformat()
            }, client_id)

    async def _get_current_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            # Get platform summary
            summary = await self.manager.get_platform_summary()
            return summary
        except Exception as e:
            logger.error(f"Failed to get current status: {str(e)}")
            return {"error": str(e)}


# Global event broadcaster instance
_event_broadcaster: Optional[EventBroadcaster] = None


async def get_event_broadcaster() -> EventBroadcaster:
    """Get event broadcaster instance."""
    global _event_broadcaster
    if _event_broadcaster is None:
        manager = PlatformManager()
        await manager.initialize()
        _event_broadcaster = EventBroadcaster(manager)
    return _event_broadcaster


async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    subscriptions: Optional[str] = Query(None, description="Comma-separated event subscriptions"),
    broadcaster: EventBroadcaster = Depends(get_event_broadcaster)
):
    """WebSocket endpoint for real-time platform updates."""
    # Parse subscriptions
    event_subscriptions = []
    if subscriptions:
        event_subscriptions = subscriptions.split(",")

    # Handle connection
    await broadcaster.handle_connection(websocket, client_id, event_subscriptions)


async def websocket_deployment_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    broadcaster: EventBroadcaster = Depends(get_event_broadcaster)
):
    """WebSocket endpoint specifically for deployment updates."""
    subscriptions = ["deployment_status", "deployment_progress", "deployment_complete"]
    await broadcaster.handle_connection(websocket, client_id, subscriptions)


async def websocket_health_endpoint(
    websocket: WebSocket,
    client_id: str = Query(..., description="Unique client identifier"),
    broadcaster: EventBroadcaster = Depends(get_event_broadcaster)
):
    """WebSocket endpoint specifically for health updates."""
    subscriptions = ["platform_health", "alert_triggered", "alert_resolved"]
    await broadcaster.handle_connection(websocket, client_id, subscriptions)


# Event handlers for broadcasting

async def broadcast_deployment_update(deployment_data: Dict[str, Any]):
    """Broadcast deployment status update."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "deployment_status",
        deployment_data
    )


async def broadcast_deployment_progress(deployment_id: str, progress: Dict[str, Any]):
    """Broadcast deployment progress update."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "deployment_progress",
        {
            "deployment_id": deployment_id,
            "progress": progress,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def broadcast_deployment_complete(deployment_data: Dict[str, Any]):
    """Broadcast deployment completion."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "deployment_complete",
        deployment_data
    )


async def broadcast_platform_health(platform_id: str, health_data: Dict[str, Any]):
    """Broadcast platform health update."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "platform_health",
        {
            "platform_id": platform_id,
            "health_data": health_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def broadcast_alert(alert_data: Dict[str, Any]):
    """Broadcast alert."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "alert_triggered",
        alert_data
    )


async def broadcast_alert_resolved(alert_data: Dict[str, Any]):
    """Broadcast alert resolution."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "alert_resolved",
        alert_data
    )


async def broadcast_platform_event(event_data: Dict[str, Any]):
    """Broadcast general platform event."""
    broadcaster = await get_event_broadcaster()
    await broadcaster.broadcast_event(
        "platform_event",
        event_data
    )


# WebSocket message types and handlers

class WebSocketMessageType:
    """WebSocket message types."""
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    GET_STATUS = "get_status"
    EVENT = "event"
    ERROR = "error"


class WebSocketEventType:
    """WebSocket event types."""
    DEPLOYMENT_STATUS = "deployment_status"
    DEPLOYMENT_PROGRESS = "deployment_progress"
    DEPLOYMENT_COMPLETE = "deployment_complete"
    PLATFORM_HEALTH = "platform_health"
    ALERT_TRIGGERED = "alert_triggered"
    ALERT_RESOLVED = "alert_resolved"
    PLATFORM_EVENT = "platform_event"


# Utility functions

def create_websocket_url(base_url: str, endpoint: str, client_id: str, subscriptions: Optional[List[str]] = None) -> str:
    """Create WebSocket URL with parameters."""
    url = f"{base_url}/{endpoint}?client_id={client_id}"
    if subscriptions:
        url += f"&subscriptions={','.join(subscriptions)}"
    return url


def create_personal_message(message_type: str, data: Any) -> Dict[str, Any]:
    """Create personal WebSocket message."""
    return {
        "type": message_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_event_message(event_type: str, data: Any) -> Dict[str, Any]:
    """Create event WebSocket message."""
    return {
        "type": "event",
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }


def create_error_message(error: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create error WebSocket message."""
    return {
        "type": "error",
        "error": error,
        "details": details,
        "timestamp": datetime.utcnow().isoformat()
    }


# Client-side JavaScript examples

WEBSOCKET_CLIENT_EXAMPLE = """
// JavaScript WebSocket client example
class PlatformWebSocketClient {
    constructor(baseUrl, clientId, subscriptions = []) {
        this.baseUrl = baseUrl;
        this.clientId = clientId;
        this.subscriptions = subscriptions;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        const url = `${this.baseUrl}/ws?client_id=${this.clientId}&subscriptions=${this.subscriptions.join(',')}`;
        this.ws = new WebSocket(url);

        this.ws.onopen = (event) => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };

        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };

        this.ws.onclose = (event) => {
            console.log('WebSocket disconnected');
            this.handleReconnect();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(message) {
        switch (message.type) {
            case 'event':
                this.handleEvent(message);
                break;
            case 'error':
                console.error('WebSocket error:', message.error);
                break;
            case 'ping':
                this.send({ type: 'pong' });
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    handleEvent(event) {
        switch (event.event_type) {
            case 'deployment_status':
                console.log('Deployment status:', event.data);
                this.onDeploymentStatus && this.onDeploymentStatus(event.data);
                break;
            case 'platform_health':
                console.log('Platform health:', event.data);
                this.onPlatformHealth && this.onPlatformHealth(event.data);
                break;
            case 'alert_triggered':
                console.log('Alert triggered:', event.data);
                this.onAlertTriggered && this.onAlertTriggered(event.data);
                break;
            default:
                console.log('Unknown event type:', event.event_type);
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff
            setTimeout(() => {
                console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
                this.connect();
            }, delay);
        }
    }

    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
        }
    }

    subscribe(eventTypes) {
        this.send({
            type: 'subscribe',
            event_types: eventTypes
        });
    }

    unsubscribe(eventTypes) {
        this.send({
            type: 'unsubscribe',
            event_types: eventTypes
        });
    }

    getStatus() {
        this.send({ type: 'get_status' });
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
        }
    }
}

// Usage example
const client = new PlatformWebSocketClient(
    'ws://localhost:8000',
    'client-123',
    ['deployment_status', 'platform_health']
);

client.onDeploymentStatus = (data) => {
    console.log('Deployment updated:', data);
    // Update UI with deployment status
};

client.onPlatformHealth = (data) => {
    console.log('Platform health changed:', data);
    // Update UI with health status
};

client.connect();
"""

if __name__ == "__main__":
    # Example usage
    print("WebSocket client example:")
    print(WEBSOCKET_CLIENT_EXAMPLE)