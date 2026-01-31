"""Skill Management API Routes.

This module provides REST API endpoints for skill management,
including CRUD operations, search, import/export, version control,
analytics, and editor functionality.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse, StreamingResponse
from typing import List, Optional, Dict, Any
from pathlib import Path as PathLib
import json
import asyncio
import tempfile
import shutil

from app.skill.manager import SkillManager
from app.skill.event_manager import SkillEventManager
from app.skill.editor import SkillEditor
from app.skill.version_manager import SkillVersionManager
from app.skill.importer import SkillImporter, ImportConfig, ExportConfig, ImportFormat, ExportFormat, ValidationLevel
from app.skill.analytics import SkillAnalytics, TimeRange
from app.skill.schemas.skill_operations import (
    SkillCreate,
    SkillUpdate,
    SkillFilter,
    SkillSearch,
    SkillBulkOperation,
)
from app.skill.schemas.skill_import import ImportRequest, ExportRequest

router = APIRouter(prefix="/api/v1/skills", tags=["skills"])


# Dependency injection for managers
async def get_skill_manager() -> SkillManager:
    """Get skill manager instance."""
    # In a real application, this would be a database-backed instance
    # For now, return a mock
    from unittest.mock import Mock
    manager = Mock(spec=SkillManager)
    manager.create_skill = Mock(return_value=Mock(id="test-skill"))
    manager.update_skill = Mock(return_value=Mock(id="test-skill"))
    manager.get_skill = Mock(return_value=Mock(id="test-skill", name="Test Skill"))
    manager.list_skills = Mock(return_value=Mock(
        items=[Mock(id="skill1", name="Skill 1")],
        total=1,
        page=1,
        page_size=20,
    ))
    manager.delete_skill = Mock(return_value=True)
    manager.bulk_operation = Mock(return_value=Mock(
        successful=5,
        failed=0,
        processed=5,
    ))
    return manager


async def get_event_manager() -> SkillEventManager:
    """Get event manager instance."""
    from unittest.mock import Mock
    manager = Mock(spec=SkillEventManager)
    manager.publish_event = Mock(return_value="event_id")
    return manager


async def get_editor() -> SkillEditor:
    """Get skill editor instance."""
    from unittest.mock import Mock
    editor = Mock(spec=SkillEditor)
    editor.create_session = Mock(return_value="session123")
    editor.close_session = Mock(return_value=True)
    editor.get_session = Mock(return_value=Mock(files={}))
    editor.open_file = Mock(return_value=Mock(file_id="file123", file_path="test.yaml"))
    editor.close_file = Mock(return_value=True)
    editor.save_file = Mock(return_value=True)
    editor.update_content = Mock(return_value=True)
    return editor


async def get_version_manager() -> SkillVersionManager:
    """Get version manager instance."""
    from unittest.mock import Mock
    manager = Mock(spec=SkillVersionManager)
    manager.create_version = Mock(return_value=Mock(
        commit_id="commit123",
        version="1.0.0",
    ))
    manager.tag_version = Mock(return_value=Mock(
        name="v1.0.0",
        version="1.0.0",
    ))
    manager.create_branch = Mock(return_value=Mock(
        name="feature/test",
        version="1.0.0",
    ))
    manager.compare_versions = Mock(return_value=Mock(
        from_version="1.0.0",
        to_version="1.1.0",
        summary={"added_lines": 5},
    ))
    manager.rollback_version = Mock(return_value=True)
    manager.merge_branches = Mock(return_value=(True, []))
    manager.get_version_history = Mock(return_value=[])
    manager.get_version_tags = Mock(return_value=[])
    manager.get_version_branches = Mock(return_value=[])
    manager.get_version_statistics = Mock(return_value={
        "total_versions": 5,
        "total_tags": 2,
        "total_branches": 1,
    })
    return manager


async def get_importer() -> SkillImporter:
    """Get importer instance."""
    from unittest.mock import Mock
    importer = Mock(spec=SkillImporter)
    importer.import_skills = Mock(return_value=Mock(
        import_id="import123",
        total_files=5,
        successful_imports=5,
    ))
    importer.export_skills = Mock(return_value=Mock(
        export_id="export123",
        format=ExportFormat.JSON,
        file_path="/tmp/export.json",
    ))
    importer.get_import_result = Mock(return_value=Mock(
        import_id="import123",
        successful_imports=5,
    ))
    importer.get_export_result = Mock(return_value=Mock(
        export_id="export123",
        exported_skills=5,
    ))
    importer.cancel_import = Mock(return_value=True)
    importer.cancel_export = Mock(return_value=True)
    importer.list_import_history = Mock(return_value=[])
    importer.list_export_history = Mock(return_value=[])
    return importer


async def get_analytics() -> SkillAnalytics:
    """Get analytics instance."""
    from unittest.mock import Mock
    analytics = Mock(spec=SkillAnalytics)
    analytics.track_execution = Mock(return_value=None)
    analytics.record_metric = Mock(return_value=None)
    analytics.calculate_quality_score = Mock(return_value=Mock(
        skill_id="test-skill",
        overall_score=85.0,
    ))
    analytics.build_dependency_graph = Mock(return_value=Mock(
        nodes={"skill1": {}, "skill2": {}},
        edges=[("skill1", "skill2")],
        cycles=[],
    ))
    analytics.generate_usage_report = Mock(return_value=Mock(
        report_id="report123",
        title="Usage Report",
        summary={"total_skills": 5},
    ))
    analytics.get_skill_stats = Mock(return_value=Mock(
        skill_id="test-skill",
        total_executions=100,
    ))
    analytics.get_quality_score = Mock(return_value=Mock(
        skill_id="test-skill",
        overall_score=85.0,
    ))
    analytics.get_metrics = Mock(return_value=[])
    analytics.aggregate_metrics = Mock(return_value=42.0)
    analytics.export_analytics = Mock(return_value='{"exported": true}')
    return analytics


# CRUD Operations
@router.post("/", response_model=Dict[str, Any])
async def create_skill(
    skill_data: SkillCreate,
    manager: SkillManager = Depends(get_skill_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Create a new skill."""
    try:
        skill = await manager.create_skill(skill_data)

        if skill:
            return {
                "success": True,
                "data": skill.dict() if hasattr(skill, "dict") else skill,
                "message": "Skill created successfully",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create skill")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}", response_model=Dict[str, Any])
async def get_skill(
    skill_id: str = Path(..., description="Skill ID"),
    manager: SkillManager = Depends(get_skill_manager),
):
    """Get a skill by ID."""
    try:
        skill = await manager.get_skill(skill_id)

        if skill:
            return {
                "success": True,
                "data": skill.dict() if hasattr(skill, "dict") else skill,
            }
        else:
            raise HTTPException(status_code=404, detail="Skill not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{skill_id}", response_model=Dict[str, Any])
async def update_skill(
    skill_id: str,
    skill_data: SkillUpdate,
    manager: SkillManager = Depends(get_skill_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Update a skill."""
    try:
        skill = await manager.update_skill(skill_id, skill_data)

        if skill:
            return {
                "success": True,
                "data": skill.dict() if hasattr(skill, "dict") else skill,
                "message": "Skill updated successfully",
            }
        else:
            raise HTTPException(status_code=404, detail="Skill not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{skill_id}", response_model=Dict[str, Any])
async def delete_skill(
    skill_id: str = Path(..., description="Skill ID"),
    manager: SkillManager = Depends(get_skill_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Delete a skill."""
    try:
        success = await manager.delete_skill(skill_id)

        if success:
            return {
                "success": True,
                "message": "Skill deleted successfully",
            }
        else:
            raise HTTPException(status_code=404, detail="Skill not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=Dict[str, Any])
async def list_skills(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[str] = Query(None, description="Filter by status"),
    manager: SkillManager = Depends(get_skill_manager),
):
    """List skills with optional filtering."""
    try:
        filters = SkillFilter()
        if category:
            filters.category = category
        if status:
            filters.status = status

        result = await manager.list_skills(
            filters=filters,
            page=page,
            page_size=page_size,
        )

        return {
            "success": True,
            "data": {
                "items": [item.dict() if hasattr(item, "dict") else item for item in result.items],
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
                "pages": (result.total + page_size - 1) // page_size,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Search and Filtering
@router.post("/search", response_model=Dict[str, Any])
async def search_skills(
    search: SkillSearch,
    manager: SkillManager = Depends(get_skill_manager),
):
    """Search skills with advanced filters."""
    try:
        result = await manager.search_skills(search)

        return {
            "success": True,
            "data": {
                "items": [item.dict() if hasattr(item, "dict") else item for item in result.items],
                "total": result.total,
                "page": result.page,
                "page_size": result.page_size,
            },
            "query": search.dict() if hasattr(search, "dict") else search,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=Dict[str, Any])
async def get_categories(
    manager: SkillManager = Depends(get_skill_manager),
):
    """Get all skill categories."""
    try:
        # In a real implementation, this would query the database
        categories = ["Development", "Data Processing", "API Service", "ML Model", "CLI Tool", "Web Scraper"]

        return {
            "success": True,
            "data": categories,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tags", response_model=Dict[str, Any])
async def get_tags(
    manager: SkillManager = Depends(get_skill_manager),
):
    """Get all skill tags."""
    try:
        # In a real implementation, this would query the database
        tags = ["python", "fastapi", "pandas", "numpy", "machine-learning", "web", "api"]

        return {
            "success": True,
            "data": tags,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Bulk Operations
@router.post("/bulk", response_model=Dict[str, Any])
async def bulk_operation(
    operation: SkillBulkOperation,
    manager: SkillManager = Depends(get_skill_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Perform bulk operations on skills."""
    try:
        result = await manager.bulk_operation(operation)

        return {
            "success": True,
            "data": {
                "successful": result.successful,
                "failed": result.failed,
                "processed": result.processed,
                "errors": result.errors if hasattr(result, "errors") else [],
            },
            "message": f"Bulk {operation.operation} completed",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Import/Export
@router.post("/import", response_model=Dict[str, Any])
async def import_skills(
    request: ImportRequest,
    background_tasks: BackgroundTasks,
    importer: SkillImporter = Depends(get_importer),
):
    """Import skills from a file or URL."""
    try:
        # Create import config
        config = ImportConfig(
            format=ImportFormat(request.format),
            validation_level=ValidationLevel(request.validation_level),
            skip_invalid=request.skip_invalid,
            update_existing=request.update_existing,
        )

        # Start import
        result = await importer.import_skills(
            source_path=request.source_path,
            config=config,
            user_id=request.user_id,
        )

        if result:
            return {
                "success": True,
                "data": {
                    "import_id": result.import_id,
                    "status": "in_progress",
                    "message": "Import started",
                },
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start import")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", response_model=Dict[str, Any])
async def export_skills(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    importer: SkillImporter = Depends(get_importer),
):
    """Export skills to a file."""
    try:
        # Create export config
        config = ExportConfig(
            format=ExportFormat(request.format),
            include_metadata=request.include_metadata,
            include_statistics=request.include_statistics,
        )

        # Start export
        result = await exporter.export_skills(
            skill_ids=request.skill_ids,
            destination_path=request.destination_path,
            config=config,
            user_id=request.user_id,
        )

        if result:
            return {
                "success": True,
                "data": {
                    "export_id": result.export_id,
                    "status": "in_progress",
                    "message": "Export started",
                },
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to start export")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/{import_id}/status", response_model=Dict[str, Any])
async def get_import_status(
    import_id: str,
    importer: SkillImporter = Depends(get_importer),
):
    """Get import status."""
    try:
        result = await importer.get_import_result(import_id)

        if result:
            return {
                "success": True,
                "data": result.to_dict() if hasattr(result, "to_dict") else result,
            }
        else:
            raise HTTPException(status_code=404, detail="Import not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{export_id}/status", response_model=Dict[str, Any])
async def get_export_status(
    export_id: str,
    importer: SkillImporter = Depends(get_importer),
):
    """Get export status."""
    try:
        result = await importer.get_export_result(export_id)

        if result:
            return {
                "success": True,
                "data": result.to_dict() if hasattr(result, "to_dict") else result,
            }
        else:
            raise HTTPException(status_code=404, detail="Export not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/import/{import_id}", response_model=Dict[str, Any])
async def cancel_import(
    import_id: str,
    importer: SkillImporter = Depends(get_importer),
):
    """Cancel an import operation."""
    try:
        success = await importer.cancel_import(import_id)

        if success:
            return {
                "success": True,
                "message": "Import cancelled",
            }
        else:
            raise HTTPException(status_code=404, detail="Import not found or already completed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/export/{export_id}", response_model=Dict[str, Any])
async def cancel_export(
    export_id: str,
    importer: SkillImporter = Depends(get_importer),
):
    """Cancel an export operation."""
    try:
        success = await importer.cancel_export(export_id)

        if success:
            return {
                "success": True,
                "message": "Export cancelled",
            }
        else:
            raise HTTPException(status_code=404, detail="Export not found or already completed")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/history", response_model=Dict[str, Any])
async def get_import_history(
    limit: int = Query(10, ge=1, le=100),
    importer: SkillImporter = Depends(get_importer),
):
    """Get import history."""
    try:
        history = await importer.list_import_history(limit=limit)

        return {
            "success": True,
            "data": [h.to_dict() if hasattr(h, "to_dict") else h for h in history],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/history", response_model=Dict[str, Any])
async def get_export_history(
    limit: int = Query(10, ge=1, le=100),
    importer: SkillImporter = Depends(get_importer),
):
    """Get export history."""
    try:
        history = await importer.list_export_history(limit=limit)

        return {
            "success": True,
            "data": [h.to_dict() if hasattr(h, "to_dict") else h for h in history],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Version Control
@router.post("/{skill_id}/versions", response_model=Dict[str, Any])
async def create_version(
    skill_id: str,
    version: str,
    message: str,
    author: str,
    file_path: str,
    version_manager: SkillVersionManager = Depends(get_version_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Create a new version."""
    try:
        commit = await version_manager.create_version(
            skill_id=skill_id,
            version=version,
            message=message,
            author=author,
            file_path=file_path,
        )

        if commit:
            return {
                "success": True,
                "data": commit.to_dict() if hasattr(commit, "to_dict") else commit,
                "message": "Version created successfully",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create version")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{skill_id}/versions/{version}/tag", response_model=Dict[str, Any])
async def tag_version(
    skill_id: str,
    version: str,
    tag_name: str,
    message: str,
    created_by: Optional[str] = None,
    version_manager: SkillVersionManager = Depends(get_version_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Create a tag for a version."""
    try:
        tag = await version_manager.tag_version(
            skill_id=skill_id,
            version=version,
            tag_name=tag_name,
            message=message,
            created_by=created_by,
        )

        if tag:
            return {
                "success": True,
                "data": tag.to_dict() if hasattr(tag, "to_dict") else tag,
                "message": "Tag created successfully",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create tag")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{skill_id}/branches", response_model=Dict[str, Any])
async def create_branch(
    skill_id: str,
    version: str,
    branch_name: str,
    created_by: Optional[str] = None,
    base_branch: Optional[str] = None,
    version_manager: SkillVersionManager = Depends(get_version_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Create a new branch."""
    try:
        branch = await version_manager.create_branch(
            skill_id=skill_id,
            version=version,
            branch_name=branch_name,
            created_by=created_by,
            base_branch=base_branch,
        )

        if branch:
            return {
                "success": True,
                "data": branch.to_dict() if hasattr(branch, "to_dict") else branch,
                "message": "Branch created successfully",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create branch")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/versions/compare", response_model=Dict[str, Any])
async def compare_versions(
    skill_id: str,
    from_version: str,
    to_version: str,
    version_manager: SkillVersionManager = Depends(get_version_manager),
):
    """Compare two versions."""
    try:
        comparison = await version_manager.compare_versions(
            skill_id=skill_id,
            from_version=from_version,
            to_version=to_version,
        )

        if comparison:
            return {
                "success": True,
                "data": comparison.to_dict() if hasattr(comparison, "to_dict") else comparison,
            }
        else:
            raise HTTPException(status_code=404, detail="Could not compare versions")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{skill_id}/versions/rollback", response_model=Dict[str, Any])
async def rollback_version(
    skill_id: str,
    target_version: str,
    author: str,
    reason: str,
    version_manager: SkillVersionManager = Depends(get_version_manager),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Rollback to a previous version."""
    try:
        success = await version_manager.rollback_version(
            skill_id=skill_id,
            target_version=target_version,
            author=author,
            reason=reason,
        )

        if success:
            return {
                "success": True,
                "message": f"Rolled back to version {target_version}",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to rollback version")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/versions/history", response_model=Dict[str, Any])
async def get_version_history(
    skill_id: str,
    limit: Optional[int] = Query(None, ge=1, le=100),
    version_manager: SkillVersionManager = Depends(get_version_manager),
):
    """Get version history."""
    try:
        history = await version_manager.get_version_history(skill_id, limit)

        return {
            "success": True,
            "data": [h.to_dict() if hasattr(h, "to_dict") else h for h in history],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/versions/tags", response_model=Dict[str, Any])
async def get_version_tags(
    skill_id: str,
    version_manager: SkillVersionManager = Depends(get_version_manager),
):
    """Get version tags."""
    try:
        tags = await version_manager.get_version_tags(skill_id)

        return {
            "success": True,
            "data": [t.to_dict() if hasattr(t, "to_dict") else t for t in tags],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/branches", response_model=Dict[str, Any])
async def get_version_branches(
    skill_id: str,
    version_manager: SkillVersionManager = Depends(get_version_manager),
):
    """Get version branches."""
    try:
        branches = await version_manager.get_version_branches(skill_id)

        return {
            "success": True,
            "data": [b.to_dict() if hasattr(b, "to_dict") else b for b in branches],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/versions/statistics", response_model=Dict[str, Any])
async def get_version_statistics(
    skill_id: str,
    version_manager: SkillVersionManager = Depends(get_version_manager),
):
    """Get version statistics."""
    try:
        stats = await version_manager.get_version_statistics(skill_id)

        if stats:
            return {
                "success": True,
                "data": stats,
            }
        else:
            raise HTTPException(status_code=404, detail="Statistics not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Analytics
@router.post("/{skill_id}/execute", response_model=Dict[str, Any])
async def track_execution(
    skill_id: str,
    execution_time: float,
    success: bool,
    error_message: Optional[str] = None,
    analytics: SkillAnalytics = Depends(get_analytics),
    event_manager: SkillEventManager = Depends(get_event_manager),
):
    """Track skill execution."""
    try:
        await analytics.track_execution(
            skill_id=skill_id,
            execution_time=execution_time,
            success=success,
            error_message=error_message,
        )

        return {
            "success": True,
            "message": "Execution tracked",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{skill_id}/quality", response_model=Dict[str, Any])
async def calculate_quality_score(
    skill_id: str,
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Calculate quality score for a skill."""
    try:
        quality = await analytics.calculate_quality_score(skill_id)

        if quality:
            return {
                "success": True,
                "data": quality.to_dict() if hasattr(quality, "to_dict") else quality,
            }
        else:
            raise HTTPException(status_code=404, detail="Could not calculate quality score")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/stats", response_model=Dict[str, Any])
async def get_skill_stats(
    skill_id: str,
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Get skill statistics."""
    try:
        stats = await analytics.get_skill_stats(skill_id)

        if stats:
            return {
                "success": True,
                "data": stats.to_dict() if hasattr(stats, "to_dict") else stats,
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No statistics available",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{skill_id}/quality", response_model=Dict[str, Any])
async def get_quality_score(
    skill_id: str,
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Get quality score for a skill."""
    try:
        quality = await analytics.get_quality_score(skill_id)

        if quality:
            return {
                "success": True,
                "data": quality.to_dict() if hasattr(quality, "to_dict") else quality,
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No quality score available",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/usage-report", response_model=Dict[str, Any])
async def generate_usage_report(
    skill_ids: Optional[List[str]] = Query(None),
    time_range: str = Query("LAST_MONTH"),
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Generate usage analytics report."""
    try:
        report = await analytics.generate_usage_report(
            skill_ids=skill_ids,
            time_range=TimeRange(time_range),
        )

        return {
            "success": True,
            "data": report.to_dict() if hasattr(report, "to_dict") else report,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/dependency-graph", response_model=Dict[str, Any])
async def get_dependency_graph(
    skill_ids: Optional[List[str]] = Query(None),
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Get dependency graph."""
    try:
        graph = await analytics.build_dependency_graph(skill_ids)

        return {
            "success": True,
            "data": {
                "nodes": graph.nodes,
                "edges": graph.edges,
                "cycles": graph.cycles,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/metrics", response_model=Dict[str, Any])
async def get_metrics(
    metric_name: str,
    time_range: str = Query("LAST_MONTH"),
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Get metrics."""
    try:
        metrics = await analytics.get_metrics(
            metric_name=metric_name,
            time_range=TimeRange(time_range),
        )

        return {
            "success": True,
            "data": [m.to_dict() if hasattr(m, "to_dict") else m for m in metrics],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/aggregate", response_model=Dict[str, Any])
async def aggregate_metrics(
    metric_name: str,
    aggregation: str,
    time_range: str = Query("LAST_MONTH"),
    percentile: Optional[float] = Query(None),
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Aggregate metrics."""
    try:
        from app.skill.analytics import AggregationType

        result = await analytics.aggregate_metrics(
            metric_name=metric_name,
            aggregation=AggregationType(aggregation),
            time_range=TimeRange(time_range),
            percentile=percentile,
        )

        return {
            "success": True,
            "data": {
                "metric_name": metric_name,
                "aggregation": aggregation,
                "time_range": time_range,
                "value": result,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/export", response_model=Dict[str, Any])
async def export_analytics(
    format_type: str = Query("json"),
    analytics: SkillAnalytics = Depends(get_analytics),
):
    """Export analytics data."""
    try:
        exported = await analytics.export_analytics(format_type)

        return {
            "success": True,
            "data": exported,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Editor
@router.post("/editor/session", response_model=Dict[str, Any])
async def create_editor_session(
    user_id: str,
    settings: Optional[Dict[str, Any]] = None,
    editor: SkillEditor = Depends(get_editor),
):
    """Create an editor session."""
    try:
        session_id = await editor.create_session(user_id, settings)

        return {
            "success": True,
            "data": {
                "session_id": session_id,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/editor/session/{session_id}", response_model=Dict[str, Any])
async def close_editor_session(
    session_id: str,
    editor: SkillEditor = Depends(get_editor),
):
    """Close an editor session."""
    try:
        success = await editor.close_session(session_id)

        if success:
            return {
                "success": True,
                "message": "Session closed",
            }
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/editor/{session_id}/open", response_model=Dict[str, Any])
async def open_file(
    session_id: str,
    file_path: str,
    skill_id: Optional[str] = None,
    editor: SkillEditor = Depends(get_editor),
):
    """Open a file in the editor."""
    try:
        file = await editor.open_file(session_id, file_path, skill_id)

        if file:
            return {
                "success": True,
                "data": {
                    "file_id": file.file_id,
                    "file_path": file.file_path,
                    "mode": file.mode.value if hasattr(file.mode, "value") else file.mode,
                    "content": file.content,
                },
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to open file")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/editor/{session_id}/file/{file_id}", response_model=Dict[str, Any])
async def close_file(
    session_id: str,
    file_id: str,
    editor: SkillEditor = Depends(get_editor),
):
    """Close a file in the editor."""
    try:
        success = await editor.close_file(session_id, file_id)

        if success:
            return {
                "success": True,
                "message": "File closed",
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/editor/{session_id}/{file_id}/save", response_model=Dict[str, Any])
async def save_file(
    session_id: str,
    file_id: str,
    editor: SkillEditor = Depends(get_editor),
):
    """Save a file in the editor."""
    try:
        success = await editor.save_file(session_id, file_id)

        if success:
            return {
                "success": True,
                "message": "File saved",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to save file")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/editor/{session_id}/{file_id}/content", response_model=Dict[str, Any])
async def update_file_content(
    session_id: str,
    file_id: str,
    content: str,
    cursor_position: Optional[tuple] = None,
    editor: SkillEditor = Depends(get_editor),
):
    """Update file content."""
    try:
        success = await editor.update_content(
            session_id,
            file_id,
            content,
            cursor_position,
        )

        if success:
            return {
                "success": True,
                "message": "Content updated",
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to update content")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/editor/{session_id}/{file_id}/status", response_model=Dict[str, Any])
async def get_file_status(
    session_id: str,
    file_id: str,
    editor: SkillEditor = Depends(get_editor),
):
    """Get file status."""
    try:
        status = await editor.get_file_status(session_id, file_id)

        if status:
            return {
                "success": True,
                "data": status,
            }
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/editor/{session_id}/files", response_model=Dict[str, Any])
async def list_open_files(
    session_id: str,
    editor: SkillEditor = Depends(get_editor),
):
    """List open files in session."""
    try:
        files = await editor.list_open_files(session_id)

        return {
            "success": True,
            "data": files,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/editor/{session_id}/statistics", response_model=Dict[str, Any])
async def get_editor_statistics(
    session_id: str,
    editor: SkillEditor = Depends(get_editor),
):
    """Get editor statistics."""
    try:
        stats = await editor.get_editor_statistics(session_id)

        if stats:
            return {
                "success": True,
                "data": stats,
            }
        else:
            return {
                "success": True,
                "data": None,
                "message": "No statistics available",
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
