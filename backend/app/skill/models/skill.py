"""Skill model.

This module defines the core Skill model for representing skills
in the skill management system.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    Float,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class Skill(Base):
    """Skill model.

    Represents a skill in the system with all its metadata,
    relationships, and statistics.
    """

    __tablename__ = "skills"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Basic information
    name = Column(
        String(200),
        nullable=False,
        index=True,
        comment="Skill name",
    )

    slug = Column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        comment="URL-friendly identifier",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Skill description",
    )

    # Classification
    category_id = Column(
        String(36),
        ForeignKey("skill_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Associated category ID",
    )

    # Status
    status = Column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
        comment="Skill status (draft, active, deprecated, archived)",
    )

    visibility = Column(
        String(20),
        nullable=False,
        default="public",
        index=True,
        comment="Visibility (public, private, internal)",
    )

    # Content
    content_type = Column(
        String(50),
        nullable=False,
        default="yaml",
        comment="Content type (yaml, json, python, etc.)",
    )

    # Metadata
    version = Column(
        String(50),
        nullable=False,
        default="1.0.0",
        comment="Current version",
    )

    author = Column(
        String(100),
        nullable=True,
        comment="Skill author",
    )

    maintainer = Column(
        String(100),
        nullable=True,
        comment="Skill maintainer",
    )

    license = Column(
        String(50),
        nullable=True,
        comment="License type",
    )

    homepage = Column(
        String(500),
        nullable=True,
        comment="Homepage URL",
    )

    repository = Column(
        String(500),
        nullable=True,
        comment="Repository URL",
    )

    documentation = Column(
        String(500),
        nullable=True,
        comment="Documentation URL",
    )

    # Keywords and tags
    keywords = Column(
        JSON,
        nullable=True,
        comment="List of keywords for search",
    )

    # Requirements
    python_requires = Column(
        String(50),
        nullable=True,
        comment="Required Python version",
    )

    dependencies = Column(
        JSON,
        nullable=True,
        comment="List of dependencies",
    )

    # Quality metrics
    quality_score = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Quality score (0-100)",
    )

    completeness = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Completeness score (0-100)",
    )

    # Usage statistics
    download_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of downloads",
    )

    view_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of views",
    )

    like_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of likes",
    )

    rating = Column(
        Float,
        default=0.0,
        nullable=False,
        comment="Average rating (0-5)",
    )

    rating_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of ratings",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Skill creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Skill last update timestamp",
    )

    published_at = Column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="Publication timestamp",
    )

    deprecated_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Deprecation timestamp",
    )

    archived_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Archival timestamp",
    )

    # Configuration
    config = Column(
        JSON,
        nullable=True,
        comment="Skill-specific configuration",
    )

    # Relationships
    category = relationship(
        "SkillCategory",
        back_populates="skills",
        lazy="select",
    )

    versions = relationship(
        "SkillVersion",
        back_populates="skill",
        lazy="select",
        cascade="all, delete-orphan",
        order_by="SkillVersion.created_at.desc()",
    )

    tags = relationship(
        "SkillTag",
        secondary="skill_tag_associations",
        back_populates="skills",
        lazy="select",
    )

    # Indexes
    __table_args__ = (
        UniqueConstraint("slug", name="uq_skill_slug"),
        Index("idx_skill_name", "name"),
        Index("idx_skill_status", "status"),
        Index("idx_skill_visibility", "visibility"),
        Index("idx_skill_category_id", "category_id"),
        Index("idx_skill_created_at", "created_at"),
        Index("idx_skill_updated_at", "updated_at"),
        Index("idx_skill_published_at", "published_at"),
        Index("idx_skill_quality_score", "quality_score"),
        Index("idx_skill_download_count", "download_count"),
        Index("idx_skill_rating", "rating"),
        Index("idx_skill_rating_count", "rating_count"),
    )

    def __repr__(self) -> str:
        """Return string representation of the skill."""
        return f"<Skill(id={self.id}, name='{self.name}', status='{self.status}', version='{self.version}')>"

    @property
    def current_version(self) -> "SkillVersion":
        """Get the current active version."""
        for version in self.versions:
            if version.is_active:
                return version
        return self.versions[0] if self.versions else None

    @property
    def is_active(self) -> bool:
        """Check if the skill is active."""
        return self.status == "active"

    @property
    def is_public(self) -> bool:
        """Check if the skill is publicly visible."""
        return self.visibility == "public"

    @property
    def is_deprecated(self) -> bool:
        """Check if the skill is deprecated."""
        return self.status == "deprecated"

    @property
    def is_archived(self) -> bool:
        """Check if the skill is archived."""
        return self.status == "archived"

    def activate(self):
        """Activate the skill."""
        self.status = "active"
        if not self.published_at:
            self.published_at = func.now()

    def deactivate(self):
        """Deactivate the skill."""
        self.status = "draft"

    def deprecate(self):
        """Mark the skill as deprecated."""
        self.status = "deprecated"
        self.deprecated_at = func.now()

    def archive(self):
        """Archive the skill."""
        self.status = "archived"
        self.archived_at = func.now()

    def increment_download_count(self):
        """Increment the download count."""
        self.download_count += 1

    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1

    def increment_like_count(self):
        """Increment the like count."""
        self.like_count += 1

    def update_rating(self, new_rating: float):
        """Update rating based on new rating.

        Args:
            new_rating: New rating value (0-5)
        """
        if 0 <= new_rating <= 5:
            total_rating = self.rating * self.rating_count + new_rating
            self.rating_count += 1
            self.rating = round(total_rating / self.rating_count, 2)

    def update_quality_score(self, score: float):
        """Update quality score.

        Args:
            score: Quality score (0-100)
        """
        self.quality_score = max(0, min(100, score))

    def update_completeness(self, completeness: float):
        """Update completeness score.

        Args:
            completeness: Completeness score (0-100)
        """
        self.completeness = max(0, min(100, completeness))

    def add_tag(self, tag):
        """Add a tag to the skill.

        Args:
            tag: SkillTag instance
        """
        if tag not in self.tags:
            self.tags.append(tag)
            tag.increment_usage()

    def remove_tag(self, tag):
        """Remove a tag from the skill.

        Args:
            tag: SkillTag instance
        """
        if tag in self.tags:
            self.tags.remove(tag)
            tag.decrement_usage()

    def get_version_count(self) -> int:
        """Get the number of versions.

        Returns:
            Number of versions
        """
        return len(self.versions)

    def get_latest_version(self) -> "SkillVersion":
        """Get the latest version.

        Returns:
            Latest SkillVersion instance or None
        """
        return self.versions[0] if self.versions else None

    def get_stable_versions(self) -> list:
        """Get all stable versions.

        Returns:
            List of stable SkillVersion instances
        """
        return [v for v in self.versions if v.is_stable]

    def to_dict(self, include_versions: bool = False, include_tags: bool = False) -> dict:
        """Convert skill to dictionary.

        Args:
            include_versions: Whether to include versions
            include_tags: Whether to include tags

        Returns:
            Dictionary representation
        """
        data = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "status": self.status,
            "visibility": self.visibility,
            "version": self.version,
            "author": self.author,
            "maintainer": self.maintainer,
            "license": self.license,
            "homepage": self.homepage,
            "repository": self.repository,
            "documentation": self.documentation,
            "keywords": self.keywords,
            "python_requires": self.python_requires,
            "dependencies": self.dependencies,
            "quality_score": self.quality_score,
            "completeness": self.completeness,
            "download_count": self.download_count,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "rating": self.rating,
            "rating_count": self.rating_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "deprecated_at": self.deprecated_at.isoformat() if self.deprecated_at else None,
            "archived_at": self.archived_at.isoformat() if self.archived_at else None,
        }

        if include_versions:
            data["versions"] = [
                {
                    "id": v.id,
                    "version": v.version,
                    "description": v.description,
                    "is_active": v.is_active,
                    "is_stable": v.is_stable,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                }
                for v in self.versions
            ]

        if include_tags:
            data["tags"] = [
                {"id": tag.id, "name": tag.name, "color": tag.color}
                for tag in self.tags
            ]

        return data


# Association table for many-to-many relationship between skills and tags
class SkillTagAssociation(Base):
    """Association table for skill-tag many-to-many relationship."""

    __tablename__ = "skill_tag_associations"

    skill_id = Column(
        String(36),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )

    tag_id = Column(
        String(36),
        ForeignKey("skill_tags.id", ondelete="CASCADE"),
        primary_key=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Indexes
    __table_args__ = (
        Index("idx_skill_tag_skill_id", "skill_id"),
        Index("idx_skill_tag_tag_id", "tag_id"),
    )
