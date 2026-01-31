"""Data serialization utilities for progress tracking system.

This module provides serialization and deserialization functions for
progress tracking data models including tasks, logs, notifications,
and metrics.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from uuid import UUID

from ..models import TaskProgress, TaskLog, Notification, ProgressMetric

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SerializationError(Exception):
    """Raised when serialization fails."""
    pass


class DeserializationError(Exception):
    """Raised when deserialization fails."""
    pass


class BaseSerializer:
    """Base serializer with common functionality."""

    @staticmethod
    def to_json_serializable(obj: Any) -> Any:
        """Convert object to JSON-serializable format.

        Args:
            obj: Object to convert

        Returns:
            JSON-serializable object

        Raises:
            SerializationError: If conversion fails
        """
        try:
            if isinstance(obj, (datetime,)):
                return obj.isoformat()
            elif isinstance(obj, (UUID,)):
                return str(obj)
            elif isinstance(obj, (dict,)):
                return {k: BaseSerializer.to_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [BaseSerializer.to_json_serializable(item) for item in obj]
            else:
                return obj
        except Exception as e:
            logger.error(f"Serialization failed for {obj}: {e}")
            raise SerializationError(f"Failed to serialize object: {e}")

    @staticmethod
    def from_json_serializable(data: Any, target_type: Type[T]) -> T:
        """Convert JSON data to target type.

        Args:
            data: JSON data
            target_type: Target type

        Returns:
            Converted object

        Raises:
            DeserializationError: If conversion fails
        """
        try:
            if target_type == datetime and isinstance(data, str):
                return datetime.fromisoformat(data)
            elif target_type == UUID and isinstance(data, str):
                return UUID(data)
            else:
                return data
        except Exception as e:
            logger.error(f"Deserialization failed for {data}: {e}")
            raise DeserializationError(f"Failed to deserialize data: {e}")


class TaskProgressSerializer(BaseSerializer):
    """Serializer for TaskProgress model."""

    @staticmethod
    def serialize(task_progress: TaskProgress) -> Dict[str, Any]:
        """Serialize TaskProgress to dictionary.

        Args:
            task_progress: TaskProgress instance

        Returns:
            Serialized dictionary

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return {
                "id": str(task_progress.id),
                "task_id": task_progress.task_id,
                "user_id": task_progress.user_id,
                "task_type": task_progress.task_type,
                "task_name": task_progress.task_name,
                "description": task_progress.description,
                "progress": task_progress.progress,
                "status": task_progress.status,
                "current_step": task_progress.current_step,
                "total_steps": task_progress.total_steps,
                "estimated_duration": task_progress.estimated_duration,
                "started_at": BaseSerializer.to_json_serializable(task_progress.started_at),
                "completed_at": BaseSerializer.to_json_serializable(task_progress.completed_at),
                "updated_at": BaseSerializer.to_json_serializable(task_progress.updated_at),
                "result": BaseSerializer.to_json_serializable(task_progress.result),
                "error_message": task_progress.error_message,
                "error_details": BaseSerializer.to_json_serializable(task_progress.error_details),
                "metadata": BaseSerializer.to_json_serializable(task_progress.task_metadata),
                "tags": BaseSerializer.to_json_serializable(task_progress.tags),
                "retry_count": task_progress.retry_count,
                "view_count": task_progress.view_count,
                "duration_seconds": task_progress.duration_seconds,
                "estimated_remaining_seconds": task_progress.estimated_remaining_seconds,
                "progress_percentage": task_progress.progress_percentage,
                "steps_completed": task_progress.steps_completed,
                "is_pending": task_progress.is_pending,
                "is_running": task_progress.is_running,
                "is_completed": task_progress.is_completed,
                "is_failed": task_progress.is_failed,
                "is_paused": task_progress.is_paused,
                "is_cancelled": task_progress.is_cancelled,
                "is_active": task_progress.is_active,
                "is_finished": task_progress.is_finished,
            }
        except Exception as e:
            logger.error(f"TaskProgress serialization failed: {e}")
            raise SerializationError(f"Failed to serialize TaskProgress: {e}")

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> TaskProgress:
        """Deserialize dictionary to TaskProgress.

        Args:
            data: Serialized dictionary

        Returns:
            TaskProgress instance

        Raises:
            DeserializationError: If deserialization fails
        """
        try:
            # Create a minimal TaskProgress instance
            # Note: This is a simplified version for demonstration
            # In practice, you'd need to map all fields appropriately
            task_progress = TaskProgress(
                task_id=data.get("task_id"),
                user_id=data.get("user_id"),
                task_type=data.get("task_type"),
                task_name=data.get("task_name"),
                description=data.get("description"),
                progress=data.get("progress", 0.0),
                status=data.get("status", "pending"),
                current_step=data.get("current_step"),
                total_steps=data.get("total_steps"),
                estimated_duration=data.get("estimated_duration"),
                retry_count=data.get("retry_count", 0),
                view_count=data.get("view_count", 0),
            )
            return task_progress
        except Exception as e:
            logger.error(f"TaskProgress deserialization failed: {e}")
            raise DeserializationError(f"Failed to deserialize TaskProgress: {e}")


class LogEntrySerializer(BaseSerializer):
    """Serializer for TaskLog model."""

    @staticmethod
    def serialize(log_entry: TaskLog) -> Dict[str, Any]:
        """Serialize TaskLog to dictionary.

        Args:
            log_entry: TaskLog instance

        Returns:
            Serialized dictionary

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return {
                "id": str(log_entry.id),
                "task_id": log_entry.task_id,
                "level": log_entry.level,
                "message": log_entry.message,
                "source": log_entry.source,
                "timestamp": BaseSerializer.to_json_serializable(log_entry.timestamp),
                "context": BaseSerializer.to_json_serializable(log_entry.context),
                "stack_trace": log_entry.stack_trace,
                "log_file_path": log_entry.log_file_path,
                "attachments": BaseSerializer.to_json_serializable(log_entry.attachments),
                "is_debug": log_entry.is_debug,
                "is_info": log_entry.is_info,
                "is_warning": log_entry.is_warning,
                "is_error": log_entry.is_error,
                "is_critical": log_entry.is_critical,
                "is_error_level": log_entry.is_error_level,
                "level_priority": log_entry.level_priority,
                "has_stack_trace": log_entry.has_stack_trace,
                "has_context": log_entry.has_context,
                "has_attachments": log_entry.has_attachments,
                "attachment_count": log_entry.attachment_count,
            }
        except Exception as e:
            logger.error(f"TaskLog serialization failed: {e}")
            raise SerializationError(f"Failed to serialize TaskLog: {e}")

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> TaskLog:
        """Deserialize dictionary to TaskLog.

        Args:
            data: Serialized dictionary

        Returns:
            TaskLog instance

        Raises:
            DeserializationError: If deserialization fails
        """
        try:
            log_entry = TaskLog(
                task_id=data.get("task_id"),
                level=data.get("level"),
                message=data.get("message"),
                source=data.get("source"),
                context=data.get("context", {}),
                stack_trace=data.get("stack_trace"),
                attachments=data.get("attachments", []),
            )
            return log_entry
        except Exception as e:
            logger.error(f"TaskLog deserialization failed: {e}")
            raise DeserializationError(f"Failed to deserialize TaskLog: {e}")


class NotificationSerializer(BaseSerializer):
    """Serializer for Notification model."""

    @staticmethod
    def serialize(notification: Notification) -> Dict[str, Any]:
        """Serialize Notification to dictionary.

        Args:
            notification: Notification instance

        Returns:
            Serialized dictionary

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return {
                "id": str(notification.id),
                "user_id": notification.user_id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "priority": notification.priority,
                "channels": BaseSerializer.to_json_serializable(notification.channels),
                "related_task_id": notification.related_task_id,
                "action_url": notification.action_url,
                "created_at": BaseSerializer.to_json_serializable(notification.created_at),
                "read_at": BaseSerializer.to_json_serializable(notification.read_at),
                "expires_at": BaseSerializer.to_json_serializable(notification.expires_at),
                "delivery_status": BaseSerializer.to_json_serializable(notification.delivery_status),
                "retry_count": notification.retry_count or 0,
                "max_retries": notification.max_retries or 3,
                "metadata": BaseSerializer.to_json_serializable(notification.notification_metadata),
                "is_info": notification.is_info,
                "is_success": notification.is_success,
                "is_warning": notification.is_warning,
                "is_error": notification.is_error,
                "is_progress": notification.is_progress,
                "is_unread": notification.is_unread,
                "is_low_priority": notification.is_low_priority,
                "is_normal_priority": notification.is_normal_priority,
                "is_high_priority": notification.is_high_priority,
                "is_urgent_priority": notification.is_urgent_priority,
                "is_expired": notification.is_expired,
                "can_retry": notification.can_retry,
                "age_seconds": notification.age_seconds,
                "priority_value": notification.priority_value,
                "channel_count": notification.channel_count,
                "successful_deliveries": notification.successful_deliveries,
                "failed_deliveries": notification.failed_deliveries,
            }
        except Exception as e:
            logger.error(f"Notification serialization failed: {e}")
            raise SerializationError(f"Failed to serialize Notification: {e}")

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> Notification:
        """Deserialize dictionary to Notification.

        Args:
            data: Serialized dictionary

        Returns:
            Notification instance

        Raises:
            DeserializationError: If deserialization fails
        """
        try:
            notification = Notification(
                user_id=data.get("user_id"),
                title=data.get("title"),
                message=data.get("message"),
                notification_type=data.get("notification_type", "info"),
                priority=data.get("priority", "normal"),
                channels=data.get("channels", []),
                related_task_id=data.get("related_task_id"),
                action_url=data.get("action_url"),
                notification_metadata=data.get("metadata", {}),
            )
            return notification
        except Exception as e:
            logger.error(f"Notification deserialization failed: {e}")
            raise DeserializationError(f"Failed to deserialize Notification: {e}")


class MetricSerializer(BaseSerializer):
    """Serializer for ProgressMetric model."""

    @staticmethod
    def serialize(metric: ProgressMetric) -> Dict[str, Any]:
        """Serialize ProgressMetric to dictionary.

        Args:
            metric: ProgressMetric instance

        Returns:
            Serialized dictionary

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return {
                "id": str(metric.id),
                "metric_name": metric.metric_name,
                "value": metric.value,
                "unit": metric.unit,
                "labels": BaseSerializer.to_json_serializable(metric.labels),
                "dimensions": BaseSerializer.to_json_serializable(metric.dimensions),
                "timestamp": BaseSerializer.to_json_serializable(metric.timestamp),
                "collection_time": BaseSerializer.to_json_serializable(metric.collection_time),
                "metadata": BaseSerializer.to_json_serializable(metric.metric_metadata),
                "is_aggregated": metric.is_aggregated,
                "aggregation_type": metric.aggregation_type,
                "aggregation_period": metric.aggregation_period,
                "related_task_id": metric.related_task_id,
                "related_user_id": metric.related_user_id,
                "is_response_time": metric.is_response_time,
                "is_throughput": metric.is_throughput,
                "is_percentage": metric.is_percentage,
                "is_aggregated_data": metric.is_aggregated_data,
                "has_labels": metric.has_labels,
                "has_dimensions": metric.has_dimensions,
                "label_count": metric.label_count,
                "dimension_count": metric.dimension_count,
                "age_seconds": metric.age_seconds,
                "value_as_integer": metric.value_as_integer,
                "value_as_string": metric.value_as_string,
            }
        except Exception as e:
            logger.error(f"ProgressMetric serialization failed: {e}")
            raise SerializationError(f"Failed to serialize ProgressMetric: {e}")

    @staticmethod
    def deserialize(data: Dict[str, Any]) -> ProgressMetric:
        """Deserialize dictionary to ProgressMetric.

        Args:
            data: Serialized dictionary

        Returns:
            ProgressMetric instance

        Raises:
            DeserializationError: If deserialization fails
        """
        try:
            metric = ProgressMetric(
                metric_name=data.get("metric_name"),
                value=data.get("value"),
                unit=data.get("unit"),
                labels=data.get("labels", {}),
                dimensions=data.get("dimensions", {}),
                related_task_id=data.get("related_task_id"),
                related_user_id=data.get("related_user_id"),
                metric_metadata=data.get("metadata", {}),
                is_aggregated=data.get("is_aggregated", False),
                aggregation_type=data.get("aggregation_type"),
                aggregation_period=data.get("aggregation_period"),
            )
            return metric
        except Exception as e:
            logger.error(f"ProgressMetric deserialization failed: {e}")
            raise DeserializationError(f"Failed to deserialize ProgressMetric: {e}")


class WebSocketMessageSerializer(BaseSerializer):
    """Serializer for WebSocket messages."""

    @staticmethod
    def serialize(message: Dict[str, Any]) -> str:
        """Serialize WebSocket message to JSON string.

        Args:
            message: Message dictionary

        Returns:
            JSON string

        Raises:
            SerializationError: If serialization fails
        """
        try:
            return json.dumps(BaseSerializer.to_json_serializable(message))
        except Exception as e:
            logger.error(f"WebSocket message serialization failed: {e}")
            raise SerializationError(f"Failed to serialize WebSocket message: {e}")

    @staticmethod
    def deserialize(json_string: str) -> Dict[str, Any]:
        """Deserialize JSON string to message dictionary.

        Args:
            json_string: JSON string

        Returns:
            Message dictionary

        Raises:
            DeserializationError: If deserialization fails
        """
        try:
            data = json.loads(json_string)
            return BaseSerializer.to_json_serializable(data)
        except Exception as e:
            logger.error(f"WebSocket message deserialization failed: {e}")
            raise DeserializationError(f"Failed to deserialize WebSocket message: {e}")


# Convenience functions
def serialize_task_progress(task_progress: TaskProgress) -> Dict[str, Any]:
    """Serialize TaskProgress to dictionary.

    Args:
        task_progress: TaskProgress instance

    Returns:
        Serialized dictionary
    """
    return TaskProgressSerializer.serialize(task_progress)


def deserialize_task_progress(data: Dict[str, Any]) -> TaskProgress:
    """Deserialize dictionary to TaskProgress.

    Args:
        data: Serialized dictionary

    Returns:
        TaskProgress instance
    """
    return TaskProgressSerializer.deserialize(data)


def serialize_log_entry(log_entry: TaskLog) -> Dict[str, Any]:
    """Serialize TaskLog to dictionary.

    Args:
        log_entry: TaskLog instance

    Returns:
        Serialized dictionary
    """
    return LogEntrySerializer.serialize(log_entry)


def deserialize_log_entry(data: Dict[str, Any]) -> TaskLog:
    """Deserialize dictionary to TaskLog.

    Args:
        data: Serialized dictionary

    Returns:
        TaskLog instance
    """
    return LogEntrySerializer.deserialize(data)


def serialize_notification(notification: Notification) -> Dict[str, Any]:
    """Serialize Notification to dictionary.

    Args:
        notification: Notification instance

    Returns:
        Serialized dictionary
    """
    return NotificationSerializer.serialize(notification)


def deserialize_notification(data: Dict[str, Any]) -> Notification:
    """Deserialize dictionary to Notification.

    Args:
        data: Serialized dictionary

    Returns:
        Notification instance
    """
    return NotificationSerializer.deserialize(data)


def serialize_metric(metric: ProgressMetric) -> Dict[str, Any]:
    """Serialize ProgressMetric to dictionary.

    Args:
        metric: ProgressMetric instance

    Returns:
        Serialized dictionary
    """
    return MetricSerializer.serialize(metric)


def deserialize_metric(data: Dict[str, Any]) -> ProgressMetric:
    """Deserialize dictionary to ProgressMetric.

    Args:
        data: Serialized dictionary

    Returns:
        ProgressMetric instance
    """
    return MetricSerializer.deserialize(data)


def serialize_websocket_message(message: Dict[str, Any]) -> str:
    """Serialize WebSocket message to JSON string.

    Args:
        message: Message dictionary

    Returns:
        JSON string
    """
    return WebSocketMessageSerializer.serialize(message)


def deserialize_websocket_message(json_string: str) -> Dict[str, Any]:
    """Deserialize JSON string to message dictionary.

    Args:
        json_string: JSON string

    Returns:
        Message dictionary
    """
    return WebSocketMessageSerializer.deserialize(json_string)
