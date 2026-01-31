"""Platform API v1 package.

This package contains version 1 API routes for platform management.
"""

from .platforms import router as platforms_router
from .deployment import router as deployment_router
from .compatibility import router as compatibility_router

__all__ = [
    "platforms_router",
    "deployment_router",
    "compatibility_router",
]