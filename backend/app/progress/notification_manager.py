"""Notification management for real-time progress tracking.

This module provides NotificationManager for creating, sending, and managing
user notifications with multiple delivery channels.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4
from collections import defaultdict, deque

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from .models.notification import Notification, NotificationType, NotificationPriority
from .schemas.progress_operations import (
    CreateNotificationRequest,
    NotificationQueryParams,
    UpdateNotificationRequest,
)
from .schemas.websocket_messages import (
    NotificationMessage,
    MessageType,
)
from .utils.validators import (
    validate_user_id,
    validate_notification_type,
    validate_priority,
    ValidationError,
)
from .utils.serializers import serialize_notification
from .utils.formatters import format_timestamp, format_relative_time
from .websocket import websocket_manager

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification delivery channels."""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    PUSH = "push"
    SLACK = "slack"


class NotificationDelivery:
    """Tracks notification delivery status."""

    def __init__(
        self,
        channel: NotificationChannel,
        status: str = "pending",
        attempts: int = 0,
        max_attempts: int = 3,
        last_attempt: Optional[datetime] = None,
        error_message: Optional[str] = None,
    ):
        """Initialize notification delivery.

        Args:
            channel: Delivery channel
            status: Delivery status (pending, sent, failed, delivered)
            attempts: Number of delivery attempts
            max_attempts: Maximum retry attempts
            last_attempt: Timestamp of last attempt
            error_message: Error message if failed
        """
        self.channel = channel
        self.status = status
        self.attempts = attempts
        self.max_attempts = max_attempts
        self.last_attempt = last_attempt
        self.error_message = error_message
        self.delivered_at: Optional[datetime] = None

    def can_retry(self) -> bool:
        """Check if delivery can be retried.

        Returns:
            True if can retry
        """
        return self.attempts < self.max_attempts and self.status in ["pending", "failed"]

    def mark_sent(self):
        """Mark as sent."""
        self.status = "sent"
        self.attempts += 1
        self.last_attempt = datetime.utcnow()

    def mark_delivered(self):
        """Mark as delivered."""
        self.status = "delivered"
        self.delivered_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark as failed.

        Args:
            error: Error message
        """
        self.status = "failed"
        self.error_message = error
        self.attempts += 1
        self.last_attempt = datetime.utcnow()


class NotificationManager:
    """Core manager for user notifications."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize notification manager.

        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session
        self.notification_handlers: Dict[NotificationChannel, List[Callable]] = defaultdict(list)
        self.delivery_queue: deque = deque()
        self._lock = asyncio.Lock()
        self._stats = {
            "total_created": 0,
            "total_sent": 0,
            "total_delivered": 0,
            "total_failed": 0,
            "by_channel": defaultdict(int),
            "by_priority": defaultdict(int),
            "by_type": defaultdict(int),
        }

    async def create_notification(
        self,
        request: CreateNotificationRequest,
        db_session: Optional[Session] = None,
    ) -> Notification:
        """Create a new notification.

        Args:
            request: Notification creation request
            db_session: Database session (overrides instance session)

        Returns:
            Created Notification instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate request
        if not validate_user_id(request.user_id):
            raise ValidationError(f"Invalid user_id: {request.user_id}")

        if not validate_notification_type(request.notification_type):
            raise ValidationError(f"Invalid notification type: {request.notification_type}")

        if not validate_priority(request.priority):
            raise ValidationError(f"Invalid priority: {request.priority}")

        # Create notification
        notification = Notification(
            user_id=request.user_id,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            priority=request.priority,
            channels=request.channels or [NotificationChannel.WEBSOCKET],
            related_task_id=request.related_task_id,
            action_url=request.action_url,
            notification_metadata=request.metadata or {},
            retry_count=0,
            max_retries=3,
        )

        # Save to database if session provided
        session = db_session or self.db_session
        if session:
            session.add(notification)
            session.commit()
            session.refresh(notification)

        # Update statistics
        self._stats["total_created"] += 1
        self._stats["by_priority"][request.priority] += 1
        self._stats["by_type"][request.notification_type] += 1

        # Send notification
        await self.send_notification(notification, db_session)

        logger.info(f"Created notification {notification.id} for user {request.user_id}")
        return notification

    async def get_notification(
        self,
        notification_id: Union[str, UUID],
        db_session: Optional[Session] = None,
    ) -> Optional[Notification]:
        """Get notification by ID.

        Args:
            notification_id: Notification ID
            db_session: Database session (overrides instance session)

        Returns:
            Notification instance or None if not found
        """
        session = db_session or self.db_session
        if not session:
            return None

        if isinstance(notification_id, str):
            try:
                notification_id = UUID(notification_id)
            except ValueError:
                return None

        return session.query(Notification).filter(Notification.id == notification_id).first()

    async def list_notifications(
        self,
        query: NotificationQueryParams,
        db_session: Optional[Session] = None,
    ) -> List[Notification]:
        """List notifications with optional filtering.

        Args:
            query: Query parameters for filtering
            db_session: Database session (overrides instance session)

        Returns:
            List of Notification instances
        """
        session = db_session or self.db_session
        if not session:
            # Return empty list if no database
            return []

        # Query database
        query_builder = session.query(Notification)

        # Apply filters
        if query.user_id:
            query_builder = query_builder.filter(Notification.user_id == query.user_id)
        if query.notification_type:
            query_builder = query_builder.filter(Notification.notification_type == query.notification_type)
        if query.priority:
            query_builder = query_builder.filter(Notification.priority == query.priority)
        if query.is_read is not None:
            query_builder = query_builder.filter(Notification.is_read == query.is_read)
        if query.date_from:
            query_builder = query_builder.filter(Notification.created_at >= query.date_from)
        if query.date_to:
            query_builder = query_builder.filter(Notification.created_at <= query.date_to)

        # Sort
        if query.sort_order == "asc":
            query_builder = query_builder.order_by(Notification.created_at)
        else:
            query_builder = query_builder.order_by(desc(Notification.created_at))

        # Limit
        if query.limit:
            query_builder = query_builder.limit(query.limit)

        return query_builder.all()

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        db_session: Optional[Session] = None,
    ) -> List[Notification]:
        """Get notifications for a specific user.

        Args:
            user_id: User ID
            unread_only: Only return unread notifications
            limit: Maximum number of notifications to return
            db_session: Database session (overrides instance session)

        Returns:
            List of Notification instances
        """
        query = NotificationQueryParams(
            user_id=user_id,
            is_read=not unread_only if unread_only else None,
            limit=limit,
        )
        return await self.list_notifications(query, db_session)

    async def mark_as_read(
        self,
        notification_id: Union[str, UUID],
        db_session: Optional[Session] = None,
    ) -> bool:
        """Mark notification as read.

        Args:
            notification_id: Notification ID
            db_session: Database session (overrides instance session)

        Returns:
            True if marked successfully
        """
        session = db_session or self.db_session
        if not session:
            return False

        if isinstance(notification_id, str):
            try:
                notification_id = UUID(notification_id)
            except ValueError:
                return False

        notification = session.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            session.commit()
            return True

        return False

    async def mark_all_as_read(
        self,
        user_id: str,
        db_session: Optional[Session] = None,
    ) -> int:
        """Mark all notifications as read for a user.

        Args:
            user_id: User ID
            db_session: Database session (overrides instance session)

        Returns:
            Number of notifications marked as read
        """
        session = db_session or self.db_session
        if not session:
            return 0

        updated = (
            session.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa
            )
            .update(
                {
                    "is_read": True,
                    "read_at": datetime.utcnow(),
                }
            )
        )
        session.commit()
        return updated

    async def delete_notification(
        self,
        notification_id: Union[str, UUID],
        db_session: Optional[Session] = None,
    ) -> bool:
        """Delete a notification.

        Args:
            notification_id: Notification ID
            db_session: Database session (overrides instance session)

        Returns:
            True if deleted successfully
        """
        session = db_session or self.db_session
        if not session:
            return False

        if isinstance(notification_id, str):
            try:
                notification_id = UUID(notification_id)
            except ValueError:
                return False

        notification = session.query(Notification).filter(Notification.id == notification_id).first()
        if notification:
            session.delete(notification)
            session.commit()
            return True

        return False

    async def send_notification(
        self,
        notification: Notification,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Send notification through configured channels.

        Args:
            notification: Notification instance
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary with delivery results
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(notification.channels),
        }

        for channel in notification.channels:
            try:
                success = await self._send_through_channel(notification, channel)
                if success:
                    results["successful"].append(channel.value)
                    self._stats["total_sent"] += 1
                    self._stats["by_channel"][channel.value] += 1
                else:
                    results["failed"].append(channel.value)
                    self._stats["total_failed"] += 1
            except Exception as e:
                results["failed"].append(channel.value)
                self._stats["total_failed"] += 1
                logger.error(f"Failed to send notification through {channel.value}: {e}")

        # Update delivery status in database
        session = db_session or self.db_session
        if session:
            session.merge(notification)
            session.commit()

        logger.info(f"Sent notification {notification.id}: {len(results['successful'])}/{results['total']} channels")
        return results

    async def _send_through_channel(
        self,
        notification: Notification,
        channel: NotificationChannel,
    ) -> bool:
        """Send notification through a specific channel.

        Args:
            notification: Notification instance
            channel: Delivery channel

        Returns:
            True if sent successfully
        """
        if channel == NotificationChannel.WEBSOCKET:
            return await self._send_websocket(notification)
        elif channel == NotificationChannel.EMAIL:
            return await self._send_email(notification)
        elif channel == NotificationChannel.PUSH:
            return await self._send_push(notification)
        elif channel == NotificationChannel.SLACK:
            return await self._send_slack(notification)
        else:
            logger.warning(f"Unknown notification channel: {channel}")
            return False

    async def _send_websocket(self, notification: Notification) -> bool:
        """Send notification via WebSocket.

        Args:
            notification: Notification instance

        Returns:
            True if sent successfully
        """
        message = NotificationMessage(
            type=MessageType.NOTIFICATION,
            notification_id=str(notification.id),
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            priority=notification.priority,
            related_task_id=notification.related_task_id,
            action_url=notification.action_url,
            timestamp=time.time(),
        )

        # Send to user's WebSocket connections
        sent_count = await websocket_manager.broadcast_to_user(
            notification.user_id,
            message.dict(),
        )

        # Mark as delivered if sent to at least one connection
        if sent_count > 0:
            notification.successful_deliveries = (
                notification.successful_deliveries or 0
            ) + 1
            self._stats["total_delivered"] += 1
            return True

        return False

    async def _send_email(self, notification: Notification) -> bool:
        """Send notification via email (placeholder).

        Args:
            notification: Notification instance

        Returns:
            True if sent successfully
        """
        # Placeholder for email sending logic
        # In a real implementation, you would integrate with an email service
        logger.info(f"Email notification would be sent: {notification.title}")
        return True

    async def _send_push(self, notification: Notification) -> bool:
        """Send push notification (placeholder).

        Args:
            notification: Notification instance

        Returns:
            True if sent successfully
        """
        # Placeholder for push notification logic
        # In a real implementation, you would integrate with FCM/APNS
        logger.info(f"Push notification would be sent: {notification.title}")
        return True

    async def _send_slack(self, notification: Notification) -> bool:
        """Send Slack notification (placeholder).

        Args:
            notification: Notification instance

        Returns:
            True if sent successfully
        """
        # Placeholder for Slack notification logic
        # In a real implementation, you would integrate with Slack API
        logger.info(f"Slack notification would be sent: {notification.title}")
        return True

    async def create_task_notification(
        self,
        user_id: str,
        task_id: str,
        title: str,
        message: str,
        notification_type: str = NotificationType.PROGRESS,
        priority: str = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        db_session: Optional[Session] = None,
    ) -> Notification:
        """Create a notification related to a task.

        Args:
            user_id: User ID
            task_id: Related task ID
            title: Notification title
            message: Notification message
            notification_type: Notification type
            priority: Notification priority
            channels: Delivery channels
            db_session: Database session (overrides instance session)

        Returns:
            Created Notification instance
        """
        request = CreateNotificationRequest(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            channels=channels or [NotificationChannel.WEBSOCKET],
            related_task_id=task_id,
        )

        return await self.create_notification(request, db_session)

    async def get_notification_statistics(
        self,
        user_id: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Get notification statistics.

        Args:
            user_id: Filter by user ID (optional)
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary containing statistics
        """
        session = db_session or self.db_session
        if not session:
            return dict(self._stats)

        # Build query
        query_builder = session.query(Notification)
        if user_id:
            query_builder = query_builder.filter(Notification.user_id == user_id)

        total = query_builder.count()
        unread = query_builder.filter(Notification.is_read == False).count()  # noqa

        # Get priority distribution
        priority_stats = {}
        for priority in NotificationPriority:
            count = query_builder.filter(Notification.priority == priority).count()
            priority_stats[priority] = count

        # Get type distribution
        type_stats = {}
        for ntype in NotificationType:
            count = query_builder.filter(Notification.notification_type == ntype).count()
            type_stats[ntype] = count

        # Get channel distribution
        channel_stats = {}
        for channel in NotificationChannel:
            # Count notifications that include this channel
            count = query_builder.filter(Notification.channels.contains([channel])).count()
            channel_stats[channel.value] = count

        return {
            "total": total,
            "unread": unread,
            "read": total - unread,
            "by_priority": priority_stats,
            "by_type": type_stats,
            "by_channel": channel_stats,
            **dict(self._stats),
        }

    def register_channel_handler(
        self,
        channel: NotificationChannel,
        handler: Callable,
    ):
        """Register a notification channel handler.

        Args:
            channel: Notification channel
            handler: Async handler function(notification)
        """
        self.notification_handlers[channel].append(handler)

    def unregister_channel_handler(
        self,
        channel: NotificationChannel,
        handler: Callable,
    ):
        """Unregister a notification channel handler.

        Args:
            channel: Notification channel
            handler: Handler to remove
        """
        if handler in self.notification_handlers[channel]:
            self.notification_handlers[channel].remove(handler)

    def get_stats(self) -> Dict[str, Any]:
        """Get notification manager statistics.

        Returns:
            Dictionary containing statistics
        """
        return dict(self._stats)


# Global notification manager instance
notification_manager = NotificationManager()
