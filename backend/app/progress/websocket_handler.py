"""WebSocket handlers for real-time progress tracking.

This module provides specialized WebSocket handlers for different
message types and event processing.
"""

import asyncio
import logging
from typing import Any, Dict, Optional

from .schemas.websocket_messages import (
    MessageType,
    ProgressUpdateMessage,
    LogMessage,
    NotificationMessage,
    MetricMessage,
    HeartbeatMessage,
)
from .progress_manager import progress_manager
from .log_manager import log_manager
from .notification_manager import notification_manager
from .websocket import websocket_manager

logger = logging.getLogger(__name__)


class ProgressWebSocketHandler:
    """Handler for progress-related WebSocket messages."""

    def __init__(self):
        """Initialize progress handler."""
        self.connection_tasks: Dict[str, str] = {}  # Maps connection_id to task_id

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """Handle progress-related message.

        Args:
            connection_id: WebSocket connection ID
            message: Received message

        Returns:
            True if handled successfully
        """
        try:
            msg_type = message.get("type")
            msg_type_enum = MessageType(msg_type)

            if msg_type_enum == MessageType.PROGRESS_UPDATE:
                await self._handle_progress_update(connection_id, message)
            elif msg_type_enum == MessageType.LOG_MESSAGE:
                await self._handle_log_message(connection_id, message)
            elif msg_type_enum == MessageType.HEARTBEAT:
                await self._handle_heartbeat(connection_id, message)
            else:
                logger.warning(f"Unknown message type: {msg_type}")

            return True

        except Exception as e:
            logger.error(f"Error handling progress message: {e}")
            return False

    async def _handle_progress_update(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ):
        """Handle progress update message.

        Args:
            connection_id: WebSocket connection ID
            message: Progress update message
        """
        try:
            # Parse message
            progress_msg = ProgressUpdateMessage(**message)

            # Track connection-task association
            if progress_msg.task_id:
                self.connection_tasks[connection_id] = progress_msg.task_id

            # Send acknowledgment
            await websocket_manager.send_message(connection_id, {
                "type": "progress_update_acknowledged",
                "task_id": progress_msg.task_id,
                "timestamp": message.get("timestamp"),
            })

            logger.debug(f"Processed progress update for task {progress_msg.task_id}")

        except Exception as e:
            logger.error(f"Error handling progress update: {e}")
            await websocket_manager.send_error(
                connection_id,
                f"Failed to process progress update: {str(e)}",
            )

    async def _handle_log_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ):
        """Handle log message.

        Args:
            connection_id: WebSocket connection ID
            message: Log message
        """
        try:
            # Parse message
            log_msg = LogMessage(**message)

            # Create log entry
            from .schemas.progress_operations import CreateLogEntryRequest

            request = CreateLogEntryRequest(
                task_id=log_msg.task_id,
                level=log_msg.level,
                message=log_msg.message,
                source=log_msg.source,
            )

            await log_manager.create_log_entry(request)

            # Send acknowledgment
            await websocket_manager.send_message(connection_id, {
                "type": "log_message_acknowledged",
                "task_id": log_msg.task_id,
                "timestamp": message.get("timestamp"),
            })

            logger.debug(f"Processed log message for task {log_msg.task_id}")

        except Exception as e:
            logger.error(f"Error handling log message: {e}")
            await websocket_manager.send_error(
                connection_id,
                f"Failed to process log message: {str(e)}",
            )

    async def _handle_heartbeat(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ):
        """Handle heartbeat message.

        Args:
            connection_id: WebSocket connection ID
            message: Heartbeat message
        """
        try:
            # Parse message
            heartbeat_msg = HeartbeatMessage(**message)

            # Send heartbeat response
            await websocket_manager.send_message(connection_id, {
                "type": "heartbeat_response",
                "timestamp": message.get("timestamp"),
                "server_time": heartbeat_msg.timestamp,
            })

        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}")

    async def subscribe_to_task(
        self,
        connection_id: str,
        task_id: str,
    ) -> bool:
        """Subscribe connection to task updates.

        Args:
            connection_id: WebSocket connection ID
            task_id: Task ID to subscribe to

        Returns:
            True if subscribed successfully
        """
        try:
            # Subscribe to log stream
            await log_manager.subscribe_to_logs(task_id, connection_id)

            # Track subscription
            self.connection_tasks[connection_id] = task_id

            # Send confirmation
            await websocket_manager.send_message(connection_id, {
                "type": "subscription_confirmed",
                "task_id": task_id,
                "message": f"Subscribed to task {task_id}",
            })

            logger.info(f"Subscribed connection {connection_id} to task {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error subscribing to task: {e}")
            await websocket_manager.send_error(
                connection_id,
                f"Failed to subscribe to task: {str(e)}",
            )
            return False

    async def unsubscribe_from_task(
        self,
        connection_id: str,
        task_id: str,
    ):
        """Unsubscribe connection from task updates.

        Args:
            connection_id: WebSocket connection ID
            task_id: Task ID to unsubscribe from
        """
        try:
            await log_manager.unsubscribe_from_logs(task_id, connection_id)

            # Remove tracking
            if connection_id in self.connection_tasks:
                del self.connection_tasks[connection_id]

            # Send confirmation
            await websocket_manager.send_message(connection_id, {
                "type": "unsubscription_confirmed",
                "task_id": task_id,
                "message": f"Unsubscribed from task {task_id}",
            })

            logger.info(f"Unsubscribed connection {connection_id} from task {task_id}")

        except Exception as e:
            logger.error(f"Error unsubscribing from task: {e}")


class NotificationWebSocketHandler:
    """Handler for notification-related WebSocket messages."""

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """Handle notification-related message.

        Args:
            connection_id: WebSocket connection ID
            message: Received message

        Returns:
            True if handled successfully
        """
        try:
            msg_type = message.get("type")
            msg_type_enum = MessageType(msg_type)

            if msg_type_enum == MessageType.NOTIFICATION:
                await self._handle_notification_message(connection_id, message)
            elif msg_type_enum == MessageType.HEARTBEAT:
                # Forward to progress handler
                return await progress_handler._handle_heartbeat(connection_id, message)

            return True

        except Exception as e:
            logger.error(f"Error handling notification message: {e}")
            return False

    async def _handle_notification_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ):
        """Handle notification message.

        Args:
            connection_id: WebSocket connection ID
            message: Notification message
        """
        try:
            # Parse message
            notification_msg = NotificationMessage(**message)

            # Create notification
            from .schemas.progress_operations import CreateNotificationRequest

            request = CreateNotificationRequest(
                user_id=notification_msg.user_id,
                title=notification_msg.title,
                message=notification_msg.message,
                notification_type=notification_msg.notification_type,
                priority=notification_msg.priority,
                related_task_id=notification_msg.related_task_id,
                action_url=notification_msg.action_url,
            )

            await notification_manager.create_notification(request)

            # Send acknowledgment
            await websocket_manager.send_message(connection_id, {
                "type": "notification_acknowledged",
                "notification_id": notification_msg.notification_id,
                "timestamp": message.get("timestamp"),
            })

            logger.debug(f"Processed notification for user {notification_msg.user_id}")

        except Exception as e:
            logger.error(f"Error handling notification message: {e}")
            await websocket_manager.send_error(
                connection_id,
                f"Failed to process notification: {str(e)}",
            )


class MetricWebSocketHandler:
    """Handler for metric-related WebSocket messages."""

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """Handle metric-related message.

        Args:
            connection_id: WebSocket connection ID
            message: Received message

        Returns:
            True if handled successfully
        """
        try:
            msg_type = message.get("type")
            msg_type_enum = MessageType(msg_type)

            if msg_type_enum == MessageType.METRIC:
                await self._handle_metric_message(connection_id, message)
            elif msg_type_enum == MessageType.HEARTBEAT:
                # Forward to progress handler
                return await progress_handler._handle_heartbeat(connection_id, message)

            return True

        except Exception as e:
            logger.error(f"Error handling metric message: {e}")
            return False

    async def _handle_metric_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ):
        """Handle metric message.

        Args:
            connection_id: WebSocket connection ID
            message: Metric message
        """
        try:
            # Parse message
            metric_msg = MetricMessage(**message)

            # Create metric entry
            from .models.metric import ProgressMetric

            metric = ProgressMetric(
                metric_name=metric_msg.metric_name,
                value=metric_msg.value,
                unit=metric_msg.unit,
                labels=metric_msg.labels or {},
                dimensions=metric_msg.dimensions or {},
                related_task_id=metric_msg.related_task_id,
                related_user_id=metric_msg.related_user_id,
            )

            # In a real implementation, you would save to database
            logger.debug(f"Received metric: {metric_msg.metric_name} = {metric_msg.value}")

            # Send acknowledgment
            await websocket_manager.send_message(connection_id, {
                "type": "metric_acknowledged",
                "metric_name": metric_msg.metric_name,
                "timestamp": message.get("timestamp"),
            })

        except Exception as e:
            logger.error(f"Error handling metric message: {e}")
            await websocket_manager.send_error(
                connection_id,
                f"Failed to process metric: {str(e)}",
            )


class WebSocketEventHandler:
    """Main event handler for all WebSocket messages."""

    def __init__(self):
        """Initialize event handler."""
        self.progress_handler = ProgressWebSocketHandler()
        self.notification_handler = NotificationWebSocketHandler()
        self.metric_handler = MetricWebSocketHandler()

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """Handle any WebSocket message.

        Args:
            connection_id: WebSocket connection ID
            message: Received message

        Returns:
            True if handled successfully
        """
        try:
            msg_type = message.get("type")

            if not msg_type or not MessageType.has_value(msg_type):
                await websocket_manager.send_error(connection_id, "Invalid message type")
                return False

            msg_type_enum = MessageType(msg_type)

            # Route to appropriate handler
            if msg_type_enum in [MessageType.PROGRESS_UPDATE, MessageType.LOG_MESSAGE, MessageType.HEARTBEAT]:
                return await self.progress_handler.handle_message(connection_id, message)
            elif msg_type_enum in [MessageType.NOTIFICATION]:
                return await self.notification_handler.handle_message(connection_id, message)
            elif msg_type_enum in [MessageType.METRIC]:
                return await self.metric_handler.handle_message(connection_id, message)
            else:
                logger.warning(f"Unknown message type: {msg_type}")
                await websocket_manager.send_error(connection_id, f"Unknown message type: {msg_type}")
                return False

        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")
            await websocket_manager.send_error(connection_id, f"Message handling error: {str(e)}")
            return False

    async def handle_connection(
        self,
        connection_id: str,
        task_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Handle new WebSocket connection.

        Args:
            connection_id: WebSocket connection ID
            task_id: Associated task ID (optional)
            user_id: Associated user ID (optional)
        """
        try:
            # Track connection
            if task_id:
                await self.progress_handler.subscribe_to_task(connection_id, task_id)

            # Send welcome message
            await websocket_manager.send_message(connection_id, {
                "type": "connection_welcome",
                "connection_id": connection_id,
                "task_id": task_id,
                "user_id": user_id,
                "timestamp": message.get("timestamp"),
                "message": "Connected to progress tracking WebSocket",
            })

            logger.info(f"Handled WebSocket connection: {connection_id}")

        except Exception as e:
            logger.error(f"Error handling connection: {e}")

    async def handle_disconnection(self, connection_id: str):
        """Handle WebSocket disconnection.

        Args:
            connection_id: WebSocket connection ID
        """
        try:
            # Clean up subscriptions
            if connection_id in self.progress_handler.connection_tasks:
                task_id = self.progress_handler.connection_tasks[connection_id]
                await log_manager.unsubscribe_from_logs(task_id, connection_id)
                del self.progress_handler.connection_tasks[connection_id]

            logger.info(f"Handled WebSocket disconnection: {connection_id}")

        except Exception as e:
            logger.error(f"Error handling disconnection: {e}")


# Global event handler instance
websocket_event_handler = WebSocketEventHandler()


# Register handlers with WebSocket manager
async def setup_websocket_handlers():
    """Set up WebSocket message handlers."""
    # This function can be called during application startup
    logger.info("WebSocket handlers registered")


# Handler functions for integration with API
async def handle_websocket_message(connection_id: str, message: Dict[str, Any]) -> bool:
    """Handle WebSocket message using registered handlers.

    Args:
        connection_id: WebSocket connection ID
        message: Received message

    Returns:
        True if handled successfully
    """
    return await websocket_event_handler.handle_message(connection_id, message)


async def handle_websocket_connection(connection_id: str, task_id: str = None, user_id: str = None):
    """Handle new WebSocket connection.

    Args:
        connection_id: WebSocket connection ID
        task_id: Associated task ID (optional)
        user_id: Associated user ID (optional)
    """
    await websocket_event_handler.handle_connection(connection_id, task_id, user_id)


async def handle_websocket_disconnection(connection_id: str):
    """Handle WebSocket disconnection.

    Args:
        connection_id: WebSocket connection ID
    """
    await websocket_event_handler.handle_disconnection(connection_id)
