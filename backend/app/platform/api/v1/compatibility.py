"""Compatibility validation API routes.

This module provides RESTful API endpoints for compatibility validation,
including skill validation, compatibility reports, and batch validation.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from ...manager import PlatformManager
from ...schemas.platform_operations import (
    CompatibilityValidationRequest,
    CompatibilityValidationResponse,
    CompatibilityReport,
    BatchCompatibilityRequest,
    BatchCompatibilityResponse,
    ValidationResult
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/compatibility", tags=["compatibility"])


async def get_platform_manager() -> PlatformManager:
    """Get platform manager instance."""
    # In real implementation, this would be injected
    return PlatformManager()


@router.post(
    "/validate",
    response_model=CompatibilityValidationResponse,
    summary="Validate skill compatibility",
    description="Validate a skill's compatibility across multiple platforms"
)
async def validate_skill_compatibility(
    request: CompatibilityValidationRequest,
    background_tasks: BackgroundTasks,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Validate skill compatibility across platforms."""
    try:
        # Perform validation
        report = await manager.validate_skill_compatibility(
            skill_data=request.skill_data,
            target_platforms=request.target_platforms,
            validation_config=request.validation_config
        )

        # Convert platform results to response format
        platform_results = []
        for platform_id, result in report["platform_results"].items():
            platform_result = {
                "platform_id": platform_id,
                "valid": result.valid,
                "error_count": len(result.issues),
                "warning_count": len(result.warnings),
                "info_count": len(result.info),
                "validation_time": result.validation_time,
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "type": issue.type.value,
                        "message": issue.message,
                        "platform": issue.platform,
                        "field": issue.field,
                        "suggestion": issue.suggestion
                    }
                    for issue in result.issues
                ],
                "warnings": [
                    {
                        "severity": warning.severity.value,
                        "type": warning.type.value,
                        "message": warning.message,
                        "platform": warning.platform,
                        "field": warning.field
                    }
                    for warning in result.warnings
                ]
            }
            platform_results.append(platform_result)

        # Convert recommendations
        recommendations = []
        for rec in report.get("recommendations", []):
            recommendation = {
                "type": rec.get("type"),
                "priority": rec.get("priority"),
                "description": rec.get("description"),
                "affected_platforms": rec.get("affected_platforms", []),
                "field": rec.get("field"),
                "action": rec.get("action")
            }
            recommendations.append(recommendation)

        response = CompatibilityValidationResponse(
            overall_compatible=report["overall_compatible"],
            compatibility_score=report["compatibility_score"],
            compatible_platforms=report["compatible_platforms"],
            incompatible_platforms=report["incompatible_platforms"],
            platform_count=report["platform_count"],
            compatible_count=report["compatible_count"],
            incompatible_count=report["incompatible_count"],
            validation_time=report["validation_time"],
            timestamp=report["timestamp"],
            platform_results=platform_results,
            recommendations=recommendations,
            detailed_report=report.get("detailed_report")
        )

        return response

    except Exception as e:
        logger.error(f"Compatibility validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.post(
    "/validate/batch",
    response_model=BatchCompatibilityResponse,
    summary="Batch validate skills compatibility",
    description="Validate multiple skills compatibility across platforms"
)
async def batch_validate_compatibility(
    request: BatchCompatibilityRequest,
    background_tasks: BackgroundTasks,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Batch validate skills compatibility."""
    try:
        # Perform batch validation
        results = await manager.validator.validate_batch_compatibility(
            skills_data=[item.skill_data for item in request.skills_data],
            target_platforms=request.target_platforms,
            max_concurrent=request.max_concurrent
        )

        # Process results
        successful_validations = []
        failed_validations = []

        for i, result in enumerate(results):
            if isinstance(result, dict) and result.get("success", True):
                successful_validations.append(result)
            else:
                failed_validations.append({
                    "index": i,
                    "error": result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                })

        return BatchCompatibilityResponse(
            total=request.total_skills,
            successful=len(successful_validations),
            failed=len(failed_validations),
            validations=successful_validations,
            failures=failed_validations
        )

    except Exception as e:
        logger.error(f"Batch validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch validation failed: {str(e)}")


@router.get(
    "/report/{validation_id}",
    summary="Get compatibility report",
    description="Get a detailed compatibility validation report"
)
async def get_compatibility_report(
    validation_id: str,
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get compatibility report (placeholder - would need validation storage in real implementation)."""
    try:
        # In real implementation, this would retrieve a stored report
        # For now, return a placeholder response
        return JSONResponse(content={
            "validation_id": validation_id,
            "message": "Compatibility report storage not yet implemented",
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get compatibility report: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.post(
    "/check-format",
    response_model=ValidationResult,
    summary="Check format compatibility",
    description="Check if a skill format is compatible with specific platforms"
)
async def check_format_compatibility(
    skill_data: Dict[str, Any],
    source_format: str = Query(..., description="Source format"),
    target_platforms: List[str] = Query(..., description="Target platforms"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Check format compatibility."""
    try:
        # Validate format compatibility using converter
        validation_results = []

        for platform in target_platforms:
            # Check if format is supported by platform
            platform_health = await manager.get_platform_health()

            if platform not in platform_health:
                validation_results.append({
                    "platform_id": platform,
                    "compatible": False,
                    "reason": "Platform not found or not registered"
                })
                continue

            # Check supported formats (this would come from adapter capabilities)
            # For now, return a basic compatibility check
            validation_results.append({
                "platform_id": platform,
                "compatible": True,
                "reason": "Format appears compatible"
            })

        # Determine overall compatibility
        all_compatible = all(result["compatible"] for result in validation_results)

        response = ValidationResult(
            compatible=all_compatible,
            source_format=source_format,
            target_platforms=target_platforms,
            validation_results=validation_results,
            timestamp=datetime.utcnow().isoformat()
        )

        return response

    except Exception as e:
        logger.error(f"Format compatibility check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Format check failed: {str(e)}")


@router.get(
    "/supported-platforms",
    summary="Get supported platforms",
    description="Get list of platforms that support a specific format"
)
async def get_supported_platforms(
    format: str = Query(..., description="Format to check"),
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get platforms that support a specific format."""
    try:
        # Get platform health to see available platforms
        health_status = await manager.get_platform_health()

        # Get supported formats from converter
        supported_formats = manager.converter.get_supported_formats()

        # Filter platforms based on format support
        # In real implementation, this would check each adapter's supported_formats
        compatible_platforms = []
        for platform_id in health_status.keys():
            # Basic check - in reality would query adapter capabilities
            if format in ["json", "yaml", "markdown"]:
                compatible_platforms.append(platform_id)

        return JSONResponse(content={
            "format": format,
            "supported_platforms": compatible_platforms,
            "total_platforms": len(health_status),
            "compatibility_rate": len(compatible_platforms) / len(health_status) * 100 if health_status else 0,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get supported platforms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported platforms: {str(e)}")


@router.get(
    "/statistics",
    summary="Get compatibility validation statistics",
    description="Get statistics about compatibility validations"
)
async def get_compatibility_statistics(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get compatibility validation statistics."""
    try:
        stats = manager.validator.get_validation_statistics()
        return JSONResponse(content=stats)

    except Exception as e:
        logger.error(f"Failed to get compatibility statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.post(
    "/recommendations",
    summary="Get compatibility recommendations",
    description="Get recommendations for improving skill compatibility"
)
async def get_compatibility_recommendations(
    request: Dict[str, Any],  # Flexible request format
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get compatibility recommendations for a skill."""
    try:
        # Validate request
        if "skill_data" not in request:
            raise HTTPException(status_code=400, detail="skill_data is required")
        if "target_platforms" not in request:
            raise HTTPException(status_code=400, detail="target_platforms is required")

        # Perform validation to get recommendations
        report = await manager.validate_skill_compatibility(
            skill_data=request["skill_data"],
            target_platforms=request["target_platforms"]
        )

        # Extract recommendations
        recommendations = report.get("recommendations", [])

        return JSONResponse(content={
            "skill_name": request["skill_data"].get("name", "Unknown"),
            "target_platforms": request["target_platforms"],
            "recommendations": recommendations,
            "compatibility_score": report.get("compatibility_score", 0),
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.post(
    "/best-platform",
    summary="Find best compatible platform",
    description="Find the best platform for a skill based on compatibility"
)
async def find_best_platform(
    request: Dict[str, Any],
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Find the best platform for a skill."""
    try:
        # Validate request
        if "skill_data" not in request:
            raise HTTPException(status_code=400, detail="skill_data is required")

        # Get all platforms or filter by provided list
        target_platforms = request.get("target_platforms")

        # Perform validation
        report = await manager.validate_skill_compatibility(
            skill_data=request["skill_data"],
            target_platforms=target_platforms
        )

        # Extract compatible platforms with scores
        compatible_platforms = []
        for platform_id, result in report["platform_results"].items():
            if result.valid:
                # Calculate score (100 - errors*10 - warnings*5)
                score = 100 - (len(result.issues) * 10) - (len(result.warnings) * 5)
                score = max(0, score)
                compatible_platforms.append({
                    "platform_id": platform_id,
                    "compatibility_score": score,
                    "error_count": len(result.issues),
                    "warning_count": len(result.warnings)
                })

        # Sort by score
        compatible_platforms.sort(key=lambda x: x["compatibility_score"], reverse=True)

        return JSONResponse(content={
            "skill_name": request["skill_data"].get("name", "Unknown"),
            "best_platform": compatible_platforms[0] if compatible_platforms else None,
            "all_compatible_platforms": compatible_platforms,
            "overall_compatible": report["overall_compatible"],
            "timestamp": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find best platform: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to find best platform: {str(e)}")


@router.get(
    "/formats/compatibility-matrix",
    summary="Get format compatibility matrix",
    description="Get a matrix showing format compatibility across platforms"
)
async def get_format_compatibility_matrix(
    manager: PlatformManager = Depends(get_platform_manager)
):
    """Get format compatibility matrix across platforms."""
    try:
        # Get available platforms
        health_status = await manager.get_platform_health()
        platforms = list(health_status.keys())

        # Get supported formats
        supported_formats = list(manager.converter.get_supported_formats())

        # Build compatibility matrix
        matrix = {}
        for format in supported_formats:
            matrix[format] = {}
            for platform in platforms:
                # Basic compatibility check
                # In reality, would check adapter.supported_formats
                if format in ["json", "yaml", "markdown"]:
                    matrix[format][platform] = True
                else:
                    matrix[format][platform] = False

        return JSONResponse(content={
            "formats": supported_formats,
            "platforms": platforms,
            "compatibility_matrix": matrix,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        logger.error(f"Failed to get compatibility matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get matrix: {str(e)}")