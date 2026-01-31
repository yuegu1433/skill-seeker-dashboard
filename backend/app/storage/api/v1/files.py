"""Files API endpoints.

This module provides REST API endpoints for file operations including
upload, download, delete, list, and metadata management.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session

from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.schemas.file_operations import (
    FileUploadResponse,
    FileDownloadResponse,
    FileDeleteResponse,
    FileListResponse,
    FileMoveResponse,
    FileInfoResponse,
)
from backend.app.storage.schemas.storage_config import StorageConfig
from backend.app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/files", tags=["files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload a file",
    description="Upload a file to the storage system",
)
async def upload_file(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="Destination file path"),
    content_type: Optional[str] = Query(None, description="File content type"),
    file: UploadFile = File(..., description="File to upload"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Upload a file to the storage system.

    Args:
        skill_id: Target skill ID
        file_path: Destination path for the file
        content_type: Optional content type override
        file: File to upload
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        FileUploadResponse with upload result

    Raises:
        HTTPException: If upload fails
    """
    try:
        # Read file data
        file_data = await file.read()

        # Create upload request
        from backend.app.storage.schemas.file_operations import FileUploadRequest

        upload_request = FileUploadRequest(
            skill_id=skill_id,
            file_path=file_path,
            content_type=content_type or file.content_type,
        )

        # Upload file
        result = await storage_manager.upload_file(upload_request, file_data)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)

        logger.info(
            f"File uploaded: skill={skill_id}, path={file_path}, size={result.file_size}"
        )

        return FileUploadResponse(
            success=True,
            file_path=result.file_path,
            file_size=result.file_size,
            checksum=result.checksum,
            message="File uploaded successfully",
        )

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/download",
    response_model=FileDownloadResponse,
    summary="Download a file",
    description="Download a file from the storage system",
)
async def download_file(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Download a file from the storage system.

    Args:
        skill_id: Skill ID
        file_path: File path
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        FileDownloadResponse with download URL

    Raises:
        HTTPException: If file not found or download fails
    """
    try:
        # Create download request
        from backend.app.storage.schemas.file_operations import FileDownloadRequest

        download_request = FileDownloadRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        # Download file
        result = await storage_manager.download_file(download_request)

        if not result.success:
            raise HTTPException(status_code=404, detail=result.error_message)

        logger.info(f"File download initiated: skill={skill_id}, path={file_path}")

        return FileDownloadResponse(
            success=True,
            file_path=result.file_path,
            download_url=result.download_url,
            expires_at=result.expires_at,
            message="Download URL generated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/delete",
    response_model=FileDeleteResponse,
    summary="Delete a file",
    description="Delete a file from the storage system",
)
async def delete_file(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Delete a file from the storage system.

    Args:
        skill_id: Skill ID
        file_path: File path
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        FileDeleteResponse with deletion result

    Raises:
        HTTPException: If file not found or deletion fails
    """
    try:
        # Create delete request
        from backend.app.storage.schemas.file_operations import FileDeleteRequest

        delete_request = FileDeleteRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        # Delete file
        result = await storage_manager.delete_file(delete_request)

        if not result.success:
            raise HTTPException(status_code=404, detail=result.error_message)

        logger.info(f"File deleted: skill={skill_id}, path={file_path}")

        return FileDeleteResponse(
            success=True,
            file_path=result.file_path,
            message="File deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/list",
    response_model=FileListResponse,
    summary="List files",
    description="List files in a skill's storage",
)
async def list_files(
    skill_id: UUID = Path(..., description="Skill ID"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of files to return"),
    offset: int = Query(0, ge=0, description="Number of files to skip"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """List files in a skill's storage.

    Args:
        skill_id: Skill ID
        limit: Maximum number of files to return
        offset: Number of files to skip
        file_type: Optional file type filter
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        FileListResponse with file list

    Raises:
        HTTPException: If skill not found or operation fails
    """
    try:
        # Create list request
        from backend.app.storage.schemas.file_operations import FileListRequest

        list_request = FileListRequest(
            skill_id=skill_id,
            limit=limit,
            offset=offset,
            file_type=file_type,
        )

        # List files
        result = await storage_manager.list_files(list_request)

        logger.info(
            f"Files listed: skill={skill_id}, count={len(result.files)}, "
            f"total={result.total}"
        )

        return FileListResponse(
            success=True,
            files=result.files,
            total=result.total,
            has_more=result.has_more,
            message="Files retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/move",
    response_model=FileMoveResponse,
    summary="Move a file",
    description="Move or rename a file within the storage system",
)
async def move_file(
    skill_id: UUID = Path(..., description="Skill ID"),
    source_path: str = Query(..., description="Source file path"),
    target_path: str = Query(..., description="Target file path"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Move or rename a file within the storage system.

    Args:
        skill_id: Skill ID
        source_path: Source file path
        target_path: Target file path
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        FileMoveResponse with move result

    Raises:
        HTTPException: If file not found or move fails
    """
    try:
        # Create move request
        from backend.app.storage.schemas.file_operations import FileMoveRequest

        move_request = FileMoveRequest(
            skill_id=skill_id,
            source_path=source_path,
            target_path=target_path,
        )

        # Move file
        result = await storage_manager.move_file(move_request)

        if not result.success:
            raise HTTPException(status_code=404, detail=result.error_message)

        logger.info(
            f"File moved: skill={skill_id}, from={source_path}, to={target_path}"
        )

        return FileMoveResponse(
            success=True,
            source_path=result.source_path,
            target_path=result.target_path,
            message="File moved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File move failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/info",
    response_model=FileInfoResponse,
    summary="Get file information",
    description="Get detailed information about a file",
)
async def get_file_info(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Get detailed information about a file.

    Args:
        skill_id: Skill ID
        file_path: File path
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        FileInfoResponse with file information

    Raises:
        HTTPException: If file not found
    """
    try:
        # Get file info
        file_info = await storage_manager.get_file_info(skill_id, file_path)

        logger.info(f"File info retrieved: skill={skill_id}, path={file_path}")

        return FileInfoResponse(
            success=True,
            file_info=file_info,
            message="File information retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file info failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/stats",
    summary="Get skill storage statistics",
    description="Get storage statistics for a skill",
)
async def get_skill_stats(
    skill_id: UUID = Path(..., description="Skill ID"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Get storage statistics for a skill.

    Args:
        skill_id: Skill ID
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        Dictionary with storage statistics

    Raises:
        HTTPException: If skill not found
    """
    try:
        # Get skill stats
        stats = await storage_manager.get_skill_stats(skill_id)

        logger.info(f"Skill stats retrieved: skill={skill_id}")

        return {
            "success": True,
            "stats": stats,
            "message": "Statistics retrieved successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get skill stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/verify",
    summary="Verify file integrity",
    description="Verify the integrity of a file using checksum",
)
async def verify_file_integrity(
    skill_id: UUID = Path(..., description="Skill ID"),
    file_path: str = Query(..., description="File path"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Verify the integrity of a file using checksum.

    Args:
        skill_id: Skill ID
        file_path: File path
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        Dictionary with verification result

    Raises:
        HTTPException: If file not found or verification fails
    """
    try:
        # Verify file integrity
        is_valid = await storage_manager.verify_file_integrity(skill_id, file_path)

        logger.info(
            f"File integrity verified: skill={skill_id}, path={file_path}, "
            f"valid={is_valid}"
        )

        return {
            "success": True,
            "file_path": file_path,
            "is_valid": is_valid,
            "message": "File integrity verified successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File integrity verification failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/prepare",
    summary="Prepare storage for skill",
    description="Prepare storage bucket and structure for a skill",
)
async def prepare_skill_storage(
    skill_id: UUID = Path(..., description="Skill ID"),
    storage_manager: SkillStorageManager = Depends(get_storage_manager),
    db: Session = Depends(get_db),
):
    """Prepare storage bucket and structure for a skill.

    Args:
        skill_id: Skill ID
        storage_manager: Storage manager dependency
        db: Database session

    Returns:
        Dictionary with preparation result

    Raises:
        HTTPException: If preparation fails
    """
    try:
        # Prepare skill storage
        result = await storage_manager.ensure_skill_storage(skill_id)

        logger.info(f"Skill storage prepared: skill={skill_id}")

        return {
            "success": result,
            "skill_id": str(skill_id),
            "message": "Storage prepared successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prepare skill storage failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dependency to get storage manager
def get_storage_manager() -> SkillStorageManager:
    """Get storage manager instance.

    Returns:
        SkillStorageManager instance
    """
    # In a real application, this would be injected via FastAPI's dependency system
    # For now, we'll return a placeholder
    # This should be replaced with actual dependency injection
    from backend.app.storage.manager import SkillStorageManager
    from backend.app.storage.client import MinIOClient
    from backend.app.storage.schemas.storage_config import StorageConfig, MinIOConfig

    # This is a placeholder - in production, use proper DI
    raise NotImplementedError(
        "Storage manager dependency not configured. "
        "Configure FastAPI dependency injection for SkillStorageManager."
    )
