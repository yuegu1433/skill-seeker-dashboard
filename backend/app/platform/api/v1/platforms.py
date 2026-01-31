"""Platform management API routes.

This module provides RESTful API endpoints for platform management,
including platform CRUD operations, health checks, and statistics.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ...manager import PlatformManager
from ...schemas.platform_operations import (
    PlatformCreate,
    PlatformUpdate,
    PlatformResponse,
    PlatformListResponse,
    HealthCheckResponse,
    StatisticsResponse,
    PlatformFilter
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/platforms", tags=["platforms"])


async def get_platform_manager() -> PlatformManager:
    """Get platform manager instance."""
    # In real implementation, this would be injected
    return PlatformManager()


@router.get(
    "",
    response_model=PlatformListResponse,
    summary="List all platforms",
    description="Get a list of all registered platforms with optional filtering"
)
async def list_platforms(
    filter: PlatformFilter = Depends(),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """List all platforms with optional filtering."""
    try:
        # Get platform health status
        health_status = await manager.get_platform_health()

        # Convert to response format
        platforms = []
        for platform_id, snapshot in health_status.items():
            platform_data = {
                "platform_id": platform_id,
                "status": snapshot.status.value,
                "last_check": snapshot.last_check.isoformat(),
                "is_healthy": snapshot.is_healthy,
                "health_checks": [
                    {
                        "name": check.status.value,
                        "message": check.message,
                        "response_time_ms": check.response_time_ms
                    }
                    for check in snapshot.health_checks
                ]
            }

            # Apply filters
            if filter.status and snapshot.status.value != filter.status:
                continue
            if filter.healthy_only and not snapshot.is_healthy:
                continue
            if filter.platform_id and platform_id != filter.platform_id:
                continue

            platforms.append(platform_data)

        return PlatformListResponse(
            platforms=platforms,
            total=len(platforms),
            filtered=len(platforms)
        )

    except Exception as e:
        logger.error(f"Failed to list platforms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list platforms: {str(e)}")


@router.get(
    "/{platform_id}",
    response_model=PlatformResponse,
    summary="Get platform details",
    description="Get detailed information about a specific platform"
)
async def get_platform(
    platform_id: str,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get platform details."""
    try:
        # Get platform health status
        health_status = await manager.get_platform_health()

        if platform_id not in health_status:
            raise HTTPException(status_code=404, detail=f"Platform not found: {platform_id}")

        snapshot = health_status[platform_id]

        platform_response = PlatformResponse(
            platform_id=platform_id,
            status=snapshot.status.value,
            last_check=snapshot.last_check.isoformat(),
            is_healthy=snapshot.is_healthy,
            consecutive_failures=snapshot.consecutive_failures,
            health_checks=[
                {
                    "name": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "details": check.details
                }
                for check in snapshot.health_checks
            ],
            metadata=snapshot.metrics
        )

        return platform_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get platform {platform_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get platform: {str(e)}")


@router.post(
    "/{platform_id}/health-check",
    response_model=HealthCheckResponse,
    summary="Trigger health check",
    description="Manually trigger a health check for a specific platform"
)
async def trigger_health_check(
    platform_id: str,
    background_tasks: BackgroundTasks,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Trigger health check for a platform."""
    try:
        # Perform health check
        snapshot = await manager.monitor.check_platform_health(platform_id)

        response = HealthCheckResponse(
            platform_id=platform_id,
            status=snapshot.status.value,
            healthy=snapshot.is_healthy,
            last_check=snapshot.last_check.isoformat(),
            response_time_ms=sum(
                check.response_time_ms for check in snapshot.health_checks
            ),
            checks=[
                {
                    "name": check.status.value,
                    "message": check.message,
                    "response_time_ms": check.response_time_ms,
                    "passed": check.status.value in ["pass", "warn"]
                }
                for check in snapshot.health_checks
            ]
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed for {platform_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get(
    "/health-check/all",
    response_model=List[HealthCheckResponse],
    summary="Check all platforms health",
    description="Perform health checks on all registered platforms"
)
async def check_all_platforms_health(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Check health of all platforms."""
    try:
        health_status = await manager.get_platform_health()

        responses = []
        for platform_id, snapshot in health_status.items():
            response = HealthCheckResponse(
                platform_id=platform_id,
                status=snapshot.status.value,
                healthy=snapshot.is_healthy,
                last_check=snapshot.last_check.isoformat(),
                response_time_ms=sum(
                    check.response_time_ms for check in snapshot.health_checks
                ),
                checks=[
                    {
                        "name": check.status.value,
                        "message": check.message,
                        "response_time_ms": check.response_time_ms,
                        "passed": check.status.value in ["pass", "warn"]
                    }
                    for check in snapshot.health_checks
                ]
            )
            responses.append(response)

        return responses

    except Exception as e:
        logger.error(f"Failed to check all platforms health: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Get platform statistics",
    description="Get comprehensive platform statistics and metrics"
)
async def get_platform_statistics(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get platform statistics."""
    try:
        # Get statistics from manager
        stats = manager.get_statistics()
        summary = await manager.get_platform_summary()

        response = StatisticsResponse(
            platforms=summary["platforms"],
            deployments=summary["deployments"],
            alerts=summary["alerts"],
            timestamp=datetime.utcnow().isoformat(),
            details=stats
        )

        return response

    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get(
    "/summary",
    summary="Get platform summary",
    description="Get a summary of all platforms status and activity"
)
async def get_platform_summary(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get platform summary."""
    try:
        summary = await manager.get_platform_summary()
        return JSONResponse(content=summary)

    except Exception as e:
        logger.error(f"Failed to get summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get(
    "/{platform_id}/capabilities",
    summary="Get platform capabilities",
    description="Get capabilities and supported features of a platform"
)
async def get_platform_capabilities(
    platform_id: str,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get platform capabilities."""
    try:
        # Get platform health status
        health_status = await manager.get_platform_health()

        if platform_id not in health_status:
            raise HTTPException(status_code=404, detail=f"Platform not found: {platform_id}")

        snapshot = health_status[platform_id]

        # Extract capabilities from health checks metadata
        capabilities = {}
        for check in snapshot.health_checks:
            if "supported_formats" in check.details:
                capabilities["supported_formats"] = check.details["supported_formats"]
            if "features" in check.details:
                capabilities["features"] = check.details["features"]

        return JSONResponse(content={
            "platform_id": platform_id,
            "capabilities": capabilities,
            "status": snapshot.status.value,
            "last_check": snapshot.last_check.isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get capabilities for {platform_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get capabilities: {str(e)}")


@router.get(
    "/alerts/active",
    summary="Get active alerts",
    description="Get all active alerts across platforms"
)
async def get_active_alerts(
    platform_id: Optional[str] = Query(None, description="Filter by platform ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get active alerts."""
    try:
        alerts = manager.monitor.get_active_alerts(platform_id=platform_id)

        # Apply limit
        alerts = alerts[:limit]

        alert_responses = []
        for alert in alerts:
            alert_response = {
                "alert_id": alert.alert_id,
                "platform_id": alert.platform_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat(),
                "acknowledged": alert.acknowledged,
                "is_active": alert.is_active
            }
            alert_responses.append(alert_response)

        return JSONResponse(content={
            "alerts": alert_responses,
            "total": len(alert_responses),
            "filtered_by": platform_id
        })

    except Exception as e:
        logger.error(f"Failed to get active alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.post(
    "/alerts/{alert_id}/acknowledge",
    summary="Acknowledge alert",
    description="Acknowledge an active alert"
)
async def acknowledge_alert(
    alert_id: str,
    user: str = Query(..., description="User acknowledging the alert"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Acknowledge an alert."""
    try:
        success = manager.monitor.acknowledge_alert(alert_id, user)

        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return JSONResponse(content={
            "alert_id": alert_id,
            "acknowledged": True,
            "acknowledged_by": user,
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.post(
    "/alerts/{alert_id}/resolve",
    summary="Resolve alert",
    description="Resolve an active alert"
)
async def resolve_alert(
    alert_id: str,
    user: str = Query(..., description="User resolving the alert"),
    notes: Optional[str] = Query(None, description="Resolution notes"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Resolve an alert."""
    try:
        success = manager.monitor.resolve_alert(alert_id, user, notes)

        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return JSONResponse(content={
            "alert_id": alert_id,
            "resolved": True,
            "resolved_by": user,
            "resolution_notes": notes,
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


@router.get(
    "/health",
    summary="Overall health check",
    description="Check overall health of the platform management system"
)
async def overall_health_check(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Overall health check."""
    try:
        health_result = await manager.health_check()
        return JSONResponse(content=health_result)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )