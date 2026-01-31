"""Platform managers package.

This package contains manager classes for handling platform operations,
including CRUD operations, business logic, and coordination.
"""

from .platform_manager import PlatformManager
from .deployment_manager import DeploymentManager
from .compatibility_manager import CompatibilityManager

__all__ = [
    "PlatformManager",
    "DeploymentManager",
    "CompatibilityManager",
]