"""Platform model for managing LLM platform configurations.

This module defines the Platform SQLAlchemy model for storing LLM platform
information, API configurations, and feature support.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .deployment import Deployment

Base = declarative_base()


class Platform(Base):
    """Platform model for LLM platform configurations.

    Stores platform information including API endpoints, authentication,
    supported formats, and feature flags.
    """

    __tablename__ = "platforms"

    # Primary key and basic fields
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Platform unique identifier",
    )
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Platform name (claude, gemini, openai, markdown)",
    )
    display_name = Column(
        String(100),
        nullable=False,
        comment="Human-readable platform name",
    )
    platform_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Platform type identifier",
    )

    # API configuration
    api_endpoint = Column(
        String(200),
        nullable=True,
        comment="Platform API endpoint URL",
    )
    api_version = Column(
        String(20),
        nullable=True,
        comment="API version being used",
    )
    authentication_type = Column(
        String(20),
        default="api_key",
        nullable=False,
        comment="Authentication method (api_key, oauth, bearer)",
    )

    # Platform capabilities
    supported_formats = Column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of supported skill formats",
    )
    max_file_size = Column(
        BigInteger,
        default=10 * 1024 * 1024,  # 10MB default
        comment="Maximum supported file size in bytes",
    )
    features = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Platform-specific features and capabilities",
    )

    # Status information
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether platform is currently active",
    )
    is_healthy = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Current health status of the platform",
    )
    last_health_check = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last health check",
    )

    # Configuration and rules
    configuration = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Platform-specific configuration settings",
    )
    validation_rules = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Platform-specific validation rules",
    )
    conversion_templates = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Format conversion templates for this platform",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="Platform registration timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp",
    )

    # Relationships
    deployments = relationship(
        "Deployment",
        back_populates="platform",
        cascade="all, delete-orphan",
        lazy="select",
    )

    def __repr__(self) -> str:
        """Return string representation of the platform."""
        return f"<Platform(name='{self.name}', display_name='{self.display_name}')>"

    def is_available(self) -> bool:
        """Check if platform is available for operations.

        Returns:
            True if platform is active and healthy
        """
        return self.is_active and self.is_healthy

    def supports_format(self, format_name: str) -> bool:
        """Check if platform supports a specific format.

        Args:
            format_name: Name of format to check

        Returns:
            True if format is supported
        """
        return format_name in (self.supported_formats or [])

    def get_max_size_for_format(self, format_name: str) -> int:
        """Get maximum file size for a specific format.

        Args:
            format_name: Name of format

        Returns:
            Maximum file size in bytes
        """
        # Platform-specific size limits could be stored in features
        format_limits = self.features.get("format_limits", {})
        return format_limits.get(format_name, self.max_file_size)

    def get_conversion_template(self, source_format: str, target_format: str) -> Optional[dict]:
        """Get conversion template for source to target format.

        Args:
            source_format: Source format name
            target_format: Target format name

        Returns:
            Conversion template or None if not found
        """
        templates = self.conversion_templates or {}
        return templates.get(f"{source_format}_to_{target_format}")

    def update_health_status(self, is_healthy: bool):
        """Update platform health status.

        Args:
            is_healthy: New health status
        """
        self.is_healthy = is_healthy
        self.last_health_check = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convert platform to dictionary representation.

        Returns:
            Dictionary containing platform data
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "platform_type": self.platform_type,
            "api_endpoint": self.api_endpoint,
            "api_version": self.api_version,
            "authentication_type": self.authentication_type,
            "supported_formats": self.supported_formats,
            "max_file_size": self.max_file_size,
            "features": self.features,
            "is_active": self.is_active,
            "is_healthy": self.is_healthy,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "configuration": self.configuration,
            "validation_rules": self.validation_rules,
            "conversion_templates": self.conversion_templates,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Platform type constants
class PlatformType:
    """Platform type identifiers."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"
    MARKDOWN = "markdown"


# Authentication type constants
class AuthType:
    """Authentication type identifiers."""
    API_KEY = "api_key"
    OAUTH = "oauth"
    BEARER = "bearer"
    BASIC = "basic"
