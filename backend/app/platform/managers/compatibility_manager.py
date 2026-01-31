"""Compatibility manager for handling compatibility checks.

This module provides the CompatibilityManager class for managing cross-platform
compatibility checks, issue tracking, and recommendation generation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
import asyncio
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from ..models.compatibility import (
    CompatibilityCheck,
    IssueSeverity,
    IssueType,
)
from ..models.platform import Platform
from ..schemas.platform_operations import (
    CompatibilityCheckRequest,
    CompatibilityCheckResponse,
    CompatibilityIssue,
    CompatibilityWarning,
    PlatformCompatibilityResult,
)
from ..utils.validators import (
    validate_platform_list,
    validate_pagination_params,
)
from ..utils.serializers import (
    serialize_compatibility_check,
    serialize_compatibility_check_list,
    serialize_compatibility_statistics,
)
from ..utils.formatters import (
    format_compatibility_status,
    format_compatibility_score,
    format_issues_by_severity,
)


logger = logging.getLogger(__name__)


class CompatibilityManager:
    """Manager for compatibility operations.

    Handles compatibility check creation, issue tracking, severity analysis,
    and compatibility-related queries.
    """

    def __init__(self, db_session: Session):
        """Initialize CompatibilityManager.

        Args:
            db_session: Database session
        """
        self.db = db_session

    # CRUD Operations
    async def create_compatibility_check(
        self,
        request: CompatibilityCheckRequest
    ) -> CompatibilityCheck:
        """Create a new compatibility check.

        Args:
            request: Compatibility check request

        Returns:
            Created compatibility check instance

        Raises:
            ValueError: If validation fails
            Exception: If creation fails
        """
        try:
            # Validate platform list
            validate_platform_list(request.platforms)

            # Generate unique check ID
            check_id = f"check_{uuid4().hex[:16]}"

            # Create compatibility check
            compatibility_check = CompatibilityCheck(
                skill_id=request.skill_id,
                check_id=check_id,
                platforms_checked=request.platforms,
                skill_version=request.skill_version,
                check_version="1.0",
                checked_at=datetime.utcnow(),
            )

            self.db.add(compatibility_check)
            self.db.commit()
            self.db.refresh(compatibility_check)

            logger.info(
                f"Created compatibility check: {check_id} for skill {request.skill_id}"
            )
            return compatibility_check

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create compatibility check: {str(e)}")
            raise

    async def get_compatibility_check(self, check_id: str) -> Optional[CompatibilityCheck]:
        """Get compatibility check by ID.

        Args:
            check_id: Compatibility check ID

        Returns:
            CompatibilityCheck instance or None
        """
        return self.db.query(CompatibilityCheck).filter(
            CompatibilityCheck.check_id == check_id
        ).first()

    async def get_compatibility_check_by_id(self, check_uuid: Union[str, uuid4]) -> Optional[CompatibilityCheck]:
        """Get compatibility check by UUID.

        Args:
            check_uuid: Compatibility check UUID

        Returns:
            CompatibilityCheck instance or None
        """
        return self.db.query(CompatibilityCheck).filter(
            CompatibilityCheck.id == check_uuid
        ).first()

    async def update_compatibility_check(
        self,
        check_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[CompatibilityCheck]:
        """Update compatibility check.

        Args:
            check_id: Compatibility check ID
            update_data: Update data

        Returns:
            Updated compatibility check instance
        """
        try:
            compatibility_check = await self.get_compatibility_check(check_id)
            if not compatibility_check:
                return None

            # Update fields
            for key, value in update_data.items():
                if hasattr(compatibility_check, key):
                    setattr(compatibility_check, key, value)

            compatibility_check.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(compatibility_check)

            logger.info(f"Updated compatibility check: {check_id}")
            return compatibility_check

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update compatibility check: {str(e)}")
            raise

    async def delete_compatibility_check(self, check_id: str) -> bool:
        """Delete compatibility check.

        Args:
            check_id: Compatibility check ID

        Returns:
            True if deleted, False if not found
        """
        try:
            compatibility_check = await self.get_compatibility_check(check_id)
            if not compatibility_check:
                return False

            self.db.delete(compatibility_check)
            self.db.commit()

            logger.info(f"Deleted compatibility check: {check_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete compatibility check: {str(e)}")
            raise

    # Compatibility Analysis
    async def perform_compatibility_check(
        self,
        request: CompatibilityCheckRequest,
        skill_data: Optional[Dict[str, Any]] = None
    ) -> CompatibilityCheck:
        """Perform a full compatibility check.

        Args:
            request: Compatibility check request
            skill_data: Optional skill data for analysis

        Returns:
            Completed compatibility check instance
        """
        try:
            # Create check record
            compatibility_check = await self.create_compatibility_check(request)

            # Initialize results
            platform_results = {}
            all_issues = []
            all_warnings = []
            all_recommendations = []

            # Check each platform
            for platform_name in request.platforms:
                try:
                    result = await self._check_platform_compatibility(
                        platform_name,
                        request,
                        skill_data
                    )

                    platform_results[platform_name] = result
                    all_issues.extend(result.get('issues', []))
                    all_warnings.extend(result.get('warnings', []))
                    all_recommendations.extend(result.get('recommendations', []))

                except Exception as e:
                    logger.error(
                        f"Failed to check compatibility for {platform_name}: {str(e)}"
                    )
                    # Add error as issue
                    all_issues.append({
                        'type': 'check_error',
                        'severity': IssueSeverity.HIGH,
                        'description': f'Failed to check platform: {str(e)}',
                        'affected_platforms': [platform_name],
                    })

                    platform_results[platform_name] = {
                        'compatible': False,
                        'issues': [{'description': str(e)}],
                        'warnings': [],
                        'limitations': [],
                        'supported_features': [],
                        'unsupported_features': [],
                    }

            # Calculate overall compatibility
            compatibility_check.platform_results = platform_results
            compatibility_check.compatibility_issues = all_issues
            compatibility_check.warnings = all_warnings
            compatibility_check.recommendations = all_recommendations

            # Calculate score and overall compatibility
            compatibility_check.calculate_overall_compatibility()

            # Perform feature and dependency analysis
            await self._perform_detailed_analysis(compatibility_check, skill_data)

            self.db.commit()
            self.db.refresh(compatibility_check)

            logger.info(
                f"Completed compatibility check: {check_id} - "
                f"{'compatible' if compatibility_check.overall_compatible else 'incompatible'}"
            )
            return compatibility_check

        except Exception as e:
            logger.error(f"Failed to perform compatibility check: {str(e)}")
            raise

    async def _check_platform_compatibility(
        self,
        platform_name: str,
        request: CompatibilityCheckRequest,
        skill_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Check compatibility for a specific platform.

        Args:
            platform_name: Platform name
            request: Compatibility check request
            skill_data: Skill data for analysis

        Returns:
            Platform compatibility result
        """
        # Get platform
        platform = self.db.query(Platform).filter(
            Platform.name == platform_name
        ).first()

        if not platform:
            return {
                'compatible': False,
                'issues': [{
                    'type': IssueType.FEATURE_UNSUPPORTED,
                    'severity': IssueSeverity.CRITICAL,
                    'description': f'Platform not found: {platform_name}',
                    'affected_platforms': [platform_name],
                }],
                'warnings': [],
                'limitations': [f'Platform {platform_name} is not registered'],
                'supported_features': [],
                'unsupported_features': [],
            }

        if not platform.is_active:
            return {
                'compatible': False,
                'issues': [{
                    'type': IssueType.FEATURE_UNSUPPORTED,
                    'severity': IssueSeverity.CRITICAL,
                    'description': f'Platform is not active: {platform_name}',
                    'affected_platforms': [platform_name],
                }],
                'warnings': [],
                'limitations': [f'Platform {platform_name} is inactive'],
                'supported_features': [],
                'unsupported_features': [],
            }

        # Check compatibility
        compatible = True
        issues = []
        warnings = []
        limitations = []
        supported_features = platform.supported_formats or []
        unsupported_features = []

        # Check format compatibility
        if request.skill_version:
            # Check if platform supports the skill format/version
            # This is a simplified check - in reality, you'd analyze the skill data
            pass

        # Check feature compatibility
        if platform.features:
            # Analyze platform features against skill requirements
            pass

        # Check size limits
        if skill_data and 'file_size' in skill_data:
            max_size = platform.max_file_size
            if skill_data['file_size'] > max_size:
                compatible = False
                issues.append({
                    'type': IssueType.SIZE_EXCEEDED,
                    'severity': IssueSeverity.HIGH,
                    'description': f'File size ({skill_data["file_size"]} bytes) exceeds platform limit ({max_size} bytes)',
                    'affected_platforms': [platform_name],
                })

        # Check API limits
        if platform.features and 'api_rate_limit' in platform.features:
            rate_limit = platform.features['api_rate_limit']
            # Check if skill deployment would exceed rate limits
            # This is a simplified check
            pass

        # Add limitations
        if not platform.is_healthy:
            limitations.append(f'Platform {platform_name} is currently unhealthy')

        return {
            'compatible': compatible,
            'score': 100.0 if compatible else 50.0,
            'issues': issues,
            'warnings': warnings,
            'limitations': limitations,
            'supported_features': supported_features,
            'unsupported_features': unsupported_features,
        }

    async def _perform_detailed_analysis(
        self,
        compatibility_check: CompatibilityCheck,
        skill_data: Optional[Dict[str, Any]]
    ):
        """Perform detailed compatibility analysis.

        Args:
            compatibility_check: Compatibility check instance
            skill_data: Skill data for analysis
        """
        # Feature analysis
        feature_analysis = {}
        for platform_name in compatibility_check.platforms_checked or []:
            platform_result = compatibility_check.platform_results.get(platform_name, {})
            feature_analysis[platform_name] = {
                'supported_features': platform_result.get('supported_features', []),
                'unsupported_features': platform_result.get('unsupported_features', []),
                'limitations': platform_result.get('limitations', []),
            }

        compatibility_check.feature_analysis = feature_analysis

        # Dependency analysis (simplified)
        compatibility_check.dependency_analysis = {
            'platform_dependencies': {},
            'missing_dependencies': [],
            'version_conflicts': [],
        }

        # Limitation analysis
        limitation_analysis = {}
        for platform_name in compatibility_check.platforms_checked or []:
            platform_result = compatibility_check.platform_results.get(platform_name, {})
            limitation_analysis[platform_name] = {
                'limitations': platform_result.get('limitations', []),
                'restrictions': [],
            }

        compatibility_check.limitation_analysis = limitation_analysis

        # Generate detailed report
        compatibility_check.detailed_report = {
            'summary': compatibility_check.generate_summary(),
            'platform_breakdown': {},
            'issue_analysis': self._analyze_issues(compatibility_check.compatibility_issues or []),
            'recommendations': self._generate_recommendations(compatibility_check),
        }

        # Add platform breakdown
        for platform_name in compatibility_check.platforms_checked or []:
            platform_result = compatibility_check.platform_results.get(platform_name, {})
            compatibility_check.detailed_report['platform_breakdown'][platform_name] = {
                'compatible': platform_result.get('compatible', False),
                'score': platform_result.get('score'),
                'issues_count': len(platform_result.get('issues', [])),
                'warnings_count': len(platform_result.get('warnings', [])),
                'limitations': platform_result.get('limitations', []),
            }

    def _analyze_issues(self, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze issues for patterns and insights.

        Args:
            issues: List of issues

        Returns:
            Issue analysis
        """
        analysis = {
            'total_issues': len(issues),
            'by_severity': {},
            'by_type': {},
            'by_platform': {},
            'common_issues': [],
        }

        # Count by severity
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            issue_type = issue.get('type', 'unknown')
            affected_platforms = issue.get('affected_platforms', [])

            # By severity
            analysis['by_severity'][severity] = analysis['by_severity'].get(severity, 0) + 1

            # By type
            analysis['by_type'][issue_type] = analysis['by_type'].get(issue_type, 0) + 1

            # By platform
            for platform in affected_platforms:
                analysis['by_platform'][platform] = analysis['by_platform'].get(platform, 0) + 1

        return analysis

    def _generate_recommendations(self, compatibility_check: CompatibilityCheck) -> List[Dict[str, Any]]:
        """Generate recommendations based on compatibility analysis.

        Args:
            compatibility_check: Compatibility check instance

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze issues and generate recommendations
        for issue in compatibility_check.compatibility_issues or []:
            severity = issue.get('severity')
            issue_type = issue.get('type')
            affected_platforms = issue.get('affected_platforms', [])

            # Generate recommendations based on issue type
            if issue_type == IssueType.SIZE_EXCEEDED:
                recommendations.append({
                    'category': 'optimization',
                    'priority': 'high' if severity == IssueSeverity.HIGH else 'medium',
                    'description': 'Optimize file size to meet platform requirements',
                    'platforms': affected_platforms,
                    'code_suggestion': 'Consider compressing assets or removing unnecessary files',
                })

            elif issue_type == IssueType.FEATURE_UNSUPPORTED:
                recommendations.append({
                    'category': 'feature_compatibility',
                    'priority': 'high' if severity == IssueSeverity.CRITICAL else 'medium',
                    'description': 'Adapt code to be compatible with platform features',
                    'platforms': affected_platforms,
                    'code_suggestion': 'Replace unsupported features with platform-compatible alternatives',
                })

            elif issue_type == IssueType.API_LIMIT_EXCEEDED:
                recommendations.append({
                    'category': 'rate_limiting',
                    'priority': 'high',
                    'description': 'Implement rate limiting to comply with API limits',
                    'platforms': affected_platforms,
                    'code_suggestion': 'Add request throttling or batch processing',
                })

        return recommendations

    # Query Operations
    async def list_compatibility_checks(
        self,
        skill_id: Optional[str] = None,
        overall_compatible: Optional[bool] = None,
        platforms_checked: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """List compatibility checks with filtering and pagination.

        Args:
            skill_id: Optional skill ID filter
            overall_compatible: Optional compatibility filter
            platforms_checked: Optional platforms filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Dictionary with checks and pagination info
        """
        query = self.db.query(CompatibilityCheck)

        # Apply filters
        if skill_id:
            query = query.filter(CompatibilityCheck.skill_id == skill_id)

        if overall_compatible is not None:
            query = query.filter(CompatibilityCheck.overall_compatible == overall_compatible)

        if platforms_checked:
            query = query.filter(
                CompatibilityCheck.platforms_checked.op('&&')(platforms_checked)
            )

        # Get total count
        total = query.count()

        # Apply pagination
        skip, limit = validate_pagination_params(skip, limit)
        checks = query.order_by(desc(CompatibilityCheck.checked_at)).offset(skip).limit(limit).all()

        return {
            'checks': serialize_compatibility_check_list(checks),
            'total': total,
            'skip': skip,
            'limit': limit,
        }

    async def get_compatibility_checks_by_skill(
        self,
        skill_id: str,
        limit: int = 10
    ) -> List[CompatibilityCheck]:
        """Get compatibility checks for a skill.

        Args:
            skill_id: Skill ID
            limit: Maximum number of checks to return

        Returns:
            List of compatibility checks
        """
        return self.db.query(CompatibilityCheck).filter(
            CompatibilityCheck.skill_id == skill_id
        ).order_by(desc(CompatibilityCheck.checked_at)).limit(limit).all()

    async def get_latest_compatibility_check(
        self,
        skill_id: str,
        platforms: Optional[List[str]] = None
    ) -> Optional[CompatibilityCheck]:
        """Get the latest compatibility check for a skill.

        Args:
            skill_id: Skill ID
            platforms: Optional platforms filter

        Returns:
            Latest compatibility check or None
        """
        query = self.db.query(CompatibilityCheck).filter(
            CompatibilityCheck.skill_id == skill_id
        )

        if platforms:
            query = query.filter(
                CompatibilityCheck.platforms_checked.op('&&')(platforms)
            )

        return query.order_by(desc(CompatibilityCheck.checked_at)).first()

    async def get_compatibility_statistics(
        self,
        skill_id: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get compatibility statistics.

        Args:
            skill_id: Optional skill ID to filter by
            date_from: Optional start date
            date_to: Optional end date

        Returns:
            Compatibility statistics
        """
        query = self.db.query(CompatibilityCheck)

        if skill_id:
            query = query.filter(CompatibilityCheck.skill_id == skill_id)

        if date_from:
            query = query.filter(CompatibilityCheck.checked_at >= date_from)

        if date_to:
            query = query.filter(CompatibilityCheck.checked_at <= date_to)

        checks = query.all()
        return serialize_compatibility_statistics(checks)

    # Issue Management
    async def add_issue(
        self,
        check_id: str,
        issue: CompatibilityIssue
    ) -> Optional[CompatibilityCheck]:
        """Add an issue to a compatibility check.

        Args:
            check_id: Compatibility check ID
            issue: Issue to add

        Returns:
            Updated compatibility check
        """
        compatibility_check = await self.get_compatibility_check(check_id)
        if not compatibility_check:
            return None

        compatibility_check.add_issue(issue.dict())
        compatibility_check.updated_at = datetime.utcnow()

        self.db.commit()

        return compatibility_check

    async def add_warning(
        self,
        check_id: str,
        warning: CompatibilityWarning
    ) -> Optional[CompatibilityCheck]:
        """Add a warning to a compatibility check.

        Args:
            check_id: Compatibility check ID
            warning: Warning to add

        Returns:
            Updated compatibility check
        """
        compatibility_check = await self.get_compatibility_check(check_id)
        if not compatibility_check:
            return None

        compatibility_check.add_warning(warning.dict())
        compatibility_check.updated_at = datetime.utcnow()

        self.db.commit()

        return compatibility_check

    async def get_issues_by_severity(
        self,
        check_id: str,
        severity: str
    ) -> List[Dict[str, Any]]:
        """Get issues by severity for a compatibility check.

        Args:
            check_id: Compatibility check ID
            severity: Severity level

        Returns:
            List of issues with specified severity
        """
        compatibility_check = await self.get_compatibility_check(check_id)
        if not compatibility_check:
            return []

        return compatibility_check.get_issues_by_severity(severity)

    async def get_issues_by_platform(
        self,
        check_id: str,
        platform_name: str
    ) -> List[Dict[str, Any]]:
        """Get issues by platform for a compatibility check.

        Args:
            check_id: Compatibility check ID
            platform_name: Platform name

        Returns:
            List of issues affecting specified platform
        """
        compatibility_check = await self.get_compatibility_check(check_id)
        if not compatibility_check:
            return []

        return compatibility_check.get_issues_by_platform(platform_name)

    # Utility Methods
    async def compatibility_check_exists(self, check_id: str) -> bool:
        """Check if compatibility check exists.

        Args:
            check_id: Compatibility check ID

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(CompatibilityCheck).filter(
            CompatibilityCheck.check_id == check_id
        ).first() is not None

    async def is_skill_compatible(
        self,
        skill_id: str,
        platforms: List[str]
    ) -> bool:
        """Check if skill is compatible with specified platforms.

        Args:
            skill_id: Skill ID
            platforms: List of platform names

        Returns:
            True if compatible with all platforms, False otherwise
        """
        latest_check = await self.get_latest_compatibility_check(skill_id, platforms)
        return latest_check.overall_compatible is True if latest_check else False

    async def get_compatibility_summary(
        self,
        skill_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get compatibility summary for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Compatibility summary or None
        """
        latest_check = await self.get_latest_compatibility_check(skill_id)
        return latest_check.generate_summary() if latest_check else None