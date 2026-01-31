"""Real-time Progress Tracking Module for Skill Seekers Web Management System.

This module provides comprehensive real-time progress tracking capabilities including:
- Task progress monitoring and management
- Real-time logging with WebSocket streaming
- Multi-channel notification system
- Data visualization and dashboards
- WebSocket-based real-time communication
- Resource management and monitoring

Main Components:
    - ProgressManager: Core task progress tracking
    - LogManager: Real-time log management
    - NotificationManager: Multi-channel notifications
    - VisualizationManager: Charts and dashboards
    - WebSocketManager: Real-time communication
    - ResourceManager: System resource optimization
"""

from .models import (
    TaskProgress,
    TaskLog,
    Notification,
    ProgressMetric,
    TaskStatus,
    LogLevel,
    NotificationType,
    NotificationPriority,
)

from .schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
    UpdateStatusRequest,
    CreateLogEntryRequest,
    CreateNotificationRequest,
    TaskQueryParams,
    LogQueryParams,
    NotificationQueryParams,
    BulkUpdateRequest,
    BulkLogRequest,
)

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

from .progress_manager import ProgressManager, progress_manager
from .log_manager import LogManager, log_manager
from .notification_manager import NotificationManager, notification_manager
from .visualization_manager import VisualizationManager, visualization_manager
from .websocket_manager import WebSocketManager, websocket_manager, WebSocketConnection
from .websocket_handler import WebSocketEventHandler, websocket_event_handler
from .resource_manager import (
    ResourceManager,
    ResourcePool,
    DatabaseSessionPool,
    MemoryCachePool,
    ResourceType,
    ResourceStatus,
    resource_manager,
)

from .utils.serializers import (
    serialize_task_progress,
    deserialize_task_progress,
    serialize_log_entry,
    deserialize_log_entry,
    serialize_notification,
    deserialize_notification,
    serialize_metric,
    deserialize_metric,
    serialize_websocket_message,
    deserialize_websocket_message,
)

from .utils.validators import (
    validate_task_id,
    validate_user_id,
    validate_progress_value,
    validate_status,
    validate_log_level,
    validate_notification_type,
    ValidationError,
    ValidationResult,
)

from .utils.formatters import (
    format_duration,
    format_percentage,
    format_timestamp,
    format_file_size,
    format_speed,
    format_progress_bar,
    format_status_badge,
    format_priority_badge,
    format_log_level,
    format_notification_title,
    truncate_text,
    format_error_message,
    format_summary,
)

# Version
__version__ = "1.0.0"

# Public API
__all__ = [
    # Models
    "TaskProgress",
    "TaskLog",
    "Notification",
    "ProgressMetric",
    "TaskStatus",
    "LogLevel",
    "NotificationType",
    "NotificationPriority",

    # Schemas
    "CreateTaskRequest",
    "UpdateProgressRequest",
    "UpdateStatusRequest",
    "CreateLogEntryRequest",
    "CreateNotificationRequest",
    "TaskQueryParams",
    "LogQueryParams",
    "NotificationQueryParams",
    "BulkUpdateRequest",
    "BulkLogRequest",

    # WebSocket Messages
    "WebSocketMessage",
    "MessageType",
    "ProgressUpdateMessage",
    "LogMessage",
    "NotificationMessage",
    "MetricMessage",
    "ConnectionMessage",
    "HeartbeatMessage",
    "ErrorMessage",

    # Managers
    "ProgressManager",
    "progress_manager",
    "LogManager",
    "log_manager",
    "NotificationManager",
    "notification_manager",
    "VisualizationManager",
    "visualization_manager",
    "WebSocketManager",
    "websocket_manager",
    "WebSocketConnection",
    "WebSocketEventHandler",
    "websocket_event_handler",
    "ResourceManager",
    "resource_manager",

    # Resource Management
    "ResourcePool",
    "DatabaseSessionPool",
    "MemoryCachePool",
    "ResourceType",
    "ResourceStatus",

    # Serializers
    "serialize_task_progress",
    "deserialize_task_progress",
    "serialize_log_entry",
    "deserialize_log_entry",
    "serialize_notification",
    "deserialize_notification",
    "serialize_metric",
    "deserialize_metric",
    "serialize_websocket_message",
    "deserialize_websocket_message",

    # Validators
    "validate_task_id",
    "validate_user_id",
    "validate_progress_value",
    "validate_status",
    "validate_log_level",
    "validate_notification_type",
    "ValidationError",
    "ValidationResult",

    # Formatters
    "format_duration",
    "format_percentage",
    "format_timestamp",
    "format_file_size",
    "format_speed",
    "format_progress_bar",
    "format_status_badge",
    "format_priority_badge",
    "format_log_level",
    "format_notification_title",
    "truncate_text",
    "format_error_message",
    "format_summary",
]
