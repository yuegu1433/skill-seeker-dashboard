"""Task monitoring system for storage operations.

This module provides monitoring capabilities for Celery tasks including
task status tracking, execution monitoring, and performance metrics.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from celery import current_app
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class TaskStatus:
    """Task execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


class TaskMetrics:
    """Task execution metrics."""

    def __init__(self):
        """Initialize task metrics."""
        self.total_tasks = 0
        self.successful_tasks = 0
        self.failed_tasks = 0
        self.retried_tasks = 0
        self.revoked_tasks = 0
        self.start_times: Dict[str, datetime] = {}
        self.end_times: Dict[str, datetime] = {}
        self.durations: Dict[str, float] = {}
        self.error_counts: Dict[str, int] = {}
        self.task_types: Dict[str, int] = {}

    def record_task_start(self, task_id: str, task_type: str):
        """Record task start.

        Args:
            task_id: Task ID
            task_type: Type of task
        """
        self.start_times[task_id] = datetime.utcnow()
        self.task_types[task_type] = self.task_types.get(task_type, 0) + 1

    def record_task_end(
        self,
        task_id: str,
        status: str,
        duration: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """Record task end.

        Args:
            task_id: Task ID
            status: Task status
            duration: Task duration in seconds
            error: Error message if any
        """
        self.end_times[task_id] = datetime.utcnow()

        # Calculate duration if not provided
        if duration is None and task_id in self.start_times:
            duration = (self.end_times[task_id] - self.start_times[task_id]).total_seconds()

        if duration is not None:
            self.durations[task_id] = duration

        # Update counters
        self.total_tasks += 1

        if status == TaskStatus.SUCCESS:
            self.successful_tasks += 1
        elif status == TaskStatus.FAILURE:
            self.failed_tasks += 1
            if error:
                self.error_counts[error] = self.error_counts.get(error, 0) + 1
        elif status == TaskStatus.RETRY:
            self.retried_tasks += 1
        elif status == TaskStatus.REVOKED:
            self.revoked_tasks += 1

    def get_success_rate(self) -> float:
        """Get success rate percentage.

        Returns:
            Success rate as percentage
        """
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100

    def get_average_duration(self) -> float:
        """Get average task duration.

        Returns:
            Average duration in seconds
        """
        if not self.durations:
            return 0.0
        return sum(self.durations.values()) / len(self.durations)

    def get_median_duration(self) -> float:
        """Get median task duration.

        Returns:
            Median duration in seconds
        """
        if not self.durations:
            return 0.0
        durations = sorted(self.durations.values())
        mid = len(durations) // 2
        if len(durations) % 2 == 0:
            return (durations[mid - 1] + durations[mid]) / 2
        else:
            return durations[mid]

    def get_error_summary(self) -> List[Dict[str, Any]]:
        """Get error summary.

        Returns:
            List of error summaries
        """
        return [
            {"error": error, "count": count}
            for error, count in sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)
        ]

    def get_task_type_summary(self) -> List[Dict[str, Any]]:
        """Get task type summary.

        Returns:
            List of task type summaries
        """
        return [
            {"task_type": task_type, "count": count}
            for task_type, count in sorted(self.task_types.items(), key=lambda x: x[1], reverse=True)
        ]


class StorageTaskMonitor:
    """Monitor for storage system tasks.

    Provides monitoring capabilities for Celery tasks including
    status tracking, execution monitoring, and performance metrics.
    """

    def __init__(self, celery_app=None):
        """Initialize task monitor.

        Args:
            celery_app: Celery application instance
        """
        self.celery_app = celery_app or current_app
        self.metrics = TaskMetrics()
        self.task_history: List[Dict[str, Any]] = []
        self.max_history_size = 10000

        # Active tasks tracking
        self.active_tasks: Dict[str, Dict[str, Any]] = {}

        logger.info("StorageTaskMonitor initialized")

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a specific task.

        Args:
            task_id: Task ID

        Returns:
            Task status information
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)

            status_info = {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None,
                "info": result.info if hasattr(result, 'info') else {},
            }

            # Add duration if available
            if task_id in self.metrics.start_times:
                start_time = self.metrics.start_times[task_id]
                end_time = self.metrics.end_times.get(task_id, datetime.utcnow())
                duration = (end_time - start_time).total_seconds()
                status_info["duration_seconds"] = duration

            return status_info

        except Exception as e:
            logger.error(f"Failed to get task status for {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": TaskStatus.UNKNOWN,
                "error": str(e),
            }

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get all active tasks.

        Returns:
            List of active tasks
        """
        active = []

        for task_id, task_info in list(self.active_tasks.items()):
            # Check if task is still running
            status_info = self.get_task_status(task_id)

            if status_info["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                active.append({
                    **task_info,
                    **status_info,
                })
            else:
                # Task finished, remove from active
                self.active_tasks.pop(task_id, None)

        return active

    def get_task_history(
        self,
        task_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get task execution history.

        Args:
            task_type: Optional task type filter
            status: Optional status filter
            limit: Maximum number of records to return

        Returns:
            List of task history records
        """
        history = self.task_history

        # Apply filters
        if task_type:
            history = [h for h in history if h.get("task_type") == task_type]

        if status:
            history = [h for h in history if h.get("status") == status]

        # Sort by start time (newest first)
        history.sort(key=lambda x: x.get("start_time", datetime.min), reverse=True)

        # Apply limit
        return history[:limit]

    def get_metrics(self) -> Dict[str, Any]:
        """Get task execution metrics.

        Returns:
            Dictionary with metrics
        """
        return {
            "total_tasks": self.metrics.total_tasks,
            "successful_tasks": self.metrics.successful_tasks,
            "failed_tasks": self.metrics.failed_tasks,
            "retried_tasks": self.metrics.retried_tasks,
            "revoked_tasks": self.metrics.revoked_tasks,
            "success_rate_percent": round(self.metrics.get_success_rate(), 2),
            "average_duration_seconds": round(self.metrics.get_average_duration(), 2),
            "median_duration_seconds": round(self.metrics.get_median_duration(), 2),
            "error_summary": self.metrics.get_error_summary(),
            "task_type_summary": self.metrics.get_task_type_summary(),
            "active_tasks_count": len(self.get_active_tasks()),
        }

    def monitor_task(
        self,
        task_id: str,
        task_type: str,
        start_time: Optional[datetime] = None,
    ):
        """Start monitoring a task.

        Args:
            task_id: Task ID
            task_type: Type of task
            start_time: Task start time
        """
        self.active_tasks[task_id] = {
            "task_id": task_id,
            "task_type": task_type,
            "start_time": start_time or datetime.utcnow(),
            "status": TaskStatus.RUNNING,
        }

        self.metrics.record_task_start(task_id, task_type)

        logger.debug(f"Started monitoring task {task_id} ({task_type})")

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None,
        duration: Optional[float] = None,
    ):
        """Update task status.

        Args:
            task_id: Task ID
            status: Task status
            result: Task result
            error: Error message if any
            duration: Task duration in seconds
        """
        # Get current time
        end_time = datetime.utcnow()

        # Calculate duration if not provided
        if duration is None and task_id in self.metrics.start_times:
            duration = (end_time - self.metrics.start_times[task_id]).total_seconds()

        # Record metrics
        self.metrics.record_task_end(task_id, status, duration, error)

        # Add to history
        task_info = self.active_tasks.get(task_id, {})
        history_record = {
            "task_id": task_id,
            "task_type": task_info.get("task_type", "unknown"),
            "status": status,
            "start_time": task_info.get("start_time", end_time),
            "end_time": end_time,
            "duration_seconds": duration,
            "result": result,
            "error": error,
        }

        self.add_to_history(history_record)

        # Update active tasks
        if status in [TaskStatus.SUCCESS, TaskStatus.FAILURE, TaskStatus.REVOKED]:
            self.active_tasks.pop(task_id, None)

        logger.debug(f"Updated task {task_id} status to {status}")

    def add_to_history(self, record: Dict[str, Any]):
        """Add record to history.

        Args:
            record: History record
        """
        self.task_history.append(record)

        # Limit history size
        if len(self.task_history) > self.max_history_size:
            self.task_history = self.task_history[-self.max_history_size:]

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        """Get all pending tasks.

        Returns:
            List of pending tasks
        """
        try:
            # Get active tasks from Celery
            inspect = self.celery_app.control.inspect()
            active_tasks = inspect.active()

            pending = []

            if active_tasks:
                for worker, tasks in active_tasks.items():
                    for task in tasks:
                        pending.append({
                            "worker": worker,
                            "task_id": task.get("id"),
                            "task_name": task.get("name"),
                            "args": task.get("args", []),
                            "kwargs": task.get("kwargs", {}),
                            "time_start": task.get("time_start"),
                            "hostname": task.get("hostname"),
                        })

            return pending

        except Exception as e:
            logger.error(f"Failed to get pending tasks: {e}")
            return []

    def get_worker_status(self) -> Dict[str, Any]:
        """Get worker status.

        Returns:
            Dictionary with worker status
        """
        try:
            inspect = self.celery_app.control.inspect()

            # Get stats
            stats = inspect.stats() or {}

            # Get active tasks
            active = inspect.active() or {}

            # Get scheduled tasks
            scheduled = inspect.scheduled() or {}

            # Get reserved tasks
            reserved = inspect.reserved() or {}

            worker_status = {}

            for worker, worker_stats in stats.items():
                worker_status[worker] = {
                    "stats": worker_stats,
                    "active_count": len(active.get(worker, [])),
                    "scheduled_count": len(scheduled.get(worker, [])),
                    "reserved_count": len(reserved.get(worker, [])),
                    "status": "online" if worker_stats else "offline",
                }

            return worker_status

        except Exception as e:
            logger.error(f"Failed to get worker status: {e}")
            return {}

    def get_task_statistics(
        self,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """Get task statistics for a time range.

        Args:
            time_range_hours: Number of hours to include

        Returns:
            Dictionary with statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

        # Filter history by time range
        recent_history = [
            record for record in self.task_history
            if record.get("start_time", datetime.min) >= cutoff_time
        ]

        # Calculate statistics
        total_tasks = len(recent_history)
        successful_tasks = len([r for r in recent_history if r.get("status") == TaskStatus.SUCCESS])
        failed_tasks = len([r for r in recent_history if r.get("status") == TaskStatus.FAILURE])

        # Calculate average duration
        durations = [r.get("duration_seconds") for r in recent_history if r.get("duration_seconds")]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Get error breakdown
        errors = {}
        for record in recent_history:
            if record.get("status") == TaskStatus.FAILURE:
                error = record.get("error", "Unknown error")
                errors[error] = errors.get(error, 0) + 1

        return {
            "time_range_hours": time_range_hours,
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate_percent": round((successful_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2),
            "average_duration_seconds": round(avg_duration, 2),
            "error_breakdown": errors,
            "task_type_breakdown": {
                record.get("task_type", "unknown"): recent_history.count(record)
                for record in recent_history
            },
        }

    def cleanup_finished_tasks(self, max_age_hours: int = 168):
        """Clean up finished tasks from active tracking.

        Args:
            max_age_hours: Maximum age in hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        finished_tasks = []

        for task_id, task_info in list(self.active_tasks.items()):
            start_time = task_info.get("start_time")
            if start_time and start_time < cutoff_time:
                finished_tasks.append(task_id)

        for task_id in finished_tasks:
            self.active_tasks.pop(task_id, None)
            logger.debug(f"Cleaned up finished task {task_id}")

        return len(finished_tasks)

    def reset_metrics(self):
        """Reset all metrics."""
        self.metrics = TaskMetrics()
        logger.info("Task metrics reset")

    def export_metrics(self) -> Dict[str, Any]:
        """Export all metrics for analysis.

        Returns:
            Dictionary with all metrics and history
        """
        return {
            "metrics": self.get_metrics(),
            "active_tasks": self.get_active_tasks(),
            "recent_history": self.get_task_history(limit=1000),
            "worker_status": self.get_worker_status(),
            "statistics_24h": self.get_task_statistics(24),
            "statistics_7d": self.get_task_statistics(168),
        }


# Global monitor instance
_global_monitor = None


def get_task_monitor() -> StorageTaskMonitor:
    """Get global task monitor instance.

    Returns:
        StorageTaskMonitor instance
    """
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = StorageTaskMonitor()
    return _global_monitor


def set_task_monitor(monitor: StorageTaskMonitor):
    """Set global task monitor instance.

    Args:
        monitor: Task monitor instance
    """
    global _global_monitor
    _global_monitor = monitor
