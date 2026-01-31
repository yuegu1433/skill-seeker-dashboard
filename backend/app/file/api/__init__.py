"""File Management API.

This module provides the main entry point for file management API routes.
"""

from fastapi import APIRouter

# Import routers
from app.file.api.v1.files import router as files_router
from app.file.api.v1.editor import router as editor_router
from app.file.api.v1.versions import router as versions_router
from app.file.api.v1.preview import router as preview_router

# Main API router
router = APIRouter(prefix="/api/v1/files", tags=["file-management"])

# Include all sub-routers
router.include_router(files_router, prefix="/files", tags=["files"])
router.include_router(editor_router, prefix="/editor", tags=["editor"])
router.include_router(versions_router, prefix="/versions", tags=["versions"])
router.include_router(preview_router, prefix="/preview", tags=["preview"])
