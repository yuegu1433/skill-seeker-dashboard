"""SkillFile model for managing skill files in MinIO storage.

This module defines the SkillFile SQLAlchemy model for tracking
skill files stored in MinIO object storage.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    BigInteger,
    Boolean,
    Index,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class SkillFile(Base):
    """Skill file model for MinIO object storage.

    Tracks all files associated with skills in the MinIO storage system,
    including metadata, access control, and versioning information.
    """

    __tablename__ = "skill_files"

    # Primary key and basic fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="文件ID")
    skill_id = Column(UUID(as_uuid=True), nullable=False, index=True, comment="技能ID")

    # File information
    object_name = Column(
        String(500),
        nullable=False,
        comment="MinIO对象名",
    )
    file_path = Column(
        String(500),
        nullable=False,
        comment="逻辑文件路径",
    )
    file_type = Column(
        String(20),
        nullable=False,
        comment="文件类型 (skill_file, reference, config, metadata, log)",
    )

    # Storage information
    file_size = Column(
        BigInteger,
        default=0,
        comment="文件大小(字节)",
    )
    content_type = Column(
        String(100),
        comment="MIME类型",
    )
    checksum = Column(
        String(64),
        comment="SHA256校验和",
    )

    # Metadata and tags
    file_metadata = Column(
        JSONB,
        default=dict,
        comment="文件元数据",
    )
    tags = Column(
        JSONB,
        default=list,
        comment="文件标签",
    )

    # Access control
    is_public = Column(
        Boolean,
        default=False,
        comment="是否公开访问",
    )
    permissions = Column(
        JSONB,
        default=dict,
        comment="权限配置",
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
    last_accessed_at = Column(
        DateTime(timezone=True),
        comment="最后访问时间",
    )

    # Relationships
    skill = relationship(
        "Skill",
        back_populates="files",
        foreign_keys=[skill_id],
    )
    versions = relationship(
        "FileVersion",
        back_populates="file",
        cascade="all, delete-orphan",
        order_by="FileVersion.created_at.desc()",
    )

    def __repr__(self) -> str:
        """Return string representation of the SkillFile."""
        return (
            f"<SkillFile(id={self.id}, skill_id={self.skill_id}, "
            f"file_path='{self.file_path}', file_type='{self.file_type}')>"
        )

    @property
    def is_directory(self) -> bool:
        """Check if this represents a directory."""
        return self.file_path.endswith("/") or self.file_type == "directory"

    @property
    def extension(self) -> Optional[str]:
        """Get file extension."""
        if self.is_directory:
            return None
        return self.file_path.split(".")[-1].lower() if "." in self.file_path else None

    def to_dict(self) -> dict:
        """Convert SkillFile to dictionary."""
        return {
            "id": str(self.id),
            "skill_id": str(self.skill_id),
            "object_name": self.object_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "content_type": self.content_type,
            "checksum": self.checksum,
            "metadata": self.file_metadata or {},
            "tags": self.tags or [],
            "is_public": self.is_public,
            "permissions": self.permissions or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
            "extension": self.extension,
        }


# Database indexes for performance optimization
Index("idx_skill_files_skill_id", SkillFile.skill_id)
Index("idx_skill_files_file_type", SkillFile.file_type)
Index("idx_skill_files_created_at", SkillFile.created_at.desc())
Index("idx_skill_files_updated_at", SkillFile.updated_at.desc())
Index("idx_skill_files_is_public", SkillFile.is_public)
Index("idx_skill_files_object_name", SkillFile.object_name)

# Composite indexes for common queries
Index(
    "idx_skill_files_skill_type",
    SkillFile.skill_id,
    SkillFile.file_type,
)
Index(
    "idx_skill_files_skill_public",
    SkillFile.skill_id,
    SkillFile.is_public,
)
