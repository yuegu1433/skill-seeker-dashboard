"""File Model.

This module defines the File model for the file management system.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
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
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class FileType(str, Enum):
    """File type enumeration."""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CODE = "code"
    ARCHIVE = "archive"
    OTHER = "other"


class FileStatus(str, Enum):
    """File status enumeration."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PENDING = "pending"
    PROCESSING = "processing"
    ERROR = "error"


class File(Base):
    """File model representing a file in the system.

    Attributes:
        id: Unique file identifier
        name: File name
        path: File path in storage
        size: File size in bytes
        mime_type: MIME type of the file
        type: File type (document, image, etc.)
        status: File status
        owner_id: File owner identifier
        parent_id: Parent folder identifier (for hierarchical structure)
        folder_id: Folder identifier
        bucket: MinIO bucket name
        storage_key: Storage key/path in bucket
        checksum: File checksum (SHA-256)
        description: File description
        tags: File tags (JSON array)
        metadata: Additional metadata (JSON object)
        is_public: Whether file is publicly accessible
        is_deleted: Whether file is deleted (soft delete)
        deleted_at: Deletion timestamp
        created_at: Creation timestamp
        updated_at: Last update timestamp
        accessed_at: Last access timestamp
        version_count: Number of versions
        download_count: Download count
        preview_count: Preview count
    """

    __tablename__ = "files"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Basic file information
    name = Column(String(255), nullable=False, index=True)
    original_name = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False, unique=True, index=True)
    size = Column(BigInteger, nullable=False, default=0)
    mime_type = Column(String(100), nullable=False, index=True)
    extension = Column(String(20), nullable=False, index=True)

    # File classification
    type = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default=FileStatus.ACTIVE, index=True)

    # Ownership and organization
    owner_id = Column(String(100), nullable=False, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=True)
    folder_id = Column(String(100), nullable=True, index=True)

    # Storage information
    bucket = Column(String(100), nullable=False, default="files")
    storage_key = Column(String(500), nullable=False, index=True)

    # File integrity
    checksum = Column(String(64), nullable=True, index=True)

    # Description and metadata
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True, default=list)
    metadata = Column(JSON, nullable=True, default=dict)

    # Access control
    is_public = Column(Boolean, nullable=False, default=False, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)

    # Timestamps
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )
    accessed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Statistics
    version_count = Column(Integer, nullable=False, default=0)
    download_count = Column(Integer, nullable=False, default=0)
    preview_count = Column(Integer, nullable=False, default=0)

    # Relationships
    versions = relationship(
        "FileVersion",
        back_populates="file",
        cascade="all, delete-orphan",
        lazy="select",
    )

    permissions = relationship(
        "FilePermission",
        back_populates="file",
        cascade="all, delete-orphan",
        lazy="select",
    )

    backups = relationship(
        "FileBackup",
        back_populates="file",
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Parent-child relationship for folder hierarchy
    children = relationship(
        "File",
        backref=Base._parent_property(),
        cascade="all, delete-orphan",
        lazy="select",
    )

    # Indexes
    __table_args__ = (
        Index("ix_files_owner_status", "owner_id", "status"),
        Index("ix_files_type_status", "type", "status"),
        Index("ix_files_folder_status", "folder_id", "status"),
        Index("ix_files_created_at", "created_at"),
        Index("ix_files_updated_at", "updated_at"),
        Index("ix_files_size", "size"),
        UniqueConstraint("path", name="uq_files_path"),
    )

    def __repr__(self) -> str:
        """Return string representation of the File."""
        return f"<File(id={self.id}, name={self.name}, type={self.type}, status={self.status})>"

    @validates("name")
    def validate_name(self, key: str, name: str) -> str:
        """Validate file name."""
        if not name or len(name.strip()) == 0:
            raise ValueError("File name cannot be empty")
        if len(name) > 255:
            raise ValueError("File name cannot exceed 255 characters")
        return name.strip()

    @validates("size")
    def validate_size(self, key: str, size: int) -> int:
        """Validate file size."""
        if size < 0:
            raise ValueError("File size cannot be negative")
        return size

    @validates("mime_type")
    def validate_mime_type(self, key: str, mime_type: str) -> str:
        """Validate MIME type."""
        if not mime_type or len(mime_type.strip()) == 0:
            raise ValueError("MIME type cannot be empty")
        if len(mime_type) > 100:
            raise ValueError("MIME type cannot exceed 100 characters")
        return mime_type.lower()

    @validates("extension")
    def validate_extension(self, key: str, extension: str) -> str:
        """Validate file extension."""
        if not extension:
            return ""
        if not extension.startswith("."):
            extension = "." + extension
        return extension.lower()

    @property
    def is_folder(self) -> bool:
        """Check if this file is a folder."""
        return self.type == "folder"

    @property
    def is_file(self) -> bool:
        """Check if this is a regular file."""
        return self.type != "folder"

    @property
    def age_days(self) -> int:
        """Calculate file age in days."""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

    @property
    def size_mb(self) -> float:
        """Get file size in MB."""
        return round(self.size / (1024 * 1024), 2)

    @property
    def size_gb(self) -> float:
        """Get file size in GB."""
        return round(self.size / (1024 * 1024 * 1024), 2)

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
    def full_path(self) -> str:
        """Get full file path including folder structure."""
        return self.path

    def to_dict(self) -> Dict[str, Any]:
        """Convert file to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "original_name": self.original_name,
            "path": self.path,
            "size": self.size,
            "size_mb": self.size_mb,
            "human_readable_size": self.human_readable_size,
            "mime_type": self.mime_type,
            "extension": self.extension,
            "type": self.type,
            "status": self.status,
            "owner_id": self.owner_id,
            "parent_id": str(self.parent_id) if self.parent_id else None,
            "folder_id": self.folder_id,
            "bucket": self.bucket,
            "storage_key": self.storage_key,
            "checksum": self.checksum,
            "description": self.description,
            "tags": self.tags or [],
            "metadata": self.metadata or {},
            "is_public": self.is_public,
            "is_deleted": self.is_deleted,
            "is_folder": self.is_folder,
            "is_file": self.is_file,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "version_count": self.version_count,
            "download_count": self.download_count,
            "preview_count": self.preview_count,
            "age_days": self.age_days,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert file to summary dictionary (for list views)."""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "status": self.status,
            "size": self.size,
            "human_readable_size": self.human_readable_size,
            "extension": self.extension,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_folder": self.is_folder,
            "is_public": self.is_public,
        }

    def increment_download_count(self):
        """Increment download count."""
        self.download_count += 1

    def increment_preview_count(self):
        """Increment preview count."""
        self.preview_count += 1

    def update_access_time(self):
        """Update access time."""
        self.accessed_at = datetime.utcnow()

    def soft_delete(self):
        """Mark file as deleted (soft delete)."""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.status = FileStatus.DELETED

    def restore(self):
        """Restore deleted file."""
        self.is_deleted = False
        self.deleted_at = None
        self.status = FileStatus.ACTIVE

    def archive(self):
        """Archive file."""
        self.status = FileStatus.ARCHIVED

    def activate(self):
        """Activate file."""
        self.status = FileStatus.ACTIVE

    def update_size(self, new_size: int):
        """Update file size."""
        self.size = new_size
        self.updated_at = datetime.utcnow()

    def add_tag(self, tag: str):
        """Add tag to file."""
        if self.tags is None:
            self.tags = []
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove tag from file."""
        if self.tags and tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if file has specific tag."""
        return self.tags and tag in self.tags

    def update_metadata(self, metadata: Dict[str, Any]):
        """Update file metadata."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata.update(metadata)
        self.updated_at = datetime.utcnow()

    @classmethod
    def create_folder(
        cls,
        name: str,
        owner_id: str,
        parent_id: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> "File":
        """Create a new folder."""
        from pathlib import Path

        folder_path = name if not parent_id else f"{parent_id}/{name}"

        return cls(
            name=name,
            original_name=name,
            path=folder_path,
            size=0,
            mime_type="inode/directory",
            extension="",
            type="folder",
            status=FileStatus.ACTIVE,
            owner_id=owner_id,
            parent_id=parent_id,
            folder_id=folder_id or name,
            bucket="files",
            storage_key=folder_path,
            is_public=False,
        )

    @classmethod
    def create_file(
        cls,
        name: str,
        size: int,
        mime_type: str,
        owner_id: str,
        storage_key: str,
        bucket: str = "files",
        parent_id: Optional[str] = None,
        folder_id: Optional[str] = None,
        checksum: Optional[str] = None,
    ) -> "File":
        """Create a new file."""
        from pathlib import Path

        extension = Path(name).suffix.lower()
        file_type = cls.determine_file_type(mime_type, extension)

        return cls(
            name=name,
            original_name=name,
            path=storage_key,
            size=size,
            mime_type=mime_type,
            extension=extension,
            type=file_type,
            status=FileStatus.ACTIVE,
            owner_id=owner_id,
            parent_id=parent_id,
            folder_id=folder_id,
            bucket=bucket,
            storage_key=storage_key,
            checksum=checksum,
            is_public=False,
        )

    @staticmethod
    def determine_file_type(mime_type: str, extension: str) -> str:
        """Determine file type from MIME type and extension."""
        mime_type = mime_type.lower()
        extension = extension.lower()

        # Document files
        if any(doc_type in mime_type for doc_type in [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument",
            "text/plain",
        ]):
            return FileType.DOCUMENT

        # Image files
        if any(img_type in mime_type for img_type in [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ]):
            return FileType.IMAGE

        # Video files
        if any(vid_type in mime_type for vid_type in [
            "video/mp4",
            "video/webm",
            "video/ogg",
        ]):
            return FileType.VIDEO

        # Audio files
        if any(aud_type in mime_type for aud_type in [
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/mp4",
        ]):
            return FileType.AUDIO

        # Code files
        if any(code_type in mime_type for code_type in [
            "text/x-python",
            "text/x-java-source",
            "text/javascript",
            "text/css",
            "text/html",
            "text/xml",
            "application/json",
            "application/yaml",
        ]) or extension in [".py", ".java", ".js", ".css", ".html", ".xml", ".json", ".yaml", ".yml"]:
            return FileType.CODE

        # Archive files
        if any(arch_type in mime_type for arch_type in [
            "application/zip",
            "application/x-rar",
            "application/x-7z-compressed",
            "application/x-tar",
            "application/gzip",
        ]) or extension in [".zip", ".rar", ".7z", ".tar", ".gz"]:
            return FileType.ARCHIVE

        return FileType.OTHER
