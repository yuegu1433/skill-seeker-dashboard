"""File Permission Model.

This module defines the FilePermission model for access control.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from app.core.database import Base


class PermissionType(str, Enum):
    """Permission type enumeration."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    SHARE = "share"
    ADMIN = "admin"


class PermissionScope(str, Enum):
    """Permission scope enumeration."""
    OWNER = "owner"
    GROUP = "group"
    PUBLIC = "public"
    SPECIFIC = "specific"


class FilePermission(Base):
    """FilePermission model for controlling file access.

    Attributes:
        id: Unique permission identifier
        file_id: Associated file identifier
        user_id: User identifier (for specific permissions)
        group_id: Group identifier (for group permissions)
        permission_type: Type of permission
        scope: Permission scope
        is_active: Whether permission is active
        granted_by: User who granted this permission
        granted_at: When permission was granted
        expires_at: When permission expires (optional)
        conditions: Additional conditions (JSON)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "file_permissions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True)

    # File association
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), nullable=False, index=True)

    # Permission targets
    user_id = Column(String(100), nullable=True, index=True)
    group_id = Column(String(100), nullable=True, index=True)

    # Permission details
    permission_type = Column(String(20), nullable=False, index=True)
    scope = Column(String(20), nullable=False, default=PermissionScope.SPECIFIC, index=True)

    # Permission state
    is_active = Column(Boolean, nullable=False, default=True, index=True)

    # Granting information
    granted_by = Column(String(100), nullable=False, index=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Additional data
    conditions = Column(JSON, nullable=True, default=dict)

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
    file = relationship("File", back_populates="permissions", lazy="select")

    # Indexes
    __table_args__ = (
        Index("ix_file_permissions_file_user", "file_id", "user_id"),
        Index("ix_file_permissions_file_group", "file_id", "group_id"),
        Index("ix_file_permissions_type", "permission_type"),
        Index("ix_file_permissions_scope", "scope"),
        Index("ix_file_permissions_active", "is_active"),
        UniqueConstraint("file_id", "user_id", "permission_type", name="uq_file_user_permission"),
        UniqueConstraint("file_id", "group_id", "permission_type", name="uq_file_group_permission"),
    )

    def __repr__(self) -> str:
        """Return string representation of the FilePermission."""
        return f"<FilePermission(id={self.id}, file_id={self.file_id}, user_id={self.user_id}, permission_type={self.permission_type})>"

    @validates("permission_type")
    def validate_permission_type(self, key: str, permission_type: str) -> str:
        """Validate permission type."""
        valid_types = [pt.value for pt in PermissionType]
        if permission_type not in valid_types:
            raise ValueError(f"Invalid permission type: {permission_type}")
        return permission_type

    @validates("scope")
    def validate_scope(self, key: str, scope: str) -> str:
        """Validate scope."""
        valid_scopes = [s.value for s in PermissionScope]
        if scope not in valid_scopes:
            raise ValueError(f"Invalid scope: {scope}")
        return scope

    @property
    def is_expired(self) -> bool:
        """Check if permission is expired."""
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
    def is_effective(self) -> bool:
        """Check if permission is currently effective."""
        return self.is_active and not self.is_expired

    def to_dict(self) -> Dict[str, Any]:
        """Convert permission to dictionary."""
        return {
            "id": str(self.id),
            "file_id": str(self.file_id),
            "user_id": self.user_id,
            "group_id": self.group_id,
            "permission_type": self.permission_type,
            "scope": self.scope,
            "is_active": self.is_active,
            "granted_by": self.granted_by,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "conditions": self.conditions or {},
            "is_expired": self.is_expired,
            "days_until_expiry": self.days_until_expiry,
            "is_effective": self.is_effective,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_summary_dict(self) -> Dict[str, Any]:
        """Convert permission to summary dictionary."""
        return {
            "id": str(self.id),
            "permission_type": self.permission_type,
            "scope": self.scope,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "is_active": self.is_active,
            "is_effective": self.is_effective,
        }

    def grant(self, granted_by: str, expires_at: Optional[datetime] = None):
        """Grant this permission."""
        self.is_active = True
        self.granted_by = granted_by
        self.granted_at = datetime.utcnow()
        self.expires_at = expires_at

    def revoke(self):
        """Revoke this permission."""
        self.is_active = False

    def renew(self, expires_at: Optional[datetime] = None):
        """Renew this permission."""
        self.is_active = True
        self.granted_at = datetime.utcnow()
        if expires_at:
            self.expires_at = expires_at

    def add_condition(self, key: str, value: Any):
        """Add permission condition."""
        if self.conditions is None:
            self.conditions = {}
        self.conditions[key] = value

    def remove_condition(self, key: str):
        """Remove permission condition."""
        if self.conditions and key in self.conditions:
            del self.conditions[key]

    @classmethod
    def create_user_permission(
        cls,
        file_id: str,
        user_id: str,
        permission_type: PermissionType,
        granted_by: str,
        expires_at: Optional[datetime] = None,
    ) -> "FilePermission":
        """Create user-specific permission."""
        return cls(
            file_id=file_id,
            user_id=user_id,
            permission_type=permission_type.value,
            scope=PermissionScope.SPECIFIC,
            granted_by=granted_by,
            expires_at=expires_at,
            is_active=True,
        )

    @classmethod
    def create_group_permission(
        cls,
        file_id: str,
        group_id: str,
        permission_type: PermissionType,
        granted_by: str,
        expires_at: Optional[datetime] = None,
    ) -> "FilePermission":
        """Create group-specific permission."""
        return cls(
            file_id=file_id,
            group_id=group_id,
            permission_type=permission_type.value,
            scope=PermissionScope.GROUP,
            granted_by=granted_by,
            expires_at=expires_at,
            is_active=True,
        )

    @classmethod
    def create_owner_permission(
        cls,
        file_id: str,
        owner_id: str,
    ) -> "FilePermission":
        """Create owner permission (full access)."""
        return cls(
            file_id=file_id,
            user_id=owner_id,
            permission_type=PermissionType.ADMIN.value,
            scope=PermissionScope.OWNER,
            granted_by=owner_id,
            is_active=True,
        )

    @classmethod
    def create_public_permission(
        cls,
        file_id: str,
        permission_type: PermissionType,
        granted_by: str,
    ) -> "FilePermission":
        """Create public permission."""
        return cls(
            file_id=file_id,
            permission_type=permission_type.value,
            scope=PermissionScope.PUBLIC,
            granted_by=granted_by,
            is_active=True,
        )
