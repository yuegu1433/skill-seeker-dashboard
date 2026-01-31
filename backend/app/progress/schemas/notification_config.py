"""Notification configuration schemas for progress tracking system.

This module contains Pydantic models for configuring notification rules,
channels, templates, and user settings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Notification Channels
# =============================================================================

class NotificationChannel(BaseModel):
    """Configuration for a notification channel."""

    name: str = Field(..., description="渠道名称")
    enabled: bool = Field(default=True, description="是否启用")
    priority: str = Field(default="normal", description="优先级")
    rate_limit: Optional[int] = Field(None, description="频率限制(条/分钟)")
    retry_policy: Dict[str, Any] = Field(default_factory=dict, description="重试策略")
    config: Dict[str, Any] = Field(default_factory=dict, description="渠道配置")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤规则")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# =============================================================================
# Notification Templates
# =============================================================================

class NotificationTemplate(BaseModel):
    """Template for notification messages."""

    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    template_type: str = Field(..., description="模板类型")
    channel: str = Field(..., description="适用渠道")
    subject: Optional[str] = Field(None, description="标题模板")
    body: str = Field(..., description="内容模板")
    variables: Optional[List[str]] = Field(None, description="模板变量")
    formatting: Optional[Dict[str, Any]] = Field(None, description="格式配置")
    is_active: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Notification Rules
# =============================================================================

class NotificationRule(BaseModel):
    """Rule for notification triggering."""

    rule_id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    enabled: bool = Field(default=True, description="是否启用")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    actions: List[Dict[str, Any]] = Field(..., description="执行动作")
    priority: int = Field(default=1, description="规则优先级")
    cooldown: Optional[int] = Field(None, description="冷却时间(秒)")
    max_executions: Optional[int] = Field(None, description="最大执行次数")
    execution_count: int = Field(default=0, description="已执行次数")
    last_execution: Optional[datetime] = Field(None, description="最后执行时间")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Notification Configuration
# =============================================================================

class NotificationConfig(BaseModel):
    """Overall notification system configuration."""

    config_id: str = Field(..., description="配置ID")
    name: str = Field(..., description="配置名称")
    enabled: bool = Field(default=True, description="是否启用")
    default_channels: List[str] = Field(default_factory=list, description="默认渠道")
    global_settings: Dict[str, Any] = Field(default_factory=dict, description="全局设置")
    rate_limits: Dict[str, int] = Field(default_factory=dict, description="全局频率限制")
    retry_settings: Dict[str, Any] = Field(default_factory=dict, description="全局重试设置")
    template_settings: Dict[str, Any] = Field(default_factory=dict, description="模板设置")
    security_settings: Dict[str, Any] = Field(default_factory=dict, description="安全设置")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# User Notification Settings
# =============================================================================

class UserNotificationSettings(BaseModel):
    """User-specific notification settings."""

    user_id: str = Field(..., description="用户ID")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="用户偏好")
    enabled_channels: List[str] = Field(default_factory=list, description="启用的渠道")
    channel_settings: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="渠道设置")
    quiet_hours: Optional[Dict[str, Any]] = Field(None, description="免打扰时间")
    task_filters: Optional[Dict[str, Any]] = Field(None, description="任务过滤")
    frequency_limits: Dict[str, int] = Field(default_factory=dict, description="频率限制")
    auto_mark_read: bool = Field(default=True, description="自动标记已读")
    grouping_enabled: bool = Field(default=True, description="启用消息分组")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# API Request Models
# =============================================================================

class NotificationCreateRequest(BaseModel):
    """Request model for creating notifications."""

    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., min_length=1, max_length=200, description="通知标题")
    message: str = Field(..., min_length=1, max_length=2000, description="通知内容")
    notification_type: str = Field(..., description="通知类型")
    priority: str = Field(default="normal", description="优先级")
    channels: List[str] = Field(default_factory=list, description="发送渠道")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    action_url: Optional[str] = Field(None, description="操作链接")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    template_id: Optional[str] = Field(None, description="模板ID")
    template_vars: Optional[Dict[str, Any]] = Field(None, description="模板变量")
    immediate: bool = Field(default=True, description="立即发送")
    scheduled_for: Optional[datetime] = Field(None, description="计划发送时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class NotificationUpdateRequest(BaseModel):
    """Request model for updating notifications."""

    notification_id: str = Field(..., description="通知ID")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="通知标题")
    message: Optional[str] = Field(None, min_length=1, max_length=2000, description="通知内容")
    priority: Optional[str] = Field(None, description="优先级")
    channels: Optional[List[str]] = Field(None, description="发送渠道")
    action_url: Optional[str] = Field(None, description="操作链接")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class NotificationListRequest(BaseModel):
    """Request model for listing notifications."""

    user_id: Optional[str] = Field(None, description="用户ID(过滤)")
    notification_type: Optional[str] = Field(None, description="通知类型(过滤)")
    priority: Optional[str] = Field(None, description="优先级(过滤)")
    status: Optional[str] = Field(None, description="状态(过滤)")
    related_task_id: Optional[str] = Field(None, description="关联任务ID(过滤)")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(default=50, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class NotificationMarkReadRequest(BaseModel):
    """Request model for marking notifications as read."""

    notification_ids: List[str] = Field(..., description="通知ID列表")
    mark_all: bool = Field(default=False, description="标记全部")
    user_id: Optional[str] = Field(None, description="用户ID")
    older_than_days: Optional[int] = Field(None, description="标记超过指定天数的通知")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# =============================================================================
# API Response Models
# =============================================================================

class NotificationResponse(BaseModel):
    """Response model for notification information."""

    id: str = Field(..., description="通知ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    notification_type: str = Field(..., description="通知类型")
    is_read: bool = Field(..., description="是否已读")
    priority: str = Field(..., description="优先级")
    channels: List[str] = Field(..., description="发送渠道")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    action_url: Optional[str] = Field(None, description="操作链接")
    created_at: datetime = Field(..., description="创建时间")
    read_at: Optional[datetime] = Field(None, description="阅读时间")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    delivery_status: Dict[str, Any] = Field(..., description="送达状态")
    retry_count: int = Field(..., description="重试次数")
    max_retries: int = Field(..., description="最大重试次数")
    metadata: Dict[str, Any] = Field(..., description="通知元数据")
    is_info: bool = Field(..., description="是否为信息类型")
    is_success: bool = Field(..., description="是否为成功类型")
    is_warning: bool = Field(..., description="是否为警告类型")
    is_error: bool = Field(..., description="是否为错误类型")
    is_progress: bool = Field(..., description="是否为进度类型")
    is_unread: bool = Field(..., description="是否未读")
    is_low_priority: bool = Field(..., description="是否为低优先级")
    is_normal_priority: bool = Field(..., description="是否为普通优先级")
    is_high_priority: bool = Field(..., description="是否为高优先级")
    is_urgent_priority: bool = Field(..., description="是否为紧急优先级")
    is_expired: bool = Field(..., description="是否已过期")
    can_retry: bool = Field(..., description="是否可以重试")
    age_seconds: int = Field(..., description="年龄(秒)")
    priority_value: int = Field(..., description="优先级值")
    channel_count: int = Field(..., description="渠道数量")
    successful_deliveries: int = Field(..., description="成功送达数")
    failed_deliveries: int = Field(..., description="失败送达数")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class NotificationListResponse(BaseModel):
    """Response model for notification list."""

    notifications: List[NotificationResponse] = Field(..., description="通知列表")
    total: int = Field(..., description="总数量")
    unread_count: int = Field(..., description="未读数量")
    limit: int = Field(..., description="返回数量限制")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class NotificationStatsResponse(BaseModel):
    """Response model for notification statistics."""

    total_notifications: int = Field(..., description="总通知数")
    unread_notifications: int = Field(..., description="未读通知数")
    read_notifications: int = Field(..., description="已读通知数")
    sent_notifications: int = Field(..., description="已发送通知数")
    failed_notifications: int = Field(..., description="失败通知数")
    pending_notifications: int = Field(..., description="待发送通知数")
    notifications_by_type: Dict[str, int] = Field(..., description="按类型统计")
    notifications_by_priority: Dict[str, int] = Field(..., description="按优先级统计")
    notifications_by_channel: Dict[str, int] = Field(..., description="按渠道统计")
    average_delivery_time: Optional[float] = Field(None, description="平均送达时间(秒)")
    success_rate: float = Field(..., description="成功率")
    last_notification: Optional[datetime] = Field(None, description="最后通知时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}
