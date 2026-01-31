"""WebSocket message schemas for real-time progress tracking.

This module contains Pydantic models for validating WebSocket messages
used in real-time communication between client and server.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Base Message Types
# =============================================================================

class WebSocketMessage(BaseModel):
    """Base WebSocket message model."""

    message_type: str = Field(..., description="消息类型")
    message_id: Optional[str] = Field(None, description="消息ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="消息时间戳")
    source: Optional[str] = Field(None, description="消息来源")
    target: Optional[str] = Field(None, description="消息目标")
    correlation_id: Optional[str] = Field(None, description="关联ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    priority: str = Field(default="normal", description="消息优先级")
    retry_count: int = Field(default=0, description="重试次数")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="消息元数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Progress Update Messages
# =============================================================================

class ProgressUpdateMessage(WebSocketMessage):
    """Message for progress updates."""

    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    progress: float = Field(..., description="进度百分比")
    status: str = Field(..., description="任务状态")
    current_step: Optional[str] = Field(None, description="当前步骤")
    total_steps: Optional[int] = Field(None, description="总步骤数")
    message: Optional[str] = Field(None, description="状态消息")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")
    speed: Optional[float] = Field(None, description="处理速度")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# =============================================================================
# Log Messages
# =============================================================================

class LogMessage(WebSocketMessage):
    """Message for log entries."""

    task_id: str = Field(..., description="任务ID")
    log_id: str = Field(..., description="日志ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    source: Optional[str] = Field(None, description="日志来源")
    timestamp: datetime = Field(..., description="日志时间戳")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    attachments: Optional[List[str]] = Field(None, description="附件列表")
    source_line: Optional[int] = Field(None, description="源码行号")
    source_file: Optional[str] = Field(None, description="源码文件")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Notification Messages
# =============================================================================

class NotificationMessage(WebSocketMessage):
    """Message for notifications."""

    notification_id: str = Field(..., description="通知ID")
    user_id: str = Field(..., description="用户ID")
    title: str = Field(..., description="通知标题")
    message: str = Field(..., description="通知内容")
    notification_type: str = Field(..., description="通知类型")
    priority: str = Field(default="normal", description="优先级")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    action_url: Optional[str] = Field(None, description="操作链接")
    channels: List[str] = Field(default_factory=list, description="发送渠道")
    metadata: Optional[Dict[str, Any]] = Field(None, description="通知元数据")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    auto_hide: bool = Field(default=False, description="自动隐藏")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Connection Management Messages
# =============================================================================

class ConnectionMessage(WebSocketMessage):
    """Message for connection management."""

    connection_id: str = Field(..., description="连接ID")
    action: str = Field(..., description="连接动作")
    status: str = Field(..., description="连接状态")
    client_info: Optional[Dict[str, Any]] = Field(None, description="客户端信息")
    server_info: Optional[Dict[str, Any]] = Field(None, description="服务器信息")
    error: Optional[str] = Field(None, description="错误信息")
    reconnect_attempts: int = Field(default=0, description="重连尝试次数")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# =============================================================================
# Error Messages
# =============================================================================

class ErrorMessage(WebSocketMessage):
    """Message for error handling."""

    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_type: str = Field(default="general", description="错误类型")
    task_id: Optional[str] = Field(None, description="关联任务ID")
    user_id: Optional[str] = Field(None, description="关联用户ID")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="错误时间")
    severity: str = Field(default="error", description="严重程度")
    recoverable: bool = Field(default=True, description="是否可恢复")
    suggestions: Optional[List[str]] = Field(None, description="解决建议")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Heartbeat Messages
# =============================================================================

class HeartbeatMessage(WebSocketMessage):
    """Message for connection heartbeat."""

    connection_id: str = Field(..., description="连接ID")
    client_time: datetime = Field(..., description="客户端时间")
    server_time: datetime = Field(default_factory=datetime.utcnow, description="服务器时间")
    latency: Optional[float] = Field(None, description="延迟(毫秒)")
    status: str = Field(default="alive", description="连接状态")
    load: Optional[Dict[str, float]] = Field(None, description="服务器负载信息")
    metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Subscription Messages
# =============================================================================

class SubscribeMessage(WebSocketMessage):
    """Message for subscribing to task updates."""

    subscription_id: str = Field(..., description="订阅ID")
    task_ids: List[str] = Field(..., description="订阅的任务ID列表")
    event_types: List[str] = Field(..., description="订阅的事件类型")
    filters: Optional[Dict[str, Any]] = Field(None, description="订阅过滤器")
    expires_at: Optional[datetime] = Field(None, description="订阅过期时间")
    max_events: Optional[int] = Field(None, description="最大事件数量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class UnsubscribeMessage(WebSocketMessage):
    """Message for unsubscribing from task updates."""

    subscription_id: str = Field(..., description="订阅ID")
    task_ids: Optional[List[str]] = Field(None, description="要取消订阅的任务ID列表")
    event_types: Optional[List[str]] = Field(None, description="要取消订阅的事件类型")
    reason: Optional[str] = Field(None, description="取消原因")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# =============================================================================
# Broadcast Messages
# =============================================================================

class BroadcastMessage(WebSocketMessage):
    """Message for broadcasting to multiple clients."""

    broadcast_id: str = Field(..., description="广播ID")
    broadcast_type: str = Field(..., description="广播类型")
    content: Dict[str, Any] = Field(..., description="广播内容")
    target_users: Optional[List[str]] = Field(None, description="目标用户列表")
    target_tasks: Optional[List[str]] = Field(None, description="目标任务列表")
    target_roles: Optional[List[str]] = Field(None, description="目标角色列表")
    priority: str = Field(default="normal", description="广播优先级")
    ttl: Optional[int] = Field(None, description="生存时间(秒)")
    delivery_status: Optional[Dict[str, str]] = Field(None, description="送达状态")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


# =============================================================================
# Status Change Messages
# =============================================================================

class StatusChangeMessage(WebSocketMessage):
    """Message for task status changes."""

    task_id: str = Field(..., description="任务ID")
    old_status: str = Field(..., description="旧状态")
    new_status: str = Field(..., description="新状态")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="状态变化时间")
    user_id: str = Field(..., description="用户ID")
    reason: Optional[str] = Field(None, description="状态变化原因")
    metadata: Optional[Dict[str, Any]] = Field(None, description="状态变化元数据")
    auto_transition: bool = Field(default=False, description="是否为自动转换")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Task Complete/Fail Messages
# =============================================================================

class TaskCompleteMessage(WebSocketMessage):
    """Message for task completion."""

    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    completion_time: datetime = Field(default_factory=datetime.utcnow, description="完成时间")
    duration: int = Field(..., description="执行时长(秒)")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    output_files: Optional[List[str]] = Field(None, description="输出文件列表")
    summary: Optional[str] = Field(None, description="完成摘要")
    metrics: Optional[Dict[str, Any]] = Field(None, description="性能指标")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskFailMessage(WebSocketMessage):
    """Message for task failure."""

    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    failure_time: datetime = Field(default_factory=datetime.utcnow, description="失败时间")
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误消息")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    retryable: bool = Field(default=False, description="是否可重试")
    recovery_suggestions: Optional[List[str]] = Field(None, description="恢复建议")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Metric Update Messages
# =============================================================================

class MetricUpdateMessage(WebSocketMessage):
    """Message for metric updates."""

    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: Optional[str] = Field(None, description="指标单位")
    labels: Optional[Dict[str, str]] = Field(None, description="指标标签")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="指标时间戳")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    related_user_id: Optional[str] = Field(None, description="关联用户ID")
    aggregation_type: Optional[str] = Field(None, description="聚合类型")
    source: Optional[str] = Field(None, description="指标来源")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}
