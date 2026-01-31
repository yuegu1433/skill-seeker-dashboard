"""File Management WebSocket.

This module provides WebSocket endpoints for real-time file status updates,
collaborative editing notifications, and file operation progress tracking.
"""

import json
import logging
from typing import Dict, Set, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.websockets import WebSocketState

# Import managers and services
from app.file.manager import FileManager
from app.file.services.upload_service import UploadService
from app.file.services.download_service import DownloadService
from app.file.batch_processor import BatchProcessor
from app.file.event_manager import FileOperationEvent

logger = logging.getLogger(__name__)

# WebSocket connection manager
class FileWebSocketManager:
    """Manages WebSocket connections for file operations."""

    def __init__(self):
        # Store active connections by file_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        # Store user subscriptions
        self.user_subscriptions: Dict[str, Set[str]] = {}  # user_id -> file_ids

    async def connect(
        self,
        websocket: WebSocket,
        file_id: Optional[str] = None,
        user_id: Optional[str] = None,
        subscribe_updates: bool = True,
    ):
        """Accept a WebSocket connection.

        Args:
            websocket: WebSocket connection
            file_id: Optional file ID to subscribe to
            user_id: Optional user ID for user-specific subscriptions
            subscribe_updates: Whether to subscribe to file updates
        """
        await websocket.accept()

        connection_id = str(uuid4())
        self.connection_metadata[websocket] = {
            "connection_id": connection_id,
            "file_id": file_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
        }

        if subscribe_updates and file_id:
            if file_id not in self.active_connections:
                self.active_connections[file_id] = set()
            self.active_connections[file_id].add(websocket)

        if user_id:
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            self.user_subscriptions[user_id].add(file_id)

        logger.info(f"WebSocket connected: {connection_id} (file: {file_id}, user: {user_id})")

        # Send welcome message
        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "connection_id": connection_id,
                "message": "Connected to file management WebSocket",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket.

        Args:
            websocket: WebSocket connection
        """
        metadata = self.connection_metadata.get(websocket)
        if not metadata:
            return

        connection_id = metadata["connection_id"]
        file_id = metadata.get("file_id")
        user_id = metadata.get("user_id")

        # Remove from file connections
        if file_id and file_id in self.active_connections:
            self.active_connections[file_id].discard(websocket)
            if not self.active_connections[file_id]:
                del self.active_connections[file_id]

        # Remove from user subscriptions
        if user_id and user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(file_id)
            if not self.user_subscriptions[user_id]:
                del self.user_subscriptions[user_id]

        # Remove metadata
        del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket.

        Args:
            websocket: WebSocket connection
            message: Message to send
        """
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_text(json.dumps(message))

    async def broadcast_to_file(self, file_id: str, message: Dict[str, Any], exclude: Optional[WebSocket] = None):
        """Broadcast a message to all connections for a specific file.

        Args:
            file_id: File ID
            message: Message to broadcast
            exclude: Optional WebSocket to exclude
        """
        if file_id not in self.active_connections:
            return

        message["timestamp"] = datetime.utcnow().isoformat()
        message["file_id"] = file_id

        disconnected = []
        for connection in self.active_connections[file_id]:
            if connection != exclude and connection.client_state == WebSocketState.CONNECTED:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send message to WebSocket: {e}")
                    disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a specific user.

        Args:
            user_id: User ID
            message: Message to broadcast
        """
        if user_id not in self.user_subscriptions:
            return

        message["timestamp"] = datetime.utcnow().isoformat()
        message["user_id"] = user_id

        disconnected = []
        for file_id in self.user_subscriptions[user_id]:
            if file_id in self.active_connections:
                for connection in self.active_connections[file_id]:
                    metadata = self.connection_metadata.get(connection, {})
                    if metadata.get("user_id") == user_id and connection.client_state == WebSocketState.CONNECTED:
                        try:
                            await connection.send_text(json.dumps(message))
                        except Exception as e:
                            logger.error(f"Failed to send message to WebSocket: {e}")
                            disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all active connections.

        Args:
            message: Message to broadcast
        """
        message["timestamp"] = datetime.utcnow().isoformat()

        disconnected = []
        for connections in self.active_connections.values():
            for connection in connections:
                if connection.client_state == WebSocketState.CONNECTED:
                    try:
                        await connection.send_text(json.dumps(message))
                    except Exception as e:
                        logger.error(f"Failed to send message to WebSocket: {e}")
                        disconnected.append(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

    def get_connection_count(self, file_id: Optional[str] = None) -> int:
        """Get the number of active connections.

        Args:
            file_id: Optional file ID to get count for

        Returns:
            Number of active connections
        """
        if file_id:
            return len(self.active_connections.get(file_id, set()))
        return sum(len(connections) for connections in self.active_connections.values())


# Global WebSocket manager instance
websocket_manager = FileWebSocketManager()

# Create router
router = APIRouter()


# Dependency injection
async def get_file_manager():
    """Get FileManager instance (placeholder for actual DI)."""
    # In real implementation, this would get the actual instance
    return None


async def get_upload_service():
    """Get UploadService instance (placeholder for actual DI)."""
    # In real implementation, this would get the actual instance
    return None


async def get_download_service():
    """Get DownloadService instance (placeholder for actual DI)."""
    # In real implementation, this would get the actual instance
    return None


async def get_batch_processor():
    """Get BatchProcessor instance (placeholder for actual DI)."""
    # In real implementation, this would get the actual instance
    return None


# Main WebSocket endpoint
@router.websocket("/ws/files")
async def file_websocket(
    websocket: WebSocket,
    file_id: Optional[str] = Query(None, description="File ID to subscribe to"),
    user_id: Optional[str] = Query(None, description="User ID for personalized updates"),
    subscribe_updates: bool = Query(True, description="Subscribe to file updates"),
):
    """WebSocket endpoint for file management real-time updates.

    Args:
        websocket: WebSocket connection
        file_id: Optional file ID to subscribe to
        user_id: Optional user ID
        subscribe_updates: Whether to subscribe to updates
    """
    await websocket_manager.connect(
        websocket=websocket,
        file_id=file_id,
        user_id=user_id,
        subscribe_updates=subscribe_updates,
    )

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "ping":
                # Respond to ping
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            elif message_type == "subscribe":
                # Subscribe to additional file updates
                new_file_id = message.get("file_id")
                if new_file_id:
                    if new_file_id not in websocket_manager.active_connections:
                        websocket_manager.active_connections[new_file_id] = set()
                    websocket_manager.active_connections[new_file_id].add(websocket)

                    # Update metadata
                    metadata = websocket_manager.connection_metadata[websocket]
                    metadata["file_id"] = new_file_id

                    await websocket_manager.send_personal_message(
                        websocket,
                        {
                            "type": "subscription_updated",
                            "file_id": new_file_id,
                            "message": f"Subscribed to file {new_file_id}",
                        }
                    )

            elif message_type == "unsubscribe":
                # Unsubscribe from file updates
                file_id_to_remove = message.get("file_id")
                if file_id_to_remove in websocket_manager.active_connections:
                    websocket_manager.active_connections[file_id_to_remove].discard(websocket)

                    await websocket_manager.send_personal_message(
                        websocket,
                        {
                            "type": "subscription_removed",
                            "file_id": file_id_to_remove,
                            "message": f"Unsubscribed from file {file_id_to_remove}",
                        }
                    )

            elif message_type == "get_status":
                # Get current connection status
                metadata = websocket_manager.connection_metadata.get(websocket, {})
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "status",
                        "connection_id": metadata.get("connection_id"),
                        "file_id": metadata.get("file_id"),
                        "user_id": metadata.get("user_id"),
                        "connected_at": metadata.get("connected_at").isoformat() if metadata.get("connected_at") else None,
                        "active_connections": websocket_manager.get_connection_count(),
                    }
                )

            else:
                # Unknown message type
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "error",
                        "message": f"Unknown message type: {message_type}",
                    }
                )

            # Update last activity
            if websocket in websocket_manager.connection_metadata:
                websocket_manager.connection_metadata[websocket]["last_activity"] = datetime.utcnow()

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

    except json.JSONDecodeError:
        await websocket_manager.send_personal_message(
            websocket,
            {
                "type": "error",
                "message": "Invalid JSON message",
            }
        )

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# File Operation WebSocket
@router.websocket("/ws/files/{file_id}/operations")
async def file_operations_websocket(
    websocket: WebSocket,
    file_id: str,
    operation_id: Optional[str] = Query(None, description="Specific operation ID"),
):
    """WebSocket endpoint for file operation progress updates.

    Args:
        websocket: WebSocket connection
        file_id: File ID
        operation_id: Optional specific operation ID
    """
    await websocket_manager.connect(
        websocket=websocket,
        file_id=file_id,
        subscribe_updates=True,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "subscribe_operations":
                # Subscribe to operation updates
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "operation_subscription",
                        "file_id": file_id,
                        "operation_id": operation_id,
                        "message": "Subscribed to operation updates",
                    }
                )

            elif message_type == "get_operation_status":
                # Get status of specific operation
                op_id = message.get("operation_id")
                if op_id:
                    # In real implementation, would check actual operation status
                    await websocket_manager.send_personal_message(
                        websocket,
                        {
                            "type": "operation_status",
                            "operation_id": op_id,
                            "status": "running",
                            "progress": 50,
                            "message": "Operation in progress",
                        }
                    )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"File operations WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# Upload Progress WebSocket
@router.websocket("/ws/upload/{upload_id}")
async def upload_progress_websocket(
    websocket: WebSocket,
    upload_id: str,
):
    """WebSocket endpoint for upload progress tracking.

    Args:
        websocket: WebSocket connection
        upload_id: Upload ID
    """
    await websocket_manager.connect(
        websocket=websocket,
        file_id=f"upload_{upload_id}",
        subscribe_updates=True,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "get_progress":
                # In real implementation, would get actual upload progress
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "upload_progress",
                        "upload_id": upload_id,
                        "status": "uploading",
                        "progress": 50,
                        "uploaded_bytes": 512000,
                        "total_bytes": 1024000,
                        "speed": 1024.0,
                        "eta": 500,
                    }
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Upload progress WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# Download Progress WebSocket
@router.websocket("/ws/download/{download_id}")
async def download_progress_websocket(
    websocket: WebSocket,
    download_id: str,
):
    """WebSocket endpoint for download progress tracking.

    Args:
        websocket: WebSocket connection
        download_id: Download ID
    """
    await websocket_manager.connect(
        websocket=websocket,
        file_id=f"download_{download_id}",
        subscribe_updates=True,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "get_progress":
                # In real implementation, would get actual download progress
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "download_progress",
                        "download_id": download_id,
                        "status": "downloading",
                        "progress": 75,
                        "downloaded_bytes": 768000,
                        "total_bytes": 1024000,
                        "speed": 2048.0,
                        "eta": 250,
                    }
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Download progress WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# Batch Operation WebSocket
@router.websocket("/ws/batch/{job_id}")
async def batch_operation_websocket(
    websocket: WebSocket,
    job_id: str,
):
    """WebSocket endpoint for batch operation progress.

    Args:
        websocket: WebSocket connection
        job_id: Batch job ID
    """
    await websocket_manager.connect(
        websocket=websocket,
        file_id=f"batch_{job_id}",
        subscribe_updates=True,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "get_batch_status":
                # In real implementation, would get actual batch status
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "batch_status",
                        "job_id": job_id,
                        "status": "running",
                        "progress": 60,
                        "total_files": 100,
                        "processed_files": 60,
                        "successful_files": 58,
                        "failed_files": 2,
                        "current_operation": "Processing file 60 of 100",
                    }
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

    except Exception as e:
        logger.error(f"Batch operation WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# Collaborative Editing WebSocket
@router.websocket("/ws/editor/{session_id}")
async def collaborative_editing_websocket(
    websocket: WebSocket,
    session_id: str,
    user_id: Optional[str] = Query(None, description="User ID for the editor session"),
):
    """WebSocket endpoint for collaborative editing.

    Args:
        websocket: WebSocket connection
        session_id: Editor session ID
        user_id: Optional user ID
    """
    await websocket_manager.connect(
        websocket=websocket,
        file_id=f"editor_{session_id}",
        user_id=user_id,
        subscribe_updates=True,
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "join_session":
                # User joins the editing session
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "session_joined",
                        "session_id": session_id,
                        "user_id": user_id,
                        "message": "Joined collaborative editing session",
                    }
                )

                # Broadcast to other users
                await websocket_manager.broadcast_to_file(
                    file_id=f"editor_{session_id}",
                    message={
                        "type": "user_joined",
                        "session_id": session_id,
                        "user_id": user_id,
                        "message": f"User {user_id} joined the session",
                    },
                    exclude=websocket,
                )

            elif message_type == "edit_operation":
                # Broadcast edit operation to other users
                await websocket_manager.broadcast_to_file(
                    file_id=f"editor_{session_id}",
                    message={
                        "type": "edit_operation",
                        "session_id": session_id,
                        "user_id": user_id,
                        "operation": message.get("operation"),
                        "position": message.get("position"),
                        "content": message.get("content"),
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    exclude=websocket,
                )

            elif message_type == "cursor_position":
                # Broadcast cursor position to other users
                await websocket_manager.broadcast_to_file(
                    file_id=f"editor_{session_id}",
                    message={
                        "type": "cursor_position",
                        "session_id": session_id,
                        "user_id": user_id,
                        "position": message.get("position"),
                        "selection": message.get("selection"),
                    },
                    exclude=websocket,
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

        # Notify other users that user left
        await websocket_manager.broadcast_to_file(
            file_id=f"editor_{session_id}",
            message={
                "type": "user_left",
                "session_id": session_id,
                "user_id": user_id,
                "message": f"User {user_id} left the session",
            }
        )

    except Exception as e:
        logger.error(f"Collaborative editing WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


# Event Broadcasting Functions
async def broadcast_file_created(file_id: str, file_info: Dict[str, Any]):
    """Broadcast file creation event.

    Args:
        file_id: File ID
        file_info: File information
    """
    await websocket_manager.broadcast_to_file(
        file_id=file_id,
        message={
            "type": "file_created",
            "file_id": file_id,
            "file_info": file_info,
        }
    )


async def broadcast_file_updated(file_id: str, update_info: Dict[str, Any]):
    """Broadcast file update event.

    Args:
        file_id: File ID
        update_info: Update information
    """
    await websocket_manager.broadcast_to_file(
        file_id=file_id,
        message={
            "type": "file_updated",
            "file_id": file_id,
            "update_info": update_info,
        }
    )


async def broadcast_file_deleted(file_id: str):
    """Broadcast file deletion event.

    Args:
        file_id: File ID
    """
    await websocket_manager.broadcast_to_file(
        file_id=file_id,
        message={
            "type": "file_deleted",
            "file_id": file_id,
        }
    )


async def broadcast_upload_progress(upload_id: str, progress: Dict[str, Any]):
    """Broadcast upload progress update.

    Args:
        upload_id: Upload ID
        progress: Progress information
    """
    await websocket_manager.broadcast_to_file(
        file_id=f"upload_{upload_id}",
        message={
            "type": "upload_progress",
            "upload_id": upload_id,
            **progress,
        }
    )


async def broadcast_download_progress(download_id: str, progress: Dict[str, Any]):
    """Broadcast download progress update.

    Args:
        download_id: Download ID
        progress: Progress information
    """
    await websocket_manager.broadcast_to_file(
        file_id=f"download_{download_id}",
        message={
            "type": "download_progress",
            "download_id": download_id,
            **progress,
        }
    )


async def broadcast_batch_progress(job_id: str, progress: Dict[str, Any]):
    """Broadcast batch operation progress.

    Args:
        job_id: Batch job ID
        progress: Progress information
    """
    await websocket_manager.broadcast_to_file(
        file_id=f"batch_{job_id}",
        message={
            "type": "batch_progress",
            "job_id": job_id,
            **progress,
        }
    )


# Health Check Endpoint
@router.get("/ws/health")
async def websocket_health_check():
    """Check WebSocket service health.

    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "active_connections": websocket_manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


# Statistics Endpoint
@router.get("/ws/stats")
async def websocket_statistics():
    """Get WebSocket statistics.

    Returns:
        WebSocket statistics
    """
    return {
        "total_connections": websocket_manager.get_connection_count(),
        "file_connections": {
            file_id: len(connections)
            for file_id, connections in websocket_manager.active_connections.items()
        },
        "user_subscriptions": {
            user_id: list(file_ids)
            for user_id, file_ids in websocket_manager.user_subscriptions.items()
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
