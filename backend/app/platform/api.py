"""Platform API routes.

This module defines FastAPI routes for platform operations including
platform management, deployment, and compatibility checks.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    status,
    BackgroundTasks,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .managers import (
    PlatformManager,
    DeploymentManager,
    CompatibilityManager,
)
from .schemas.platform_operations import (
    PlatformCreateRequest,
    PlatformUpdateRequest,
    PlatformListRequest,
    PlatformHealthCheckRequest,
    PlatformResponse,
    DeploymentCreateRequest,
    DeploymentUpdateRequest,
    DeploymentListRequest,
    DeploymentRetryRequest,
    DeploymentResponse,
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
    CompatibilitySummary,
)
from .schemas.notification_config import (
    NotificationDeliveryRequest,
    NotificationDeliveryResponse,
)
from .schemas.websocket_messages import (
    ConnectionRequest,
    ConnectionResponse,
)
from ..database import get_db_session


# Create router
router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


# Dependency to get database session
def get_db() -> Session:
    """Get database session."""
    return next(get_db_session())


# Dependency to get managers
def get_platform_manager(db: Session = Depends(get_db)) -> PlatformManager:
    """Get PlatformManager instance."""
    return PlatformManager(db)


def get_deployment_manager(db: Session = Depends(get_db)) -> DeploymentManager:
    """Get DeploymentManager instance."""
    return DeploymentManager(db)


def get_compatibility_manager(db: Session = Depends(get_db)) -> CompatibilityManager:
    """Get CompatibilityManager instance."""
    return CompatibilityManager(db)


# Platform Management Endpoints
@router.post(
    "/platforms",
    response_model=PlatformResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Platform",
    description="Create a new LLM platform configuration",
)
async def create_platform(
    request: PlatformCreateRequest,
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Create a new platform."""
    try:
        platform = await platform_manager.create_platform(request)
        return PlatformResponse.from_model(platform)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create platform: {str(e)}"
        )


@router.get(
    "/platforms/{platform_id}",
    response_model=PlatformResponse,
    summary="Get Platform",
    description="Get platform by ID",
)
async def get_platform(
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Get platform by ID."""
    platform = await platform_manager.get_platform(platform_id)
    if not platform:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Platform not found: {platform_id}"
        )
    return PlatformResponse.from_model(platform)


@router.get(
    "/platforms",
    summary="List Platforms",
    description="List platforms with filtering and pagination",
)
async def list_platforms(
    platform_type: Optional[str] = Query(None, description="Filter by platform type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_healthy: Optional[bool] = Query(None, description="Filter by health status"),
    search: Optional[str] = Query(None, description="Search in name or display name"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """List platforms."""
    try:
        request = PlatformListRequest(
            platform_type=platform_type,
            is_active=is_active,
            is_healthy=is_healthy,
            search=search,
            skip=skip,
            limit=limit,
        )
        result = await platform_manager.list_platforms(request)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list platforms: {str(e)}"
        )


@router.patch(
    "/platforms/{platform_id}",
    response_model=PlatformResponse,
    summary="Update Platform",
    description="Update platform configuration",
)
async def update_platform(
    request: PlatformUpdateRequest,
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Update platform."""
    try:
        platform = await platform_manager.update_platform(platform_id, request)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform not found: {platform_id}"
            )
        return PlatformResponse.from_model(platform)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update platform: {str(e)}"
        )


@router.delete(
    "/platforms/{platform_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Platform",
    description="Delete platform",
)
async def delete_platform(
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Delete platform."""
    try:
        deleted = await platform_manager.delete_platform(platform_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform not found: {platform_id}"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete platform: {str(e)}"
        )


@router.post(
    "/platforms/{platform_id}/health-check",
    summary="Check Platform Health",
    description="Perform health check on platform",
)
async def check_platform_health(
    request: PlatformHealthCheckRequest,
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Check platform health."""
    try:
        result = await platform_manager.check_platform_health(platform_id, request)
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.post(
    "/platforms/health-check-all",
    summary="Check All Platforms Health",
    description="Perform health check on all active platforms",
)
async def check_all_platforms_health(
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Check all platforms health."""
    try:
        results = await platform_manager.check_all_platforms_health()
        return JSONResponse(content={"results": results})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get(
    "/platforms/{platform_id}/activate",
    response_model=PlatformResponse,
    summary="Activate Platform",
    description="Activate a platform",
)
async def activate_platform(
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Activate platform."""
    try:
        platform = await platform_manager.activate_platform(platform_id)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform not found: {platform_id}"
            )
        return PlatformResponse.from_model(platform)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate platform: {str(e)}"
        )


@router.get(
    "/platforms/{platform_id}/deactivate",
    response_model=PlatformResponse,
    summary="Deactivate Platform",
    description="Deactivate a platform",
)
async def deactivate_platform(
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Deactivate platform."""
    try:
        platform = await platform_manager.deactivate_platform(platform_id)
        if not platform:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Platform not found: {platform_id}"
            )
        return PlatformResponse.from_model(platform)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate platform: {str(e)}"
        )


@router.get(
    "/statistics",
    summary="Get Platform Statistics",
    description="Get platform statistics",
)
async def get_platform_statistics(
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Get platform statistics."""
    try:
        statistics = await platform_manager.get_platform_statistics()
        return JSONResponse(content=statistics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get(
    "/platforms/{platform_id}/statistics",
    summary="Get Platform Usage Statistics",
    description="Get platform usage statistics",
)
async def get_platform_usage_statistics(
    platform_id: UUID = Path(..., description="Platform ID"),
    platform_manager: PlatformManager = Depends(get_platform_manager),
):
    """Get platform usage statistics."""
    try:
        statistics = await platform_manager.get_platform_usage_stats(platform_id)
        return JSONResponse(content=statistics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get usage statistics: {str(e)}"
        )


# Deployment Endpoints
@router.post(
    "/deployments",
    response_model=DeploymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Deployment",
    description="Create a new skill deployment",
)
async def create_deployment(
    request: DeploymentCreateRequest,
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Create deployment."""
    try:
        deployment = await deployment_manager.create_deployment(request)
        return DeploymentResponse.from_model(deployment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deployment: {str(e)}"
        )


@router.get(
    "/deployments/{deployment_id}",
    response_model=DeploymentResponse,
    summary="Get Deployment",
    description="Get deployment by ID",
)
async def get_deployment(
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Get deployment."""
    deployment = await deployment_manager.get_deployment(deployment_id)
    if not deployment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deployment not found: {deployment_id}"
        )
    return DeploymentResponse.from_model(deployment)


@router.get(
    "/deployments",
    summary="List Deployments",
    description="List deployments with filtering and pagination",
)
async def list_deployments(
    platform_id: Optional[UUID] = Query(None, description="Filter by platform ID"),
    skill_id: Optional[str] = Query(None, description="Filter by skill ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """List deployments."""
    try:
        request = DeploymentListRequest(
            platform_id=str(platform_id) if platform_id else None,
            skill_id=skill_id,
            status=status,
            success=success,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit,
        )
        result = await deployment_manager.list_deployments(request)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list deployments: {str(e)}"
        )


@router.post(
    "/deployments/{deployment_id}/start",
    response_model=DeploymentResponse,
    summary="Start Deployment",
    description="Start a deployment",
)
async def start_deployment(
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Start deployment."""
    try:
        deployment = await deployment_manager.start_deployment(deployment_id)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        return DeploymentResponse.from_model(deployment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start deployment: {str(e)}"
        )


@router.post(
    "/deployments/{deployment_id}/complete",
    response_model=DeploymentResponse,
    summary="Complete Deployment",
    description="Mark deployment as completed",
)
async def complete_deployment(
    success: bool = Query(..., description="Whether deployment was successful"),
    platform_response: Optional[Dict[str, Any]] = Query(None, description="Platform response data"),
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Complete deployment."""
    try:
        deployment = await deployment_manager.complete_deployment(
            deployment_id,
            success,
            platform_response
        )
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        return DeploymentResponse.from_model(deployment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete deployment: {str(e)}"
        )


@router.post(
    "/deployments/{deployment_id}/fail",
    response_model=DeploymentResponse,
    summary="Fail Deployment",
    description="Mark deployment as failed",
)
async def fail_deployment(
    error_message: str = Query(..., description="Error message"),
    error_details: Optional[Dict[str, Any]] = Query(None, description="Additional error details"),
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Fail deployment."""
    try:
        deployment = await deployment_manager.fail_deployment(
            deployment_id,
            error_message,
            error_details
        )
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        return DeploymentResponse.from_model(deployment)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fail deployment: {str(e)}"
        )


@router.post(
    "/deployments/{deployment_id}/cancel",
    response_model=DeploymentResponse,
    summary="Cancel Deployment",
    description="Cancel a deployment",
)
async def cancel_deployment(
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Cancel deployment."""
    try:
        deployment = await deployment_manager.cancel_deployment(deployment_id)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        return DeploymentResponse.from_model(deployment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel deployment: {str(e)}"
        )


@router.post(
    "/deployments/{deployment_id}/retry",
    response_model=DeploymentResponse,
    summary="Retry Deployment",
    description="Retry a failed deployment",
)
async def retry_deployment(
    request: DeploymentRetryRequest,
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Retry deployment."""
    try:
        deployment = await deployment_manager.retry_deployment(deployment_id, request)
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        return DeploymentResponse.from_model(deployment)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry deployment: {str(e)}"
        )


@router.get(
    "/deployments/{deployment_id}/progress",
    summary="Get Deployment Progress",
    description="Get deployment progress information",
)
async def get_deployment_progress(
    deployment_id: UUID = Path(..., description="Deployment ID"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Get deployment progress."""
    try:
        progress = await deployment_manager.get_deployment_progress(deployment_id)
        if not progress:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Deployment not found: {deployment_id}"
            )
        return JSONResponse(content=progress)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get progress: {str(e)}"
        )


@router.get(
    "/deployments/statistics",
    summary="Get Deployment Statistics",
    description="Get deployment statistics",
)
async def get_deployment_statistics(
    platform_id: Optional[UUID] = Query(None, description="Filter by platform ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Get deployment statistics."""
    try:
        statistics = await deployment_manager.get_deployment_statistics(
            str(platform_id) if platform_id else None,
            date_from,
            date_to,
        )
        return JSONResponse(content=statistics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.post(
    "/deployments/bulk-create",
    summary="Bulk Create Deployments",
    description="Create multiple deployments",
)
async def bulk_create_deployments(
    requests: List[DeploymentCreateRequest],
    parallel: bool = Query(True, description="Execute in parallel"),
    deployment_manager: DeploymentManager = Depends(get_deployment_manager),
):
    """Bulk create deployments."""
    try:
        deployments = await deployment_manager.bulk_create_deployments(requests, parallel)
        result = {
            "created": [DeploymentResponse.from_model(d) for d in deployments if d],
            "total": len(requests),
            "successful": len(deployments),
        }
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create deployments: {str(e)}"
        )


# Compatibility Check Endpoints
@router.post(
    "/compatibility-checks",
    response_model=CompatibilityCheckResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Compatibility Check",
    description="Create a new compatibility check",
)
async def create_compatibility_check(
    request: CompatibilityCheckRequest,
    skill_data: Optional[Dict[str, Any]] = Query(None, description="Skill data for analysis"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Create compatibility check."""
    try:
        # Perform check in background for better performance
        background_tasks.add_task(
            compatibility_manager.perform_compatibility_check,
            request,
            skill_data
        )

        # Return immediate response
        compatibility_check = await compatibility_manager.create_compatibility_check(request)
        return CompatibilityCheckResponse.from_model(compatibility_check)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create compatibility check: {str(e)}"
        )


@router.get(
    "/compatibility-checks/{check_id}",
    response_model=CompatibilityCheckResponse,
    summary="Get Compatibility Check",
    description="Get compatibility check by ID",
)
async def get_compatibility_check(
    check_id: str = Path(..., description="Compatibility check ID"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Get compatibility check."""
    compatibility_check = await compatibility_manager.get_compatibility_check(check_id)
    if not compatibility_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Compatibility check not found: {check_id}"
        )
    return CompatibilityCheckResponse.from_model(compatibility_check)


@router.get(
    "/compatibility-checks",
    summary="List Compatibility Checks",
    description="List compatibility checks with filtering",
)
async def list_compatibility_checks(
    skill_id: Optional[str] = Query(None, description="Filter by skill ID"),
    overall_compatible: Optional[bool] = Query(None, description="Filter by compatibility"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """List compatibility checks."""
    try:
        result = await compatibility_manager.list_compatibility_checks(
            skill_id,
            overall_compatible,
            None,  # platforms_checked
            skip,
            limit,
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list compatibility checks: {str(e)}"
        )


@router.get(
    "/compatibility-checks/skill/{skill_id}/latest",
    response_model=CompatibilityCheckResponse,
    summary="Get Latest Compatibility Check",
    description="Get latest compatibility check for a skill",
)
async def get_latest_compatibility_check(
    skill_id: str = Path(..., description="Skill ID"),
    platforms: Optional[str] = Query(None, description="Comma-separated platform names"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Get latest compatibility check."""
    platform_list = platforms.split(",") if platforms else None
    compatibility_check = await compatibility_manager.get_latest_compatibility_check(
        skill_id,
        platform_list
    )
    if not compatibility_check:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compatibility check found for skill: {skill_id}"
        )
    return CompatibilityCheckResponse.from_model(compatibility_check)


@router.get(
    "/compatibility-checks/skill/{skill_id}/summary",
    response_model=CompatibilitySummary,
    summary="Get Compatibility Summary",
    description="Get compatibility summary for a skill",
)
async def get_compatibility_summary(
    skill_id: str = Path(..., description="Skill ID"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Get compatibility summary."""
    summary = await compatibility_manager.get_compatibility_summary(skill_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No compatibility check found for skill: {skill_id}"
        )
    return summary


@router.get(
    "/compatibility-checks/statistics",
    summary="Get Compatibility Statistics",
    description="Get compatibility check statistics",
)
async def get_compatibility_statistics(
    skill_id: Optional[str] = Query(None, description="Filter by skill ID"),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Get compatibility statistics."""
    try:
        statistics = await compatibility_manager.get_compatibility_statistics(
            skill_id,
            date_from,
            date_to,
        )
        return JSONResponse(content=statistics)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get(
    "/compatibility-checks/{check_id}/issues/{severity}",
    summary="Get Issues by Severity",
    description="Get issues by severity for a compatibility check",
)
async def get_issues_by_severity(
    check_id: str = Path(..., description="Compatibility check ID"),
    severity: str = Path(..., description="Severity level"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Get issues by severity."""
    try:
        issues = await compatibility_manager.get_issues_by_severity(check_id, severity)
        return JSONResponse(content={"issues": issues})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get issues: {str(e)}"
        )


@router.get(
    "/compatibility-checks/{check_id}/issues/platform/{platform_name}",
    summary="Get Issues by Platform",
    description="Get issues by platform for a compatibility check",
)
async def get_issues_by_platform(
    check_id: str = Path(..., description="Compatibility check ID"),
    platform_name: str = Path(..., description="Platform name"),
    compatibility_manager: CompatibilityManager = Depends(get_compatibility_manager),
):
    """Get issues by platform."""
    try:
        issues = await compatibility_manager.get_issues_by_platform(check_id, platform_name)
        return JSONResponse(content={"issues": issues})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get issues: {str(e)}"
        )