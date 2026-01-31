"""File Editor API.

This module provides REST API endpoints for online file editing including
syntax highlighting, auto-save, real-time preview, and collaborative editing.
"""

import logging
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
import json
import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

# Import editor and services
from app.file.editor import FileEditor
from app.file.schemas.editor_config import (
    EditorSession,
    EditorConfig,
    AutoSaveConfig,
    CollaborativeEdit,
)
from app.database.session import get_db

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/editor", tags=["editor"])


# Dependency injection
async def get_file_editor(db: AsyncSession = Depends(get_db)) -> FileEditor:
    """Get FileEditor instance."""
    return FileEditor(db_session=db)


# Editor Session Management

@router.post(
    "/session",
    response_model=Dict[str, Any],
    summary="Create editor session",
    description="Create a new online editing session for a file",
)
async def create_editor_session(
    file_id: UUID = ...,
    config: Optional[EditorConfig] = None,
    editor: FileEditor = Depends(get_file_editor),
):
    """Create a new editor session.

    Args:
        file_id: File ID to edit
        config: Optional editor configuration
        editor: File editor instance

    Returns:
        Editor session information
    """
    try:
        session = await editor.create_editor_session(
            file_id=file_id,
            config=config,
        )

        logger.info(f"Editor session created: {session.session_id} for file {file_id}")

        return {
            "success": True,
            "session": {
                "session_id": session.session_id,
                "file_id": session.file_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
            },
            "message": "Editor session created successfully",
        }

    except Exception as e:
        logger.error(f"Editor session creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/session/{session_id}",
    response_model=Dict[str, Any],
    summary="Get editor session",
    description="Get editor session information",
)
async def get_editor_session(
    session_id: str = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Get editor session information.

    Args:
        session_id: Session ID
        editor: File editor instance

    Returns:
        Session information
    """
    try:
        session = await editor.get_editor_session(session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Editor session not found")

        return {
            "success": True,
            "session": {
                "session_id": session.session_id,
                "file_id": session.file_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get editor session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/session/{session_id}",
    response_model=Dict[str, Any],
    summary="Close editor session",
    description="Close an editor session",
)
async def close_editor_session(
    session_id: str = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Close an editor session.

    Args:
        session_id: Session ID
        editor: File editor instance

    Returns:
        Closure result
    """
    try:
        success = await editor.close_editor_session(session_id)

        return {
            "success": success,
            "message": "Editor session closed successfully" if success else "Session not found",
        }

    except Exception as e:
        logger.error(f"Close editor session failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# File Content Operations

@router.get(
    "/session/{session_id}/content",
    response_model=Dict[str, Any],
    summary="Get file content",
    description="Get file content for editing",
)
async def get_file_content(
    session_id: str = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Get file content for editing.

    Args:
        session_id: Session ID
        editor: File editor instance

    Returns:
        File content and metadata
    """
    try:
        result = await editor.get_file_content(session_id)

        if not result:
            raise HTTPException(status_code=404, detail="Session not found or file not accessible")

        return {
            "success": True,
            "content": result["content"],
            "metadata": result["metadata"],
            "syntax_highlighting": result.get("syntax_highlighting"),
            "line_count": result.get("line_count", 0),
            "last_modified": result.get("last_modified"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file content failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/session/{session_id}/content",
    response_model=Dict[str, Any],
    summary="Update file content",
    description="Update file content in editor",
)
async def update_file_content(
    session_id: str = ...,
    content: str = ...,
    version_note: Optional[str] = None,
    editor: FileEditor = Depends(get_file_editor),
):
    """Update file content.

    Args:
        session_id: Session ID
        content: New file content
        version_note: Optional version note
        editor: File editor instance

    Returns:
        Update result
    """
    try:
        result = await editor.update_file_content(
            session_id=session_id,
            content=content,
            version_note=version_note,
        )

        return {
            "success": True,
            "result": {
                "file_id": result.file_id,
                "version_id": result.version_id,
                "content_hash": result.content_hash,
                "last_modified": result.last_modified.isoformat(),
            },
            "message": "File content updated successfully",
        }

    except Exception as e:
        logger.error(f"Update file content failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# Auto-save Configuration

@router.post(
    "/session/{session_id}/autosave",
    response_model=Dict[str, Any],
    summary="Configure auto-save",
    description="Configure auto-save settings for editor session",
)
async def configure_autosave(
    session_id: str = ...,
    config: AutoSaveConfig = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Configure auto-save settings.

    Args:
        session_id: Session ID
        config: Auto-save configuration
        editor: File editor instance

    Returns:
        Configuration result
    """
    try:
        result = await editor.configure_autosave(
            session_id=session_id,
            config=config,
        )

        return {
            "success": True,
            "config": {
                "enabled": result.enabled,
                "interval": result.interval,
                "min_changes": result.min_changes,
            },
            "message": "Auto-save configured successfully",
        }

    except Exception as e:
        logger.error(f"Configure auto-save failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/session/{session_id}/autosave/status",
    response_model=Dict[str, Any],
    summary="Get auto-save status",
    description="Get auto-save status and statistics",
)
async def get_autosave_status(
    session_id: str = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Get auto-save status.

    Args:
        session_id: Session ID
        editor: File editor instance

    Returns:
        Auto-save status
    """
    try:
        status = await editor.get_autosave_status(session_id)

        if not status:
            raise HTTPException(status_code=404, detail="Session not found or auto-save not configured")

        return {
            "success": True,
            "status": {
                "enabled": status.enabled,
                "interval": status.interval,
                "last_save": status.last_save.isoformat() if status.last_save else None,
                "save_count": status.save_count,
                "pending_changes": status.pending_changes,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get auto-save status failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Syntax Highlighting and Preview

@router.post(
    "/session/{session_id}/syntax",
    response_model=Dict[str, Any],
    summary="Get syntax highlighting",
    description="Get syntax highlighted content",
)
async def get_syntax_highlighting(
    session_id: str = ...,
    language: Optional[str] = None,
    theme: Optional[str] = "default",
    editor: FileEditor = Depends(get_file_editor),
):
    """Get syntax highlighted content.

    Args:
        session_id: Session ID
        language: Optional language override
        theme: Color theme
        editor: File editor instance

    Returns:
        Syntax highlighted content
    """
    try:
        result = await editor.get_syntax_highlighting(
            session_id=session_id,
            language=language,
            theme=theme,
        )

        return {
            "success": True,
            "highlighted_content": result["highlighted_content"],
            "language": result["language"],
            "theme": theme,
            "line_highlights": result.get("line_highlights", []),
        }

    except Exception as e:
        logger.error(f"Get syntax highlighting failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/session/{session_id}/preview",
    response_model=Dict[str, Any],
    summary="Generate preview",
    description="Generate real-time preview of the content",
)
async def generate_preview(
    session_id: str = ...,
    preview_type: Optional[str] = "html",
    editor: FileEditor = Depends(get_file_editor),
):
    """Generate content preview.

    Args:
        session_id: Session ID
        preview_type: Preview type (html, markdown, etc.)
        editor: File editor instance

    Returns:
        Preview content
    """
    try:
        result = await editor.generate_preview(
            session_id=session_id,
            preview_type=preview_type,
        )

        return {
            "success": True,
            "preview": {
                "type": preview_type,
                "content": result["preview_content"],
                "metadata": result.get("metadata", {}),
            },
            "message": "Preview generated successfully",
        }

    except Exception as e:
        logger.error(f"Generate preview failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Collaborative Editing

@router.post(
    "/session/{session_id}/collaborate",
    response_model=Dict[str, Any],
    summary="Start collaborative editing",
    description="Start collaborative editing session",
)
async def start_collaborative_editing(
    session_id: str = ...,
    user_id: Optional[str] = None,
    editor: FileEditor = Depends(get_file_editor),
):
    """Start collaborative editing.

    Args:
        session_id: Session ID
        user_id: Optional user ID
        editor: File editor instance

    Returns:
        Collaborative session info
    """
    try:
        result = await editor.start_collaborative_editing(
            session_id=session_id,
            user_id=user_id,
        )

        return {
            "success": True,
            "collaborative_session": {
                "session_id": result.session_id,
                "participants": result.participants,
                "active_users": result.active_users,
            },
            "websocket_url": f"/api/v1/files/editor/websocket/{session_id}",
            "message": "Collaborative editing started",
        }

    except Exception as e:
        logger.error(f"Start collaborative editing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/session/{session_id}/collaborators",
    response_model=Dict[str, Any],
    summary="Get collaborators",
    description="Get list of active collaborators",
)
async def get_collaborators(
    session_id: str = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Get active collaborators.

    Args:
        session_id: Session ID
        editor: File editor instance

    Returns:
        List of collaborators
    """
    try:
        collaborators = await editor.get_collaborators(session_id)

        return {
            "success": True,
            "collaborators": [
                {
                    "user_id": c.user_id,
                    "username": c.username,
                    "cursor_position": c.cursor_position,
                    "selection": c.selection,
                    "last_activity": c.last_activity.isoformat(),
                }
                for c in collaborators
            ],
        }

    except Exception as e:
        logger.error(f"Get collaborators failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket for Real-time Collaboration

@router.websocket("/websocket/{session_id}")
async def editor_websocket(
    websocket: WebSocket,
    session_id: str,
    editor: FileEditor = Depends(get_file_editor),
):
    """WebSocket endpoint for real-time collaborative editing.

    Args:
        websocket: WebSocket connection
        session_id: Session ID
        editor: File editor instance
    """
    await editor.connect_websocket(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            message_type = message.get("type")

            if message_type == "edit":
                # Handle collaborative edit
                edit = CollaborativeEdit(
                    session_id=session_id,
                    user_id=message.get("user_id"),
                    operation=message.get("operation"),
                    position=message.get("position"),
                    content=message.get("content"),
                    timestamp=message.get("timestamp"),
                )

                result = await editor.apply_collaborative_edit(edit)

                # Broadcast to all connected clients
                await editor.broadcast_to_session(session_id, {
                    "type": "edit_applied",
                    "edit_id": result.edit_id,
                    "user_id": edit.user_id,
                    "operation": edit.operation,
                    "position": edit.position,
                    "content": edit.content,
                })

            elif message_type == "cursor":
                # Handle cursor position update
                await editor.update_cursor_position(
                    session_id=session_id,
                    user_id=message.get("user_id"),
                    position=message.get("position"),
                )

                # Broadcast cursor position
                await editor.broadcast_to_session(session_id, {
                    "type": "cursor_update",
                    "user_id": message.get("user_id"),
                    "position": message.get("position"),
                })

            elif message_type == "save":
                # Handle manual save
                result = await editor.save_file(session_id)

                await websocket.send_text(json.dumps({
                    "type": "save_complete",
                    "success": True,
                    "file_id": result.file_id,
                    "version_id": result.version_id,
                    "timestamp": result.last_modified.isoformat(),
                }))

    except WebSocketDisconnect:
        await editor.disconnect_websocket(session_id, websocket)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()


# Editor Statistics

@router.get(
    "/session/{session_id}/stats",
    response_model=Dict[str, Any],
    summary="Get editor statistics",
    description="Get editing session statistics",
)
async def get_editor_stats(
    session_id: str = ...,
    editor: FileEditor = Depends(get_file_editor),
):
    """Get editing session statistics.

    Args:
        session_id: Session ID
        editor: File editor instance

    Returns:
        Session statistics
    """
    try:
        stats = await editor.get_editor_stats(session_id)

        if not stats:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "success": True,
            "stats": {
                "session_duration": stats.session_duration,
                "edit_count": stats.edit_count,
                "save_count": stats.save_count,
                "lines_added": stats.lines_added,
                "lines_deleted": stats.lines_deleted,
                "characters_added": stats.characters_added,
                "characters_deleted": stats.characters_deleted,
                "typing_speed": stats.typing_speed,
                "last_activity": stats.last_activity.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get editor stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
