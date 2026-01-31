"""FileVersion model for managing file versions in MinIO storage.

This module defines the FileVersion SQLAlchemy model for tracking
file versions and history in the MinIO storage system.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    BigInteger,
    Integer,
    Index,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class FileVersion(Base):
    """File version model for version control.

    Tracks all versions of files in the MinIO storage system,
    providing complete version history and rollback capabilities.
    """

    __tablename__ = "file_versions"

    # Primary key and identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="版本ID")
    file_id = Column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="文件ID",
    )

    # Version information
    version_id = Column(
        String(50),
        nullable=False,
        comment="版本ID (时间戳)",
    )
    version_number = Column(
        Integer,
        nullable=False,
        comment="版本号 (1, 2, 3, ...)",
    )

    # File information
    object_name = Column(
        String(500),
        nullable=False,
        comment="版本对象名",
    )
    file_size = Column(
        BigInteger,
        default=0,
        comment="文件大小(字节)",
    )
    checksum = Column(
        String(64),
        comment="SHA256校验和",
    )

    # Version metadata
    comment = Column(
        Text,
        comment="版本说明",
    )
    version_metadata = Column(
        JSONB,
        default=dict,
        comment="版本元数据",
    )

    # Timestamps and author
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        comment="创建时间",
    )
    created_by = Column(
        String(100),
        comment="创建者",
    )

    # Relationships
    file = relationship(
        "SkillFile",
        back_populates="versions",
        foreign_keys=[file_id],
    )

    def __repr__(self) -> str:
        """Return string representation of the FileVersion."""
        return (
            f"<FileVersion(id={self.id}, file_id={self.file_id}, "
            f"version_id='{self.version_id}', version_number={self.version_number})>"
        )

    @property
    def is_latest(self) -> bool:
        """Check if this is the latest version."""
        if not self.file:
            return False
        latest_version = max(self.file.versions, key=lambda v: v.version_number)
        return self.version_number == latest_version.version_number

    @property
    def size_human_readable(self) -> str:
        """Get human-readable size string."""
        size_bytes = self.file_size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    def to_dict(self) -> dict:
        """Convert FileVersion to dictionary."""
        return {
            "id": str(self.id),
            "file_id": str(self.file_id),
            "version_id": self.version_id,
            "version_number": self.version_number,
            "object_name": self.object_name,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "comment": self.comment,
            "metadata": self.version_metadata or {},
            "is_latest": self.is_latest,
            "size_human_readable": self.size_human_readable,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.created_by,
        }

    @classmethod
    def generate_version_id(cls) -> str:
        """Generate a unique version ID based on timestamp."""
        return datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")

    @classmethod
    def create_initial_version(
        cls,
        file_id: uuid.UUID,
        object_name: str,
        file_size: int,
        checksum: str,
        created_by: Optional[str] = None,
        comment: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> "FileVersion":
        """Create the initial version of a file."""
        version_id = cls.generate_version_id()
        return cls(
            file_id=file_id,
            version_id=version_id,
            version_number=1,
            object_name=object_name,
            file_size=file_size,
            checksum=checksum,
            comment=comment or "Initial version",
            created_by=created_by,
            metadata=metadata or {},
        )


# Database indexes for performance optimization
Index("idx_file_versions_file_id", FileVersion.file_id)
Index("idx_file_versions_version_id", FileVersion.version_id)
Index("idx_file_versions_version_number", FileVersion.version_number)
Index("idx_file_versions_created_at", FileVersion.created_at.desc())
Index("idx_file_versions_created_by", FileVersion.created_by)

# Composite indexes for common queries
Index(
    "idx_file_versions_file_number",
    FileVersion.file_id,
    FileVersion.version_number,
)
Index(
    "idx_file_versions_file_created",
    FileVersion.file_id,
    FileVersion.created_at.desc(),
)
