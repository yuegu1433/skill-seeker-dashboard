"""StorageBucket model for managing MinIO storage buckets.

This module defines the StorageBucket SQLAlchemy model for tracking
MinIO storage buckets and their configuration.
"""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    String,
    DateTime,
    BigInteger,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class StorageBucket(Base):
    """Storage bucket model for MinIO object storage.

    Tracks MinIO storage buckets, their configuration, and statistics
    for the skill seekers storage system.
    """

    __tablename__ = "storage_buckets"

    # Primary key and identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, comment="桶ID")
    name = Column(
        String(100),
        unique=True,
        nullable=False,
        comment="桶名称",
    )
    bucket_type = Column(
        String(20),
        nullable=False,
        comment="桶类型 (skills, cache, archives, temp)",
    )

    # Configuration
    config = Column(
        JSONB,
        default=dict,
        comment="桶配置",
    )
    policy = Column(
        String(20),
        default="private",
        comment="访问策略 (private, public, custom)",
    )

    # Statistics
    file_count = Column(
        BigInteger,
        default=0,
        comment="文件数量",
    )
    total_size = Column(
        BigInteger,
        default=0,
        comment="总大小(字节)",
    )
    last_activity = Column(
        DateTime(timezone=True),
        comment="最后活动",
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

    def __repr__(self) -> str:
        """Return string representation of the StorageBucket."""
        return (
            f"<StorageBucket(id={self.id}, name='{self.name}', "
            f"bucket_type='{self.bucket_type}')>"
        )

    @property
    def average_file_size(self) -> float:
        """Calculate average file size."""
        if self.file_count == 0:
            return 0.0
        return float(self.total_size) / float(self.file_count)

    @property
    def size_human_readable(self) -> str:
        """Get human-readable size string."""
        size_bytes = self.total_size
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    def to_dict(self) -> dict:
        """Convert StorageBucket to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "bucket_type": self.bucket_type,
            "config": self.config or {},
            "policy": self.policy,
            "file_count": self.file_count,
            "total_size": self.total_size,
            "average_file_size": self.average_file_size,
            "size_human_readable": self.size_human_readable,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_skills_bucket(cls) -> "StorageBucket":
        """Create the main skills bucket."""
        return cls(
            name="skillseekers-skills",
            bucket_type="skills",
            policy="private",
            config={
                "versioning": True,
                "lifecycle": {"enabled": True},
                "encryption": {"enabled": True},
            },
        )

    @classmethod
    def create_cache_bucket(cls) -> "StorageBucket":
        """Create the cache bucket."""
        return cls(
            name="skillseekers-cache",
            bucket_type="cache",
            policy="private",
            config={
                "ttl": 3600,  # 1 hour default TTL
                "compression": {"enabled": True},
            },
        )

    @classmethod
    def create_archives_bucket(cls) -> "StorageBucket":
        """Create the archives bucket."""
        return cls(
            name="skillseekers-archives",
            bucket_type="archives",
            policy="private",
            config={
                "versioning": True,
                "retention": {"days": 90},
                "compression": {"enabled": True},
            },
        )

    @classmethod
    def create_temp_bucket(cls) -> "StorageBucket":
        """Create the temporary bucket."""
        return cls(
            name="skillseekers-temp",
            bucket_type="temp",
            policy="private",
            config={
                "auto_cleanup": True,
                "ttl": 86400,  # 24 hours default TTL
            },
        )


# Database indexes for performance optimization
Index("idx_storage_buckets_name", StorageBucket.name, unique=True)
Index("idx_storage_buckets_bucket_type", StorageBucket.bucket_type)
Index("idx_storage_buckets_policy", StorageBucket.policy)
Index("idx_storage_buckets_created_at", StorageBucket.created_at.desc())
Index("idx_storage_buckets_last_activity", StorageBucket.last_activity.desc())
