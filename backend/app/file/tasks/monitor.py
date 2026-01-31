"""Task Monitoring System.

This module provides monitoring and tracking for Celery tasks including
task status, progress tracking, metrics collection, and alerting.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import json
import psutil

from app.file.tasks import task_states, get_task_state, cleanup_task_state
from app.database.session import get_db

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


@dataclass
class TaskMetrics:
    """Task execution metrics."""

    task_id: str
    task_name: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    progress: float = 0.0
    memory_usage: int = 0
    cpu_usage: float = 0.0
    retries: int = 0
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "progress": self.progress,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage,
            "retries": self.retries,
            "error_message": self.error_message,
            "result": self.result,
        }


@dataclass
class TaskAlert:
    """Task alert information."""

    alert_id: str
    task_id: str
    alert_type: str  # timeout, error, resource_usage
    severity: str  # low, medium, high, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class TaskMonitor:
    """Task monitoring and tracking system."""

    def __init__(self):
        """Initialize task monitor."""
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.task_history: List[TaskMetrics] = []
        self.alerts: List[TaskAlert] = []
        self.monitors_running = False
        self.monitor_tasks: List[asyncio.Task] = []

    async def start_monitoring(self):
        """Start background monitoring tasks."""
        if self.monitors_running:
            return

        self.monitors_running = True

        # Start task status monitoring
        monitor_task = asyncio.create_task(self._monitor_tasks())
        self.monitor_tasks.append(monitor_task)

        # Start resource monitoring
        resource_task = asyncio.create_task(self._monitor_resources())
        self.monitor_tasks.append(resource_task)

        logger.info("Task monitoring started")

    async def stop_monitoring(self):
        """Stop background monitoring tasks."""
        self.monitors_running = False

        # Cancel all monitor tasks
        for task in self.monitor_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.monitor_tasks, return_exceptions=True)
        self.monitor_tasks.clear()

        logger.info("Task monitoring stopped")

    async def track_task_start(
        self,
        task_id: str,
        task_name: str,
        **kwargs,
    ):
        """Track task start.

        Args:
            task_id: Task ID
            task_name: Task name
            **kwargs: Additional task information
        """
        metrics = TaskMetrics(
            task_id=task_id,
            task_name=task_name,
            status=TaskStatus.STARTED,
            start_time=datetime.utcnow(),
        )

        self.active_tasks[task_id] = metrics

        logger.info(f"Started tracking task: {task_id} ({task_name})")

    async def track_task_progress(
        self,
        task_id: str,
        progress: float,
        status: Optional[TaskStatus] = None,
        **kwargs,
    ):
        """Track task progress.

        Args:
            task_id: Task ID
            progress: Progress percentage (0-100)
            status: Optional task status
            **kwargs: Additional progress information
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task not found for progress tracking: {task_id}")
            return

        metrics = self.active_tasks[task_id]
        metrics.progress = progress

        if status:
            metrics.status = status

        # Check for alert conditions
        await self._check_alerts(task_id, metrics)

    async def track_task_complete(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
    ):
        """Track task completion.

        Args:
            task_id: Task ID
            result: Task result
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task not found for completion tracking: {task_id}")
            return

        metrics = self.active_tasks[task_id]
        metrics.status = TaskStatus.COMPLETED
        metrics.end_time = datetime.utcnow()
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.result = result
        metrics.progress = 100.0

        # Move to history
        self.task_history.append(metrics)
        del self.active_tasks[task_id]

        logger.info(f"Completed task: {task_id} (duration: {metrics.duration:.2f}s)")

    async def track_task_failure(
        self,
        task_id: str,
        error_message: str,
        retries: int = 0,
    ):
        """Track task failure.

        Args:
            task_id: Task ID
            error_message: Error message
            retries: Number of retries
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task not found for failure tracking: {task_id}")
            return

        metrics = self.active_tasks[task_id]
        metrics.status = TaskStatus.FAILED
        metrics.end_time = datetime.utcnow()
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.error_message = error_message
        metrics.retries = retries

        # Create alert
        await self._create_alert(
            task_id=task_id,
            alert_type="error",
            severity="high" if retries > 2 else "medium",
            message=f"Task failed: {error_message}",
        )

        # Move to history
        self.task_history.append(metrics)
        del self.active_tasks[task_id]

        logger.error(f"Failed task: {task_id} (error: {error_message})")

    async def get_task_status(self, task_id: str) -> Optional[TaskMetrics]:
        """Get task status.

        Args:
            task_id: Task ID

        Returns:
            Task metrics or None
        """
        # Check active tasks
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]

        # Check history
        for task in self.task_history:
            if task.task_id == task_id:
                return task

        return None

    async def get_active_tasks(self) -> List[TaskMetrics]:
        """Get all active tasks.

        Returns:
            List of active task metrics
        """
        return list(self.active_tasks.values())

    async def get_task_history(
        self,
        task_name: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[TaskMetrics]:
        """Get task history with optional filtering.

        Args:
            task_name: Optional task name filter
            status: Optional status filter
            since: Optional date filter
            limit: Maximum number of results

        Returns:
            Filtered list of task metrics
        """
        filtered_tasks = self.task_history

        # Apply filters
        if task_name:
            filtered_tasks = [t for t in filtered_tasks if t.task_name == task_name]

        if status:
            filtered_tasks = [t for t in filtered_tasks if t.status == status]

        if since:
            filtered_tasks = [t for t in filtered_tasks if t.start_time >= since]

        # Sort by start time (newest first) and limit
        filtered_tasks.sort(key=lambda t: t.start_time, reverse=True)
        return filtered_tasks[:limit]

    async def get_task_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get task execution statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Statistics dictionary
        """
        since = datetime.utcnow() - timedelta(hours=hours)

        # Get tasks in time range
        recent_tasks = [
            t for t in self.task_history
            if t.start_time >= since
        ]

        # Calculate statistics
        total_tasks = len(recent_tasks)
        completed_tasks = len([t for t in recent_tasks if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in recent_tasks if t.status == TaskStatus.FAILED])

        # Duration statistics
        durations = [t.duration for t in recent_tasks if t.duration is not None]
        avg_duration = sum(durations) / len(durations) if durations else 0
        max_duration = max(durations) if durations else 0
        min_duration = min(durations) if durations else 0

        # Success rate
        success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Resource usage
        avg_memory = sum(t.memory_usage for t in recent_tasks) / len(recent_tasks) if recent_tasks else 0
        avg_cpu = sum(t.cpu_usage for t in recent_tasks) / len(recent_tasks) if recent_tasks else 0

        return {
            "period_hours": hours,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": round(success_rate, 2),
            "duration_statistics": {
                "average": round(avg_duration, 2),
                "maximum": round(max_duration, 2),
                "minimum": round(min_duration, 2),
            },
            "resource_usage": {
                "average_memory_mb": round(avg_memory / 1024 / 1024, 2),
                "average_cpu_percent": round(avg_cpu, 2),
            },
        }

    async def get_active_alerts(self, resolved: bool = False) -> List[TaskAlert]:
        """Get active alerts.

        Args:
            resolved: Whether to include resolved alerts

        Returns:
            List of alerts
        """
        if resolved:
            return self.alerts

        return [a for a in self.alerts if not a.resolved]

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert.

        Args:
            alert_id: Alert ID

        Returns:
            True if alert was resolved
        """
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.utcnow()
                logger.info(f"Resolved alert: {alert_id}")
                return True

        return False

    async def _monitor_tasks(self):
        """Background task status monitoring."""
        while self.monitors_running:
            try:
                # Check for stuck tasks
                await self._check_stuck_tasks()

                # Clean up old history
                await self._cleanup_old_history()

                # Sleep before next check
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task monitoring: {e}")
                await asyncio.sleep(5)

    async def _monitor_resources(self):
        """Background resource monitoring."""
        while self.monitors_running:
            try:
                # Get current system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')

                # Update active tasks with resource usage
                for task in self.active_tasks.values():
                    task.cpu_usage = cpu_percent
                    task.memory_usage = memory.used

                # Check for resource alerts
                await self._check_resource_alerts(cpu_percent, memory.percent, disk.percent)

                # Sleep before next check
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                await asyncio.sleep(10)

    async def _check_stuck_tasks(self):
        """Check for stuck tasks."""
        now = datetime.utcnow()
        stuck_threshold = timedelta(minutes=30)  # Consider stuck after 30 minutes

        for task_id, metrics in list(self.active_tasks.items()):
            if metrics.status in [TaskStatus.STARTED, TaskStatus.PROCESSING]:
                duration = now - metrics.start_time

                if duration > stuck_threshold:
                    await self._create_alert(
                        task_id=task_id,
                        alert_type="timeout",
                        severity="high",
                        message=f"Task appears to be stuck (duration: {duration})",
                    )

    async def _check_alerts(self, task_id: str, metrics: TaskMetrics):
        """Check for alert conditions.

        Args:
            task_id: Task ID
            metrics: Task metrics
        """
        # Check for slow progress
        if metrics.progress < 10 and metrics.duration and metrics.duration > 300:  # 5 minutes
            await self._create_alert(
                task_id=task_id,
                alert_type="slow_progress",
                severity="medium",
                message="Task progress is very slow",
            )

        # Check for high memory usage
        if metrics.memory_usage > 1024 * 1024 * 1024:  # 1GB
            await self._create_alert(
                task_id=task_id,
                alert_type="high_memory",
                severity="medium",
                message="Task is using high memory",
            )

    async def _check_resource_alerts(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check for resource usage alerts.

        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            disk_percent: Disk usage percentage
        """
        # CPU alert
        if cpu_percent > 90:
            await self._create_alert(
                task_id="system",
                alert_type="high_cpu",
                severity="medium",
                message=f"High CPU usage: {cpu_percent}%",
            )

        # Memory alert
        if memory_percent > 90:
            await self._create_alert(
                task_id="system",
                alert_type="high_memory",
                severity="high",
                message=f"High memory usage: {memory_percent}%",
            )

        # Disk alert
        if disk_percent > 95:
            await self._create_alert(
                task_id="system",
                alert_type="high_disk",
                severity="critical",
                message=f"High disk usage: {disk_percent}%",
            )

    async def _create_alert(
        self,
        task_id: str,
        alert_type: str,
        severity: str,
        message: str,
    ):
        """Create an alert.

        Args:
            task_id: Task ID
            alert_type: Alert type
            severity: Alert severity
            message: Alert message
        """
        alert = TaskAlert(
            alert_id=str(uuid4()),
            task_id=task_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp=datetime.utcnow(),
        )

        self.alerts.append(alert)

        # Log the alert
        if severity == "critical":
            logger.critical(f"ALERT [{alert_id}]: {message}")
        elif severity == "high":
            logger.error(f"ALERT [{alert_id}]: {message}")
        else:
            logger.warning(f"ALERT [{alert_id}]: {message}")

    async def _cleanup_old_history(self):
        """Clean up old task history."""
        # Keep history for 7 days
        cutoff = datetime.utcnow() - timedelta(days=7)

        # Remove old tasks from history
        self.task_history = [t for t in self.task_history if t.start_time >= cutoff]

        # Remove old resolved alerts (keep for 30 days)
        alert_cutoff = datetime.utcnow() - timedelta(days=30)
        self.alerts = [
            a for a in self.alerts
            if not a.resolved or a.timestamp >= alert_cutoff
        ]


# Global task monitor instance
task_monitor = TaskMonitor()


# Task monitoring utilities
async def start_task_monitor():
    """Start the global task monitor."""
    await task_monitor.start_monitoring()


async def stop_task_monitor():
    """Stop the global task monitor."""
    await task_monitor.stop_monitoring()


async def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get task status.

    Args:
        task_id: Task ID

    Returns:
        Task status dictionary or None
    """
    metrics = await task_monitor.get_task_status(task_id)
    return metrics.to_dict() if metrics else None


async def get_task_statistics(hours: int = 24) -> Dict[str, Any]:
    """Get task execution statistics.

    Args:
        hours: Number of hours to analyze

    Returns:
        Statistics dictionary
    """
    return await task_monitor.get_task_statistics(hours)


async def get_active_alerts() -> List[Dict[str, Any]]:
    """Get active alerts.

    Returns:
        List of alert dictionaries
    """
    alerts = await task_monitor.get_active_alerts()
    return [
        {
            "alert_id": a.alert_id,
            "task_id": a.task_id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "timestamp": a.timestamp.isoformat(),
            "resolved": a.resolved,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }
        for a in alerts
    ]


async def resolve_alert(alert_id: str) -> bool:
    """Resolve an alert.

    Args:
        alert_id: Alert ID

    Returns:
        True if alert was resolved
    """
    return await task_monitor.resolve_alert(alert_id)
