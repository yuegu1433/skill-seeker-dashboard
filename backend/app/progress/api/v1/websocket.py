"""WebSocket API routes v1.

This module provides WebSocket endpoints for real-time progress tracking,
including message routing, connection management, and status推送.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Path
from typing import Any, Dict, List, Optional
import json
import logging

from ...schemas.websocket_messages import WebSocketMessage
from ...websocket import websocket_manager
from ...websocket_handler import ProgressWebSocketHandler
from ...log_stream import log_stream_service
from ...notification_manager import notification_manager
from ...visualization_manager import visualization_manager

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize handler
progress_handler = ProgressWebSocketHandler()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    task_id: Optional[str] = Query(None, description="Task ID to subscribe to"),
    user_id: Optional[str] = Query(None, description="User ID"),
    stream_type: Optional[str] = Query("all", description="Stream type: progress/logs/notifications/all"),
):
    """WebSocket endpoint for real-time updates.

    This endpoint provides real-time WebSocket connections for:
    - Progress updates
    - Log streaming
    - Notifications
    - Status changes

    Args:
        websocket: WebSocket connection
        task_id: Task ID to subscribe to (optional)
        user_id: User ID (optional)
        stream_type: Type of streams to subscribe to (default: all)
    """
    connection_id = None
    try:
        # Extract connection parameters from query params
        task_id = task_id or websocket.query_params.get("task_id")
        user_id = user_id or websocket.query_params.get("user_id")
        stream_type = stream_type or websocket.query_params.get("stream_type", "all")

        logger.info(
            f"WebSocket connection attempt: task_id={task_id}, user_id={user_id}, stream_type={stream_type}"
        )

        # Establish connection
        connection_id = await websocket_manager.connect(
            websocket,
            task_id=task_id,
            user_id=user_id,
        )

        if not connection_id:
            await websocket.close(code=1008, reason="Connection rejected")
            return

        logger.info(f"WebSocket connected: {connection_id}")

        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection",
                    "connection_id": connection_id,
                    "status": "connected",
                    "message": "WebSocket connection established",
                    "timestamp": websocket_manager._get_timestamp(),
                }
            )
        )

        # Handle different stream types
        if stream_type in ["progress", "all"]:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "subscription",
                        "stream_type": "progress",
                        "message": "Subscribed to progress updates",
                        "timestamp": websocket_manager._get_timestamp(),
                    }
                )
            )

        if stream_type in ["logs", "all"]:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "subscription",
                        "stream_type": "logs",
                        "message": "Subscribed to log updates",
                        "timestamp": websocket_manager._get_timestamp(),
                    }
                )
            )

        if stream_type in ["notifications", "all"]:
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "subscription",
                        "stream_type": "notifications",
                        "message": "Subscribed to notifications",
                        "timestamp": websocket_manager._get_timestamp(),
                    }
                )
            )

        # Main message loop
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                msg_type = message.get("type")

                if msg_type == "ping":
                    # Handle ping/pong
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "pong",
                                "timestamp": websocket_manager._get_timestamp(),
                            }
                        )
                    )

                elif msg_type == "subscribe":
                    # Handle subscription changes
                    subscription_task_id = message.get("task_id")
                    subscription_user_id = message.get("user_id")
                    await websocket_manager.subscribe(
                        connection_id,
                        task_id=subscription_task_id,
                        user_id=subscription_user_id,
                    )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "subscribed",
                                "task_id": subscription_task_id,
                                "user_id": subscription_user_id,
                                "timestamp": websocket_manager._get_timestamp(),
                            }
                        )
                    )

                elif msg_type == "unsubscribe":
                    # Handle unsubscription
                    subscription_task_id = message.get("task_id")
                    subscription_user_id = message.get("user_id")
                    await websocket_manager.unsubscribe(
                        connection_id,
                        task_id=subscription_task_id,
                        user_id=subscription_user_id,
                    )
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "unsubscribed",
                                "task_id": subscription_task_id,
                                "user_id": subscription_user_id,
                                "timestamp": websocket_manager._get_timestamp(),
                            }
                        )
                    )

                elif msg_type == "progress_request":
                    # Handle progress data request
                    if task_id:
                        # Get current progress
                        # Note: In real implementation, you would call progress_manager
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "progress_data",
                                    "task_id": task_id,
                                    "timestamp": websocket_manager._get_timestamp(),
                                }
                            )
                        )

                elif msg_type == "logs_request":
                    # Handle logs data request
                    if task_id:
                        # Get recent logs
                        # Note: In real implementation, you would call log_manager
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "logs_data",
                                    "task_id": task_id,
                                    "timestamp": websocket_manager._get_timestamp(),
                                }
                            )
                        )

                elif msg_type == "notification_request":
                    # Handle notifications request
                    if user_id:
                        # Get recent notifications
                        # Note: In real implementation, you would call notification_manager
                        await websocket.send_text(
                            json.dumps(
                                {
                                    "type": "notifications_data",
                                    "user_id": user_id,
                                    "timestamp": websocket_manager._get_timestamp(),
                                }
                            )
                        )

                else:
                    # Handle with progress handler
                    await progress_handler.handle_message(connection_id, message)

            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON from connection {connection_id}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": "Invalid JSON",
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

            except Exception as e:
                logger.error(f"WebSocket message error from {connection_id}: {e}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "error",
                            "error": str(e),
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"WebSocket error from {connection_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass

    finally:
        if connection_id:
            logger.info(f"WebSocket cleanup: {connection_id}")
            await websocket_manager.disconnect(connection_id)


@router.websocket("/stream/{stream_type}")
async def stream_endpoint(
    websocket: WebSocket,
    stream_type: str = Path(..., description="Stream type: progress/logs/notifications"),
):
    """Specialized streaming endpoint for specific data types.

    Args:
        websocket: WebSocket connection
        stream_type: Type of stream (progress/logs/notifications)
    """
    connection_id = None
    try:
        # Establish connection
        connection_id = await websocket_manager.connect(websocket)
        if not connection_id:
            await websocket.close(code=1008, reason="Connection rejected")
            return

        logger.info(f"Stream WebSocket connected: {connection_id}, type={stream_type}")

        # Send stream status
        await websocket.send_text(
            json.dumps(
                {
                    "type": "stream_status",
                    "stream_type": stream_type,
                    "status": "connected",
                    "message": f"Stream endpoint connected for {stream_type}",
                    "timestamp": websocket_manager._get_timestamp(),
                }
            )
        )

        # Handle messages based on stream type
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "ping":
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "pong",
                            "stream_type": stream_type,
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

            elif msg_type == "start_stream":
                # Start streaming data
                task_id = message.get("task_id")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "stream_started",
                            "stream_type": stream_type,
                            "task_id": task_id,
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

            elif msg_type == "stop_stream":
                # Stop streaming data
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "stream_stopped",
                            "stream_type": stream_type,
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"Stream WebSocket disconnected: {connection_id}, type={stream_type}")

    except Exception as e:
        logger.error(f"Stream WebSocket error from {connection_id}: {e}")

    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)


@router.websocket("/dashboard")
async def dashboard_endpoint(
    websocket: WebSocket,
    dashboard_id: Optional[str] = Query(None, description="Dashboard ID"),
):
    """Dashboard-specific WebSocket endpoint.

    This endpoint provides aggregated data for dashboards
    and supports multiple task subscriptions.

    Args:
        websocket: WebSocket connection
        dashboard_id: Dashboard ID (optional)
    """
    connection_id = None
    try:
        connection_id = await websocket_manager.connect(websocket)
        if not connection_id:
            await websocket.close(code=1008, reason="Connection rejected")
            return

        logger.info(f"Dashboard WebSocket connected: {connection_id}, dashboard_id={dashboard_id}")

        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "dashboard_status",
                    "status": "connected",
                    "dashboard_id": dashboard_id,
                    "message": "Dashboard WebSocket connection established",
                    "timestamp": websocket_manager._get_timestamp(),
                }
            )
        )

        # Handle dashboard-specific messages
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            msg_type = message.get("type")

            if msg_type == "subscribe_tasks":
                # Subscribe to multiple tasks
                task_ids = message.get("task_ids", [])
                await websocket_manager.subscribe_to_tasks(connection_id, task_ids)
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "tasks_subscribed",
                            "task_ids": task_ids,
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

            elif msg_type == "get_dashboard_data":
                # Get aggregated dashboard data
                task_ids = message.get("task_ids", [])
                # Note: In real implementation, call visualization_manager for dashboard data
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "dashboard_data",
                            "task_ids": task_ids,
                            "data": {
                                "total_tasks": len(task_ids),
                                "active_tasks": 0,
                                "completed_tasks": 0,
                            },
                            "timestamp": websocket_manager._get_timestamp(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info(f"Dashboard WebSocket disconnected: {connection_id}")

    except Exception as e:
        logger.error(f"Dashboard WebSocket error from {connection_id}: {e}")

    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)
