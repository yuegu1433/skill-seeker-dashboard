"""Skill model for managing skills in the storage system.

This module defines the base Skill SQLAlchemy model for establishing
relationships with skill files in the MinIO storage system.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Skill(Base):
    """Skill model for establishing relationships with files.

    This is a simplified skill model for establishing relationships
    with skill files in the storage system. In a full implementation,
    this would be extended with more skill-specific fields.
    """

    __tablename__ = "skills"

    # Primary key and identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="技能ID")
    name = Column(
        String(100),
        nullable=False,
        comment="技能名称",
    )
    description = Column(
        Text,
        comment="技能描述",
    )
    platform = Column(
        String(20),
        nullable=False,
        comment="目标平台 (claude, gemini, openai, markdown)",
    )

    # Status and metadata
    status = Column(
        String(20),
        default="creating",
        comment="技能状态 (creating, completed, failed, enhancing)",
    )
    source_type = Column(
        String(20),
        nullable=False,
        comment="来源类型 (github, web, upload, multi)",
    )

    # Configuration and metadata
    skill_metadata = Column(
        JSONB,
        default=dict,
        comment="技能元数据",
    )
    config = Column(
        JSONB,
        default=dict,
        comment="技能配置",
    )

    # Storage-related fields
    storage_bucket = Column(
        String(50),
        default="skillseekers-skills",
        comment="存储桶",
    )
    storage_prefix = Column(
        String(200),
        comment="存储前缀",
    )
    file_count = Column(
        default=0,
        comment="文件数量",
    )
    total_size_bytes = Column(
        default=0,
        comment="总大小(字节)",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        comment="创建时间",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    # Relationships
    files = relationship(
        "SkillFile",
        back_populates="skill",
        cascade="all, delete-orphan",
        order_by="SkillFile.created_at.desc()",
    )

    def __repr__(self) -> str:
        """Return string representation of the Skill."""
        return (
            f"<Skill(id={self.id}, name='{self.name}', "
            f"platform='{self.platform}', status='{self.status}')>"
        )

    @property
    def is_completed(self) -> bool:
        """Check if skill creation is completed."""
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        """Check if skill creation failed."""
        return self.status == "failed"

    @property
    def is_creating(self) -> bool:
        """Check if skill is being created."""
        return self.status == "creating"

    @property
    def size_human_readable(self) -> str:
        """Get human-readable total size."""
        size_bytes = self.total_size_bytes
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    def to_dict(self) -> dict:
        """Convert Skill to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "platform": self.platform,
            "status": self.status,
            "source_type": self.source_type,
            "metadata": self.skill_metadata or {},
            "config": self.config or {},
            "storage_bucket": self.storage_bucket,
            "storage_prefix": self.storage_prefix,
            "file_count": self.file_count,
            "total_size_bytes": self.total_size_bytes,
            "size_human_readable": self.size_human_readable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_completed": self.is_completed,
            "is_failed": self.is_failed,
            "is_creating": self.is_creating,
        }


# Database indexes for performance optimization
Index("idx_skills_name", Skill.name)
Index("idx_skills_platform", Skill.platform)
Index("idx_skills_status", Skill.status)
Index("idx_skills_source_type", Skill.source_type)
Index("idx_skills_created_at", Skill.created_at.desc())
Index("idx_skills_updated_at", Skill.updated_at.desc())

# Composite indexes for common queries
Index(
    "idx_skills_platform_status",
    Skill.platform,
    Skill.status,
)
Index(
    "idx_skills_status_created",
    Skill.status,
    Skill.created_at.desc(),
)
