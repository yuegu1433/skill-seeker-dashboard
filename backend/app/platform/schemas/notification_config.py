"""Notification configuration schemas.

This module defines Pydantic models for validating notification configurations
related to platform operations, deployments, and compatibility checks.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enumeration."""
    DEPLOYMENT_SUCCESS = "deployment_success"
    DEPLOYMENT_FAILURE = "deployment_failure"
    DEPLOYMENT_STATUS = "deployment_status"
    PLATFORM_HEALTH = "platform_health"
    COMPATIBILITY_CHECK = "compatibility_check"
    COMPATIBILITY_ISSUE = "compatibility_issue"
    SYSTEM_ALERT = "system_alert"
    BULK_OPERATION = "bulk_operation"


class NotificationPriority(str, Enum):
    """Notification priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DeliveryChannel(str, Enum):
    """Delivery channel enumeration."""
    WEBSOCKET = "websocket"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    DISCORD = "discord"


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


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


# Notification Configuration Schemas
class NotificationConfigCreateRequest(BaseSchema):
    """Request schema for creating notification configuration."""
    name: str = Field(..., min_length=1, max_length=100, description="Configuration name")
    description: Optional[str] = Field(None, max_length=500, description="Configuration description")
    notification_types: List[NotificationType] = Field(..., min_items=1, description="Types of notifications to send")
    priority_threshold: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Minimum priority to send")
    channels: List[DeliveryChannel] = Field(..., min_items=1, description="Delivery channels to use")
    is_active: bool = Field(default=True, description="Whether configuration is active")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Notification filters")
    template_config: Dict[str, Any] = Field(default_factory=dict, description="Template configuration")
    retry_config: Dict[str, Any] = Field(default_factory=dict, description="Retry configuration")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")

    @validator('name')
    def validate_name(cls, v):
        """Validate configuration name."""
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class NotificationConfigUpdateRequest(BaseSchema):
    """Request schema for updating notification configuration."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    notification_types: Optional[List[NotificationType]] = None
    priority_threshold: Optional[NotificationPriority] = None
    channels: Optional[List[DeliveryChannel]] = None
    is_active: Optional[bool] = None
    filters: Optional[Dict[str, Any]] = None
    template_config: Optional[Dict[str, Any]] = None
    retry_config: Optional[Dict[str, Any]] = None
    rate_limit: Optional[Dict[str, Any]] = None


class NotificationConfigResponse(BaseSchema):
    """Response schema for notification configuration."""
    id: str
    name: str
    description: Optional[str]
    notification_types: List[str]
    priority_threshold: str
    channels: List[str]
    is_active: bool
    filters: Dict[str, Any]
    template_config: Dict[str, Any]
    retry_config: Dict[str, Any]
    rate_limit: Optional[Dict[str, Any]]
    created_at: Optional[str]
    updated_at: Optional[str]


# Notification Delivery Schemas
class NotificationDeliveryRequest(BaseSchema):
    """Request schema for sending a notification."""
    config_id: Optional[str] = Field(None, description="Notification configuration ID")
    notification_type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(NotificationPriority.MEDIUM, description="Notification priority")
    title: str = Field(..., min_length=1, max_length=200, description="Notification title")
    message: str = Field(..., min_length=1, max_length=2000, description="Notification message")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional notification data")
    channels: Optional[List[DeliveryChannel]] = Field(None, description="Specific channels to use")
    recipients: Optional[List[str]] = Field(None, description="Specific recipients")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule delivery time")
    expires_at: Optional[datetime] = Field(None, description="Notification expiration time")

    @root_validator
    def validate_delivery(cls, values):
        """Validate delivery configuration."""
        scheduled_at = values.get('scheduled_at')
        expires_at = values.get('expires_at')

        if scheduled_at and expires_at and scheduled_at >= expires_at:
            raise ValueError('expires_at must be after scheduled_at')

        return values


class NotificationDeliveryResponse(BaseSchema):
    """Response schema for notification delivery."""
    notification_id: str
    status: str
    message: str
    channels: List[str]
    delivered_count: int
    failed_count: int
    scheduled_at: Optional[str]
    delivered_at: Optional[str]


# Notification Status Schemas
class NotificationStatusRequest(BaseSchema):
    """Request schema for checking notification status."""
    notification_id: str = Field(..., description="Notification ID")
    include_details: Optional[bool] = Field(False, description="Include delivery details")


class NotificationStatusResponse(BaseSchema):
    """Response schema for notification status."""
    notification_id: str
    status: str
    notification_type: str
    priority: str
    title: str
    created_at: str
    scheduled_at: Optional[str]
    delivered_at: Optional[str]
    delivery_attempts: int
    deliveries: List[Dict[str, Any]]


# Channel-Specific Schemas
class EmailChannelConfig(BaseSchema):
    """Email channel configuration."""
    smtp_server: str = Field(..., description="SMTP server address")
    smtp_port: int = Field(587, ge=1, le=65535, description="SMTP port")
    username: str = Field(..., description="SMTP username")
    password: str = Field(..., description="SMTP password")
    use_tls: bool = Field(True, description="Use TLS encryption")
    from_address: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender display name")


class WebhookChannelConfig(BaseSchema):
    """Webhook channel configuration."""
    url: str = Field(..., description="Webhook URL")
    method: str = Field("POST", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="HTTP headers")
    auth_type: Optional[str] = Field(None, description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    timeout: Optional[int] = Field(30, ge=1, le=300, description="Request timeout in seconds")
    retry_config: Optional[Dict[str, Any]] = Field(None, description="Retry configuration")


class SlackChannelConfig(BaseSchema):
    """Slack channel configuration."""
    webhook_url: str = Field(..., description="Slack webhook URL")
    channel: str = Field(..., description="Slack channel")
    username: Optional[str] = Field(None, description="Bot username")
    icon_emoji: Optional[str] = Field(None, description="Icon emoji")
    icon_url: Optional[str] = Field(None, description="Icon URL")


class DiscordChannelConfig(BaseSchema):
    """Discord channel configuration."""
    webhook_url: str = Field(..., description="Discord webhook URL")
    username: Optional[str] = Field(None, description="Bot username")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


# Template Schemas
class NotificationTemplate(BaseSchema):
    """Notification template configuration."""
    template_id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    notification_type: NotificationType = Field(..., description="Associated notification type")
    subject_template: Optional[str] = Field(None, description="Subject template")
    message_template: str = Field(..., description="Message template")
    variables: List[str] = Field(default_factory=list, description="Template variables")
    format: str = Field("text", description="Template format: text, html, markdown")
    channel_overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Channel-specific overrides")


class TemplateRenderRequest(BaseSchema):
    """Request schema for rendering a template."""
    template_id: str = Field(..., description="Template ID")
    variables: Dict[str, Any] = Field(..., description="Template variables")
    format: Optional[str] = Field(None, description="Output format")
    channel: Optional[DeliveryChannel] = Field(None, description="Target delivery channel")


class TemplateRenderResponse(BaseSchema):
    """Response schema for template rendering."""
    template_id: str
    rendered_subject: Optional[str]
    rendered_message: str
    format: str
    variables_used: List[str]
    variables_missing: List[str]


# Subscription Schemas
class NotificationSubscription(BaseSchema):
    """Notification subscription configuration."""
    user_id: str = Field(..., description="User ID")
    subscription_name: str = Field(..., min_length=1, max_length=100, description="Subscription name")
    notification_types: List[NotificationType] = Field(..., min_items=1, description="Subscribed notification types")
    platforms: Optional[List[str]] = Field(None, description="Subscribed platforms")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Subscription filters")
    channels: List[DeliveryChannel] = Field(..., min_items=1, description="Delivery channels")
    is_active: bool = Field(default=True, description="Whether subscription is active")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")


class SubscriptionCreateRequest(BaseSchema):
    """Request schema for creating a subscription."""
    subscription: NotificationSubscription
    validate_only: Optional[bool] = Field(False, description="Only validate, don't create")


class SubscriptionUpdateRequest(BaseSchema):
    """Request schema for updating a subscription."""
    subscription_name: Optional[str] = Field(None, min_length=1, max_length=100)
    notification_types: Optional[List[NotificationType]] = None
    platforms: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    channels: Optional[List[DeliveryChannel]] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


class SubscriptionResponse(BaseSchema):
    """Response schema for subscription operations."""
    subscription_id: str
    user_id: str
    subscription_name: str
    notification_types: List[str]
    platforms: Optional[List[str]]
    filters: Dict[str, Any]
    channels: List[str]
    is_active: bool
    preferences: Dict[str, Any]
    created_at: str
    updated_at: str


# Event-Triggered Notification Schemas
class NotificationRule(BaseSchema):
    """Event-triggered notification rule."""
    rule_id: str = Field(..., description="Rule identifier")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    event_type: str = Field(..., description="Event type that triggers notification")
    conditions: Dict[str, Any] = Field(..., description="Trigger conditions")
    actions: List[Dict[str, Any]] = Field(..., min_items=1, description="Notification actions")
    is_active: bool = Field(default=True, description="Whether rule is active")
    priority: int = Field(0, ge=0, le=100, description="Rule priority")


class RuleCreateRequest(BaseSchema):
    """Request schema for creating a notification rule."""
    rule: NotificationRule


class RuleUpdateRequest(BaseSchema):
    """Request schema for updating a notification rule."""
    name: Optional[str] = Field(None, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    conditions: Optional[Dict[str, Any]] = None
    actions: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100, description="Rule priority")


class RuleResponse(BaseSchema):
    """Response schema for notification rule operations."""
    rule_id: str
    name: str
    description: Optional[str]
    event_type: str
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    is_active: bool
    priority: int
    created_at: str
    updated_at: str


# Analytics and Monitoring Schemas
class NotificationAnalytics(BaseSchema):
    """Notification analytics data."""
    total_sent: int = Field(..., description="Total notifications sent")
    total_delivered: int = Field(..., description="Total notifications delivered")
    total_failed: int = Field(..., description="Total notifications failed")
    delivery_rate: float = Field(..., description="Delivery success rate")
    avg_delivery_time: float = Field(..., description="Average delivery time in seconds")
    channel_performance: Dict[str, Dict[str, Any]] = Field(..., description="Performance by channel")
    type_breakdown: Dict[str, Dict[str, Any]] = Field(..., description="Breakdown by notification type")
    hourly_distribution: Dict[int, int] = Field(..., description="Hourly distribution of notifications")


class NotificationMetricsRequest(BaseSchema):
    """Request schema for notification metrics."""
    date_from: datetime = Field(..., description="Start date")
    date_to: datetime = Field(..., description="End date")
    channels: Optional[List[DeliveryChannel]] = Field(None, description="Filter by channels")
    notification_types: Optional[List[NotificationType]] = Field(None, description="Filter by types")
    group_by: Optional[str] = Field(None, description="Grouping: channel, type, day, hour")


class NotificationMetricsResponse(BaseSchema):
    """Response schema for notification metrics."""
    analytics: NotificationAnalytics
    period: Dict[str, str]
    filters_applied: Dict[str, Any]


# Bulk Operations Schemas
class BulkNotificationRequest(BaseSchema):
    """Request schema for bulk notification operations."""
    notifications: List[NotificationDeliveryRequest] = Field(..., min_items=1, max_items=100, description="Notifications to send")
    parallel: Optional[bool] = Field(True, description="Send notifications in parallel")
    stop_on_error: Optional[bool] = Field(False, description="Stop on first error")
    rate_limit: Optional[Dict[str, Any]] = Field(None, description="Rate limiting for bulk send")


class BulkSubscriptionRequest(BaseSchema):
    """Request schema for bulk subscription operations."""
    subscriptions: List[NotificationSubscription] = Field(..., min_items=1, max_items=50, description="Subscriptions to create")
    validate_only: Optional[bool] = Field(False, description="Only validate, don't create")


# List and Filter Schemas
class NotificationListRequest(BaseSchema):
    """Request schema for listing notifications."""
    notification_type: Optional[NotificationType] = Field(None, description="Filter by notification type")
    priority: Optional[NotificationPriority] = Field(None, description="Filter by priority")
    status: Optional[DeliveryStatus] = Field(None, description="Filter by delivery status")
    channel: Optional[DeliveryChannel] = Field(None, description="Filter by channel")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    search: Optional[str] = Field(None, description="Search in title or message")
    skip: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class SubscriptionListRequest(BaseSchema):
    """Request schema for listing subscriptions."""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    notification_type: Optional[NotificationType] = Field(None, description="Filter by notification type")
    platform: Optional[str] = Field(None, description="Filter by platform")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    skip: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class RuleListRequest(BaseSchema):
    """Request schema for listing notification rules."""
    event_type: Optional[str] = Field(None, description="Filter by event type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    priority: Optional[int] = Field(None, ge=0, le=100, description="Filter by priority")
    skip: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of records to return")


# Error Schemas
class NotificationError(BaseSchema):
    """Schema for notification-related errors."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    notification_id: Optional[str] = Field(None, description="Associated notification ID")
    channel: Optional[DeliveryChannel] = Field(None, description="Associated delivery channel")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class TemplateError(BaseSchema):
    """Schema for template-related errors."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    template_id: Optional[str] = Field(None, description="Associated template ID")
    variables: Optional[List[str]] = Field(None, description="Problematic variables")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")