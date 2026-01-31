"""Versions API endpoints.

This module provides REST API endpoints for file version control operations
including version creation, listing, restoration, comparison, and deletion.
"""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.app.storage.versioning import (
    VersionManager,
    VersioningError,
    VersionNotFoundError,
    VersionLimitExceededError,
    VersionRestoreError,
)
from backend.app.storage.schemas.file_operations import (
    FileVersionCreateRequest,
    FileVersionRestoreRequest,
)
from backend.app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/versions", tags=["versions"])


@router.post(
    "/create",
    summary="Create a new version",
    description="Create a new version of an existing file",
)
async def create_version(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    comment: Optional[str] = Query(None, description="Version comment"),
    file: UploadFile = File(..., description="File data for the new version"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Create a new version of a file.

    Args:
        skill_id: Skill ID
        file_path: File path
        comment: Optional version comment
        file: File data for the new version
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Version creation result with version ID

    Raises:
        HTTPException: If version creation fails
    """
    try:
        # Read file data
        file_data = await file.read()

        # Create version request
        version_request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
            comment=comment,
            metadata={"content_type": file.content_type},
        )

        # Create version
        version_id = await version_manager.create_version(version_request, file_data)

        logger.info(
            f"Version created: skill={skill_id}, path={file_path}, "
            f"version_id={version_id}"
        )

        return {
            "success": True,
            "version_id": version_id,
            "file_path": file_path,
            "comment": comment,
            "message": "Version created successfully",
        }

    except VersionNotFoundError as e:
        logger.error(f"Create version failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except VersionLimitExceededError as e:
        logger.error(f"Create version failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except VersioningError as e:
        logger.error(f"Create version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Create version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/list",
    summary="List file versions",
    description="List all versions of a file",
)
async def list_versions(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """List all versions of a file.

    Args:
        skill_id: Skill ID
        file_path: File path
        version_manager: Version manager dependency
        db: Database session

    Returns:
        List of file versions

    Raises:
        HTTPException: If file not found or operation fails
    """
    try:
        # List versions
        versions = await version_manager.list_versions(skill_id, file_path)

        # Convert to response format
        version_list = []
        for version in versions:
            version_list.append(
                {
                    "id": str(version.id),
                    "version_id": version.version_id,
                    "version_number": version.version_number,
                    "file_size": version.file_size,
                    "checksum": version.checksum,
                    "comment": version.comment,
                    "created_at": version.created_at.isoformat(),
                    "created_by": version.created_by,
                    "is_latest": version.is_latest,
                }
            )

        logger.info(
            f"Versions listed: skill={skill_id}, path={file_path}, "
            f"count={len(version_list)}"
        )

        return {
            "success": True,
            "file_path": file_path,
            "versions": version_list,
            "total": len(version_list),
            "message": "Versions retrieved successfully",
        }

    except VersionNotFoundError as e:
        logger.error(f"List versions failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except VersioningError as e:
        logger.error(f"List versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"List versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/restore",
    summary="Restore file to version",
    description="Restore a file to a specific version",
)
async def restore_version(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    version_id: str = Query(..., description="Version ID to restore"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Restore a file to a specific version.

    Args:
        skill_id: Skill ID
        file_path: File path
        version_id: Version ID to restore
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Version restore result

    Raises:
        HTTPException: If file or version not found or restore fails
    """
    try:
        # Create restore request
        restore_request = FileVersionRestoreRequest(
            skill_id=skill_id,
            file_path=file_path,
            version_id=version_id,
        )

        # Restore version
        result = await version_manager.restore_version(restore_request)

        if not result:
            raise HTTPException(status_code=500, detail="Restore operation failed")

        logger.info(
            f"Version restored: skill={skill_id}, path={file_path}, "
            f"version_id={version_id}"
        )

        return {
            "success": True,
            "file_path": file_path,
            "version_id": version_id,
            "message": "File restored to specified version successfully",
        }

    except VersionNotFoundError as e:
        logger.error(f"Restore version failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except VersionRestoreError as e:
        logger.error(f"Restore version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except VersioningError as e:
        logger.error(f"Restore version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Restore version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/compare",
    summary="Compare two versions",
    description="Compare two versions of a file and show differences",
)
async def compare_versions(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    version_id_1: str = Query(..., description="First version ID"),
    version_id_2: str = Query(..., description="Second version ID"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Compare two versions of a file.

    Args:
        skill_id: Skill ID
        file_path: File path
        version_id_1: First version ID
        version_id_2: Second version ID
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Comparison results

    Raises:
        HTTPException: If file or versions not found or comparison fails
    """
    try:
        # Compare versions
        comparison = await version_manager.compare_versions(
            skill_id, file_path, version_id_1, version_id_2
        )

        logger.info(
            f"Versions compared: skill={skill_id}, path={file_path}, "
            f"version1={version_id_1}, version2={version_id_2}"
        )

        return {
            "success": True,
            "comparison": comparison,
            "message": "Versions compared successfully",
        }

    except VersionNotFoundError as e:
        logger.error(f"Compare versions failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except VersioningError as e:
        logger.error(f"Compare versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Compare versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/delete",
    summary="Delete a version",
    description="Delete a specific version of a file",
)
async def delete_version(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    version_id: str = Query(..., description="Version ID to delete"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Delete a specific version of a file.

    Args:
        skill_id: Skill ID
        file_path: File path
        version_id: Version ID to delete
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Version deletion result

    Raises:
        HTTPException: If file or version not found or deletion fails
    """
    try:
        # Delete version
        result = await version_manager.delete_version(skill_id, file_path, version_id)

        if not result:
            raise HTTPException(status_code=500, detail="Delete operation failed")

        logger.info(
            f"Version deleted: skill={skill_id}, path={file_path}, "
            f"version_id={version_id}"
        )

        return {
            "success": True,
            "file_path": file_path,
            "version_id": version_id,
            "message": "Version deleted successfully",
        }

    except VersionNotFoundError as e:
        logger.error(f"Delete version failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except VersioningError as e:
        logger.error(f"Delete version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Delete version failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/cleanup",
    summary="Clean up old versions",
    description="Clean up old versions based on retention policy",
)
async def cleanup_old_versions(
    skill_id: Optional[UUID] = Query(None, description="Optional skill ID to filter cleanup"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Clean up old versions based on retention policy.

    Args:
        skill_id: Optional skill ID to filter cleanup
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Cleanup result with number of versions cleaned up

    Raises:
        HTTPException: If cleanup fails
    """
    try:
        # Clean up old versions
        deleted_count = await version_manager.cleanup_old_versions(skill_id)

        logger.info(
            f"Cleanup completed: skill={skill_id}, deleted_count={deleted_count}"
        )

        return {
            "success": True,
            "skill_id": str(skill_id) if skill_id else None,
            "deleted_count": deleted_count,
            "message": f"Cleaned up {deleted_count} old versions",
        }

    except VersioningError as e:
        logger.error(f"Cleanup versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Cleanup versions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics",
    summary="Get version statistics",
    description="Get version control statistics",
)
async def get_version_statistics(
    skill_id: Optional[UUID] = Query(None, description="Optional skill ID to filter statistics"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Get version control statistics.

    Args:
        skill_id: Optional skill ID to filter statistics
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Version statistics

    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        # Get statistics
        stats = await version_manager.get_version_statistics(skill_id)

        logger.info(f"Version statistics retrieved: skill={skill_id}")

        return {
            "success": True,
            "skill_id": str(skill_id) if skill_id else None,
            "statistics": stats,
            "message": "Statistics retrieved successfully",
        }

    except Exception as e:
        logger.error(f"Get version statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{version_id}/info",
    summary="Get version information",
    description="Get detailed information about a specific version",
)
async def get_version_info(
    version_id: str = Path(..., description="Version ID"),
    skill_id: Optional[UUID] = Query(None, description="Optional skill ID"),
    file_path: Optional[str] = Query(None, description="Optional file path"),
    version_manager: VersionManager = Depends(get_version_manager),
    db: Session = Depends(get_db),
):
    """Get detailed information about a specific version.

    Args:
        version_id: Version ID
        skill_id: Optional skill ID
        file_path: Optional file path
        version_manager: Version manager dependency
        db: Database session

    Returns:
        Version information

    Raises:
        HTTPException: If version not found or retrieval fails
    """
    try:
        # If skill_id and file_path provided, get from list
        if skill_id and file_path:
            versions = await version_manager.list_versions(skill_id, file_path)
            version = next((v for v in versions if v.version_id == version_id), None)

            if not version:
                raise HTTPException(status_code=404, detail="Version not found")

            version_info = {
                "id": str(version.id),
                "version_id": version.version_id,
                "version_number": version.version_number,
                "file_size": version.file_size,
                "checksum": version.checksum,
                "comment": version.comment,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "is_latest": version.is_latest,
            }
        else:
            # Without skill_id and file_path, we can't retrieve version info
            # This would need to be implemented based on specific requirements
            raise HTTPException(
                status_code=400,
                detail="skill_id and file_path are required to retrieve version info",
            )

        logger.info(f"Version info retrieved: version_id={version_id}")

        return {
            "success": True,
            "version_info": version_info,
            "message": "Version information retrieved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get version info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dependency to get version manager
def get_version_manager() -> VersionManager:
    """Get version manager instance.

    Returns:
        VersionManager instance
    """
    # In a real application, this would be injected via FastAPI's dependency system
    # For now, we'll return a placeholder
    # This should be replaced with actual dependency injection
    from backend.app.storage.versioning import VersionManager
    from backend.app.storage.manager import SkillStorageManager
    from backend.app.storage.client import MinIOClient
    from backend.app.database.session import get_db

    # This is a placeholder - in production, use proper DI
    raise NotImplementedError(
        "Version manager dependency not configured. "
        "Configure FastAPI dependency injection for VersionManager."
    )
