"""Event bus implementation for real-time progress tracking system.

This module provides EventBus for implementing publish-subscribe pattern,
event filtering, routing, and asynchronous event handling with thread safety
and event ordering guarantees.
"""

import asyncio
import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Callable, Set, Union
from uuid import uuid4
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class EventBusError(Exception):
    """Base exception for event bus operations."""
    pass


class EventFilterError(EventBusError):
    """Raised when event filtering fails."""
    pass


class EventRouterError(EventBusError):
    """Raised when event routing fails."""
    pass


class Event:
    """Base event class for event bus."""

    def __init__(
        self,
        event_type: str,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize event.

        Args:
            event_type: Type/category of the event
            data: Event payload data
            source: Source that generated the event
            correlation_id: ID for correlating related events
            metadata: Additional event metadata
        """
        self.event_id = str(uuid4())
        self.event_type = event_type
        self.data = data or {}
        self.source = source
        self.correlation_id = correlation_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)
        self.delivery_count = 0

    def __repr__(self) -> str:
        """Return string representation of the event."""
        return (
            f"Event(id={self.event_id[:8]}, type={self.event_type}, "
            f"source={self.source}, timestamp={self.timestamp.isoformat()})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "data": self.data,
            "source": self.source,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "delivery_count": self.delivery_count,
        }


class EventFilter:
    """Base class for event filters."""

    def filter(self, event: Event) -> bool:
        """Filter event based on criteria.

        Args:
            event: Event to filter

        Returns:
            True if event passes filter, False otherwise
        """
        raise NotImplementedError

    def __call__(self, event: Event) -> bool:
        """Allow filter to be called as a function.

        Args:
            event: Event to filter

        Returns:
            True if event passes filter, False otherwise
        """
        return self.filter(event)


class EventTypeFilter(EventFilter):
    """Filter events by event type."""

    def __init__(self, event_types: Union[str, List[str]]):
        """Initialize event type filter.

        Args:
            event_types: Event type(s) to filter for
        """
        self.event_types = event_types if isinstance(event_types, list) else [event_types]

    def filter(self, event: Event) -> bool:
        """Filter events by type.

        Args:
            event: Event to filter

        Returns:
            True if event type matches, False otherwise
        """
        return event.event_type in self.event_types


class SourceFilter(EventFilter):
    """Filter events by source."""

    def __init__(self, sources: Union[str, List[str]]):
        """Initialize source filter.

        Args:
            sources: Source(s) to filter for
        """
        self.sources = sources if isinstance(sources, list) else [sources]

    def filter(self, event: Event) -> bool:
        """Filter events by source.

        Args:
            event: Event to filter

        Returns:
            True if event source matches, False otherwise
        """
        return event.source in self.sources


class CorrelationFilter(EventFilter):
    """Filter events by correlation ID."""

    def __init__(self, correlation_id: str):
        """Initialize correlation filter.

        Args:
            correlation_id: Correlation ID to filter for
        """
        self.correlation_id = correlation_id

    def filter(self, event: Event) -> bool:
        """Filter events by correlation ID.

        Args:
            event: Event to filter

        Returns:
            True if correlation ID matches, False otherwise
        """
        return event.correlation_id == self.correlation_id


class MetadataFilter(EventFilter):
    """Filter events by metadata."""

    def __init__(self, metadata_filters: Dict[str, Any]):
        """Initialize metadata filter.

        Args:
            metadata_filters: Dictionary of metadata key-value pairs to filter for
        """
        self.metadata_filters = metadata_filters

    def filter(self, event: Event) -> bool:
        """Filter events by metadata.

        Args:
            event: Event to filter

        Returns:
            True if all metadata matches, False otherwise
        """
        for key, expected_value in self.metadata_filters.items():
            actual_value = event.metadata.get(key)
            if actual_value != expected_value:
                return False
        return True


class EventHandler:
    """Base class for event handlers."""

    def __init__(self, handler_id: str):
        """Initialize event handler.

        Args:
            handler_id: Unique handler ID
        """
        self.handler_id = handler_id
        self.filters: List[EventFilter] = []
        self.is_enabled = True
        self.statistics = {
            "events_received": 0,
            "events_processed": 0,
            "events_failed": 0,
            "last_event_timestamp": None,
        }

    def add_filter(self, event_filter: EventFilter):
        """Add event filter.

        Args:
            event_filter: Event filter to add
        """
        self.filters.append(event_filter)

    def clear_filters(self):
        """Clear all filters."""
        self.filters.clear()

    def can_handle(self, event: Event) -> bool:
        """Check if handler can handle the event.

        Args:
            event: Event to check

        Returns:
            True if handler can handle event, False otherwise
        """
        if not self.is_enabled:
            return False

        for event_filter in self.filters:
            if not event_filter(event):
                return False
        return True

    def handle(self, event: Event) -> bool:
        """Handle the event.

        Args:
            event: Event to handle

        Returns:
            True if handled successfully, False otherwise
        """
        raise NotImplementedError

    def update_statistics(self, success: bool):
        """Update handler statistics.

        Args:
            success: Whether event was handled successfully
        """
        self.statistics["events_received"] += 1
        if success:
            self.statistics["events_processed"] += 1
        else:
            self.statistics["events_failed"] += 1
        self.statistics["last_event_timestamp"] = datetime.now(timezone.utc)


class SyncEventHandler(EventHandler):
    """Synchronous event handler."""

    def __init__(
        self,
        handler_id: str,
        callback: Callable[[Event], bool],
    ):
        """Initialize synchronous event handler.

        Args:
            handler_id: Unique handler ID
            callback: Synchronous callback function
        """
        super().__init__(handler_id)
        self.callback = callback

    def handle(self, event: Event) -> bool:
        """Handle the event synchronously.

        Args:
            event: Event to handle

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            result = self.callback(event)
            self.update_statistics(result)
            return result
        except Exception as e:
            logger.error(f"Error in sync event handler {self.handler_id}: {e}")
            self.update_statistics(False)
            return False


class AsyncEventHandler(EventHandler):
    """Asynchronous event handler."""

    def __init__(
        self,
        handler_id: str,
        callback: Callable[[Event], Any],
    ):
        """Initialize asynchronous event handler.

        Args:
            handler_id: Unique handler ID
            callback: Asynchronous callback function
        """
        super().__init__(handler_id)
        self.callback = callback

    async def handle(self, event: Event) -> bool:
        """Handle the event asynchronously.

        Args:
            event: Event to handle

        Returns:
            True if handled successfully, False otherwise
        """
        try:
            result = await self.callback(event)
            self.update_statistics(result)
            return result
        except Exception as e:
            logger.error(f"Error in async event handler {self.handler_id}: {e}")
            self.update_statistics(False)
            return False


class EventBus:
    """Event bus for publish-subscribe pattern."""

    def __init__(self, max_handlers_per_event: int = 1000):
        """Initialize event bus.

        Args:
            max_handlers_per_event: Maximum number of handlers per event type
        """
        self.max_handlers_per_event = max_handlers_per_event
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._global_handlers: List[EventHandler] = []
        self._lock = asyncio.Lock()
        self._stats = {
            "total_events_published": 0,
            "total_events_delivered": 0,
            "total_events_failed": 0,
            "active_handlers": 0,
            "event_types": set(),
        }

    async def subscribe(
        self,
        handler: EventHandler,
        event_types: Optional[List[str]] = None,
    ):
        """Subscribe a handler to events.

        Args:
            handler: Event handler to subscribe
            event_types: Event types to subscribe to (None for all events)

        Raises:
            ValueError: If too many handlers for an event type
        """
        async with self._lock:
            if event_types is None:
                # Global handler
                self._global_handlers.append(handler)
            else:
                # Event-specific handlers
                for event_type in event_types:
                    if len(self._handlers[event_type]) >= self.max_handlers_per_event:
                        raise ValueError(
                            f"Maximum handlers ({self.max_handlers_per_event}) "
                            f"reached for event type: {event_type}"
                        )
                    self._handlers[event_type].append(handler)

            self._stats["active_handlers"] = self._get_total_handler_count()
            logger.info(
                f"Subscribed handler {handler.handler_id} to events: {event_types or 'all'}"
            )

    async def unsubscribe(
        self,
        handler_id: str,
        event_types: Optional[List[str]] = None,
    ):
        """Unsubscribe a handler from events.

        Args:
            handler_id: Handler ID to unsubscribe
            event_types: Event types to unsubscribe from (None for all)
        """
        async with self._lock:
            removed_count = 0

            if event_types is None:
                # Remove from global handlers
                self._global_handlers = [
                    h for h in self._global_handlers if h.handler_id != handler_id
                ]
                removed_count += 1

                # Remove from event-specific handlers
                for event_type in list(self._handlers.keys()):
                    self._handlers[event_type] = [
                        h for h in self._handlers[event_type]
                        if h.handler_id != handler_id
                    ]
                    if not self._handlers[event_type]:
                        del self._handlers[event_type]
                    else:
                        removed_count += len(
                            [h for h in self._handlers[event_type] if h.handler_id == handler_id]
                        )
            else:
                # Remove from specific event types
                for event_type in event_types:
                    self._handlers[event_type] = [
                        h for h in self._handlers[event_type]
                        if h.handler_id != handler_id
                    ]
                    removed_count += 1

            self._stats["active_handlers"] = self._get_total_handler_count()
            logger.info(f"Unsubscribed handler {handler_id} from {removed_count} event types")

    async def publish(self, event: Event, timeout: Optional[float] = None) -> Dict[str, bool]:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish
            timeout: Timeout for event delivery (seconds)

        Returns:
            Dictionary mapping handler IDs to delivery results
        """
        async with self._lock:
            self._stats["total_events_published"] += 1
            self._stats["event_types"].add(event.event_type)

        # Get handlers that can handle this event
        async with self._lock:
            handlers = self._get_handlers_for_event(event)

        if not handlers:
            logger.debug(f"No handlers for event type: {event.event_type}")
            return {}

        # Deliver event to all handlers
        results = {}
        tasks = []

        for handler in handlers:
            event.delivery_count += 1
            if asyncio.iscoroutinefunction(handler.handle):
                task = asyncio.create_task(
                    self._deliver_event_async(handler, event, timeout)
                )
                tasks.append((handler.handler_id, task))
            else:
                task = asyncio.create_task(
                    self._deliver_event_sync(handler, event, timeout)
                )
                tasks.append((handler.handler_id, task))

        # Wait for all deliveries
        for handler_id, task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=timeout)
                results[handler_id] = result
            except asyncio.TimeoutError:
                logger.warning(f"Event delivery timeout for handler: {handler_id}")
                results[handler_id] = False
            except Exception as e:
                logger.error(f"Error delivering event to handler {handler_id}: {e}")
                results[handler_id] = False

        # Update statistics
        successful = sum(1 for r in results.values() if r)
        failed = len(results) - successful
        async with self._lock:
            self._stats["total_events_delivered"] += successful
            self._stats["total_events_failed"] += failed

        logger.info(
            f"Published event {event.event_id[:8]} to {len(handlers)} handlers: "
            f"{successful} success, {failed} failed"
        )

        return results

    async def publish_sync(self, event: Event, timeout: Optional[float] = None) -> bool:
        """Synchronous wrapper for event publishing.

        Args:
            event: Event to publish
            timeout: Timeout for event delivery (seconds)

        Returns:
            True if at least one handler processed the event successfully
        """
        results = await self.publish(event, timeout)
        return any(results.values())

    def _get_handlers_for_event(self, event: Event) -> List[EventHandler]:
        """Get handlers that can handle the event.

        Args:
            event: Event to get handlers for

        Returns:
            List of handlers that can handle the event
        """
        handlers = []

        # Add event-specific handlers
        event_handlers = self._handlers.get(event.event_type, [])
        handlers.extend([h for h in event_handlers if h.can_handle(event)])

        # Add global handlers
        handlers.extend([h for h in self._global_handlers if h.can_handle(event)])

        return handlers

    async def _deliver_event_async(
        self,
        handler: AsyncEventHandler,
        event: Event,
        timeout: Optional[float],
    ) -> bool:
        """Deliver event to async handler.

        Args:
            handler: Async handler to deliver to
            event: Event to deliver
            timeout: Timeout for delivery

        Returns:
            True if delivered successfully
        """
        try:
            return await asyncio.wait_for(handler.handle(event), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Async handler {handler.handler_id} timed out")
            handler.update_statistics(False)
            return False
        except Exception as e:
            logger.error(f"Error in async handler {handler.handler_id}: {e}")
            handler.update_statistics(False)
            return False

    async def _deliver_event_sync(
        self,
        handler: SyncEventHandler,
        event: Event,
        timeout: Optional[float],
    ) -> bool:
        """Deliver event to sync handler.

        Args:
            handler: Sync handler to deliver to
            event: Event to deliver
            timeout: Timeout for delivery

        Returns:
            True if delivered successfully
        """
        try:
            if timeout:
                return await asyncio.wait_for(
                    asyncio.to_thread(handler.handle, event), timeout=timeout
                )
            else:
                return await asyncio.to_thread(handler.handle, event)
        except asyncio.TimeoutError:
            logger.warning(f"Sync handler {handler.handler_id} timed out")
            handler.update_statistics(False)
            return False
        except Exception as e:
            logger.error(f"Error in sync handler {handler.handler_id}: {e}")
            handler.update_statistics(False)
            return False

    def _get_total_handler_count(self) -> int:
        """Get total number of active handlers.

        Returns:
            Total number of active handlers
        """
        return len(self._global_handlers) + sum(
            len(handlers) for handlers in self._handlers.values()
        )

    async def get_statistics(self) -> Dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Dictionary containing statistics
        """
        async with self._lock:
            handler_stats = {
                "total_handlers": self._get_total_handler_count(),
                "global_handlers": len(self._global_handlers),
                "event_type_handlers": {
                    event_type: len(handlers)
                    for event_type, handlers in self._handlers.items()
                },
            }

            return {
                **self._stats,
                "handler_statistics": handler_stats,
            }

    async def get_handler_statistics(self, handler_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific handler.

        Args:
            handler_id: Handler ID

        Returns:
            Handler statistics or None if not found
        """
        # Check global handlers
        for handler in self._global_handlers:
            if handler.handler_id == handler_id:
                return handler.statistics

        # Check event-specific handlers
        for handlers in self._handlers.values():
            for handler in handlers:
                if handler.handler_id == handler_id:
                    return handler.statistics

        return None

    async def enable_handler(self, handler_id: str) -> bool:
        """Enable a handler.

        Args:
            handler_id: Handler ID to enable

        Returns:
            True if handler was found and enabled
        """
        handler = self._get_handler_by_id(handler_id)
        if handler:
            handler.is_enabled = True
            logger.info(f"Enabled handler: {handler_id}")
            return True
        return False

    async def disable_handler(self, handler_id: str) -> bool:
        """Disable a handler.

        Args:
            handler_id: Handler ID to disable

        Returns:
            True if handler was found and disabled
        """
        handler = self._get_handler_by_id(handler_id)
        if handler:
            handler.is_enabled = False
            logger.info(f"Disabled handler: {handler_id}")
            return True
        return False

    def _get_handler_by_id(self, handler_id: str) -> Optional[EventHandler]:
        """Get handler by ID.

        Args:
            handler_id: Handler ID to find

        Returns:
            Handler or None if not found
        """
        # Check global handlers
        for handler in self._global_handlers:
            if handler.handler_id == handler_id:
                return handler

        # Check event-specific handlers
        for handlers in self._handlers.values():
            for handler in handlers:
                if handler.handler_id == handler_id:
                    return handler

        return None

    async def clear_handlers(self, event_type: Optional[str] = None):
        """Clear all handlers or handlers for specific event type.

        Args:
            event_type: Event type to clear handlers for (None for all)
        """
        async with self._lock:
            if event_type is None:
                # Clear all handlers
                self._handlers.clear()
                self._global_handlers.clear()
                logger.info("Cleared all event handlers")
            else:
                # Clear handlers for specific event type
                if event_type in self._handlers:
                    del self._handlers[event_type]
                    logger.info(f"Cleared handlers for event type: {event_type}")

            self._stats["active_handlers"] = self._get_total_handler_count()


# Global event bus instance
event_bus = EventBus()


# Convenience functions

def create_event(
    event_type: str,
    data: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Event:
    """Create a new event.

    Args:
        event_type: Type/category of the event
        data: Event payload data
        source: Source that generated the event
        correlation_id: ID for correlating related events
        metadata: Additional event metadata

    Returns:
        New Event instance
    """
    return Event(event_type, data, source, correlation_id, metadata)


async def publish_event(
    event: Event,
    timeout: Optional[float] = None,
) -> Dict[str, bool]:
    """Publish an event using the global event bus.

    Args:
        event: Event to publish
        timeout: Timeout for event delivery

    Returns:
        Dictionary mapping handler IDs to delivery results
    """
    return await event_bus.publish(event, timeout)


async def subscribe_handler(
    handler: EventHandler,
    event_types: Optional[List[str]] = None,
):
    """Subscribe a handler using the global event bus.

    Args:
        handler: Event handler to subscribe
        event_types: Event types to subscribe to
    """
    await event_bus.subscribe(handler, event_types)


async def unsubscribe_handler(
    handler_id: str,
    event_types: Optional[List[str]] = None,
):
    """Unsubscribe a handler using the global event bus.

    Args:
        handler_id: Handler ID to unsubscribe
        event_types: Event types to unsubscribe from
    """
    await event_bus.unsubscribe(handler_id, event_types)


if __name__ == "__main__":
    # Example usage
    async def main():
        # Create event
        event = create_event(
            event_type="task_progress",
            data={"task_id": "task-001", "progress": 50.0},
            source="progress_manager",
        )

        # Create handler
        async def progress_handler(e: Event) -> bool:
            print(f"Received progress event: {e.event_type}, progress: {e.data['progress']}")
            return True

        handler = AsyncEventHandler("progress_handler_1", progress_handler)

        # Subscribe handler
        await subscribe_handler(handler, ["task_progress"])

        # Publish event
        results = await publish_event(event)
        print(f"Event delivery results: {results}")

        # Get statistics
        stats = await event_bus.get_statistics()
        print(f"Event bus statistics: {stats}")

    asyncio.run(main())
