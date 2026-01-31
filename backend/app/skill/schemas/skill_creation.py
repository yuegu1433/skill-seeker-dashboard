"""Skill creation schemas.

This module defines Pydantic schemas specifically for skill creation
with comprehensive validation.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re


class ContentFormat(str, Enum):
    """Supported content formats."""
    YAML = "yaml"
    JSON = "json"
    PYTHON = "python"
    MARKDOWN = "markdown"
    TEXT = "text"


class LicenseType(str, Enum):
    """Common license types."""
    MIT = "MIT"
    APACHE_2_0 = "Apache-2.0"
    GPL_3_0 = "GPL-3.0"
    BSD_3_CLAUSE = "BSD-3-Clause"
    BSD_2_CLAUSE = "BSD-2-Clause"
    ISC = "ISC"
    UNLICENSE = "Unlicense"
    CUSTOM = "custom"


class SkillCreationRequest(BaseModel):
    """Schema for skill creation request."""

    # Required fields
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Skill name (required)",
        example="Image Processing Skill",
    )

    description: Optional[str] = Field(
        None,
        max_length=5000,
        description="Detailed description of the skill",
        example="A comprehensive skill for processing and analyzing images...",
    )

    # Classification
    category_id: Optional[str] = Field(
        None,
        description="ID of the category to assign",
        example="cat_1234567890",
    )

    # Content
    content: str = Field(
        ...,
        min_length=1,
        max_length=1000000,
        description="Skill content (required)",
        example="name: Image Processing\nversion: 1.0.0\n...",
    )

    content_format: ContentFormat = Field(
        ContentFormat.YAML,
        description="Format of the skill content",
        example="yaml",
    )

    # Versioning
    version: str = Field(
        "1.0.0",
        description="Initial version number",
        example="1.0.0",
    )

    # Metadata
    author: Optional[str] = Field(
        None,
        max_length=100,
        description="Author name or ID",
        example="john_doe",
    )

    maintainer: Optional[str] = Field(
        None,
        max_length=100,
        description="Maintainer name or ID",
        example="jane_doe",
    )

    license: Optional[Union[LicenseType, str]] = Field(
        None,
        description="License type",
        example="MIT",
    )

    # URLs
    homepage: Optional[str] = Field(
        None,
        description="Project homepage URL",
        example="https://github.com/user/skill-project",
    )

    repository: Optional[str] = Field(
        None,
        description="Source repository URL",
        example="https://github.com/user/skill-project.git",
    )

    documentation: Optional[str] = Field(
        None,
        description="Documentation URL",
        example="https://skill-project.readthedocs.io",
    )

    # Search and classification
    keywords: Optional[List[str]] = Field(
        None,
        max_items=20,
        max_length=50,
        description="Keywords for search and discovery",
        example=["image", "processing", "computer-vision", "ai"],
    )

    # Requirements
    python_requires: Optional[str] = Field(
        None,
        description="Required Python version",
        example=">=3.8",
    )

    dependencies: Optional[List[str]] = Field(
        None,
        max_items=100,
        description="Required dependencies",
        example=["pillow", "opencv-python", "numpy"],
    )

    # Configuration
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Skill-specific configuration",
        example={
            "max_image_size": "10MB",
            "supported_formats": ["jpg", "png", "bmp"],
            "enable_gpu": True,
        },
    )

    # Status
    status: str = Field(
        "draft",
        description="Initial status",
        example="draft",
    )

    visibility: str = Field(
        "public",
        description="Visibility level",
        example="public",
    )

    # Tags
    tags: Optional[List[str]] = Field(
        None,
        max_items=20,
        description="Tags to associate with the skill",
        example=["computer-vision", "image-processing", "ai"],
    )

    # Validation
    @validator("name")
    def validate_name(cls, v):
        """Validate skill name."""
        if not v or not v.strip():
            raise ValueError("Skill name cannot be empty")

        # Remove extra whitespace
        v = v.strip()

        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
            raise ValueError("Skill name contains invalid characters")

        return v

    @validator("description")
    def validate_description(cls, v):
        """Validate description."""
        if v:
            v = v.strip()
            if len(v) < 10:
                raise ValueError("Description must be at least 10 characters")
        return v

    @validator("version")
    def validate_version(cls, v):
        """Validate version format."""
        if v:
            # Semantic versioning pattern
            version_pattern = r"^\d+(\.\d+){0,3}(-[a-zA-Z0-9\-]+)?$"
            if not re.match(version_pattern, v):
                raise ValueError(
                    "Invalid version format. Use semantic versioning (e.g., '1.0.0', '2.1.3', '1.0.0-alpha')"
                )
        return v

    @validator("keywords")
    def validate_keywords(cls, v):
        """Validate keywords list."""
        if v:
            # Remove duplicates and empty values
            v = [kw.strip().lower() for kw in v if kw and kw.strip()]
            v = list(dict.fromkeys(v))  # Remove duplicates while preserving order

            if len(v) > 20:
                raise ValueError("Maximum 20 keywords allowed")

            for keyword in v:
                if len(keyword) > 50:
                    raise ValueError(f"Keyword '{keyword}' exceeds 50 characters")

                if not re.match(r"^[a-z0-9\-]+$", keyword):
                    raise ValueError(
                        f"Keyword '{keyword}' contains invalid characters. Use lowercase letters, numbers, and hyphens only"
                    )
        return v

    @validator("dependencies")
    def validate_dependencies(cls, v):
        """Validate dependencies list."""
        if v:
            # Remove duplicates and empty values
            v = [dep.strip() for dep in v if dep and dep.strip()]
            v = list(dict.fromkeys(v))  # Remove duplicates

            if len(v) > 100:
                raise ValueError("Maximum 100 dependencies allowed")

            for dep in v:
                if len(dep) > 200:
                    raise ValueError(f"Dependency '{dep}' exceeds 200 characters")

                # Basic dependency format check
                if not re.match(r"^[a-zA-Z0-9\-_.]+", dep):
                    raise ValueError(f"Dependency '{dep}' has invalid format")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        """Validate tags list."""
        if v:
            # Remove duplicates and empty values
            v = [tag.strip() for tag in v if tag and tag.strip()]
            v = list(dict.fromkeys(v))  # Remove duplicates

            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")

            for tag in v:
                if len(tag) > 50:
                    raise ValueError(f"Tag '{tag}' exceeds 50 characters")

                if not re.match(r"^[a-zA-Z0-9\s\-_]+$", tag):
                    raise ValueError(f"Tag '{tag}' contains invalid characters")
        return v

    @validator("content")
    def validate_content(cls, v):
        """Validate content."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")

        # Check content size
        if len(v) > 1000000:  # 1MB
            raise ValueError("Content too large (maximum 1MB)")

        # Basic content structure validation
        content_lines = v.splitlines()
        if len(content_lines) < 3:
            raise ValueError("Content must have at least 3 lines")

        return v.strip()

    @validator("python_requires")
    def validate_python_requires(cls, v):
        """Validate Python version requirement."""
        if v:
            # Basic Python version format check
            python_pattern = r"^(>=|<=|>|<|==|!=)?\s*\d+(\.\d+){0,2}$"
            if not re.match(python_pattern, v):
                raise ValueError(
                    "Invalid Python version format. Use formats like '>=3.8', '==3.9', '<4.0'"
                )
        return v

    @validator("license")
    def validate_license(cls, v):
        """Validate license."""
        if v and isinstance(v, str):
            # Check if it's a known license
            known_licenses = [license.value for license in LicenseType]
            if v not in known_licenses and v != "custom":
                raise ValueError(f"Unknown license '{v}'. Use a known license or 'custom'")
        return v

    @validator("config")
    def validate_config(cls, v):
        """Validate configuration."""
        if v:
            # Check config size
            config_str = str(v)
            if len(config_str) > 10000:
                raise ValueError("Configuration too large (maximum 10KB)")

            # Basic structure validation
            if not isinstance(v, dict):
                raise ValueError("Configuration must be a dictionary")

            # Check nested depth
            def check_depth(obj, depth=0, max_depth=5):
                if depth > max_depth:
                    raise ValueError("Configuration nested too deeply (maximum 5 levels)")

                if isinstance(obj, dict):
                    for value in obj.values():
                        check_depth(value, depth + 1, max_depth)
                elif isinstance(obj, list):
                    for item in obj:
                        check_depth(item, depth + 1, max_depth)

            check_depth(v)
        return v

    @validator("homepage", "repository", "documentation")
    def validate_urls(cls, v):
        """Validate URLs."""
        if v:
            # Basic URL validation
            url_pattern = r"^(https?://)[a-zA-Z0-9\-_.]+(\.[a-zA-Z]{2,})+([/\w\-._~:/?#[\]@!$&'()*+,;=]*)?$"
            if not re.match(url_pattern, v):
                raise ValueError(f"Invalid URL format: {v}")
        return v


class SkillCreationResponse(BaseModel):
    """Schema for skill creation response."""

    success: bool = Field(..., description="Whether creation was successful")
    skill_id: str = Field(..., description="ID of created skill")
    skill_slug: str = Field(..., description="URL-friendly slug")
    version_id: str = Field(..., description="ID of initial version")
    message: str = Field(..., description="Response message")
    created_at: datetime = Field(..., description="Creation timestamp")

    # Skill summary
    name: str = Field(..., description="Skill name")
    version: str = Field(..., description="Initial version")
    status: str = Field(..., description="Initial status")
    category_id: Optional[str] = Field(None, description="Category ID")

    # URLs
    api_url: str = Field(..., description="API URL for the skill")
    public_url: Optional[str] = Field(None, description="Public URL")

    # Validation warnings
    warnings: Optional[List[str]] = Field(None, description="Validation warnings")

    class Config:
        from_attributes = True


class SkillTemplate(BaseModel):
    """Schema for skill creation templates."""

    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    category_id: Optional[str] = Field(None, description="Default category")
    content: str = Field(..., description="Template content")
    content_format: ContentFormat = Field(ContentFormat.YAML, description="Content format")
    version: str = Field("1.0.0", description="Default version")
    keywords: Optional[List[str]] = Field(None, description="Default keywords")
    dependencies: Optional[List[str]] = Field(None, description="Default dependencies")
    config: Optional[Dict[str, Any]] = Field(None, description="Default configuration")

    # Template metadata
    tags: Optional[List[str]] = Field(None, description="Template tags")
    is_public: bool = Field(True, description="Whether template is public")
    usage_count: int = Field(0, description="Number of times used")

    class Config:
        from_attributes = True


class SkillCloneRequest(BaseModel):
    """Schema for cloning an existing skill."""

    # Source skill
    source_skill_id: str = Field(..., description="ID of skill to clone")

    # New skill details
    new_name: Optional[str] = Field(None, description="Name for cloned skill")
    new_description: Optional[str] = Field(None, description="Description for cloned skill")
    new_version: Optional[str] = Field(None, description="Version for cloned skill")

    # Options
    clone_versions: bool = Field(True, description="Whether to clone version history")
    clone_metadata: bool = Field(True, description="Whether to clone metadata")
    clone_tags: bool = Field(True, description="Whether to clone tags")
    clone_config: bool = Field(False, description="Whether to clone configuration")

    @validator("new_name")
    def validate_new_name(cls, v):
        """Validate new skill name."""
        if v:
            if len(v) > 200:
                raise ValueError("Name cannot exceed 200 characters")

            if not re.match(r"^[a-zA-Z0-9\s\-_]+$", v):
                raise ValueError("Name contains invalid characters")
        return v

    @validator("new_version")
    def validate_new_version(cls, v):
        """Validate new version."""
        if v:
            version_pattern = r"^\d+(\.\d+){0,3}(-[a-zA-Z0-9\-]+)?$"
            if not re.match(version_pattern, v):
                raise ValueError("Invalid version format")
        return v
