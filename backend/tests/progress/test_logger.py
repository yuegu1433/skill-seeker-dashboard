"""Tests for log management functionality.

This module contains comprehensive tests for LogManager and related components,
including log collection, storage, search, export, and streaming capabilities.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from uuid import uuid4

# Import components to test
from backend.app.progress.models.log import TaskLog, LogLevel
from backend.app.progress.log_manager import LogManager, LogStream
from backend.app.progress.log_stream import (
    LogStreamService,
    LogStreamSession,
    StreamFilter,
    StreamStatus,
)
from backend.app.progress.schemas.progress_operations import (
    CreateLogEntryRequest,
    LogQueryParams,
    BulkLogRequest,
)
from backend.app.progress.schemas.websocket_messages import LogMessage, MessageType


class TestLogStream:
    """Test LogStream functionality."""

    @pytest.fixture
    def task_id(self):
        """Create test task ID."""
        return "test-task-123"

    @pytest.fixture
    def log_stream(self, task_id):
        """Create LogStream instance."""
        return LogStream(task_id=task_id, max_size=100)

    @pytest.fixture
    def sample_log_entry(self, task_id):
        """Create sample log entry."""
        return TaskLog(
            task_id=task_id,
            level=LogLevel.INFO,
            message="Test log message",
            source="test-source",
            context={"key": "value"},
        )

    @pytest.mark.asyncio
    async def test_add_log(self, log_stream, sample_log_entry):
        """Test adding log entry to stream."""
        await log_stream.add_log(sample_log_entry)

        # Check log was added
        logs = log_stream.get_recent_logs(limit=10)
        assert len(logs) == 1
        assert logs[0] == sample_log_entry

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, log_stream):
        """Test subscription management."""
        connection_id = "test-connection"

        # Subscribe
        await log_stream.subscribe(connection_id)
        assert connection_id in log_stream.subscribers
        assert log_stream.get_subscriber_count() == 1

        # Unsubscribe
        await log_stream.unsubscribe(connection_id)
        assert connection_id not in log_stream.subscribers
        assert log_stream.get_subscriber_count() == 0

    @pytest.mark.asyncio
    async def test_max_size_limit(self, task_id):
        """Test log stream size limit."""
        stream = LogStream(task_id=task_id, max_size=5)

        # Add more logs than max size
        for i in range(10):
            log_entry = TaskLog(
                task_id=task_id,
                level=LogLevel.INFO,
                message=f"Log message {i}",
                source="test-source",
            )
            await stream.add_log(log_entry)

        # Check only max_size logs are kept
        logs = stream.get_recent_logs(limit=10)
        assert len(logs) == 5
        assert logs[0].message == "Log message 5"  # First kept log
        assert logs[-1].message == "Log message 9"  # Last log


class TestStreamFilter:
    """Test StreamFilter functionality."""

    @pytest.fixture
    def sample_log_entry(self):
        """Create sample log entry."""
        return TaskLog(
            task_id="task-123",
            level=LogLevel.ERROR,
            message="Error occurred in processing",
            source="worker-1",
            timestamp=datetime.utcnow(),
            context={"error_code": 500},
        )

    def test_filter_by_task_id(self, sample_log_entry):
        """Test filtering by task ID."""
        filter_obj = StreamFilter(task_id="task-123")
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(task_id="other-task")
        assert not filter_obj.matches(sample_log_entry)

    def test_filter_by_level(self, sample_log_entry):
        """Test filtering by log level."""
        # Single level
        filter_obj = StreamFilter(level="ERROR")
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(level="INFO")
        assert not filter_obj.matches(sample_log_entry)

        # Multiple levels
        filter_obj = StreamFilter(level=["ERROR", "WARNING"])
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(level=["INFO", "DEBUG"])
        assert not filter_obj.matches(sample_log_entry)

    def test_filter_by_source(self, sample_log_entry):
        """Test filtering by source."""
        filter_obj = StreamFilter(source="worker-1")
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(source="worker-2")
        assert not filter_obj.matches(sample_log_entry)

    def test_filter_by_search(self, sample_log_entry):
        """Test text search filtering."""
        filter_obj = StreamFilter(search="error")
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(search="Error")
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(search="processing")
        assert filter_obj.matches(sample_log_entry)

        filter_obj = StreamFilter(search="nonexistent")
        assert not filter_obj.matches(sample_log_entry)

    def test_filter_by_date(self, sample_log_entry):
        """Test date range filtering."""
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        hour_later = now + timedelta(hours=1)

        # Filter within range
        filter_obj = StreamFilter(date_from=hour_ago, date_to=hour_later)
        assert filter_obj.matches(sample_log_entry)

        # Filter before range
        filter_obj = StreamFilter(date_from=hour_later)
        assert not filter_obj.matches(sample_log_entry)

        # Filter after range
        filter_obj = StreamFilter(date_to=hour_ago)
        assert not filter_obj.matches(sample_log_entry)


class TestLogStreamSession:
    """Test LogStreamSession functionality."""

    @pytest.fixture
    def session(self):
        """Create LogStreamSession instance."""
        return LogStreamSession(
            session_id="session-123",
            connection_id="connection-123",
            filter=StreamFilter(task_id="task-123"),
            buffer_size=10,
            flush_interval=0.1,
        )

    @pytest.mark.asyncio
    async def test_start_stop_session(self, session):
        """Test session lifecycle."""
        assert session.status == StreamStatus.IDLE
        assert not session._running

        # Start session
        await session.start()
        assert session.status == StreamStatus.STREAMING
        assert session._running

        # Stop session
        await session.stop()
        assert session.status == StreamStatus.IDLE
        assert not session._running

    @pytest.mark.asyncio
    async def test_pause_resume_session(self, session):
        """Test pause and resume functionality."""
        await session.start()
        assert session.status == StreamStatus.STREAMING

        # Pause
        await session.pause()
        assert session.status == StreamStatus.PAUSED

        # Resume
        await session.resume()
        assert session.status == StreamStatus.STREAMING

    def test_log_filtering(self, session):
        """Test log filtering in session."""
        # Matching log
        matching_log = TaskLog(
            task_id="task-123",
            level=LogLevel.INFO,
            message="Test message",
            source="test",
        )
        session.add_log(matching_log)
        assert len(session.buffer) == 1

        # Non-matching log
        non_matching_log = TaskLog(
            task_id="other-task",
            level=LogLevel.INFO,
            message="Test message",
            source="test",
        )
        session.add_log(non_matching_log)
        assert len(session.buffer) == 1  # Still 1, not added

    def test_session_stats(self, session):
        """Test session statistics."""
        stats = session.get_stats()
        assert "session_id" in stats
        assert "status" in stats
        assert "buffer_size" in stats
        assert "total_sent" in stats
        assert "total_filtered" in stats
        assert "running" in stats


class TestLogManager:
    """Test LogManager functionality."""

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.refresh = Mock()
        session.delete = Mock()
        return session

    @pytest.fixture
    def log_manager(self, mock_db_session):
        """Create LogManager instance."""
        return LogManager(db_session=mock_db_session)

    @pytest.mark.asyncio
    async def test_create_log_entry(self, log_manager, mock_db_session):
        """Test log entry creation."""
        request = CreateLogEntryRequest(
            task_id="task-123",
            level="INFO",
            message="Test log message",
            source="test-source",
            context={"key": "value"},
        )

        result = await log_manager.create_log_entry(request)

        # Verify log entry was created
        assert result.task_id == request.task_id
        assert result.level == request.level
        assert result.message == request.message
        assert result.source == request.source
        assert result.context == request.context

        # Verify database operations
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_task_logs(self, log_manager, mock_db_session):
        """Test getting task logs."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db_session.query = Mock(return_value=mock_query)

        query = LogQueryParams(task_id="task-123", limit=10)
        logs = await log_manager.list_logs(query)

        # Verify query was built correctly
        mock_db_session.query.assert_called_once()
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.limit.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_logs(self, log_manager, mock_db_session):
        """Test log search functionality."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db_session.query = Mock(return_value=mock_query)

        logs = await log_manager.search_logs(
            query="error",
            task_id="task-123",
            limit=10,
        )

        # Verify search was performed
        mock_db_session.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_create_logs(self, log_manager, mock_db_session):
        """Test bulk log creation."""
        log_requests = [
            CreateLogEntryRequest(
                task_id="task-123",
                level="INFO",
                message=f"Log message {i}",
                source="test",
            )
            for i in range(5)
        ]

        request = BulkLogRequest(logs=log_requests)
        result = await log_manager.bulk_create_logs(request)

        # Verify all logs were created
        assert result["total"] == 5
        assert len(result["successful"]) == 5
        assert len(result["failed"]) == 0

    @pytest.mark.asyncio
    async def test_delete_task_logs(self, log_manager, mock_db_session):
        """Test log deletion."""
        # Mock database query and delete
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=[])
        mock_db_session.query = Mock(return_value=mock_query)

        deleted_count = await log_manager.delete_task_logs("task-123")

        # Verify deletion was performed
        mock_db_session.query.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_log_statistics(self, log_manager):
        """Test log statistics."""
        stats = log_manager.get_stats()

        # Verify statistics structure
        assert "total_logs_created" in stats
        assert "logs_by_level" in stats
        assert "active_streams" in stats
        assert "total_subscribers" in stats

    @pytest.mark.asyncio
    async def test_export_logs_json(self, log_manager, mock_db_session):
        """Test log export to JSON."""
        # Mock database query to return sample logs
        sample_logs = [
            TaskLog(
                task_id="task-123",
                level=LogLevel.INFO,
                message="Test message 1",
                source="test",
                timestamp=datetime.utcnow(),
            ),
            TaskLog(
                task_id="task-123",
                level=LogLevel.ERROR,
                message="Test message 2",
                source="test",
                timestamp=datetime.utcnow(),
            ),
        ]

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.limit = Mock(return_value=mock_query)
        mock_query.all = Mock(return_value=sample_logs)
        mock_db_session.query = Mock(return_value=mock_query)

        # Test export (without actual storage manager for simplicity)
        # This test validates the serialization logic
        json_output = log_manager._serialize_logs_json(sample_logs)
        parsed = json.loads(json_output)

        assert len(parsed) == 2
        assert parsed[0]["task_id"] == "task-123"
        assert parsed[0]["level"] == "INFO"
        assert parsed[1]["level"] == "ERROR"

    @pytest.mark.asyncio
    async def test_export_logs_csv(self, log_manager):
        """Test log export to CSV."""
        sample_logs = [
            TaskLog(
                task_id="task-123",
                level=LogLevel.INFO,
                message="Test message 1",
                source="test",
                timestamp=datetime.utcnow(),
            ),
        ]

        csv_output = log_manager._serialize_logs_csv(sample_logs)

        # Verify CSV structure
        lines = csv_output.strip().split('\n')
        assert len(lines) >= 2  # Header + data
        assert "ID" in lines[0]
        assert "Task ID" in lines[0]
        assert "task-123" in csv_output

    @pytest.mark.asyncio
    async def test_export_logs_txt(self, log_manager):
        """Test log export to plain text."""
        sample_logs = [
            TaskLog(
                task_id="task-123",
                level=LogLevel.INFO,
                message="Test message",
                source="test",
                timestamp=datetime.utcnow(),
            ),
        ]

        txt_output = log_manager._serialize_logs_txt(sample_logs)

        # Verify text structure
        assert "LOG EXPORT REPORT" in txt_output
        assert "Total logs: 1" in txt_output
        assert "[INFO]" in txt_output
        assert "Test message" in txt_output


class TestLogStreamService:
    """Test LogStreamService functionality."""

    @pytest.fixture
    def stream_service(self):
        """Create LogStreamService instance."""
        return LogStreamService()

    @pytest.mark.asyncio
    async def test_create_stream(self, stream_service):
        """Test stream creation."""
        filter_params = {
            "task_id": "task-123",
            "level": "INFO",
        }

        session_id = await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Verify session was created
        assert session_id in stream_service.sessions
        assert "connection-123" in stream_service.connection_to_session
        assert stream_service.sessions[session_id].status == StreamStatus.STREAMING

    @pytest.mark.asyncio
    async def test_close_stream(self, stream_service):
        """Test stream closure."""
        # Create stream first
        filter_params = {"task_id": "task-123"}
        session_id = await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Close stream
        await stream_service.close_stream("connection-123")

        # Verify session was removed
        assert session_id not in stream_service.sessions
        assert "connection-123" not in stream_service.connection_to_session

    @pytest.mark.asyncio
    async def test_pause_resume_stream(self, stream_service):
        """Test pause and resume functionality."""
        # Create stream
        filter_params = {"task_id": "task-123"}
        await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Pause
        await stream_service.pause_stream("connection-123")
        session = stream_service.sessions[
            stream_service.connection_to_session["connection-123"]
        ]
        assert session.status == StreamStatus.PAUSED

        # Resume
        await stream_service.resume_stream("connection-123")
        assert session.status == StreamStatus.STREAMING

    @pytest.mark.asyncio
    async def test_add_log_to_streams(self, stream_service):
        """Test adding logs to all matching streams."""
        # Create stream with task filter
        filter_params = {"task_id": "task-123"}
        await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Add matching log
        matching_log = TaskLog(
            task_id="task-123",
            level=LogLevel.INFO,
            message="Test message",
            source="test",
        )
        await stream_service.add_log_to_streams(matching_log)

        # Verify log was added to session
        session_id = stream_service.connection_to_session["connection-123"]
        session = stream_service.sessions[session_id]
        assert len(session.buffer) == 1

        # Add non-matching log
        non_matching_log = TaskLog(
            task_id="other-task",
            level=LogLevel.INFO,
            message="Test message",
            source="test",
        )
        await stream_service.add_log_to_streams(non_matching_log)

        # Verify non-matching log was not added
        assert len(session.buffer) == 1

    @pytest.mark.asyncio
    async def test_update_filter(self, stream_service):
        """Test filter update."""
        # Create stream
        filter_params = {"task_id": "task-123"}
        await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Update filter
        new_filter = {"task_id": "task-456", "level": "ERROR"}
        result = await stream_service.update_filter(
            connection_id="connection-123",
            filter_params=new_filter,
        )

        assert result is True
        session_id = stream_service.connection_to_session["connection-123"]
        session = stream_service.sessions[session_id]
        assert session.filter.task_id == "task-456"
        assert session.filter.level == "ERROR"

    @pytest.mark.asyncio
    async def test_handle_websocket_message(self, stream_service):
        """Test WebSocket message handling."""
        # Mock websocket_manager.send_message
        with patch('backend.app.progress.log_stream.websocket_manager') as mock_ws:
            mock_ws.send_message = AsyncMock(return_value=True)

            # Test start_stream message
            message = {
                "type": "start_stream",
                "filter": {"task_id": "task-123"},
                "buffer_size": 100,
                "flush_interval": 0.1,
            }
            await stream_service.handle_websocket_message(
                "connection-123",
                message,
            )

            # Verify stream was created
            assert len(stream_service.sessions) == 1

    def test_service_statistics(self, stream_service):
        """Test service statistics."""
        stats = stream_service.get_stats()

        # Verify statistics structure
        assert "active_sessions" in stats
        assert "total_sessions" in stats
        assert "total_logs_streamed" in stats
        assert "total_connections" in stats
        assert "session_breakdown" in stats

    @pytest.mark.asyncio
    async def test_cleanup_idle_sessions(self, stream_service):
        """Test cleanup of idle sessions."""
        # Create paused session
        filter_params = {"task_id": "task-123"}
        await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Pause session
        await stream_service.pause_stream("connection-123")

        # Mock last_flush to simulate idle time
        session = stream_service.sessions[
            stream_service.connection_to_session["connection-123"]
        ]
        session.last_flush = time.time() - 7200  # 2 hours ago

        # Cleanup idle sessions
        await stream_service.cleanup_idle_sessions(idle_timeout=3600)  # 1 hour

        # Verify session was cleaned up
        assert len(stream_service.sessions) == 0


class TestLogIntegration:
    """Integration tests for log system."""

    @pytest.mark.asyncio
    async def test_end_to_end_log_flow(self):
        """Test complete log flow from creation to streaming."""
        # Create components
        log_manager = LogManager()
        stream_service = LogStreamService(log_manager)

        # Create log entry
        request = CreateLogEntryRequest(
            task_id="task-123",
            level="INFO",
            message="Integration test message",
            source="test",
        )
        log_entry = await log_manager.create_log_entry(request)

        # Verify log was created
        assert log_entry.task_id == "task-123"
        assert log_entry.message == "Integration test message"

        # Create stream
        filter_params = {"task_id": "task-123"}
        session_id = await stream_service.create_stream(
            connection_id="connection-123",
            filter_params=filter_params,
        )

        # Add log to stream
        await stream_service.add_log_to_streams(log_entry)

        # Verify log reached stream
        session = stream_service.sessions[session_id]
        assert len(session.buffer) == 1
        assert session.total_filtered == 1

    @pytest.mark.asyncio
    async def test_filtered_streaming(self):
        """Test filtered log streaming."""
        log_manager = LogManager()
        stream_service = LogStreamService(log_manager)

        # Create streams with different filters
        await stream_service.create_stream(
            connection_id="connection-info",
            filter_params={"level": "INFO"},
        )
        await stream_service.create_stream(
            connection_id="connection-error",
            filter_params={"level": "ERROR"},
        )

        # Add different level logs
        info_log = TaskLog(
            task_id="task-123",
            level=LogLevel.INFO,
            message="Info message",
            source="test",
        )
        error_log = TaskLog(
            task_id="task-123",
            level=LogLevel.ERROR,
            message="Error message",
            source="test",
        )

        await stream_service.add_log_to_streams(info_log)
        await stream_service.add_log_to_streams(error_log)

        # Verify filtering worked
        info_session = stream_service.sessions[
            stream_service.connection_to_session["connection-info"]
        ]
        error_session = stream_service.sessions[
            stream_service.connection_to_session["connection-error"]
        ]

        assert len(info_session.buffer) == 1
        assert info_session.buffer[0].level == LogLevel.INFO
        assert len(error_session.buffer) == 1
        assert error_session.buffer[0].level == LogLevel.ERROR


# Test data fixtures
@pytest.fixture
def sample_logs():
    """Create sample log entries for testing."""
    logs = []
    for i in range(10):
        logs.append(
            TaskLog(
                task_id=f"task-{i % 3}",  # 3 different tasks
                level=list(LogLevel)[i % len(LogLevel)],  # Cycle through levels
                message=f"Log message {i}",
                source=f"source-{i % 2}",  # 2 different sources
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                context={"index": i},
            )
        )
    return logs


@pytest.fixture
def log_query_params():
    """Create sample log query parameters."""
    return LogQueryParams(
        task_id="task-1",
        level="INFO",
        source="source-1",
        search="error",
        date_from=datetime.utcnow() - timedelta(hours=1),
        date_to=datetime.utcnow(),
        limit=50,
        sort_order="desc",
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
