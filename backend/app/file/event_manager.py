"""File Operation Event Manager.

This module contains the FileOperationEventManager class which provides
event-driven file operations with publish-subscribe pattern.
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Callable, Any, Set
from datetime import datetime
from uuid import uuid4, UUID
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for file operations."""
    # File lifecycle events
    FILE_CREATED = "file.created"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
    FILE_RESTORED = "file.restored"
    FILE_MOVED = "file.moved"
    FILE_COPIED = "file.copied"

    # File access events
    FILE_ACCESSED = "file.accessed"
    FILE_DOWNLOADED = "file.downloaded"
    FILE_VIEWED = "file.viewed"

    # Version events
    VERSION_CREATED = "version.created"
    VERSION_RESTORED = "version.restored"
    VERSION_DELETED = "version.deleted"

    # Permission events
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"

    # Backup events
    BACKUP_CREATED = "backup.created"
    BACKUP_RESTORED = "backup.restored"
    BACKUP_DELETED = "backup.deleted"

    # Bulk operation events
    BULK_OPERATION_STARTED = "bulk_operation.started"
    BULK_OPERATION_PROGRESS = "bulk_operation.progress"
    BULK_OPERATION_COMPLETED = "bulk_operation.completed"
    BULK_OPERATION_FAILED = "bulk_operation.failed"

    # System events
    FILE_SYSTEM_ERROR = "file_system.error"
    FILE_QUOTA_EXCEEDED = "file.quota_exceeded"
    FILE_STORAGE_FULL = "file.storage_full"


@dataclass
class EventContext:
    """Event context information."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class FileOperationEvent:
    """File operation event data."""

    event_id: UUID
    event_type: EventType
    file_id: Optional[UUID] = None
    user_id: Optional[str] = None
    timestamp: datetime = None
    data: Dict[str, Any] = None
    context: EventContext = None
    version: int = 1

    def __post_init__(self):
        """Initialize default values."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.data is None:
            self.data = {}
        if self.context is None:
            self.context = EventContext()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type.value,
            "file_id": str(self.file_id) if self.file_id else None,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "context": asdict(self.context),
            "version": self.version,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


EventHandler = Callable[[FileOperationEvent], asyncio.Future or Any]


class EventStatistics:
    """Event statistics tracking."""

    def __init__(self):
        """Initialize statistics."""
        self.total_events = 0
        self.events_by_type: Dict[str, int] = defaultdict(int)
        self.events_by_user: Dict[str, int] = defaultdict(int)
        self.handler_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "success": 0,
            "errors": 0,
            "avg_duration": 0.0
        })
        self._lock = threading.RLock()

    def record_event(self, event: FileOperationEvent):
        """Record event statistics."""
        with self._lock:
            self.total_events += 1
            self.events_by_type[event.event_type.value] += 1

            if event.user_id:
                self.events_by_user[event.user_id] += 1

    def record_handler_execution(self, handler_name: str, duration: float, success: bool, error: Optional[Exception] = None):
        """Record handler execution statistics."""
        with self._lock:
            stats = self.handler_stats[handler_name]
            stats["count"] += 1

            if success:
                stats["success"] += 1
            else:
                stats["errors"] += 1

            # Update average duration
            if stats["count"] > 1:
                stats["avg_duration"] = ((stats["avg_duration"] * (stats["count"] - 1)) + duration) / stats["count"]
            else:
                stats["avg_duration"] = duration

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics summary."""
        with self._lock:
            return {
                "total_events": self.total_events,
                "events_by_type": dict(self.events_by_type),
                "events_by_user": dict(self.events_by_user),
                "handler_stats": dict(self.handler_stats),
            }


class FileOperationEventManager:
    """File operation event manager with publish-subscribe pattern."""

    def __init__(self, max_workers: int = 10):
        """Initialize event manager.

        Args:
            max_workers: Maximum number of worker threads for async operations
        """
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[FileOperationEvent] = []
        self._max_history_size = 10000
        self._statistics = EventStatistics()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        self._event_queue = asyncio.Queue(maxsize=10000)
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the event manager."""
        if not self._running:
            self._running = True
            self._worker_task = asyncio.create_task(self._event_worker())
            logger.info("FileOperationEventManager started")

    async def stop(self):
        """Stop the event manager."""
        if self._running:
            self._running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            self._executor.shutdown(wait=True)
            logger.info("FileOperationEventManager stopped")

    async def publish_event(
        self,
        event_type: EventType,
        file_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[EventContext] = None,
        async_mode: bool = True
    ) -> str:
        """Publish an event.

        Args:
            event_type: Type of event
            file_id: Related file ID
            user_id: User who triggered the event
            data: Event data
            context: Event context
            async_mode: Whether to process asynchronously

        Returns:
            Event ID
        """
        event = FileOperationEvent(
            event_id=uuid4(),
            event_type=event_type,
            file_id=file_id,
            user_id=user_id,
            data=data or {},
            context=context or EventContext()
        )

        if async_mode:
            await self._event_queue.put(event)
        else:
            await self._process_event(event)

        logger.debug(f"Event published: {event_type.value} (ID: {event.event_id})")
        return str(event.event_id)

    async def publish_file_created(
        self,
        file_id: UUID,
        user_id: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        context: Optional[EventContext] = None
    ) -> str:
        """Publish file created event.

        Args:
            file_id: File ID
            user_id: User who created the file
            file_name: Name of the file
            file_size: Size of the file
            mime_type: MIME type
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "file_name": file_name,
            "file_size": file_size,
            "mime_type": mime_type
        }

        return await self.publish_event(
            EventType.FILE_CREATED,
            file_id=file_id,
            user_id=user_id,
            data=data,
            context=context
        )

    async def publish_file_updated(
        self,
        file_id: UUID,
        user_id: str,
        changes: Dict[str, Any],
        context: Optional[EventContext] = None
    ) -> str:
        """Publish file updated event.

        Args:
            file_id: File ID
            user_id: User who updated the file
            changes: Changes made to the file
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "changes": changes,
            "change_count": len(changes)
        }

        return await self.publish_event(
            EventType.FILE_UPDATED,
            file_id=file_id,
            user_id=user_id,
            data=data,
            context=context
        )

    async def publish_file_deleted(
        self,
        file_id: UUID,
        user_id: str,
        permanent: bool = False,
        context: Optional[EventContext] = None
    ) -> str:
        """Publish file deleted event.

        Args:
            file_id: File ID
            user_id: User who deleted the file
            permanent: Whether deletion was permanent
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "permanent": permanent
        }

        return await self.publish_event(
            EventType.FILE_DELETED,
            file_id=file_id,
            user_id=user_id,
            data=data,
            context=context
        )

    async def publish_file_accessed(
        self,
        file_id: UUID,
        user_id: str,
        access_type: str,
        context: Optional[EventContext] = None
    ) -> str:
        """Publish file accessed event.

        Args:
            file_id: File ID
            user_id: User who accessed the file
            access_type: Type of access (view, download, edit)
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "access_type": access_type
        }

        return await self.publish_event(
            EventType.FILE_ACCESSED,
            file_id=file_id,
            user_id=user_id,
            data=data,
            context=context
        )

    async def publish_bulk_operation_started(
        self,
        operation_id: str,
        user_id: str,
        operation_type: str,
        file_count: int,
        context: Optional[EventContext] = None
    ) -> str:
        """Publish bulk operation started event.

        Args:
            operation_id: Operation ID
            user_id: User who started the operation
            operation_type: Type of operation
            file_count: Number of files
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "operation_id": operation_id,
            "operation_type": operation_type,
            "file_count": file_count
        }

        return await self.publish_event(
            EventType.BULK_OPERATION_STARTED,
            user_id=user_id,
            data=data,
            context=context
        )

    async def publish_bulk_operation_progress(
        self,
        operation_id: str,
        user_id: str,
        progress: int,
        total: int,
        successful: int,
        failed: int,
        context: Optional[EventContext] = None
    ) -> str:
        """Publish bulk operation progress event.

        Args:
            operation_id: Operation ID
            user_id: User who started the operation
            progress: Current progress
            total: Total files
            successful: Successful operations
            failed: Failed operations
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "operation_id": operation_id,
            "progress": progress,
            "total": total,
            "successful": successful,
            "failed": failed,
            "percentage": (progress / total * 100) if total > 0 else 0
        }

        return await self.publish_event(
            EventType.BULK_OPERATION_PROGRESS,
            user_id=user_id,
            data=data,
            context=context
        )

    async def publish_bulk_operation_completed(
        self,
        operation_id: str,
        user_id: str,
        total: int,
        successful: int,
        failed: int,
        duration: float,
        context: Optional[EventContext] = None
    ) -> str:
        """Publish bulk operation completed event.

        Args:
            operation_id: Operation ID
            user_id: User who started the operation
            total: Total files
            successful: Successful operations
            failed: Failed operations
            duration: Operation duration
            context: Event context

        Returns:
            Event ID
        """
        data = {
            "operation_id": operation_id,
            "total": total,
            "successful": successful,
            "failed": failed,
            "duration": duration,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }

        return await self.publish_event(
            EventType.BULK_OPERATION_COMPLETED,
            user_id=user_id,
            data=data,
            context=context
        )

    def register_handler(
        self,
        event_type: EventType,
        handler: EventHandler,
        handler_name: Optional[str] = None
    ):
        """Register event handler for specific event type.

        Args:
            event_type: Event type to handle
            handler: Handler function
            handler_name: Name of the handler (for statistics)
        """
        with self._lock:
            self._handlers[event_type].append(handler)
            logger.debug(f"Handler registered for {event_type.value}")

    def register_global_handler(self, handler: EventHandler, handler_name: Optional[str] = None):
        """Register global event handler.

        Args:
            handler: Handler function
            handler_name: Name of the handler (for statistics)
        """
        with self._lock:
            self._global_handlers.append(handler)
            logger.debug("Global handler registered")

    def unregister_handler(self, event_type: EventType, handler: EventHandler):
        """Unregister event handler.

        Args:
            event_type: Event type
            handler: Handler function
        """
        with self._lock:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Handler unregistered for {event_type.value}")

    def unregister_global_handler(self, handler: EventHandler):
        """Unregister global event handler.

        Args:
            handler: Handler function
        """
        with self._lock:
            if handler in self._global_handlers:
                self._global_handlers.remove(handler)
                logger.debug("Global handler unregistered")

    async def _event_worker(self):
        """Background worker to process events."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event worker: {str(e)}")

    async def _process_event(self, event: FileOperationEvent):
        """Process a single event.

        Args:
            event: Event to process
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Record event statistics
            self._statistics.record_event(event)

            # Add to history
            self._add_to_history(event)

            # Get handlers
            handlers = self._handlers.get(event.event_type, []) + self._global_handlers

            if not handlers:
                logger.debug(f"No handlers registered for {event.event_type.value}")
                return

            # Execute handlers
            tasks = []
            for handler in handlers:
                handler_name = getattr(handler, '__name__', str(handler))
                task = asyncio.create_task(
                    self._execute_handler(handler, event, handler_name)
                )
                tasks.append(task)

            # Wait for all handlers to complete
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {str(e)}")
        finally:
            duration = asyncio.get_event_loop().time() - start_time
            logger.debug(f"Event {event.event_id} processed in {duration:.3f}s")

    async def _execute_handler(
        self,
        handler: EventHandler,
        event: FileOperationEvent,
        handler_name: str
    ):
        """Execute a single handler.

        Args:
            handler: Handler function
            event: Event to process
            handler_name: Handler name for statistics
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Check if handler is async
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(self._executor, handler, event)

            duration = asyncio.get_event_loop().time() - start_time
            self._statistics.record_handler_execution(handler_name, duration, True)

        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            self._statistics.record_handler_execution(handler_name, duration, False, e)
            logger.error(f"Error in handler {handler_name}: {str(e)}", exc_info=True)

    def _add_to_history(self, event: FileOperationEvent):
        """Add event to history.

        Args:
            event: Event to add
        """
        with self._lock:
            self._event_history.append(event)

            # Trim history if needed
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]

    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        file_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[FileOperationEvent]:
        """Get event history with filtering.

        Args:
            event_type: Filter by event type
            file_id: Filter by file ID
            user_id: Filter by user ID
            limit: Maximum number of events to return

        Returns:
            List of filtered events
        """
        with self._lock:
            events = self._event_history

            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]

            if file_id:
                events = [e for e in events if e.file_id == file_id]

            if user_id:
                events = [e for e in events if e.user_id == user_id]

            # Return most recent events
            return events[-limit:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get event manager statistics.

        Returns:
            Statistics dictionary
        """
        return self._statistics.get_statistics()

    def clear_history(self):
        """Clear event history."""
        with self._lock:
            self._event_history.clear()
            logger.info("Event history cleared")

    def get_queue_size(self) -> int:
        """Get current event queue size.

        Returns:
            Queue size
        """
        return self._event_queue.qsize()


# Global event manager instance
_event_manager: Optional[FileOperationEventManager] = None


def get_event_manager() -> FileOperationEventManager:
    """Get global event manager instance.

    Returns:
        Event manager instance
    """
    global _event_manager
    if _event_manager is None:
        _event_manager = FileOperationEventManager()
    return _event_manager


async def initialize_event_manager(max_workers: int = 10) -> FileOperationEventManager:
    """Initialize global event manager.

    Args:
        max_workers: Maximum worker threads

    Returns:
        Event manager instance
    """
    global _event_manager
    if _event_manager is None:
        _event_manager = FileOperationEventManager(max_workers=max_workers)
    await _event_manager.start()
    return _event_manager


async def shutdown_event_manager():
    """Shutdown global event manager."""
    global _event_manager
    if _event_manager:
        await _event_manager.stop()
        _event_manager = None


# Convenience functions for publishing events
async def publish_file_created(
    file_id: UUID,
    user_id: str,
    file_name: str,
    file_size: int,
    mime_type: str,
    context: Optional[EventContext] = None
) -> str:
    """Publish file created event."""
    manager = get_event_manager()
    return await manager.publish_file_created(
        file_id, user_id, file_name, file_size, mime_type, context
    )


async def publish_file_updated(
    file_id: UUID,
    user_id: str,
    changes: Dict[str, Any],
    context: Optional[EventContext] = None
) -> str:
    """Publish file updated event."""
    manager = get_event_manager()
    return await manager.publish_file_updated(
        file_id, user_id, changes, context
    )


async def publish_file_deleted(
    file_id: UUID,
    user_id: str,
    permanent: bool = False,
    context: Optional[EventContext] = None
) -> str:
    """Publish file deleted event."""
    manager = get_event_manager()
    return await manager.publish_file_deleted(
        file_id, user_id, permanent, context
    )


# Decorator for event handlers
def event_handler(event_type: EventType):
    """Decorator for registering event handlers.

    Args:
        event_type: Event type to handle

    Usage:
        @event_handler(EventType.FILE_CREATED)
        async def handle_file_created(event):
            print(f"File created: {event.file_id}")
    """
    def decorator(func: EventHandler) -> EventHandler:
        # Register handler
        manager = get_event_manager()
        manager.register_handler(event_type, func, func.__name__)
        return func
    return decorator
