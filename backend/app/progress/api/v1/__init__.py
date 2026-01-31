"""Progress tracking API v1.

This module contains version 1 API routes for progress tracking functionality.
"""

from fastapi import APIRouter

from ...progress_manager import progress_router
from ...log_manager import logs_router
from ...tracker import history_router

# Main v1 router
v1_router = APIRouter(prefix="/v1")

# Include sub-routers
v1_router.include_router(progress_router, prefix="/progress", tags=["progress"])
v1_router.include_router(logs_router, prefix="/logs", tags=["logs"])
v1_router.include_router(history_router, prefix="/history", tags=["history"])

__all__ = [
    "v1_router",
    "progress_router",
    "logs_router",
    "history_router",
]
