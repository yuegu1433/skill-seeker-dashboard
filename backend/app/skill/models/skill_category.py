"""Skill category model.

This module defines the SkillCategory model for organizing skills
into hierarchical categories.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid

Base = declarative_base()


class SkillCategory(Base):
    """Skill category model.

    Represents a category for organizing skills into hierarchical structures.
    Categories can have parent-child relationships to form trees.
    """

    __tablename__ = "skill_categories"

    # Primary key
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    # Category information
    name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Category name",
    )

    slug = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="URL-friendly identifier",
    )

    description = Column(
        Text,
        nullable=True,
        comment="Category description",
    )

    # Hierarchy
    parent_id = Column(
        String(36),
        ForeignKey("skill_categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Parent category ID for hierarchy",
    )

    level = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Hierarchy level (0 for root categories)",
    )

    path = Column(
        Text,
        nullable=True,
        comment="Full path from root (e.g., 'programming/languages/python')",
    )

    # Display properties
    icon = Column(
        String(100),
        nullable=True,
        comment="Icon name or URL",
    )

    color = Column(
        String(7),
        nullable=True,
        comment="Hex color code for category display",
    )

    sort_order = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Sort order within the same level",
    )

    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the category is active",
    )

    is_public = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the category is publicly visible",
    )

    # Metadata
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Category creation timestamp",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Category last update timestamp",
    )

    # Statistics
    skill_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of skills in this category",
    )

    # Relationships
    parent = relationship(
        "SkillCategory",
        remote_side=[id],
        backref="children",
        lazy="select",
    )

    skills = relationship(
        "Skill",
        back_populates="category",
        lazy="select",
        cascade="all, delete-orphan",
    )

    # Indexes
    __table_args__ = (
        UniqueConstraint("slug", name="uq_skill_category_slug"),
        Index("idx_skill_category_parent_id", "parent_id"),
        Index("idx_skill_category_level", "level"),
        Index("idx_skill_category_path", "path"),
        Index("idx_skill_category_sort_order", "sort_order"),
        Index("idx_skill_category_is_active", "is_active"),
        Index("idx_skill_category_is_public", "is_public"),
        Index("idx_skill_category_skill_count", "skill_count"),
    )

    def __repr__(self) -> str:
        """Return string representation of the category."""
        return f"<SkillCategory(id={self.id}, name='{self.name}', level={self.level}, path='{self.path}')>"

    @property
    def full_name(self) -> str:
        """Get the full hierarchical name of the category."""
        if self.path:
            return self.path.replace("/", " > ")
        return self.name

    def increment_skill_count(self):
        """Increment the skill count for this category."""
        self.skill_count += 1

    def decrement_skill_count(self):
        """Decrement the skill count for this category."""
        if self.skill_count > 0:
            self.skill_count -= 1

    def get_ancestors(self):
        """Get all ancestor categories in order from root to parent."""
        ancestors = []
        current = self.parent
        while current:
            ancestors.insert(0, current)
            current = current.parent
        return ancestors

    def get_descendants(self):
        """Get all descendant categories recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants
