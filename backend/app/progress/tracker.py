"""Task tracking system for real-time progress tracking.

This module provides TaskTracker for tracking task progress, status management,
progress aggregation, and caching with batch processing optimization.
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, text

from .models.task import TaskProgress, TaskStatus
from .models.log import TaskLog
from .schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
    TaskQueryParams,
)
from .utils.validators import (
    validate_task_id,
    validate_user_id,
    validate_progress_value,
    validate_status,
    ValidationError,
)
from .utils.serializers import serialize_task_progress

logger = logging.getLogger(__name__)


class TaskTrackerError(Exception):
    """Base exception for task tracking operations."""
    pass


class TaskNotFoundError(TaskTrackerError):
    """Raised when task is not found."""
    pass


class TaskUpdateError(TaskTrackerError):
    """Raised when task update fails."""
    pass


class TaskCache:
    """In-memory cache for task tracking."""

    def __init__(self, max_size: int = 10000, ttl: int = 3600):
        """Initialize task cache.

        Args:
            max_size: Maximum cache size
            ttl: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task from cache.

        Args:
            task_id: Task ID

        Returns:
            Cached task data or None
        """
        async with self._lock:
            if task_id not in self._cache:
                return None

            # Check TTL
            if time.time() - self._access_times[task_id] > self.ttl:
                await self._remove(task_id)
                return None

            # Update access time
            self._access_times[task_id] = time.time()
            return self._cache[task_id].copy()

    async def set(self, task_id: str, data: Dict[str, Any]) -> None:
        """Set task in cache.

        Args:
            task_id: Task ID
            data: Task data
        """
        async with self._lock:
            # Check if we need to evict
            if len(self._cache) >= self.max_size and task_id not in self._cache:
                await self._evict_oldest()

            self._cache[task_id] = data.copy()
            self._access_times[task_id] = time.time()

    async def remove(self, task_id: str) -> None:
        """Remove task from cache.

        Args:
            task_id: Task ID
        """
        async with self._lock:
            await self._remove(task_id)

    async def _remove(self, task_id: str) -> None:
        """Remove task from cache (internal method).

        Args:
            task_id: Task ID
        """
        self._cache.pop(task_id, None)
        self._access_times.pop(task_id, None)

    async def _evict_oldest(self) -> None:
        """Evict oldest accessed task."""
        if not self._access_times:
            return

        oldest_task_id = min(self._access_times.keys(), key=lambda k: self._access_times[k])
        await self._remove(oldest_task_id)

    async def clear(self) -> None:
        """Clear all cached tasks."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()


class ProgressAggregator:
    """Aggregates progress across multiple tasks."""

    def __init__(self):
        """Initialize progress aggregator."""
        self._aggregated_data: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def add_task_progress(
        self,
        task_id: str,
        task_type: str,
        progress: float,
        status: str,
        weight: float = 1.0,
    ) -> None:
        """Add task progress to aggregation.

        Args:
            task_id: Task ID
            task_type: Task type
            progress: Progress percentage (0-100)
            status: Task status
            weight: Task weight for aggregation
        """
        async with self._lock:
            if task_type not in self._aggregated_data:
                self._aggregated_data[task_type] = {
                    "tasks": [],
                    "total_progress": 0.0,
                    "weighted_progress": 0.0,
                    "total_weight": 0.0,
                    "completed_count": 0,
                    "running_count": 0,
                    "failed_count": 0,
                }

            data = self._aggregated_data[task_type]
            data["tasks"].append(
                {
                    "task_id": task_id,
                    "progress": progress,
                    "status": status,
                    "weight": weight,
                    "timestamp": time.time(),
                }
            )

            # Update aggregation
            data["total_progress"] = sum(t["progress"] for t in data["tasks"]) / len(data["tasks"])
            data["weighted_progress"] = sum(t["progress"] * t["weight"] for t in data["tasks"]) / sum(
                t["weight"] for t in data["tasks"]
            )
            data["total_weight"] = sum(t["weight"] for t in data["tasks"])

            # Update status counts
            data["completed_count"] = sum(1 for t in data["tasks"] if t["status"] == "completed")
            data["running_count"] = sum(1 for t in data["tasks"] if t["status"] == "running")
            data["failed_count"] = sum(1 for t in data["tasks"] if t["status"] == "failed")

    async def remove_task(self, task_id: str) -> None:
        """Remove task from aggregation.

        Args:
            task_id: Task ID
        """
        async with self._lock:
            for task_type, data in list(self._aggregated_data.items()):
                data["tasks"] = [t for t in data["tasks"] if t["task_id"] != task_id]

                # Remove task type if no tasks left
                if not data["tasks"]:
                    del self._aggregated_data[task_type]
                    continue

                # Recalculate aggregation
                data["total_progress"] = sum(t["progress"] for t in data["tasks"]) / len(data["tasks"])
                data["weighted_progress"] = sum(t["progress"] * t["weight"] for t in data["tasks"]) / sum(
                    t["weight"] for t in data["tasks"]
                )
                data["total_weight"] = sum(t["weight"] for t in data["tasks"])
                data["completed_count"] = sum(1 for t in data["tasks"] if t["status"] == "completed")
                data["running_count"] = sum(1 for t in data["tasks"] if t["status"] == "running")
                data["failed_count"] = sum(1 for t in data["tasks"] if t["status"] == "failed")

    async def get_aggregation(self, task_type: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated progress data.

        Args:
            task_type: Specific task type (optional)

        Returns:
            Aggregated progress data
        """
        async with self._lock:
            if task_type:
                return self._aggregated_data.get(task_type, {})
            return self._aggregated_data.copy()

    async def clear(self) -> None:
        """Clear all aggregated data."""
        async with self._lock:
            self._aggregated_data.clear()


class TaskTracker:
    """Task tracker for managing task progress and status updates."""

    def __init__(
        self,
        db_session: Optional[Session] = None,
        cache_size: int = 10000,
        cache_ttl: int = 3600,
        batch_size: int = 100,
        batch_timeout: float = 5.0,
    ):
        """Initialize task tracker.

        Args:
            db_session: SQLAlchemy database session
            cache_size: Task cache size limit
            cache_ttl: Cache time to live in seconds
            batch_size: Batch processing size
            batch_timeout: Batch timeout in seconds
        """
        self.db_session = db_session
        self.cache = TaskCache(max_size=cache_size, ttl=cache_ttl)
        self.aggregator = ProgressAggregator()
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self._pending_updates: deque = deque()
        self._update_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
        self._stats = {
            "tasks_created": 0,
            "tasks_updated": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_updates": 0,
            "last_update_time": None,
        }

    async def create_task(self, request: CreateTaskRequest) -> Dict[str, Any]:
        """Create a new task.

        Args:
            request: Task creation request

        Returns:
            Created task data

        Raises:
            ValidationError: If request is invalid
        """
        # Validate input
        task_id_result = validate_task_id(request.task_id)
        if not task_id_result.is_valid:
            raise ValidationError(f"Invalid task_id: {task_id_result.errors}")

        user_id_result = validate_user_id(request.user_id)
        if not user_id_result.is_valid:
            raise ValidationError(f"Invalid user_id: {user_id_result.errors}")

        # Create task in database
        if self.db_session:
            task = TaskProgress(
                task_id=request.task_id,
                user_id=request.user_id,
                task_type=request.task_type,
                task_name=request.task_name,
                description=request.description,
                estimated_duration=request.estimated_duration,
                total_steps=request.total_steps,
                task_metadata=request.metadata or {},
                tags=request.tags or [],
                status=TaskStatus.PENDING,
                progress=0.0,
                started_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            self.db_session.add(task)
            self.db_session.commit()
            self.db_session.refresh(task)

            # Serialize task
            task_data = serialize_task_progress(task)
        else:
            # In-memory task
            task_data = {
                "task_id": request.task_id,
                "user_id": request.user_id,
                "task_type": request.task_type,
                "task_name": request.task_name,
                "description": request.description,
                "progress": 0.0,
                "status": "pending",
                "estimated_duration": request.estimated_duration,
                "total_steps": request.total_steps,
                "current_step": None,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "metadata": request.metadata or {},
                "tags": request.tags or [],
            }

        # Cache task
        await self.cache.set(request.task_id, task_data)

        # Update statistics
        self._stats["tasks_created"] += 1
        self._stats["last_update_time"] = time.time()

        logger.info(f"Created task: {request.task_id}")
        return task_data

    async def update_task_progress(self, request: UpdateProgressRequest) -> Dict[str, Any]:
        """Update task progress.

        Args:
            request: Progress update request

        Returns:
            Updated task data

        Raises:
            TaskNotFoundError: If task not found
            ValidationError: If request is invalid
        """
        # Validate input
        task_id_result = validate_task_id(request.task_id)
        if not task_id_result.is_valid:
            raise ValidationError(f"Invalid task_id: {task_id_result.errors}")

        progress_result = validate_progress_value(request.progress)
        if not progress_result.is_valid:
            raise ValidationError(f"Invalid progress: {progress_result.errors}")

        # Check cache first
        task_data = await self.cache.get(request.task_id)
        if not task_data:
            self._stats["cache_misses"] += 1
            # Try to load from database
            if self.db_session:
                task = (
                    self.db_session.query(TaskProgress)
                    .filter(TaskProgress.task_id == request.task_id)
                    .first()
                )
                if not task:
                    raise TaskNotFoundError(f"Task not found: {request.task_id}")
                task_data = serialize_task_progress(task)
                await self.cache.set(request.task_id, task_data)
            else:
                raise TaskNotFoundError(f"Task not found: {request.task_id}")
        else:
            self._stats["cache_hits"] += 1

        # Update progress
        old_progress = task_data.get("progress", 0.0)
        old_status = task_data.get("status", "pending")

        task_data["progress"] = request.progress
        task_data["updated_at"] = datetime.utcnow().isoformat()

        if request.current_step:
            task_data["current_step"] = request.current_step

        if request.status:
            status_result = validate_status(request.status)
            if not status_result.is_valid:
                raise ValidationError(f"Invalid status: {status_result.errors}")
            task_data["status"] = request.status

        if request.metadata:
            task_data["metadata"] = {**task_data.get("metadata", {}), **request.metadata}

        # Update in database
        if self.db_session:
            task = (
                self.db_session.query(TaskProgress)
                .filter(TaskProgress.task_id == request.task_id)
                .first()
            )
            if task:
                task.progress = request.progress
                task.current_step = request.current_step
                if request.status:
                    task.status = request.status
                if request.metadata:
                    task.task_metadata = {**task.task_metadata, **request.metadata}
                task.updated_at = datetime.utcnow()

                # Handle completion
                if request.status == "completed":
                    task.completed_at = datetime.utcnow()
                    self._stats["tasks_completed"] += 1
                elif request.status == "failed":
                    self._stats["tasks_failed"] += 1

                self.db_session.commit()
                self.db_session.refresh(task)
                task_data = serialize_task_progress(task)

        # Cache updated task
        await self.cache.set(request.task_id, task_data)

        # Update aggregator
        await self.aggregator.add_task_progress(
            task_id=request.task_id,
            task_type=task_data.get("task_type", "unknown"),
            progress=request.progress,
            status=task_data.get("status", "pending"),
        )

        # Update statistics
        self._stats["tasks_updated"] += 1
        self._stats["last_update_time"] = time.time()

        # Notify handlers
        await self._notify_handlers("progress_updated", task_data)

        logger.info(
            f"Updated task progress: {request.task_id} "
            f"({old_progress}% -> {request.progress}%)"
        )

        return task_data

    async def get_task(self, task_id: str) -> Dict[str, Any]:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data

        Raises:
            TaskNotFoundError: If task not found
        """
        # Check cache first
        task_data = await self.cache.get(task_id)
        if task_data:
            self._stats["cache_hits"] += 1
            return task_data

        self._stats["cache_misses"] += 1

        # Try to load from database
        if self.db_session:
            task = (
                self.db_session.query(TaskProgress)
                .filter(TaskProgress.task_id == task_id)
                .first()
            )
            if not task:
                raise TaskNotFoundError(f"Task not found: {task_id}")

            task_data = serialize_task_progress(task)
            await self.cache.set(task_id, task_data)
            return task_data

        raise TaskNotFoundError(f"Task not found: {task_id}")

    async def get_user_tasks(
        self,
        user_id: str,
        status_filter: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Get tasks for a user.

        Args:
            user_id: User ID
            status_filter: Status filter (optional)
            limit: Result limit
            offset: Result offset

        Returns:
            List of task data
        """
        if self.db_session:
            query = self.db_session.query(TaskProgress).filter(TaskProgress.user_id == user_id)

            if status_filter:
                query = query.filter(TaskProgress.status.in_(status_filter))

            # Order by updated_at descending
            query = query.order_by(desc(TaskProgress.updated_at))

            # Apply pagination
            tasks = query.offset(offset).limit(limit).all()

            return [serialize_task_progress(task) for task in tasks]
        else:
            # In-memory filtering (simplified)
            tasks = []
            for task_data in self.cache._cache.values():
                if task_data.get("user_id") == user_id:
                    if status_filter is None or task_data.get("status") in status_filter:
                        tasks.append(task_data)

            # Sort by updated_at (most recent first)
            tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

            # Apply pagination
            return tasks[offset : offset + limit]

    async def get_tasks_by_status(
        self,
        status: str,
        task_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get tasks by status.

        Args:
            status: Task status
            task_type: Task type filter (optional)
            limit: Result limit

        Returns:
            List of task data
        """
        status_result = validate_status(status)
        if not status_result.is_valid:
            raise ValidationError(f"Invalid status: {status_result.errors}")

        if self.db_session:
            query = self.db_session.query(TaskProgress).filter(TaskProgress.status == status)

            if task_type:
                query = query.filter(TaskProgress.task_type == task_type)

            query = query.order_by(desc(TaskProgress.updated_at)).limit(limit)

            tasks = query.all()
            return [serialize_task_progress(task) for task in tasks]
        else:
            # In-memory filtering
            tasks = []
            for task_data in self.cache._cache.values():
                if task_data.get("status") == status:
                    if task_type is None or task_data.get("task_type") == task_type:
                        tasks.append(task_data)

            tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return tasks[:limit]

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted successfully

        Raises:
            TaskNotFoundError: If task not found
        """
        # Remove from cache
        await self.cache.remove(task_id)

        # Remove from aggregator
        await self.aggregator.remove_task(task_id)

        # Delete from database
        if self.db_session:
            task = (
                self.db_session.query(TaskProgress)
                .filter(TaskProgress.task_id == task_id)
                .first()
            )
            if not task:
                raise TaskNotFoundError(f"Task not found: {task_id}")

            self.db_session.delete(task)
            self.db_session.commit()
            logger.info(f"Deleted task: {task_id}")
            return True

        logger.info(f"Deleted task (in-memory): {task_id}")
        return True

    async def get_progress_statistics(
        self,
        user_id: Optional[str] = None,
        task_type: Optional[str] = None,
        time_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get progress statistics.

        Args:
            user_id: User ID filter (optional)
            task_type: Task type filter (optional)
            time_range: Time range filter (optional)

        Returns:
            Progress statistics
        """
        if self.db_session:
            query = self.db_session.query(TaskProgress)

            if user_id:
                query = query.filter(TaskProgress.user_id == user_id)

            if task_type:
                query = query.filter(TaskProgress.task_type == task_type)

            if time_range:
                # Parse time range (simplified)
                now = datetime.utcnow()
                if time_range == "1h":
                    since = now - timedelta(hours=1)
                elif time_range == "24h":
                    since = now - timedelta(hours=24)
                elif time_range == "7d":
                    since = now - timedelta(days=7)
                elif time_range == "30d":
                    since = now - timedelta(days=30)
                else:
                    since = now - timedelta(hours=24)  # Default

                query = query.filter(TaskProgress.updated_at >= since)

            # Calculate statistics
            total_tasks = query.count()
            completed_tasks = query.filter(TaskProgress.status == TaskStatus.COMPLETED).count()
            running_tasks = query.filter(TaskProgress.status == TaskStatus.RUNNING).count()
            failed_tasks = query.filter(TaskProgress.status == TaskStatus.FAILED).count()
            paused_tasks = query.filter(TaskProgress.status == TaskStatus.PAUSED).count()

            # Calculate average progress
            avg_progress = query.with_entities(func.avg(TaskProgress.progress)).scalar() or 0

            # Calculate success rate
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "running_tasks": running_tasks,
                "failed_tasks": failed_tasks,
                "paused_tasks": paused_tasks,
                "success_rate": success_rate,
                "average_progress": avg_progress,
                "task_type": task_type,
                "user_id": user_id,
                "time_range": time_range,
            }
        else:
            # In-memory statistics (simplified)
            tasks = list(self.cache._cache.values())

            if user_id:
                tasks = [t for t in tasks if t.get("user_id") == user_id]

            if task_type:
                tasks = [t for t in tasks if t.get("task_type") == task_type]

            total_tasks = len(tasks)
            completed_tasks = len([t for t in tasks if t.get("status") == "completed"])
            running_tasks = len([t for t in tasks if t.get("status") == "running"])
            failed_tasks = len([t for t in tasks if t.get("status") == "failed"])
            paused_tasks = len([t for t in tasks if t.get("status") == "paused"])

            avg_progress = sum(t.get("progress", 0) for t in tasks) / total_tasks if total_tasks > 0 else 0
            success_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            return {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "running_tasks": running_tasks,
                "failed_tasks": failed_tasks,
                "paused_tasks": paused_tasks,
                "success_rate": success_rate,
                "average_progress": avg_progress,
                "task_type": task_type,
                "user_id": user_id,
                "time_range": time_range,
            }

    async def aggregate_progress(self, task_ids: List[str]) -> Dict[str, Any]:
        """Aggregate progress across multiple tasks.

        Args:
            task_ids: List of task IDs

        Returns:
            Aggregated progress data
        """
        tasks_data = []
        total_progress = 0.0
        completed_count = 0
        running_count = 0
        failed_count = 0

        for task_id in task_ids:
            try:
                task_data = await self.get_task(task_id)
                tasks_data.append(task_data)
                total_progress += task_data.get("progress", 0.0)

                status = task_data.get("status", "pending")
                if status == "completed":
                    completed_count += 1
                elif status == "running":
                    running_count += 1
                elif status == "failed":
                    failed_count += 1
            except TaskNotFoundError:
                logger.warning(f"Task not found during aggregation: {task_id}")

        avg_progress = total_progress / len(tasks_data) if tasks_data else 0.0

        return {
            "task_ids": task_ids,
            "total_tasks": len(tasks_data),
            "average_progress": avg_progress,
            "completed_count": completed_count,
            "running_count": running_count,
            "failed_count": failed_count,
            "tasks": tasks_data,
        }

    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """Clean up old completed tasks.

        Args:
            older_than_hours: Remove tasks older than this many hours

        Returns:
            Number of tasks cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        if self.db_session:
            # Find completed tasks older than cutoff
            old_tasks = (
                self.db_session.query(TaskProgress)
                .filter(
                    and_(
                        TaskProgress.status == TaskStatus.COMPLETED,
                        TaskProgress.completed_at < cutoff_time,
                    )
                )
                .all()
            )

            # Delete old tasks
            for task in old_tasks:
                await self.cache.remove(task.task_id)
                await self.aggregator.remove_task(task.task_id)
                self.db_session.delete(task)

            self.db_session.commit()

            logger.info(f"Cleaned up {len(old_tasks)} old completed tasks")
            return len(old_tasks)
        else:
            # In-memory cleanup (simplified)
            # In a real implementation, you'd track creation/completion times
            return 0

    def register_update_handler(self, handler: Callable) -> None:
        """Register a task update handler.

        Args:
            handler: Async handler function
        """
        self._update_handlers.append(handler)

    def unregister_update_handler(self, handler: Callable) -> None:
        """Unregister a task update handler.

        Args:
            handler: Handler to remove
        """
        if handler in self._update_handlers:
            self._update_handlers.remove(handler)

    async def _notify_handlers(self, event_type: str, task_data: Dict[str, Any]) -> None:
        """Notify registered handlers of task updates.

        Args:
            event_type: Type of event
            task_data: Updated task data
        """
        for handler in self._update_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, task_data)
                else:
                    handler(event_type, task_data)
            except Exception as e:
                logger.error(f"Error in task update handler: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get task tracker statistics.

        Returns:
            Task tracker statistics
        """
        return {
            **self._stats,
            "cached_tasks": len(self.cache._cache),
            "active_handlers": len(self._update_handlers),
            "aggregated_types": len(self.aggregator._aggregated_data),
        }


# Global task tracker instance
task_tracker = TaskTracker()


if __name__ == "__main__":
    # Example usage
    async def main():
        tracker = TaskTracker()

        # Create task
        task_data = await tracker.create_task(
            CreateTaskRequest(
                task_id="task-001",
                user_id="user-001",
                task_type="skill_creation",
                task_name="Test Task",
                description="Testing task tracker",
            )
        )
        print(f"Created task: {task_data['task_id']}")

        # Update progress
        updated_task = await tracker.update_task_progress(
            UpdateProgressRequest(
                task_id="task-001",
                progress=50.0,
                status="running",
                current_step="step_2",
                message="Processing...",
            )
        )
        print(f"Updated task progress: {updated_task['progress']}%")

        # Get task
        task = await tracker.get_task("task-001")
        print(f"Retrieved task: {task['task_name']}")

        # Get statistics
        stats = tracker.get_statistics()
        print(f"Statistics: {stats}")

    asyncio.run(main())
