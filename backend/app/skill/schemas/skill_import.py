"""Skill import/export schemas.

This module defines Pydantic schemas for importing and exporting skills
from various sources and in various formats.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


class ImportSource(str, Enum):
    """Import source types."""
    FILE = "file"
    URL = "url"
    GITHUB = "github"
    GIT = "git"
    TEXT = "text"
    JSON = "json"
    YAML = "yaml"


class ImportFormat(str, Enum):
    """Import formats."""
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    CSV = "csv"
    ZIP = "zip"
    TAR_GZ = "tar.gz"


class ExportFormat(str, Enum):
    """Export formats."""
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    CSV = "csv"
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    MARKDOWN = "markdown"
    HTML = "html"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""
    SKIP = "skip"
    OVERWRITE = "overwrite"
    RENAME = "rename"
    CREATE_VERSION = "create_version"
    ASK_USER = "ask_user"


class ImportRequest(BaseModel):
    """Schema for skill import request."""

    # Source information
    source: ImportSource = Field(..., description="Import source type")
    format: ImportFormat = Field(..., description="Import format")

    # Source details
    file_path: Optional[str] = Field(None, description="File path for file imports")
    url: Optional[str] = Field(None, description="URL for web imports")
    content: Optional[str] = Field(None, description="Raw content for text imports")

    # GitHub specific
    github_repo: Optional[str] = Field(None, description="GitHub repository (user/repo)")
    github_path: Optional[str] = Field(None, description="Path in repository")
    github_branch: Optional[str] = Field("main", description="Git branch")
    github_token: Optional[str] = Field(None, description="GitHub token")

    # Git specific
    git_url: Optional[str] = Field(None, description="Git repository URL")
    git_branch: Optional[str] = Field("main", description="Git branch")
    git_token: Optional[str] = Field(None, description="Git token")

    # Import options
    overwrite_existing: bool = Field(False, description="Overwrite existing skills")
    conflict_resolution: ConflictResolution = Field(
        ConflictResolution.SKIP,
        description="How to handle conflicts"
    )

    # Metadata options
    auto_categorize: bool = Field(True, description="Auto-categorize imported skills")
    extract_keywords: bool = Field(True, description="Extract keywords from content")
    validate_content: bool = Field(True, description="Validate imported content")

    # Processing options
    batch_size: int = Field(50, ge=1, le=1000, description="Batch size for processing")
    skip_errors: bool = Field(True, description="Skip files with errors")
    continue_on_error: bool = Field(True, description="Continue on error")

    # Custom metadata
    author: Optional[str] = Field(None, description="Import author")
    tags: Optional[List[str]] = Field(None, description="Tags to apply")
    category_id: Optional[str] = Field(None, description="Default category")

    # Validation
    @validator("url")
    def validate_url(cls, v):
        """Validate URL."""
        if v:
            url_pattern = r"^(https?://)[a-zA-Z0-9\-_.]+(\.[a-zA-Z]{2,})+([/\w\-._~:/?#[\]@!$&'()*+,;=]*)?$"
            if not re.match(url_pattern, v):
                raise ValueError("Invalid URL format")
        return v

    @validator("github_repo")
    def validate_github_repo(cls, v):
        """Validate GitHub repository format."""
        if v:
            if not re.match(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$", v):
                raise ValueError("Invalid GitHub repository format (user/repo)")
        return v

    @validator("file_path")
    def validate_file_path(cls, v):
        """Validate file path."""
        if v:
            # Basic path validation
            if ".." in v or v.startswith("/"):
                raise ValueError("Invalid file path")
        return v

    @validator("content")
    def validate_content(cls, v):
        """Validate content."""
        if v and len(v) > 10000000:  # 10MB
            raise ValueError("Content too large (max 10MB)")
        return v


class ExportRequest(BaseModel):
    """Schema for skill export request."""

    # Export configuration
    format: ExportFormat = Field(..., description="Export format")

    # Source selection
    skill_ids: Optional[List[str]] = Field(None, description="Specific skill IDs to export")
    category_id: Optional[str] = Field(None, description="Category to export")
    status: Optional[List[str]] = Field(None, description="Status filter")

    # Export options
    include_versions: bool = Field(True, description="Include version history")
    include_metadata: bool = Field(True, description="Include metadata")
    include_stats: bool = Field(False, description="Include statistics")
    include_tags: bool = Field(True, description="Include tags")
    include_dependencies: bool = Field(True, description="Include dependencies")

    # File options
    compression: bool = Field(True, description="Compress export file")
    encrypt: bool = Field(False, description="Encrypt export file")
    password: Optional[str] = Field(None, description="Encryption password")

    # Naming
    file_name: Optional[str] = Field(None, description="Custom file name")
    include_timestamp: bool = Field(True, description="Include timestamp in filename")

    # Processing
    batch_size: int = Field(100, ge=1, le=1000, description="Batch size for processing")

    # Validation
    @validator("skill_ids")
    def validate_skill_ids(cls, v):
        """Validate skill IDs list."""
        if v:
            if len(v) > 1000:
                raise ValueError("Maximum 1000 skill IDs allowed")

            for skill_id in v:
                if not re.match(r"^[a-zA-Z0-9\-_]+$", skill_id):
                    raise ValueError(f"Invalid skill ID format: {skill_id}")
        return v

    @validator("file_name")
    def validate_file_name(cls, v):
        """Validate file name."""
        if v:
            # Remove path traversal and invalid characters
            v = re.sub(r"[^\w\-_.]", "", v)
            if not v:
                raise ValueError("Invalid file name")
        return v

    @validator("password")
    def validate_password(cls, v):
        """Validate encryption password."""
        if v and len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class ImportResult(BaseModel):
    """Schema for import operation result."""

    success: bool = Field(..., description="Whether import was successful")
    import_id: str = Field(..., description="Import operation ID")

    # Statistics
    total_files: int = Field(..., description="Total files processed")
    successful_imports: int = Field(..., description="Successful imports")
    failed_imports: int = Field(..., description="Failed imports")
    skipped_files: int = Field(..., description="Skipped files")

    # Created skills
    created_skills: List[str] = Field(..., description="IDs of created skills")
    updated_skills: List[str] = Field(..., description="IDs of updated skills")
    skipped_skills: List[str] = Field(..., description="IDs of skipped skills")

    # Errors and warnings
    errors: List[Dict[str, Any]] = Field(..., description="Import errors")
    warnings: List[str] = Field(..., description="Import warnings")

    # Metadata
    imported_at: datetime = Field(..., description="Import timestamp")
    duration_seconds: float = Field(..., description="Import duration")
    author: Optional[str] = Field(None, description="Import author")

    # File information
    source: str = Field(..., description="Import source")
    format: str = Field(..., description="Import format")
    file_size_bytes: Optional[int] = Field(None, description="Source file size")


class ExportResult(BaseModel):
    """Schema for export operation result."""

    success: bool = Field(..., description="Whether export was successful")
    export_id: str = Field(..., description="Export operation ID")

    # File information
    file_name: str = Field(..., description="Export filename")
    file_path: Optional[str] = Field(None, description="Export file path")
    file_size_bytes: Optional[int] = Field(None, description="Export file size")
    file_url: Optional[str] = Field(None, description="Download URL")

    # Statistics
    total_skills: int = Field(..., description="Total skills exported")
    total_versions: int = Field(..., description="Total versions exported")

    # Metadata
    exported_at: datetime = Field(..., description="Export timestamp")
    duration_seconds: float = Field(..., description="Export duration")
    format: str = Field(..., description="Export format")

    # Options used
    options: Dict[str, Any] = Field(..., description="Export options used")


class BatchImportRequest(BaseModel):
    """Schema for batch import request."""

    imports: List[ImportRequest] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of import requests"
    )

    # Processing options
    parallel_processing: bool = Field(True, description="Process imports in parallel")
    max_concurrent: int = Field(5, ge=1, le=20, description="Max concurrent imports")
    continue_on_error: bool = Field(True, description="Continue on error")

    # Global options
    default_author: Optional[str] = Field(None, description="Default import author")
    default_category_id: Optional[str] = Field(None, description="Default category")


class BatchExportRequest(BaseModel):
    """Schema for batch export request."""

    exports: List[ExportRequest] = Field(
        ...,
        min_items=1,
        max_items=100,
        description="List of export requests"
    )

    # Processing options
    parallel_processing: bool = Field(True, description="Process exports in parallel")
    max_concurrent: int = Field(3, ge=1, le=10, description="Max concurrent exports")

    # Packaging
    create_archive: bool = Field(False, description="Create a single archive")
    archive_name: Optional[str] = Field(None, description="Archive name")


class SkillExportData(BaseModel):
    """Schema for individual skill export data."""

    # Basic information
    id: str = Field(..., description="Skill ID")
    name: str = Field(..., description="Skill name")
    slug: str = Field(..., description="Skill slug")
    description: Optional[str] = Field(None, description="Skill description")

    # Content
    content: str = Field(..., description="Skill content")
    content_type: str = Field(..., description="Content type")

    # Metadata
    version: str = Field(..., description="Skill version")
    author: Optional[str] = Field(None, description="Author")
    maintainer: Optional[str] = Field(None, description="Maintainer")
    license: Optional[str] = Field(None, description="License")

    # URLs
    homepage: Optional[str] = Field(None, description="Homepage URL")
    repository: Optional[str] = Field(None, description="Repository URL")
    documentation: Optional[str] = Field(None, description="Documentation URL")

    # Classification
    category: Optional[Dict[str, Any]] = Field(None, description="Category info")
    tags: Optional[List[Dict[str, Any]]] = Field(None, description="Tag list")

    # Dependencies
    keywords: Optional[List[str]] = Field(None, description="Keywords")
    dependencies: Optional[List[str]] = Field(None, description="Dependencies")
    python_requires: Optional[str] = Field(None, description="Python version")

    # Configuration
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration")

    # Statistics
    stats: Optional[Dict[str, Any]] = Field(None, description="Statistics")

    # Versions
    versions: Optional[List[Dict[str, Any]]] = Field(None, description="Version history")

    # Timestamps
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")

    class Config:
        from_attributes = True


class ImportTemplate(BaseModel):
    """Schema for import templates."""

    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")

    # Template configuration
    source: ImportSource = Field(..., description="Import source type")
    format: ImportFormat = Field(..., description="Import format")

    # Default options
    default_options: Dict[str, Any] = Field(..., description="Default import options")

    # Metadata
    is_public: bool = Field(False, description="Whether template is public")
    usage_count: int = Field(0, description="Usage count")

    class Config:
        from_attributes = True


class ImportProgress(BaseModel):
    """Schema for import progress tracking."""

    import_id: str = Field(..., description="Import operation ID")
    status: str = Field(..., description="Import status")
    progress_percent: float = Field(..., ge=0, le=100, description="Progress percentage")

    # Statistics
    total_files: int = Field(..., description="Total files to process")
    processed_files: int = Field(..., description="Files processed")
    successful_imports: int = Field(..., description="Successful imports")
    failed_imports: int = Field(..., description="Failed imports")

    # Current operation
    current_file: Optional[str] = Field(None, description="Currently processing file")
    current_operation: Optional[str] = Field(None, description="Current operation")

    # Timing
    started_at: datetime = Field(..., description="Import start time")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

    # Errors
    errors: List[Dict[str, Any]] = Field(..., description="Errors encountered")
    warnings: List[str] = Field(..., description="Warnings")

    class Config:
        from_attributes = True
