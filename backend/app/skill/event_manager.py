"""Skill event manager.

This module provides the SkillEventManager class for implementing
event-driven architecture with publish-subscribe patterns for skill operations.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from asyncio import Lock
import json

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Skill event types."""

    # Skill lifecycle events
    SKILL_CREATED = "skill.created"
    SKILL_UPDATED = "skill.updated"
    SKILL_DELETED = "skill.deleted"

    # State change events
    SKILL_ACTIVATED = "skill.activated"
    SKILL_DEACTIVATED = "skill.deactivated"
    SKILL_DEPRECATED = "skill.deprecated"
    SKILL_ARCHIVED = "skill.archived"

    # Version events
    VERSION_CREATED = "version.created"
    VERSION_UPDATED = "version.updated"
    VERSION_DELETED = "version.deleted"
    VERSION_RESTORED = "version.restored"

    # Category events
    CATEGORY_CREATED = "category.created"
    CATEGORY_UPDATED = "category.updated"
    CATEGORY_DELETED = "category.deleted"

    # Tag events
    TAG_CREATED = "tag.created"
    TAG_UPDATED = "tag.updated"
    TAG_DELETED = "tag.deleted"
    TAG_ADDED_TO_SKILL = "tag.added_to_skill"
    TAG_REMOVED_FROM_SKILL = "tag.removed_from_skill"

    # Import/Export events
    IMPORT_STARTED = "import.started"
    IMPORT_COMPLETED = "import.completed"
    IMPORT_FAILED = "import.failed"
    EXPORT_STARTED = "export.started"
    EXPORT_COMPLETED = "export.completed"
    EXPORT_FAILED = "export.failed"

    # Analytics events
    SKILL_VIEWED = "skill.viewed"
    SKILL_DOWNLOADED = "skill.downloaded"
    SKILL_RATED = "skill.rated"
    SKILL_LIKED = "skill.liked"

    # Error events
    ERROR_OCCURRED = "error.occurred"
    VALIDATION_FAILED = "validation.failed"


@dataclass
class SkillEvent:
    """Skill event data structure.

    Represents an event in the skill management system.
    """

    event_type: EventType
    event_id: str
    skill_id: Optional[str] = None
    user_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    source: Optional[str] = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        """Initialize event after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary.

        Returns:
            Event as dictionary
        """
        return {
            "event_type": self.event_type.value,
            "event_id": self.event_id,
            "skill_id": self.skill_id,
            "user_id": self.user_id,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "correlation_id": self.correlation_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SkillEvent":
        """Create event from dictionary.

        Args:
            data: Event dictionary

        Returns:
            SkillEvent instance
        """
        return cls(
            event_type=EventType(data["event_type"]),
            event_id=data["event_id"],
            skill_id=data.get("skill_id"),
            user_id=data.get("user_id"),
            data=data.get("data"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            source=data.get("source"),
            correlation_id=data.get("correlation_id"),
        )


class EventHandler:
    """Base class for event handlers."""

    async def handle(self, event: SkillEvent) -> None:
        """Handle an event.

        Args:
            event: Event to handle

        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement handle method")


class LoggingEventHandler(EventHandler):
    """Event handler that logs all events."""

    def __init__(self, logger: logging.Logger = None):
        """Initialize logging handler.

        Args:
            logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)

    async def handle(self, event: SkillEvent) -> None:
        """Log event.

        Args:
            event: Event to log
        """
        self.logger.info(
            f"Event: {event.event_type.value} - "
            f"ID: {event.event_id} - "
            f"Skill: {event.skill_id or 'N/A'}"
        )


class NotificationEventHandler(EventHandler):
    """Event handler for sending notifications."""

    def __init__(self, notification_service=None):
        """Initialize notification handler.

        Args:
            notification_service: Service for sending notifications
        """
        self.notification_service = notification_service

    async def handle(self, event: SkillEvent) -> None:
        """Send notification for important events.

        Args:
            event: Event to handle
        """
        if event.event_type in [
            EventType.SKILL_CREATED,
            EventType.SKILL_UPDATED,
            EventType.SKILL_DEPRECATED,
            EventType.SKILL_ARCHIVED,
        ]:
            # Send notification
            logger.info(f"Would send notification for event: {event.event_type.value}")

            if self.notification_service:
                await self.notification_service.send_notification(
                    event_type=event.event_type.value,
                    data=event.data,
                )


class AnalyticsEventHandler(EventHandler):
    """Event handler for analytics tracking."""

    def __init__(self, analytics_service=None):
        """Initialize analytics handler.

        Args:
            analytics_service: Service for tracking analytics
        """
        self.analytics_service = analytics_service

    async def handle(self, event: SkillEvent) -> None:
        """Track analytics event.

        Args:
            event: Event to track
        """
        if event.event_type in [
            EventType.SKILL_VIEWED,
            EventType.SKILL_DOWNLOADED,
            EventType.SKILL_RATED,
            EventType.SKILL_LIKED,
        ]:
            logger.info(f"Would track analytics for event: {event.event_type.value}")

            if self.analytics_service:
                await self.analytics_service.track_event(
                    event_type=event.event_type.value,
                    skill_id=event.skill_id,
                    user_id=event.user_id,
                    data=event.data,
                )


class AuditEventHandler(EventHandler):
    """Event handler for audit logging."""

    def __init__(self, audit_service=None):
        """Initialize audit handler.

        Args:
            audit_service: Service for audit logging
        """
        self.audit_service = audit_service

    async def handle(self, event: SkillEvent) -> None:
        """Log audit event.

        Args:
            event: Event to audit
        """
        if event.event_type in [
            EventType.SKILL_CREATED,
            EventType.SKILL_UPDATED,
            EventType.SKILL_DELETED,
            EventType.SKILL_ACTIVATED,
            EventType.SKILL_DEACTIVATED,
        ]:
            logger.info(f"Would audit log event: {event.event_type.value}")

            if self.audit_service:
                await self.audit_service.log_event(
                    event_type=event.event_type.value,
                    skill_id=event.skill_id,
                    user_id=event.user_id,
                    data=event.data,
                )


class SkillEventManager:
    """Event manager for skill-related events.

    Implements publish-subscribe pattern for handling skill events
    with support for multiple handlers and event filtering.
    """

    def __init__(self):
        """Initialize event manager."""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []
        self._event_history: List[SkillEvent] = []
        self._max_history_size = 1000
        self._lock = Lock()
        self._is_running = False

        # Register default handlers
        self.register_handler(EventType.SKILL_CREATED, LoggingEventHandler())
        self.register_handler(EventType.SKILL_UPDATED, LoggingEventHandler())
        self.register_handler(EventType.SKILL_DELETED, LoggingEventHandler())

    # ================================
    # Event Publishing
    # ================================

    async def publish_event(
        self,
        event_type: EventType,
        skill_id: Optional[str] = None,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Publish an event.

        Args:
            event_type: Type of event
            skill_id: Associated skill ID
            user_id: Associated user ID
            event_data: Event data
            source: Event source
            correlation_id: Correlation ID for tracing

        Returns:
            Event ID
        """
        # Generate event ID
        import uuid
        event_id = str(uuid.uuid4())

        # Create event
        event = SkillEvent(
            event_type=event_type,
            event_id=event_id,
            skill_id=skill_id,
            user_id=user_id,
            data=data,
            source=source,
            correlation_id=correlation_id,
        )

        # Store in history
        await self._add_to_history(event)

        # Notify handlers
        await self._notify_handlers(event)

        logger.debug(f"Published event: {event_type.value} (ID: {event_id})")
        return event_id

    async def publish_skill_created(
        self,
        skill_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish skill created event.

        Args:
            skill_id: Skill ID
            user_id: User who created the skill
            data: Additional event data
            source: Event source

        Returns:
            Event ID
        """
        return await self.publish_event(
            event_type=EventType.SKILL_CREATED,
            skill_id=skill_id,
            user_id=user_id,
            data=data,
            source=source,
        )

    async def publish_skill_updated(
        self,
        skill_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish skill updated event.

        Args:
            skill_id: Skill ID
            user_id: User who updated the skill
            data: Additional event data
            source: Event source

        Returns:
            Event ID
        """
        return await self.publish_event(
            event_type=EventType.SKILL_UPDATED,
            skill_id=skill_id,
            user_id=user_id,
            data=data,
            source=source,
        )

    async def publish_skill_deleted(
        self,
        skill_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish skill deleted event.

        Args:
            skill_id: Skill ID
            user_id: User who deleted the skill
            data: Additional event data
            source: Event source

        Returns:
            Event ID
        """
        return await self.publish_event(
            event_type=EventType.SKILL_DELETED,
            skill_id=skill_id,
            user_id=user_id,
            data=data,
            source=source,
        )

    async def publish_skill_state_changed(
        self,
        event_type: EventType,
        skill_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish skill state change event.

        Args:
            event_type: State change event type
            skill_id: Skill ID
            user_id: User who changed the state
            data: Additional event data
            source: Event source

        Returns:
            Event ID
        """
        if event_type not in [
            EventType.SKILL_ACTIVATED,
            EventType.SKILL_DEACTIVATED,
            EventType.SKILL_DEPRECATED,
            EventType.SKILL_ARCHIVED,
        ]:
            raise ValueError(f"Invalid state change event type: {event_type}")

        return await self.publish_event(
            event_type=event_type,
            skill_id=skill_id,
            user_id=user_id,
            data=data,
            source=source,
        )

    async def publish_version_event(
        self,
        event_type: EventType,
        skill_id: str,
        version_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish version event.

        Args:
            event_type: Version event type
            skill_id: Skill ID
            version_id: Version ID
            user_id: User who performed the action
            data: Additional event data
            source: Event source

        Returns:
            Event ID
        """
        if event_type not in [
            EventType.VERSION_CREATED,
            EventType.VERSION_UPDATED,
            EventType.VERSION_DELETED,
            EventType.VERSION_RESTORED,
        ]:
            raise ValueError(f"Invalid version event type: {event_type}")

        event_data = data or {}
        event_data["version_id"] = version_id

        return await self.publish_event(
            event_type=event_type,
            skill_id=skill_id,
            user_id=user_id,
            data=event_data,
            source=source,
        )

    async def publish_analytics_event(
        self,
        event_type: EventType,
        skill_id: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish analytics event.

        Args:
            event_type: Analytics event type
            skill_id: Skill ID
            user_id: User who performed the action
            data: Additional event data
            source: Event source

        Returns:
            Event ID
        """
        if event_type not in [
            EventType.SKILL_VIEWED,
            EventType.SKILL_DOWNLOADED,
            EventType.SKILL_RATED,
            EventType.SKILL_LIKED,
        ]:
            raise ValueError(f"Invalid analytics event type: {event_type}")

        return await self.publish_event(
            event_type=event_type,
            skill_id=skill_id,
            user_id=user_id,
            data=data,
            source=source,
        )

    async def publish_error_event(
        self,
        error_type: EventType,
        skill_id: Optional[str] = None,
        user_id: Optional[str] = None,
        error_message: Optional[str] = None,
        error_data: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
    ) -> str:
        """Publish error event.

        Args:
            error_type: Error event type
            skill_id: Associated skill ID
            user_id: Associated user ID
            error_message: Error message
            error_data: Additional error data
            source: Event source

        Returns:
            Event ID
        """
        if error_type not in [
            EventType.ERROR_OCCURRED,
            EventType.VALIDATION_FAILED,
        ]:
            raise ValueError(f"Invalid error event type: {error_type}")

        event_data = error_data or {}
        if error_message:
            event_data["error_message"] = error_message

        return await self.publish_event(
            event_type=error_type,
            skill_id=skill_id,
            user_id=user_id,
            data=event_data,
            source=source,
        )

    # ================================
    # Handler Management
    # ================================

    def register_handler(
        self,
        event_type: EventType,
        handler: EventHandler,
    ):
        """Register an event handler for a specific event type.

        Args:
            event_type: Event type to handle
            handler: Handler instance
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event: {event_type.value}")

    def register_global_handler(self, handler: EventHandler):
        """Register a global event handler that receives all events.

        Args:
            handler: Handler instance
        """
        self._global_handlers.append(handler)
        logger.debug("Registered global event handler")

    def unregister_handler(
        self,
        event_type: EventType,
        handler: EventHandler,
    ):
        """Unregister an event handler.

        Args:
            event_type: Event type
            handler: Handler instance
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.debug(f"Unregistered handler for event: {event_type.value}")
            except ValueError:
                pass  # Handler not found

    def unregister_global_handler(self, handler: EventHandler):
        """Unregister a global event handler.

        Args:
            handler: Handler instance
        """
        try:
            self._global_handlers.remove(handler)
            logger.debug("Unregistered global event handler")
        except ValueError:
            pass  # Handler not found

    def clear_handlers(self, event_type: Optional[EventType] = None):
        """Clear all handlers.

        Args:
            event_type: Specific event type to clear (None for all)
        """
        if event_type:
            self._handlers.pop(event_type, None)
            logger.debug(f"Cleared handlers for event: {event_type.value}")
        else:
            self._handlers.clear()
            self._global_handlers.clear()
            logger.debug("Cleared all event handlers")

    # ================================
    # Event History
    # ================================

    async def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        skill_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SkillEvent]:
        """Get event history with filtering.

        Args:
            event_type: Filter by event type
            skill_id: Filter by skill ID
            user_id: Filter by user ID
            limit: Maximum number of events to return
            offset: Offset for pagination

        Returns:
            List of filtered events
        """
        async with self._lock:
            events = self._event_history

            # Apply filters
            if event_type:
                events = [e for e in events if e.event_type == event_type]

            if skill_id:
                events = [e for e in events if e.skill_id == skill_id]

            if user_id:
                events = [e for e in events if e.user_id == user_id]

            # Sort by timestamp (newest first)
            events.sort(key=lambda e: e.timestamp, reverse=True)

            # Apply pagination
            return events[offset:offset + limit]

    async def get_event_by_id(self, event_id: str) -> Optional[SkillEvent]:
        """Get event by ID.

        Args:
            event_id: Event ID

        Returns:
            Event or None if not found
        """
        async with self._lock:
            for event in self._event_history:
                if event.event_id == event_id:
                    return event
            return None

    async def clear_event_history(self):
        """Clear event history."""
        async with self._lock:
            self._event_history.clear()
            logger.debug("Cleared event history")

    # ================================
    # Event Statistics
    # ================================

    async def get_event_stats(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get event statistics.

        Args:
            start_time: Start time for stats
            end_time: End time for stats

        Returns:
            Event statistics
        """
        async with self._lock:
            events = self._event_history

            # Apply time filter
            if start_time:
                events = [e for e in events if e.timestamp >= start_time]

            if end_time:
                events = [e for e in events if e.timestamp <= end_time]

            # Calculate stats
            total_events = len(events)

            # Count by type
            event_type_counts = {}
            for event in events:
                event_type = event.event_type.value
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1

            # Count by skill
            skill_counts = {}
            for event in events:
                if event.skill_id:
                    skill_counts[event.skill_id] = skill_counts.get(event.skill_id, 0) + 1

            # Count by user
            user_counts = {}
            for event in events:
                if event.user_id:
                    user_counts[event.user_id] = user_counts.get(event.user_id, 0) + 1

            # Time range
            if events:
                earliest_event = min(events, key=lambda e: e.timestamp)
                latest_event = max(events, key=lambda e: e.timestamp)
                time_range = {
                    "start": earliest_event.timestamp.isoformat(),
                    "end": latest_event.timestamp.isoformat(),
                }
            else:
                time_range = None

            return {
                "total_events": total_events,
                "event_type_counts": event_type_counts,
                "skill_counts": skill_counts,
                "user_counts": user_counts,
                "time_range": time_range,
                "handler_count": sum(len(handlers) for handlers in self._handlers.values()),
                "global_handler_count": len(self._global_handlers),
            }

    # ================================
    # Internal Methods
    # ================================

    async def _add_to_history(self, event: SkillEvent):
        """Add event to history.

        Args:
            event: Event to add
        """
        async with self._lock:
            self._event_history.append(event)

            # Trim history if too large
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]

    async def _notify_handlers(self, event: SkillEvent):
        """Notify all registered handlers of an event.

        Args:
            event: Event to notify
        """
        # Notify type-specific handlers
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                try:
                    await handler.handle(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")

        # Notify global handlers
        for handler in self._global_handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                logger.error(f"Error in global event handler: {e}")


# Global event manager instance
skill_event_manager = SkillEventManager()
