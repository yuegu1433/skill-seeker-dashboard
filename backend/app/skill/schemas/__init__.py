"""Skill management schemas.

This module exports all skill-related Pydantic schemas for validation.
"""

from .skill_operations import (
    SkillBase,
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListItem,
    SkillFilter,
    SkillSearch,
    SkillSearchResult,
    SkillStats,
    SkillBulkOperation,
    SkillBulkResult,
    SkillStatus,
    SkillVisibility,
    SortOrder,
)

from .skill_creation import (
    SkillCreationRequest,
    SkillCreationResponse,
    SkillTemplate,
    SkillCloneRequest,
    ContentFormat,
    LicenseType,
)

from .skill_import import (
    ImportRequest,
    ExportRequest,
    ImportResult,
    ExportResult,
    BatchImportRequest,
    BatchExportRequest,
    SkillExportData,
    ImportTemplate,
    ImportProgress,
    ImportSource,
    ImportFormat,
    ExportFormat,
    ConflictResolution,
)

__all__ = [
    # Skill operations
    "SkillBase",
    "SkillCreate",
    "SkillUpdate",
    "SkillResponse",
    "SkillListItem",
    "SkillFilter",
    "SkillSearch",
    "SkillSearchResult",
    "SkillStats",
    "SkillBulkOperation",
    "SkillBulkResult",
    "SkillStatus",
    "SkillVisibility",
    "SortOrder",
    # Skill creation
    "SkillCreationRequest",
    "SkillCreationResponse",
    "SkillTemplate",
    "SkillCloneRequest",
    "ContentFormat",
    "LicenseType",
    # Import/export
    "ImportRequest",
    "ExportRequest",
    "ImportResult",
    "ExportResult",
    "BatchImportRequest",
    "BatchExportRequest",
    "SkillExportData",
    "ImportTemplate",
    "ImportProgress",
    "ImportSource",
    "ImportFormat",
    "ExportFormat",
    "ConflictResolution",
]

# Schema groups for easy reference
SCHEMA_GROUPS = {
    "operations": [
        "SkillBase",
        "SkillCreate",
        "SkillUpdate",
        "SkillResponse",
        "SkillListItem",
        "SkillFilter",
        "SkillSearch",
        "SkillSearchResult",
        "SkillStats",
        "SkillBulkOperation",
        "SkillBulkResult",
    ],
    "creation": [
        "SkillCreationRequest",
        "SkillCreationResponse",
        "SkillTemplate",
        "SkillCloneRequest",
    ],
    "import_export": [
        "ImportRequest",
        "ExportRequest",
        "ImportResult",
        "ExportResult",
        "BatchImportRequest",
        "BatchExportRequest",
        "SkillExportData",
        "ImportTemplate",
        "ImportProgress",
    ],
}

# Validation rules
VALIDATION_RULES = {
    "skill_name": {
        "min_length": 1,
        "max_length": 200,
        "pattern": r"^[a-zA-Z0-9\s\-_]+$",
    },
    "skill_version": {
        "pattern": r"^\d+(\.\d+){0,3}(-[a-zA-Z0-9\-]+)?$",
    },
    "keywords": {
        "max_items": 20,
        "max_length": 50,
        "pattern": r"^[a-z0-9\-]+$",
    },
    "dependencies": {
        "max_items": 100,
        "max_length": 200,
    },
    "tags": {
        "max_items": 20,
        "max_length": 50,
        "pattern": r"^[a-zA-Z0-9\s\-_]+$",
    },
    "content": {
        "max_size": 1000000,  # 1MB
        "min_lines": 3,
    },
    "config": {
        "max_size": 10000,  # 10KB
        "max_depth": 5,
    },
}

# Common response formats
RESPONSE_FORMATS = {
    "success": {
        "success": True,
        "message": "Operation completed successfully",
        "timestamp": "ISO 8601 datetime",
    },
    "error": {
        "success": False,
        "error": "Error message",
        "error_code": "ERROR_CODE",
        "timestamp": "ISO 8601 datetime",
    },
    "validation_error": {
        "success": False,
        "error": "Validation failed",
        "validation_errors": [
            {
                "field": "field_name",
                "message": "Validation error message",
                "code": "validation_error_code",
            }
        ],
        "timestamp": "ISO 8601 datetime",
    },
}
