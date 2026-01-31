"""Task monitoring and management for platform Celery tasks.

This module provides monitoring and management capabilities for
asynchronous platform tasks including tracking, statistics, and alerts.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID, uuid4

from celery import current_task
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task status enumeration."""
    PENDING = "pending"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class TaskInfo:
    """Task information representation."""
    task_id: str
    task_name: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    worker: Optional[str] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    retries: int = 0
    max_retries: int = 3
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        """Check if task is complete."""
        return self.status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate task duration in seconds."""
        if self.started_at:
            end_time = self.completed_at or datetime.utcnow()
            return (end_time - self.started_at).total_seconds()
        return None


@dataclass
class TaskStatistics:
    """Task statistics tracking."""
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    retry_attempts: int = 0
    avg_execution_time: float = 0.0
    success_rate: float = 0.0
    failure_rate: float = 0.0
    tasks_per_hour: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def update(self, task_info: TaskInfo):
        """Update statistics with task information."""
        self.total_tasks += 1

        if task_info.status == TaskStatus.SUCCESS:
            self.successful_tasks += 1
        elif task_info.status == TaskStatus.FAILURE:
            self.failed_tasks += 1
        elif task_info.status == TaskStatus.PENDING:
            self.pending_tasks += 1
        elif task_info.status in [TaskStatus.STARTED, TaskStatus.PROGRESS]:
            self.running_tasks += 1

        if task_info.retries > 0:
            self.retry_attempts += task_info.retries

        # Update execution time
        duration = task_info.duration_seconds
        if duration:
            self.avg_execution_time = (
                (self.avg_execution_time * (self.total_tasks - 1) + duration)
                / self.total_tasks
            )

        # Update rates
        if self.total_tasks > 0:
            self.success_rate = (self.successful_tasks / self.total_tasks) * 100
            self.failure_rate = (self.failed_tasks / self.total_tasks) * 100

        self.last_updated = datetime.utcnow()


class TaskMonitor:
    """Task monitoring and management system.

    Provides comprehensive monitoring including:
    - Task tracking and status monitoring
    - Statistics collection and analysis
    - Performance monitoring
    - Alert generation
    - Task management operations
    """

    def __init__(self):
        """Initialize task monitor."""
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.completed_tasks: Dict[str, TaskInfo] = {}
        self.task_history: List[TaskInfo] = []
        self.statistics = TaskStatistics()
        self.max_history_size = 1000

        # Event handlers
        self.event_handlers = {
            "task_started": [],
            "task_progress": [],
            "task_completed": [],
            "task_failed": [],
            "task_retried": []
        }

        # Task queue statistics
        self.queue_stats: Dict[str, Dict[str, Any]] = {}

    def track_task(
        self,
        task_id: str,
        task_name: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> TaskInfo:
        """Start tracking a task.

        Args:
            task_id: Task ID
            task_name: Task name
            args: Task arguments
            kwargs: Task keyword arguments
            priority: Task priority

        Returns:
            TaskInfo object
        """
        task_info = TaskInfo(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.PENDING,
            priority=priority,
            created_at=datetime.utcnow(),
            args=args or [],
            kwargs=kwargs or {}
        )

        self.active_tasks[task_id] = task_info
        self.statistics.update(task_info)

        # Emit event
        asyncio.create_task(self._emit_event("task_started", {
            "task_info": task_info
        }))

        logger.info(f"Started tracking task: {task_id} ({task_name})")
        return task_info

    def update_task_progress(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ) -> Optional[TaskInfo]:
        """Update task progress.

        Args:
            task_id: Task ID
            status: New task status
            progress: Progress information
            result: Task result
            error: Error message

        Returns:
            Updated TaskInfo or None if not found
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task not found for update: {task_id}")
            return None

        task_info = self.active_tasks[task_id]

        # Update status
        old_status = task_info.status
        task_info.status = status

        # Update timestamps
        if status == TaskStatus.STARTED and not task_info.started_at:
            task_info.started_at = datetime.utcnow()
        elif status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
            task_info.completed_at = datetime.utcnow()
            task_info.execution_time = task_info.duration_seconds

        # Update other fields
        if progress:
            task_info.progress = progress
        if result is not None:
            task_info.result = result
        if error:
            task_info.error = error

        # Update statistics
        self.statistics.update(task_info)

        # Emit events
        if status == TaskStatus.PROGRESS:
            asyncio.create_task(self._emit_event("task_progress", {
                "task_info": task_info,
                "progress": progress
            }))
        elif status == TaskStatus.SUCCESS:
            self._complete_task(task_id, task_info)
            asyncio.create_task(self._emit_event("task_completed", {
                "task_info": task_info,
                "result": result
            }))
        elif status == TaskStatus.FAILURE:
            self._complete_task(task_id, task_info)
            asyncio.create_task(self._emit_event("task_failed", {
                "task_info": task_info,
                "error": error
            }))
        elif status == TaskStatus.RETRY:
            task_info.retries += 1
            asyncio.create_task(self._emit_event("task_retried", {
                "task_info": task_info
            }))

        logger.info(f"Updated task {task_id}: {old_status.value} -> {status.value}")
        return task_info

    def _complete_task(self, task_id: str, task_info: TaskInfo):
        """Complete a task by moving it to completed tasks."""
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]

        self.completed_tasks[task_id] = task_info
        self.task_history.append(task_info)

        # Limit history size
        if len(self.task_history) > self.max_history_size:
            self.task_history = self.task_history[-self.max_history_size:]

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information.

        Args:
            task_id: Task ID

        Returns:
            TaskInfo or None if not found
        """
        return self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)

    def list_active_tasks(
        self,
        task_name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        priority: Optional[TaskPriority] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """List active tasks with optional filtering.

        Args:
            task_name: Filter by task name
            status: Filter by status
            priority: Filter by priority
            limit: Maximum number of tasks to return

        Returns:
            List of TaskInfo objects
        """
        tasks = list(self.active_tasks.values())

        # Apply filters
        if task_name:
            tasks = [t for t in tasks if t.task_name == task_name]

        if status:
            tasks = [t for t in tasks if t.status == status]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        # Sort by creation time (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    def list_completed_tasks(
        self,
        task_name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TaskInfo]:
        """List completed tasks with optional filtering.

        Args:
            task_name: Filter by task name
            status: Filter by status
            since: Filter by completion time
            limit: Maximum number of tasks to return

        Returns:
            List of TaskInfo objects
        """
        tasks = list(self.completed_tasks.values())

        # Apply filters
        if task_name:
            tasks = [t for t in tasks if t.task_name == task_name]

        if status:
            tasks = [t for t in tasks if t.status == status]

        if since:
            tasks = [t for t in tasks if t.completed_at and t.completed_at >= since]

        # Sort by completion time (newest first)
        tasks.sort(key=lambda t: t.completed_at or datetime.min, reverse=True)

        return tasks[:limit]

    def get_statistics(self) -> Dict[str, Any]:
        """Get task monitoring statistics.

        Returns:
            Statistics dictionary
        """
        return {
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "total_tasks": self.statistics.total_tasks,
            "successful_tasks": self.statistics.successful_tasks,
            "failed_tasks": self.statistics.failed_tasks,
            "pending_tasks": self.statistics.pending_tasks,
            "running_tasks": self.statistics.running_tasks,
            "retry_attempts": self.statistics.retry_attempts,
            "success_rate": self.statistics.success_rate,
            "failure_rate": self.statistics.failure_rate,
            "avg_execution_time": self.statistics.avg_execution_time,
            "last_updated": self.statistics.last_updated.isoformat()
        }

    def get_performance_metrics(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance metrics for a time window.

        Args:
            time_window_hours: Time window in hours

        Returns:
            Performance metrics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        # Filter tasks in time window
        recent_tasks = [
            task for task in self.task_history
            if task.completed_at and task.completed_at >= cutoff_time
        ]

        if not recent_tasks:
            return {
                "time_window_hours": time_window_hours,
                "task_count": 0,
                "avg_execution_time": 0,
                "success_rate": 0,
                "throughput_per_hour": 0
            }

        # Calculate metrics
        total_tasks = len(recent_tasks)
        successful_tasks = sum(1 for t in recent_tasks if t.status == TaskStatus.SUCCESS)
        failed_tasks = sum(1 for t in recent_tasks if t.status == TaskStatus.FAILURE)

        execution_times = [
            t.execution_time for t in recent_tasks
            if t.execution_time is not None
        ]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

        success_rate = (successful_tasks / total_tasks) * 100 if total_tasks > 0 else 0
        throughput_per_hour = total_tasks / time_window_hours

        return {
            "time_window_hours": time_window_hours,
            "task_count": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "avg_execution_time": avg_execution_time,
            "success_rate": success_rate,
            "throughput_per_hour": throughput_per_hour
        }

    def get_queue_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get queue statistics.

        Returns:
            Queue statistics dictionary
        """
        # This would be populated from Celery's inspect interface
        # For now, return empty statistics
        return self.queue_stats.copy()

    def cleanup_old_tasks(self, older_than_hours: int = 168):
        """Cleanup old completed tasks.

        Args:
            older_than_hours: Remove tasks older than this many hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        # Remove old completed tasks
        old_task_ids = [
            task_id for task_id, task in self.completed_tasks.items()
            if task.completed_at and task.completed_at < cutoff_time
        ]

        for task_id in old_task_ids:
            del self.completed_tasks[task_id]

        # Remove old history entries
        self.task_history = [
            task for task in self.task_history
            if task.completed_at is None or task.completed_at >= cutoff_time
        ]

        logger.info(f"Cleaned up {len(old_task_ids)} old tasks")

    def add_event_handler(self, event_type: str, handler):
        """Add event handler.

        Args:
            event_type: Event type
            handler: Event handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)

    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]):
        """Emit event to handlers.

        Args:
            event_type: Event type
            event_data: Event data
        """
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.warning(f"Event handler error: {str(e)}")


# Global task monitor instance
_task_monitor = None


def get_task_monitor() -> TaskMonitor:
    """Get or create task monitor instance."""
    global _task_monitor
    if _task_monitor is None:
        _task_monitor = TaskMonitor()
    return _task_monitor


# Utility functions for Celery task integration

def track_celery_task(task_func):
    """Decorator to track Celery tasks.

    Args:
        task_func: Celery task function

    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        task_monitor = get_task_monitor()
        task_id = task_func.request.id if hasattr(task_func, 'request') else str(uuid4())
        task_name = task_func.name if hasattr(task_func, 'name') else task_func.__name__

        # Track task
        task_info = task_monitor.track_task(
            task_id=task_id,
            task_name=task_name,
            args=args,
            kwargs=kwargs
        )

        try:
            # Execute task
            result = task_func(*args, **kwargs)

            # Update status
            task_monitor.update_task_progress(
                task_id=task_id,
                status=TaskStatus.SUCCESS,
                result=result
            )

            return result

        except Exception as e:
            # Update status with error
            task_monitor.update_task_progress(
                task_id=task_id,
                status=TaskStatus.FAILURE,
                error=str(e)
            )
            raise

    return wrapper


def update_celery_task_progress(progress: Dict[str, Any]):
    """Update Celery task progress.

    Args:
        progress: Progress information
    """
    task_monitor = get_task_monitor()

    if current_task:
        task_id = current_task.request.id
        task_monitor.update_task_progress(
            task_id=task_id,
            status=TaskStatus.PROGRESS,
            progress=progress
        )


def get_celery_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get Celery task status.

    Args:
        task_id: Task ID

    Returns:
        Task status dictionary
    """
    task_monitor = get_task_monitor()
    task_info = task_monitor.get_task_info(task_id)

    if not task_info:
        return None

    return {
        "task_id": task_info.task_id,
        "task_name": task_info.task_name,
        "status": task_info.status.value,
        "priority": task_info.priority.value,
        "created_at": task_info.created_at.isoformat(),
        "started_at": task_info.started_at.isoformat() if task_info.started_at else None,
        "completed_at": task_info.completed_at.isoformat() if task_info.completed_at else None,
        "duration_seconds": task_info.duration_seconds,
        "progress": task_info.progress,
        "result": task_info.result,
        "error": task_info.error,
        "retries": task_info.retries
    }


if __name__ == "__main__":
    # Example usage
    monitor = TaskMonitor()

    # Track a task
    task_info = monitor.track_task(
        task_id="test-task-1",
        task_name="test_task",
        args=["arg1", "arg2"],
        kwargs={"key": "value"}
    )

    # Update progress
    monitor.update_task_progress(
        task_id="test-task-1",
        status=TaskStatus.PROGRESS,
        progress={"step": "processing", "percentage": 50}
    )

    # Complete task
    monitor.update_task_progress(
        task_id="test-task-1",
        status=TaskStatus.SUCCESS,
        result={"output": "success"}
    )

    # Get statistics
    stats = monitor.get_statistics()
    print(json.dumps(stats, indent=2))