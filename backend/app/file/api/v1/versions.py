"""File Version Management API.

This module provides REST API endpoints for file version control including
version creation, listing, comparison, restoration, and diff viewing.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

# Import version manager
from app.file.version_manager import VersionManager
from app.file.schemas.file_operations import (
    VersionCreateRequest,
    VersionResponse,
    VersionListResponse,
    VersionRestoreRequest,
    VersionComparisonRequest,
)
from app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/versions", tags=["versions"])


# Dependency injection
async def get_version_manager(db: AsyncSession = Depends(get_db)) -> VersionManager:
    """Get VersionManager instance."""
    return VersionManager(db_session=db)


# Version Creation

@router.post(
    "/files/{file_id}",
    response_model=VersionResponse,
    summary="Create file version",
    description="Create a new version of a file",
)
async def create_file_version(
    file_id: UUID = ...,
    request: VersionCreateRequest = ...,
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Create a new version of a file.

    Args:
        file_id: File ID
        request: Version creation request
        version_manager: Version manager instance

    Returns:
        Created version information

    Raises:
        HTTPException: If version creation fails
    """
    try:
        version = await version_manager.create_version(
            file_id=file_id,
            content=request.content,
            version_note=request.note,
            metadata=request.metadata,
        )

        logger.info(f"Version created: {version.id} for file {file_id}")

        return VersionResponse(
            success=True,
            version=version,
            message="Version created successfully",
        )

    except Exception as e:
        logger.error(f"Create version failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/files/{file_id}/auto",
    response_model=VersionResponse,
    summary="Auto-create version",
    description="Automatically create a version of a file based on changes",
)
async def auto_create_version(
    file_id: UUID = ...,
    note: Optional[str] = Query(None, description="Optional version note"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Auto-create a version based on file changes.

    Args:
        file_id: File ID
        note: Optional version note
        version_manager: Version manager instance

    Returns:
        Auto-created version information

    Raises:
        HTTPException: If auto-version creation fails
    """
    try:
        version = await version_manager.auto_create_version(
            file_id=file_id,
            note=note,
        )

        logger.info(f"Auto-version created: {version.id} for file {file_id}")

        return VersionResponse(
            success=True,
            version=version,
            message="Auto-version created successfully",
        )

    except Exception as e:
        logger.error(f"Auto-create version failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Version Listing and Retrieval

@router.get(
    "/files/{file_id}",
    response_model=VersionListResponse,
    summary="List file versions",
    description="List all versions of a file",
)
async def list_file_versions(
    file_id: UUID = ...,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """List all versions of a file.

    Args:
        file_id: File ID
        page: Page number (1-indexed)
        size: Page size
        version_manager: Version manager instance

    Returns:
        List of file versions

    Raises:
        HTTPException: If version listing fails
    """
    try:
        result = await version_manager.list_versions(
            file_id=file_id,
            page=page,
            size=size,
        )

        return VersionListResponse(
            success=True,
            versions=result.versions,
            total=result.total,
            page=result.page,
            size=result.size,
            pages=result.pages,
            message="Versions retrieved successfully",
        )

    except Exception as e:
        logger.error(f"List versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/files/{file_id}/{version_id}",
    response_model=VersionResponse,
    summary="Get version details",
    description="Get detailed information about a specific version",
)
async def get_version_details(
    file_id: UUID = ...,
    version_id: UUID = ...,
    include_content: bool = Query(False, description="Include version content"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Get detailed information about a version.

    Args:
        file_id: File ID
        version_id: Version ID
        include_content: Whether to include version content
        version_manager: Version manager instance

    Returns:
        Version details

    Raises:
        HTTPException: If version not found
    """
    try:
        version = await version_manager.get_version(
            version_id=version_id,
            include_content=include_content,
        )

        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        return VersionResponse(
            success=True,
            version=version,
            message="Version retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get version details failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/files/{file_id}/latest",
    response_model=VersionResponse,
    summary="Get latest version",
    description="Get the latest version of a file",
)
async def get_latest_version(
    file_id: UUID = ...,
    include_content: bool = Query(False, description="Include version content"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Get the latest version of a file.

    Args:
        file_id: File ID
        include_content: Whether to include version content
        version_manager: Version manager instance

    Returns:
        Latest version information

    Raises:
        HTTPException: If no versions found
    """
    try:
        version = await version_manager.get_latest_version(
            file_id=file_id,
            include_content=include_content,
        )

        if not version:
            raise HTTPException(status_code=404, detail="No versions found for this file")

        return VersionResponse(
            success=True,
            version=version,
            message="Latest version retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get latest version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Version Restoration

@router.post(
    "/files/{file_id}/{version_id}/restore",
    response_model=VersionResponse,
    summary="Restore version",
    description="Restore a file to a previous version",
)
async def restore_version(
    file_id: UUID = ...,
    version_id: UUID = ...,
    request: Optional[VersionRestoreRequest] = None,
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Restore a file to a previous version.

    Args:
        file_id: File ID
        version_id: Version ID to restore from
        request: Optional restore request with note
        version_manager: Version manager instance

    Returns:
        Restored version information

    Raises:
        HTTPException: If version restoration fails
    """
    try:
        restore_note = request.note if request else None

        version = await version_manager.restore_version(
            file_id=file_id,
            version_id=version_id,
            note=restore_note,
        )

        logger.info(f"Version restored: {version.id} for file {file_id}")

        return VersionResponse(
            success=True,
            version=version,
            message="Version restored successfully",
        )

    except Exception as e:
        logger.error(f"Restore version failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/files/{file_id}/restore",
    response_model=VersionResponse,
    summary="Restore to version",
    description="Restore a file to a specific version",
)
async def restore_to_version(
    file_id: UUID = ...,
    version_id: UUID = Query(..., description="Version ID to restore to"),
    create_backup: bool = Query(True, description="Create backup of current version"),
    note: Optional[str] = Query(None, description="Optional restore note"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Restore file to a specific version.

    Args:
        file_id: File ID
        version_id: Version ID to restore to
        create_backup: Whether to create backup of current version
        note: Optional restore note
        version_manager: Version manager instance

    Returns:
        Restored version information

    Raises:
        HTTPException: If restore fails
    """
    try:
        version = await version_manager.restore_to_version(
            file_id=file_id,
            version_id=version_id,
            create_backup=create_backup,
            note=note,
        )

        logger.info(f"File restored to version: {version.id} for file {file_id}")

        return VersionResponse(
            success=True,
            version=version,
            message="File restored to specified version",
        )

    except Exception as e:
        logger.error(f"Restore to version failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Version Comparison

@router.post(
    "/compare",
    response_model=Dict[str, Any],
    summary="Compare versions",
    description="Compare two versions and show differences",
)
async def compare_versions(
    request: VersionComparisonRequest = ...,
    diff_format: str = Query("unified", regex="^(unified|side-by-side|inline)$", description="Diff format"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Compare two versions and show differences.

    Args:
        request: Version comparison request
        diff_format: Diff format (unified, side-by-side, inline)
        version_manager: Version manager instance

    Returns:
        Version comparison result

    Raises:
        HTTPException: If comparison fails
    """
    try:
        result = await version_manager.compare_versions(
            version1_id=request.version1_id,
            version2_id=request.version2_id,
            format=diff_format,
        )

        return {
            "success": True,
            "comparison": {
                "version1": {
                    "id": result.version1.id,
                    "created_at": result.version1.created_at.isoformat(),
                    "note": result.version1.version_note,
                },
                "version2": {
                    "id": result.version2.id,
                    "created_at": result.version2.created_at.isoformat(),
                    "note": result.version2.version_note,
                },
                "diff": result.diff,
                "format": diff_format,
                "statistics": {
                    "added_lines": result.statistics.added_lines,
                    "deleted_lines": result.statistics.deleted_lines,
                    "modified_lines": result.statistics.modified_lines,
                    "unchanged_lines": result.statistics.unchanged_lines,
                },
            },
            "message": "Version comparison completed successfully",
        }

    except Exception as e:
        logger.error(f"Compare versions failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/files/{file_id}/compare/{version1_id}/{version2_id}",
    response_model=Dict[str, Any],
    summary="Compare specific versions",
    description="Compare two specific versions of a file",
)
async def compare_specific_versions(
    file_id: UUID = ...,
    version1_id: UUID = ...,
    version2_id: UUID = ...,
    format: str = Query("unified", regex="^(unified|side-by-side|inline)$", description="Diff format"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Compare two specific versions of a file.

    Args:
        file_id: File ID
        version1_id: First version ID
        version2_id: Second version ID
        format: Diff format
        version_manager: Version manager instance

    Returns:
        Comparison result

    Raises:
        HTTPException: If comparison fails
    """
    try:
        result = await version_manager.compare_versions(
            version1_id=version1_id,
            version2_id=version2_id,
            format=format,
        )

        return {
            "success": True,
            "comparison": {
                "version1": {
                    "id": result.version1.id,
                    "created_at": result.version1.created_at.isoformat(),
                    "note": result.version1.version_note,
                },
                "version2": {
                    "id": result.version2.id,
                    "created_at": result.version2.created_at.isoformat(),
                    "note": result.version2.version_note,
                },
                "diff": result.diff,
                "format": format,
                "statistics": {
                    "added_lines": result.statistics.added_lines,
                    "deleted_lines": result.statistics.deleted_lines,
                    "modified_lines": result.statistics.modified_lines,
                    "unchanged_lines": result.statistics.unchanged_lines,
                },
            },
        }

    except Exception as e:
        logger.error(f"Compare specific versions failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Version Content

@router.get(
    "/versions/{version_id}/content",
    response_model=Dict[str, Any],
    summary="Get version content",
    description="Get the content of a specific version",
)
async def get_version_content(
    version_id: UUID = ...,
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Get the content of a version.

    Args:
        version_id: Version ID
        version_manager: Version manager instance

    Returns:
        Version content

    Raises:
        HTTPException: If version not found
    """
    try:
        content = await version_manager.get_version_content(version_id)

        if content is None:
            raise HTTPException(status_code=404, detail="Version not found")

        return {
            "success": True,
            "content": content,
            "version_id": version_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get version content failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/files/{file_id}/{version_id}/preview",
    response_model=Dict[str, Any],
    summary="Preview version",
    description="Preview a specific version of a file",
)
async def preview_version(
    file_id: UUID = ...,
    version_id: UUID = ...,
    max_lines: int = Query(100, ge=1, le=1000, description="Maximum lines to preview"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Preview a specific version of a file.

    Args:
        file_id: File ID
        version_id: Version ID
        max_lines: Maximum lines to include
        version_manager: Version manager instance

    Returns:
        Version preview

    Raises:
        HTTPException: If preview generation fails
    """
    try:
        preview = await version_manager.preview_version(
            file_id=file_id,
            version_id=version_id,
            max_lines=max_lines,
        )

        return {
            "success": True,
            "preview": {
                "version_id": preview.version_id,
                "content": preview.content,
                "line_count": preview.line_count,
                "truncated": preview.truncated,
                "max_lines": max_lines,
                "created_at": preview.created_at.isoformat(),
            },
            "message": "Version preview generated successfully",
        }

    except Exception as e:
        logger.error(f"Preview version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Version Statistics

@router.get(
    "/files/{file_id}/statistics",
    response_model=Dict[str, Any],
    summary="Get version statistics",
    description="Get statistics about file versions",
)
async def get_version_statistics(
    file_id: UUID = ...,
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Get statistics about file versions.

    Args:
        file_id: File ID
        version_manager: Version manager instance

    Returns:
        Version statistics

    Raises:
        HTTPException: If statistics generation fails
    """
    try:
        stats = await version_manager.get_version_statistics(file_id)

        return {
            "success": True,
            "statistics": {
                "total_versions": stats.total_versions,
                "first_version_date": stats.first_version_date.isoformat(),
                "latest_version_date": stats.latest_version_date.isoformat(),
                "average_versions_per_day": stats.average_versions_per_day,
                "most_active_day": stats.most_active_day,
                "size_statistics": {
                    "average_size": stats.average_size,
                    "largest_version_size": stats.largest_version_size,
                    "smallest_version_size": stats.smallest_version_size,
                },
                "content_statistics": {
                    "total_lines_added": stats.total_lines_added,
                    "total_lines_deleted": stats.total_lines_deleted,
                    "total_characters_added": stats.total_characters_added,
                    "total_characters_deleted": stats.total_characters_deleted,
                },
            },
            "message": "Version statistics generated successfully",
        }

    except Exception as e:
        logger.error(f"Get version statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Version Management

@router.delete(
    "/versions/{version_id}",
    response_model=Dict[str, Any],
    summary="Delete version",
    description="Delete a specific version",
)
async def delete_version(
    version_id: UUID = ...,
    force: bool = Query(False, description="Force delete (bypass safety checks)"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Delete a specific version.

    Args:
        version_id: Version ID
        force: Whether to force delete
        version_manager: Version manager instance

    Returns:
        Deletion result

    Raises:
        HTTPException: If deletion fails
    """
    try:
        success = await version_manager.delete_version(
            version_id=version_id,
            force=force,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Version not found or cannot be deleted")

        logger.info(f"Version deleted: {version_id}")

        return {
            "success": True,
            "version_id": version_id,
            "message": "Version deleted successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/files/{file_id}/cleanup",
    response_model=Dict[str, Any],
    summary="Cleanup old versions",
    description="Cleanup old versions based on retention policy",
)
async def cleanup_old_versions(
    file_id: UUID = ...,
    keep_count: int = Query(10, ge=1, description="Number of versions to keep"),
    keep_days: int = Query(30, ge=1, description="Number of days to keep versions"),
    version_manager: VersionManager = Depends(get_version_manager),
):
    """Cleanup old versions based on retention policy.

    Args:
        file_id: File ID
        keep_count: Number of recent versions to keep
        keep_days: Number of days to keep versions
        version_manager: Version manager instance

    Returns:
        Cleanup result

    Raises:
        HTTPException: If cleanup fails
    """
    try:
        result = await version_manager.cleanup_old_versions(
            file_id=file_id,
            keep_count=keep_count,
            keep_days=keep_days,
        )

        logger.info(f"Version cleanup completed for file {file_id}: {result.deleted_count} versions deleted")

        return {
            "success": True,
            "cleanup": {
                "deleted_count": result.deleted_count,
                "kept_count": result.kept_count,
                "criteria": {
                    "keep_count": keep_count,
                    "keep_days": keep_days,
                },
            },
            "message": f"Cleaned up {result.deleted_count} old versions",
        }

    except Exception as e:
        logger.error(f"Cleanup old versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
