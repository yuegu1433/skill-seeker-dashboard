"""File Preview API.

This module provides REST API endpoints for file preview generation including
image preview, document preview, code highlighting, and thumbnail generation.
"""

import logging
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
import base64

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Import preview manager and services
from app.file.preview_manager import PreviewManager
from app.file.services.conversion_service import ConversionService
from app.schemas.preview_config import (
    PreviewRequest,
    PreviewResponse,
    ThumbnailRequest,
    ThumbnailResponse,
    PreviewFormat,
)
from app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/preview", tags=["preview"])


# Dependency injection
async def get_preview_manager(db: AsyncSession = Depends(get_db)) -> PreviewManager:
    """Get PreviewManager instance."""
    return PreviewManager(db_session=db)


async def get_conversion_service(db: AsyncSession = Depends(get_db)) -> ConversionService:
    """Get ConversionService instance."""
    return ConversionService(db_session=db)


# Basic Preview Generation

@router.post(
    "/generate",
    response_model=PreviewResponse,
    summary="Generate file preview",
    description="Generate a preview for a file",
)
async def generate_preview(
    request: PreviewRequest = ...,
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Generate a preview for a file.

    Args:
        request: Preview generation request
        preview_manager: Preview manager instance

    Returns:
        Generated preview

    Raises:
        HTTPException: If preview generation fails
    """
    try:
        preview = await preview_manager.generate_preview(
            file_id=request.file_id,
            format=request.format,
            options=request.options,
        )

        return PreviewResponse(
            success=True,
            preview=preview,
            message="Preview generated successfully",
        )

    except Exception as e:
        logger.error(f"Generate preview failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/files/{file_id}",
    response_model=PreviewResponse,
    summary="Get file preview",
    description="Get an existing preview for a file",
)
async def get_file_preview(
    file_id: UUID = ...,
    format: PreviewFormat = Query(PreviewFormat.AUTO, description="Preview format"),
    refresh: bool = Query(False, description="Regenerate preview"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get a preview for a file.

    Args:
        file_id: File ID
        format: Preview format
        refresh: Whether to regenerate preview
        preview_manager: Preview manager instance

    Returns:
        File preview

    Raises:
        HTTPException: If preview not found
    """
    try:
        preview = await preview_manager.get_file_preview(
            file_id=file_id,
            format=format,
            refresh=refresh,
        )

        if not preview:
            raise HTTPException(status_code=404, detail="Preview not found")

        return PreviewResponse(
            success=True,
            preview=preview,
            message="Preview retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Image Preview

@router.get(
    "/files/{file_id}/image",
    summary="Get image preview",
    description="Get an image preview of a file",
)
async def get_image_preview(
    file_id: UUID = ...,
    width: Optional[int] = Query(None, description="Image width"),
    height: Optional[int] = Query(None, description="Image height"),
    quality: int = Query(85, ge=1, le=100, description="Image quality"),
    format: str = Query("jpeg", regex="^(jpeg|png|webp)$", description="Output format"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get an image preview of a file.

    Args:
        file_id: File ID
        width: Optional image width
        height: Optional image height
        quality: Image quality (1-100)
        format: Output format
        preview_manager: Preview manager instance

    Returns:
        Image stream response

    Raises:
        HTTPException: If image preview fails
    """
    try:
        preview_data = await preview_manager.get_image_preview(
            file_id=file_id,
            width=width,
            height=height,
            quality=quality,
            format=format,
        )

        if not preview_data:
            raise HTTPException(status_code=404, detail="Image preview not found")

        # Return as streaming response
        media_type = f"image/{format}"
        return Response(
            content=preview_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="preview_{file_id}.{format}"',
                "Cache-Control": "public, max-age=3600",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get image preview failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/files/{file_id}/thumbnail",
    response_model=ThumbnailResponse,
    summary="Generate thumbnail",
    description="Generate a thumbnail for a file",
)
async def generate_thumbnail(
    file_id: UUID = ...,
    request: ThumbnailRequest = ...,
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Generate a thumbnail for a file.

    Args:
        file_id: File ID
        request: Thumbnail generation request
        preview_manager: Preview manager instance

    Returns:
        Generated thumbnail

    Raises:
        HTTPException: If thumbnail generation fails
    """
    try:
        thumbnail = await preview_manager.generate_thumbnail(
            file_id=file_id,
            size=request.size,
            format=request.format,
            quality=request.quality,
        )

        return ThumbnailResponse(
            success=True,
            thumbnail=thumbnail,
            message="Thumbnail generated successfully",
        )

    except Exception as e:
        logger.error(f"Generate thumbnail failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/files/{file_id}/thumbnail",
    summary="Get file thumbnail",
    description="Get an existing thumbnail for a file",
)
async def get_file_thumbnail(
    file_id: UUID = ...,
    size: str = Query("200x200", regex="^\d+x\d+$", description="Thumbnail size"),
    format: str = Query("jpeg", regex="^(jpeg|png|webp)$", description="Output format"),
    refresh: bool = Query(False, description="Regenerate thumbnail"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get a thumbnail for a file.

    Args:
        file_id: File ID
        size: Thumbnail size (WxH)
        format: Output format
        refresh: Whether to regenerate
        preview_manager: Preview manager instance

    Returns:
        Thumbnail image stream

    Raises:
        HTTPException: If thumbnail not found
    """
    try:
        # Parse size
        width, height = map(int, size.split('x'))

        thumbnail_data = await preview_manager.get_thumbnail(
            file_id=file_id,
            width=width,
            height=height,
            format=format,
            refresh=refresh,
        )

        if not thumbnail_data:
            raise HTTPException(status_code=404, detail="Thumbnail not found")

        # Return as streaming response
        media_type = f"image/{format}"
        return Response(
            content=thumbnail_data,
            media_type=media_type,
            headers={
                "Content-Disposition": f'inline; filename="thumbnail_{file_id}_{size}.{format}"',
                "Cache-Control": "public, max-age=86400",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file thumbnail failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Document Preview

@router.get(
    "/files/{file_id}/document",
    summary="Get document preview",
    description="Get a document preview (HTML/PDF text)",
)
async def get_document_preview(
    file_id: UUID = ...,
    format: str = Query("html", regex="^(html|text)$", description="Preview format"),
    page: int = Query(1, ge=1, description="Page number for multi-page documents"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get a document preview.

    Args:
        file_id: File ID
        format: Preview format (html or text)
        page: Page number for multi-page documents
        preview_manager: Preview manager instance

    Returns:
        Document preview content

    Raises:
        HTTPException: If document preview fails
    """
    try:
        preview = await preview_manager.get_document_preview(
            file_id=file_id,
            format=format,
            page=page,
        )

        if not preview:
            raise HTTPException(status_code=404, detail="Document preview not found")

        if format == "html":
            return HTMLResponse(content=preview)
        else:
            return PlainTextResponse(content=preview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/files/{file_id}/text",
    summary="Extract text content",
    description="Extract text content from a file",
)
async def extract_text_content(
    file_id: UUID = ...,
    encoding: str = Query("utf-8", description="Text encoding"),
    max_length: Optional[int] = Query(None, description="Maximum text length"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Extract text content from a file.

    Args:
        file_id: File ID
        encoding: Text encoding
        max_length: Maximum text length to extract
        preview_manager: Preview manager instance

    Returns:
        Extracted text content

    Raises:
        HTTPException: If text extraction fails
    """
    try:
        text_content = await preview_manager.extract_text_content(
            file_id=file_id,
            encoding=encoding,
            max_length=max_length,
        )

        if text_content is None:
            raise HTTPException(status_code=404, detail="Text extraction not available for this file")

        return {
            "success": True,
            "content": text_content,
            "encoding": encoding,
            "truncated": max_length and len(text_content) > max_length,
            "file_id": file_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Extract text content failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Code Preview

@router.get(
    "/files/{file_id}/code",
    summary="Get code preview",
    description="Get a syntax-highlighted code preview",
)
async def get_code_preview(
    file_id: UUID = ...,
    language: Optional[str] = Query(None, description="Programming language"),
    theme: str = Query("github", description="Syntax highlighting theme"),
    line_numbers: bool = Query(True, description="Show line numbers"),
    max_lines: Optional[int] = Query(None, description="Maximum lines to show"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get a syntax-highlighted code preview.

    Args:
        file_id: File ID
        language: Programming language
        theme: Syntax highlighting theme
        line_numbers: Whether to show line numbers
        max_lines: Maximum lines to show
        preview_manager: Preview manager instance

    Returns:
        Code preview with syntax highlighting

    Raises:
        HTTPException: If code preview fails
    """
    try:
        preview = await preview_manager.get_code_preview(
            file_id=file_id,
            language=language,
            theme=theme,
            line_numbers=line_numbers,
            max_lines=max_lines,
        )

        if not preview:
            raise HTTPException(status_code=404, detail="Code preview not available")

        return {
            "success": True,
            "preview": {
                "html_content": preview.html_content,
                "language": preview.language,
                "theme": theme,
                "line_numbers": line_numbers,
                "line_count": preview.line_count,
                "truncated": preview.truncated,
            },
            "file_id": file_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get code preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Video/Audio Preview

@router.get(
    "/files/{file_id}/video",
    summary="Get video preview",
    description="Get video metadata and preview information",
)
async def get_video_preview(
    file_id: UUID = ...,
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get video preview metadata.

    Args:
        file_id: File ID
        preview_manager: Preview manager instance

    Returns:
        Video preview metadata

    Raises:
        HTTPException: If video preview fails
    """
    try:
        preview = await preview_manager.get_video_preview(file_id)

        if not preview:
            raise HTTPException(status_code=404, detail="Video preview not available")

        return {
            "success": True,
            "preview": {
                "duration": preview.duration,
                "width": preview.width,
                "height": preview.height,
                "frame_rate": preview.frame_rate,
                "bitrate": preview.bitrate,
                "codec": preview.codec,
                "thumbnail_available": preview.thumbnail_available,
            },
            "file_id": file_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get video preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/files/{file_id}/audio",
    summary="Get audio preview",
    description="Get audio metadata and waveform data",
)
async def get_audio_preview(
    file_id: UUID = ...,
    include_waveform: bool = Query(False, description="Include waveform data"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get audio preview metadata.

    Args:
        file_id: File ID
        include_waveform: Whether to include waveform data
        preview_manager: Preview manager instance

    Returns:
        Audio preview metadata

    Raises:
        HTTPException: If audio preview fails
    """
    try:
        preview = await preview_manager.get_audio_preview(
            file_id=file_id,
            include_waveform=include_waveform,
        )

        if not preview:
            raise HTTPException(status_code=404, detail="Audio preview not available")

        return {
            "success": True,
            "preview": {
                "duration": preview.duration,
                "sample_rate": preview.sample_rate,
                "channels": preview.channels,
                "bitrate": preview.bitrate,
                "codec": preview.codec,
                "waveform": preview.waveform if include_waveform else None,
            },
            "file_id": file_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get audio preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Format Conversion

@router.post(
    "/convert",
    response_model=Dict[str, Any],
    summary="Convert file format",
    description="Convert a file to a different format",
)
async def convert_file_format(
    source_format: str = Query(..., description="Source file format"),
    target_format: str = Query(..., description="Target file format"),
    quality: Optional[int] = Query(None, description="Conversion quality"),
    conversion_service: ConversionService = Depends(get_conversion_service),
):
    """Convert a file format.

    Args:
        source_format: Source file format
        target_format: Target file format
        quality: Conversion quality
        conversion_service: Conversion service instance

    Returns:
        Conversion result information

    Raises:
        HTTPException: If conversion fails
    """
    try:
        # This would typically be used with a file_id in the request
        # For now, just return the supported formats
        supported_formats = await conversion_service.get_supported_formats()

        return {
            "success": True,
            "conversion": {
                "source_format": source_format,
                "target_format": target_format,
                "quality": quality,
                "supported_formats": supported_formats,
            },
            "message": "Format conversion information retrieved",
        }

    except Exception as e:
        logger.error(f"Convert file format failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/formats",
    response_model=Dict[str, Any],
    summary="Get supported formats",
    description="Get list of supported preview formats",
)
async def get_supported_formats(
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get supported preview formats.

    Args:
        preview_manager: Preview manager instance

    Returns:
        List of supported formats
    """
    try:
        formats = await preview_manager.get_supported_formats()

        return {
            "success": True,
            "formats": formats,
            "message": "Supported formats retrieved",
        }

    except Exception as e:
        logger.error(f"Get supported formats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Preview Management

@router.delete(
    "/files/{file_id}",
    response_model=Dict[str, Any],
    summary="Delete preview",
    description="Delete all previews for a file",
)
async def delete_preview(
    file_id: UUID = ...,
    preview_type: Optional[str] = Query(None, description="Specific preview type to delete"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Delete previews for a file.

    Args:
        file_id: File ID
        preview_type: Specific preview type to delete
        preview_manager: Preview manager instance

    Returns:
        Deletion result

    Raises:
        HTTPException: If deletion fails
    """
    try:
        success = await preview_manager.delete_preview(
            file_id=file_id,
            preview_type=preview_type,
        )

        return {
            "success": success,
            "file_id": file_id,
            "preview_type": preview_type,
            "message": "Preview deleted successfully" if success else "Preview not found",
        }

    except Exception as e:
        logger.error(f"Delete preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/files/{file_id}/refresh",
    response_model=Dict[str, Any],
    summary="Refresh preview",
    description="Refresh all previews for a file",
)
async def refresh_preview(
    file_id: UUID = ...,
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Refresh previews for a file.

    Args:
        file_id: File ID
        preview_manager: Preview manager instance

    Returns:
        Refresh result

    Raises:
        HTTPException: If refresh fails
    """
    try:
        result = await preview_manager.refresh_preview(file_id)

        return {
            "success": True,
            "refresh": {
                "file_id": file_id,
                "generated_previews": result.generated_previews,
                "failed_previews": result.failed_previews,
            },
            "message": f"Refreshed {result.generated_previews} previews",
        }

    except Exception as e:
        logger.error(f"Refresh preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Preview Statistics

@router.get(
    "/files/{file_id}/stats",
    response_model=Dict[str, Any],
    summary="Get preview statistics",
    description="Get statistics about file previews",
)
async def get_preview_statistics(
    file_id: UUID = ...,
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Get preview statistics for a file.

    Args:
        file_id: File ID
        preview_manager: Preview manager instance

    Returns:
        Preview statistics

    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        stats = await preview_manager.get_preview_statistics(file_id)

        return {
            "success": True,
            "statistics": {
                "total_previews": stats.total_previews,
                "preview_types": stats.preview_types,
                "cache_hit_rate": stats.cache_hit_rate,
                "generation_time": stats.generation_time,
                "last_generated": stats.last_generated.isoformat() if stats.last_generated else None,
            },
            "file_id": file_id,
        }

    except Exception as e:
        logger.error(f"Get preview statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/cleanup",
    response_model=Dict[str, Any],
    summary="Cleanup old previews",
    description="Clean up old and unused previews",
)
async def cleanup_previews(
    older_than_days: int = Query(30, ge=1, description="Delete previews older than N days"),
    preview_manager: PreviewManager = Depends(get_preview_manager),
):
    """Clean up old previews.

    Args:
        older_than_days: Delete previews older than N days
        preview_manager: Preview manager instance

    Returns:
        Cleanup result

    Raises:
        HTTPException: If cleanup fails
    """
    try:
        result = await preview_manager.cleanup_old_previews(
            older_than_days=older_than_days,
        )

        logger.info(f"Preview cleanup completed: {result.deleted_count} previews deleted")

        return {
            "success": True,
            "cleanup": {
                "deleted_count": result.deleted_count,
                "criteria": {
                    "older_than_days": older_than_days,
                },
            },
            "message": f"Cleaned up {result.deleted_count} old previews",
        }

    except Exception as e:
        logger.error(f"Cleanup previews failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
