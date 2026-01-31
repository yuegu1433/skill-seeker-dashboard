"""Skill version model.

This module defines the SkillVersion model for tracking changes
and maintaining version history of skills.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    JSON,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
import hashlib

Base = declarative_base()


class SkillVersion(Base):
    """Skill version model.

    Represents a version of a skill, tracking changes over time.
    Each skill can have multiple versions, with one being current.
    """

    __tablename__ = "skill_versions"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Version information
    version = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Version number or tag (e.g., '1.0.0', 'v2.1')",
    )

    skill_id = Column(
        String(36),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Associated skill ID",
    )

    # Content
    content = Column(
        Text,
        nullable=False,
        comment="Skill content/data (YAML, JSON, or other format)",
    )

    content_format = Column(
        String(20),
        nullable=False,
        default="yaml",
        comment="Format of content (yaml, json, etc.)",
    )

    # Metadata
    description = Column(
        Text,
        nullable=True,
        comment="Version description or changelog",
    )

    change_log = Column(
        JSON,
        nullable=True,
        comment="Structured changelog with added/removed/modified items",
    )

    # Version properties
    is_active = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the active version",
    )

    is_stable = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is a stable release",
    )

    is_latest = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the latest version",
    )

    # Statistics
    content_size = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Size of content in bytes",
    )

    content_hash = Column(
        String(64),
        nullable=False,
        index=True,
        comment="SHA-256 hash of content for deduplication",
    )

    line_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of lines in the content",
    )

    # Dependency information
    dependencies = Column(
        JSON,
        nullable=True,
        comment="List of skill dependencies in this version",
    )

    peer_dependencies = Column(
        JSON,
        nullable=True,
        comment="List of peer dependencies",
    )

    # Compatibility
    python_version = Column(
        String(20),
        nullable=True,
        comment="Required Python version",
    )

    api_version = Column(
        String(50),
        nullable=True,
        comment="Compatible API version",
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Version creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Version last update timestamp",
    )

    # Usage statistics
    download_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of downloads for this version",
    )

    rating = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Average rating (1-5)",
    )

    rating_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of ratings",
    )

    # Relationships
    skill = relationship(
        "Skill",
        back_populates="versions",
        lazy="select",
    )

    # Indexes
    __table_args__ = (
        UniqueConstraint(
            "skill_id",
            "version",
            name="uq_skill_version_skill_id_version",
        ),
        Index("idx_skill_version_skill_id", "skill_id"),
        Index("idx_skill_version_is_active", "is_active"),
        Index("idx_skill_version_is_latest", "is_latest"),
        Index("idx_skill_version_is_stable", "is_stable"),
        Index("idx_skill_version_created_at", "created_at"),
        Index("idx_skill_version_download_count", "download_count"),
        Index("idx_skill_version_content_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        """Return string representation of the version."""
        return f"<SkillVersion(id={self.id}, skill_id={self.skill_id}, version='{self.version}', is_active={self.is_active})>"

    def calculate_content_hash(self) -> str:
        """Calculate SHA-256 hash of content.

        Returns:
            Hex string of the hash
        """
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def update_content_stats(self):
        """Update content statistics (size, hash, line count)."""
        self.content_size = len(self.content.encode("utf-8"))
        self.content_hash = self.calculate_content_hash()
        self.line_count = len(self.content.splitlines())

    def increment_download_count(self):
        """Increment the download count."""
        self.download_count += 1

    def update_rating(self, new_rating: int):
        """Update rating based on new rating.

        Args:
            new_rating: New rating value (1-5)
        """
        if 1 <= new_rating <= 5:
            total_rating = self.rating * self.rating_count + new_rating
            self.rating_count += 1
            self.rating = round(total_rating / self.rating_count, 2)

    @classmethod
    def generate_version_number(
        cls,
        major: int = 1,
        minor: int = 0,
        patch: int = 0,
        prerelease: str = None,
    ) -> str:
        """Generate a version number.

        Args:
            major: Major version
            minor: Minor version
            patch: Patch version
            prerelease: Prerelease identifier (e.g., 'alpha', 'beta', 'rc.1')

        Returns:
            Formatted version string
        """
        version = f"{major}.{minor}.{patch}"
        if prerelease:
            version += f"-{prerelease}"
        return version

    def get_comparable_version(self) -> tuple:
        """Get comparable version tuple for sorting.

        Returns:
            Tuple of (major, minor, patch, is_prerelease, prerelease_id)
        """
        import re

        # Parse version string
        match = re.match(r"(\d+)\.(\d+)\.(\d+)(?:-([\w.]+))?", self.version)
        if match:
            major, minor, patch, prerelease = match.groups()
            return (
                int(major),
                int(minor),
                int(patch),
                prerelease is not None,
                prerelease or "",
            )
        return (0, 0, 0, False, "")
