"""Progress tracking schemas package for Pydantic models.

This package contains Pydantic models for request/response validation
in the real-time progress tracking system API.
"""

from .progress_operations import (
    # Task progress operations
    CreateTaskRequest,
    UpdateProgressRequest,
    TaskProgressResponse,
    TaskStatusResponse,
    TaskListRequest,
    TaskListResponse,
    TaskHistoryRequest,
    TaskHistoryResponse,
    TaskCancelRequest,
    TaskPauseRequest,
    TaskResumeRequest,
    # Log operations
    CreateLogRequest,
    LogEntryResponse,
    LogListRequest,
    LogListResponse,
    LogFilterRequest,
    LogExportRequest,
    LogExportResponse,
    # Metric operations
    CreateMetricRequest,
    MetricResponse,
    MetricQueryRequest,
    MetricQueryResponse,
    MetricAggregateRequest,
    MetricAggregateResponse,
)
from .websocket_messages import (
    # WebSocket message types
    WebSocketMessage,
    ProgressUpdateMessage,
    LogMessage,
    NotificationMessage,
    ConnectionMessage,
    ErrorMessage,
    HeartbeatMessage,
    SubscribeMessage,
    UnsubscribeMessage,
    BroadcastMessage,
)
from .notification_config import (
    # Notification configuration
    NotificationConfig,
    NotificationRule,
    NotificationChannel,
    NotificationTemplate,
    UserNotificationSettings,
    NotificationCreateRequest,
    NotificationUpdateRequest,
    NotificationResponse,
    NotificationListRequest,
    NotificationListResponse,
    NotificationMarkReadRequest,
    NotificationStatsResponse,
)

__all__ = [
    # Progress operation schemas
    "CreateTaskRequest",
    "UpdateProgressRequest",
    "TaskProgressResponse",
    "TaskStatusResponse",
    "TaskListRequest",
    "TaskListResponse",
    "TaskHistoryRequest",
    "TaskHistoryResponse",
    "TaskCancelRequest",
    "TaskPauseRequest",
    "TaskResumeRequest",
    # Log operation schemas
    "CreateLogRequest",
    "LogEntryResponse",
    "LogListRequest",
    "LogListResponse",
    "LogFilterRequest",
    "LogExportRequest",
    "LogExportResponse",
    # Metric operation schemas
    "CreateMetricRequest",
    "MetricResponse",
    "MetricQueryRequest",
    "MetricQueryResponse",
    "MetricAggregateRequest",
    "MetricAggregateResponse",
    # WebSocket message schemas
    "WebSocketMessage",
    "ProgressUpdateMessage",
    "LogMessage",
    "NotificationMessage",
    "ConnectionMessage",
    "ErrorMessage",
    "HeartbeatMessage",
    "SubscribeMessage",
    "UnsubscribeMessage",
    "BroadcastMessage",
    # Notification configuration schemas
    "NotificationConfig",
    "NotificationRule",
    "NotificationChannel",
    "NotificationTemplate",
    "UserNotificationSettings",
    "NotificationCreateRequest",
    "NotificationUpdateRequest",
    "NotificationResponse",
    "NotificationListRequest",
    "NotificationListResponse",
    "NotificationMarkReadRequest",
    "NotificationStatsResponse",
]
