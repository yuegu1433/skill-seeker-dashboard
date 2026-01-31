"""Progress operation schemas for real-time progress tracking API.

This module contains Pydantic models for validating progress tracking
operations including task creation, progress updates, log management,
and metric collection.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field


# =============================================================================
# Task Progress Operations
# =============================================================================

class CreateTaskRequest(BaseModel):
    """Request model for creating a new task."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    user_id: str = Field(..., min_length=1, max_length=100, description="用户ID")
    task_type: str = Field(..., min_length=1, max_length=50, description="任务类型")
    task_name: str = Field(..., min_length=1, max_length=200, description="任务名称")
    description: Optional[str] = Field(None, max_length=1000, description="任务描述")
    estimated_duration: Optional[int] = Field(None, ge=1, le=86400, description="预计耗时(秒)")
    total_steps: Optional[int] = Field(None, ge=1, le=1000, description="总步骤数")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任务元数据")
    tags: Optional[List[str]] = Field(default_factory=list, description="任务标签")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class UpdateProgressRequest(BaseModel):
    """Request model for updating task progress."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    progress: float = Field(..., ge=0.0, le=100.0, description="进度百分比")
    status: Optional[str] = Field(None, description="任务状态")
    current_step: Optional[str] = Field(None, max_length=100, description="当前步骤")
    message: Optional[str] = Field(None, max_length=500, description="状态消息")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    force_update: bool = Field(default=False, description="强制更新状态")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class UpdateStatusRequest(BaseModel):
    """Request model for updating task status only."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    status: str = Field(..., description="任务状态")
    message: Optional[str] = Field(None, max_length=500, description="状态消息")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")
    force_update: bool = Field(default=False, description="强制更新状态")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class TaskProgressResponse(BaseModel):
    """Response model for task progress information."""

    id: str = Field(..., description="进度记录ID")
    task_id: str = Field(..., description="任务ID")
    user_id: str = Field(..., description="用户ID")
    task_type: str = Field(..., description="任务类型")
    task_name: str = Field(..., description="任务名称")
    description: Optional[str] = Field(None, description="任务描述")
    progress: float = Field(..., description="进度百分比")
    status: str = Field(..., description="任务状态")
    current_step: Optional[str] = Field(None, description="当前步骤")
    total_steps: Optional[int] = Field(None, description="总步骤数")
    estimated_duration: Optional[int] = Field(None, description="预计耗时(秒)")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    result: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任务结果")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="错误详情")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="任务元数据")
    tags: Optional[List[str]] = Field(default_factory=list, description="任务标签")
    retry_count: int = Field(default=0, description="重试次数")
    view_count: int = Field(default=0, description="查看次数")
    duration_seconds: int = Field(default=0, description="执行时长(秒)")
    estimated_remaining_seconds: int = Field(default=0, description="预计剩余时间(秒)")
    progress_percentage: str = Field(..., description="进度百分比字符串")
    steps_completed: int = Field(default=0, description="已完成步骤数")
    is_pending: bool = Field(..., description="是否等待中")
    is_running: bool = Field(..., description="是否运行中")
    is_completed: bool = Field(..., description="是否已完成")
    is_failed: bool = Field(..., description="是否失败")
    is_paused: bool = Field(..., description="是否暂停")
    is_cancelled: bool = Field(..., description="是否已取消")
    is_active: bool = Field(..., description="是否活跃")
    is_finished: bool = Field(..., description="是否已完成(成功/失败/取消)")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class TaskStatusResponse(BaseModel):
    """Response model for task status summary."""

    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: float = Field(..., description="进度百分比")
    current_step: Optional[str] = Field(None, description="当前步骤")
    message: Optional[str] = Field(None, description="状态消息")
    estimated_remaining: Optional[int] = Field(None, description="预计剩余时间(秒)")
    last_updated: datetime = Field(..., description="最后更新时间")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskListRequest(BaseModel):
    """Request model for listing tasks."""

    user_id: Optional[str] = Field(None, description="用户ID(过滤)")
    task_type: Optional[str] = Field(None, description="任务类型(过滤)")
    status: Optional[str] = Field(None, description="任务状态(过滤)")
    tags: Optional[List[str]] = Field(None, description="标签(过滤)")
    limit: int = Field(default=50, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    sort_by: str = Field(default="updated_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class TaskListResponse(BaseModel):
    """Response model for task list."""

    tasks: List[TaskProgressResponse] = Field(..., description="任务列表")
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="返回数量限制")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class TaskHistoryRequest(BaseModel):
    """Request model for task history."""

    user_id: Optional[str] = Field(None, description="用户ID(过滤)")
    task_type: Optional[str] = Field(None, description="任务类型(过滤)")
    status: Optional[List[str]] = Field(None, description="任务状态列表(过滤)")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    limit: int = Field(default=100, ge=1, le=5000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class TaskHistoryResponse(BaseModel):
    """Response model for task history."""

    tasks: List[TaskProgressResponse] = Field(..., description="历史任务列表")
    total: int = Field(..., description="总数量")
    statistics: Dict[str, Any] = Field(..., description="统计信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class TaskCancelRequest(BaseModel):
    """Request model for cancelling a task."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    reason: Optional[str] = Field(None, max_length=500, description="取消原因")


class TaskPauseRequest(BaseModel):
    """Request model for pausing a task."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    reason: Optional[str] = Field(None, max_length=500, description="暂停原因")


class TaskResumeRequest(BaseModel):
    """Request model for resuming a task."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")


# =============================================================================
# Log Operations
# =============================================================================

class CreateLogRequest(BaseModel):
    """Request model for creating a log entry."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., min_length=1, max_length=5000, description="日志消息")
    source: Optional[str] = Field(None, max_length=50, description="日志来源")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    attachments: Optional[List[str]] = Field(default_factory=list, description="附件列表")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class LogEntryResponse(BaseModel):
    """Response model for log entry."""

    id: str = Field(..., description="日志ID")
    task_id: str = Field(..., description="任务ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., description="日志消息")
    source: Optional[str] = Field(None, description="日志来源")
    timestamp: datetime = Field(..., description="时间戳")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上下文信息")
    stack_trace: Optional[str] = Field(None, description="堆栈跟踪")
    log_file_path: Optional[str] = Field(None, description="日志文件路径")
    attachments: Optional[List[str]] = Field(default_factory=list, description="附件列表")
    is_debug: bool = Field(..., description="是否为DEBUG级别")
    is_info: bool = Field(..., description="是否为INFO级别")
    is_warning: bool = Field(..., description="是否为WARNING级别")
    is_error: bool = Field(..., description="是否为ERROR级别")
    is_critical: bool = Field(..., description="是否为CRITICAL级别")
    is_error_level: bool = Field(..., description="是否为错误级别")
    level_priority: int = Field(..., description="级别优先级")
    has_stack_trace: bool = Field(..., description="是否有堆栈跟踪")
    has_context: bool = Field(..., description="是否有上下文")
    has_attachments: bool = Field(..., description="是否有附件")
    attachment_count: int = Field(..., description="附件数量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class LogListRequest(BaseModel):
    """Request model for listing logs."""

    task_id: Optional[str] = Field(None, description="任务ID(过滤)")
    level: Optional[List[str]] = Field(None, description="日志级别列表(过滤)")
    source: Optional[str] = Field(None, description="日志来源(过滤)")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    search: Optional[str] = Field(None, description="搜索关键词")
    limit: int = Field(default=100, ge=1, le=1000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    sort_order: str = Field(default="desc", description="排序方向")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class LogListResponse(BaseModel):
    """Response model for log list."""

    logs: List[LogEntryResponse] = Field(..., description="日志列表")
    total: int = Field(..., description="总数量")
    limit: int = Field(..., description="返回数量限制")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class LogFilterRequest(BaseModel):
    """Request model for log filtering."""

    task_id: Optional[str] = Field(None, description="任务ID(过滤)")
    levels: Optional[List[str]] = Field(None, description="日志级别列表(过滤)")
    sources: Optional[List[str]] = Field(None, description="来源列表(过滤)")
    date_range: Optional[Dict[str, datetime]] = Field(None, description="时间范围")
    search_terms: Optional[List[str]] = Field(None, description="搜索词列表")
    has_context: Optional[bool] = Field(None, description="是否包含上下文")
    has_stack_trace: Optional[bool] = Field(None, description="是否包含堆栈跟踪")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class LogExportRequest(BaseModel):
    """Request model for log export."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    format: str = Field(..., description="导出格式")
    filters: Optional[LogFilterRequest] = Field(None, description="过滤条件")
    include_context: bool = Field(default=True, description="是否包含上下文")
    include_stack_trace: bool = Field(default=False, description="是否包含堆栈跟踪")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class LogExportResponse(BaseModel):
    """Response model for log export."""

    export_id: str = Field(..., description="导出任务ID")
    task_id: str = Field(..., description="任务ID")
    format: str = Field(..., description="导出格式")
    status: str = Field(..., description="导出状态")
    download_url: Optional[str] = Field(None, description="下载URL")
    file_size: Optional[int] = Field(None, description="文件大小")
    record_count: Optional[int] = Field(None, description="记录数量")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    error: Optional[str] = Field(None, description="错误信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Metric Operations
# =============================================================================

class CreateMetricRequest(BaseModel):
    """Request model for creating a metric."""

    metric_name: str = Field(..., min_length=1, max_length=100, description="指标名称")
    value: float = Field(..., description="指标值")
    unit: Optional[str] = Field(None, max_length=20, description="指标单位")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="指标标签")
    dimensions: Optional[Dict[str, str]] = Field(default_factory=dict, description="指标维度")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    related_user_id: Optional[str] = Field(None, description="关联用户ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="指标元数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class MetricResponse(BaseModel):
    """Response model for metric information."""

    id: str = Field(..., description="指标ID")
    metric_name: str = Field(..., description="指标名称")
    value: float = Field(..., description="指标值")
    unit: Optional[str] = Field(None, description="指标单位")
    labels: Optional[Dict[str, str]] = Field(default_factory=dict, description="指标标签")
    dimensions: Optional[Dict[str, str]] = Field(default_factory=dict, description="指标维度")
    timestamp: datetime = Field(..., description="指标时间戳")
    collection_time: datetime = Field(..., description="收集时间")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="指标元数据")
    is_aggregated: bool = Field(..., description="是否为聚合数据")
    aggregation_type: Optional[str] = Field(None, description="聚合类型")
    aggregation_period: Optional[str] = Field(None, description="聚合周期")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    related_user_id: Optional[str] = Field(None, description="关联用户ID")
    is_response_time: bool = Field(..., description="是否为响应时间指标")
    is_throughput: bool = Field(..., description="是否为吞吐量指标")
    is_percentage: bool = Field(..., description="是否为百分比指标")
    is_aggregated_data: bool = Field(..., description="是否为聚合数据")
    has_labels: bool = Field(..., description="是否有标签")
    has_dimensions: bool = Field(..., description="是否有维度")
    label_count: int = Field(..., description="标签数量")
    dimension_count: int = Field(..., description="维度数量")
    age_seconds: int = Field(..., description="年龄(秒)")
    value_as_integer: int = Field(..., description="整数值")
    value_as_string: str = Field(..., description="格式化值")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MetricQueryRequest(BaseModel):
    """Request model for metric queries."""

    metric_names: Optional[List[str]] = Field(None, description="指标名称列表")
    labels: Optional[Dict[str, str]] = Field(None, description="标签过滤")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    related_task_id: Optional[str] = Field(None, description="关联任务ID")
    related_user_id: Optional[str] = Field(None, description="关联用户ID")
    limit: int = Field(default=1000, ge=1, le=10000, description="返回数量限制")
    offset: int = Field(default=0, ge=0, description="偏移量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MetricQueryResponse(BaseModel):
    """Response model for metric query results."""

    metrics: List[MetricResponse] = Field(..., description="指标列表")
    total: int = Field(..., description="总数量")
    query_info: Dict[str, Any] = Field(..., description="查询信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class MetricAggregateRequest(BaseModel):
    """Request model for metric aggregation."""

    metric_names: List[str] = Field(..., description="指标名称列表")
    aggregation_type: str = Field(..., description="聚合类型")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    period: Optional[str] = Field(None, description="聚合周期")
    labels: Optional[Dict[str, str]] = Field(None, description="标签过滤")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class MetricAggregateResponse(BaseModel):
    """Response model for metric aggregation results."""

    aggregation_type: str = Field(..., description="聚合类型")
    period: Optional[str] = Field(None, description="聚合周期")
    results: List[Dict[str, Any]] = Field(..., description="聚合结果")
    summary: Dict[str, Any] = Field(..., description="汇总信息")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# =============================================================================
# Additional Request Models for Missing Imports
# =============================================================================

class CreateLogEntryRequest(BaseModel):
    """Request model for creating a log entry."""

    task_id: str = Field(..., min_length=1, max_length=100, description="任务ID")
    user_id: str = Field(..., min_length=1, max_length=100, description="用户ID")
    level: str = Field(..., description="日志级别")
    message: str = Field(..., max_length=1000, description="日志消息")
    details: Optional[Dict[str, Any]] = Field(default_factory=dict, description="日志详情")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class CreateNotificationRequest(BaseModel):
    """Request model for creating a notification."""

    user_id: str = Field(..., min_length=1, max_length=100, description="用户ID")
    title: str = Field(..., max_length=200, description="通知标题")
    message: str = Field(..., max_length=1000, description="通知消息")
    notification_type: str = Field(..., description="通知类型")
    priority: str = Field(default="normal", description="优先级")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class TaskQueryParams(BaseModel):
    """Query parameters for task operations."""

    user_id: Optional[str] = Field(None, description="用户ID")
    task_type: Optional[str] = Field(None, description="任务类型")
    status: Optional[str] = Field(None, description="任务状态")
    tags: Optional[List[str]] = Field(None, description="标签")
    limit: int = Field(default=50, ge=1, le=1000, description="限制数量")
    offset: int = Field(default=0, ge=0, description="偏移量")
    sort_by: str = Field(default="updated_at", description="排序字段")
    sort_order: str = Field(default="desc", description="排序方向")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class LogQueryParams(BaseModel):
    """Query parameters for log operations."""

    task_id: Optional[str] = Field(None, description="任务ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    level: Optional[str] = Field(None, description="日志级别")
    date_from: Optional[datetime] = Field(None, description="开始时间")
    date_to: Optional[datetime] = Field(None, description="结束时间")
    limit: int = Field(default=100, ge=1, le=1000, description="限制数量")
    offset: int = Field(default=0, ge=0, description="偏移量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class NotificationQueryParams(BaseModel):
    """Query parameters for notification operations."""

    user_id: Optional[str] = Field(None, description="用户ID")
    notification_type: Optional[str] = Field(None, description="通知类型")
    is_read: Optional[bool] = Field(None, description="是否已读")
    priority: Optional[str] = Field(None, description="优先级")
    limit: int = Field(default=50, ge=1, le=1000, description="限制数量")
    offset: int = Field(default=0, ge=0, description="偏移量")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BulkUpdateRequest(BaseModel):
    """Request model for bulk update operations."""

    task_ids: List[str] = Field(..., description="任务ID列表")
    status: Optional[str] = Field(None, description="状态")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="元数据")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True


class BulkLogRequest(BaseModel):
    """Request model for bulk log operations."""

    logs: List[CreateLogEntryRequest] = Field(..., description="日志条目列表")

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
