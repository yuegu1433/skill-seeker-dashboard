"""Progress tracking API routes.

This module provides RESTful API endpoints for task progress tracking,
including progress updates, status management, and statistics.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from ...schemas.progress_operations import (
    CreateTaskProgressRequest,
    UpdateTaskProgressRequest,
    TaskProgressResponse,
    ProgressQueryParams,
    BulkProgressUpdateRequest,
)
from ...schemas.websocket_messages import ProgressUpdateMessage
from ...progress_manager import progress_manager
from ...tracker import tracker
from ...visualization_manager import visualization_manager
from ...log_manager import log_manager

router = APIRouter()


@router.post("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def create_task_progress(
    task_id: str = Path(..., description="Task ID"),
    request: CreateTaskProgressRequest = ...,
    db: Session = Depends(get_db),
):
    """Create or update task progress.

    Args:
        task_id: Task identifier
        request: Progress creation request
        db: Database session

    Returns:
        Created task progress
    """
    try:
        # Validate task_id format
        if not task_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task ID is required"
            )

        # Create progress update
        progress = await progress_manager.update_progress(
            task_id=task_id,
            progress=request.progress,
            status=request.status,
            metadata=request.metadata,
            db_session=db,
        )

        return TaskProgressResponse(
            task_id=progress.task_id,
            progress=progress.progress,
            status=progress.status,
            current_step=progress.current_step,
            total_steps=progress.total_steps,
            estimated_completion=progress.estimated_completion,
            metadata=progress.metadata,
            created_at=progress.created_at,
            updated_at=progress.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create progress: {str(e)}"
        )


@router.get("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def get_task_progress(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
):
    """Get task progress by ID.

    Args:
        task_id: Task identifier
        db: Database session

    Returns:
        Task progress
    """
    try:
        progress = await progress_manager.get_task_progress(task_id, db_session=db)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return TaskProgressResponse(
            task_id=progress.task_id,
            progress=progress.progress,
            status=progress.status,
            current_step=progress.current_step,
            total_steps=progress.total_steps,
            estimated_completion=progress.estimated_completion,
            metadata=progress.metadata,
            created_at=progress.created_at,
            updated_at=progress.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


@router.put("/tasks/{task_id}/progress", response_model=TaskProgressResponse)
async def update_task_progress(
    task_id: str = Path(..., description="Task ID"),
    request: UpdateTaskProgressRequest = ...,
    db: Session = Depends(get_db),
):
    """Update task progress.

    Args:
        task_id: Task identifier
        request: Progress update request
        db: Database session

    Returns:
        Updated task progress
    """
    try:
        progress = await progress_manager.update_progress(
            task_id=task_id,
            progress=request.progress,
            status=request.status,
            current_step=request.current_step,
            total_steps=request.total_steps,
            metadata=request.metadata,
            db_session=db,
        )

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return TaskProgressResponse(
            task_id=progress.task_id,
            progress=progress.progress,
            status=progress.status,
            current_step=progress.current_step,
            total_steps=progress.total_steps,
            estimated_completion=progress.estimated_completion,
            metadata=progress.metadata,
            created_at=progress.created_at,
            updated_at=progress.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update progress: {str(e)}"
        )


@router.get("/progress", response_model=List[TaskProgressResponse])
async def list_task_progress(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """List task progress with optional filtering.

    Args:
        user_id: Filter by user ID
        status: Filter by task status
        task_type: Filter by task type
        limit: Maximum number of results
        offset: Number of results to skip
        db: Database session

    Returns:
        List of task progress
    """
    try:
        query = ProgressQueryParams(
            user_id=user_id,
            status=status,
            task_type=task_type,
            limit=limit,
            offset=offset,
        )

        progress_list = await progress_manager.list_progress(query, db_session=db)

        return [
            TaskProgressResponse(
                task_id=progress.task_id,
                progress=progress.progress,
                status=progress.status,
                current_step=progress.current_step,
                total_steps=progress.total_steps,
                estimated_completion=progress.estimated_completion,
                metadata=progress.metadata,
                created_at=progress.created_at,
                updated_at=progress.updated_at,
            )
            for progress in progress_list
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list progress: {str(e)}"
        )


@router.post("/progress/bulk-update")
async def bulk_update_progress(
    request: BulkProgressUpdateRequest,
    db: Session = Depends(get_db),
):
    """Bulk update multiple task progress.

    Args:
        request: Bulk progress update request
        db: Database session

    Returns:
        Bulk update results
    """
    try:
        results = await progress_manager.bulk_update_progress(
            updates=request.updates,
            db_session=db,
        )

        return {
            "total": len(request.updates),
            "successful": results["successful"],
            "failed": results["failed"],
            "errors": results.get("errors", []),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update progress: {str(e)}"
        )


@router.delete("/tasks/{task_id}/progress")
async def delete_task_progress(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
):
    """Delete task progress.

    Args:
        task_id: Task identifier
        db: Database session

    Returns:
        Deletion confirmation
    """
    try:
        deleted = await progress_manager.delete_progress(task_id, db_session=db)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        return {"message": f"Task progress {task_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete progress: {str(e)}"
        )


@router.get("/tasks/{task_id}/progress/chart")
async def get_progress_chart(
    task_id: str = Path(..., description="Task ID"),
    time_range: Optional[str] = Query("7d", description="Time range (e.g., 1d, 7d, 30d)"),
    aggregation: str = Query("avg", description="Aggregation method"),
    db: Session = Depends(get_db),
):
    """Get progress visualization chart.

    Args:
        task_id: Task identifier
        time_range: Time range for chart data
        aggregation: Aggregation method
        db: Database session

    Returns:
        Progress chart data
    """
    try:
        chart = await visualization_manager.create_progress_chart(
            task_ids=[task_id],
            time_range=time_range,
            aggregation=aggregation,
            db_session=db,
        )

        return {
            "chart_type": chart.chart_type.value,
            "title": chart.title,
            "data": chart.data,
            "metadata": chart.metadata,
            "generated_at": chart.generated_at.isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate chart: {str(e)}"
        )


@router.get("/tasks/{task_id}/status-distribution")
async def get_status_distribution(
    task_id: Optional[str] = Query(None, description="Filter by task ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
):
    """Get task status distribution.

    Args:
        task_id: Filter by task ID
        user_id: Filter by user ID
        db: Database session

    Returns:
        Status distribution data
    """
    try:
        chart = await visualization_manager.create_status_distribution_chart(
            user_id=user_id,
            task_type=None,  # Could be added as parameter
            db_session=db,
        )

        return {
            "chart_type": chart.chart_type.value,
            "title": chart.title,
            "data": chart.data,
            "metadata": chart.metadata,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status distribution: {str(e)}"
        )


@router.get("/statistics")
async def get_progress_statistics(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    time_range: Optional[str] = Query("30d", description="Time range"),
    db: Session = Depends(get_db),
):
    """Get progress statistics.

    Args:
        user_id: Filter by user ID
        task_type: Filter by task type
        time_range: Time range for statistics
        db: Database session

    Returns:
        Progress statistics
    """
    try:
        # Get task statistics
        task_stats = await tracker.get_task_statistics(
            user_id=user_id,
            task_type=task_type,
            db_session=db,
        )

        # Get chart data
        performance_chart = await visualization_manager.create_performance_metrics_chart(
            task_ids=task_stats.get("task_ids", []),
            time_range=time_range,
            db_session=db,
        )

        return {
            "task_statistics": task_stats,
            "performance_metrics": {
                "chart_type": performance_chart.chart_type.value,
                "data": performance_chart.data,
                "metadata": performance_chart.metadata,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/tasks/{task_id}/estimated-completion")
async def get_estimated_completion(
    task_id: str = Path(..., description="Task ID"),
    db: Session = Depends(get_db),
):
    """Get estimated completion time for a task.

    Args:
        task_id: Task identifier
        db: Database session

    Returns:
        Estimated completion data
    """
    try:
        progress = await progress_manager.get_task_progress(task_id, db_session=db)

        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found"
            )

        if not progress.estimated_completion:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No estimated completion time available for task {task_id}"
            )

        return {
            "task_id": task_id,
            "estimated_completion": progress.estimated_completion.isoformat(),
            "current_progress": progress.progress,
            "remaining_progress": 100 - progress.progress,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get estimated completion: {str(e)}"
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
