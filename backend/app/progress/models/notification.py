"""Notification model for managing user notifications and alerts.

This module defines the Notification SQLAlchemy model for managing
user notifications, including notification types, status, channels,
and metadata.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Notification(Base):
    """Notification model for user notifications and alerts.

    This model manages user notifications including task status changes,
    errors, warnings, and system alerts.
    """

    __tablename__ = "notifications"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="通知ID",
    )
    user_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # Notification content
    title = Column(
        String(200),
        nullable=False,
        comment="通知标题",
    )
    message = Column(
        Text,
        nullable=False,
        comment="通知内容",
    )
    notification_type = Column(
        String(20),
        default="info",
        comment="通知类型 (info, success, warning, error, progress)",
    )

    # Status management
    is_read = Column(
        Boolean,
        default=False,
        index=True,
        comment="是否已读",
    )
    priority = Column(
        String(10),
        default="normal",
        comment="优先级 (low, normal, high, urgent)",
    )
    channels = Column(
        JSONB,
        default=list,
        comment="发送渠道 (websocket, email, browser, sms)",
    )

    # Related information
    related_task_id = Column(
        String(100),
        comment="关联任务ID",
    )
    action_url = Column(
        String(500),
        comment="操作链接",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        comment="创建时间",
    )
    read_at = Column(
        DateTime(timezone=True),
        comment="阅读时间",
    )
    expires_at = Column(
        DateTime(timezone=True),
        comment="过期时间",
    )

    # Delivery tracking
    delivery_status = Column(
        JSONB,
        default=dict,
        comment="各渠道送达状态",
    )
    retry_count = Column(
        Integer,
        default=0,
        comment="重试次数",
    )
    max_retries = Column(
        Integer,
        default=3,
        comment="最大重试次数",
    )

    # Metadata
    notification_metadata = Column(
        JSONB,
        default=dict,
        comment="通知元数据",
    )

    def __repr__(self) -> str:
        """Return string representation of the Notification."""
        return (
            f"<Notification(id={self.id}, user_id='{self.user_id}', "
            f"type='{self.notification_type}', priority='{self.priority}', "
            f"is_read={self.is_read})>"
        )

    @property
    def is_info(self) -> bool:
        """Check if notification type is info."""
        return self.notification_type == "info"

    @property
    def is_success(self) -> bool:
        """Check if notification type is success."""
        return self.notification_type == "success"

    @property
    def is_warning(self) -> bool:
        """Check if notification type is warning."""
        return self.notification_type == "warning"

    @property
    def is_error(self) -> bool:
        """Check if notification type is error."""
        return self.notification_type == "error"

    @property
    def is_progress(self) -> bool:
        """Check if notification type is progress."""
        return self.notification_type == "progress"

    @property
    def is_unread(self) -> bool:
        """Check if notification is unread."""
        return not self.is_read

    @property
    def is_low_priority(self) -> bool:
        """Check if priority is low."""
        return self.priority == "low"

    @property
    def is_normal_priority(self) -> bool:
        """Check if priority is normal."""
        return self.priority == "normal"

    @property
    def is_high_priority(self) -> bool:
        """Check if priority is high."""
        return self.priority == "high"

    @property
    def is_urgent_priority(self) -> bool:
        """Check if priority is urgent."""
        return self.priority == "urgent"

    @property
    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def can_retry(self) -> bool:
        """Check if notification can be retried."""
        return (self.retry_count or 0) < (self.max_retries or 3)

    @property
    def age_seconds(self) -> int:
        """Get notification age in seconds."""
        if not self.created_at:
            return 0
        return int((datetime.utcnow() - self.created_at).total_seconds())

    @property
    def priority_value(self) -> int:
        """Get numeric priority value."""
        priorities = {
            "low": 1,
            "normal": 2,
            "high": 3,
            "urgent": 4,
        }
        return priorities.get(self.priority, 0)

    @property
    def channel_count(self) -> int:
        """Get number of notification channels."""
        return len(self.channels) if self.channels else 0

    @property
    def successful_deliveries(self) -> int:
        """Get count of successful deliveries."""
        if not self.delivery_status:
            return 0
        return sum(
            1 for status in self.delivery_status.values()
            if status.get("status") == "sent"
        )

    @property
    def failed_deliveries(self) -> int:
        """Get count of failed deliveries."""
        if not self.delivery_status:
            return 0
        return sum(
            1 for status in self.delivery_status.values()
            if status.get("status") == "failed"
        )

    def mark_as_read(self) -> None:
        """Mark notification as read."""
        self.is_read = True
        if not self.read_at:
            self.read_at = func.now()

    def mark_as_unread(self) -> None:
        """Mark notification as unread."""
        self.is_read = False
        self.read_at = None

    def update_delivery_status(self, channel: str, status: str, error: str = None) -> None:
        """Update delivery status for a specific channel.

        Args:
            channel: Channel name
            status: Delivery status (sent, failed, pending)
            error: Optional error message
        """
        if not self.delivery_status:
            self.delivery_status = {}

        self.delivery_status[channel] = {
            "status": status,
            "timestamp": func.now(),
            "error": error,
        }

        if status == "failed":
            self.retry_count = (self.retry_count or 0) + 1

    def add_channel(self, channel: str) -> None:
        """Add a notification channel.

        Args:
            channel: Channel name to add
        """
        if not self.channels:
            self.channels = []

        if channel not in self.channels:
            self.channels.append(channel)

    def remove_channel(self, channel: str) -> None:
        """Remove a notification channel.

        Args:
            channel: Channel name to remove
        """
        if self.channels and channel in self.channels:
            self.channels.remove(channel)

    def to_dict(self) -> dict:
        """Convert Notification to dictionary."""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "notification_type": self.notification_type,
            "is_read": self.is_read,
            "priority": self.priority,
            "channels": self.channels or [],
            "related_task_id": self.related_task_id,
            "action_url": self.action_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "delivery_status": self.delivery_status or {},
            "retry_count": self.retry_count or 0,
            "max_retries": self.max_retries or 3,
            "metadata": self.notification_metadata or {},
            "is_info": self.is_info,
            "is_success": self.is_success,
            "is_warning": self.is_warning,
            "is_error": self.is_error,
            "is_progress": self.is_progress,
            "is_unread": self.is_unread,
            "is_low_priority": self.is_low_priority,
            "is_normal_priority": self.is_normal_priority,
            "is_high_priority": self.is_high_priority,
            "is_urgent_priority": self.is_urgent_priority,
            "is_expired": self.is_expired,
            "can_retry": self.can_retry,
            "age_seconds": self.age_seconds,
            "priority_value": self.priority_value,
            "channel_count": self.channel_count,
            "successful_deliveries": self.successful_deliveries,
            "failed_deliveries": self.failed_deliveries,
        }

    @classmethod
    def create_progress_notification(
        cls,
        user_id: str,
        task_id: str,
        title: str,
        message: str,
        progress: float = None,
        current_step: str = None,
        channels: list = None,
    ) -> "Notification":
        """Create a progress notification.

        Args:
            user_id: User ID
            task_id: Related task ID
            title: Notification title
            message: Notification message
            progress: Optional progress percentage
            current_step: Optional current step
            channels: Optional list of channels

        Returns:
            Notification: Progress notification instance
        """
        metadata = {}
        if progress is not None:
            metadata["progress"] = progress
        if current_step:
            metadata["current_step"] = current_step

        return cls(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="progress",
            related_task_id=task_id,
            channels=channels or ["websocket"],
            metadata=metadata,
        )

    @classmethod
    def create_success_notification(
        cls,
        user_id: str,
        task_id: str,
        title: str,
        message: str,
        channels: list = None,
    ) -> "Notification":
        """Create a success notification.

        Args:
            user_id: User ID
            task_id: Related task ID
            title: Notification title
            message: Notification message
            channels: Optional list of channels

        Returns:
            Notification: Success notification instance
        """
        return cls(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="success",
            related_task_id=task_id,
            channels=channels or ["websocket"],
        )

    @classmethod
    def create_error_notification(
        cls,
        user_id: str,
        task_id: str,
        title: str,
        message: str,
        error_details: dict = None,
        channels: list = None,
    ) -> "Notification":
        """Create an error notification.

        Args:
            user_id: User ID
            task_id: Related task ID
            title: Notification title
            message: Notification message
            error_details: Optional error details
            channels: Optional list of channels

        Returns:
            Notification: Error notification instance
        """
        metadata = {}
        if error_details:
            metadata["error_details"] = error_details

        return cls(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="error",
            priority="high",
            related_task_id=task_id,
            channels=channels or ["websocket"],
            metadata=metadata,
        )


# Database indexes for performance optimization
Index("idx_notifications_user_id", Notification.user_id)
Index("idx_notifications_is_read", Notification.is_read)
Index("idx_notifications_priority", Notification.priority)
Index("idx_notifications_created_at", Notification.created_at.desc())
Index("idx_notifications_related_task_id", Notification.related_task_id)

# Composite indexes for common queries
Index(
    "idx_notifications_user_read",
    Notification.user_id,
    Notification.is_read,
)
Index(
    "idx_notifications_user_priority",
    Notification.user_id,
    Notification.priority,
)
Index(
    "idx_notifications_type_priority",
    Notification.notification_type,
    Notification.priority,
)
