"""Platform operation validation schemas.

This module defines Pydantic models for validating platform operations,
including platform CRUD, deployment, and compatibility checks.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum


class PlatformType(str, Enum):
    """Platform type enumeration."""
    CLAUDE = "claude"
    GEMINI = "gemini"
    OPENAI = "openai"
    MARKDOWN = "markdown"


class AuthType(str, Enum):
    """Authentication type enumeration."""
    API_KEY = "api_key"
    OAUTH = "oauth"
    BEARER = "bearer"
    BASIC = "basic"


class DeploymentStatus(str, Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IssueSeverity(str, Enum):
    """Issue severity enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueType(str, Enum):
    """Compatibility issue type enumeration."""
    FORMAT_INCOMPATIBLE = "format_incompatible"
    FEATURE_UNSUPPORTED = "feature_unsupported"
    DEPENDENCY_MISSING = "dependency_missing"
    DEPENDENCY_INCOMPATIBLE = "dependency_incompatible"
    SIZE_EXCEEDED = "size_exceeded"
    API_LIMIT_EXCEEDED = "api_limit_exceeded"
    CONTENT_POLICY_VIOLATION = "content_policy_violation"
    SYNTAX_ERROR = "syntax_error"
    SEMANTIC_ERROR = "semantic_error"


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            UUID: str
        }


# Platform Operation Schemas
class PlatformCreateRequest(BaseSchema):
    """Request schema for creating a new platform."""
    name: str = Field(..., min_length=1, max_length=50, description="Platform name")
    display_name: str = Field(..., min_length=1, max_length=100, description="Human-readable platform name")
    platform_type: PlatformType = Field(..., description="Platform type identifier")
    api_endpoint: Optional[str] = Field(None, max_length=200, description="Platform API endpoint URL")
    api_version: Optional[str] = Field(None, max_length=20, description="API version being used")
    authentication_type: AuthType = Field(default=AuthType.API_KEY, description="Authentication method")
    supported_formats: List[str] = Field(default_factory=list, description="List of supported skill formats")
    max_file_size: int = Field(default=10 * 1024 * 1024, ge=1024, description="Maximum supported file size in bytes")
    features: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific features")
    is_active: bool = Field(default=True, description="Whether platform is currently active")
    configuration: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific configuration")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Platform-specific validation rules")
    conversion_templates: Dict[str, Any] = Field(default_factory=dict, description="Format conversion templates")

    @validator('name')
    def validate_name(cls, v):
        """Validate platform name format."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Platform name must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()


class PlatformUpdateRequest(BaseSchema):
    """Request schema for updating a platform."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    api_endpoint: Optional[str] = Field(None, max_length=200)
    api_version: Optional[str] = Field(None, max_length=20)
    authentication_type: Optional[AuthType] = None
    supported_formats: Optional[List[str]] = None
    max_file_size: Optional[int] = Field(None, ge=1024)
    features: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_healthy: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    conversion_templates: Optional[Dict[str, Any]] = None


class PlatformResponse(BaseSchema):
    """Response schema for platform operations."""
    id: str
    name: str
    display_name: str
    platform_type: str
    api_endpoint: Optional[str]
    api_version: Optional[str]
    authentication_type: str
    supported_formats: List[str]
    max_file_size: int
    features: Dict[str, Any]
    is_active: bool
    is_healthy: bool
    last_health_check: Optional[str]
    configuration: Dict[str, Any]
    validation_rules: Dict[str, Any]
    conversion_templates: Dict[str, Any]
    created_at: Optional[str]
    updated_at: Optional[str]

    @classmethod
    def from_model(cls, platform) -> 'PlatformResponse':
        """Create response from Platform model."""
        return cls(
            id=str(platform.id),
            name=platform.name,
            display_name=platform.display_name,
            platform_type=platform.platform_type,
            api_endpoint=platform.api_endpoint,
            api_version=platform.api_version,
            authentication_type=platform.authentication_type,
            supported_formats=platform.supported_formats or [],
            max_file_size=platform.max_file_size,
            features=platform.features or {},
            is_active=platform.is_active,
            is_healthy=platform.is_healthy,
            last_health_check=platform.last_health_check.isoformat() if platform.last_health_check else None,
            configuration=platform.configuration or {},
            validation_rules=platform.validation_rules or {},
            conversion_templates=platform.conversion_templates or {},
            created_at=platform.created_at.isoformat() if platform.created_at else None,
            updated_at=platform.updated_at.isoformat() if platform.updated_at else None,
        )


class PlatformHealthCheckRequest(BaseSchema):
    """Request schema for platform health check."""
    check_timeout: Optional[int] = Field(30, ge=1, le=300, description="Health check timeout in seconds")
    check_depth: Optional[str] = Field("basic", description="Health check depth: basic, detailed, comprehensive")


class PlatformHealthStatus(BaseSchema):
    """Schema for platform health status."""
    platform_id: str
    is_healthy: bool
    last_check: str
    response_time_ms: Optional[float]
    error_message: Optional[str]
    check_details: Dict[str, Any]


# Deployment Operation Schemas
class DeploymentCreateRequest(BaseSchema):
    """Request schema for creating a deployment."""
    platform_id: str = Field(..., description="Platform identifier")
    skill_id: str = Field(..., min_length=1, max_length=100, description="Skill identifier")
    skill_name: str = Field(..., min_length=1, max_length=200, description="Skill name")
    skill_version: str = Field(..., min_length=1, max_length=50, description="Skill version")
    original_format: Optional[str] = Field(None, max_length=20, description="Original skill format")
    target_format: Optional[str] = Field(None, max_length=20, description="Target platform format")
    file_size: Optional[int] = Field(None, ge=0, description="Package file size in bytes")
    checksum: Optional[str] = Field(None, max_length=64, description="Package file checksum")
    deployment_config: Dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional deployment metadata")
    max_retries: Optional[int] = Field(default=3, ge=0, le=10, description="Maximum retry attempts")

    @validator('checksum')
    def validate_checksum(cls, v):
        """Validate checksum format."""
        if v and not all(c in '0123456789abcdef' for c in v.lower()):
            raise ValueError('Checksum must be hexadecimal')
        return v.lower() if v else v


class DeploymentUpdateRequest(BaseSchema):
    """Request schema for updating a deployment."""
    status: Optional[DeploymentStatus] = None
    deployment_id: Optional[str] = Field(None, max_length=100)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    platform_response: Optional[Dict[str, Any]] = None


class DeploymentResponse(BaseSchema):
    """Response schema for deployment operations."""
    id: str
    platform_id: str
    platform_name: Optional[str]
    skill_id: str
    skill_name: str
    skill_version: str
    deployment_id: Optional[str]
    status: str
    original_format: Optional[str]
    target_format: Optional[str]
    file_size: Optional[int]
    checksum: Optional[str]
    deployment_config: Dict[str, Any]
    metadata: Dict[str, Any]
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: Optional[int]
    success: Optional[bool]
    error_message: Optional[str]
    error_details: Dict[str, Any]
    platform_response: Dict[str, Any]
    retry_count: int
    max_retries: int
    created_at: Optional[str]
    updated_at: Optional[str]

    @classmethod
    def from_model(cls, deployment) -> 'DeploymentResponse':
        """Create response from Deployment model."""
        return cls(
            id=str(deployment.id),
            platform_id=str(deployment.platform_id),
            platform_name=deployment.platform.name if deployment.platform else None,
            skill_id=deployment.skill_id,
            skill_name=deployment.skill_name,
            skill_version=deployment.skill_version,
            deployment_id=deployment.deployment_id,
            status=deployment.status,
            original_format=deployment.original_format,
            target_format=deployment.target_format,
            file_size=deployment.file_size,
            checksum=deployment.checksum,
            deployment_config=deployment.deployment_config or {},
            metadata=deployment.metadata or {},
            started_at=deployment.started_at.isoformat() if deployment.started_at else None,
            completed_at=deployment.completed_at.isoformat() if deployment.completed_at else None,
            duration_seconds=deployment.duration_seconds,
            success=deployment.success,
            error_message=deployment.error_message,
            error_details=deployment.error_details or {},
            platform_response=deployment.platform_response or {},
            retry_count=deployment.retry_count,
            max_retries=deployment.max_retries,
            created_at=deployment.created_at.isoformat() if deployment.created_at else None,
            updated_at=deployment.updated_at.isoformat() if deployment.updated_at else None,
        )


class DeploymentRetryRequest(BaseSchema):
    """Request schema for retrying a deployment."""
    force_retry: Optional[bool] = Field(False, description="Force retry even if max retries reached")


# Compatibility Check Schemas
class CompatibilityCheckRequest(BaseSchema):
    """Request schema for compatibility check."""
    skill_id: str = Field(..., min_length=1, max_length=100, description="Skill identifier")
    skill_version: Optional[str] = Field(None, max_length=50, description="Skill version")
    platforms: List[str] = Field(..., min_items=1, description="List of platform names to check")
    check_depth: Optional[str] = Field("standard", description="Check depth: basic, standard, comprehensive")
    include_recommendations: Optional[bool] = Field(True, description="Include improvement recommendations")

    @validator('platforms')
    def validate_platforms(cls, v):
        """Validate platform names."""
        valid_platforms = {pt.value for pt in PlatformType}
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f'Invalid platform: {platform}. Must be one of {valid_platforms}')
        return v


class CompatibilityIssue(BaseSchema):
    """Schema for compatibility issue."""
    type: IssueType = Field(..., description="Issue type")
    severity: IssueSeverity = Field(..., description="Issue severity")
    description: str = Field(..., description="Issue description")
    affected_platforms: List[str] = Field(..., description="Platforms affected by this issue")
    location: Optional[str] = Field(None, description="Location in code or file")
    suggestion: Optional[str] = Field(None, description="Suggested fix")


class CompatibilityWarning(BaseSchema):
    """Schema for compatibility warning."""
    type: str = Field(..., description="Warning type")
    description: str = Field(..., description="Warning description")
    affected_platforms: List[str] = Field(..., description="Platforms affected by this warning")
    recommendation: Optional[str] = Field(None, description="Recommendation to address warning")


class CompatibilityRecommendation(BaseSchema):
    """Schema for compatibility recommendation."""
    category: str = Field(..., description="Recommendation category")
    priority: str = Field(..., description="Priority: high, medium, low")
    description: str = Field(..., description="Recommendation description")
    platforms: List[str] = Field(..., description="Platforms this recommendation applies to")
    code_suggestion: Optional[str] = Field(None, description="Code modification suggestion")


class PlatformCompatibilityResult(BaseSchema):
    """Schema for platform-specific compatibility result."""
    platform_name: str = Field(..., description="Platform name")
    compatible: bool = Field(..., description="Whether skill is compatible with this platform")
    score: Optional[float] = Field(None, ge=0, le=100, description="Compatibility score (0-100)")
    issues: List[CompatibilityIssue] = Field(default_factory=list, description="Compatibility issues")
    warnings: List[CompatibilityWarning] = Field(default_factory=list, description="Compatibility warnings")
    limitations: List[str] = Field(default_factory=list, description="Platform limitations")
    supported_features: List[str] = Field(default_factory=list, description="Supported features")
    unsupported_features: List[str] = Field(default_factory=list, description="Unsupported features")


class CompatibilityCheckResponse(BaseSchema):
    """Response schema for compatibility check."""
    id: str
    skill_id: str
    check_id: str
    platforms_checked: List[str]
    skill_version: Optional[str]
    overall_compatible: bool
    compatibility_score: Optional[float]
    platform_results: Dict[str, PlatformCompatibilityResult]
    compatibility_issues: List[CompatibilityIssue]
    warnings: List[CompatibilityWarning]
    recommendations: List[CompatibilityRecommendation]
    code_suggestions: Dict[str, Any]
    feature_analysis: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    limitation_analysis: Dict[str, Any]
    detailed_report: Dict[str, Any]
    check_duration_seconds: Optional[int]
    check_version: str
    checked_at: str
    created_at: str
    updated_at: str

    @classmethod
    def from_model(cls, check) -> 'CompatibilityCheckResponse':
        """Create response from CompatibilityCheck model."""
        # Convert platform results
        platform_results = {}
        if check.platform_results:
            for platform_name, result_data in check.platform_results.items():
                platform_results[platform_name] = PlatformCompatibilityResult(
                    platform_name=platform_name,
                    compatible=result_data.get('compatible', False),
                    score=result_data.get('score'),
                    issues=[
                        CompatibilityIssue(**issue) for issue in result_data.get('issues', [])
                    ],
                    warnings=[
                        CompatibilityWarning(**warning) for warning in result_data.get('warnings', [])
                    ],
                    limitations=result_data.get('limitations', []),
                    supported_features=result_data.get('supported_features', []),
                    unsupported_features=result_data.get('unsupported_features', [])
                )

        return cls(
            id=str(check.id),
            skill_id=check.skill_id,
            check_id=check.check_id,
            platforms_checked=check.platforms_checked or [],
            skill_version=check.skill_version,
            overall_compatible=check.overall_compatible,
            compatibility_score=check.get_compatibility_score(),
            platform_results=platform_results,
            compatibility_issues=[
                CompatibilityIssue(**issue) for issue in (check.compatibility_issues or [])
            ],
            warnings=[
                CompatibilityWarning(**warning) for warning in (check.warnings or [])
            ],
            recommendations=[
                CompatibilityRecommendation(**rec) for rec in (check.recommendations or [])
            ],
            code_suggestions=check.code_suggestions or {},
            feature_analysis=check.feature_analysis or {},
            dependency_analysis=check.dependency_analysis or {},
            limitation_analysis=check.limitation_analysis or {},
            detailed_report=check.detailed_report or {},
            check_duration_seconds=check.check_duration_seconds,
            check_version=check.check_version,
            checked_at=check.checked_at.isoformat() if check.checked_at else None,
            created_at=check.created_at.isoformat() if check.created_at else None,
            updated_at=check.updated_at.isoformat() if check.updated_at else None,
        )


class CompatibilitySummary(BaseSchema):
    """Summary schema for compatibility check."""
    skill_id: str
    overall_compatible: bool
    compatibility_score: Optional[float]
    platforms_checked: int
    issues_count: int
    warnings_count: int
    recommendations_count: int
    critical_issues: int
    checked_at: str


# List and Filter Schemas
class PlatformListRequest(BaseSchema):
    """Request schema for listing platforms."""
    platform_type: Optional[PlatformType] = Field(None, description="Filter by platform type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_healthy: Optional[bool] = Field(None, description="Filter by health status")
    search: Optional[str] = Field(None, description="Search in name or display name")
    skip: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class DeploymentListRequest(BaseSchema):
    """Request schema for listing deployments."""
    platform_id: Optional[str] = Field(None, description="Filter by platform ID")
    skill_id: Optional[str] = Field(None, description="Filter by skill ID")
    status: Optional[DeploymentStatus] = Field(None, description="Filter by deployment status")
    success: Optional[bool] = Field(None, description="Filter by success status")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    skip: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class CompatibilityListRequest(BaseSchema):
    """Request schema for listing compatibility checks."""
    skill_id: Optional[str] = Field(None, description="Filter by skill ID")
    overall_compatible: Optional[bool] = Field(None, description="Filter by compatibility result")
    platforms_checked: Optional[List[str]] = Field(None, description="Filter by platforms checked")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    skip: Optional[int] = Field(0, ge=0, description="Number of records to skip")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Maximum number of records to return")


# Error Schemas
class PlatformError(BaseSchema):
    """Schema for platform-related errors."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    platform: Optional[str] = Field(None, description="Associated platform name")


class DeploymentError(BaseSchema):
    """Schema for deployment-related errors."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    deployment_id: Optional[str] = Field(None, description="Associated deployment ID")
    platform: Optional[str] = Field(None, description="Associated platform name")
    skill_id: Optional[str] = Field(None, description="Associated skill ID")
    retry_count: Optional[int] = Field(None, description="Current retry count")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class CompatibilityError(BaseSchema):
    """Schema for compatibility check errors."""
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    skill_id: Optional[str] = Field(None, description="Associated skill ID")
    check_id: Optional[str] = Field(None, description="Associated check ID")
    platforms: Optional[List[str]] = Field(None, description="Platforms being checked")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


# Bulk Operation Schemas
class BulkDeploymentRequest(BaseSchema):
    """Request schema for bulk deployment operations."""
    deployments: List[DeploymentCreateRequest] = Field(..., min_items=1, max_items=50, description="List of deployments to create")
    parallel: Optional[bool] = Field(True, description="Execute deployments in parallel")
    stop_on_error: Optional[bool] = Field(False, description="Stop on first error")


class BulkCompatibilityCheckRequest(BaseSchema):
    """Request schema for bulk compatibility checks."""
    checks: List[CompatibilityCheckRequest] = Field(..., min_items=1, max_items=20, description="List of compatibility checks")
    parallel: Optional[bool] = Field(True, description="Execute checks in parallel")
    stop_on_error: Optional[bool] = Field(False, description="Stop on first error")