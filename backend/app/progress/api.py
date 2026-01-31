"""API routes for real-time progress tracking.

This module provides FastAPI route handlers for all progress tracking
operations including tasks, logs, notifications, and visualization.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, Path
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import json
import asyncio

from .schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
    UpdateStatusRequest,
    TaskQueryParams,
    CreateLogEntryRequest,
    LogQueryParams,
    CreateNotificationRequest,
    NotificationQueryParams,
    VisualizationQuery,
    DashboardQuery,
    BulkUpdateRequest,
    BulkLogRequest,
)
from .schemas.websocket_messages import WebSocketMessage
from .progress_manager import progress_manager
from .log_manager import log_manager
from .notification_manager import notification_manager
from .visualization_manager import visualization_manager
from .websocket import websocket_manager
from .utils.validators import ValidationError
from .utils.serializers import serialize_task_progress, serialize_log_entry, serialize_notification

# Create API router
router = APIRouter(prefix="/api/v1/progress", tags=["progress-tracking"])


# ============================================================================
# Task Management Endpoints
# ============================================================================

@router.post("/tasks", response_model=Dict[str, Any])
async def create_task(request: CreateTaskRequest):
    """Create a new task for progress tracking."""
    try:
        task = await progress_manager.create_task(request)
        return {
            "success": True,
            "task": serialize_task_progress(task),
            "message": "Task created successfully",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")


@router.get("/tasks/{task_id}", response_model=Dict[str, Any])
async def get_task(task_id: str = Path(..., description="Task ID")):
    """Get task by ID."""
    try:
        task = await progress_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "success": True,
            "task": serialize_task_progress(task),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task: {str(e)}")


@router.get("/tasks", response_model=Dict[str, Any])
async def list_tasks(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    sort_by: Optional[str] = Query(None, description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    limit: Optional[int] = Query(100, description="Maximum results"),
):
    """List tasks with optional filtering."""
    try:
        query = TaskQueryParams(
            user_id=user_id,
            status=status,
            task_type=task_type,
            search=search,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
        )

        tasks = await progress_manager.list_tasks(query)

        return {
            "success": True,
            "tasks": [serialize_task_progress(task) for task in tasks],
            "total": len(tasks),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tasks: {str(e)}")


@router.patch("/tasks/{task_id}/progress", response_model=Dict[str, Any])
async def update_progress(
    task_id: str,
    request: UpdateProgressRequest,
):
    """Update task progress."""
    try:
        task = await progress_manager.update_progress(
            task_id=task_id,
            progress=request.progress,
            current_step=request.current_step,
            metadata=request.metadata,
        )

        return {
            "success": True,
            "task": serialize_task_progress(task),
            "message": "Progress updated successfully",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update progress: {str(e)}")


@router.patch("/tasks/{task_id}/status", response_model=Dict[str, Any])
async def update_status(
    task_id: str,
    request: UpdateStatusRequest,
):
    """Update task status."""
    try:
        task = await progress_manager.update_status(
            task_id=task_id,
            status=request.status,
            error_message=request.error_message,
            error_details=request.error_details,
            result=request.result,
        )

        return {
            "success": True,
            "task": serialize_task_progress(task),
            "message": "Status updated successfully",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.post("/tasks/{task_id}/complete", response_model=Dict[str, Any])
async def complete_task(
    task_id: str,
    result: Optional[Any] = None,
):
    """Mark task as completed."""
    try:
        task = await progress_manager.complete_task(task_id, result=result)

        return {
            "success": True,
            "task": serialize_task_progress(task),
            "message": "Task completed successfully",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete task: {str(e)}")


@router.post("/tasks/{task_id}/fail", response_model=Dict[str, Any])
async def fail_task(
    task_id: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
):
    """Mark task as failed."""
    try:
        task = await progress_manager.fail_task(task_id, error_message, error_details)

        return {
            "success": True,
            "task": serialize_task_progress(task),
            "message": "Task marked as failed",
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fail task: {str(e)}")


@router.delete("/tasks/{task_id}", response_model=Dict[str, Any])
async def delete_task(task_id: str):
    """Delete a task."""
    try:
        success = await progress_manager.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")

        return {
            "success": True,
            "message": "Task deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.post("/tasks/bulk-update", response_model=Dict[str, Any])
async def bulk_update_tasks(request: BulkUpdateRequest):
    """Bulk update multiple tasks."""
    try:
        results = await progress_manager.bulk_update(request)

        return {
            "success": True,
            "results": results,
            "message": f"Bulk update completed: {len(results['successful'])} successful, {len(results['failed'])} failed",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk update failed: {str(e)}")


@router.get("/tasks/stats", response_model=Dict[str, Any])
async def get_task_stats(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
):
    """Get task statistics."""
    try:
        stats = await progress_manager.get_task_stats(user_id=user_id)

        return {
            "success": True,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


# ============================================================================
# Log Management Endpoints
# ============================================================================

@router.post("/logs", response_model=Dict[str, Any])
async def create_log_entry(request: CreateLogEntryRequest):
    """Create a new log entry."""
    try:
        log_entry = await log_manager.create_log_entry(request)

        return {
            "success": True,
            "log": serialize_log_entry(log_entry),
            "message": "Log entry created successfully",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create log: {str(e)}")


@router.get("/tasks/{task_id}/logs", response_model=Dict[str, Any])
async def get_task_logs(
    task_id: str,
    level: Optional[str] = Query(None, description="Filter by log level"),
    limit: int = Query(100, description="Maximum results"),
):
    """Get logs for a specific task."""
    try:
        logs = await log_manager.get_task_logs(task_id, level=level, limit=limit)

        return {
            "success": True,
            "logs": [serialize_log_entry(log) for log in logs],
            "total": len(logs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@router.get("/logs", response_model=Dict[str, Any])
async def list_logs(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    level: Optional[str] = Query(None, description="Filter by log level"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search in message/source"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(100, description="Maximum results"),
):
    """List logs with optional filtering."""
    try:
        query = LogQueryParams(
            task_id=task_id,
            level=level,
            source=source,
            search=search,
            date_from=date_from,
            date_to=date_to,
            sort_order=sort_order,
            limit=limit,
        )

        logs = await log_manager.list_logs(query)

        return {
            "success": True,
            "logs": [serialize_log_entry(log) for log in logs],
            "total": len(logs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list logs: {str(e)}")


@router.delete("/tasks/{task_id}/logs", response_model=Dict[str, Any])
async def delete_task_logs(
    task_id: str,
    older_than: Optional[str] = Query(None, description="Delete logs older than this date"),
):
    """Delete logs for a specific task."""
    try:
        cutoff = None
        if older_than:
            cutoff = datetime.fromisoformat(older_than)

        count = await log_manager.delete_task_logs(task_id, older_than=cutoff)

        return {
            "success": True,
            "deleted_count": count,
            "message": f"Deleted {count} log entries",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete logs: {str(e)}")


@router.get("/logs/stats", response_model=Dict[str, Any])
async def get_log_stats(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
):
    """Get log statistics."""
    try:
        stats = await log_manager.get_log_statistics(task_id=task_id)

        return {
            "success": True,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get log stats: {str(e)}")


# ============================================================================
# Notification Management Endpoints
# ============================================================================

@router.post("/notifications", response_model=Dict[str, Any])
async def create_notification(request: CreateNotificationRequest):
    """Create a new notification."""
    try:
        notification = await notification_manager.create_notification(request)

        return {
            "success": True,
            "notification": serialize_notification(notification),
            "message": "Notification created successfully",
        }
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notification: {str(e)}")


@router.get("/notifications", response_model=Dict[str, Any])
async def list_notifications(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    notification_type: Optional[str] = Query(None, description="Filter by type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    sort_order: Optional[str] = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(50, description="Maximum results"),
):
    """List notifications with optional filtering."""
    try:
        query = NotificationQueryParams(
            user_id=user_id,
            notification_type=notification_type,
            priority=priority,
            is_read=is_read,
            date_from=date_from,
            date_to=date_to,
            sort_order=sort_order,
            limit=limit,
        )

        notifications = await notification_manager.list_notifications(query)

        return {
            "success": True,
            "notifications": [serialize_notification(n) for n in notifications],
            "total": len(notifications),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list notifications: {str(e)}")


@router.get("/users/{user_id}/notifications", response_model=Dict[str, Any])
async def get_user_notifications(
    user_id: str,
    unread_only: bool = Query(False, description="Only return unread notifications"),
    limit: int = Query(50, description="Maximum results"),
):
    """Get notifications for a specific user."""
    try:
        notifications = await notification_manager.get_user_notifications(
            user_id, unread_only=unread_only, limit=limit
        )

        return {
            "success": True,
            "notifications": [serialize_notification(n) for n in notifications],
            "total": len(notifications),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user notifications: {str(e)}")


@router.patch("/notifications/{notification_id}/read", response_model=Dict[str, Any])
async def mark_notification_read(
    notification_id: str = Path(..., description="Notification ID"),
):
    """Mark notification as read."""
    try:
        success = await notification_manager.mark_as_read(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "success": True,
            "message": "Notification marked as read",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark notification as read: {str(e)}")


@router.post("/users/{user_id}/notifications/read-all", response_model=Dict[str, Any])
async def mark_all_notifications_read(user_id: str):
    """Mark all notifications as read for a user."""
    try:
        count = await notification_manager.mark_all_as_read(user_id)

        return {
            "success": True,
            "marked_count": count,
            "message": f"Marked {count} notifications as read",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark all as read: {str(e)}")


@router.delete("/notifications/{notification_id}", response_model=Dict[str, Any])
async def delete_notification(notification_id: str):
    """Delete a notification."""
    try:
        success = await notification_manager.delete_notification(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="Notification not found")

        return {
            "success": True,
            "message": "Notification deleted successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete notification: {str(e)}")


@router.get("/notifications/stats", response_model=Dict[str, Any])
async def get_notification_stats(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
):
    """Get notification statistics."""
    try:
        stats = await notification_manager.get_notification_statistics(user_id=user_id)

        return {
            "success": True,
            "stats": stats,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get notification stats: {str(e)}")


# ============================================================================
# Visualization Endpoints
# ============================================================================

@router.post("/visualizations/progress-chart", response_model=Dict[str, Any])
async def create_progress_chart(request: Dict[str, Any]):
    """Create progress tracking chart."""
    try:
        query = VisualizationQuery(**request)
        visualization = await visualization_manager.create_progress_chart(
            task_ids=query.task_ids,
            time_range=query.time_range,
            group_by=query.group_by,
            aggregation=query.aggregation,
        )

        return {
            "success": True,
            "visualization": {
                "chart_type": visualization.chart_type.value,
                "title": visualization.title,
                "data": visualization.data,
                "metadata": visualization.metadata,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chart: {str(e)}")


@router.post("/visualizations/status-distribution", response_model=Dict[str, Any])
async def create_status_distribution_chart(request: Dict[str, Any]):
    """Create task status distribution chart."""
    try:
        visualization = await visualization_manager.create_status_distribution_chart(
            user_id=request.get("user_id"),
            task_type=request.get("task_type"),
        )

        return {
            "success": True,
            "visualization": {
                "chart_type": visualization.chart_type.value,
                "title": visualization.title,
                "data": visualization.data,
                "metadata": visualization.metadata,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chart: {str(e)}")


@router.post("/visualizations/performance-metrics", response_model=Dict[str, Any])
async def create_performance_metrics_chart(request: Dict[str, Any]):
    """Create performance metrics chart."""
    try:
        visualization = await visualization_manager.create_performance_metrics_chart(
            task_ids=request["task_ids"],
            time_range=request.get("time_range", "7d"),
        )

        return {
            "success": True,
            "visualization": {
                "chart_type": visualization.chart_type.value,
                "title": visualization.title,
                "data": visualization.data,
                "metadata": visualization.metadata,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create chart: {str(e)}")


@router.post("/visualizations/activity-heatmap", response_model=Dict[str, Any])
async def create_activity_heatmap(request: Dict[str, Any]):
    """Create activity heatmap."""
    try:
        visualization = await visualization_manager.create_activity_heatmap(
            user_id=request.get("user_id"),
            days=request.get("days", 30),
        )

        return {
            "success": True,
            "visualization": {
                "chart_type": visualization.chart_type.value,
                "title": visualization.title,
                "data": visualization.data,
                "metadata": visualization.metadata,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create heatmap: {str(e)}")


@router.post("/visualizations/dashboard", response_model=Dict[str, Any])
async def create_dashboard(request: Dict[str, Any]):
    """Create a dashboard with multiple widgets."""
    try:
        dashboard = await visualization_manager.create_dashboard(
            dashboard_id=request["dashboard_id"],
            title=request["title"],
            widgets=request["widgets"],
        )

        return {
            "success": True,
            "dashboard": dashboard,
            "message": "Dashboard created successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create dashboard: {str(e)}")


@router.get("/visualizations/dashboard/{dashboard_id}", response_model=Dict[str, Any])
async def get_dashboard_data(dashboard_id: str):
    """Get dashboard data for all widgets."""
    try:
        dashboard_data = await visualization_manager.get_dashboard_data(dashboard_id)

        if "error" in dashboard_data:
            raise HTTPException(status_code=404, detail=dashboard_data["error"])

        return {
            "success": True,
            "dashboard": dashboard_data,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")


# ============================================================================
# Statistics Endpoints
# ============================================================================

@router.get("/stats/overview", response_model=Dict[str, Any])
async def get_overall_stats():
    """Get overall system statistics."""
    try:
        task_stats = progress_manager.get_stats()
        log_stats = log_manager.get_stats()
        notification_stats = notification_manager.get_stats()
        visualization_stats = visualization_manager.get_stats()
        websocket_stats = websocket_manager.get_stats()

        return {
            "success": True,
            "stats": {
                "tasks": task_stats,
                "logs": log_stats,
                "notifications": notification_stats,
                "visualizations": visualization_stats,
                "websocket": websocket_stats,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overall stats: {str(e)}")


# ============================================================================
# WebSocket Endpoint
# ============================================================================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    connection_id = None
    try:
        # Extract connection parameters
        task_id = websocket.query_params.get("task_id")
        user_id = websocket.query_params.get("user_id")

        # Connect
        connection_id = await websocket_manager.connect(
            websocket,
            task_id=task_id,
            user_id=user_id,
        )

        if not connection_id:
            await websocket.close(code=1008, reason="Connection rejected")
            return

        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)

                # Process message
                await websocket_manager.handle_message(connection_id, message)

            except json.JSONDecodeError:
                await websocket_manager.send_error(connection_id, "Invalid JSON")
            except Exception as e:
                logger.error(f"WebSocket message error: {e}")
                await websocket_manager.send_error(connection_id, str(e))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if connection_id:
            await websocket_manager.disconnect(connection_id)
