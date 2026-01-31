"""Skill operation schemas.

This module defines Pydantic schemas for skill operations including
CRUD operations, filtering, and searching.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum


class SkillStatus(str, Enum):
    """Skill status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class SkillVisibility(str, Enum):
    """Skill visibility enumeration."""
    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"


class SortOrder(str, Enum):
    """Sort order enumeration."""
    ASC = "asc"
    DESC = "desc"


class SkillBase(BaseModel):
    """Base skill schema with common fields."""

    name: str = Field(..., min_length=1, max_length=200, description="Skill name")
    description: Optional[str] = Field(None, description="Skill description")
    category_id: Optional[str] = Field(None, description="Category ID")
    status: SkillStatus = Field(SkillStatus.DRAFT, description="Skill status")
    visibility: SkillVisibility = Field(
        SkillVisibility.PUBLIC, description="Skill visibility"
    )
    content_type: str = Field("yaml", description="Content type")
    version: str = Field("1.0.0", description="Skill version")
    author: Optional[str] = Field(None, max_length=100, description="Skill author")
    maintainer: Optional[str] = Field(None, max_length=100, description="Skill maintainer")
    license: Optional[str] = Field(None, max_length=50, description="License type")
    homepage: Optional[str] = Field(None, description="Homepage URL")
    repository: Optional[str] = Field(None, description="Repository URL")
    documentation: Optional[str] = Field(None, description="Documentation URL")
    keywords: Optional[List[str]] = Field(None, description="Keywords for search")
    python_requires: Optional[str] = Field(None, description="Required Python version")
    dependencies: Optional[List[str]] = Field(None, description="List of dependencies")
    config: Optional[Dict[str, Any]] = Field(None, description="Skill-specific configuration")

    @validator("version")
    def validate_version(cls, v):
        """Validate version format."""
        if v:
            # Basic version format check
            parts = v.split(".")
            if len(parts) < 1 or len(parts) > 4:
                raise ValueError("Version must have 1-4 parts (e.g., '1', '1.0', '1.0.0')")
            for part in parts:
                if not part.replace("-", "").replace(".", "").isalnum():
                    raise ValueError("Version parts must be alphanumeric")
        return v

    @validator("keywords")
    def validate_keywords(cls, v):
        """Validate keywords list."""
        if v and len(v) > 20:
            raise ValueError("Maximum 20 keywords allowed")
        if v:
            for keyword in v:
                if len(keyword) > 50:
                    raise ValueError("Each keyword must be 50 characters or less")
        return v

    @validator("dependencies")
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if v and len(v) > 100:
            raise ValueError("Maximum 100 dependencies allowed")
        return v

    @validator("config")
    def validate_config(cls, v):
        """Validate configuration dictionary."""
        if v:
            if len(str(v)) > 10000:
                raise ValueError("Configuration too large (max 10KB)")
        return v


class SkillCreate(SkillBase):
    """Schema for creating a skill."""

    # Content is required for creation
    content: str = Field(..., min_length=1, description="Skill content")
    content_format: str = Field("yaml", description="Content format")

    # Validation for content
    @validator("content")
    def validate_content(cls, v):
        """Validate content."""
        if len(v) > 1000000:  # 1MB
            raise ValueError("Content too large (max 1MB)")
        return v


class SkillUpdate(BaseModel):
    """Schema for updating a skill."""

    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Skill name")
    description: Optional[str] = Field(None, description="Skill description")
    category_id: Optional[str] = Field(None, description="Category ID")
    status: Optional[SkillStatus] = Field(None, description="Skill status")
    visibility: Optional[SkillVisibility] = Field(None, description="Skill visibility")
    content_type: Optional[str] = Field(None, description="Content type")
    version: Optional[str] = Field(None, description="Skill version")
    author: Optional[str] = Field(None, max_length=100, description="Skill author")
    maintainer: Optional[str] = Field(None, max_length=100, description="Skill maintainer")
    license: Optional[str] = Field(None, max_length=50, description="License type")
    homepage: Optional[str] = Field(None, description="Homepage URL")
    repository: Optional[str] = Field(None, description="Repository URL")
    documentation: Optional[str] = Field(None, description="Documentation URL")
    keywords: Optional[List[str]] = Field(None, description="Keywords for search")
    python_requires: Optional[str] = Field(None, description="Required Python version")
    dependencies: Optional[List[str]] = Field(None, description="List of dependencies")
    config: Optional[Dict[str, Any]] = Field(None, description="Skill-specific configuration")

    # Update validators
    @validator("version")
    def validate_version(cls, v):
        """Validate version format."""
        if v:
            parts = v.split(".")
            if len(parts) < 1 or len(parts) > 4:
                raise ValueError("Version must have 1-4 parts")
            for part in parts:
                if not part.replace("-", "").replace(".", "").isalnum():
                    raise ValueError("Version parts must be alphanumeric")
        return v

    @validator("keywords")
    def validate_keywords(cls, v):
        """Validate keywords list."""
        if v and len(v) > 20:
            raise ValueError("Maximum 20 keywords allowed")
        if v:
            for keyword in v:
                if len(keyword) > 50:
                    raise ValueError("Each keyword must be 50 characters or less")
        return v

    @validator("dependencies")
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if v and len(v) > 100:
            raise ValueError("Maximum 100 dependencies allowed")
        return v


class SkillResponse(SkillBase):
    """Schema for skill response."""

    id: str = Field(..., description="Skill ID")
    slug: str = Field(..., description="URL-friendly identifier")
    quality_score: float = Field(0.0, description="Quality score")
    completeness: float = Field(0.0, description="Completeness score")
    download_count: int = Field(0, description="Download count")
    view_count: int = Field(0, description="View count")
    like_count: int = Field(0, description="Like count")
    rating: float = Field(0.0, description="Average rating")
    rating_count: int = Field(0, description="Number of ratings")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")
    deprecated_at: Optional[datetime] = Field(None, description="Deprecation timestamp")
    archived_at: Optional[datetime] = Field(None, description="Archival timestamp")

    # Category and tags info
    category: Optional[Dict[str, Any]] = Field(None, description="Category information")
    tags: Optional[List[Dict[str, Any]]] = Field(None, description="Tag list")

    class Config:
        from_attributes = True


class SkillListItem(BaseModel):
    """Schema for skill list items."""

    id: str = Field(..., description="Skill ID")
    name: str = Field(..., description="Skill name")
    slug: str = Field(..., description="URL-friendly identifier")
    description: Optional[str] = Field(None, description="Skill description")
    status: SkillStatus = Field(..., description="Skill status")
    visibility: SkillVisibility = Field(..., description="Skill visibility")
    version: str = Field(..., description="Skill version")
    author: Optional[str] = Field(None, description="Skill author")
    rating: float = Field(0.0, description="Average rating")
    rating_count: int = Field(0, description="Number of ratings")
    download_count: int = Field(0, description="Download count")
    view_count: int = Field(0, description="View count")
    like_count: int = Field(0, description="Like count")
    quality_score: float = Field(0.0, description="Quality score")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    published_at: Optional[datetime] = Field(None, description="Publication timestamp")

    # Category and tags
    category_name: Optional[str] = Field(None, description="Category name")
    tags: Optional[List[str]] = Field(None, description="Tag names")

    class Config:
        from_attributes = True


class SkillFilter(BaseModel):
    """Schema for filtering skills."""

    # Status and visibility filters
    status: Optional[List[SkillStatus]] = Field(None, description="Filter by status")
    visibility: Optional[List[SkillVisibility]] = Field(None, description="Filter by visibility")
    category_id: Optional[str] = Field(None, description="Filter by category")
    category_slug: Optional[str] = Field(None, description="Filter by category slug")

    # Author and maintainer filters
    author: Optional[str] = Field(None, description="Filter by author")
    maintainer: Optional[str] = Field(None, description="Filter by maintainer")

    # Content filters
    content_type: Optional[str] = Field(None, description="Filter by content type")
    has_content: Optional[bool] = Field(None, description="Filter by content existence")

    # Quality filters
    min_quality_score: Optional[float] = Field(None, ge=0, le=100, description="Minimum quality score")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating")

    # Date filters
    created_after: Optional[datetime] = Field(None, description="Created after date")
    created_before: Optional[datetime] = Field(None, description="Created before date")
    updated_after: Optional[datetime] = Field(None, description="Updated after date")
    updated_before: Optional[datetime] = Field(None, description="Updated before date")
    published_after: Optional[datetime] = Field(None, description="Published after date")
    published_before: Optional[datetime] = Field(None, description="Published before date")

    # Usage filters
    min_downloads: Optional[int] = Field(None, ge=0, description="Minimum download count")
    min_views: Optional[int] = Field(None, ge=0, description="Minimum view count")
    min_likes: Optional[int] = Field(None, ge=0, description="Minimum like count")

    # Text filters
    search: Optional[str] = Field(None, description="Search query")
    keyword: Optional[str] = Field(None, description="Filter by keyword")
    tag: Optional[str] = Field(None, description="Filter by tag name")

    # Version filters
    version: Optional[str] = Field(None, description="Filter by version")
    has_versions: Optional[bool] = Field(None, description="Filter by version existence")


class SkillSearch(BaseModel):
    """Schema for skill search parameters."""

    query: Optional[str] = Field(None, description="Search query")
    filters: Optional[SkillFilter] = Field(None, description="Search filters")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("updated_at", description="Sort field")
    sort_order: SortOrder = Field(SortOrder.DESC, description="Sort order")

    # Field selection
    include_tags: bool = Field(False, description="Include tags in results")
    include_category: bool = Field(False, description="Include category info")
    include_stats: bool = Field(True, description="Include statistics")


class SkillSearchResult(BaseModel):
    """Schema for skill search results."""

    items: List[SkillListItem] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    page: int = Field(..., description="Current page")
    page_size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Has next page")
    has_prev: bool = Field(..., description="Has previous page")

    # Search metadata
    query: Optional[str] = Field(None, description="Search query")
    filters_applied: Optional[Dict[str, Any]] = Field(None, description="Applied filters")

    class Config:
        from_attributes = True


class SkillStats(BaseModel):
    """Schema for skill statistics."""

    total_skills: int = Field(..., description="Total number of skills")
    active_skills: int = Field(..., description="Number of active skills")
    draft_skills: int = Field(..., description="Number of draft skills")
    deprecated_skills: int = Field(..., description="Number of deprecated skills")
    archived_skills: int = Field(..., description="Number of archived skills")

    # Usage statistics
    total_downloads: int = Field(..., description="Total downloads")
    total_views: int = Field(..., description="Total views")
    total_likes: int = Field(..., description="Total likes")

    # Rating statistics
    avg_rating: float = Field(..., description="Average rating across all skills")
    total_ratings: int = Field(..., description="Total number of ratings")

    # Quality statistics
    avg_quality_score: float = Field(..., description="Average quality score")
    avg_completeness: float = Field(..., description="Average completeness")

    # Category distribution
    categories: List[Dict[str, Any]] = Field(..., description="Category distribution")

    # Tag distribution
    top_tags: List[Dict[str, Any]] = Field(..., description="Top tags")

    # Content type distribution
    content_types: List[Dict[str, Any]] = Field(..., description="Content type distribution")


class SkillBulkOperation(BaseModel):
    """Schema for bulk operations on skills."""

    skill_ids: List[str] = Field(..., min_items=1, max_items=100, description="List of skill IDs")
    operation: str = Field(..., description="Operation to perform")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")

    @validator("operation")
    def validate_operation(cls, v):
        """Validate operation type."""
        allowed_operations = [
            "activate",
            "deactivate",
            "deprecate",
            "archive",
            "delete",
            "update_category",
            "add_tags",
            "remove_tags",
            "update_status",
        ]
        if v not in allowed_operations:
            raise ValueError(f"Invalid operation. Must be one of: {', '.join(allowed_operations)}")
        return v


class SkillBulkResult(BaseModel):
    """Schema for bulk operation results."""

    operation: str = Field(..., description="Operation performed")
    total_requested: int = Field(..., description="Total number of skills in request")
    total_succeeded: int = Field(..., description="Total number of successful operations")
    total_failed: int = Field(..., description="Total number of failed operations")
    succeeded_ids: List[str] = Field(..., description="IDs of successful operations")
    failed_ids: List[str] = Field(..., description="IDs of failed operations")
    errors: List[Dict[str, Any]] = Field(..., description="Error details")
    processed_at: datetime = Field(..., description="Processing timestamp")
