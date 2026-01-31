"""WebSocket message schemas for platform operations.

This module defines Pydantic models for validating WebSocket messages
related to platform operations, deployments, and compatibility checks.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message type enumeration."""
    # Platform messages
    PLATFORM_STATUS_UPDATE = "platform_status_update"
    PLATFORM_HEALTH_CHECK = "platform_health_check"
    PLATFORM_CONFIG_UPDATE = "platform_config_update"

    # Deployment messages
    DEPLOYMENT_STATUS_UPDATE = "deployment_status_update"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_PROGRESS = "deployment_progress"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    DEPLOYMENT_RETRY = "deployment_retry"

    # Compatibility check messages
    COMPATIBILITY_CHECK_STARTED = "compatibility_check_started"
    COMPATIBILITY_CHECK_PROGRESS = "compatibility_check_progress"
    COMPATIBILITY_CHECK_COMPLETED = "compatibility_check_completed"
    COMPATIBILITY_CHECK_FAILED = "compatibility_check_failed"

    # Notification messages
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_DELIVERED = "notification_delivered"
    NOTIFICATION_FAILED = "notification_failed"

    # System messages
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    ACKNOWLEDGMENT = "acknowledgment"
    SUBSCRIPTION_UPDATE = "subscription_update"
    BULK_OPERATION_UPDATE = "bulk_operation_update"


class MessagePriority(str, Enum):
    """Message priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class ConnectionStatus(str, Enum):
    """Connection status enumeration."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: str
        }


# Core Message Schemas
class WebSocketMessage(BaseSchema):
    """Base WebSocket message schema."""
    message_id: str = Field(..., description="Unique message identifier")
    message_type: MessageType = Field(..., description="Message type")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    priority: MessagePriority = Field(MessagePriority.NORMAL, description="Message priority")
    correlation_id: Optional[str] = Field(None, description="Correlation ID for request-response")
    source: str = Field(..., description="Message source")
    target: Optional[str] = Field(None, description="Message target")
    data: Dict[str, Any] = Field(default_factory=dict, description="Message data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator('message_id')
    def validate_message_id(cls, v):
        """Validate message ID format."""
        if not v or len(v) < 8:
            raise ValueError('Message ID must be at least 8 characters')
        return v


class MessageAcknowledgment(BaseSchema):
    """Schema for message acknowledgment."""
    original_message_id: str = Field(..., description="ID of message being acknowledged")
    status: str = Field(..., description="Acknowledgment status: success, error")
    message: Optional[str] = Field(None, description="Status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


# Platform-Specific Message Schemas
class PlatformStatusUpdate(BaseSchema):
    """Schema for platform status update message."""
    platform_id: str = Field(..., description="Platform identifier")
    platform_name: str = Field(..., description="Platform name")
    is_active: bool = Field(..., description="Platform active status")
    is_healthy: bool = Field(..., description="Platform health status")
    last_health_check: Optional[datetime] = Field(None, description="Last health check time")
    response_time_ms: Optional[float] = FieldResponse time in milliseconds(None, description="")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    status_details: Dict[str, Any] = Field(default_factory=dict, description="Additional status details")


class PlatformHealthCheckRequest(BaseSchema):
    """Schema for platform health check request."""
    platform_id: str = Field(..., description="Platform identifier")
    check_timeout: Optional[int] = Field(30, ge=1, le=300, description="Check timeout in seconds")
    check_depth: Optional[str] = Field("standard", description="Check depth: basic, standard, comprehensive")


class PlatformHealthCheckResponse(BaseSchema):
    """Schema for platform health check response."""
    platform_id: str = Field(..., description="Platform identifier")
    is_healthy: bool = Field(..., description="Health status")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    check_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed check results")


class PlatformConfigUpdate(BaseSchema):
    """Schema for platform configuration update message."""
    platform_id: str = Field(..., description="Platform identifier")
    config_changes: Dict[str, Any] = Field(..., description="Configuration changes")
    updated_by: str = Field(..., description="User who made the update")
    update_reason: Optional[str] = Field(None, description="Reason for update")


# Deployment-Specific Message Schemas
class DeploymentStatusUpdate(BaseSchema):
    """Schema for deployment status update message."""
    deployment_id: str = Field(..., description="Deployment identifier")
    platform_id: str = Field(..., description="Platform identifier")
    platform_name: str = Field(..., description="Platform name")
    skill_id: str = Field(..., description="Skill identifier")
    skill_name: str = Field(..., description="Skill name")
    status: str = Field(..., description="Deployment status")
    progress: Optional[float] = Field(None, ge=0, le=100, description="Deployment progress percentage")
    current_step: Optional[str] = Field(None, description="Current deployment step")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    platform_response: Optional[Dict[str, Any]] = Field(None, description="Platform response data")
    retry_count: int = Field(0, ge=0, description="Current retry count")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


class DeploymentStarted(BaseSchema):
    """Schema for deployment started message."""
    deployment_id: str = Field(..., description="Deployment identifier")
    platform_id: str = Field(..., description="Platform identifier")
    platform_name: str = Field(..., description="Platform name")
    skill_id: str = Field(..., description="Skill identifier")
    skill_name: str = Field(..., description="Skill name")
    skill_version: str = Field(..., description="Skill version")
    original_format: Optional[str] = Field(None, description="Original skill format")
    target_format: Optional[str] = Field(None, description="Target platform format")
    deployment_config: Dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")
    started_by: str = Field(..., description="User who initiated deployment")


class DeploymentProgress(BaseSchema):
    """Schema for deployment progress message."""
    deployment_id: str = Field(..., description="Deployment identifier")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    current_step: str = Field(..., description="Current step description")
    steps_completed: int = Field(..., ge=0, description="Number of completed steps")
    steps_total: int = Field(..., ge=0, description="Total number of steps")
    step_details: Optional[Dict[str, Any]] = Field(None, description="Current step details")
    time_elapsed: Optional[int] = Field(None, description="Time elapsed in seconds")
    estimated_remaining: Optional[int] = Field(None, description="Estimated remaining time in seconds")


class DeploymentCompleted(BaseSchema):
    """Schema for deployment completed message."""
    deployment_id: str = Field(..., description="Deployment identifier")
    success: bool = Field(..., description="Deployment success status")
    duration_seconds: Optional[int] = Field(None, description="Total duration in seconds")
    platform_deployment_id: Optional[str] = Field(None, description="Platform deployment ID")
    deployment_url: Optional[str] = Field(None, description="Deployment URL")
    platform_response: Dict[str, Any] = Field(default_factory=dict, description="Platform response data")
    summary: Optional[str] = Field(None, description="Deployment summary")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DeploymentFailed(BaseSchema):
    """Schema for deployment failed message."""
    deployment_id: str = Field(..., description="Deployment identifier")
    error_message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    can_retry: bool = Field(..., description="Whether deployment can be retried")
    retry_count: int = Field(..., description="Current retry count")
    max_retries: int = Field(..., description="Maximum retry attempts")
    platform_error_code: Optional[str] = Field(None, description="Platform-specific error code")
    troubleshooting_tips: Optional[List[str]] = Field(None, description="Troubleshooting suggestions")


class DeploymentRetry(BaseSchema):
    """Schema for deployment retry message."""
    deployment_id: str = Field(..., description="Deployment identifier")
    retry_count: int = Field(..., description="Current retry count")
    max_retries: int = Field(..., description="Maximum retry attempts")
    retry_reason: Optional[str] = Field(None, description="Reason for retry")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Retry configuration")
    estimated_delay: Optional[int] = Field(None, description="Estimated delay before retry in seconds")


# Compatibility Check Message Schemas
class CompatibilityCheckStarted(BaseSchema):
    """Schema for compatibility check started message."""
    check_id: str = Field(..., description="Compatibility check identifier")
    skill_id: str = Field(..., description="Skill identifier")
    skill_version: Optional[str] = Field(None, description="Skill version")
    platforms: List[str] = Field(..., description="Platforms to check")
    check_depth: str = Field(..., description="Check depth level")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    started_by: str = Field(..., description="User who initiated check")


class CompatibilityCheckProgress(BaseSchema):
    """Schema for compatibility check progress message."""
    check_id: str = Field(..., description="Compatibility check identifier")
    progress: float = Field(..., ge=0, le=100, description="Check progress percentage")
    current_platform: str = Field(..., description="Platform currently being checked")
    platforms_completed: List[str] = Field(..., description="Completed platforms")
    platforms_remaining: List[str] = Field(..., description="Remaining platforms")
    current_step: str = Field(..., description="Current check step")
    issues_found: int = Field(0, ge=0, description="Number of issues found so far")
    warnings_found: int = Field(0, ge=0, description="Number of warnings found so far")
    step_details: Optional[Dict[str, Any]] = Field(None, description="Current step details")


class CompatibilityCheckCompleted(BaseSchema):
    """Schema for compatibility check completed message."""
    check_id: str = Field(..., description="Compatibility check identifier")
    overall_compatible: bool = Field(..., description="Overall compatibility result")
    compatibility_score: Optional[float] = Field(None, ge=0, le=100, description="Overall compatibility score")
    platforms_checked: List[str] = Field(..., description="Platforms checked")
    platforms_compatible: List[str] = Field(..., description="Compatible platforms")
    platforms_incompatible: List[str] = Field(..., description="Incompatible platforms")
    total_issues: int = Field(..., description="Total number of issues")
    total_warnings: int = Field(..., description="Total number of warnings")
    critical_issues: int = Field(..., description="Number of critical issues")
    duration_seconds: Optional[int] = Field(None, description="Check duration in seconds")
    summary: Optional[str] = Field(None, description="Check summary")
    report_url: Optional[str] = Field(None, description="Detailed report URL")


class CompatibilityCheckFailed(BaseSchema):
    """Schema for compatibility check failed message."""
    check_id: str = Field(..., description="Compatibility check identifier")
    error_message: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")
    failed_platforms: List[str] = Field(..., description="Platforms that failed")
    error_details: Dict[str, Any] = Field(default_factory=dict, description="Detailed error information")
    progress_at_failure: Optional[float] = Field(None, description="Progress at time of failure")
    can_retry: bool = Field(..., description="Whether check can be retried")


# Notification Message Schemas
class NotificationSent(BaseSchema):
    """Schema for notification sent message."""
    notification_id: str = Field(..., description="Notification identifier")
    notification_type: str = Field(..., description="Notification type")
    priority: str = Field(..., description="Notification priority")
    title: str = Field(..., description="Notification title")
    channels: List[str] = Field(..., description="Delivery channels")
    recipient_count: int = Field(..., description="Number of recipients")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled delivery time")
    delivery_config: Dict[str, Any] = Field(default_factory=dict, description="Delivery configuration")


class NotificationDelivered(BaseSchema):
    """Schema for notification delivered message."""
    notification_id: str = Field(..., description="Notification identifier")
    channel: str = Field(..., description="Delivery channel")
    delivery_time: datetime = Field(..., description="Delivery timestamp")
    recipient: Optional[str] = Field(None, description="Recipient identifier")
    delivery_status: str = Field(..., description="Delivery status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    platform_response: Optional[Dict[str, Any]] = Field(None, description="Platform response")


class NotificationFailed(BaseSchema):
    """Schema for notification failed message."""
    notification_id: str = Field(..., description="Notification identifier")
    channel: str = Field(..., description="Delivery channel")
    failure_reason: str = Field(..., description="Failure reason")
    error_message: Optional[str] = Field(None, description="Error message")
    retry_count: int = Field(0, ge=0, description="Current retry count")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    will_retry: bool = Field(..., description="Whether notification will be retried")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry time")


# System Message Schemas
class HeartbeatMessage(BaseSchema):
    """Schema for heartbeat message."""
    connection_id: str = Field(..., description="Connection identifier")
    server_time: datetime = Field(default_factory=datetime.utcnow, description="Server timestamp")
    client_time: Optional[datetime] = Field(None, description="Client timestamp")
    latency_ms: Optional[float] = Field(None, description="Latency in milliseconds")
    server_status: str = Field("healthy", description="Server status")


class ErrorMessage(BaseSchema):
    """Schema for error message."""
    error_code: str = Field(..., description="Error code")
    error_message: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Error type")
    severity: str = Field(..., description="Error severity")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    correlation_id: Optional[str] = Field(None, description="Correlation ID")


class SubscriptionUpdate(BaseSchema):
    """Schema for subscription update message."""
    user_id: str = Field(..., description="User identifier")
    subscription_id: str = Field(..., description="Subscription identifier")
    action: str = Field(..., description="Action: added, removed, updated")
    notification_types: List[str] = Field(..., description="Affected notification types")
    platforms: Optional[List[str]] = Field(None, description="Affected platforms")
    channels: List[str] = Field(..., description="Delivery channels")
    is_active: bool = Field(..., description="Subscription active status")


class BulkOperationUpdate(BaseSchema):
    """Schema for bulk operation update message."""
    operation_id: str = Field(..., description="Bulk operation identifier")
    operation_type: str = Field(..., description="Operation type")
    total_items: int = Field(..., description="Total items to process")
    processed_items: int = Field(..., description="Number of processed items")
    successful_items: int = Field(..., description="Number of successful items")
    failed_items: int = Field(..., description="Number of failed items")
    current_item: Optional[str] = Field(None, description="Currently processing item")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    summary: Optional[str] = Field(None, description="Operation summary")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Errors encountered")


# Connection Management Schemas
class ConnectionRequest(BaseSchema):
    """Schema for WebSocket connection request."""
    user_id: Optional[str] = Field(None, description="User identifier")
    connection_type: str = Field(..., description="Connection type")
    subscriptions: List[str] = Field(default_factory=list, description="Message subscriptions")
    platform_id: Optional[str] = Field(None, description="Platform ID for platform-specific connections")
    skill_id: Optional[str] = Field(None, description="Skill ID for skill-specific connections")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional connection metadata")


class ConnectionResponse(BaseSchema):
    """Schema for WebSocket connection response."""
    connection_id: str = Field(..., description="Connection identifier")
    status: str = Field(..., description="Connection status")
    server_info: Dict[str, Any] = Field(default_factory=dict, description="Server information")
    subscribed_topics: List[str] = Field(default_factory=list, description="Subscribed topics")
    heartbeat_interval: int = Field(30, description="Heartbeat interval in seconds")
    rate_limits: Dict[str, int] = Field(default_factory=dict, description="Rate limits")
    message_queue_size: Optional[int] = Field(None, description="Message queue size")


class DisconnectionRequest(BaseSchema):
    """Schema for disconnection request."""
    connection_id: str = Field(..., description="Connection identifier")
    reason: Optional[str] = Field(None, description="Disconnection reason")
    graceful: bool = Field(True, description="Whether disconnection is graceful")


# Message Routing Schemas
class MessageRouting(BaseSchema):
    """Schema for message routing configuration."""
    message_type: MessageType = Field(..., description="Message type")
    routing_key: str = Field(..., description="Routing key")
    target_connections: Optional[List[str]] = Field(None, description="Specific connection IDs")
    target_users: Optional[List[str]] = Field(None, description="User IDs")
    target_platforms: Optional[List[str]] = Field(None, description="Platform IDs")
    broadcast: bool = Field(False, description="Whether to broadcast to all")
    persistent: bool = Field(False, description="Whether message should be persisted")


# Message Queue Schemas
class MessageQueueStatus(BaseSchema):
    """Schema for message queue status."""
    queue_name: str = Field(..., description="Queue name")
    queue_size: int = Field(..., description="Current queue size")
    max_size: Optional[int] = Field(None, description="Maximum queue size")
    oldest_message_age: Optional[int] = Field(None, description="Oldest message age in seconds")
    message_types: Dict[str, int] = Field(default_factory=dict, description="Message count by type")
    consumer_count: int = Field(..., description="Number of consumers")


class QueueStats(BaseSchema):
    """Schema for queue statistics."""
    total_messages: int = Field(..., description="Total messages processed")
    messages_per_second: float = Field(..., description="Messages processed per second")
    average_processing_time: float = Field(..., description="Average message processing time")
    error_rate: float = Field(..., description="Error rate percentage")
    queue_efficiency: float = Field(..., description="Queue efficiency percentage")