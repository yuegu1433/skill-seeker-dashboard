"""Skill tag model.

This module defines the SkillTag model for categorizing and tagging skills.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class SkillTag(Base):
    """Skill tag model.

    Represents a tag that can be associated with skills for categorization
    and filtering purposes.
    """

    __tablename__ = "skill_tags"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Tag information
    name = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Tag name (unique)",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Tag description",
    )

    color = Column(
        String(7),
        nullable=True,
        comment="Hex color code for tag display",
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Tag creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Tag last update timestamp",
    )

    # Usage statistics
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of skills using this tag",
    )

    # Relationships
    skills = relationship(
        "Skill",
        secondary="skill_tag_associations",
        back_populates="tags",
        lazy="select",
    )

    # Indexes
    __table_args__ = (
        UniqueConstraint("name", name="uq_skill_tag_name"),
        Index("idx_skill_tag_name", "name"),
        Index("idx_skill_tag_usage_count", "usage_count"),
        Index("idx_skill_tag_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        """Return string representation of the tag."""
        return f"<SkillTag(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"

    def increment_usage(self):
        """Increment the usage count for this tag."""
        self.usage_count += 1

    def decrement_usage(self):
        """Decrement the usage count for this tag."""
        if self.usage_count > 0:
            self.usage_count -= 1
