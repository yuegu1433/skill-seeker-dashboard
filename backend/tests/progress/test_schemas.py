"""Test cases for progress tracking Pydantic schemas.

This module contains comprehensive unit tests for all progress tracking
schemas including progress operations, WebSocket messages, and notification configs.
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID, uuid4

from backend.app.progress.schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
    TaskProgressResponse,
    TaskStatus,
    CreateLogRequest,
    TaskLogResponse,
    CreateNotificationRequest,
    NotificationResponse,
    CreateMetricRequest,
    ProgressMetricResponse,
    TaskListResponse,
    TaskHistoryResponse,
    BulkProgressUpdateRequest,
    BulkProgressUpdateResponse
)
from backend.app.progress.schemas.websocket_messages import (
    WebSocketMessage,
    ProgressUpdateMessage,
    LogMessage,
    NotificationMessage,
    ConnectionMessage,
    HeartbeatMessage,
    SubscribeMessage,
    UnsubscribeMessage,
    BroadcastMessage,
    ErrorMessage,
    AckMessage
)
from backend.app.progress.schemas.notification_config import (
    NotificationChannel,
    NotificationTemplate,
    NotificationRule,
    UserNotificationSettings,
    NotificationStats,
    BulkNotificationRequest
)


class TestProgressOperationsSchemas:
    """Test cases for progress operation schemas."""

    def test_create_task_request_valid(self):
        """Test CreateTaskRequest with valid data."""
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Create New Skill",
            description="Create a new skill for the platform",
            estimated_duration=300,
            total_steps=5,
            metadata={"priority": "high", "department": "engineering"},
            tags=["test", "automation"]
        )

        assert request.task_id == "task-001"
        assert request.user_id == "user-001"
        assert request.task_type == "skill_creation"
        assert request.task_name == "Create New Skill"
        assert request.description == "Create a new skill for the platform"
        assert request.estimated_duration == 300
        assert request.total_steps == 5
        assert request.metadata["priority"] == "high"
        assert "test" in request.tags

    def test_create_task_request_minimal(self):
        """Test CreateTaskRequest with minimal required fields."""
        request = CreateTaskRequest(
            task_id="task-002",
            user_id="user-002",
            task_type="file_processing",
            task_name="Process File"
        )

        assert request.task_id == "task-002"
        assert request.user_id == "user-002"
        assert request.task_type == "file_processing"
        assert request.task_name == "Process File"
        assert request.description is None
        assert request.estimated_duration is None
        assert request.total_steps is None
        assert request.metadata == {}
        assert request.tags == []

    def test_create_task_request_validation_errors(self):
        """Test CreateTaskRequest validation errors."""
        # Test empty task_id
        with pytest.raises(Exception):  # ValidationError from Pydantic
            CreateTaskRequest(
                task_id="",  # Empty string should fail
                user_id="user-001",
                task_type="skill_creation",
                task_name="Test Task"
            )

        # Test task_id too long
        with pytest.raises(Exception):
            CreateTaskRequest(
                task_id="x" * 101,  # Too long
                user_id="user-001",
                task_type="skill_creation",
                task_name="Test Task"
            )

        # Test invalid estimated_duration
        with pytest.raises(Exception):
            CreateTaskRequest(
                task_id="task-003",
                user_id="user-003",
                task_type="skill_creation",
                task_name="Test Task",
                estimated_duration=0  # Must be >= 1
            )

        # Test invalid total_steps
        with pytest.raises(Exception):
            CreateTaskRequest(
                task_id="task-004",
                user_id="user-004",
                task_type="skill_creation",
                task_name="Test Task",
                total_steps=0  # Must be >= 1
            )

    def test_update_progress_request_valid(self):
        """Test UpdateProgressRequest with valid data."""
        request = UpdateProgressRequest(
            task_id="task-001",
            progress=50.0,
            status="running",
            current_step="processing",
            message="Processing data...",
            metadata={"current_operation": "validation"},
            force_update=False
        )

        assert request.task_id == "task-001"
        assert request.progress == 50.0
        assert request.status == "running"
        assert request.current_step == "processing"
        assert request.message == "Processing data..."
        assert request.metadata["current_operation"] == "validation"
        assert request.force_update is False

    def test_update_progress_request_minimal(self):
        """Test UpdateProgressRequest with minimal fields."""
        request = UpdateProgressRequest(
            task_id="task-002",
            progress=25.0
        )

        assert request.task_id == "task-002"
        assert request.progress == 25.0
        assert request.status is None
        assert request.current_step is None
        assert request.message is None
        assert request.metadata == {}
        assert request.force_update is False

    def test_update_progress_request_validation_errors(self):
        """Test UpdateProgressRequest validation errors."""
        # Test progress < 0
        with pytest.raises(Exception):
            UpdateProgressRequest(
                task_id="task-001",
                progress=-1.0
            )

        # Test progress > 100
        with pytest.raises(Exception):
            UpdateProgressRequest(
                task_id="task-001",
                progress=101.0
            )

        # Test empty task_id
        with pytest.raises(Exception):
            UpdateProgressRequest(
                task_id="",
                progress=50.0
            )

    def test_task_progress_response_valid(self):
        """Test TaskProgressResponse with valid data."""
        response = TaskProgressResponse(
            id=str(uuid4()),
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Create Skill",
            description="Create a new skill",
            progress=75.0,
            status="running",
            current_step="validation",
            total_steps=4,
            estimated_duration=300,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            result={"output": "success"},
            error_message=None,
            task_metadata={"priority": "high"},
            tags=["test"]
        )

        assert response.task_id == "task-001"
        assert response.user_id == "user-001"
        assert response.progress == 75.0
        assert response.status == "running"
        assert response.current_step == "validation"
        assert response.total_steps == 4

    def test_task_progress_response_computed_fields(self):
        """Test TaskProgressResponse computed fields."""
        response = TaskProgressResponse(
            id=str(uuid4()),
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Create Skill",
            progress=50.0,
            status="running",
            current_step="step_2",
            total_steps=4,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Test completion percentage calculation
        assert response.completion_percentage == 50.0

        # Test duration calculation
        duration = response.duration_seconds
        assert duration is not None
        assert duration >= 0

    def test_bulk_progress_update_request_valid(self):
        """Test BulkProgressUpdateRequest with valid data."""
        updates = [
            {
                "task_id": "task-001",
                "progress": 50.0,
                "status": "running"
            },
            {
                "task_id": "task-002",
                "progress": 75.0,
                "status": "running",
                "message": "Processing..."
            }
        ]

        request = BulkProgressUpdateRequest(
            updates=updates,
            force_update=False
        )

        assert len(request.updates) == 2
        assert request.updates[0]["task_id"] == "task-001"
        assert request.updates[1]["task_id"] == "task-002"
        assert request.force_update is False


class TestWebSocketMessageSchemas:
    """Test cases for WebSocket message schemas."""

    def test_websocket_message_base(self):
        """Test WebSocketMessage base model."""
        message = WebSocketMessage(
            message_type="progress_update",
            message_id="msg-001",
            source="task_executor",
            target="client-001",
            correlation_id="corr-001",
            session_id="session-001",
            user_id="user-001",
            priority="high",
            retry_count=1,
            metadata={"channel": "websocket"}
        )

        assert message.message_type == "progress_update"
        assert message.message_id == "msg-001"
        assert message.source == "task_executor"
        assert message.target == "client-001"
        assert message.correlation_id == "corr-001"
        assert message.session_id == "session-001"
        assert message.user_id == "user-001"
        assert message.priority == "high"
        assert message.retry_count == 1
        assert message.metadata["channel"] == "websocket"

    def test_websocket_message_default_values(self):
        """Test WebSocketMessage default values."""
        message = WebSocketMessage(
            message_type="heartbeat"
        )

        assert message.message_type == "heartbeat"
        assert message.message_id is None
        assert isinstance(message.timestamp, datetime)
        assert message.source is None
        assert message.target is None
        assert message.correlation_id is None
        assert message.session_id is None
        assert message.user_id is None
        assert message.priority == "normal"
        assert message.retry_count == 0
        assert message.metadata == {}

    def test_progress_update_message_valid(self):
        """Test ProgressUpdateMessage with valid data."""
        message = ProgressUpdateMessage(
            message_type="progress_update",
            task_id="task-001",
            user_id="user-001",
            progress=50.0,
            status="running",
            current_step="processing",
            total_steps=4,
            message="Processing data...",
            estimated_remaining=150,
            speed=2.5,
            result={"processed": 500, "total": 1000},
            error=None
        )

        assert message.task_id == "task-001"
        assert message.user_id == "user-001"
        assert message.progress == 50.0
        assert message.status == "running"
        assert message.current_step == "processing"
        assert message.total_steps == 4
        assert message.message == "Processing data..."
        assert message.estimated_remaining == 150
        assert message.speed == 2.5
        assert message.result["processed"] == 500
        assert message.error is None

    def test_log_message_valid(self):
        """Test LogMessage with valid data."""
        message = LogMessage(
            message_type="log_entry",
            task_id="task-001",
            user_id="user-001",
            level="INFO",
            message="Task execution started",
            source="task_executor",
            timestamp=datetime.now(timezone.utc),
            context={"operation": "start"},
            stack_trace=None
        )

        assert message.task_id == "task-001"
        assert message.user_id == "user-001"
        assert message.level == "INFO"
        assert message.message == "Task execution started"
        assert message.source == "task_executor"
        assert message.context["operation"] == "start"
        assert message.stack_trace is None

    def test_notification_message_valid(self):
        """Test NotificationMessage with valid data."""
        message = NotificationMessage(
            message_type="notification",
            user_id="user-001",
            notification_id=str(uuid4()),
            title="Task Completed",
            message="Your task has been completed successfully",
            notification_type="success",
            priority="normal",
            channels=["websocket", "email"],
            action_url="/tasks/task-001",
            metadata={"task_id": "task-001"}
        )

        assert message.user_id == "user-001"
        assert message.title == "Task Completed"
        assert message.message == "Your task has been completed successfully"
        assert message.notification_type == "success"
        assert message.priority == "normal"
        assert "websocket" in message.channels
        assert "email" in message.channels
        assert message.action_url == "/tasks/task-001"
        assert message.metadata["task_id"] == "task-001"

    def test_connection_message_valid(self):
        """Test ConnectionMessage with valid data."""
        message = ConnectionMessage(
            message_type="connection",
            action="connect",
            client_id="client-001",
            user_id="user-001",
            session_id="session-001",
            capabilities=["progress_tracking", "log_streaming"],
            metadata={"client_version": "1.0.0"}
        )

        assert message.action == "connect"
        assert message.client_id == "client-001"
        assert message.user_id == "user-001"
        assert message.session_id == "session-001"
        assert "progress_tracking" in message.capabilities
        assert "log_streaming" in message.capabilities

    def test_heartbeat_message_valid(self):
        """Test HeartbeatMessage with valid data."""
        message = HeartbeatMessage(
            message_type="heartbeat",
            client_id="client-001",
            server_time=datetime.now(timezone.utc),
            latency_ms=50,
            status="healthy",
            load_average=0.75
        )

        assert message.client_id == "client-001"
        assert isinstance(message.server_time, datetime)
        assert message.latency_ms == 50
        assert message.status == "healthy"
        assert message.load_average == 0.75

    def test_subscribe_message_valid(self):
        """Test SubscribeMessage with valid data."""
        message = SubscribeMessage(
            message_type="subscribe",
            subscription_type="task_progress",
            filters={
                "user_id": "user-001",
                "task_types": ["skill_creation", "skill_deployment"]
            },
            batch_size=100,
            realtime=True
        )

        assert message.subscription_type == "task_progress"
        assert message.filters["user_id"] == "user-001"
        assert "skill_creation" in message.filters["task_types"]
        assert message.batch_size == 100
        assert message.realtime is True

    def test_error_message_valid(self):
        """Test ErrorMessage with valid data."""
        message = ErrorMessage(
            message_type="error",
            error_code="INVALID_REQUEST",
            error_message="The request format is invalid",
            details={
                "field": "task_id",
                "reason": "missing required field"
            },
            correlation_id="corr-001",
            retry_after=30
        )

        assert message.error_code == "INVALID_REQUEST"
        assert message.error_message == "The request format is invalid"
        assert message.details["field"] == "task_id"
        assert message.correlation_id == "corr-001"
        assert message.retry_after == 30


class TestNotificationConfigSchemas:
    """Test cases for notification configuration schemas."""

    def test_notification_channel_valid(self):
        """Test NotificationChannel with valid data."""
        channel = NotificationChannel(
            name="websocket",
            enabled=True,
            priority="high",
            rate_limit=60,
            retry_policy={
                "max_retries": 3,
                "backoff_factor": 2.0
            },
            config={
                "endpoint": "wss://example.com/ws",
                "timeout": 30
            },
            filters={
                "message_types": ["progress_update", "notification"]
            }
        )

        assert channel.name == "websocket"
        assert channel.enabled is True
        assert channel.priority == "high"
        assert channel.rate_limit == 60
        assert channel.retry_policy["max_retries"] == 3
        assert channel.config["endpoint"] == "wss://example.com/ws"
        assert "progress_update" in channel.filters["message_types"]

    def test_notification_channel_defaults(self):
        """Test NotificationChannel with default values."""
        channel = NotificationChannel(
            name="email"
        )

        assert channel.name == "email"
        assert channel.enabled is True
        assert channel.priority == "normal"
        assert channel.rate_limit is None
        assert channel.retry_policy == {}
        assert channel.config == {}
        assert channel.filters is None

    def test_notification_template_valid(self):
        """Test NotificationTemplate with valid data."""
        template = NotificationTemplate(
            template_id="task_completion",
            name="Task Completion",
            template_type="success",
            channel="websocket",
            subject="Task Completed: {{task_name}}",
            body="Your task '{{task_name}}' has been completed successfully.",
            variables=["task_name", "task_id", "completion_time"],
            formatting={
                "color": "green",
                "icon": "check_circle"
            }
        )

        assert template.template_id == "task_completion"
        assert template.name == "Task Completion"
        assert template.template_type == "success"
        assert template.channel == "websocket"
        assert "{{task_name}}" in template.subject
        assert "{{task_name}}" in template.body
        assert "task_name" in template.variables
        assert template.formatting["color"] == "green"

    def test_notification_template_default_values(self):
        """Test NotificationTemplate with default values."""
        template = NotificationTemplate(
            template_id="test_template",
            name="Test Template",
            template_type="info",
            channel="websocket",
            body="Test message body"
        )

        assert template.subject is None
        assert template.variables is None
        assert template.formatting is None
        assert template.is_active is True
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)

    def test_notification_rule_valid(self):
        """Test NotificationRule with valid data."""
        rule = NotificationRule(
            rule_id="task_completion_rule",
            name="Task Completion Notifications",
            description="Send notifications when tasks are completed",
            enabled=True,
            priority=1,
            conditions={
                "status": "completed",
                "task_types": ["skill_creation", "skill_deployment"]
            },
            actions={
                "channels": ["websocket", "email"],
                "template": "task_completion",
                "priority": "normal"
            },
            filters={
                "user_preferences": True,
                "rate_limit": True
            },
            schedule=None,
            metadata={"version": "1.0"}
        )

        assert rule.rule_id == "task_completion_rule"
        assert rule.name == "Task Completion Notifications"
        assert rule.enabled is True
        assert rule.priority == 1
        assert rule.conditions["status"] == "completed"
        assert "skill_creation" in rule.conditions["task_types"]
        assert "websocket" in rule.actions["channels"]
        assert rule.actions["template"] == "task_completion"
        assert rule.filters["user_preferences"] is True

    def test_user_notification_settings_valid(self):
        """Test UserNotificationSettings with valid data."""
        settings = UserNotificationSettings(
            user_id="user-001",
            channels={
                "websocket": {
                    "enabled": True,
                    "priority": "high"
                },
                "email": {
                    "enabled": True,
                    "priority": "normal",
                    "config": {
                        "address": "user@example.com"
                    }
                }
            },
            preferences={
                "task_completion": True,
                "task_failure": True,
                "task_progress": False,
                "system_alerts": True
            },
            quiet_hours={
                "enabled": True,
                "start_time": "22:00",
                "end_time": "08:00",
                "timezone": "UTC"
            },
            rate_limits={
                "notifications_per_hour": 50,
                "notifications_per_day": 200
            }
        )

        assert settings.user_id == "user-001"
        assert settings.channels["websocket"]["enabled"] is True
        assert settings.channels["email"]["enabled"] is True
        assert settings.preferences["task_completion"] is True
        assert settings.preferences["task_progress"] is False
        assert settings.quiet_hours["enabled"] is True
        assert settings.rate_limits["notifications_per_hour"] == 50

    def test_notification_stats_valid(self):
        """Test NotificationStats with valid data."""
        stats = NotificationStats(
            user_id="user-001",
            total_sent=150,
            total_failed=5,
            by_channel={
                "websocket": {"sent": 100, "failed": 2},
                "email": {"sent": 50, "failed": 3}
            },
            by_type={
                "task_completion": 80,
                "task_failure": 20,
                "task_progress": 50,
                "system_alerts": 5
            },
            recent_activity=[
                {
                    "timestamp": datetime.now(timezone.utc),
                    "type": "task_completion",
                    "channel": "websocket",
                    "status": "sent"
                }
            ]
        )

        assert stats.user_id == "user-001"
        assert stats.total_sent == 150
        assert stats.total_failed == 5
        assert stats.by_channel["websocket"]["sent"] == 100
        assert stats.by_type["task_completion"] == 80
        assert len(stats.recent_activity) == 1
        assert stats.recent_activity[0]["status"] == "sent"

    def test_bulk_notification_request_valid(self):
        """Test BulkNotificationRequest with valid data."""
        request = BulkNotificationRequest(
            notifications=[
                {
                    "user_id": "user-001",
                    "title": "Task 1 Completed",
                    "message": "Task 1 has been completed",
                    "notification_type": "success"
                },
                {
                    "user_id": "user-002",
                    "title": "Task 2 Failed",
                    "message": "Task 2 has failed",
                    "notification_type": "error"
                }
            ],
            channels=["websocket", "email"],
            dry_run=False,
            metadata={"batch_id": "batch-001"}
        )

        assert len(request.notifications) == 2
        assert request.notifications[0]["user_id"] == "user-001"
        assert request.notifications[1]["user_id"] == "user-002"
        assert "websocket" in request.channels
        assert request.dry_run is False
        assert request.metadata["batch_id"] == "batch-001"


class TestSchemaIntegration:
    """Integration tests for progress tracking schemas."""

    def test_task_lifecycle_schemas(self):
        """Test schemas for complete task lifecycle."""
        # Create task
        create_request = CreateTaskRequest(
            task_id="lifecycle-task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Lifecycle Test Task",
            description="Testing complete task lifecycle",
            estimated_duration=600,
            total_steps=6
        )

        # Update progress
        update_request = UpdateProgressRequest(
            task_id="lifecycle-task-001",
            progress=33.33,
            status="running",
            current_step="step_2",
            message="Processing step 2 of 6"
        )

        # Create response
        response = TaskProgressResponse(
            id=str(uuid4()),
            task_id="lifecycle-task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Lifecycle Test Task",
            progress=33.33,
            status="running",
            current_step="step_2",
            total_steps=6,
            estimated_duration=600,
            started_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Verify data consistency
        assert create_request.task_id == update_request.task_id == response.task_id
        assert create_request.user_id == response.user_id
        assert update_request.progress == response.progress
        assert update_request.status == response.status

    def test_websocket_message_flow(self):
        """Test WebSocket message flow."""
        # Connection message
        connect_msg = ConnectionMessage(
            message_type="connection",
            action="connect",
            client_id="client-001",
            user_id="user-001"
        )

        # Progress update message
        progress_msg = ProgressUpdateMessage(
            message_type="progress_update",
            task_id="task-001",
            user_id="user-001",
            progress=50.0,
            status="running"
        )

        # Notification message
        notification_msg = NotificationMessage(
            message_type="notification",
            user_id="user-001",
            title="Task Update",
            message="Task progress updated"
        )

        # Heartbeat message
        heartbeat_msg = HeartbeatMessage(
            message_type="heartbeat",
            client_id="client-001"
        )

        # Verify message flow
        assert connect_msg.message_type == "connection"
        assert progress_msg.progress == 50.0
        assert notification_msg.title == "Task Update"
        assert heartbeat_msg.message_type == "heartbeat"

    def test_notification_flow(self):
        """Test complete notification flow."""
        # Channel configuration
        channel = NotificationChannel(
            name="websocket",
            enabled=True,
            priority="high"
        )

        # Template
        template = NotificationTemplate(
            template_id="progress_update",
            name="Progress Update",
            template_type="info",
            channel="websocket",
            body="Task {{task_name}} is now {{progress}}% complete"
        )

        # Rule
        rule = NotificationRule(
            rule_id="progress_rule",
            name="Progress Updates",
            enabled=True,
            conditions={"status": "running"},
            actions={"channels": ["websocket"], "template": "progress_update"}
        )

        # User settings
        settings = UserNotificationSettings(
            user_id="user-001",
            channels={"websocket": {"enabled": True}},
            preferences={"task_progress": True}
        )

        # Verify configuration
        assert channel.name == "websocket"
        assert template.template_id == "progress_update"
        assert rule.conditions["status"] == "running"
        assert settings.preferences["task_progress"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
