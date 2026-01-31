"""File Version Model.

This module defines the FileVersion model for version tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    BigInteger,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


class VersionStatus(str, Enum):
    """File version status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    LOCKED = "locked"


class FileVersion(Base):
    """FileVersion model for tracking file versions.

    Attributes:
        id: Unique version identifier
        file_id: Associated file identifier
        version: Version number or tag
        content: File content (for text files)
        content_hash: Hash of the content
        checksum: File checksum
        size: File size in bytes
        mime_type: MIME type
        author_id: Version author identifier
        author_name: Author name
        message: Version message/description
        change_log: Detailed change log
        status: Version status
        is_current: Whether this is the current version
        parent_version_id: Parent version identifier
        storage_key: Storage key in MinIO
        metadata: Additional metadata (JSON)
        compression_ratio: Compression ratio if compressed
        diff_from_previous: Diff from previous version
        created_at: Creation timestamp
        updated_at: Last update timestamp
        access_count: Number of times accessed
        download_count: Number of times downloaded
    """

    __tablename__ = "file_versions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)

    # File association
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False, index=True)

    # Version information
    version = Column(String(50), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    version_tag = Column(String(100), nullable=True, index=True)

    # Content information
    content = Column(Text, nullable=True)  # For text files
    content_hash = Column(String(64), nullable=True, index=True)
    checksum = Column(String(64), nullable=True, index=True)
    size = Column(BigInteger, nullable=False, default=0)

    # File properties
    mime_type = Column(String(100), nullable=True)
    encoding = Column(String(50), nullable=True)

    # Author information
    author_id = Column(String(100), nullable=False, index=True)
    author_name = Column(String(100), nullable=True)

    # Version details
    message = Column(Text, nullable=True)
    change_log = Column(Text, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default=VersionStatus.ACTIVE, index=True)
    is_current = Column(Boolean, nullable=False, default=False, index=True)

    # Version hierarchy
    parent_version_id = Column(UUID(as_uuid=True), ForeignKey("file_versions.id"), nullable=True)

    # Storage
    storage_key = Column(String(500), nullable=False, index=True)

    # Additional data
    metadata = Column(JSON, nullable=True, default=dict)
    compression_ratio = Column(Integer, nullable=True)  # Percentage
    diff_from_previous = Column(Text, nullable=True)

    # Statistics
    access_count = Column(Integer, nullable=False, default=0)
    download_count = Column(Integer, nullable=False, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    # Relationships
    file = relationship("File", back_populates="versions", lazy="select")
    parent_version = relationship("FileVersion", remote_side=[id], lazy="select")
    child_versions = relationship("FileVersion", back_populates="parent_version", lazy="select")

    # Indexes
    __table_args__ = (
        Index("ix_file_versions_file_current", "file_id", "is_current"),
        Index("ix_file_versions_file_version", "file_id", "version"),
        Index("ix_file_versions_author", "author_id", "created_at"),
        Index("ix_file_versions_status", "status"),
        UniqueConstraint("file_id", "version", name="uq_file_versions_file_version"),
    )

    def __repr__(self) -> str:
        """Return string representation of the FileVersion."""
        return f"<FileVersion(id={self.id}, file_id={self.file_id}, version={self.version}, is_current={self.is_current})>"

    @validates("version")
    def validate_version(self, key: str, version: str) -> str:
        """Validate version string."""
        if not version or len(version.strip()) == 0:
            raise ValueError("Version cannot be empty")
        if len(version) > 50:
            raise ValueError("Version cannot exceed 50 characters")
        return version.strip()

    @validates("size")
    def validate_size(self, key: str, size: int) -> int:
        """Validate size."""
        if size < 0:
            raise ValueError("Size cannot be negative")
        return size

    @property
    def age_days(self) -> int:
        """Calculate version age in days."""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

    @property
    def size_mb(self) -> float:
        """Get version size in MB."""
        return round(self.size / (1024 * 1024), 2)

    @property
    def size_kb(self) -> float:
        """Get version size in KB."""
        return round(self.size / 1024, 2)

    @property
    def human_readable_size(self) -> str:
        """Get human-readable file size."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.1f} GB"

    @property
    def is_text_file(self) -> bool:
        """Check if this is a text file version."""
        return self.content is not None

    @property
    def compression_info(self) -> Optional[Dict[str, Any]]:
        """Get compression information."""
        if self.compression_ratio:
            return {
                "ratio": self.compression_ratio,
                "original_size": self.size * 100 / max(1, 100 - self.compression_ratio),
                "compressed_size": self.size,
            }
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert version to dictionary."""
        return {
            "id": str(self.id),
            "file_id": str(self.file_id),
            "version": self.version,
            "version_number": self.version_number,
            "version_tag": self.version_tag,
            "content_hash": self.content_hash,
            "checksum": self.checksum,
            "size": self.size,
            "size_mb": self.size_mb,
            "human_readable_size": self.human_readable_size,
            "mime_type": self.mime_type,
            "encoding": self.encoding,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "message": self.message,
            "change_log": self.change_log,
            "status": self.status,
            "is_current": self.is_current,
            "parent_version_id": str(self.parent_version_id) if self.parent_version_id else None,
            "storage_key": self.storage_key,
            "metadata": self.metadata or {},
            "compression_ratio": self.compression_ratio,
            "compression_info": self.compression_info,
            "diff_from_previous": self.diff_from_previous,
            "access_count": self.access_count,
            "download_count": self.download_count,
            "is_text_file": self.is_text_file,
            "age_days": self.age_days,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert version to summary dictionary."""
        return {
            "id": str(self.id),
            "version": self.version,
            "version_number": self.version_number,
            "author_id": self.author_id,
            "author_name": self.author_name,
            "message": self.message,
            "status": self.status,
            "is_current": self.is_current,
            "size": self.size,
            "human_readable_size": self.human_readable_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def increment_access_count(self):
        """Increment access count."""
        self.access_count += 1

    def increment_download_count(self):
        """Increment download count."""
        self.download_count += 1

    def set_as_current(self):
        """Mark this version as current."""
        self.is_current = True
        self.status = VersionStatus.ACTIVE

    def unset_as_current(self):
        """Unmark this version as current."""
        self.is_current = False

    def archive(self):
        """Archive version."""
        self.status = VersionStatus.ARCHIVED

    def lock(self):
        """Lock version."""
        self.status = VersionStatus.LOCKED

    def unlock(self):
        """Unlock version."""
        self.status = VersionStatus.ACTIVE

    def update_content(self, content: str, content_hash: str, size: int):
        """Update version content."""
        self.content = content
        self.content_hash = content_hash
        self.size = size
        self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: Any):
        """Add metadata to version."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def remove_metadata(self, key: str):
        """Remove metadata from version."""
        if self.metadata and key in self.metadata:
            del self.metadata[key]

    def update_change_log(self, change_log: str):
        """Update change log."""
        self.change_log = change_log
        self.updated_at = datetime.utcnow()

    @classmethod
    def create_initial_version(
        cls,
        file_id: str,
        author_id: str,
        author_name: str,
        storage_key: str,
        size: int,
        mime_type: str,
        content: Optional[str] = None,
        checksum: Optional[str] = None,
        message: str = "Initial version",
    ) -> "FileVersion":
        """Create initial version for a file."""
        return cls(
            file_id=file_id,
            version="1.0.0",
            version_number=1,
            content=content,
            checksum=checksum,
            size=size,
            mime_type=mime_type,
            author_id=author_id,
            author_name=author_name,
            message=message,
            status=VersionStatus.ACTIVE,
            is_current=True,
            storage_key=storage_key,
        )

    @classmethod
    def create_new_version(
        cls,
        file_id: str,
        parent_version_id: str,
        version_number: int,
        author_id: str,
        author_name: str,
        storage_key: str,
        size: int,
        mime_type: str,
        content: Optional[str] = None,
        checksum: Optional[str] = None,
        message: str = "New version",
        version_tag: Optional[str] = None,
    ) -> "FileVersion":
        """Create new version based on parent version."""
        version_str = f"{version_number}.0.0"

        return cls(
            file_id=file_id,
            parent_version_id=parent_version_id,
            version=version_str,
            version_number=version_number,
            content=content,
            checksum=checksum,
            size=size,
            mime_type=mime_type,
            author_id=author_id,
            author_name=author_name,
            message=message,
            status=VersionStatus.ACTIVE,
            is_current=False,
            storage_key=storage_key,
            version_tag=version_tag,
        )

    @classmethod
    def create_tagged_version(
        cls,
        file_id: str,
        version_tag: str,
        author_id: str,
        author_name: str,
        storage_key: str,
        size: int,
        mime_type: str,
        content: Optional[str] = None,
        checksum: Optional[str] = None,
        message: str = "Tagged version",
    ) -> "FileVersion":
        """Create tagged version."""
        return cls(
            file_id=file_id,
            version=version_tag,
            version_number=0,  # Tagged versions don't have sequential numbers
            content=content,
            checksum=checksum,
            size=size,
            mime_type=mime_type,
            author_id=author_id,
            author_name=author_name,
            message=message,
            status=VersionStatus.ACTIVE,
            is_current=False,
            storage_key=storage_key,
            version_tag=version_tag,
        )
