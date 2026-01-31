"""Logs API routes.

This module provides RESTful API endpoints for task log viewing and management,
including log retrieval, filtering, search, and export.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from sqlalchemy.orm import Session

from ...schemas.progress_operations import (
    CreateLogEntryRequest,
    LogQueryParams,
    BulkLogRequest,
    LogEntryResponse,
)
from ...log_manager import log_manager
from ...log_stream import log_stream_service
from ...models.log import LogLevel

router = APIRouter()


@router.post("/tasks/{task_id}/logs", response_model=LogEntryResponse)
async def create_log_entry(
    task_id: str = Path(..., description="Task ID"),
    request: CreateLogEntryRequest = ...,
    db: Session = Depends(get_db),
):
    """Create a new log entry for a task.

    Args:
        task_id: Task identifier
        request: Log entry creation request
        db: Database session

    Returns:
        Created log entry
    """
    try:
        # Ensure task_id matches
        request.task_id = task_id

        log_entry = await log_manager.create_log_entry(
            request=request,
            db_session=db,
        )

        return LogEntryResponse(
            id=str(log_entry.id),
            task_id=log_entry.task_id,
            level=log_entry.level,
            message=log_entry.message,
            source=log_entry.source,
            context=log_entry.context,
            stack_trace=log_entry.stack_trace,
            attachments=log_entry.attachments,
            timestamp=log_entry.timestamp,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create log entry: {str(e)}"
        )


@router.get("/tasks/{task_id}/logs", response_model=List[LogEntryResponse])
async def get_task_logs(
    task_id: str = Path(..., description="Task ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by log source"),
    search: Optional[str] = Query(None, description="Search in log messages"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
):
    """Get logs for a specific task with optional filtering.

    Args:
        task_id: Task identifier
        level: Filter by log level
        source: Filter by log source
        search: Search in log messages
        date_from: Filter from date
        date_to: Filter to date
        limit: Maximum number of results
        offset: Number of results to skip
        sort_order: Sort order
        db: Database session

    Returns:
        List of log entries
    """
    try:
        query = LogQueryParams(
            task_id=task_id,
            level=level,
            source=source,
            search=search,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
            sort_order=sort_order,
        )

        logs = await log_manager.list_logs(query, db_session=db)

        return [
            LogEntryResponse(
                id=str(log.id),
                task_id=log.task_id,
                level=log.level,
                message=log.message,
                source=log.source,
                context=log.context,
                stack_trace=log.stack_trace,
                attachments=log.attachments,
                timestamp=log.timestamp,
            )
            for log in logs
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task logs: {str(e)}"
        )


@router.get("/logs/search", response_model=List[LogEntryResponse])
async def search_logs(
    query: str = Query(..., description="Search query"),
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by log source"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of results"),
    db: Session = Depends(get_db),
):
    """Search logs across all tasks.

    Args:
        query: Search query
        task_id: Filter by task ID
        level: Filter by log level
        source: Filter by log source
        date_from: Filter from date
        date_to: Filter to date
        limit: Maximum number of results
        db: Database session

    Returns:
        List of matching log entries
    """
    try:
        logs = await log_manager.search_logs(
            query=query,
            task_id=task_id,
            level=level,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            db_session=db,
        )

        return [
            LogEntryResponse(
                id=str(log.id),
                task_id=log.task_id,
                level=log.level,
                message=log.message,
                source=log.source,
                context=log.context,
                stack_trace=log.stack_trace,
                attachments=log.attachments,
                timestamp=log.timestamp,
            )
            for log in logs
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search logs: {str(e)}"
        )


@router.post("/logs/bulk", response_model=Dict[str, Any])
async def bulk_create_logs(
    request: BulkLogRequest,
    db: Session = Depends(get_db),
):
    """Create multiple log entries in bulk.

    Args:
        request: Bulk log creation request
        db: Database session

    Returns:
        Bulk creation results
    """
    try:
        results = await log_manager.bulk_create_logs(
            request=request,
            db_session=db,
        )

        return {
            "total": results["total"],
            "successful": len(results["successful"]),
            "failed": len(results["failed"]),
            "successful_ids": results["successful"],
            "failed_entries": results["failed"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create logs: {str(e)}"
        )


@router.get("/logs/statistics")
async def get_log_statistics(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    db: Session = Depends(get_db),
):
    """Get log statistics.

    Args:
        task_id: Filter by task ID
        db: Database session

    Returns:
        Log statistics
    """
    try:
        stats = await log_manager.get_log_statistics(
            task_id=task_id,
            db_session=db,
        )

        return {
            "total_logs": stats["total"],
            "by_level": stats["by_level"],
            "recent_24h": stats.get("recent_24h", 0),
            "active_streams": stats["active_streams"],
            "total_subscribers": stats["total_subscribers"],
            "exported_files": stats.get("exported_files", 0),
            "total_export_size": stats.get("total_export_size", 0),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log statistics: {str(e)}"
        )


@router.delete("/tasks/{task_id}/logs")
async def delete_task_logs(
    task_id: str = Path(..., description="Task ID"),
    older_than: Optional[datetime] = Query(None, description="Delete logs older than this date"),
    db: Session = Depends(get_db),
):
    """Delete logs for a specific task.

    Args:
        task_id: Task identifier
        older_than: Delete logs older than this date
        db: Database session

    Returns:
        Deletion confirmation
    """
    try:
        deleted_count = await log_manager.delete_task_logs(
            task_id=task_id,
            older_than=older_than,
            db_session=db,
        )

        return {
            "message": f"Deleted {deleted_count} logs for task {task_id}",
            "deleted_count": deleted_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete logs: {str(e)}"
        )


@router.post("/logs/export")
async def export_logs(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    format: str = Query("json", description="Export format (json, csv, txt)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """Export logs to storage.

    Args:
        task_id: Filter by task ID
        level: Filter by log level
        date_from: Filter from date
        date_to: Filter to date
        format: Export format
        background_tasks: Background task handler
        db: Database session

    Returns:
        Export task ID for tracking
    """
    try:
        export_result = await log_manager.export_logs_to_storage(
            task_id=task_id,
            level=level,
            date_from=date_from,
            date_to=date_to,
            format=format,
            db_session=db,
        )

        if export_result["success"]:
            return {
                "export_id": export_result["file_path"],
                "status": "completed",
                "file_path": export_result["file_path"],
                "size": export_result["size"],
                "log_count": export_result["log_count"],
                "format": export_result["format"],
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=export_result["message"]
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export logs: {str(e)}"
        )


@router.get("/logs/recent")
async def get_recent_logs(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    db: Session = Depends(get_db),
):
    """Get recent logs across all tasks.

    Args:
        task_id: Filter by task ID
        level: Filter by log level
        limit: Maximum number of results
        db: Database session

    Returns:
        List of recent log entries
    """
    try:
        query = LogQueryParams(
            task_id=task_id,
            level=level,
            limit=limit,
            sort_order="desc",
        )

        logs = await log_manager.list_logs(query, db_session=db)

        return [
            LogEntryResponse(
                id=str(log.id),
                task_id=log.task_id,
                level=log.level,
                message=log.message,
                source=log.source,
                context=log.context,
                stack_trace=log.stack_trace,
                attachments=log.attachments,
                timestamp=log.timestamp,
            )
            for log in logs
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent logs: {str(e)}"
        )


@router.get("/logs/levels")
async def get_log_levels():
    """Get available log levels.

    Returns:
        List of available log levels
    """
    from ...models.log import LogLevel

    return {
        "levels": [level.value for level in LogLevel]
    }


@router.get("/streams/active")
async def get_active_streams():
    """Get information about active log streams.

    Returns:
        Active stream information
    """
    try:
        stats = log_stream_service.get_stats()

        return {
            "active_sessions": stats["active_sessions"],
            "total_sessions": stats["total_sessions"],
            "total_logs_streamed": stats["total_logs_streamed"],
            "session_breakdown": stats["session_breakdown"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active streams: {str(e)}"
        )


# Helper function to get database session
def get_db() -> Session:
    """Get database session.

    This is a placeholder - in a real application, you would use
    a proper database dependency injection system.

    Returns:
        Database session
    """
    # Placeholder implementation
    return None
