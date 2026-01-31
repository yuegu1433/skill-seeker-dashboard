"""Deployment model for tracking skill deployments to LLM platforms.

This module defines the Deployment SQLAlchemy model for storing deployment
records, status tracking, and deployment metadata.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .platform import Platform

Base = declarative_base()


class Deployment(Base):
    """Deployment model for tracking skill deployments to platforms.

    Stores deployment information including status, platform response,
    configuration, and metadata.
    """

    __tablename__ = "deployments"

    # Primary key and foreign keys
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Deployment unique identifier",
    )
    platform_id = Column(
        UUID(as_uuid=True),
        ForeignKey("platforms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Platform identifier",
    )

    # Skill information
    skill_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Skill identifier",
    )
    skill_name = Column(
        String(200),
        nullable=False,
        comment="Skill name",
    )
    skill_version = Column(
        String(50),
        nullable=False,
        comment="Skill version",
    )

    # Deployment information
    deployment_id = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Platform-specific deployment identifier",
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
        comment="Deployment status (pending, deploying, success, failed, cancelled)",
    )

    # File information
    original_format = Column(
        String(20),
        nullable=True,
        comment="Original skill format",
    )
    target_format = Column(
        String(20),
        nullable=True,
        comment="Target platform format",
    )
    file_size = Column(
        BigInteger,
        nullable=True,
        comment="Package file size in bytes",
    )
    checksum = Column(
        String(64),
        nullable=True,
        comment="Package file checksum (SHA-256)",
    )

    # Configuration and metadata
    deployment_config = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Deployment configuration parameters",
    )
    metadata = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Additional deployment metadata",
    )

    # Deployment details
    started_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Deployment start timestamp",
    )
    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Deployment completion timestamp",
    )
    duration_seconds = Column(
        BigInteger,
        nullable=True,
        comment="Deployment duration in seconds",
    )

    # Results and status
    success = Column(
        Boolean,
        nullable=True,
        comment="Whether deployment was successful",
    )
    error_message = Column(
        Text,
        nullable=True,
        comment="Error message if deployment failed",
    )
    error_details = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Detailed error information",
    )
    platform_response = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Platform API response data",
    )

    # Retry information
    retry_count = Column(
        BigInteger,
        default=0,
        nullable=False,
        comment="Number of retry attempts",
    )
    max_retries = Column(
        BigInteger,
        default=3,
        nullable=False,
        comment="Maximum retry attempts allowed",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="Deployment creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp",
    )

    # Relationships
    platform = relationship(
        "Platform",
        back_populates="deployments",
        lazy="select",
    )

    def __repr__(self) -> str:
        """Return string representation of the deployment."""
        return (
            f"<Deployment(skill='{self.skill_name}', platform='{self.platform.name if self.platform else 'unknown'}', "
            f"status='{self.status}')>"
        )

    def is_pending(self) -> bool:
        """Check if deployment is pending.

        Returns:
            True if deployment status is pending
        """
        return self.status == "pending"

    def is_deploying(self) -> bool:
        """Check if deployment is in progress.

        Returns:
            True if deployment status is deploying
        """
        return self.status == "deploying"

    def is_success(self) -> bool:
        """Check if deployment was successful.

        Returns:
            True if deployment status is success
        """
        return self.status == "success"

    def is_failed(self) -> bool:
        """Check if deployment failed.

        Returns:
            True if deployment status is failed
        """
        return self.status == "failed"

    def is_cancelled(self) -> bool:
        """Check if deployment was cancelled.

        Returns:
            True if deployment status is cancelled
        """
        return self.status == "cancelled"

    def is_completed(self) -> bool:
        """Check if deployment is completed (success or failed).

        Returns:
            True if deployment is in a final state
        """
        return self.status in ["success", "failed", "cancelled"]

    def can_retry(self) -> bool:
        """Check if deployment can be retried.

        Returns:
            True if deployment failed and can be retried
        """
        return (
            self.status == "failed"
            and self.retry_count < self.max_retries
        )

    def calculate_duration(self):
        """Calculate deployment duration based on start and completion times."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_seconds = int(delta.total_seconds())

    def start_deployment(self):
        """Mark deployment as started."""
        self.status = "deploying"
        self.started_at = datetime.utcnow()

    def complete_deployment(self, success: bool, platform_response: Optional[Dict[str, Any]] = None):
        """Mark deployment as completed.

        Args:
            success: Whether deployment was successful
            platform_response: Platform API response data
        """
        self.status = "success" if success else "failed"
        self.success = success
        self.completed_at = datetime.utcnow()
        self.calculate_duration()

        if platform_response:
            self.platform_response = platform_response

    def fail_deployment(self, error_message: str, error_details: Optional[Dict[str, Any]] = None):
        """Mark deployment as failed.

        Args:
            error_message: Error message
            error_details: Additional error details
        """
        self.status = "failed"
        self.success = False
        self.error_message = error_message
        if error_details:
            self.error_details = error_details
        self.completed_at = datetime.utcnow()
        self.calculate_duration()

    def cancel_deployment(self):
        """Cancel deployment."""
        self.status = "cancelled"
        self.completed_at = datetime.utcnow()
        self.calculate_duration()

    def retry_deployment(self):
        """Increment retry count and reset status."""
        if self.can_retry():
            self.retry_count += 1
            self.status = "pending"
            self.error_message = None
            self.error_details = {}
            self.started_at = None
            self.completed_at = None
            self.duration_seconds = None

    def get_deployment_url(self) -> Optional[str]:
        """Get platform deployment URL if available.

        Returns:
            Deployment URL or None
        """
        return self.platform_response.get("deployment_url")

    def get_platform_skill_id(self) -> Optional[str]:
        """Get platform-specific skill ID if available.

        Returns:
            Platform skill ID or None
        """
        return self.platform_response.get("skill_id")

    def to_dict(self) -> dict:
        """Convert deployment to dictionary representation.

        Returns:
            Dictionary containing deployment data
        """
        return {
            "id": str(self.id),
            "platform_id": str(self.platform_id),
            "platform_name": self.platform.name if self.platform else None,
            "skill_id": self.skill_id,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "deployment_id": self.deployment_id,
            "status": self.status,
            "original_format": self.original_format,
            "target_format": self.target_format,
            "file_size": self.file_size,
            "checksum": self.checksum,
            "deployment_config": self.deployment_config,
            "metadata": self.metadata,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "success": self.success,
            "error_message": self.error_message,
            "error_details": self.error_details,
            "platform_response": self.platform_response,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Deployment status constants
class DeploymentStatus:
    """Deployment status identifiers."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
