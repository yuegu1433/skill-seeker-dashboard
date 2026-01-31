"""Skill management models.

This module exports all skill-related models for the skill management system.
"""

from .skill import Skill, SkillTagAssociation
from .skill_version import SkillVersion
from .skill_category import SkillCategory
from .skill_tag import SkillTag

__all__ = [
    "Skill",
    "SkillVersion",
    "SkillCategory",
    "SkillTag",
    "SkillTagAssociation",
]

# Model metadata for database setup
MODEL_METADATA = {
    "Skill": {
        "table_name": "skills",
        "description": "Core skill model with metadata and relationships",
        "indexes": [
            "idx_skill_name",
            "idx_skill_status",
            "idx_skill_visibility",
            "idx_skill_category_id",
            "idx_skill_created_at",
            "idx_skill_updated_at",
            "idx_skill_published_at",
            "idx_skill_quality_score",
            "idx_skill_download_count",
            "idx_skill_rating",
        ],
        "unique_constraints": ["uq_skill_slug"],
    },
    "SkillVersion": {
        "table_name": "skill_versions",
        "description": "Version history for skills",
        "indexes": [
            "idx_skill_version_skill_id",
            "idx_skill_version_is_active",
            "idx_skill_version_is_latest",
            "idx_skill_version_is_stable",
            "idx_skill_version_created_at",
            "idx_skill_version_download_count",
            "idx_skill_version_content_hash",
        ],
        "unique_constraints": ["uq_skill_version_skill_id_version"],
    },
    "SkillCategory": {
        "table_name": "skill_categories",
        "description": "Hierarchical categories for organizing skills",
        "indexes": [
            "idx_skill_category_parent_id",
            "idx_skill_category_level",
            "idx_skill_category_path",
            "idx_skill_category_sort_order",
            "idx_skill_category_is_active",
            "idx_skill_category_is_public",
            "idx_skill_category_skill_count",
        ],
        "unique_constraints": ["uq_skill_category_slug"],
    },
    "SkillTag": {
        "table_name": "skill_tags",
        "description": "Tags for categorizing and filtering skills",
        "indexes": [
            "idx_skill_tag_name",
            "idx_skill_tag_usage_count",
            "idx_skill_tag_created_at",
        ],
        "unique_constraints": ["uq_skill_tag_name"],
    },
    "SkillTagAssociation": {
        "table_name": "skill_tag_associations",
        "description": "Many-to-many association between skills and tags",
        "indexes": [
            "idx_skill_tag_skill_id",
            "idx_skill_tag_tag_id",
        ],
        "unique_constraints": [],
    },
}

# Relationship map for easy reference
RELATIONSHIPS = {
    "Skill": {
        "versions": "SkillVersion",
        "category": "SkillCategory",
        "tags": "SkillTag",
    },
    "SkillVersion": {
        "skill": "Skill",
    },
    "SkillCategory": {
        "skills": "Skill",
        "parent": "SkillCategory",
        "children": "SkillCategory",
    },
    "SkillTag": {
        "skills": "Skill",
    },
}
