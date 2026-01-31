"""TaskProgress model for tracking real-time task progress.

This module defines the TaskProgress SQLAlchemy model for managing
real-time task progress tracking, including status updates, progress
percentage, and task metadata.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Float,
    Integer,
    Boolean,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TaskProgress(Base):
    """Task progress model for real-time progress tracking.

    This model tracks the progress of tasks in real-time, including
    progress percentage, current step, status, and metadata.
    """

    __tablename__ = "task_progress"

    # Primary key and identification
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="任务进度ID",
    )
    task_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="任务ID",
    )
    user_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="用户ID",
    )

    # Task information
    task_type = Column(
        String(50),
        nullable=False,
        comment="任务类型 (skill_creation, skill_deployment, file_processing, etc.)",
    )
    task_name = Column(
        String(200),
        nullable=False,
        comment="任务名称",
    )
    description = Column(
        Text,
        comment="任务描述",
    )

    # Progress information
    progress = Column(
        Float,
        default=0.0,
        comment="进度百分比 (0.0-100.0)",
    )
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="任务状态 (pending, running, completed, failed, paused, cancelled)",
    )
    current_step = Column(
        String(100),
        comment="当前步骤",
    )
    total_steps = Column(
        Integer,
        default=0,
        comment="总步骤数",
    )

    # Time information
    estimated_duration = Column(
        Integer,
        comment="预计耗时(秒)",
    )
    started_at = Column(
        DateTime(timezone=True),
        comment="开始时间",
    )
    completed_at = Column(
        DateTime(timezone=True),
        comment="完成时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # Result and error information
    result = Column(
        JSONB,
        default=dict,
        comment="任务结果",
    )
    error_message = Column(
        Text,
        comment="错误信息",
    )
    error_details = Column(
        JSONB,
        default=dict,
        comment="错误详情",
    )

    # Metadata
    task_metadata = Column(
        JSONB,
        default=dict,
        comment="任务元数据",
    )
    tags = Column(
        JSONB,
        default=list,
        comment="任务标签",
    )

    # Statistics
    retry_count = Column(
        Integer,
        default=0,
        comment="重试次数",
    )
    view_count = Column(
        Integer,
        default=0,
        comment="查看次数",
    )

    def __repr__(self) -> str:
        """Return string representation of the TaskProgress."""
        return (
            f"<TaskProgress(id={self.id}, task_id='{self.task_id}', "
            f"task_type='{self.task_type}', progress={self.progress}%, "
            f"status='{self.status}')>"
        )

    @property
    def is_pending(self) -> bool:
        """Check if task is pending."""
        return self.status == "pending"

    @property
    def is_running(self) -> bool:
        """Check if task is running."""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if task failed."""
        return self.status == "failed"

    @property
    def is_paused(self) -> bool:
        """Check if task is paused."""
        return self.status == "paused"

    @property
    def is_cancelled(self) -> bool:
        """Check if task is cancelled."""
        return self.status == "cancelled"

    @property
    def is_active(self) -> bool:
        """Check if task is active (running or pending)."""
        return self.status in ["pending", "running"]

    @property
    def is_finished(self) -> bool:
        """Check if task is finished (completed, failed, or cancelled)."""
        return self.status in ["completed", "failed", "cancelled"]

    @property
    def duration_seconds(self) -> int:
        """Get task duration in seconds."""
        if self.started_at is None:
            return 0

        end_time = self.completed_at or datetime.utcnow()

        # Handle SQLAlchemy function expressions
        if hasattr(self.started_at, 'compile'):
            # For unsaved instances with func.now(), return 0
            return 0

        return int((end_time - self.started_at).total_seconds())

    @property
    def estimated_remaining_seconds(self) -> int:
        """Get estimated remaining time in seconds."""
        if self.started_at is None or self.progress <= 0:
            return self.estimated_duration or 0

        # Handle SQLAlchemy function expressions
        if hasattr(self.started_at, 'compile'):
            return self.estimated_duration or 0

        elapsed = self.duration_seconds
        rate = self.progress / elapsed
        remaining_progress = 100.0 - self.progress

        return int(remaining_progress / rate) if rate > 0 else 0

    @property
    def progress_percentage(self) -> float:
        """Get progress as percentage string."""
        return f"{self.progress:.1f}%"

    @property
    def steps_completed(self) -> int:
        """Get number of completed steps."""
        if not self.total_steps or self.total_steps <= 0:
            return 0
        return int((self.progress / 100.0) * self.total_steps)

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
        """Convert TaskProgress to dictionary."""
        return {
            "id": str(self.id),
            "task_id": self.task_id,
            "user_id": self.user_id,
            "task_type": self.task_type,
            "task_name": self.task_name,
            "description": self.description,
            "progress": self.progress,
            "status": self.status,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "estimated_duration": self.estimated_duration,
            "started_at": self._datetime_to_iso(self.started_at),
            "completed_at": self._datetime_to_iso(self.completed_at),
            "updated_at": self._datetime_to_iso(self.updated_at),
            "result": self.result or {},
            "error_message": self.error_message,
            "error_details": self.error_details or {},
            "metadata": self.task_metadata or {},
            "tags": self.tags or [],
            "retry_count": self.retry_count,
            "view_count": self.view_count,
            "duration_seconds": self.duration_seconds,
            "estimated_remaining_seconds": self.estimated_remaining_seconds,
            "progress_percentage": self.progress_percentage,
            "steps_completed": self.steps_completed,
            "is_pending": self.is_pending,
            "is_running": self.is_running,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_paused": self.is_paused,
            "is_cancelled": self.is_cancelled,
            "is_active": self.is_active,
            "is_finished": self.is_finished,
        }

    def update_progress(
        self,
        progress: float,
        status: str = None,
        current_step: str = None,
        metadata: dict = None,
    ) -> None:
        """Update task progress.

        Args:
            progress: New progress percentage (0.0-100.0)
            status: New status (optional)
            current_step: New current step (optional)
            metadata: Additional metadata (optional)
        """
        self.progress = max(0.0, min(100.0, progress))

        if status:
            self.status = status

        if current_step:
            self.current_step = current_step

        if metadata:
            self.task_metadata = {**(self.task_metadata or {}), **metadata}

        if self.status == "running" and not self.started_at:
            self.started_at = func.now()

        if self.status in ["completed", "failed", "cancelled"] and not self.completed_at:
            self.completed_at = func.now()

        self.updated_at = func.now()


# Database indexes for performance optimization
Index("idx_task_progress_task_id", TaskProgress.task_id)
Index("idx_task_progress_user_id", TaskProgress.user_id)
Index("idx_task_progress_task_type", TaskProgress.task_type)
Index("idx_task_progress_status", TaskProgress.status)
Index("idx_task_progress_started_at", TaskProgress.started_at.desc())
Index("idx_task_progress_updated_at", TaskProgress.updated_at.desc())

# Composite indexes for common queries
Index(
    "idx_task_progress_user_status",
    TaskProgress.user_id,
    TaskProgress.status,
)
Index(
    "idx_task_progress_type_status",
    TaskProgress.task_type,
    TaskProgress.status,
)
Index(
    "idx_task_progress_status_updated",
    TaskProgress.status,
    TaskProgress.updated_at.desc(),
)
