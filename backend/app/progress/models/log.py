"""TaskLog model for detailed task execution logging.

This module defines the TaskLog SQLAlchemy model for collecting
and managing detailed logs of task execution, including log levels,
messages, context, and attachments.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class TaskLog(Base):
    """Task log model for detailed execution logging.

    This model stores detailed logs of task execution, including
    log levels, messages, context information, and stack traces.
    """

    __tablename__ = "task_logs"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="日志ID",
    )
    task_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="任务ID",
    )

    # Log level and message
    level = Column(
        String(10),
        nullable=False,
        comment="日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    message = Column(
        Text,
        nullable=False,
        comment="日志消息",
    )
    source = Column(
        String(50),
        comment="日志来源 (task_tracker, progress_manager, etc.)",
    )

    # Timestamp
    timestamp = Column(
        DateTime(timezone=True),
        default=func.now(),
        index=True,
        comment="日志时间戳",
    )

    # Context information
    context = Column(
        JSONB,
        default=dict,
        comment="日志上下文信息",
    )
    stack_trace = Column(
        Text,
        comment="堆栈跟踪信息",
    )

    # File storage
    log_file_path = Column(
        String(500),
        comment="日志文件路径",
    )
    attachments = Column(
        JSONB,
        default=list,
        comment="附件列表",
    )

    def __repr__(self) -> str:
        """Return string representation of the TaskLog."""
        return (
            f"<TaskLog(id={self.id}, task_id='{self.task_id}', "
            f"level='{self.level}', timestamp='{self.timestamp}')>"
        )

    @property
    def is_debug(self) -> bool:
        """Check if log level is DEBUG."""
        return self.level == "DEBUG"

    @property
    def is_info(self) -> bool:
        """Check if log level is INFO."""
        return self.level == "INFO"

    @property
    def is_warning(self) -> bool:
        """Check if log level is WARNING."""
        return self.level == "WARNING"

    @property
    def is_error(self) -> bool:
        """Check if log level is ERROR."""
        return self.level == "ERROR"

    @property
    def is_critical(self) -> bool:
        """Check if log level is CRITICAL."""
        return self.level == "CRITICAL"

    @property
    def is_error_level(self) -> bool:
        """Check if log level is ERROR or CRITICAL."""
        return self.level in ["ERROR", "CRITICAL"]

    @property
    def level_priority(self) -> int:
        """Get numeric priority for log level."""
        priorities = {
            "DEBUG": 10,
            "INFO": 20,
            "WARNING": 30,
            "ERROR": 40,
            "CRITICAL": 50,
        }
        return priorities.get(self.level, 0)

    @property
    def has_stack_trace(self) -> bool:
        """Check if log entry has stack trace."""
        return bool(self.stack_trace)

    @property
    def has_context(self) -> bool:
        """Check if log entry has context."""
        return bool(self.context)

    @property
    def has_attachments(self) -> bool:
        """Check if log entry has attachments."""
        return bool(self.attachments)

    @property
    def attachment_count(self) -> int:
        """Get number of attachments."""
        return len(self.attachments) if self.attachments else 0

    def to_dict(self) -> dict:
        """Convert TaskLog to dictionary."""
        return {
            "id": str(self.id),
            "task_id": self.task_id,
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "context": self.context or {},
            "stack_trace": self.stack_trace,
            "log_file_path": self.log_file_path,
            "attachments": self.attachments or [],
            "is_debug": self.is_debug,
            "is_info": self.is_info,
            "is_warning": self.is_warning,
            "is_error": self.is_error,
            "is_critical": self.is_critical,
            "is_error_level": self.is_error_level,
            "level_priority": self.level_priority,
            "has_stack_trace": self.has_stack_trace,
            "has_context": self.has_context,
            "has_attachments": self.has_attachments,
            "attachment_count": self.attachment_count,
        }

    @classmethod
    def create_log(
        cls,
        task_id: str,
        level: str,
        message: str,
        source: str = None,
        context: dict = None,
        stack_trace: str = None,
        attachments: list = None,
    ) -> "TaskLog":
        """Create a new TaskLog instance with specified parameters.

        Args:
            task_id: The task ID this log belongs to
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            source: Optional source component name
            context: Optional context dictionary
            stack_trace: Optional stack trace string
            attachments: Optional list of attachment references

        Returns:
            TaskLog: New TaskLog instance
        """
        return cls(
            task_id=task_id,
            level=level,
            message=message,
            source=source,
            context=context or {},
            stack_trace=stack_trace,
            attachments=attachments or [],
        )

    @classmethod
    def create_debug_log(
        cls,
        task_id: str,
        message: str,
        source: str = None,
        context: dict = None,
    ) -> "TaskLog":
        """Create a DEBUG level log entry.

        Args:
            task_id: The task ID
            message: Log message
            source: Optional source component
            context: Optional context dictionary

        Returns:
            TaskLog: DEBUG level log entry
        """
        return cls.create_log(
            task_id=task_id,
            level="DEBUG",
            message=message,
            source=source,
            context=context,
        )

    @classmethod
    def create_info_log(
        cls,
        task_id: str,
        message: str,
        source: str = None,
        context: dict = None,
    ) -> "TaskLog":
        """Create an INFO level log entry.

        Args:
            task_id: The task ID
            message: Log message
            source: Optional source component
            context: Optional context dictionary

        Returns:
            TaskLog: INFO level log entry
        """
        return cls.create_log(
            task_id=task_id,
            level="INFO",
            message=message,
            source=source,
            context=context,
        )

    @classmethod
    def create_warning_log(
        cls,
        task_id: str,
        message: str,
        source: str = None,
        context: dict = None,
    ) -> "TaskLog":
        """Create a WARNING level log entry.

        Args:
            task_id: The task ID
            message: Log message
            source: Optional source component
            context: Optional context dictionary

        Returns:
            TaskLog: WARNING level log entry
        """
        return cls.create_log(
            task_id=task_id,
            level="WARNING",
            message=message,
            source=source,
            context=context,
        )

    @classmethod
    def create_error_log(
        cls,
        task_id: str,
        message: str,
        source: str = None,
        context: dict = None,
        stack_trace: str = None,
    ) -> "TaskLog":
        """Create an ERROR level log entry.

        Args:
            task_id: The task ID
            message: Log message
            source: Optional source component
            context: Optional context dictionary
            stack_trace: Optional stack trace

        Returns:
            TaskLog: ERROR level log entry
        """
        return cls.create_log(
            task_id=task_id,
            level="ERROR",
            message=message,
            source=source,
            context=context,
            stack_trace=stack_trace,
        )

    @classmethod
    def create_critical_log(
        cls,
        task_id: str,
        message: str,
        source: str = None,
        context: dict = None,
        stack_trace: str = None,
    ) -> "TaskLog":
        """Create a CRITICAL level log entry.

        Args:
            task_id: The task ID
            message: Log message
            source: Optional source component
            context: Optional context dictionary
            stack_trace: Optional stack trace

        Returns:
            TaskLog: CRITICAL level log entry
        """
        return cls.create_log(
            task_id=task_id,
            level="CRITICAL",
            message=message,
            source=source,
            context=context,
            stack_trace=stack_trace,
        )


# Database indexes for performance optimization
Index("idx_task_logs_task_id", TaskLog.task_id)
Index("idx_task_logs_level", TaskLog.level)
Index("idx_task_logs_timestamp", TaskLog.timestamp.desc())
Index("idx_task_logs_source", TaskLog.source)

# Composite indexes for common queries
Index(
    "idx_task_logs_task_level",
    TaskLog.task_id,
    TaskLog.level,
)
Index(
    "idx_task_logs_task_timestamp",
    TaskLog.task_id,
    TaskLog.timestamp.desc(),
)
Index(
    "idx_task_logs_level_timestamp",
    TaskLog.level,
    TaskLog.timestamp.desc(),
)
