"""Compatibility check model for cross-platform compatibility validation.

This module defines the CompatibilityCheck SQLAlchemy model for storing
compatibility check results, issues, and recommendations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4

from sqlalchemy import (
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

Base = declarative_base()


class CompatibilityCheck(Base):
    """Compatibility check model for cross-platform validation.

    Stores compatibility check results, issues found, and recommendations
    for improving cross-platform compatibility.
    """

    __tablename__ = "compatibility_checks"

    # Primary key and foreign keys
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        comment="Compatibility check unique identifier",
    )
    skill_id = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Skill identifier being checked",
    )

    # Check information
    check_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique check identifier",
    )
    platforms_checked = Column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of platform names checked",
    )
    skill_version = Column(
        String(50),
        nullable=True,
        comment="Skill version being checked",
    )

    # Check results
    overall_compatible = Column(
        Boolean,
        nullable=True,
        comment="Overall compatibility result",
    )
    compatibility_score = Column(
        # Using Integer to store percentage (0-100)
        # SQLAlchemy doesn't have a percentage type
        # Using String to store as text for flexibility
        String(10),
        nullable=True,
        comment="Compatibility score as percentage (0-100)",
    )

    # Platform-specific results
    platform_results = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Per-platform compatibility results",
    )
    compatibility_issues = Column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of compatibility issues found",
    )
    warnings = Column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of compatibility warnings",
    )

    # Recommendations and suggestions
    recommendations = Column(
        JSONB,
        default=list,
        nullable=False,
        comment="List of improvement recommendations",
    )
    code_suggestions = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Code modification suggestions",
    )

    # Detailed analysis
    feature_analysis = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Detailed feature compatibility analysis",
    )
    dependency_analysis = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Dependency compatibility analysis",
    )
    limitation_analysis = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Platform limitation analysis",
    )

    # Detailed report
    detailed_report = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Complete detailed compatibility report",
    )

    # Check metadata
    check_duration_seconds = Column(
        # Using Integer to store duration
        # BigInteger for larger values if needed
        Integer,
        nullable=True,
        comment="Time taken for compatibility check in seconds",
    )
    check_version = Column(
        String(20),
        nullable=False,
        default="1.0",
        comment="Version of compatibility check rules used",
    )

    # Timestamps
    checked_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="Timestamp when check was performed",
    )
    created_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        nullable=False,
        comment="Record creation timestamp",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp",
    )

    def __repr__(self) -> str:
        """Return string representation of the compatibility check."""
        return (
            f"<CompatibilityCheck(skill='{self.skill_id}', "
            f"compatible={self.overall_compatible}, "
            f"platforms={len(self.platforms_checked)})>"
        )

    def is_compatible(self) -> bool:
        """Check if skill is overall compatible.

        Returns:
            True if overall compatibility is confirmed
        """
        return self.overall_compatible is True

    def has_warnings(self) -> bool:
        """Check if there are compatibility warnings.

        Returns:
            True if there are warnings
        """
        return len(self.warnings or []) > 0

    def has_issues(self) -> bool:
        """Check if there are compatibility issues.

        Returns:
            True if there are issues
        """
        return len(self.compatibility_issues or []) > 0

    def get_compatibility_score(self) -> Optional[float]:
        """Get compatibility score as float.

        Returns:
            Compatibility score (0.0-100.0) or None
        """
        if self.compatibility_score is None:
            return None
        try:
            return float(self.compatibility_score)
        except (ValueError, TypeError):
            return None

    def set_compatibility_score(self, score: float):
        """Set compatibility score.

        Args:
            score: Compatibility score (0.0-100.0)
        """
        if score < 0:
            score = 0
        elif score > 100:
            score = 100
        self.compatibility_score = f"{score:.1f}"

    def get_platform_result(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """Get compatibility result for a specific platform.

        Args:
            platform_name: Name of the platform

        Returns:
            Platform compatibility result or None
        """
        return (self.platform_results or {}).get(platform_name)

    def add_issue(self, issue: Dict[str, Any]):
        """Add a compatibility issue.

        Args:
            issue: Issue dictionary with type, description, and platform info
        """
        if self.compatibility_issues is None:
            self.compatibility_issues = []
        self.compatibility_issues.append(issue)

    def add_warning(self, warning: Dict[str, Any]):
        """Add a compatibility warning.

        Args:
            warning: Warning dictionary with type, description, and platform info
        """
        if self.warnings is None:
            self.warnings = []
        self.warnings.append(warning)

    def add_recommendation(self, recommendation: Dict[str, Any]):
        """Add a recommendation.

        Args:
            recommendation: Recommendation dictionary
        """
        if self.recommendations is None:
            self.recommendations = []
        self.recommendations.append(recommendation)

    def get_issues_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """Get compatibility issues filtered by severity.

        Args:
            severity: Severity level (critical, high, medium, low)

        Returns:
            List of issues with specified severity
        """
        if not self.compatibility_issues:
            return []

        return [
            issue for issue in self.compatibility_issues
            if issue.get("severity") == severity
        ]

    def get_issues_by_platform(self, platform_name: str) -> List[Dict[str, Any]]:
        """Get compatibility issues filtered by platform.

        Args:
            platform_name: Name of the platform

        Returns:
            List of issues affecting specified platform
        """
        if not self.compatibility_issues:
            return []

        return [
            issue for issue in self.compatibility_issues
            if platform_name in issue.get("affected_platforms", [])
        ]

    def calculate_overall_compatibility(self):
        """Calculate overall compatibility based on platform results."""
        if not self.platform_results:
            self.overall_compatible = False
            return

        # A skill is compatible if all platforms report compatible status
        compatible_platforms = 0
        total_platforms = len(self.platform_results)

        for platform_name, result in self.platform_results.items():
            if result.get("compatible", False):
                compatible_platforms += 1

        # Calculate score as percentage of compatible platforms
        if total_platforms > 0:
            score = (compatible_platforms / total_platforms) * 100
            self.set_compatibility_score(score)
            self.overall_compatible = compatible_platforms == total_platforms
        else:
            self.overall_compatible = False

    def generate_summary(self) -> Dict[str, Any]:
        """Generate a summary of compatibility check results.

        Returns:
            Dictionary containing summary information
        """
        return {
            "skill_id": self.skill_id,
            "overall_compatible": self.overall_compatible,
            "compatibility_score": self.get_compatibility_score(),
            "platforms_checked": len(self.platforms_checked),
            "issues_count": len(self.compatibility_issues or []),
            "warnings_count": len(self.warnings or []),
            "recommendations_count": len(self.recommendations or []),
            "critical_issues": len(self.get_issues_by_severity("critical")),
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
        }

    def to_dict(self) -> dict:
        """Convert compatibility check to dictionary representation.

        Returns:
            Dictionary containing compatibility check data
        """
        return {
            "id": str(self.id),
            "skill_id": self.skill_id,
            "check_id": self.check_id,
            "platforms_checked": self.platforms_checked,
            "skill_version": self.skill_version,
            "overall_compatible": self.overall_compatible,
            "compatibility_score": self.get_compatibility_score(),
            "platform_results": self.platform_results,
            "compatibility_issues": self.compatibility_issues,
            "warnings": self.warnings,
            "recommendations": self.recommendations,
            "code_suggestions": self.code_suggestions,
            "feature_analysis": self.feature_analysis,
            "dependency_analysis": self.dependency_analysis,
            "limitation_analysis": self.limitation_analysis,
            "detailed_report": self.detailed_report,
            "check_duration_seconds": self.check_duration_seconds,
            "check_version": self.check_version,
            "checked_at": self.checked_at.isoformat() if self.checked_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Issue severity constants
class IssueSeverity:
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Issue type constants
class IssueType:
    """Compatibility issue types."""
    FORMAT_INCOMPATIBLE = "format_incompatible"
    FEATURE_UNSUPPORTED = "feature_unsupported"
    DEPENDENCY_MISSING = "dependency_missing"
    DEPENDENCY_INCOMPATIBLE = "dependency_incompatible"
    SIZE_EXCEEDED = "size_exceeded"
    API_LIMIT_EXCEEDED = "api_limit_exceeded"
    CONTENT_POLICY_VIOLATION = "content_policy_violation"
    SYNTAX_ERROR = "syntax_error"
    SEMANTIC_ERROR = "semantic_error"
