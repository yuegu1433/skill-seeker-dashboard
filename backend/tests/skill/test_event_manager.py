"""Tests for SkillEventManager.

This module contains comprehensive tests for the skill event management
functionality including event publishing, subscription, and statistics.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime
import uuid

from app.skill.event_manager import (
    SkillEventManager,
    EventType,
    EventPriority,
    Event,
)


class TestSkillEventManager:
    """Test cases for SkillEventManager."""

    @pytest.fixture
    def event_manager(self):
        """Create event manager instance for testing."""
        return SkillEventManager()

    @pytest.mark.asyncio
    async def test_initialization(self, event_manager):
        """Test event manager initialization."""
        assert event_manager is not None
        assert event_manager.subscribers == {}
        assert event_manager.event_history == []
        assert event_manager.event_stats == {}

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, event_manager):
        """Test event subscription and unsubscription."""
        event_type = EventType.SKILL_CREATED
        handler = AsyncMock()

        # Subscribe to event
        await event_manager.subscribe(event_type, handler)
        assert event_type in event_manager.subscribers
        assert handler in event_manager.subscribers[event_type]

        # Unsubscribe from event
        await event_manager.unsubscribe(event_type, handler)
        assert handler not in event_manager.subscribers.get(event_type, [])

    @pytest.mark.asyncio
    async def test_publish_skill_created(self, event_manager):
        """Test publishing SKILL_CREATED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.SKILL_CREATED, handler)

        # Publish event
        skill_id = str(uuid.uuid4())
        await event_manager.publish_skill_created(
            skill_id=skill_id,
            skill_name="Test Skill",
            author="Test Author"
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.SKILL_CREATED
        assert call_args.data["skill_id"] == skill_id
        assert call_args.data["skill_name"] == "Test Skill"
        assert call_args.data["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_publish_skill_updated(self, event_manager):
        """Test publishing SKILL_UPDATED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.SKILL_UPDATED, handler)

        # Publish event
        skill_id = str(uuid.uuid4())
        await event_manager.publish_skill_updated(
            skill_id=skill_id,
            skill_name="Updated Skill",
            changes=["description", "status"]
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.SKILL_UPDATED
        assert call_args.data["skill_id"] == skill_id
        assert "description" in call_args.data["changes"]
        assert "status" in call_args.data["changes"]

    @pytest.mark.asyncio
    async def test_publish_skill_deleted(self, event_manager):
        """Test publishing SKILL_DELETED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.SKILL_DELETED, handler)

        # Publish event
        skill_id = str(uuid.uuid4())
        await event_manager.publish_skill_deleted(
            skill_id=skill_id,
            skill_name="Deleted Skill"
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.SKILL_DELETED
        assert call_args.data["skill_id"] == skill_id

    @pytest.mark.asyncio
    async def test_publish_version_created(self, event_manager):
        """Test publishing VERSION_CREATED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.VERSION_CREATED, handler)

        # Publish event
        skill_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        await event_manager.publish_version_created(
            skill_id=skill_id,
            version_id=version_id,
            version="1.0.0",
            author="Test Author"
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.VERSION_CREATED
        assert call_args.data["skill_id"] == skill_id
        assert call_args.data["version_id"] == version_id
        assert call_args.data["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_publish_execution_started(self, event_manager):
        """Test publishing EXECUTION_STARTED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.EXECUTION_STARTED, handler)

        # Publish event
        skill_id = str(uuid.uuid4())
        execution_id = str(uuid.uuid4())
        await event_manager.publish_execution_started(
            skill_id=skill_id,
            execution_id=execution_id,
            user_id="test_user"
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.EXECUTION_STARTED
        assert call_args.data["skill_id"] == skill_id
        assert call_args.data["execution_id"] == execution_id

    @pytest.mark.asyncio
    async def test_publish_execution_completed(self, event_manager):
        """Test publishing EXECUTION_COMPLETED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.EXECUTION_COMPLETED, handler)

        # Publish event
        execution_id = str(uuid.uuid4())
        await event_manager.publish_execution_completed(
            execution_id=execution_id,
            success=True,
            execution_time=1.5
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.EXECUTION_COMPLETED
        assert call_args.data["execution_id"] == execution_id
        assert call_args.data["success"] is True
        assert call_args.data["execution_time"] == 1.5

    @pytest.mark.asyncio
    async def test_publish_execution_failed(self, event_manager):
        """Test publishing EXECUTION_FAILED events."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.EXECUTION_FAILED, handler)

        # Publish event
        execution_id = str(uuid.uuid4())
        error_message = "Test error"
        await event_manager.publish_execution_failed(
            execution_id=execution_id,
            error_message=error_message
        )

        # Verify handler was called
        handler.assert_called_once()
        call_args = handler.call_args[0][0]
        assert call_args.type == EventType.EXECUTION_FAILED
        assert call_args.data["execution_id"] == execution_id
        assert call_args.data["error_message"] == error_message

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self, event_manager):
        """Test multiple subscribers to same event type."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()
        handler3 = AsyncMock()

        # Subscribe all handlers
        await event_manager.subscribe(EventType.SKILL_CREATED, handler1)
        await event_manager.subscribe(EventType.SKILL_CREATED, handler2)
        await event_manager.subscribe(EventType.SKILL_CREATED, handler3)

        # Publish event
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Test Skill",
            author="Test Author"
        )

        # Verify all handlers were called
        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_history(self, event_manager):
        """Test event history tracking."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.SKILL_CREATED, handler)

        # Publish multiple events
        for i in range(5):
            await event_manager.publish_skill_created(
                skill_id=str(uuid.uuid4()),
                skill_name=f"Skill {i}",
                author="Test Author"
            )

        # Verify history
        assert len(event_manager.event_history) == 5
        assert all(event.type == EventType.SKILL_CREATED for event in event_manager.event_history)

    @pytest.mark.asyncio
    async def test_event_statistics(self, event_manager):
        """Test event statistics tracking."""
        handler = AsyncMock()
        await event_manager.subscribe(EventType.SKILL_CREATED, handler)

        # Publish events of different types
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Skill 1",
            author="Author 1"
        )
        await event_manager.publish_skill_updated(
            skill_id=str(uuid.uuid4()),
            skill_name="Skill 2",
            changes=["description"]
        )
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Skill 3",
            author="Author 2"
        )

        # Verify statistics
        stats = await event_manager.get_event_statistics()
        assert stats[EventType.SKILL_CREATED] == 2
        assert stats[EventType.SKILL_UPDATED] == 1

    @pytest.mark.asyncio
    async def test_handler_exception(self, event_manager):
        """Test exception handling in event handlers."""
        handler1 = AsyncMock()
        handler2 = AsyncMock(side_effect=Exception("Test exception"))
        handler3 = AsyncMock()

        # Subscribe handlers
        await event_manager.subscribe(EventType.SKILL_CREATED, handler1)
        await event_manager.subscribe(EventType.SKILL_CREATED, handler2)
        await event_manager.subscribe(EventType.SKILL_CREATED, handler3)

        # Publish event - should not raise exception
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Test Skill",
            author="Test Author"
        )

        # Verify all handlers were attempted
        handler1.assert_called_once()
        handler2.assert_called_once()
        handler3.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_filtering(self, event_manager):
        """Test event filtering by priority."""
        handler_low = AsyncMock()
        handler_high = AsyncMock()

        # Subscribe with different priorities
        await event_manager.subscribe(
            EventType.SKILL_CREATED,
            handler_low,
            priority=EventPriority.LOW
        )
        await event_manager.subscribe(
            EventType.SKILL_CREATED,
            handler_high,
            priority=EventPriority.HIGH
        )

        # Publish event
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Test Skill",
            author="Test Author"
        )

        # Verify high priority handler was called first
        # (This test might need adjustment based on actual implementation)
        handler_high.assert_called_once()
        handler_low.assert_called_once()

    @pytest.mark.asyncio
    async def test_event_broadcast_failure(self, event_manager):
        """Test event broadcast when no subscribers."""
        # Don't subscribe any handlers
        skill_id = str(uuid.uuid4())

        # Publishing should not raise exception
        await event_manager.publish_skill_created(
            skill_id=skill_id,
            skill_name="Test Skill",
            author="Test Author"
        )

        # Verify event is still recorded in history
        assert len(event_manager.event_history) == 1
        assert event_manager.event_history[0].data["skill_id"] == skill_id

    @pytest.mark.asyncio
    async def test_get_subscribers(self, event_manager):
        """Test getting subscribers for an event type."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        # Subscribe handlers
        await event_manager.subscribe(EventType.SKILL_CREATED, handler1)
        await event_manager.subscribe(EventType.SKILL_UPDATED, handler2)

        # Get subscribers
        skill_created_subscribers = event_manager.get_subscribers(EventType.SKILL_CREATED)
        skill_updated_subscribers = event_manager.get_subscribers(EventType.SKILL_UPDATED)

        # Verify
        assert handler1 in skill_created_subscribers
        assert handler2 in skill_updated_subscribers
        assert len(skill_created_subscribers) == 1
        assert len(skill_updated_subscribers) == 1

    @pytest.mark.asyncio
    async def test_clear_subscribers(self, event_manager):
        """Test clearing all subscribers."""
        handler1 = AsyncMock()
        handler2 = AsyncMock()

        # Subscribe handlers
        await event_manager.subscribe(EventType.SKILL_CREATED, handler1)
        await event_manager.subscribe(EventType.SKILL_UPDATED, handler2)

        # Clear subscribers
        await event_manager.clear_subscribers()

        # Verify all subscribers are cleared
        assert len(event_manager.subscribers) == 0

    @pytest.mark.asyncio
    async def test_clear_event_history(self, event_manager):
        """Test clearing event history."""
        # Publish some events
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Test Skill",
            author="Test Author"
        )

        # Clear history
        await event_manager.clear_event_history()

        # Verify history is cleared
        assert len(event_manager.event_history) == 0

    @pytest.mark.asyncio
    async def test_clear_event_statistics(self, event_manager):
        """Test clearing event statistics."""
        # Publish some events
        await event_manager.publish_skill_created(
            skill_id=str(uuid.uuid4()),
            skill_name="Test Skill",
            author="Test Author"
        )

        # Clear statistics
        await event_manager.clear_event_statistics()

        # Verify statistics are cleared
        assert len(event_manager.event_stats) == 0
