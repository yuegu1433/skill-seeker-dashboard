"""Tests for notification management system.

This module contains comprehensive tests for NotificationManager and RuleEngine,
including multi-channel notifications, rule matching, frequency control, and smart routing.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock, patch, call
from uuid import uuid4

# Import components to test
from backend.app.progress.models.notification import Notification, NotificationType, NotificationPriority
from backend.app.progress.notification_manager import (
    NotificationManager,
    NotificationChannel,
    NotificationDelivery,
)
from backend.app.progress.rule_engine import (
    RuleEngine,
    NotificationRule,
    RuleCondition,
    RuleType,
    RuleAction,
    RulePriority,
)
from backend.app.progress.schemas.progress_operations import (
    CreateNotificationRequest,
    NotificationQueryParams,
)
from backend.app.progress.schemas.websocket_messages import NotificationMessage, MessageType


class TestNotificationDelivery:
    """Test NotificationDelivery functionality."""

    def test_delivery_initialization(self):
        """Test delivery initialization."""
        delivery = NotificationDelivery(
            channel=NotificationChannel.WEBSOCKET,
            status="pending",
            attempts=0,
            max_attempts=3,
        )

        assert delivery.channel == NotificationChannel.WEBSOCKET
        assert delivery.status == "pending"
        assert delivery.attempts == 0
        assert delivery.max_attempts == 3
        assert delivery.can_retry() is True

    def test_delivery_can_retry(self):
        """Test retry logic."""
        delivery = NotificationDelivery(
            channel=NotificationChannel.EMAIL,
            status="pending",
            attempts=0,
            max_attempts=3,
        )

        # Should be able to retry
        assert delivery.can_retry() is True

        # Mark as failed
        delivery.mark_failed("Network error")
        assert delivery.status == "failed"
        assert delivery.attempts == 1
        assert delivery.can_retry() is True

        # Exhaust retries
        delivery.mark_failed("Network error")
        delivery.mark_failed("Network error")
        assert delivery.attempts == 3
        assert delivery.can_retry() is False

    def test_delivery_status_updates(self):
        """Test delivery status updates."""
        delivery = NotificationDelivery(
            channel=NotificationChannel.WEBSOCKET,
        )

        # Test sent status
        delivery.mark_sent()
        assert delivery.status == "sent"
        assert delivery.attempts == 1
        assert delivery.last_attempt is not None

        # Test delivered status
        delivery.mark_delivered()
        assert delivery.status == "delivered"
        assert delivery.delivered_at is not None

        # Test failed status
        delivery.mark_failed("Error message")
        assert delivery.status == "failed"
        assert delivery.error_message == "Error message"


class TestNotificationManager:
    """Test NotificationManager functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.merge = Mock()
        session.delete = Mock()
        return session

    @pytest.fixture
    def notification_manager(self, mock_db_session):
        """Create NotificationManager instance."""
        return NotificationManager(db_session=mock_db_session)

    @pytest.mark.asyncio
    async def test_create_notification(self, notification_manager, mock_db_session):
        """Test notification creation."""
        request = CreateNotificationRequest(
            user_id="user-123",
            title="Test Notification",
            message="This is a test",
            notification_type=NotificationType.ALERT,
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.WEBSOCKET],
        )

        result = await notification_manager.create_notification(request)

        # Verify notification was created
        assert result.user_id == request.user_id
        assert result.title == request.title
        assert result.message == request.message
        assert result.notification_type == request.notification_type
        assert result.priority == request.priority

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_notification_websocket(self, notification_manager, mock_db_session):
        """Test WebSocket notification sending."""
        # Create notification
        notification = Notification(
            user_id="user-123",
            title="Test",
            message="Test message",
            notification_type=NotificationType.ALERT,
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.WEBSOCKET],
        )

        # Mock websocket_manager
        with patch('backend.app.progress.notification_manager.websocket_manager') as mock_ws:
            mock_ws.broadcast_to_user = AsyncMock(return_value=1)

            result = await notification_manager.send_notification(notification)

            # Verify WebSocket sending
            mock_ws.broadcast_to_user.assert_called_once()
            assert result["successful"] == ["websocket"]
            assert result["failed"] == []

    @pytest.mark.asyncio
    async def test_send_notification_email(self, notification_manager):
        """Test email notification sending."""
        notification = Notification(
            user_id="user-123",
            title="Test",
            message="Test message",
            notification_type=NotificationType.ALERT,
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.EMAIL],
        )

        result = await notification_manager._send_email(notification)

        # Email is currently a placeholder
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_as_read(self, notification_manager, mock_db_session):
        """Test marking notification as read."""
        # Mock database query
        mock_notification = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_notification

        notification_id = str(uuid4())
        result = await notification_manager.mark_as_read(notification_id)

        # Verify update
        assert result is True
        mock_notification.is_read = True
        mock_notification.read_at = datetime.utcnow()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_all_as_read(self, notification_manager, mock_db_session):
        """Test marking all notifications as read."""
        # Mock database update
        mock_db_session.query.return_value.filter.return_value.update.return_value = 5

        user_id = "user-123"
        result = await notification_manager.mark_all_as_read(user_id)

        # Verify all marked as read
        assert result == 5
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_notification(self, notification_manager, mock_db_session):
        """Test notification deletion."""
        # Mock database query
        mock_notification = Mock()
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_notification

        notification_id = str(uuid4())
        result = await notification_manager.delete_notification(notification_id)

        # Verify deletion
        assert result is True
        mock_db_session.delete.assert_called_once_with(mock_notification)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_send_notifications(self, notification_manager):
        """Test bulk notification sending."""
        # Create multiple notifications
        notifications = []
        for i in range(3):
            notification = Notification(
                user_id="user-123",
                title=f"Notification {i}",
                message=f"Message {i}",
                notification_type=NotificationType.ALERT,
                priority=NotificationPriority.NORMAL,
                channels=[NotificationChannel.WEBSOCKET],
            )
            notifications.append(notification)

        # Mock send_notification to avoid actual sending
        with patch.object(notification_manager, 'send_notification') as mock_send:
            mock_send.return_value = {"successful": ["websocket"]}

            result = await notification_manager.bulk_send_notifications(notifications)

            # Verify bulk send
            assert result["successful"] == 3
            assert result["failed"] == 0
            assert result["total"] == 3
            assert len(result["errors"]) == 0
            assert mock_send.call_count == 3

    def test_notification_statistics(self, notification_manager):
        """Test notification statistics."""
        stats = notification_manager.get_stats()

        # Verify statistics structure
        assert "total_created" in stats
        assert "total_sent" in stats
        assert "total_delivered" in stats
        assert "total_failed" in stats
        assert "by_channel" in stats
        assert "by_priority" in stats
        assert "by_type" in stats

    @pytest.mark.asyncio
    async def test_user_channel_preferences(self, notification_manager):
        """Test user channel preference management."""
        user_id = "user-123"

        # Set preferences
        notification_manager.set_user_channel_preference(
            user_id, NotificationChannel.EMAIL, False
        )
        notification_manager.set_user_channel_preference(
            user_id, NotificationChannel.PUSH, True
        )

        # Verify preferences
        assert user_id in notification_manager.user_preferences
        prefs = notification_manager.user_preferences[user_id]
        assert prefs[NotificationChannel.EMAIL] is False
        assert prefs[NotificationChannel.PUSH] is True


class TestRuleCondition:
    """Test RuleCondition functionality."""

    def test_condition_equals(self):
        """Test equals operator."""
        condition = RuleCondition(
            field="level",
            operator="equals",
            value="ERROR",
        )

        context = {"level": "ERROR"}
        assert condition.evaluate(context) is True

        context = {"level": "INFO"}
        assert condition.evaluate(context) is False

    def test_condition_contains(self):
        """Test contains operator."""
        condition = RuleCondition(
            field="message",
            operator="contains",
            value="error",
        )

        context = {"message": "Error occurred"}
        assert condition.evaluate(context) is True

        context = {"message": "Info message"}
        assert condition.evaluate(context) is False

    def test_condition_greater_than(self):
        """Test greater than operator."""
        condition = RuleCondition(
            field="count",
            operator="greater_than",
            value=5,
        )

        context = {"count": 10}
        assert condition.evaluate(context) is True

        context = {"count": 3}
        assert condition.evaluate(context) is False

    def test_condition_in_list(self):
        """Test in operator."""
        condition = RuleCondition(
            field="type",
            operator="in",
            value=["ERROR", "WARNING"],
        )

        context = {"type": "ERROR"}
        assert condition.evaluate(context) is True

        context = {"type": "INFO"}
        assert condition.evaluate(context) is False

    def test_condition_exists(self):
        """Test exists operator."""
        condition = RuleCondition(
            field="error_code",
            operator="exists",
            value=None,
        )

        context = {"error_code": 500}
        assert condition.evaluate(context) is True

        context = {}
        assert condition.evaluate(context) is False

    def test_nested_field_access(self):
        """Test nested field access with dot notation."""
        condition = RuleCondition(
            field="task.status",
            operator="equals",
            value="completed",
        )

        context = {
            "task": {
                "status": "completed",
                "id": "task-123",
            }
        }
        assert condition.evaluate(context) is True

    def test_logical_operators(self):
        """Test AND/OR logical operators."""
        # AND condition
        condition_and = RuleCondition(
            field="level",
            operator="equals",
            value="ERROR",
            logical_operator="AND",
        )

        context = {"level": "ERROR", "count": 5}
        assert condition_and.evaluate(context) is True

        # OR condition
        condition_or = RuleCondition(
            field="level",
            operator="equals",
            value="WARNING",
            logical_operator="OR",
        )

        assert condition_or.evaluate(context) is True


class TestNotificationRule:
    """Test NotificationRule functionality."""

    def test_rule_evaluation(self):
        """Test rule evaluation with multiple conditions."""
        conditions = [
            RuleCondition(
                field="event_type",
                operator="equals",
                value="task_completed",
            ),
            RuleCondition(
                field="status",
                operator="equals",
                value="success",
                logical_operator="AND",
            ),
        ]

        rule = NotificationRule(
            id="rule-1",
            name="Test Rule",
            description="Test rule description",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            enabled=True,
            conditions=conditions,
            actions=[
                {
                    "type": "send",
                    "params": {"priority": "HIGH"},
                },
            ],
        )

        # Matching context
        context = {
            "event_type": "task_completed",
            "status": "success",
        }
        assert rule.evaluate(context) is True

        # Non-matching context
        context = {
            "event_type": "task_started",
            "status": "success",
        }
        assert rule.evaluate(context) is False

    def test_rule_statistics(self):
        """Test rule statistics tracking."""
        rule = NotificationRule(
            id="rule-1",
            name="Test Rule",
            description="Test",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            enabled=True,
            conditions=[],
            actions=[],
        )

        # Evaluate multiple times
        for _ in range(5):
            rule.evaluate({"test": "value"})

        # Evaluate matching once
        rule.evaluate({"test": "match"})

        # Check statistics
        assert rule.evaluation_count == 6
        assert rule.match_count == 1

    def test_rule_disabled(self):
        """Test disabled rule."""
        rule = NotificationRule(
            id="rule-1",
            name="Test Rule",
            description="Test",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            enabled=False,
            conditions=[],
            actions=[],
        )

        context = {"test": "value"}
        assert rule.evaluate(context) is False


class TestRuleEngine:
    """Test RuleEngine functionality."""

    @pytest.fixture
    def rule_engine(self):
        """Create RuleEngine instance."""
        return RuleEngine()

    @pytest.mark.asyncio
    async def test_add_rule(self, rule_engine):
        """Test adding a rule."""
        rule_id = await rule_engine.add_rule(
            name="Test Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[
                RuleCondition(
                    field="level",
                    operator="equals",
                    value="ERROR",
                ),
            ],
            actions=[
                {
                    "type": "send",
                    "params": {"priority": "HIGH"},
                },
            ],
        )

        # Verify rule was added
        assert rule_id in rule_engine.rules
        rule = rule_engine.rules[rule_id]
        assert rule.name == "Test Rule"
        assert rule.rule_type == RuleType.CONDITION
        assert len(rule.conditions) == 1
        assert len(rule.actions) == 1

    @pytest.mark.asyncio
    async def test_remove_rule(self, rule_engine):
        """Test removing a rule."""
        # Add a rule
        rule_id = await rule_engine.add_rule(
            name="Test Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[],
            actions=[],
        )

        # Remove the rule
        result = await rule_engine.remove_rule(rule_id)
        assert result is True
        assert rule_id not in rule_engine.rules

    @pytest.mark.asyncio
    async def test_update_rule(self, rule_engine):
        """Test updating a rule."""
        # Add a rule
        rule_id = await rule_engine.add_rule(
            name="Test Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[],
            actions=[],
        )

        # Update the rule
        result = await rule_engine.update_rule(
            rule_id,
            name="Updated Rule",
            enabled=False,
        )

        assert result is True
        rule = rule_engine.rules[rule_id]
        assert rule.name == "Updated Rule"
        assert rule.enabled is False

    @pytest.mark.asyncio
    async def test_evaluate_rules(self, rule_engine):
        """Test rule evaluation."""
        # Add a rule
        await rule_engine.add_rule(
            name="Error Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="level",
                    operator="equals",
                    value="ERROR",
                ),
            ],
            actions=[
                {
                    "type": "send",
                    "params": {"priority": "HIGH"},
                },
            ],
        )

        # Test matching context
        context = {"level": "ERROR"}
        matching_rules = await rule_engine.evaluate_rules(context)
        assert len(matching_rules) == 1
        assert matching_rules[0].name == "Error Rule"

        # Test non-matching context
        context = {"level": "INFO"}
        matching_rules = await rule_engine.evaluate_rules(context)
        assert len(matching_rules) == 0

    @pytest.mark.asyncio
    async def test_rule_priority(self, rule_engine):
        """Test rule priority sorting."""
        # Add multiple rules with different priorities
        await rule_engine.add_rule(
            name="Low Priority Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.LOW,
            conditions=[],
            actions=[],
        )

        await rule_engine.add_rule(
            name="High Priority Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.HIGH,
            conditions=[],
            actions=[],
        )

        await rule_engine.add_rule(
            name="Normal Priority Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[],
            actions=[],
        )

        # Evaluate rules
        context = {"test": "value"}
        matching_rules = await rule_engine.evaluate_rules(context)

        # Should be sorted by priority (highest first)
        assert len(matching_rules) == 3
        assert matching_rules[0].priority == RulePriority.HIGH
        assert matching_rules[1].priority == RulePriority.NORMAL
        assert matching_rules[2].priority == RulePriority.LOW

    @pytest.mark.asyncio
    async def test_execute_actions(self, rule_engine):
        """Test action execution."""
        # Add a rule
        await rule_engine.add_rule(
            name="Test Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[],
            actions=[
                {
                    "type": "send",
                    "params": {"priority": "HIGH"},
                },
                {
                    "type": "route",
                    "params": {"channels": ["websocket"]},
                },
            ],
        )

        # Evaluate and execute
        context = {"test": "value"}
        matching_rules = await rule_engine.evaluate_rules(context)
        results = await rule_engine.execute_actions(matching_rules, context)

        # Verify execution
        assert len(results["executed"]) == 1
        assert len(results["skipped"]) == 0
        assert len(results["errors"]) == 0

    @pytest.mark.asyncio
    async def test_conflict_resolution(self, rule_engine):
        """Test conflict resolution between rules."""
        # Add rules with overlapping conditions
        await rule_engine.add_rule(
            name="Rule 1",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="level",
                    operator="equals",
                    value="ERROR",
                ),
            ],
            actions=[],
        )

        await rule_engine.add_rule(
            name="Rule 2",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[
                RuleCondition(
                    field="level",
                    operator="equals",
                    value="ERROR",
                ),
            ],
            actions=[],
        )

        # Both rules match
        context = {"level": "ERROR"}
        matching_rules = await rule_engine.evaluate_rules(context)

        # Resolve conflicts
        resolved_rules = await rule_engine.resolve_conflicts(matching_rules)

        # Should only have one rule (highest priority)
        assert len(resolved_rules) == 1
        assert resolved_rules[0].name == "Rule 1"

    def test_rule_engine_statistics(self, rule_engine):
        """Test rule engine statistics."""
        stats = rule_engine.get_rule_statistics()

        # Verify statistics structure
        assert "total_rules" in stats
        assert "active_rules" in stats
        assert "total_evaluations" in stats
        assert "total_matches" in stats
        assert "by_type" in stats
        assert "by_priority" in stats
        assert "groups" in stats

    @pytest.mark.asyncio
    async def test_rule_export_import(self, rule_engine):
        """Test rule export and import."""
        # Add a rule
        await rule_engine.add_rule(
            name="Test Rule",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            conditions=[
                RuleCondition(
                    field="level",
                    operator="equals",
                    value="ERROR",
                ),
            ],
            actions=[
                {
                    "type": "send",
                    "params": {"priority": "HIGH"},
                },
            ],
        )

        # Export rules
        exported = await rule_engine.export_rules()
        assert len(exported) == 1
        assert exported[0]["name"] == "Test Rule"

        # Clear rules
        rule_engine.rules.clear()

        # Import rules
        imported_count = await rule_engine.import_rules(exported)
        assert imported_count == 1
        assert len(rule_engine.rules) == 1

    @pytest.mark.asyncio
    async def test_load_default_rules(self, rule_engine):
        """Test loading default rules."""
        await rule_engine.load_default_rules()

        # Verify default rules were loaded
        stats = rule_engine.get_rule_statistics()
        assert stats["total_rules"] >= 3  # At least the default rules


class TestSmartRouting:
    """Test smart routing functionality."""

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from backend.app.progress.notification_manager import NotificationManager

        manager = NotificationManager()
        notification = Notification(
            user_id="user-123",
            title="Test",
            message="Test",
            notification_type=NotificationType.ALERT,
            priority=NotificationPriority.NORMAL,
            channels=[NotificationChannel.WEBSOCKET],
        )

        # Test rate limit for NORMAL priority (60 per minute)
        for i in range(60):
            result = await manager._check_rate_limit(notification)
            if i < 60:
                assert result is True

        # 61st should fail
        result = await manager._check_rate_limit(notification)
        assert result is False

    @pytest.mark.asyncio
    async def test_smart_routing_rules(self):
        """Test smart routing rule application."""
        from backend.app.progress.notification_manager import NotificationManager

        manager = NotificationManager()

        # Create critical priority notification
        notification = Notification(
            user_id="user-123",
            title="Critical Error",
            message="System error",
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.CRITICAL,
            channels=[NotificationChannel.EMAIL],  # Will be overridden
        )

        # Apply smart routing
        channels = await manager._apply_smart_routing(notification)

        # Should use preferred channels for critical priority
        assert NotificationChannel.WEBSOCKET in channels
        assert NotificationChannel.PUSH in channels


class TestNotificationIntegration:
    """Integration tests for notification system."""

    @pytest.mark.asyncio
    async def test_end_to_end_notification_flow(self):
        """Test complete notification flow."""
        # Create components
        from backend.app.progress.notification_manager import NotificationManager
        from backend.app.progress.rule_engine import RuleEngine

        manager = NotificationManager()
        engine = RuleEngine()

        # Load default rules
        await engine.load_default_rules()

        # Create notification via manager
        request = CreateNotificationRequest(
            user_id="user-123",
            title="Task Completed",
            message="Your task has completed successfully",
            notification_type=NotificationType.TASK_COMPLETE,
            priority=NotificationPriority.NORMAL,
        )

        notification = await manager.create_notification(request)

        # Verify notification was created
        assert notification.title == "Task Completed"
        assert notification.notification_type == NotificationType.TASK_COMPLETE

    @pytest.mark.asyncio
    async def test_rule_triggered_notification(self):
        """Test notification triggered by rule."""
        from backend.app.progress.notification_manager import NotificationManager
        from backend.app.progress.rule_engine import RuleEngine

        manager = NotificationManager()
        engine = RuleEngine()

        # Add a custom rule
        await engine.add_rule(
            name="High Error Count",
            rule_type=RuleType.THRESHOLD,
            priority=RulePriority.HIGH,
            conditions=[
                RuleCondition(
                    field="error_count",
                    operator="greater_than",
                    value=5,
                ),
            ],
            actions=[
                {
                    "type": "send",
                    "params": {
                        "notification_type": NotificationType.ERROR,
                        "priority": NotificationPriority.HIGH,
                    },
                },
            ],
        )

        # Evaluate rule with matching context
        context = {"error_count": 10}
        matching_rules = await engine.evaluate_rules(context)

        assert len(matching_rules) == 1
        assert matching_rules[0].name == "High Error Count"


# Test data fixtures
@pytest.fixture
def sample_notification():
    """Create sample notification for testing."""
    return Notification(
        user_id="user-123",
        title="Test Notification",
        message="This is a test notification",
        notification_type=NotificationType.ALERT,
        priority=NotificationPriority.NORMAL,
        channels=[NotificationChannel.WEBSOCKET],
        is_read=False,
    )


@pytest.fixture
def sample_rule_conditions():
    """Create sample rule conditions for testing."""
    return [
        RuleCondition(
            field="event_type",
            operator="equals",
            value="task_completed",
        ),
        RuleCondition(
            field="status",
            operator="equals",
            value="success",
            logical_operator="AND",
        ),
    ]


@pytest.fixture
def notification_query_params():
    """Create sample notification query parameters."""
    return NotificationQueryParams(
        user_id="user-123",
        notification_type=NotificationType.ALERT,
        priority=NotificationPriority.NORMAL,
        is_read=False,
        date_from=datetime.utcnow() - timedelta(hours=1),
        date_to=datetime.utcnow(),
        limit=50,
        sort_order="desc",
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
