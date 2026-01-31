"""Progress tracking API v1.

This module contains version 1 API routes for progress tracking functionality.
"""

from fastapi import APIRouter

from .progress import router as progress_router
from .logs import router as logs_router
from .history import router as history_router
from .websocket import router as websocket_router

# Main v1 router
v1_router = APIRouter(prefix="/v1")

# Include sub-routers
v1_router.include_router(progress_router, prefix="/progress", tags=["progress"])
v1_router.include_router(logs_router, prefix="/logs", tags=["logs"])
v1_router.include_router(history_router, prefix="/history", tags=["history"])
v1_router.include_router(websocket_router, prefix="/ws", tags=["websocket"])

__all__ = [
    "v1_router",
    "progress_router",
    "logs_router",
    "history_router",
    "websocket_router",
]
