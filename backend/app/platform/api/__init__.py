"""Platform API package.

This package contains API routes and handlers for platform management.
"""

from .v1.platforms import router as platforms_router
from .v1.deployment import router as deployment_router
from .v1.compatibility import router as compatibility_router

__all__ = [
    "platforms_router",
    "deployment_router",
    "compatibility_router",
]