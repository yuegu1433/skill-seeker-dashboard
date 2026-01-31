"""Notification rule engine for intelligent notification management.

This module provides RuleEngine for managing notification rules, conditions,
and conflict resolution with priority-based evaluation.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from collections import defaultdict

from sqlalchemy.orm import Session

from .models.notification import Notification, NotificationType, NotificationPriority
from .schemas.progress_operations import CreateNotificationRequest

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of notification rules."""
    CONDITION = "condition"
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    TIME_BASED = "time_based"
    USER_BEHAVIOR = "user_behavior"


class RuleAction(Enum):
    """Actions that rules can perform."""
    SEND = "send"
    SUPPRESS = "suppress"
    DEFER = "defer"
    ROUTE = "route"
    ESCALATE = "escalate"


class RulePriority(Enum):
    """Rule evaluation priority."""
    LOWEST = 0
    LOW = 10
    NORMAL = 20
    HIGH = 30
    CRITICAL = 40


@dataclass
class RuleCondition:
    """A single condition within a rule."""
    field: str
    operator: str
    value: Any
    logical_operator: Optional[str] = "AND"  # AND, OR

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate condition against context.

        Args:
            context: Evaluation context

        Returns:
            True if condition is met
        """
        field_value = self._get_field_value(context)

        if self.operator == "equals":
            return field_value == self.value
        elif self.operator == "not_equals":
            return field_value != self.value
        elif self.operator == "contains":
            return str(self.value).lower() in str(field_value).lower()
        elif self.operator == "not_contains":
            return str(self.value).lower() not in str(field_value).lower()
        elif self.operator == "greater_than":
            return field_value > self.value
        elif self.operator == "less_than":
            return field_value < self.value
        elif self.operator == "greater_equal":
            return field_value >= self.value
        elif self.operator == "less_equal":
            return field_value <= self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        elif self.operator == "regex":
            import re
            return bool(re.search(str(self.value), str(field_value)))
        elif self.operator == "exists":
            return field_value is not None
        elif self.operator == "not_exists":
            return field_value is None
        else:
            logger.warning(f"Unknown operator: {self.operator}")
            return False

    def _get_field_value(self, context: Dict[str, Any]) -> Any:
        """Get field value from context using dot notation.

        Args:
            context: Context dictionary

        Returns:
            Field value
        """
        keys = self.field.split('.')
        value = context

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value


@dataclass
class NotificationRule:
    """A notification rule with conditions and actions."""
    id: str
    name: str
    description: str
    rule_type: RuleType
    priority: RulePriority
    enabled: bool = True
    conditions: List[RuleCondition] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_evaluated: Optional[datetime] = None
    evaluation_count: int = 0
    match_count: int = 0

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evaluate rule against context.

        Args:
            context: Evaluation context

        Returns:
            True if rule matches
        """
        if not self.enabled:
            return False

        # Update statistics
        self.evaluation_count += 1
        self.last_evaluated = datetime.utcnow()

        # Evaluate conditions
        if not self.conditions:
            return True

        # Group conditions by logical operator
        and_groups = []
        current_or_group = []

        for condition in self.conditions:
            condition_result = condition.evaluate(context)

            if condition.logical_operator == "OR":
                # Add previous OR group to AND groups
                if current_or_group:
                    and_groups.append(current_or_group)
                    current_or_group = []
                current_or_group.append(condition_result)
            else:  # AND
                # Add previous OR group to AND groups
                if current_or_group:
                    and_groups.append(current_or_group)
                    current_or_group = []
                # Add condition to current OR group
                current_or_group.append(condition_result)

        # Add final OR group
        if current_or_group:
            and_groups.append(current_or_group)

        # Evaluate: all AND groups must have at least one True OR condition
        for or_group in and_groups:
            if not any(or_group):
                return False

        # All conditions met
        self.match_count += 1
        return True


class RuleEngine:
    """Engine for evaluating and executing notification rules."""

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize rule engine.

        Args:
            db_session: SQLAlchemy database session (optional)
        """
        self.db_session = db_session
        self.rules: Dict[str, NotificationRule] = {}
        self.rule_groups: Dict[str, List[str]] = defaultdict(list)  # Group name -> rule IDs
        self._lock = asyncio.Lock()
        self._stats = {
            "total_rules": 0,
            "active_rules": 0,
            "total_evaluations": 0,
            "total_matches": 0,
            "by_type": defaultdict(int),
            "by_priority": defaultdict(int),
        }

    async def add_rule(
        self,
        name: str,
        rule_type: RuleType,
        priority: RulePriority,
        conditions: List[RuleCondition],
        actions: List[Dict[str, Any]],
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        group: Optional[str] = None,
    ) -> str:
        """Add a new notification rule.

        Args:
            name: Rule name
            rule_type: Type of rule
            priority: Rule priority
            conditions: List of conditions
            actions: List of actions to execute
            description: Rule description
            metadata: Additional metadata
            enabled: Whether rule is enabled
            group: Rule group (optional)

        Returns:
            Rule ID
        """
        rule_id = str(uuid4())

        rule = NotificationRule(
            id=rule_id,
            name=name,
            description=description,
            rule_type=rule_type,
            priority=priority,
            enabled=enabled,
            conditions=conditions,
            actions=actions,
            metadata=metadata or {},
        )

        async with self._lock:
            self.rules[rule_id] = rule
            self._stats["total_rules"] += 1
            self._stats["active_rules"] += 1
            self._stats["by_type"][rule_type.value] += 1
            self._stats["by_priority"][priority.value] += 1

            if group:
                self.rule_groups[group].append(rule_id)

        logger.info(f"Added notification rule: {name} ({rule_id})")
        return rule_id

    async def remove_rule(self, rule_id: str) -> bool:
        """Remove a notification rule.

        Args:
            rule_id: Rule ID

        Returns:
            True if removed successfully
        """
        async with self._lock:
            if rule_id not in self.rules:
                return False

            rule = self.rules[rule_id]
            del self.rules[rule_id]
            self._stats["total_rules"] -= 1
            if rule.enabled:
                self._stats["active_rules"] -= 1

            # Remove from groups
            for group_name, rule_ids in self.rule_groups.items():
                if rule_id in rule_ids:
                    rule_ids.remove(rule_id)

        logger.info(f"Removed notification rule: {rule.name} ({rule_id})")
        return True

    async def update_rule(
        self,
        rule_id: str,
        **kwargs,
    ) -> bool:
        """Update an existing rule.

        Args:
            rule_id: Rule ID
            **kwargs: Fields to update

        Returns:
            True if updated successfully
        """
        async with self._lock:
            if rule_id not in self.rules:
                return False

            rule = self.rules[rule_id]

            # Update fields
            for field, value in kwargs.items():
                if hasattr(rule, field):
                    setattr(rule, field, value)

            rule.updated_at = datetime.utcnow()

        logger.info(f"Updated notification rule: {rule.name} ({rule_id})")
        return True

    async def evaluate_rules(
        self,
        context: Dict[str, Any],
        rule_type: Optional[RuleType] = None,
        group: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[NotificationRule]:
        """Evaluate rules against context.

        Args:
            context: Evaluation context
            rule_type: Filter by rule type (optional)
            group: Filter by rule group (optional)
            limit: Maximum number of rules to evaluate (optional)

        Returns:
            List of matching rules
        """
        matching_rules = []

        # Get rules to evaluate
        rule_ids = self.rules.keys()
        if group:
            rule_ids = self.rule_groups.get(group, [])

        # Get enabled rules
        enabled_rules = [
            self.rules[rule_id]
            for rule_id in rule_ids
            if self.rules[rule_id].enabled
        ]

        # Filter by type
        if rule_type:
            enabled_rules = [
                rule for rule in enabled_rules
                if rule.rule_type == rule_type
            ]

        # Sort by priority (highest first)
        enabled_rules.sort(key=lambda r: r.priority.value, reverse=True)

        # Limit results
        if limit:
            enabled_rules = enabled_rules[:limit]

        # Evaluate rules
        for rule in enabled_rules:
            try:
                if rule.evaluate(context):
                    matching_rules.append(rule)
                    self._stats["total_matches"] += 1
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name} ({rule.id}): {e}")

            self._stats["total_evaluations"] += 1

        return matching_rules

    async def execute_actions(
        self,
        rules: List[NotificationRule],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute actions for matching rules.

        Args:
            rules: List of matching rules
            context: Execution context

        Returns:
            Dictionary with execution results
        """
        results = {
            "executed": [],
            "skipped": [],
            "errors": [],
        }

        for rule in rules:
            try:
                rule_result = await self._execute_rule_actions(rule, context)
                if rule_result["success"]:
                    results["executed"].append({
                        "rule_id": rule.id,
                        "rule_name": rule.name,
                        "actions_executed": rule_result["actions"],
                    })
                else:
                    results["skipped"].append({
                        "rule_id": rule.id,
                        "reason": rule_result["reason"],
                    })
            except Exception as e:
                results["errors"].append({
                    "rule_id": rule.id,
                    "error": str(e),
                })
                logger.error(f"Error executing rule {rule.name} ({rule.id}): {e}")

        return results

    async def _execute_rule_actions(
        self,
        rule: NotificationRule,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute actions for a single rule.

        Args:
            rule: Notification rule
            context: Execution context

        Returns:
            Execution result
        """
        executed_actions = []
        skip_reason = None

        for action in rule.actions:
            action_type = action.get("type")
            action_params = action.get("params", {})

            if action_type == RuleAction.SEND.value:
                # Send notification
                notification_request = await self._create_notification_from_action(
                    action_params, context
                )
                executed_actions.append({
                    "type": "send_notification",
                    "notification_id": str(notification_request.get("id")),
                })

            elif action_type == RuleAction.SUPPRESS.value:
                # Suppress notification
                skip_reason = action_params.get("reason", "Rule suppressed")
                break

            elif action_type == RuleAction.DEFER.value:
                # Defer notification
                delay_minutes = action_params.get("delay_minutes", 5)
                executed_actions.append({
                    "type": "defer",
                    "delay_minutes": delay_minutes,
                })

            elif action_type == RuleAction.ROUTE.value:
                # Route to specific channels
                channels = action_params.get("channels", [])
                executed_actions.append({
                    "type": "route",
                    "channels": channels,
                })

            elif action_type == RuleAction.ESCALATE.value:
                # Escalate priority
                new_priority = action_params.get("priority")
                executed_actions.append({
                    "type": "escalate",
                    "new_priority": new_priority,
                })

        return {
            "success": True,
            "actions": executed_actions,
            "skip_reason": skip_reason,
        }

    async def _create_notification_from_action(
        self,
        action_params: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create notification from action parameters.

        Args:
            action_params: Action parameters
            context: Execution context

        Returns:
            Created notification request
        """
        # Extract notification data from context
        user_id = action_params.get("user_id") or context.get("user_id")
        title = action_params.get("title") or f"Rule Triggered: {context.get('rule_name', 'Unknown')}"
        message = action_params.get("message") or context.get("message", "Notification rule triggered")
        notification_type = action_params.get("notification_type") or NotificationType.ALERT
        priority = action_params.get("priority") or NotificationPriority.NORMAL

        # Create notification request
        notification_request = CreateNotificationRequest(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            metadata={
                "triggered_by_rule": True,
                "rule_id": context.get("rule_id"),
                "context": context,
            },
        )

        return notification_request.dict()

    async def get_rule_statistics(self) -> Dict[str, Any]:
        """Get rule engine statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **dict(self._stats),
            "rules_by_type": {
                rule_type.value: len([
                    r for r in self.rules.values()
                    if r.rule_type == rule_type
                ])
                for rule_type in RuleType
            },
            "rules_by_priority": {
                priority.name: len([
                    r for r in self.rules.values()
                    if r.priority == priority
                ])
                for priority in RulePriority
            },
            "groups": {
                group_name: len(rule_ids)
                for group_name, rule_ids in self.rule_groups.items()
            },
        }

    async def resolve_conflicts(
        self,
        rules: List[NotificationRule],
    ) -> List[NotificationRule]:
        """Resolve conflicts between overlapping rules.

        Args:
            rules: List of rules to resolve conflicts for

        Returns:
            List of resolved rules
        """
        # Sort by priority (highest first) and creation time
        rules.sort(key=lambda r: (r.priority.value, r.created_at), reverse=True)

        resolved_rules = []
        used_fields = set()

        for rule in rules:
            # Check if rule conflicts with already selected rules
            rule_fields = {cond.field for cond in rule.conditions}

            if not used_fields.intersection(rule_fields):
                # No conflict, add rule
                resolved_rules.append(rule)
                used_fields.update(rule_fields)
            else:
                # Conflict detected, skip lower priority rule
                logger.info(f"Skipped conflicting rule: {rule.name} ({rule.id})")

        return resolved_rules

    async def load_default_rules(self):
        """Load default notification rules."""
        # Task completion rule
        await self.add_rule(
            name="Task Completion Alert",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.NORMAL,
            description="Send notification when task completes",
            conditions=[
                RuleCondition(
                    field="event_type",
                    operator="equals",
                    value="task_completed",
                ),
                RuleCondition(
                    field="status",
                    operator="equals",
                    value="success",
                ),
            ],
            actions=[
                {
                    "type": "send",
                    "params": {
                        "notification_type": NotificationType.TASK_COMPLETE,
                        "priority": NotificationPriority.NORMAL,
                    },
                },
            ],
            group="task_notifications",
        )

        # Error threshold rule
        await self.add_rule(
            name="Error Threshold Alert",
            rule_type=RuleType.THRESHOLD,
            priority=RulePriority.HIGH,
            description="Alert when error count exceeds threshold",
            conditions=[
                RuleCondition(
                    field="error_count",
                    operator="greater_than",
                    value=5,
                ),
                RuleCondition(
                    field="time_window_minutes",
                    operator="less_equal",
                    value=60,
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
                {
                    "type": "escalate",
                    "params": {
                        "priority": NotificationPriority.CRITICAL,
                    },
                },
            ],
            group="error_handling",
        )

        # Low priority for background tasks
        await self.add_rule(
            name="Background Task Notification",
            rule_type=RuleType.CONDITION,
            priority=RulePriority.LOW,
            description="Low priority for background tasks",
            conditions=[
                RuleCondition(
                    field="task_type",
                    operator="equals",
                    value="background",
                ),
            ],
            actions=[
                {
                    "type": "route",
                    "params": {
                        "channels": ["websocket"],
                    },
                },
            ],
            group="task_notifications",
        )

        logger.info("Loaded default notification rules")

    async def export_rules(self) -> List[Dict[str, Any]]:
        """Export all rules to dictionary format.

        Returns:
            List of rule dictionaries
        """
        exported_rules = []

        for rule in self.rules.values():
            rule_dict = {
                "id": rule.id,
                "name": rule.name,
                "description": rule.description,
                "rule_type": rule.rule_type.value,
                "priority": rule.priority.name,
                "enabled": rule.enabled,
                "conditions": [
                    {
                        "field": cond.field,
                        "operator": cond.operator,
                        "value": cond.value,
                        "logical_operator": cond.logical_operator,
                    }
                    for cond in rule.conditions
                ],
                "actions": rule.actions,
                "metadata": rule.metadata,
                "created_at": rule.created_at.isoformat(),
                "updated_at": rule.updated_at.isoformat(),
                "statistics": {
                    "evaluation_count": rule.evaluation_count,
                    "match_count": rule.match_count,
                    "match_rate": rule.match_count / max(rule.evaluation_count, 1),
                },
            }
            exported_rules.append(rule_dict)

        return exported_rules

    async def import_rules(self, rules_data: List[Dict[str, Any]]) -> int:
        """Import rules from dictionary format.

        Args:
            rules_data: List of rule dictionaries

        Returns:
            Number of rules imported
        """
        imported_count = 0

        for rule_data in rules_data:
            try:
                # Convert conditions
                conditions = [
                    RuleCondition(
                        field=cond_data["field"],
                        operator=cond_data["operator"],
                        value=cond_data["value"],
                        logical_operator=cond_data.get("logical_operator", "AND"),
                    )
                    for cond_data in rule_data.get("conditions", [])
                ]

                # Add rule
                await self.add_rule(
                    name=rule_data["name"],
                    rule_type=RuleType(rule_data["rule_type"]),
                    priority=RulePriority[rule_data["priority"]],
                    description=rule_data.get("description", ""),
                    conditions=conditions,
                    actions=rule_data.get("actions", []),
                    metadata=rule_data.get("metadata", {}),
                    enabled=rule_data.get("enabled", True),
                )
                imported_count += 1

            except Exception as e:
                logger.error(f"Failed to import rule {rule_data.get('name')}: {e}")

        logger.info(f"Imported {imported_count} notification rules")
        return imported_count


# Global rule engine instance
rule_engine = RuleEngine()
