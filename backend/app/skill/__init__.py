"""Skill Management System.

This package provides comprehensive skill management capabilities including:
- Skill CRUD operations and business logic
- Event-driven architecture and pub/sub messaging
- Version control for skills
- Online skill editor with real-time collaboration
- Import and export skills in multiple formats
- Analytics and reporting for skills
- WebSocket-based real-time communication
- Asynchronous task processing

Main Components:
    - SkillManager: Core skill CRUD operations
    - SkillEventManager: Event publishing and subscription
    - SkillVersionManager: Version control for skills
    - SkillEditor: Online editor with real-time collaboration
    - SkillImporter: Import and export functionality
    - SkillAnalytics: Analytics and reporting
"""

from .manager import SkillManager, skill_manager
from .event_manager import SkillEventManager, skill_event_manager
from .version_manager import SkillVersionManager
from .editor import SkillEditor
from .importer import SkillImporter
from .analytics import SkillAnalytics

from .models import (
    Skill,
    SkillCategory,
    SkillTag,
    SkillVersion,
    SkillTagAssociation,
)

from .schemas.skill_operations import (
    SkillCreate,
    SkillUpdate,
    SkillFilter,
    SkillSearch,
    SkillBulkOperation,
)

from .schemas.skill_creation import SkillCreateRequest
from .schemas.skill_import import ImportRequest, ExportRequest

# Version
__version__ = "1.0.0"

# Public API
__all__ = [
    # Managers
    "SkillManager",
    "skill_manager",
    "SkillEventManager",
    "skill_event_manager",
    "SkillVersionManager",
    "SkillEditor",
    "SkillImporter",
    "SkillAnalytics",

    # Models
    "Skill",
    "SkillCategory",
    "SkillTag",
    "SkillVersion",
    "SkillTagAssociation",

    # Schemas
    "SkillCreate",
    "SkillUpdate",
    "SkillFilter",
    "SkillSearch",
    "SkillBulkOperation",
    "SkillCreateRequest",
    "ImportRequest",
    "ExportRequest",
]
