"""Log streaming service for real-time log delivery.

This module provides LogStreamService for streaming logs to WebSocket clients
with real-time filtering and push capabilities.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4
from collections import deque, defaultdict

from .models.log import TaskLog, LogLevel
from .schemas.progress_operations import LogQueryParams
from .schemas.websocket_messages import (
    LogMessage,
    MessageType,
    StreamControlMessage,
)
from .log_manager import LogManager, LogStream
from .websocket import websocket_manager

logger = logging.getLogger(__name__)


class StreamStatus(Enum):
    """Log stream status."""
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    ERROR = "error"


class StreamFilter:
    """Filter for log stream."""

    def __init__(
        self,
        task_id: Optional[str] = None,
        level: Optional[Union[str, List[str]]] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
    ):
        """Initialize stream filter.

        Args:
            task_id: Filter by task ID
            level: Filter by log level(s)
            source: Filter by source
            search: Text search filter
            date_from: Filter from date
            date_to: Filter to date
        """
        self.task_id = task_id
        self.level = level
        self.source = source
        self.search = search
        self.date_from = date_from
        self.date_to = date_to

    def matches(self, log_entry: TaskLog) -> bool:
        """Check if log entry matches filter.

        Args:
            log_entry: TaskLog instance

        Returns:
            True if log matches filter
        """
        if self.task_id and log_entry.task_id != self.task_id:
            return False

        if self.level:
            if isinstance(self.level, list):
                if log_entry.level not in self.level:
                    return False
            elif log_entry.level != self.level:
                return False

        if self.source and self.source not in log_entry.source:
            return False

        if self.search:
            search_lower = self.search.lower()
            if (search_lower not in log_entry.message.lower() and
                search_lower not in log_entry.source.lower()):
                return False

        if self.date_from and log_entry.timestamp and log_entry.timestamp < self.date_from:
            return False

        if self.date_to and log_entry.timestamp and log_entry.timestamp > self.date_to:
            return False

        return True


class LogStreamSession:
    """Manages a single log streaming session."""

    def __init__(
        self,
        session_id: str,
        connection_id: str,
        filter: StreamFilter,
        buffer_size: int = 1000,
        flush_interval: float = 0.1,
    ):
        """Initialize log stream session.

        Args:
            session_id: Unique session ID
            connection_id: WebSocket connection ID
            filter: Stream filter
            buffer_size: Buffer size for batching
            flush_interval: Flush interval in seconds
        """
        self.session_id = session_id
        self.connection_id = connection_id
        self.filter = filter
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.status = StreamStatus.IDLE
        self.buffer: deque = deque(maxlen=buffer_size)
        self.last_flush = time.time()
        self.total_sent = 0
        self.total_filtered = 0
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the streaming session."""
        self._running = True
        self.status = StreamStatus.STREAMING
        self._task = asyncio.create_task(self._stream_loop())

    async def stop(self):
        """Stop the streaming session."""
        self._running = False
        self.status = StreamStatus.IDLE
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def pause(self):
        """Pause the streaming session."""
        self._running = False
        self.status = StreamStatus.PAUSED

    async def resume(self):
        """Resume the streaming session."""
        self._running = True
        self.status = StreamStatus.STREAMING

    def add_log(self, log_entry: TaskLog):
        """Add log to session buffer.

        Args:
            log_entry: TaskLog instance
        """
        if self.filter.matches(log_entry):
            self.buffer.append(log_entry)
            self.total_filtered += 1

    async def _stream_loop(self):
        """Main streaming loop."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)

                # Check if buffer needs flushing
                now = time.time()
                if (len(self.buffer) > 0 and
                    (now - self.last_flush >= self.flush_interval or
                     len(self.buffer) >= self.buffer_size)):
                    await self._flush_buffer()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stream loop: {e}")
                self.status = StreamStatus.ERROR

    async def _flush_buffer(self):
        """Flush buffer to WebSocket connection."""
        if not self.buffer:
            return

        logs_to_send = list(self.buffer)
        self.buffer.clear()
        self.last_flush = time.time()

        # Create batch message
        messages = []
        for log_entry in logs_to_send:
            message = LogMessage(
                type=MessageType.LOG_MESSAGE,
                task_id=log_entry.task_id,
                level=log_entry.level,
                message=log_entry.message,
                source=log_entry.source,
                timestamp=log_entry.timestamp.timestamp() if log_entry.timestamp else time.time(),
            )
            messages.append(message.dict())

        # Send batch
        if messages:
            success = await websocket_manager.send_message(
                self.connection_id,
                {
                    "type": "log_batch",
                    "messages": messages,
                    "count": len(messages),
                    "session_id": self.session_id,
                }
            )

            if success:
                self.total_sent += len(messages)
            else:
                logger.warning(f"Failed to send batch to connection {self.connection_id}")

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "buffer_size": len(self.buffer),
            "total_sent": self.total_sent,
            "total_filtered": self.total_filtered,
            "running": self._running,
        }


class LogStreamService:
    """Service for real-time log streaming."""

    def __init__(self, log_manager: Optional[LogManager] = None):
        """Initialize log stream service.

        Args:
            log_manager: LogManager instance
        """
        self.log_manager = log_manager
        self.sessions: Dict[str, LogStreamSession] = {}
        self.connection_to_session: Dict[str, str] = {}
        self._stats = {
            "active_sessions": 0,
            "total_sessions": 0,
            "total_logs_streamed": 0,
            "total_connections": 0,
        }

    async def create_stream(
        self,
        connection_id: str,
        filter_params: Dict[str, Any],
        buffer_size: int = 1000,
        flush_interval: float = 0.1,
    ) -> str:
        """Create a new log stream session.

        Args:
            connection_id: WebSocket connection ID
            filter_params: Stream filter parameters
            buffer_size: Buffer size for batching
            flush_interval: Flush interval in seconds

        Returns:
            Session ID
        """
        # Create filter
        filter_obj = StreamFilter(**filter_params)

        # Generate session ID
        session_id = str(uuid4())

        # Create session
        session = LogStreamSession(
            session_id=session_id,
            connection_id=connection_id,
            filter=filter_obj,
            buffer_size=buffer_size,
            flush_interval=flush_interval,
        )

        # Store session
        self.sessions[session_id] = session
        self.connection_to_session[connection_id] = session_id
        self._stats["active_sessions"] += 1
        self._stats["total_sessions"] += 1

        # Start session
        await session.start()

        logger.info(f"Created log stream session {session_id} for connection {connection_id}")
        return session_id

    async def close_stream(self, connection_id: str):
        """Close log stream session.

        Args:
            connection_id: WebSocket connection ID
        """
        session_id = self.connection_to_session.get(connection_id)
        if not session_id:
            return

        session = self.sessions.get(session_id)
        if session:
            await session.stop()
            del self.sessions[session_id]

        del self.connection_to_session[connection_id]
        self._stats["active_sessions"] = len(self.sessions)

        logger.info(f"Closed log stream session {session_id} for connection {connection_id}")

    async def pause_stream(self, connection_id: str):
        """Pause log stream session.

        Args:
            connection_id: WebSocket connection ID
        """
        session_id = self.connection_to_session.get(connection_id)
        if not session_id:
            return

        session = self.sessions.get(session_id)
        if session:
            await session.pause()

    async def resume_stream(self, connection_id: str):
        """Resume log stream session.

        Args:
            connection_id: WebSocket connection ID
        """
        session_id = self.connection_to_session.get(connection_id)
        if not session_id:
            return

        session = self.sessions.get(session_id)
        if session:
            await session.resume()

    async def add_log_to_streams(self, log_entry: TaskLog):
        """Add log entry to all matching stream sessions.

        Args:
            log_entry: TaskLog instance
        """
        for session in self.sessions.values():
            if session.status == StreamStatus.STREAMING:
                session.add_log(log_entry)
                self._stats["total_logs_streamed"] += 1

    async def update_filter(
        self,
        connection_id: str,
        filter_params: Dict[str, Any],
    ) -> bool:
        """Update stream filter.

        Args:
            connection_id: WebSocket connection ID
            filter_params: New filter parameters

        Returns:
            True if updated successfully
        """
        session_id = self.connection_to_session.get(connection_id)
        if not session_id:
            return False

        session = self.sessions.get(session_id)
        if not session:
            return False

        # Update filter
        session.filter = StreamFilter(**filter_params)

        # Send acknowledgment
        await websocket_manager.send_message(connection_id, {
            "type": "filter_updated",
            "session_id": session_id,
            "filter": filter_params,
        })

        return True

    async def get_session_stats(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get session statistics.

        Args:
            connection_id: WebSocket connection ID

        Returns:
            Dictionary containing session statistics
        """
        session_id = self.connection_to_session.get(connection_id)
        if not session_id:
            return None

        session = self.sessions.get(session_id)
        if not session:
            return None

        return session.get_stats()

    async def handle_websocket_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ):
        """Handle WebSocket message for log streaming.

        Args:
            connection_id: WebSocket connection ID
            message: WebSocket message
        """
        message_type = message.get("type")

        if message_type == "start_stream":
            # Create new stream
            filter_params = message.get("filter", {})
            buffer_size = message.get("buffer_size", 1000)
            flush_interval = message.get("flush_interval", 0.1)

            session_id = await self.create_stream(
                connection_id=connection_id,
                filter_params=filter_params,
                buffer_size=buffer_size,
                flush_interval=flush_interval,
            )

            # Send acknowledgment
            await websocket_manager.send_message(connection_id, {
                "type": "stream_started",
                "session_id": session_id,
                "filter": filter_params,
            })

        elif message_type == "stop_stream":
            # Close stream
            await self.close_stream(connection_id)

            # Send acknowledgment
            await websocket_manager.send_message(connection_id, {
                "type": "stream_stopped",
            })

        elif message_type == "pause_stream":
            # Pause stream
            await self.pause_stream(connection_id)

        elif message_type == "resume_stream":
            # Resume stream
            await self.resume_stream(connection_id)

        elif message_type == "update_filter":
            # Update filter
            filter_params = message.get("filter", {})
            await self.update_filter(connection_id, filter_params)

        elif message_type == "get_stats":
            # Get session stats
            stats = await self.get_session_stats(connection_id)
            if stats:
                await websocket_manager.send_message(connection_id, {
                    "type": "session_stats",
                    "stats": stats,
                })

    async def handle_connection_close(self, connection_id: str):
        """Handle WebSocket connection close.

        Args:
            connection_id: WebSocket connection ID
        """
        await self.close_stream(connection_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **dict(self._stats),
            "active_sessions": len(self.sessions),
            "session_breakdown": {
                session_id: session.status.value
                for session_id, session in self.sessions.items()
            },
        }

    async def cleanup_idle_sessions(self, idle_timeout: float = 3600.0):
        """Clean up idle sessions.

        Args:
            idle_timeout: Session idle timeout in seconds
        """
        current_time = time.time()
        idle_sessions = []

        for session_id, session in self.sessions.items():
            if not session._running and session.status == StreamStatus.PAUSED:
                # Check if session has been idle
                if current_time - session.last_flush >= idle_timeout:
                    idle_sessions.append(session.connection_id)

        # Close idle sessions
        for connection_id in idle_sessions:
            await self.close_stream(connection_id)

        if idle_sessions:
            logger.info(f"Cleaned up {len(idle_sessions)} idle log stream sessions")


# Global log stream service instance
log_stream_service = LogStreamService()
