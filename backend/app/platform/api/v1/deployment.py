"""Deployment API routes.

This module provides RESTful API endpoints for deployment operations,
including skill deployment, status tracking, and batch operations.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ...manager import PlatformManager
from ...deployer import DeploymentStatus, DeploymentPriority
from ...schemas.deployment_config import (
    DeploymentCreate,
    DeploymentResponse,
    DeploymentListResponse,
    BatchDeploymentRequest,
    BatchDeploymentResponse,
    DeploymentStatusResponse,
    RetryDeploymentRequest,
    CancelDeploymentRequest
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/deployments", tags=["deployments"])


async def get_platform_manager() -> PlatformManager:
    """Get platform manager instance."""
    # In real implementation, this would be injected
    return PlatformManager()


@router.post(
    "",
    response_model=DeploymentResponse,
    summary="Deploy skill",
    description="Deploy a skill to one or more platforms"
)
async def deploy_skill(
    deployment: DeploymentCreate,
    background_tasks: BackgroundTasks,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Deploy a skill to specified platforms."""
    try:
        # Validate deployment request
        if not deployment.target_platforms:
            raise HTTPException(status_code=400, detail="At least one target platform required")

        # Deploy skill
        result = await manager.deploy_skill(
            skill_data=deployment.skill_data,
            target_platforms=deployment.target_platforms,
            source_format=deployment.source_format,
            target_formats=deployment.target_formats,
            deployment_config=deployment.deployment_config,
            validate_compatibility=deployment.validate_compatibility,
            async_mode=True
        )

        # Convert to response format
        deployment_responses = []
        if isinstance(result, list):
            for task in result:
                deployment_response = DeploymentResponse(
                    deployment_id=task.deployment_id,
                    skill_name=task.skill_data.get("name", "Unknown"),
                    source_format=task.source_format,
                    target_platform=task.target_platform,
                    target_format=task.target_format,
                    status=task.status.value,
                    priority=task.priority.value,
                    created_at=task.created_at.isoformat(),
                    metadata=task.metadata
                )
                deployment_responses.append(deployment_response)
        else:
            # Single deployment result
            deployment_response = DeploymentResponse(
                deployment_id=result.deployment_id,
                skill_name=result.skill_data.get("name", "Unknown"),
                source_format=result.source_format,
                target_platform=result.target_platform,
                target_format=result.target_format,
                status=result.status.value,
                priority=result.priority.value,
                created_at=result.created_at.isoformat(),
                metadata=result.metadata
            )
            deployment_responses.append(deployment_response)

        return DeploymentResponse(
            deployments=deployment_responses,
            total=len(deployment_responses),
            successful=len(deployment_responses),
            failed=0
        )

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")


@router.post(
    "/batch",
    response_model=BatchDeploymentResponse,
    summary="Batch deploy skills",
    description="Deploy multiple skills to platforms in batch"
)
async def batch_deploy_skills(
    request: BatchDeploymentRequest,
    background_tasks: BackgroundTasks,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Deploy multiple skills in batch."""
    try:
        # Prepare batch deployments
        deployments = []
        for deployment_request in request.deployments:
            deployments.append({
                "skill_data": deployment_request.skill_data,
                "target_platform": deployment_request.target_platform,
                "source_format": deployment_request.source_format,
                "target_format": deployment_request.target_format,
                "priority": deployment_request.priority,
                "max_retries": deployment_request.max_retries,
                "deployment_config": deployment_request.deployment_config
            })

        # Perform batch deployment
        results = await manager.deployer.deploy_batch(
            deployments=deployments,
            max_concurrent=request.max_concurrent,
            wait_for_all=request.wait_for_all
        )

        # Process results
        successful_deployments = []
        failed_deployments = []

        for result in results:
            if isinstance(result, dict) and result.get("success", True):
                successful_deployments.append(result)
            else:
                failed_deployments.append(result)

        return BatchDeploymentResponse(
            total=request.total_deployments,
            successful=len(successful_deployments),
            failed=len(failed_deployments),
            deployments=successful_deployments,
            failures=failed_deployments
        )

    except Exception as e:
        logger.error(f"Batch deployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch deployment failed: {str(e)}")


@router.get(
    "/{deployment_id}",
    response_model=DeploymentStatusResponse,
    summary="Get deployment status",
    description="Get the status of a specific deployment"
)
async def get_deployment_status(
    deployment_id: str,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get deployment status."""
    try:
        status = await manager.get_deployment_status(deployment_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Deployment not found: {deployment_id}")

        response = DeploymentStatusResponse(
            deployment_id=status["deployment_id"],
            skill_name=status["skill_name"],
            source_format=status["source_format"],
            target_platform=status["target_platform"],
            target_format=status["target_format"],
            status=status["status"],
            priority=status["priority"],
            retry_count=status["retry_count"],
            max_retries=status["max_retries"],
            created_at=status["created_at"],
            started_at=status["started_at"],
            completed_at=status["completed_at"],
            duration_seconds=status["duration_seconds"],
            error_message=status["error_message"],
            can_retry=status["can_retry"],
            metadata=status["metadata"]
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get deployment status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get(
    "",
    response_model=DeploymentListResponse,
    summary="List deployments",
    description="Get a list of deployments with optional filtering"
)
async def list_deployments(
    status: Optional[str] = Query(None, description="Filter by deployment status"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of deployments"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """List deployments with filtering."""
    try:
        # Get deployments
        deployments = await manager.list_deployments(
            status=status,
            platform=platform,
            limit=limit,
            offset=offset
        )

        # Convert to response format
        deployment_responses = []
        for deployment in deployments:
            response = DeploymentStatusResponse(
                deployment_id=deployment["deployment_id"],
                skill_name=deployment["skill_name"],
                source_format=deployment["source_format"],
                target_platform=deployment["target_platform"],
                target_format=deployment["target_format"],
                status=deployment["status"],
                priority=deployment["priority"],
                retry_count=deployment["retry_count"],
                max_retries=deployment["max_retries"],
                created_at=deployment["created_at"],
                started_at=deployment["started_at"],
                completed_at=deployment["completed_at"],
                duration_seconds=deployment["duration_seconds"],
                error_message=deployment["error_message"],
                can_retry=deployment["can_retry"],
                metadata=deployment["metadata"]
            )
            deployment_responses.append(response)

        return DeploymentListResponse(
            deployments=deployment_responses,
            total=len(deployment_responses),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Failed to list deployments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list deployments: {str(e)}")


@router.post(
    "/{deployment_id}/cancel",
    summary="Cancel deployment",
    description="Cancel a running deployment"
)
async def cancel_deployment(
    deployment_id: str,
    request: CancelDeploymentRequest,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Cancel a deployment."""
    try:
        success = await manager.cancel_deployment(
            deployment_id=deployment_id,
            force=request.force
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to cancel deployment: {deployment_id}"
            )

        return JSONResponse(content={
            "deployment_id": deployment_id,
            "cancelled": True,
            "force": request.force,
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel: {str(e)}")


@router.post(
    "/{deployment_id}/retry",
    response_model=DeploymentResponse,
    summary="Retry deployment",
    description="Retry a failed deployment"
)
async def retry_deployment(
    deployment_id: str,
    request: RetryDeploymentRequest,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Retry a failed deployment."""
    try:
        result = await manager.retry_deployment(
            deployment_id=deployment_id,
            new_config=request.new_config
        )

        if not result:
            raise HTTPException(
                status_code=400,
                detail=f"Deployment cannot be retried: {deployment_id}"
            )

        response = DeploymentResponse(
            deployment_id=result["deployment_id"],
            skill_name=result["skill_name"],
            source_format=result["source_format"],
            target_platform=result["target_platform"],
            target_format=result["target_format"],
            status=result["status"],
            priority=result["priority"],
            created_at=result["created_at"],
            metadata=result["metadata"]
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry deployment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retry: {str(e)}")


@router.get(
    "/statistics",
    summary="Get deployment statistics",
    description="Get deployment statistics and metrics"
)
async def get_deployment_statistics(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get deployment statistics."""
    try:
        stats = manager.deployer.get_statistics()
        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Failed to get deployment statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get(
    "/active/count",
    summary="Get active deployment count",
    description="Get the number of currently active deployments"
)
async def get_active_deployment_count(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get active deployment count."""
    try:
        count = manager.deployer.get_active_deployment_count()
        return JSONResponse(content={
            "active_deployments": count,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get active deployment count: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get count: {str(e)}")


@router.post(
    "/cleanup",
    summary="Cleanup completed deployments",
    description="Clean up completed deployments older than specified hours"
)
async def cleanup_completed_deployments(
    older_than_hours: int = Query(24, ge=1, le=168, description="Remove deployments older than this many hours"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Clean up old completed deployments."""
    try:
        removed_count = await manager.deployer.cleanup_completed_deployments(older_than_hours)

        return JSONResponse(content={
            "removed_deployments": removed_count,
            "older_than_hours": older_than_hours,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to cleanup deployments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get(
    "/queue/size",
    summary="Get deployment queue size",
    description="Get the current deployment queue size"
)
async def get_deployment_queue_size(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get deployment queue size."""
    try:
        queue_size = manager.deployer.get_queue_size()
        return JSONResponse(content={
            "queue_size": queue_size,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get queue size: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get queue size: {str(e)}")


@router.post(
    "/deploy-with-fallback",
    summary="Deploy with fallback strategy",
    description="Deploy skill with automatic fallback to alternative platforms"
)
async def deploy_with_fallback(
    request: Dict[str, Any],  # Using dict for flexibility
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Deploy skill with fallback strategy."""
    try:
        # Validate request
        if "skill_data" not in request:
            raise HTTPException(status_code=400, detail="skill_data is required")
        if "preferred_platforms" not in request:
            raise HTTPException(status_code=400, detail="preferred_platforms is required")

        result = await manager.deploy_with_fallback(
            skill_data=request["skill_data"],
            preferred_platforms=request["preferred_platforms"],
            fallback_platforms=request.get("fallback_platforms"),
            source_format=request.get("source_format"),
            deployment_config=request.get("deployment_config"),
            validate_compatibility=request.get("validate_compatibility", True)
        )

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fallback deployment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fallback deployment failed: {str(e)}")