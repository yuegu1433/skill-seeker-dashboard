"""File Management API.

This module provides REST API endpoints for file operations including
file CRUD, search, filtering, permissions, and batch operations.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import asyncio

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Path, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Import managers and services
from app.file.manager import FileManager
from app.file.services.upload_service import UploadService, UploadMode
from app.file.services.download_service import DownloadService
from app.file.batch_processor import BatchProcessor
from app.file.schemas.file_operations import (
    FileCreate,
    FileResponse,
    FileUpdate,
    FileDeleteResponse,
    FileListResponse,
    FileSearchRequest,
    FilePermissionRequest,
    BatchOperationRequest,
)
from app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="", tags=["files"])


# Dependency injection
async def get_file_manager(db: AsyncSession = Depends(get_db)) -> FileManager:
    """Get FileManager instance."""
    return FileManager(db_session=db)


async def get_upload_service(file_manager: FileManager = Depends(get_file_manager)) -> UploadService:
    """Get UploadService instance."""
    return UploadService(
        db_session=file_manager.db_session,
        file_manager=file_manager,
    )


async def get_download_service(file_manager: FileManager = Depends(get_file_manager)) -> DownloadService:
    """Get DownloadService instance."""
    return DownloadService(
        db_session=file_manager.db_session,
        file_manager=file_manager,
    )


async def get_batch_processor(file_manager: FileManager = Depends(get_file_manager)) -> BatchProcessor:
    """Get BatchProcessor instance."""
    return BatchProcessor(
        db_session=file_manager.db_session,
    )


# File CRUD Operations

@router.post(
    "/",
    response_model=FileResponse,
    summary="Create a new file",
    description="Create a new file in the file management system",
)
async def create_file(
    file_data: FileCreate,
    file_manager: FileManager = Depends(get_file_manager),
):
    """Create a new file.

    Args:
        file_data: File creation data
        file_manager: File manager instance

    Returns:
        FileResponse with created file information

    Raises:
        HTTPException: If file creation fails
    """
    try:
        result = await file_manager.create_file(file_data)

        logger.info(f"File created: {result.id} - {result.filename}")

        return FileResponse(
            success=True,
            file=result,
            message="File created successfully",
        )

    except Exception as e:
        logger.error(f"File creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{file_id}",
    response_model=FileResponse,
    summary="Get file information",
    description="Retrieve file information by ID",
)
async def get_file(
    file_id: UUID = Path(..., description="File ID"),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Get file information by ID.

    Args:
        file_id: File ID
        file_manager: File manager instance

    Returns:
        FileResponse with file information

    Raises:
        HTTPException: If file not found
    """
    try:
        result = await file_manager.get_file(file_id)

        if not result:
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(
            success=True,
            file=result,
            message="File retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/{file_id}",
    response_model=FileResponse,
    summary="Update file",
    description="Update file metadata and content",
)
async def update_file(
    file_id: UUID = Path(..., description="File ID"),
    file_data: FileUpdate = ...,
    file_manager: FileManager = Depends(get_file_manager),
):
    """Update file information.

    Args:
        file_id: File ID
        file_data: File update data
        file_manager: File manager instance

    Returns:
        FileResponse with updated file information

    Raises:
        HTTPException: If file update fails
    """
    try:
        result = await file_manager.update_file(file_id, file_data)

        logger.info(f"File updated: {file_id}")

        return FileResponse(
            success=True,
            file=result,
            message="File updated successfully",
        )

    except Exception as e:
        logger.error(f"File update failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/{file_id}",
    response_model=FileDeleteResponse,
    summary="Delete file",
    description="Delete a file from the system",
)
async def delete_file(
    file_id: UUID = Path(..., description="File ID"),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Delete a file.

    Args:
        file_id: File ID
        file_manager: File manager instance

    Returns:
        FileDeleteResponse with deletion result

    Raises:
        HTTPException: If file deletion fails
    """
    try:
        success = await file_manager.delete_file(file_id)

        if not success:
            raise HTTPException(status_code=404, detail="File not found or cannot be deleted")

        logger.info(f"File deleted: {file_id}")

        return FileDeleteResponse(
            success=True,
            file_id=file_id,
            message="File deleted successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Listing and Search

@router.get(
    "/",
    response_model=FileListResponse,
    summary="List files",
    description="List files with optional filtering and pagination",
)
async def list_files(
    folder_id: Optional[UUID] = Query(None, description="Folder ID to list files from"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    search: Optional[str] = Query(None, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    file_manager: FileManager = Depends(get_file_manager),
):
    """List files with optional filtering.

    Args:
        folder_id: Optional folder ID to filter by
        file_type: Optional file type filter
        tags: Optional list of tags to filter by
        search: Optional search query
        page: Page number (1-indexed)
        size: Page size
        sort_by: Sort field
        sort_order: Sort order (asc or desc)
        file_manager: File manager instance

    Returns:
        FileListResponse with files list
    """
    try:
        filters = {}
        if folder_id:
            filters["folder_id"] = folder_id
        if file_type:
            filters["file_type"] = file_type
        if tags:
            filters["tags"] = tags

        result = await file_manager.list_files(
            filters=filters,
            search=search,
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        return FileListResponse(
            success=True,
            files=result.files,
            total=result.total,
            page=result.page,
            size=result.size,
            pages=result.pages,
            message="Files retrieved successfully",
        )

    except Exception as e:
        logger.error(f"File listing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/search",
    response_model=FileListResponse,
    summary="Search files",
    description="Advanced file search with multiple criteria",
)
async def search_files(
    search_request: FileSearchRequest,
    file_manager: FileManager = Depends(get_file_manager),
):
    """Advanced file search.

    Args:
        search_request: Search request with criteria
        file_manager: File manager instance

    Returns:
        FileListResponse with search results
    """
    try:
        result = await file_manager.search_files(search_request)

        return FileListResponse(
            success=True,
            files=result.files,
            total=result.total,
            page=result.page,
            size=result.size,
            pages=result.pages,
            message="Search completed successfully",
        )

    except Exception as e:
        logger.error(f"File search failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Upload

@router.post(
    "/upload",
    response_model=Dict[str, Any],
    summary="Upload a file",
    description="Upload a file to the system",
)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="File to upload"),
    folder_id: Optional[UUID] = Query(None, description="Target folder ID"),
    overwrite: bool = Query(False, description="Overwrite existing file"),
    mode: str = Query("normal", regex="^(normal|chunked|resumable)$", description="Upload mode"),
    chunk_size: Optional[int] = Query(None, description="Chunk size for chunked uploads"),
    upload_service: UploadService = Depends(get_upload_service),
):
    """Upload a file.

    Args:
        background_tasks: Background tasks
        file: File to upload
        folder_id: Optional target folder ID
        overwrite: Whether to overwrite existing file
        mode: Upload mode (normal, chunked, or resumable)
        chunk_size: Optional chunk size for chunked uploads
        upload_service: Upload service instance

    Returns:
        Upload result with file information
    """
    try:
        # Read file data
        file_data = await file.read()

        # Prepare file info
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type or "application/octet-stream",
            "size": len(file_data),
            "folder_id": folder_id,
        }

        # Determine upload mode
        upload_mode = UploadMode.NORMAL
        if mode == "chunked":
            upload_mode = UploadMode.CHUNKED
        elif mode == "resumable":
            upload_mode = UploadMode.RESUMABLE

        # Start upload based on mode
        if upload_mode == UploadMode.NORMAL:
            result = await upload_service.upload_file(
                file_data=file_data,
                file_info=file_info,
                mode=upload_mode,
            )
        else:
            # For chunked/resumable, initiate upload first
            session = await upload_service.initiate_chunked_upload(
                file_info=file_info,
                chunk_size=chunk_size or 1024 * 1024,  # Default 1MB
            )
            result = {
                "upload_id": session.session_id,
                "total_chunks": session.total_chunks,
                "chunk_size": session.chunk_size,
                "status": "initiated",
            }

        logger.info(f"File uploaded: {file.filename} ({len(file_data)} bytes)")

        return {
            "success": True,
            "result": result,
            "message": "File uploaded successfully",
        }

    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/upload/{upload_id}/chunk/{chunk_index}",
    response_model=Dict[str, Any],
    summary="Upload a chunk",
    description="Upload a chunk for chunked upload",
)
async def upload_chunk(
    upload_id: str = Path(..., description="Upload ID"),
    chunk_index: int = Path(..., ge=0, description="Chunk index"),
    chunk_data: bytes = File(..., description="Chunk data"),
    upload_service: UploadService = Depends(get_upload_service),
):
    """Upload a chunk for chunked upload.

    Args:
        upload_id: Upload ID
        chunk_index: Chunk index
        chunk_data: Chunk data
        upload_service: Upload service instance

    Returns:
        Chunk upload result
    """
    try:
        result = await upload_service.upload_chunk(
            upload_id=upload_id,
            chunk_index=chunk_index,
            chunk_data=chunk_data,
        )

        return {
            "success": True,
            "result": result,
            "message": "Chunk uploaded successfully",
        }

    except Exception as e:
        logger.error(f"Chunk upload failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/upload/{upload_id}/complete",
    response_model=Dict[str, Any],
    summary="Complete upload",
    description="Complete a chunked upload",
)
async def complete_upload(
    upload_id: str = Path(..., description="Upload ID"),
    upload_service: UploadService = Depends(get_upload_service),
):
    """Complete a chunked upload.

    Args:
        upload_id: Upload ID
        upload_service: Upload service instance

    Returns:
        Upload completion result
    """
    try:
        result = await upload_service.complete_upload(upload_id)

        return {
            "success": True,
            "result": result,
            "message": "Upload completed successfully",
        }

    except Exception as e:
        logger.error(f"Upload completion failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# File Download

@router.get(
    "/{file_id}/download",
    summary="Download a file",
    description="Download a file from the system",
)
async def download_file(
    file_id: UUID = Path(..., description="File ID"),
    download_service: DownloadService = Depends(get_download_service),
):
    """Download a file.

    Args:
        file_id: File ID
        download_service: Download service instance

    Returns:
        File stream response

    Raises:
        HTTPException: If file download fails
    """
    try:
        result = await download_service.download_file(file_id)

        # Create streaming response
        return StreamingResponse(
            iter([result["data"]]),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f'attachment; filename="{result["filename"]}"',
                "Content-Length": str(result["size"]),
                "Content-Type": result.get("content_type", "application/octet-stream"),
            },
        )

    except Exception as e:
        logger.error(f"File download failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{file_id}/stream",
    summary="Stream a file",
    description="Stream a file with progress tracking",
)
async def stream_file(
    file_id: UUID = Path(..., description="File ID"),
    download_service: DownloadService = Depends(get_download_service),
):
    """Stream a file with progress tracking.

    Args:
        file_id: File ID
        download_service: Download service instance

    Returns:
        Streaming response
    """
    try:
        async def file_generator():
            async for chunk in download_service.stream_file(file_id):
                yield chunk

        return StreamingResponse(
            file_generator(),
            media_type="application/octet-stream",
            headers={
                "Content-Type": "application/octet-stream",
            },
        )

    except Exception as e:
        logger.error(f"File streaming failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Progress Tracking

@router.get(
    "/upload/{upload_id}/progress",
    response_model=Dict[str, Any],
    summary="Get upload progress",
    description="Get upload progress information",
)
async def get_upload_progress(
    upload_id: str = Path(..., description="Upload ID"),
    upload_service: UploadService = Depends(get_upload_service),
):
    """Get upload progress.

    Args:
        upload_id: Upload ID
        upload_service: Upload service instance

    Returns:
        Upload progress information
    """
    try:
        progress = upload_service.get_upload_progress(upload_id)

        return {
            "success": True,
            "progress": progress.to_dict(),
        }

    except Exception as e:
        logger.error(f"Get upload progress failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/download/{download_id}/progress",
    response_model=Dict[str, Any],
    summary="Get download progress",
    description="Get download progress information",
)
async def get_download_progress(
    download_id: str = Path(..., description="Download ID"),
    download_service: DownloadService = Depends(get_download_service),
):
    """Get download progress.

    Args:
        download_id: Download ID
        download_service: Download service instance

    Returns:
        Download progress information
    """
    try:
        progress = download_service.get_download_progress(download_id)

        return {
            "success": True,
            "progress": progress.to_dict(),
        }

    except Exception as e:
        logger.error(f"Get download progress failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))


# Batch Operations

@router.post(
    "/batch",
    response_model=Dict[str, Any],
    summary="Batch operation",
    description="Perform batch operations on multiple files",
)
async def batch_operation(
    operation_request: BatchOperationRequest,
    background_tasks: BackgroundTasks,
    batch_processor: BatchProcessor = Depends(get_batch_processor),
):
    """Perform batch operations on files.

    Args:
        operation_request: Batch operation request
        background_tasks: Background tasks
        batch_processor: Batch processor instance

    Returns:
        Batch operation result
    """
    try:
        # Create batch job
        job = await batch_processor.create_batch_job(
            operation_type=operation_request.operation_type,
            file_ids=operation_request.file_ids,
            parameters=operation_request.parameters,
        )

        # Start processing in background
        background_tasks.add_task(
            batch_processor.process_batch_job,
            job.job_id,
        )

        return {
            "success": True,
            "job_id": job.job_id,
            "status": job.status.value,
            "message": "Batch operation started",
        }

    except Exception as e:
        logger.error(f"Batch operation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/batch/{job_id}",
    response_model=Dict[str, Any],
    summary="Get batch job status",
    description="Get batch job status and progress",
)
async def get_batch_status(
    job_id: str = Path(..., description="Batch job ID"),
    batch_processor: BatchProcessor = Depends(get_batch_processor),
):
    """Get batch job status.

    Args:
        job_id: Batch job ID
        batch_processor: Batch processor instance

    Returns:
        Batch job status
    """
    try:
        job = await batch_processor.get_batch_job(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Batch job not found")

        return {
            "success": True,
            "job": {
                "job_id": job.job_id,
                "operation_type": job.operation_type.value,
                "status": job.status.value,
                "progress": job.progress.to_dict(),
                "created_at": job.created_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get batch status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/batch/{job_id}",
    response_model=Dict[str, Any],
    summary="Cancel batch job",
    description="Cancel a running batch job",
)
async def cancel_batch_job(
    job_id: str = Path(..., description="Batch job ID"),
    batch_processor: BatchProcessor = Depends(get_batch_processor),
):
    """Cancel a batch job.

    Args:
        job_id: Batch job ID
        batch_processor: Batch processor instance

    Returns:
        Cancellation result
    """
    try:
        result = await batch_processor.cancel_batch_job(job_id)

        return {
            "success": result,
            "message": "Batch job cancelled" if result else "Batch job not found or cannot be cancelled",
        }

    except Exception as e:
        logger.error(f"Cancel batch job failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Permissions

@router.post(
    "/{file_id}/permissions",
    response_model=Dict[str, Any],
    summary="Set file permissions",
    description="Set file permissions and access control",
)
async def set_file_permissions(
    file_id: UUID = Path(..., description="File ID"),
    permission_request: FilePermissionRequest = ...,
    file_manager: FileManager = Depends(get_file_manager),
):
    """Set file permissions.

    Args:
        file_id: File ID
        permission_request: Permission request
        file_manager: File manager instance

    Returns:
        Permission setting result
    """
    try:
        result = await file_manager.set_file_permissions(
            file_id=file_id,
            permissions=permission_request.permissions,
            user_id=permission_request.user_id,
        )

        return {
            "success": True,
            "result": result,
            "message": "Permissions set successfully",
        }

    except Exception as e:
        logger.error(f"Set file permissions failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/{file_id}/permissions",
    response_model=Dict[str, Any],
    summary="Get file permissions",
    description="Get file permissions and access control",
)
async def get_file_permissions(
    file_id: UUID = Path(..., description="File ID"),
    file_manager: FileManager = Depends(get_file_manager),
):
    """Get file permissions.

    Args:
        file_id: File ID
        file_manager: File manager instance

    Returns:
        File permissions
    """
    try:
        permissions = await file_manager.get_file_permissions(file_id)

        return {
            "success": True,
            "permissions": permissions,
        }

    except Exception as e:
        logger.error(f"Get file permissions failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
