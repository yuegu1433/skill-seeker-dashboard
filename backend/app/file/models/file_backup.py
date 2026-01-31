"""File Backup Model.

This module defines the FileBackup model for backup management.
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


class BackupStatus(str, Enum):
    """Backup status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    RESTORING = "restoring"
    VERIFIED = "verified"


class BackupType(str, Enum):
    """Backup type enumeration."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    SNAPSHOT = "snapshot"


class BackupLocation(str, Enum):
    """Backup location enumeration."""
    LOCAL = "local"
    REMOTE = "remote"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class FileBackup(Base):
    """FileBackup model for managing file backups.

    Attributes:
        id: Unique backup identifier
        file_id: Associated file identifier
        backup_name: Name of the backup
        backup_path: Path to the backup file
        backup_type: Type of backup (full, incremental, etc.)
        backup_location: Location of the backup
        status: Backup status
        size: Size of backup in bytes
        compressed_size: Compressed size if applicable
        checksum: Backup file checksum
        compression_ratio: Compression ratio
        retention_days: How long to retain this backup
        created_by: User who created the backup
        source_version: Source version identifier
        restore_count: Number of times restored
        last_restored_at: Last restoration timestamp
        metadata: Additional metadata (JSON)
        error_message: Error message if backup failed
        progress_percentage: Backup progress percentage
        start_time: Backup start time
        end_time: Backup completion time
        verified_at: Verification timestamp
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "file_backups"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)

    # File association
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False, index=True)

    # Backup information
    backup_name = Column(String(255), nullable=False, index=True)
    backup_path = Column(String(500), nullable=False, index=True)
    backup_type = Column(String(20), nullable=False, default=BackupType.FULL, index=True)
    backup_location = Column(String(20), nullable=False, default=BackupLocation.LOCAL, index=True)

    # Status and progress
    status = Column(String(20), nullable=False, default=BackupStatus.PENDING, index=True)
    progress_percentage = Column(Integer, nullable=False, default=0)

    # Size information
    size = Column(BigInteger, nullable=False, default=0)
    compressed_size = Column(BigInteger, nullable=True)
    compression_ratio = Column(Integer, nullable=True)  # Percentage

    # Integrity
    checksum = Column(String(64), nullable=True, index=True)

    # Retention
    retention_days = Column(Integer, nullable=False, default=30)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # User information
    created_by = Column(String(100), nullable=False, index=True)

    # Version tracking
    source_version = Column(String(100), nullable=True, index=True)

    # Restoration tracking
    restore_count = Column(Integer, nullable=False, default=0)
    last_restored_at = Column(DateTime(timezone=True), nullable=True)

    # Additional data
    metadata = Column(JSON, nullable=True, default=dict)
    error_message = Column(Text, nullable=True)

    # Timestamps
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    # Relationships
    file = relationship("File", back_populates="backups", lazy="select")

    # Indexes
    __table_args__ = (
        Index("ix_file_backups_file_status", "file_id", "status"),
        Index("ix_file_backups_type", "backup_type"),
        Index("ix_file_backups_location", "backup_location"),
        Index("ix_file_backups_created_by", "created_by"),
        Index("ix_file_backups_expires", "expires_at"),
        Index("ix_file_backups_created_at", "created_at"),
        UniqueConstraint("file_id", "backup_name", name="uq_file_backup_name"),
    )

    def __repr__(self) -> str:
        """Return string representation of the FileBackup."""
        return f"<FileBackup(id={self.id}, file_id={self.file_id}, backup_name={self.backup_name}, status={self.status})>"

    @validates("backup_type")
    def validate_backup_type(self, key: str, backup_type: str) -> str:
        """Validate backup type."""
        valid_types = [bt.value for bt in BackupType]
        if backup_type not in valid_types:
            raise ValueError(f"Invalid backup type: {backup_type}")
        return backup_type

    @validates("backup_location")
    def validate_backup_location(self, key: str, backup_location: str) -> str:
        """Validate backup location."""
        valid_locations = [bl.value for bl in BackupLocation]
        if backup_location not in valid_locations:
            raise ValueError(f"Invalid backup location: {backup_location}")
        return backup_location

    @validates("status")
    def validate_status(self, key: str, status: str) -> str:
        """Validate status."""
        valid_statuses = [bs.value for bs in BackupStatus]
        if status not in valid_statuses:
            raise ValueError(f"Invalid backup status: {status}")
        return status

    @validates("size")
    def validate_size(self, key: str, size: int) -> int:
        """Validate size."""
        if size < 0:
            raise ValueError("Size cannot be negative")
        return size

    @validates("compression_ratio")
    def validate_compression_ratio(self, key: str, ratio: int) -> int:
        """Validate compression ratio."""
        if ratio is not None and (ratio < 0 or ratio > 100):
            raise ValueError("Compression ratio must be between 0 and 100")
        return ratio

    @property
    def age_days(self) -> int:
        """Calculate backup age in days."""
        if self.created_at:
            return (datetime.utcnow() - self.created_at).days
        return 0

    @property
    def is_expired(self) -> bool:
        """Check if backup is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Get days until expiry."""
        if self.expires_at:
            delta = self.expires_at - datetime.utcnow()
            return delta.days
        return None

    @property
    def duration_seconds(self) -> Optional[int]:
        """Get backup duration in seconds."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds())
        return None

    @property
    def size_mb(self) -> float:
        """Get backup size in MB."""
        return round(self.size / (1024 * 1024), 2)

    @property
    def compressed_size_mb(self) -> float:
        """Get compressed size in MB."""
        if self.compressed_size:
            return round(self.compressed_size / (1024 * 1024), 2)
        return 0.0

    @property
    def space_saved_mb(self) -> float:
        """Get space saved in MB."""
        if self.compressed_size:
            return round((self.size - self.compressed_size) / (1024 * 1024), 2)
        return 0.0

    @property
    def is_successful(self) -> bool:
        """Check if backup was successful."""
        return self.status == BackupStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if backup failed."""
        return self.status == BackupStatus.FAILED

    @property
    def is_in_progress(self) -> bool:
        """Check if backup is in progress."""
        return self.status in [BackupStatus.PENDING, BackupStatus.IN_PROGRESS]

    def to_dict(self) -> Dict[str, Any]:
        """Convert backup to dictionary."""
        return {
            "id": str(self.id),
            "file_id": str(self.file_id),
            "backup_name": self.backup_name,
            "backup_path": self.backup_path,
            "backup_type": self.backup_type,
            "backup_location": self.backup_location,
            "status": self.status,
            "progress_percentage": self.progress_percentage,
            "size": self.size,
            "size_mb": self.size_mb,
            "compressed_size": self.compressed_size,
            "compressed_size_mb": self.compressed_size_mb,
            "compression_ratio": self.compression_ratio,
            "space_saved_mb": self.space_saved_mb,
            "checksum": self.checksum,
            "retention_days": self.retention_days,
            "created_by": self.created_by,
            "source_version": self.source_version,
            "restore_count": self.restore_count,
            "last_restored_at": self.last_restored_at.isoformat() if self.last_restored_at else None,
            "metadata": self.metadata or {},
            "error_message": self.error_message,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "verified_at": self.verified_at.isoformat() if self.verified_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "age_days": self.age_days,
            "is_expired": self.is_expired,
            "days_until_expiry": self.days_until_expiry,
            "is_successful": self.is_successful,
            "is_failed": self.is_failed,
            "is_in_progress": self.is_in_progress,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert backup to summary dictionary."""
        return {
            "id": str(self.id),
            "backup_name": self.backup_name,
            "backup_type": self.backup_type,
            "status": self.status,
            "size_mb": self.size_mb,
            "created_by": self.created_by,
            "is_successful": self.is_successful,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def start_backup(self):
        """Mark backup as started."""
        self.status = BackupStatus.IN_PROGRESS
        self.progress_percentage = 0
        self.start_time = datetime.utcnow()

    def complete_backup(self, checksum: str, compressed_size: Optional[int] = None):
        """Mark backup as completed."""
        self.status = BackupStatus.COMPLETED
        self.progress_percentage = 100
        self.end_time = datetime.utcnow()
        self.checksum = checksum
        if compressed_size:
            self.compressed_size = compressed_size
            if self.size > 0:
                self.compression_ratio = int((1 - compressed_size / self.size) * 100)

    def fail_backup(self, error_message: str):
        """Mark backup as failed."""
        self.status = BackupStatus.FAILED
        self.end_time = datetime.utcnow()
        self.error_message = error_message

    def cancel_backup(self):
        """Cancel backup."""
        self.status = BackupStatus.CANCELLED
        self.end_time = datetime.utcnow()

    def verify_backup(self):
        """Mark backup as verified."""
        self.status = BackupStatus.VERIFIED
        self.verified_at = datetime.utcnow()

    def restore_backup(self):
        """Mark backup as being restored."""
        self.status = BackupStatus.RESTORING

    def update_progress(self, percentage: int):
        """Update backup progress."""
        self.progress_percentage = max(0, min(100, percentage))

    def add_metadata(self, key: str, value: Any):
        """Add metadata to backup."""
        if self.metadata is None:
            self.metadata = {}
        self.metadata[key] = value

    def remove_metadata(self, key: str):
        """Remove metadata from backup."""
        if self.metadata and key in self.metadata:
            del self.metadata[key]

    def increment_restore_count(self):
        """Increment restore count."""
        self.restore_count += 1
        self.last_restored_at = datetime.utcnow()

    def set_expiry(self, retention_days: int):
        """Set backup expiry date."""
        self.retention_days = retention_days
        from datetime import timedelta
        self.expires_at = datetime.utcnow() + timedelta(days=retention_days)

    @classmethod
    def create_full_backup(
        cls,
        file_id: str,
        backup_name: str,
        backup_path: str,
        created_by: str,
        size: int,
        retention_days: int = 30,
        backup_location: BackupLocation = BackupLocation.LOCAL,
    ) -> "FileBackup":
        """Create full backup."""
        return cls(
            file_id=file_id,
            backup_name=backup_name,
            backup_path=backup_path,
            backup_type=BackupType.FULL,
            backup_location=backup_location,
            status=BackupStatus.PENDING,
            size=size,
            created_by=created_by,
            retention_days=retention_days,
            start_time=datetime.utcnow(),
        )

    @classmethod
    def create_incremental_backup(
        cls,
        file_id: str,
        backup_name: str,
        backup_path: str,
        created_by: str,
        size: int,
        source_version: str,
        retention_days: int = 30,
        backup_location: BackupLocation = BackupLocation.LOCAL,
    ) -> "FileBackup":
        """Create incremental backup."""
        return cls(
            file_id=file_id,
            backup_name=backup_name,
            backup_path=backup_path,
            backup_type=BackupType.INCREMENTAL,
            backup_location=backup_location,
            status=BackupStatus.PENDING,
            size=size,
            created_by=created_by,
            source_version=source_version,
            retention_days=retention_days,
            start_time=datetime.utcnow(),
        )
