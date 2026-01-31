"""ProgressMetric model for tracking performance metrics and statistics.

This module defines the ProgressMetric SQLAlchemy model for collecting
and managing performance metrics, including response times, throughput,
and custom metrics for the progress tracking system.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Float,
    Integer,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ProgressMetric(Base):
    """Progress metric model for performance monitoring.

    This model stores performance metrics and statistics for the
    progress tracking system, including response times, throughput,
    and custom business metrics.
    """

    __tablename__ = "progress_metrics"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="指标ID",
    )
    metric_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="指标名称",
    )

    # Metric value
    value = Column(
        Float,
        nullable=False,
        comment="指标值",
    )
    unit = Column(
        String(20),
        comment="指标单位 (ms, seconds, count, percent, etc.)",
    )

    # Labels and dimensions
    labels = Column(
        JSONB,
        default=dict,
        comment="指标标签 (key-value pairs)",
    )
    dimensions = Column(
        JSONB,
        default=dict,
        comment="指标维度 (additional metadata)",
    )

    # Time information
    timestamp = Column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        comment="指标时间戳",
    )
    collection_time = Column(
        DateTime(timezone=True),
        default=func.now(),
        comment="数据收集时间",
    )

    # Metric metadata
    metric_metadata = Column(
        JSONB,
        default=dict,
        comment="指标元数据",
    )

    # Aggregation information
    is_aggregated = Column(
        Boolean,
        default=False,
        comment="是否为聚合数据",
    )
    aggregation_type = Column(
        String(20),
        comment="聚合类型 (sum, avg, max, min, count)",
    )
    aggregation_period = Column(
        String(20),
        comment="聚合周期 (1m, 5m, 1h, 1d, etc.)",
    )

    # Task association
    related_task_id = Column(
        String(100),
        index=True,
        comment="关联任务ID",
    )
    related_user_id = Column(
        String(100),
        index=True,
        comment="关联用户ID",
    )

    def __repr__(self) -> str:
        """Return string representation of the ProgressMetric."""
        return (
            f"<ProgressMetric(id={self.id}, name='{self.metric_name}', "
            f"value={self.value}, unit='{self.unit}', "
            f"timestamp='{self.timestamp}')>"
        )

    @property
    def is_response_time(self) -> bool:
        """Check if metric is a response time metric."""
        return self.metric_name.endswith("_response_time") or self.unit == "ms"

    @property
    def is_throughput(self) -> bool:
        """Check if metric is a throughput metric."""
        return self.metric_name.endswith("_throughput") or self.unit == "count"

    @property
    def is_percentage(self) -> bool:
        """Check if metric is a percentage."""
        return self.unit == "percent" or "rate" in self.metric_name.lower()

    @property
    def is_aggregated_data(self) -> bool:
        """Check if this is aggregated data."""
        return self.is_aggregated

    @property
    def has_labels(self) -> bool:
        """Check if metric has labels."""
        return bool(self.labels)

    @property
    def has_dimensions(self) -> bool:
        """Check if metric has dimensions."""
        return bool(self.dimensions)

    @property
    def label_count(self) -> int:
        """Get number of labels."""
        return len(self.labels) if self.labels else 0

    @property
    def dimension_count(self) -> int:
        """Get number of dimensions."""
        return len(self.dimensions) if self.dimensions else 0

    @property
    def age_seconds(self) -> int:
        """Get metric age in seconds."""
        if self.collection_time is None:
            return 0

        # Handle SQLAlchemy function expressions
        if hasattr(self.collection_time, 'compile'):
            return 0

        return int((datetime.utcnow() - self.collection_time).total_seconds())

    @property
    def value_as_integer(self) -> int:
        """Get metric value as integer if possible."""
        try:
            return int(self.value)
        except (ValueError, TypeError):
            return 0

    @property
    def value_as_string(self) -> str:
        """Get metric value as formatted string."""
        if self.unit == "ms":
            return f"{self.value:.2f}ms"
        elif self.unit == "seconds":
            return f"{self.value:.2f}s"
        elif self.unit == "percent":
            return f"{self.value:.1f}%"
        elif self.unit == "count":
            return f"{int(self.value)}"
        else:
            return f"{self.value}"

    def add_label(self, key: str, value: str) -> None:
        """Add a metric label.

        Args:
            key: Label key
            value: Label value
        """
        if not self.labels:
            self.labels = {}

        self.labels[key] = value

    def add_dimension(self, key: str, value: str) -> None:
        """Add a metric dimension.

        Args:
            key: Dimension key
            value: Dimension value
        """
        if not self.dimensions:
            self.dimensions = {}

        self.dimensions[key] = value

    def _datetime_to_iso(self, dt) -> str | None:
        """Convert datetime to ISO format string.

        Handles both Python datetime objects and SQLAlchemy function expressions.
        """
        if dt is None:
            return None
        # Check if it's a datetime object (has isoformat method)
        if hasattr(dt, 'isoformat'):
            return dt.isoformat()
        # For SQLAlchemy function expressions, return None (they'll be evaluated on database side)
        return None

    def to_dict(self) -> dict:
        """Convert ProgressMetric to dictionary."""
        return {
            "id": str(self.id),
            "metric_name": self.metric_name,
            "value": self.value,
            "unit": self.unit,
            "labels": self.labels or {},
            "dimensions": self.dimensions or {},
            "timestamp": self._datetime_to_iso(self.timestamp),
            "collection_time": self._datetime_to_iso(self.collection_time),
            "metadata": self.metric_metadata or {},
            "is_aggregated": self.is_aggregated,
            "aggregation_type": self.aggregation_type,
            "aggregation_period": self.aggregation_period,
            "related_task_id": self.related_task_id,
            "related_user_id": self.related_user_id,
            "is_response_time": self.is_response_time,
            "is_throughput": self.is_throughput,
            "is_percentage": self.is_percentage,
            "is_aggregated_data": self.is_aggregated_data,
            "has_labels": self.has_labels,
            "has_dimensions": self.has_dimensions,
            "label_count": self.label_count,
            "dimension_count": self.dimension_count,
            "age_seconds": self.age_seconds,
            "value_as_integer": self.value_as_integer,
            "value_as_string": self.value_as_string,
        }

    @classmethod
    def create_response_time_metric(
        cls,
        metric_name: str,
        response_time_ms: float,
        task_id: str = None,
        user_id: str = None,
        labels: dict = None,
    ) -> "ProgressMetric":
        """Create a response time metric.

        Args:
            metric_name: Metric name
            response_time_ms: Response time in milliseconds
            task_id: Optional related task ID
            user_id: Optional related user ID
            labels: Optional labels dictionary

        Returns:
            ProgressMetric: Response time metric instance
        """
        return cls(
            metric_name=metric_name,
            value=response_time_ms,
            unit="ms",
            labels=labels or {},
            related_task_id=task_id,
            related_user_id=user_id,
        )

    @classmethod
    def create_throughput_metric(
        cls,
        metric_name: str,
        count: float,
        time_period: str = "1m",
        task_id: str = None,
        user_id: str = None,
        labels: dict = None,
    ) -> "ProgressMetric":
        """Create a throughput metric.

        Args:
            metric_name: Metric name
            count: Count value
            time_period: Time period (1m, 5m, 1h, etc.)
            task_id: Optional related task ID
            user_id: Optional related user ID
            labels: Optional labels dictionary

        Returns:
            ProgressMetric: Throughput metric instance
        """
        return cls(
            metric_name=metric_name,
            value=count,
            unit="count",
            labels=labels or {},
            aggregation_period=time_period,
            related_task_id=task_id,
            related_user_id=user_id,
        )

    @classmethod
    def create_percentage_metric(
        cls,
        metric_name: str,
        percentage: float,
        task_id: str = None,
        user_id: str = None,
        labels: dict = None,
    ) -> "ProgressMetric":
        """Create a percentage metric.

        Args:
            metric_name: Metric name
            percentage: Percentage value (0-100)
            task_id: Optional related task ID
            user_id: Optional related user ID
            labels: Optional labels dictionary

        Returns:
            ProgressMetric: Percentage metric instance
        """
        return cls(
            metric_name=metric_name,
            value=max(0.0, min(100.0, percentage)),
            unit="percent",
            labels=labels or {},
            related_task_id=task_id,
            related_user_id=user_id,
        )

    @classmethod
    def create_websocket_connection_metric(
        cls,
        connection_count: int,
        user_id: str = None,
    ) -> "ProgressMetric":
        """Create a WebSocket connection count metric.

        Args:
            connection_count: Number of active connections
            user_id: Optional user ID

        Returns:
            ProgressMetric: WebSocket connection metric
        """
        return cls(
            metric_name="websocket_connections",
            value=connection_count,
            unit="count",
            labels={"type": "websocket"},
            related_user_id=user_id,
        )

    @classmethod
    def create_task_progress_metric(
        cls,
        task_id: str,
        progress: float,
        task_type: str = None,
    ) -> "ProgressMetric":
        """Create a task progress metric.

        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
            task_type: Optional task type

        Returns:
            ProgressMetric: Task progress metric
        """
        labels = {"task_id": task_id}
        if task_type:
            labels["task_type"] = task_type

        return cls(
            metric_name="task_progress",
            value=max(0.0, min(100.0, progress)),
            unit="percent",
            labels=labels,
            related_task_id=task_id,
        )

    @classmethod
    def create_error_rate_metric(
        cls,
        error_count: int,
        total_count: int,
        time_period: str = "1m",
        task_type: str = None,
    ) -> "ProgressMetric":
        """Create an error rate metric.

        Args:
            error_count: Number of errors
            total_count: Total number of operations
            time_period: Time period
            task_type: Optional task type

        Returns:
            ProgressMetric: Error rate metric
        """
        error_rate = (error_count / total_count * 100) if total_count > 0 else 0

        labels = {"period": time_period}
        if task_type:
            labels["task_type"] = task_type

        return cls(
            metric_name="error_rate",
            value=error_rate,
            unit="percent",
            labels=labels,
            aggregation_period=time_period,
        )


# Database indexes for performance optimization
Index("idx_progress_metrics_name", ProgressMetric.metric_name)
Index("idx_progress_metrics_timestamp", ProgressMetric.timestamp.desc())
Index("idx_progress_metrics_collection_time", ProgressMetric.collection_time.desc())
Index("idx_progress_metrics_related_task_id", ProgressMetric.related_task_id)
Index("idx_progress_metrics_related_user_id", ProgressMetric.related_user_id)

# Composite indexes for common queries
Index(
    "idx_progress_metrics_name_timestamp",
    ProgressMetric.metric_name,
    ProgressMetric.timestamp.desc(),
)
Index(
    "idx_progress_metrics_task_timestamp",
    ProgressMetric.related_task_id,
    ProgressMetric.timestamp.desc(),
)
Index(
    "idx_progress_metrics_user_timestamp",
    ProgressMetric.related_user_id,
    ProgressMetric.timestamp.desc(),
)
Index(
    "idx_progress_metrics_aggregated",
    ProgressMetric.is_aggregated,
    ProgressMetric.timestamp.desc(),
)
