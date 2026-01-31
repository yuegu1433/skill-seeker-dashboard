"""Log management for real-time progress tracking.

This module provides LogManager for capturing, storing, and streaming
task execution logs with real-time updates via WebSocket.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional, Set, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from uuid import UUID, uuid4
from collections import deque, defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text

from .models.log import TaskLog, LogLevel
from .schemas.progress_operations import (
    CreateLogEntryRequest,
    LogQueryParams,
    BulkLogRequest,
)
from .schemas.websocket_messages import (
    LogMessage,
    MessageType,
)
from .utils.validators import (
    validate_task_id,
    validate_log_level,
    ValidationError,
)
from .utils.serializers import serialize_log_entry
from .utils.formatters import format_timestamp, format_relative_time
from .websocket import websocket_manager
from ..storage.manager import SkillStorageManager

logger = logging.getLogger(__name__)


class LogStream:
    """Manages real-time log streaming for a task."""

    def __init__(self, task_id: str, max_size: int = 1000):
        """Initialize log stream.

        Args:
            task_id: Associated task ID
            max_size: Maximum number of logs to keep in memory
        """
        self.task_id = task_id
        self.max_size = max_size
        self.logs: deque = deque(maxlen=max_size)
        self.subscribers: Set[str] = set()  # WebSocket connection IDs
        self._lock = asyncio.Lock()

    async def add_log(self, log_entry: TaskLog):
        """Add log entry to stream.

        Args:
            log_entry: TaskLog instance
        """
        async with self._lock:
            self.logs.append(log_entry)

        # Broadcast to subscribers
        await self._broadcast_log(log_entry)

    async def _broadcast_log(self, log_entry: TaskLog):
        """Broadcast log entry to all subscribers.

        Args:
            log_entry: TaskLog instance
        """
        if not self.subscribers:
            return

        message = LogMessage(
            type=MessageType.LOG_MESSAGE,
            task_id=log_entry.task_id,
            level=log_entry.level,
            message=log_entry.message,
            source=log_entry.source,
            timestamp=time.time(),
        )

        # Send to all subscribers
        disconnected = set()
        for connection_id in self.subscribers:
            success = await websocket_manager.send_message(connection_id, message.dict())
            if not success:
                disconnected.add(connection_id)

        # Remove disconnected subscribers
        for connection_id in disconnected:
            self.subscribers.discard(connection_id)

    async def subscribe(self, connection_id: str):
        """Subscribe to log stream.

        Args:
            connection_id: WebSocket connection ID
        """
        async with self._lock:
            self.subscribers.add(connection_id)

        # Send recent logs to new subscriber
        recent_logs = list(self.logs)[-50:]  # Send last 50 logs
        for log_entry in recent_logs:
            message = LogMessage(
                type=MessageType.LOG_MESSAGE,
                task_id=log_entry.task_id,
                level=log_entry.level,
                message=log_entry.message,
                source=log_entry.source,
                timestamp=log_entry.timestamp.timestamp() if log_entry.timestamp else time.time(),
            )
            await websocket_manager.send_message(connection_id, message.dict())

    async def unsubscribe(self, connection_id: str):
        """Unsubscribe from log stream.

        Args:
            connection_id: WebSocket connection ID
        """
        async with self._lock:
            self.subscribers.discard(connection_id)

    def get_recent_logs(self, limit: int = 100) -> List[TaskLog]:
        """Get recent log entries.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of TaskLog instances
        """
        return list(self.logs)[-limit:]

    def get_subscriber_count(self) -> int:
        """Get number of active subscribers.

        Returns:
            Number of subscribers
        """
        return len(self.subscribers)


class LogManager:
    """Core manager for task execution logs."""

    def __init__(self, db_session: Optional[Session] = None, storage_manager: Optional[SkillStorageManager] = None):
        """Initialize log manager.

        Args:
            db_session: SQLAlchemy database session (optional)
            storage_manager: MinIO storage manager for log export (optional)
        """
        self.db_session = db_session
        self.storage_manager = storage_manager
        self.log_streams: Dict[str, LogStream] = {}
        self.log_handlers: List[Callable] = []
        self._lock = asyncio.Lock()
        self._stats = {
            "total_logs_created": 0,
            "logs_by_level": defaultdict(int),
            "active_streams": 0,
            "total_subscribers": 0,
            "exported_files": 0,
            "total_export_size": 0,
        }

    async def create_log_entry(
        self,
        request: CreateLogEntryRequest,
        db_session: Optional[Session] = None,
    ) -> TaskLog:
        """Create a new log entry.

        Args:
            request: Log entry creation request
            db_session: Database session (overrides instance session)

        Returns:
            Created TaskLog instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate request
        if not validate_task_id(request.task_id):
            raise ValidationError(f"Invalid task_id: {request.task_id}")

        if not validate_log_level(request.level):
            raise ValidationError(f"Invalid log level: {request.level}")

        # Create log entry
        log_entry = TaskLog(
            task_id=request.task_id,
            level=request.level,
            message=request.message,
            source=request.source or "unknown",
            context=request.context or {},
            stack_trace=request.stack_trace,
            attachments=request.attachments or [],
        )

        # Save to database if session provided
        session = db_session or self.db_session
        if session:
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)

        # Update statistics
        self._stats["total_logs_created"] += 1
        self._stats["logs_by_level"][request.level] += 1

        # Add to log stream
        await self._add_to_stream(log_entry)

        # Call handlers
        await self._call_handlers("log_created", log_entry)

        logger.debug(f"Created log entry for task {request.task_id}: {request.level} - {request.message}")
        return log_entry

    async def get_log_entry(
        self,
        log_id: Union[str, UUID],
        db_session: Optional[Session] = None,
    ) -> Optional[TaskLog]:
        """Get log entry by ID.

        Args:
            log_id: Log entry ID
            db_session: Database session (overrides instance session)

        Returns:
            TaskLog instance or None if not found
        """
        session = db_session or self.db_session
        if not session:
            return None

        if isinstance(log_id, str):
            try:
                log_id = UUID(log_id)
            except ValueError:
                return None

        return session.query(TaskLog).filter(TaskLog.id == log_id).first()

    async def list_logs(
        self,
        query: LogQueryParams,
        db_session: Optional[Session] = None,
    ) -> List[TaskLog]:
        """List log entries with optional filtering.

        Args:
            query: Query parameters for filtering
            db_session: Database session (overrides instance session)

        Returns:
            List of TaskLog instances
        """
        session = db_session or self.db_session
        if not session:
            # Return logs from streams
            all_logs = []
            for stream in self.log_streams.values():
                # Filter by task_id if specified
                if query.task_id and stream.task_id != query.task_id:
                    continue

                # Filter by level if specified
                if query.level and stream.task_id:
                    # Check if any log matches level
                    matching_logs = [log for log in stream.logs if log.level == query.level]
                    all_logs.extend(matching_logs)
                else:
                    all_logs.extend(stream.logs)

            # Sort and limit
            all_logs.sort(key=lambda log: log.timestamp or datetime.min, reverse=True)
            if query.limit:
                all_logs = all_logs[:query.limit]

            return all_logs

        # Query database
        query_builder = session.query(TaskLog)

        # Apply filters
        if query.task_id:
            query_builder = query_builder.filter(TaskLog.task_id == query.task_id)
        if query.level:
            query_builder = query_builder.filter(TaskLog.level == query.level)
        if query.source:
            query_builder = query_builder.filter(TaskLog.source.like(f"%{query.source}%"))
        if query.search:
            search_pattern = f"%{query.search}%"
            query_builder = query_builder.filter(
                or_(
                    TaskLog.message.like(search_pattern),
                    TaskLog.source.like(search_pattern),
                )
            )
        if query.date_from:
            query_builder = query_builder.filter(TaskLog.timestamp >= query.date_from)
        if query.date_to:
            query_builder = query_builder.filter(TaskLog.timestamp <= query.date_to)

        # Sort
        if query.sort_order == "asc":
            query_builder = query_builder.order_by(asc(TaskLog.timestamp))
        else:
            query_builder = query_builder.order_by(desc(TaskLog.timestamp))

        # Limit
        if query.limit:
            query_builder = query_builder.limit(query.limit)

        return query_builder.all()

    async def get_task_logs(
        self,
        task_id: str,
        level: Optional[str] = None,
        limit: int = 100,
        db_session: Optional[Session] = None,
    ) -> List[TaskLog]:
        """Get logs for a specific task.

        Args:
            task_id: Task ID
            level: Filter by log level (optional)
            limit: Maximum number of logs to return
            db_session: Database session (overrides instance session)

        Returns:
            List of TaskLog instances
        """
        query = LogQueryParams(task_id=task_id, level=level, limit=limit)
        return await self.list_logs(query, db_session)

    async def subscribe_to_logs(
        self,
        task_id: str,
        connection_id: str,
    ) -> bool:
        """Subscribe to real-time log stream for a task.

        Args:
            task_id: Task ID
            connection_id: WebSocket connection ID

        Returns:
            True if subscribed successfully
        """
        async with self._lock:
            # Get or create log stream
            if task_id not in self.log_streams:
                self.log_streams[task_id] = LogStream(task_id)
                self._stats["active_streams"] = len(self.log_streams)

            stream = self.log_streams[task_id]
            await stream.subscribe(connection_id)
            self._stats["total_subscribers"] = sum(
                s.get_subscriber_count() for s in self.log_streams.values()
            )

        logger.debug(f"Subscribed connection {connection_id} to logs for task {task_id}")
        return True

    async def unsubscribe_from_logs(
        self,
        task_id: str,
        connection_id: str,
    ):
        """Unsubscribe from log stream.

        Args:
            task_id: Task ID
            connection_id: WebSocket connection ID
        """
        async with self._lock:
            stream = self.log_streams.get(task_id)
            if stream:
                await stream.unsubscribe(connection_id)
                self._stats["total_subscribers"] = sum(
                    s.get_subscriber_count() for s in self.log_streams.values()
                )

                # Clean up empty streams
                if stream.get_subscriber_count() == 0:
                    # Keep stream for recent logs but could be cleaned up
                    pass

        logger.debug(f"Unsubscribed connection {connection_id} from logs for task {task_id}")

    async def bulk_create_logs(
        self,
        request: BulkLogRequest,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Create multiple log entries in bulk.

        Args:
            request: Bulk log creation request
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary with creation results
        """
        results = {
            "successful": [],
            "failed": [],
            "total": len(request.logs),
        }

        for log_data in request.logs:
            try:
                log_entry = await self.create_log_entry(log_data, db_session)
                results["successful"].append(str(log_entry.id))
            except Exception as e:
                results["failed.append"]({
                    "task_id": log_data.task_id,
                    "error": str(e),
                })
                logger.error(f"Failed to create log entry: {e}")

        return results

    async def delete_task_logs(
        self,
        task_id: str,
        older_than: Optional[datetime] = None,
        db_session: Optional[Session] = None,
    ) -> int:
        """Delete logs for a specific task.

        Args:
            task_id: Task ID
            older_than: Delete logs older than this timestamp (optional)
            db_session: Database session (overrides instance session)

        Returns:
            Number of logs deleted
        """
        session = db_session or self.db_session
        if not session:
            # Clear from stream
            stream = self.log_streams.get(task_id)
            if stream:
                count = len(stream.logs)
                stream.logs.clear()
                return count
            return 0

        # Build delete query
        query = session.query(TaskLog).filter(TaskLog.task_id == task_id)
        if older_than:
            query = query.filter(TaskLog.timestamp < older_than)

        # Delete
        logs = query.all()
        for log in logs:
            session.delete(log)

        session.commit()

        logger.info(f"Deleted {len(logs)} logs for task {task_id}")
        return len(logs)

    async def get_log_statistics(
        self,
        task_id: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Get log statistics.

        Args:
            task_id: Filter by task ID (optional)
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary containing statistics
        """
        session = db_session or self.db_session
        if not session:
            # Calculate from streams
            if task_id:
                stream = self.log_streams.get(task_id)
                logs = list(stream.logs) if stream else []
            else:
                logs = []
                for stream in self.log_streams.values():
                    logs.extend(stream.logs)

            total = len(logs)
            by_level = defaultdict(int)
            for log in logs:
                by_level[log.level] += 1

            return {
                "total": total,
                "by_level": dict(by_level),
                "active_streams": len(self.log_streams),
                "total_subscribers": sum(
                    s.get_subscriber_count() for s in self.log_streams.values()
                ),
                **dict(self._stats),
            }

        # Query database
        query_builder = session.query(TaskLog)
        if task_id:
            query_builder = query_builder.filter(TaskLog.task_id == task_id)

        total = query_builder.count()

        # Count by level
        level_counts = {}
        for level in LogLevel:
            count = query_builder.filter(TaskLog.level == level).count()
            level_counts[level] = count

        # Get recent activity
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_count = query_builder.filter(TaskLog.timestamp >= recent_cutoff).count()

        return {
            "total": total,
            "by_level": level_counts,
            "recent_24h": recent_count,
            "active_streams": len(self.log_streams),
            "total_subscribers": sum(
                s.get_subscriber_count() for s in self.log_streams.values()
            ),
            **dict(self._stats),
        }

    async def search_logs(
        self,
        query: str,
        task_id: Optional[str] = None,
        level: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 100,
        db_session: Optional[Session] = None,
    ) -> List[TaskLog]:
        """Search logs by text query.

        Args:
            query: Search query
            task_id: Filter by task ID (optional)
            level: Filter by log level (optional)
            date_from: Filter from date (optional)
            date_to: Filter to date (optional)
            limit: Maximum number of results
            db_session: Database session (overrides instance session)

        Returns:
            List of matching TaskLog instances
        """
        log_query = LogQueryParams(
            search=query,
            task_id=task_id,
            level=level,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        return await self.list_logs(log_query, db_session)

    def register_log_handler(self, handler: Callable):
        """Register a log event handler.

        Args:
            handler: Async handler function(event_type, log_entry)
        """
        self.log_handlers.append(handler)

    def unregister_log_handler(self, handler: Callable):
        """Unregister a log event handler.

        Args:
            handler: Handler to remove
        """
        if handler in self.log_handlers:
            self.log_handlers.remove(handler)

    async def _add_to_stream(self, log_entry: TaskLog):
        """Add log entry to stream.

        Args:
            log_entry: TaskLog instance
        """
        async with self._lock:
            task_id = log_entry.task_id

            # Get or create stream
            if task_id not in self.log_streams:
                self.log_streams[task_id] = LogStream(task_id)
                self._stats["active_streams"] = len(self.log_streams)

            stream = self.log_streams[task_id]

        # Add to stream
        await stream.add_log(log_entry)

    async def _call_handlers(self, event_type: str, log_entry: TaskLog):
        """Call registered event handlers.

        Args:
            event_type: Type of event
            log_entry: TaskLog instance
        """
        for handler in self.log_handlers:
            try:
                await handler(event_type, log_entry)
            except Exception as e:
                logger.error(f"Error in log handler: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get log manager statistics.

        Returns:
            Dictionary containing statistics
        """
        return {
            **dict(self._stats),
            "active_streams": len(self.log_streams),
            "total_subscribers": sum(
                s.get_subscriber_count() for s in self.log_streams.values()
            ),
        }

    async def export_logs_to_storage(
        self,
        task_id: Optional[str] = None,
        level: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        format: str = "json",
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Export logs to MinIO storage.

        Args:
            task_id: Filter by task ID (optional)
            level: Filter by log level (optional)
            date_from: Filter from date (optional)
            date_to: Filter to date (optional)
            format: Export format ('json', 'csv', 'txt')
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary with export results
        """
        if not self.storage_manager:
            raise ValueError("Storage manager not configured")

        # Get logs to export
        query = LogQueryParams(
            task_id=task_id,
            level=level,
            date_from=date_from,
            date_to=date_to,
            limit=10000,  # Large limit for export
        )
        logs = await self.list_logs(query, db_session)

        if not logs:
            return {
                "success": False,
                "message": "No logs found for export",
                "file_path": None,
                "size": 0,
            }

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"logs_export_{timestamp}.{format}"
        if task_id:
            filename = f"logs_{task_id}_{timestamp}.{format}"

        # Serialize logs based on format
        if format == "json":
            content = self._serialize_logs_json(logs)
        elif format == "csv":
            content = self._serialize_logs_csv(logs)
        elif format == "txt":
            content = self._serialize_logs_txt(logs)
        else:
            raise ValueError(f"Unsupported export format: {format}")

        # Upload to storage
        try:
            from io import BytesIO
            content_bytes = content.encode('utf-8')

            # Create upload request
            from ..storage.schemas.file_operations import FileUploadRequest
            upload_request = FileUploadRequest(
                skill_id=uuid4(),  # Generate temporary skill ID for logs
                file_path=f"logs/{filename}",
                content=content_bytes,
                metadata={
                    "export_type": "logs",
                    "format": format,
                    "task_id": task_id,
                    "level": level,
                    "date_from": date_from.isoformat() if date_from else None,
                    "date_to": date_to.isoformat() if date_to else None,
                    "log_count": len(logs),
                },
            )

            result = await self.storage_manager.upload_file(upload_request)

            # Update statistics
            self._stats["exported_files"] += 1
            self._stats["total_export_size"] += len(content_bytes)

            return {
                "success": True,
                "message": f"Successfully exported {len(logs)} logs",
                "file_path": result.file_path,
                "size": len(content_bytes),
                "log_count": len(logs),
                "format": format,
            }

        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return {
                "success": False,
                "message": f"Export failed: {str(e)}",
                "file_path": None,
                "size": 0,
            }

    def _serialize_logs_json(self, logs: List[TaskLog]) -> str:
        """Serialize logs to JSON format.

        Args:
            logs: List of TaskLog instances

        Returns:
            JSON string
        """
        import json
        log_data = []
        for log in logs:
            log_data.append({
                "id": str(log.id),
                "task_id": log.task_id,
                "level": log.level,
                "message": log.message,
                "source": log.source,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "context": log.context,
                "stack_trace": log.stack_trace,
                "attachments": log.attachments,
            })
        return json.dumps(log_data, indent=2, ensure_ascii=False)

    def _serialize_logs_csv(self, logs: List[TaskLog]) -> str:
        """Serialize logs to CSV format.

        Args:
            logs: List of TaskLog instances

        Returns:
            CSV string
        """
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "ID", "Task ID", "Level", "Message", "Source",
            "Timestamp", "Context", "Stack Trace"
        ])

        # Write data
        for log in logs:
            writer.writerow([
                str(log.id),
                log.task_id,
                log.level,
                log.message,
                log.source,
                log.timestamp.isoformat() if log.timestamp else "",
                str(log.context),
                log.stack_trace or "",
            ])

        return output.getvalue()

    def _serialize_logs_txt(self, logs: List[TaskLog]) -> str:
        """Serialize logs to plain text format.

        Args:
            logs: List of TaskLog instances

        Returns:
            Plain text string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("LOG EXPORT REPORT")
        lines.append("=" * 80)
        lines.append(f"Total logs: {len(logs)}")
        lines.append(f"Export time: {datetime.utcnow().isoformat()}")
        lines.append("=" * 80)
        lines.append("")

        for log in logs:
            lines.append(f"[{log.timestamp.isoformat() if log.timestamp else 'N/A'}] "
                        f"[{log.level}] [{log.source}] Task: {log.task_id}")
            lines.append(f"Message: {log.message}")
            if log.context:
                lines.append(f"Context: {log.context}")
            if log.stack_trace:
                lines.append(f"Stack: {log.stack_trace}")
            lines.append("-" * 80)

        return "\n".join(lines)

    async def cleanup_old_logs(
        self,
        older_than_days: int = 30,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """Clean up old logs from database and streams.

        Args:
            older_than_days: Delete logs older than this many days
            db_session: Database session (overrides instance session)

        Returns:
            Dictionary with cleanup results
        """
        cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

        session = db_session or self.db_session
        if not session:
            # Clean from streams only
            cleaned_count = 0
            for task_id, stream in list(self.log_streams.items()):
                # Filter out old logs
                old_logs = [log for log in stream.logs
                           if log.timestamp and log.timestamp < cutoff_date]
                if old_logs:
                    # Remove old logs from stream
                    stream.logs = deque(
                        [log for log in stream.logs
                         if log.timestamp and log.timestamp >= cutoff_date],
                        maxlen=stream.max_size
                    )
                    cleaned_count += len(old_logs)

            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        try:
            # Query old logs
            old_logs = session.query(TaskLog).filter(
                TaskLog.timestamp < cutoff_date
            ).all()

            # Delete from database
            for log in old_logs:
                session.delete(log)

            session.commit()

            # Clean from streams
            cleaned_count = 0
            for task_id, stream in list(self.log_streams.items()):
                # Filter out old logs
                old_count = len([log for log in stream.logs
                                if log.timestamp and log.timestamp < cutoff_date])
                if old_count > 0:
                    stream.logs = deque(
                        [log for log in stream.logs
                         if log.timestamp and log.timestamp >= cutoff_date],
                        maxlen=stream.max_size
                    )
                    cleaned_count += old_count

            logger.info(f"Cleaned up {len(old_logs)} old logs from database and {cleaned_count} from streams")

            return {
                "success": True,
                "cleaned_count": len(old_logs),
                "stream_cleaned_count": cleaned_count,
                "cutoff_date": cutoff_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "cleaned_count": 0,
            }


# Global log manager instance
log_manager = LogManager()
