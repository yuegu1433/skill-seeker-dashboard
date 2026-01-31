"""Progress management core for real-time progress tracking.

This module provides ProgressManager for tracking task progress,
updating status, and coordinating with WebSocket for real-time updates.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func

from .models.task import TaskProgress, TaskStatus
from .models.log import TaskLog
from .models.metric import ProgressMetric
from .schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
    UpdateStatusRequest,
    TaskQueryParams,
    BulkUpdateRequest,
)
from .schemas.websocket_messages import (
    ProgressUpdateMessage,
    MessageType,
    TaskCompletedMessage,
    TaskFailedMessage,
    TaskStatusChangedMessage,
)
from .utils.validators import (
    validate_task_id,
    validate_user_id,
    validate_progress_value,
    validate_status,
    ValidationError,
)
from .utils.serializers import serialize_task_progress
from .websocket import websocket_manager

logger = logging.getLogger(__name__)


class ProgressManager:
    """Core manager for task progress tracking and updates."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize progress manager.

        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session
        self.active_tasks: Dict[str, TaskProgress] = {}
        self.task_update_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
        self._stats = {
            "total_tasks_created": 0,
            "total_updates": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0,
        }

    async def create_task(
        self,
        request: CreateTaskRequest,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Create a new task for progress tracking.

        Args:
            request: Task creation request
            db_session: Database session (overrides instance session)

        Returns:
            Created TaskProgress instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate request
        if not validate_task_id(request.task_id):
            raise ValidationError(f"Invalid task_id: {request.task_id}")

        if not validate_user_id(request.user_id):
            raise ValidationError(f"Invalid user_id: {request.user_id}")

        if request.progress < 0 or request.progress > 100:
            raise ValidationError("Progress must be between 0 and 100")

        if not validate_status(request.status):
            raise ValidationError(f"Invalid status: {request.status}")

        # Check if task already exists
        async with self._lock:
            if request.task_id in self.active_tasks:
                raise ValueError(f"Task {request.task_id} already exists")

            # Create task instance
            task = TaskProgress(
                task_id=request.task_id,
                user_id=request.user_id,
                task_type=request.task_type,
                task_name=request.task_name,
                description=request.description,
                progress=request.progress,
                status=request.status,
                current_step=request.current_step,
                total_steps=request.total_steps,
                estimated_duration=request.estimated_duration,
                retry_count=request.retry_count or 0,
                task_metadata=request.metadata or {},
                tags=request.tags or [],
            )

            # Save to database if session provided
            session = db_session or self.db_session
            if session:
                session.add(task)
                session.commit()
                session.refresh(task)

            # Track in memory
            self.active_tasks[request.task_id] = task
            self._stats["total_tasks_created"] += 1
            self._stats["active_tasks"] = len(self.active_tasks)

            # Broadcast task creation
            await self._broadcast_progress_update(task, "task_created")

            # Call handlers
            await self._call_handlers("task_created", task)

            logger.info(f"Created task: {request.task_id} for user: {request.user_id}")
            return task

    async def get_task(
        self,
        task_id: str,
        db_session: Optional[Session] = None,
    ) -> Optional[TaskProgress]:
        """Get task by ID.

        Args:
            task_id: Task ID
            db_session: Database session (overrides instance session)

        Returns:
            TaskProgress instance or None if not found
        """
        # Check active tasks first
        async with self._lock:
            if task_id in self.active_tasks:
                return self.active_tasks[task_id]

        # Query database if session provided
        session = db_session or self.db_session
        if session:
            task = session.query(TaskProgress).filter(TaskProgress.task_id == task_id).first()
            if task:
                # Cache in active tasks
                async with self._lock:
                    self.active_tasks[task_id] = task
                return task

        return None

    async def update_progress(
        self,
        task_id: str,
        progress: float,
        current_step: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Update task progress.

        Args:
            task_id: Task ID to update
            progress: New progress percentage (0-100)
            current_step: Current step description
            metadata: Additional metadata
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance

        Raises:
            ValidationError: If validation fails
            ValueError: If task not found
        """
        # Validate progress
        if not validate_progress_value(progress):
            raise ValidationError(f"Invalid progress value: {progress}")

        # Get task
        task = await self.get_task(task_id, db_session)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Update task
        task.progress = progress
        if current_step is not None:
            task.current_step = current_step
        if metadata:
            # Merge metadata
            task.task_metadata = {**(task.task_metadata or {}), **metadata}
        task.updated_at = datetime.utcnow()

        # Update database
        session = db_session or self.db_session
        if session:
            session.merge(task)
            session.commit()

        # Update cache
        async with self._lock:
            if task_id in self.active_tasks:
                self.active_tasks[task_id] = task

        self._stats["total_updates"] += 1

        # Broadcast update
        await self._broadcast_progress_update(task, "progress_updated")

        # Call handlers
        await self._call_handlers("progress_updated", task)

        logger.debug(f"Updated progress for task {task_id}: {progress}%")
        return task

    async def update_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        result: Optional[Any] = None,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Update task status.

        Args:
            task_id: Task ID to update
            status: New status
            error_message: Error message (if status is failed)
            error_details: Error details dictionary
            result: Task result (if completed)
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance

        Raises:
            ValidationError: If validation fails
            ValueError: If task not found
        """
        # Validate status
        if not validate_status(status):
            raise ValidationError(f"Invalid status: {status}")

        # Get task
        task = await self.get_task(task_id, db_session)
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        # Update status
        old_status = task.status
        task.status = status
        task.updated_at = datetime.utcnow()

        # Handle status-specific updates
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.utcnow()
            task.progress = 100.0
            self._stats["completed_tasks"] += 1
            async with self._lock:
                self._stats["active_tasks"] = len(self.active_tasks)
        elif status == TaskStatus.FAILED:
            task.error_message = error_message
            task.error_details = error_details or {}
            self._stats["failed_tasks"] += 1
        elif status == TaskStatus.RUNNING:
            if not task.started_at:
                task.started_at = datetime.utcnow()

        # Set result if provided
        if result is not None:
            task.result = result

        # Update database
        session = db_session or self.db_session
        if session:
            session.merge(task)
            session.commit()

        # Update cache
        async with self._lock:
            if task_id in self.active_tasks:
                self.active_tasks[task_id] = task

        self._stats["total_updates"] += 1

        # Broadcast update
        await self._broadcast_status_change(task, old_status, status)

        # Call handlers
        await self._call_handlers("status_updated", task)

        logger.info(f"Updated status for task {task_id}: {old_status} -> {status}")
        return task

    async def complete_task(
        self,
        task_id: str,
        result: Optional[Any] = None,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Mark task as completed.

        Args:
            task_id: Task ID to complete
            result: Task result
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance
        """
        return await self.update_status(
            task_id,
            TaskStatus.COMPLETED,
            result=result,
            db_session=db_session,
        )

    async def fail_task(
        self,
        task_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Mark task as failed.

        Args:
            task_id: Task ID to fail
            error_message: Error message
            error_details: Error details
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance
        """
        return await self.update_status(
            task_id,
            TaskStatus.FAILED,
            error_message=error_message,
            error_details=error_details,
            db_session=db_session,
        )

    async def pause_task(
        self,
        task_id: str,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Pause a running task.

        Args:
            task_id: Task ID to pause
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance
        """
        return await self.update_status(task_id, TaskStatus.PAUSED, db_session=db_session)

    async def resume_task(
        self,
        task_id: str,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Resume a paused task.

        Args:
            task_id: Task ID to resume
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance
        """
        return await self.update_status(task_id, TaskStatus.RUNNING, db_session=db_session)

    async def cancel_task(
        self,
        task_id: str,
        db_session: Optional[Session] = None,
    ) -> TaskProgress:
        """Cancel a task.

        Args:
            task_id: Task ID to cancel
            db_session: Database session (overrides instance session)

        Returns:
            Updated TaskProgress instance
        """
        return await self.update_status(task_id, TaskStatus.CANCELLED, db_session=db_session)

    async def delete_task(
        self,
        task_id: str,
        db_session: Optional[Session] = None,
    ) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID to delete
            db_session: Database session (overrides instance session)

        Returns:
            True if deleted successfully
        """
        async with self._lock:
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                self._stats["active_tasks"] = len(self.active_tasks)

        # Delete from database
        session = db_session or self.db_session
        if session:
            task = session.query(TaskProgress).filter(TaskProgress.task_id == task_id).first()
            if task:
                session.delete(task)
                session.commit()
                logger.info(f"Deleted task: {task_id}")
                return True

        return False

    async def list_tasks(
        self,
        query: TaskQueryParams,
        db_session: Optional[Session] = None,
    ) -> List[TaskProgress]:
        """List tasks with optional filtering.

        Args:
            query: Query parameters for filtering
            db_session: Database session (overrides instance session)

        Returns:
            List of TaskProgress instances
        """
        session = db_session or self.db_session
        if not session:
            # Return active tasks if no database
            async with self._lock:
                tasks = list(self.active_tasks.values())

            # Apply filters
            if query.user_id:
                tasks = [t for t in tasks if t.user_id == query.user_id]
            if query.status:
                tasks = [t for t in tasks if t.status == query.status]
            if query.task_type:
                tasks = [t for t in tasks if t.task_type == query.task_type]

            # Sort and limit
            tasks.sort(key=lambda t: t.updated_at or t.created_at, reverse=True)
            if query.limit:
                tasks = tasks[:query.limit]

            return tasks

        # Query database
        query_builder = session.query(TaskProgress)

        # Apply filters
        if query.user_id:
            query_builder = query_builder.filter(TaskProgress.user_id == query.user_id)
        if query.status:
            query_builder = query_builder.filter(TaskProgress.status == query.status)
        if query.task_type:
            query_builder = query_builder.filter(TaskProgress.task_type == query.task_type)
        if query.date_from:
            query_builder = query_builder.filter(TaskProgress.created_at >= query.date_from)
        if query.date_to:
            query_builder = query_builder.filter(TaskProgress.created_at <= query.date_to)
        if query.search:
            search_pattern = f"%{query.search}%"
            query_builder = query_builder.filter(
                or_(
                    TaskProgress.task_name.like(search_pattern),
                    TaskProgress.description.like(search_pattern),
                )
            )

        # Sort
        if query.sort_by:
            sort_column = getattr(TaskProgress, query.sort_by, TaskProgress.updated_at)
            if query.sort_order == "desc":
                query_builder = query_builder.order_by(desc(sort_column))
            else:
                query_builder = query_builder.order_by(sort_column)
        else:
            query_builder = query_builder.order_by(desc(TaskProgress.updated_at))

        # Limit
        if query.limit:
            query_builder = query_builder.limit(query.limit)

        return query_builder.all()

    async def bulk_update(
        self,
        request: BulkUpdateRequest,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Bulk update multiple tasks.

        Args:
            request: Bulk update request
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary with update results
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(request.task_ids),
        }

        for task_id in request.task_ids:
            try:
                if request.status:
                    await self.update_status(
                        task_id,
                        request.status,
                        error_message=request.error_message,
                        error_details=request.error_details,
                        db_session=db_session,
                    )
                elif request.progress is not None:
                    await self.update_progress(
                        task_id,
                        request.progress,
                        current_step=request.current_step,
                        metadata=request.metadata,
                        db_session=db_session,
                    )

                results["successful"].append(task_id)
            except Exception as e:
                results["failed"].append({"task_id": task_id, "error": str(e)})
                logger.error(f"Failed to update task {task_id}: {e}")

        return results

    async def get_task_stats(
        self,
        user_id: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Get task statistics.

        Args:
            user_id: Filter by user ID (optional)
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary containing statistics
        """
        session = db_session or self.db_session
        if not session:
            # Calculate from active tasks
            async with self._lock:
                tasks = list(self.active_tasks.values())
                if user_id:
                    tasks = [t for t in tasks if t.user_id == user_id]

            total = len(tasks)
            completed = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
            running = len([t for t in tasks if t.status == TaskStatus.RUNNING])
            failed = len([t for t in tasks if t.status == TaskStatus.FAILED])
            paused = len([t for t in tasks if t.status == TaskStatus.PAUSED])

            return {
                "total": total,
                "completed": completed,
                "running": running,
                "failed": failed,
                "paused": paused,
                "success_rate": (completed / total * 100) if total > 0 else 0,
                "average_progress": sum(t.progress for t in tasks) / total if total > 0 else 0,
                **self._stats,
            }

        # Query database
        query_builder = session.query(TaskProgress)
        if user_id:
            query_builder = query_builder.filter(TaskProgress.user_id == user_id)

        total = query_builder.count()
        completed = query_builder.filter(TaskProgress.status == TaskStatus.COMPLETED).count()
        running = query_builder.filter(TaskProgress.status == TaskStatus.RUNNING).count()
        failed = query_builder.filter(TaskProgress.status == TaskStatus.FAILED).count()
        paused = query_builder.filter(TaskProgress.status == TaskStatus.PAUSED).count()

        # Calculate average progress
        avg_progress = session.query(func.avg(TaskProgress.progress)).filter(
            TaskProgress.user_id == user_id if user_id else True
        ).scalar() or 0

        return {
            "total": total,
            "completed": completed,
            "running": running,
            "failed": failed,
            "paused": paused,
            "success_rate": (completed / total * 100) if total > 0 else 0,
            "average_progress": avg_progress,
            **self._stats,
        }

    def register_update_handler(self, handler: Callable):
        """Register a task update handler.

        Args:
            handler: Async handler function(event_type, task)
        """
        self.task_update_handlers.append(handler)

    def unregister_update_handler(self, handler: Callable):
        """Unregister a task update handler.

        Args:
            handler: Handler to remove
        """
        if handler in self.task_update_handlers:
            self.task_update_handlers.remove(handler)

    async def _broadcast_progress_update(self, task: TaskProgress, event_type: str):
        """Broadcast progress update via WebSocket.

        Args:
            task: TaskProgress instance
            event_type: Type of event
        """
        message = ProgressUpdateMessage(
            type=MessageType.PROGRESS_UPDATE,
            task_id=task.task_id,
            progress=task.progress,
            status=task.status,
            current_step=task.current_step,
            total_steps=task.total_steps,
            event_type=event_type,
            timestamp=time.time(),
        )

        # Broadcast to task-specific connections
        await websocket_manager.broadcast_to_task(task.task_id, message.dict())

        # Broadcast to user-specific connections
        await websocket_manager.broadcast_to_user(task.user_id, message.dict())

    async def _broadcast_status_change(
        self,
        task: TaskProgress,
        old_status: str,
        new_status: str,
    ):
        """Broadcast status change via WebSocket.

        Args:
            task: TaskProgress instance
            old_status: Previous status
            new_status: New status
        """
        if new_status == TaskStatus.COMPLETED:
            message = TaskCompletedMessage(
                type=MessageType.TASK_COMPLETED,
                task_id=task.task_id,
                result=task.result,
                duration_seconds=task.duration_seconds,
                timestamp=time.time(),
            )
        elif new_status == TaskStatus.FAILED:
            message = TaskFailedMessage(
                type=MessageType.TASK_FAILED,
                task_id=task.task_id,
                error_message=task.error_message,
                error_details=task.error_details,
                timestamp=time.time(),
            )
        else:
            message = TaskStatusChangedMessage(
                type=MessageType.TASK_STATUS_CHANGED,
                task_id=task.task_id,
                old_status=old_status,
                new_status=new_status,
                timestamp=time.time(),
            )

        # Broadcast to task-specific connections
        await websocket_manager.broadcast_to_task(task.task_id, message.dict())

        # Broadcast to user-specific connections
        await websocket_manager.broadcast_to_user(task.user_id, message.dict())

    async def _call_handlers(self, event_type: str, task: TaskProgress):
        """Call registered event handlers.

        Args:
            event_type: Type of event
            task: TaskProgress instance
        """
        for handler in self.task_update_handlers:
            try:
                await handler(event_type, task)
            except Exception as e:
                logger.error(f"Error in task update handler: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get progress manager statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **self._stats,
            "active_tasks_count": len(self.active_tasks),
        }


# Global progress manager instance
progress_manager = ProgressManager()
