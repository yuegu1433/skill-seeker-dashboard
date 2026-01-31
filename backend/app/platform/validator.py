"""Compatibility validator for cross-platform skill validation.

This module provides CompatibilityValidator class that implements
cross-platform compatibility checking with detailed reporting.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from .registry import get_registry
from .adapters import (
    PlatformAdapter,
    ValidationError,
    PlatformError,
)

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueType(Enum):
    """Issue type categories."""
    FORMAT_INCOMPATIBLE = "format_incompatible"
    FEATURE_UNSUPPORTED = "feature_unsupported"
    SIZE_EXCEEDED = "size_exceeded"
    API_LIMITATION = "api_limitation"
    SYNTAX_INVALID = "syntax_invalid"
    DEPENDENCY_MISSING = "dependency_missing"
    VERSION_INCOMPATIBLE = "version_incompatible"


@dataclass
class CompatibilityIssue:
    """Compatibility issue representation."""
    severity: IssueSeverity
    type: IssueType
    message: str
    platform: Optional[str] = None
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = field(default_factory=dict)
    suggestion: Optional[str] = None


@dataclass
class PlatformValidationResult:
    """Platform-specific validation result."""
    platform_id: str
    valid: bool
    issues: List[CompatibilityIssue] = field(default_factory=list)
    warnings: List[CompatibilityIssue] = field(default_factory=list)
    info: List[CompatibilityIssue] = field(default_factory=list)
    validation_time: float = 0.0
    checked_features: Set[str] = field(default_factory=set)


class CompatibilityValidator:
    """Cross-platform compatibility validator.

    Validates skill data across multiple platforms and provides
    detailed compatibility reports with recommendations.
    """

    def __init__(self, registry: Optional[PlatformAdapter] = None):
        """Initialize compatibility validator.

        Args:
            registry: Platform registry instance (uses global if None)
        """
        self.registry = registry or get_registry()
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Validation rules
        self.validation_rules = self._init_validation_rules()
        self.platform_rules = self._init_platform_rules()

        # Validation statistics
        self.stats = {
            "total_validations": 0,
            "compatible_skills": 0,
            "incompatible_skills": 0,
            "warnings_found": 0,
            "avg_validation_time": 0.0
        }

    def _init_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize global validation rules.

        Returns:
            Global validation rules configuration
        """
        return {
            "required_fields": {
                "name": {"type": str, "min_length": 1, "max_length": 100},
                "description": {"type": str, "max_length": 500}
            },
            "optional_fields": {
                "version": {"type": str, "pattern": r"^\d+\.\d+\.\d+$"},
                "author": {"type": str, "max_length": 100},
                "tags": {"type": list, "element_type": str}
            },
            "size_limits": {
                "max_total_size": 100 * 1024 * 1024,  # 100MB
                "max_field_size": 10 * 1024 * 1024,  # 10MB per field
                "max_fields": 100
            }
        }

    def _init_platform_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize platform-specific validation rules.

        Returns:
            Platform-specific rules configuration
        """
        return {
            "claude": {
                "max_file_size": 100 * 1024 * 1024,
                "supported_formats": ["json", "yaml", "markdown"],
                "required_features": [],
                "forbidden_fields": [],
                "max_description_length": 500,
                "model_restrictions": {}
            },
            "gemini": {
                "max_file_size": 150 * 1024 * 1024,
                "supported_formats": ["json", "yaml", "protobuf", "markdown"],
                "required_features": [],
                "forbidden_fields": [],
                "max_description_length": 1000,
                "model_restrictions": {}
            },
            "openai": {
                "max_file_size": 50 * 1024 * 1024,
                "supported_formats": ["json", "yaml", "functions", "openai"],
                "required_features": [],
                "forbidden_fields": [],
                "max_description_length": 500,
                "model_restrictions": {
                    "gpt-3.5-turbo": {"max_functions": 128},
                    "gpt-4": {"max_functions": 64}
                }
            },
            "markdown": {
                "max_file_size": 100 * 1024 * 1024,
                "supported_formats": ["markdown", "md", "json", "yaml"],
                "required_features": [],
                "forbidden_fields": [],
                "max_description_length": 1000,
                "encoding_restrictions": ["utf-8", "utf-16", "ascii"]
            }
        }

    async def validate_compatibility(
        self,
        skill_data: Dict[str, Any],
        target_platforms: Optional[List[str]] = None,
        validation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate skill compatibility across platforms.

        Args:
            skill_data: Skill data to validate
            target_platforms: List of platforms to validate against (all if None)
            validation_config: Optional validation configuration

        Returns:
            Comprehensive compatibility report

        Raises:
            ValidationError: If validation fails
        """
        start_time = asyncio.get_event_loop().time()
        self.stats["total_validations"] += 1

        try:
            # Determine target platforms
            if target_platforms is None:
                target_platforms = self.registry.get_registered_platforms()

            # Get all platform validation results
            platform_results = await self._validate_all_platforms(
                skill_data,
                target_platforms,
                validation_config
            )

            # Calculate overall compatibility
            overall_result = self._calculate_overall_compatibility(platform_results)

            # Generate recommendations
            recommendations = self._generate_recommendations(platform_results, skill_data)

            # Generate detailed report
            detailed_report = self._generate_detailed_report(
                skill_data,
                platform_results,
                recommendations
            )

            # Calculate validation time
            validation_time = asyncio.get_event_loop().time() - start_time
            self._update_avg_validation_time(validation_time)

            # Compile final result
            result = {
                "overall_compatible": overall_result["compatible"],
                "compatibility_score": overall_result["score"],
                "compatible_platforms": overall_result["compatible_platforms"],
                "incompatible_platforms": overall_result["incompatible_platforms"],
                "platform_results": platform_results,
                "platform_count": len(target_platforms),
                "compatible_count": len(overall_result["compatible_platforms"]),
                "incompatible_count": len(overall_result["incompatible_platforms"]),
                "validation_time": validation_time,
                "recommendations": recommendations,
                "detailed_report": detailed_report,
                "timestamp": datetime.utcnow().isoformat(),
                "validation_config": validation_config or {}
            }

            # Update statistics
            if overall_result["compatible"]:
                self.stats["compatible_skills"] += 1
            else:
                self.stats["incompatible_skills"] += 1

            # Count warnings
            total_warnings = sum(
                len(result["warnings"])
                for result in platform_results.values()
            )
            self.stats["warnings_found"] += total_warnings

            logger.info(
                f"Compatibility validation completed: "
                f"{len(overall_result['compatible_platforms'])}/{len(target_platforms)} compatible"
            )

            return result

        except Exception as e:
            logger.error(f"Compatibility validation failed: {str(e)}")
            raise

    async def validate_batch_compatibility(
        self,
        skills_data: List[Dict[str, Any]],
        target_platforms: Optional[List[str]] = None,
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Validate multiple skills compatibility concurrently.

        Args:
            skills_data: List of skill data
            target_platforms: List of platforms to validate against
            max_concurrent: Maximum concurrent validations

        Returns:
            List of compatibility reports
        """
        logger.info(f"Starting batch compatibility validation of {len(skills_data)} items")

        semaphore = asyncio.Semaphore(max_concurrent)
        tasks = []

        for skill_data in skills_data:
            task = self._validate_with_semaphore(
                semaphore,
                skill_data,
                target_platforms,
                self.validate_compatibility
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        successful_results = []
        failed_results = []

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_results.append({
                    "index": i,
                    "error": str(result),
                    "success": False
                })
            else:
                result["success"] = True
                successful_results.append(result)

        logger.info(
            f"Batch compatibility validation completed: "
            f"{len(successful_results)} successful, {len(failed_results)} failed"
        )

        return successful_results + failed_results

    async def _validate_all_platforms(
        self,
        skill_data: Dict[str, Any],
        target_platforms: List[str],
        validation_config: Optional[Dict[str, Any]]
    ) -> Dict[str, PlatformValidationResult]:
        """Validate skill across all target platforms.

        Args:
            skill_data: Skill data
            target_platforms: Target platforms
            validation_config: Validation configuration

        Returns:
            Platform validation results
        """
        results = {}

        # Validate against each platform
        for platform_id in target_platforms:
            try:
                result = await self._validate_platform(
                    skill_data,
                    platform_id,
                    validation_config
                )
                results[platform_id] = result
            except Exception as e:
                logger.error(f"Platform validation failed for {platform_id}: {str(e)}")
                results[platform_id] = PlatformValidationResult(
                    platform_id=platform_id,
                    valid=False,
                    issues=[CompatibilityIssue(
                        severity=IssueSeverity.ERROR,
                        type=IssueType.VERSION_INCOMPATIBLE,
                        message=f"Validation failed: {str(e)}",
                        platform=platform_id
                    )]
                )

        return results

    async def _validate_platform(
        self,
        skill_data: Dict[str, Any],
        platform_id: str,
        validation_config: Optional[Dict[str, Any]]
    ) -> PlatformValidationResult:
        """Validate skill against a specific platform.

        Args:
            skill_data: Skill data
            platform_id: Platform ID
            validation_config: Validation configuration

        Returns:
            Platform validation result
        """
        start_time = asyncio.get_event_loop().time()

        # Get platform adapter
        adapter = self.registry.get_adapter(platform_id)
        if not adapter:
            return PlatformValidationResult(
                platform_id=platform_id,
                valid=False,
                issues=[CompatibilityIssue(
                    severity=IssueSeverity.ERROR,
                    type=IssueType.FEATURE_UNSUPPORTED,
                    message=f"Platform adapter not found: {platform_id}",
                    platform=platform_id
                )]
            )

        issues = []
        warnings = []
        info = []
        checked_features = set()

        # 1. Validate basic structure
        self._validate_basic_structure(skill_data, platform_id, issues, warnings)

        # 2. Validate format compatibility
        format_result = await self._validate_format_compatibility(
            skill_data,
            adapter,
            platform_id,
            issues,
            warnings
        )
        if format_result:
            checked_features.add("format")

        # 3. Validate size constraints
        size_result = self._validate_size_constraints(
            skill_data,
            adapter,
            platform_id,
            issues,
            warnings
        )
        if size_result:
            checked_features.add("size")

        # 4. Validate platform-specific requirements
        platform_result = await self._validate_platform_requirements(
            skill_data,
            adapter,
            platform_id,
            issues,
            warnings,
            info
        )
        if platform_result:
            checked_features.add("platform_specific")

        # 5. Validate features
        feature_result = await self._validate_features(
            skill_data,
            adapter,
            platform_id,
            issues,
            warnings,
            info
        )
        if feature_result:
            checked_features.add("features")

        # Calculate validation time
        validation_time = asyncio.get_event_loop().time() - start_time

        # Determine overall validity
        has_errors = any(issue.severity == IssueSeverity.ERROR for issue in issues)
        valid = not has_errors

        return PlatformValidationResult(
            platform_id=platform_id,
            valid=valid,
            issues=issues,
            warnings=warnings,
            info=info,
            validation_time=validation_time,
            checked_features=checked_features
        )

    def _validate_basic_structure(
        self,
        skill_data: Dict[str, Any],
        platform_id: str,
        issues: List[CompatibilityIssue],
        warnings: List[CompatibilityIssue]
    ) -> None:
        """Validate basic skill structure.

        Args:
            skill_data: Skill data
            platform_id: Platform ID
            issues: Issues list
            warnings: Warnings list
        """
        # Check required fields
        for field_name, field_rules in self.validation_rules["required_fields"].items():
            if field_name not in skill_data:
                issues.append(CompatibilityIssue(
                    severity=IssueSeverity.ERROR,
                    type=IssueType.SYNTAX_INVALID,
                    message=f"Required field missing: {field_name}",
                    platform=platform_id,
                    field=field_name
                ))
                continue

            value = skill_data[field_name]

            # Type validation
            if not isinstance(value, field_rules["type"]):
                issues.append(CompatibilityIssue(
                    severity=IssueSeverity.ERROR,
                    type=IssueType.SYNTAX_INVALID,
                    message=f"Field {field_name} must be of type {field_rules['type'].__name__}",
                    platform=platform_id,
                    field=field_name
                ))

            # Length validation
            if "min_length" in field_rules and len(str(value)) < field_rules["min_length"]:
                issues.append(CompatibilityIssue(
                    severity=IssueSeverity.ERROR,
                    type=IssueType.SYNTAX_INVALID,
                    message=f"Field {field_name} must be at least {field_rules['min_length']} characters",
                    platform=platform_id,
                    field=field_name
                ))

            if "max_length" in field_rules and len(str(value)) > field_rules["max_length"]:
                warnings.append(CompatibilityIssue(
                    severity=IssueSeverity.WARNING,
                    type=IssueType.SYNTAX_INVALID,
                    message=f"Field {field_name} exceeds recommended length of {field_rules['max_length']} characters",
                    platform=platform_id,
                    field=field_name
                ))

    async def _validate_format_compatibility(
        self,
        skill_data: Dict[str, Any],
        adapter: PlatformAdapter,
        platform_id: str,
        issues: List[CompatibilityIssue],
        warnings: List[CompatibilityIssue]
    ) -> bool:
        """Validate format compatibility.

        Args:
            skill_data: Skill data
            adapter: Platform adapter
            platform_id: Platform ID
            issues: Issues list
            warnings: Warnings list

        Returns:
            True if validation performed
        """
        try:
            # Get skill format
            skill_format = skill_data.get("format", "json")

            # Check if format is supported
            if skill_format not in adapter.supported_formats:
                issues.append(CompatibilityIssue(
                    severity=IssueSeverity.ERROR,
                    type=IssueType.FORMAT_INCOMPATIBLE,
                    message=f"Format '{skill_format}' not supported by {platform_id}",
                    platform=platform_id,
                    field="format",
                    details={
                        "skill_format": skill_format,
                        "supported_formats": adapter.supported_formats
                    },
                    suggestion=f"Convert to one of: {', '.join(adapter.supported_formats)}"
                ))
                return False

            # Validate format with adapter
            if hasattr(adapter, "validate_skill_format"):
                validation_result = await adapter.validate_skill_format(skill_data, skill_format)

                if not validation_result["valid"]:
                    issues.extend([
                        CompatibilityIssue(
                            severity=IssueSeverity.ERROR,
                            type=IssueType.FORMAT_INCOMPATIBLE,
                            message=error,
                            platform=platform_id,
                            details={"validation_result": validation_result}
                        )
                        for error in validation_result.get("errors", [])
                    ])

                    warnings.extend([
                        CompatibilityIssue(
                            severity=IssueSeverity.WARNING,
                            type=IssueType.FORMAT_INCOMPATIBLE,
                            message=warning,
                            platform=platform_id,
                            details={"validation_result": validation_result}
                        )
                        for warning in validation_result.get("warnings", [])
                    ])

            return True

        except Exception as e:
            issues.append(CompatibilityIssue(
                severity=IssueSeverity.ERROR,
                type=IssueType.FORMAT_INCOMPATIBLE,
                message=f"Format validation failed: {str(e)}",
                platform=platform_id,
                details={"error": str(e)}
            ))
            return False

    def _validate_size_constraints(
        self,
        skill_data: Dict[str, Any],
        adapter: PlatformAdapter,
        platform_id: str,
        issues: List[CompatibilityIssue],
        warnings: List[CompatibilityIssue]
    ) -> bool:
        """Validate size constraints.

        Args:
            skill_data: Skill data
            adapter: Platform adapter
            platform_id: Platform ID
            issues: Issues list
            warnings: Warnings list

        Returns:
            True if validation performed
        """
        try:
            # Calculate skill size
            skill_str = json.dumps(skill_data, separators=(',', ':'))
            skill_size = len(skill_str.encode('utf-8'))

            # Check against adapter limit
            max_size = adapter.max_file_size
            if skill_size > max_size:
                issues.append(CompatibilityIssue(
                    severity=IssueSeverity.ERROR,
                    type=IssueType.SIZE_EXCEEDED,
                    message=f"Skill size ({skill_size} bytes) exceeds {platform_id} limit ({max_size} bytes)",
                    platform=platform_id,
                    details={
                        "skill_size": skill_size,
                        "max_size": max_size,
                        "percentage": (skill_size / max_size) * 100
                    },
                    suggestion="Compress skill data or split into smaller components"
                ))
                return False

            # Check format-specific limits
            format_type = skill_data.get("format", "json")
            if format_type in adapter.format_size_limits:
                format_limit = adapter.format_size_limits[format_type]
                if skill_size > format_limit:
                    warnings.append(CompatibilityIssue(
                        severity=IssueSeverity.WARNING,
                        type=IssueType.SIZE_EXCEEDED,
                        message=f"Skill size ({skill_size} bytes) exceeds {format_type} format limit ({format_limit} bytes)",
                        platform=platform_id,
                        details={
                            "skill_size": skill_size,
                            "format_limit": format_limit,
                            "percentage": (skill_size / format_limit) * 100
                        }
                    ))

            return True

        except Exception as e:
            issues.append(CompatibilityIssue(
                severity=IssueSeverity.ERROR,
                type=IssueType.SIZE_EXCEEDED,
                message=f"Size validation failed: {str(e)}",
                platform=platform_id,
                details={"error": str(e)}
            ))
            return False

    async def _validate_platform_requirements(
        self,
        skill_data: Dict[str, Any],
        adapter: PlatformAdapter,
        platform_id: str,
        issues: List[CompatibilityIssue],
        warnings: List[CompatibilityIssue],
        info: List[CompatibilityIssue]
    ) -> bool:
        """Validate platform-specific requirements.

        Args:
            skill_data: Skill data
            adapter: Platform adapter
            platform_id: Platform ID
            issues: Issues list
            warnings: Warnings list
            info: Info list

        Returns:
            True if validation performed
        """
        try:
            # Get platform rules
            platform_rules = self.platform_rules.get(platform_id, {})

            # Validate description length
            if "description" in skill_data and "max_description_length" in platform_rules:
                desc_length = len(skill_data["description"])
                max_length = platform_rules["max_description_length"]

                if desc_length > max_length:
                    warnings.append(CompatibilityIssue(
                        severity=IssueSeverity.WARNING,
                        type=IssueType.API_LIMITATION,
                        message=f"Description length ({desc_length}) exceeds {platform_id} recommended limit ({max_length})",
                        platform=platform_id,
                        field="description",
                        details={
                            "current_length": desc_length,
                            "max_length": max_length
                        }
                    ))

            # Validate forbidden fields
            if "forbidden_fields" in platform_rules:
                forbidden = platform_rules["forbidden_fields"]
                for field in forbidden:
                    if field in skill_data:
                        issues.append(CompatibilityIssue(
                            severity=IssueSeverity.ERROR,
                            type=IssueType.FEATURE_UNSUPPORTED,
                            message=f"Field '{field}' is not supported by {platform_id}",
                            platform=platform_id,
                            field=field,
                            suggestion=f"Remove field '{field}' or convert to supported format"
                        ))

            # Validate model restrictions
            if "model_restrictions" in platform_rules:
                model_restrictions = platform_rules["model_restrictions"]
                model = skill_data.get("model")

                if model and model in model_restrictions:
                    restrictions = model_restrictions[model]
                    for restriction, limit in restrictions.items():
                        current_value = skill_data.get(restriction, 0)
                        if current_value > limit:
                            issues.append(CompatibilityIssue(
                                severity=IssueSeverity.ERROR,
                                type=IssueType.API_LIMITATION,
                                message=f"{restriction} ({current_value}) exceeds {model} limit ({limit})",
                                platform=platform_id,
                                field=restriction,
                                details={
                                    "model": model,
                                    "restriction": restriction,
                                    "current": current_value,
                                    "limit": limit
                                }
                            ))

            return True

        except Exception as e:
            issues.append(CompatibilityIssue(
                severity=IssueSeverity.ERROR,
                type=IssueType.VERSION_INCOMPATIBLE,
                message=f"Platform requirement validation failed: {str(e)}",
                platform=platform_id,
                details={"error": str(e)}
            ))
            return False

    async def _validate_features(
        self,
        skill_data: Dict[str, Any],
        adapter: PlatformAdapter,
        platform_id: str,
        issues: List[CompatibilityIssue],
        warnings: List[CompatibilityIssue],
        info: List[CompatibilityIssue]
    ) -> bool:
        """Validate feature compatibility.

        Args:
            skill_data: Skill data
            adapter: Platform adapter
            platform_id: Platform ID
            issues: Issues list
            warnings: Warnings list
            info: Info list

        Returns:
            True if validation performed
        """
        try:
            # Check required features
            for capability, required in [
                ("streaming", skill_data.get("streaming", False)),
                ("vision", skill_data.get("vision", False)),
                ("function_calling", skill_data.get("function_calling", False))
            ]:
                if required:
                    # Check if platform supports capability
                    if capability not in [f.value for f in adapter.features]:
                        warnings.append(CompatibilityIssue(
                            severity=IssueSeverity.WARNING,
                            type=IssueType.FEATURE_UNSUPPORTED,
                            message=f"Feature '{capability}' requested but not supported by {platform_id}",
                            platform=platform_id,
                            details={"capability": capability}
                        ))

            # Add feature compatibility info
            supported_features = set(adapter.features)
            requested_features = {
                "streaming": skill_data.get("streaming", False),
                "vision": skill_data.get("vision", False),
                "function_calling": skill_data.get("function_calling", False)
            }

            compatible_features = [
                feature for feature, requested in requested_features.items()
                if not requested or feature in [f.value for f in adapter.features]
            ]

            info.append(CompatibilityIssue(
                severity=IssueSeverity.INFO,
                type=IssueType.FEATURE_UNSUPPORTED,
                message=f"Compatible features with {platform_id}: {', '.join(compatible_features)}",
                platform=platform_id,
                details={
                    "supported_features": list(supported_features),
                    "compatible_features": compatible_features
                }
            ))

            return True

        except Exception as e:
            issues.append(CompatibilityIssue(
                severity=IssueSeverity.ERROR,
                type=IssueType.FEATURE_UNSUPPORTED,
                message=f"Feature validation failed: {str(e)}",
                platform=platform_id,
                details={"error": str(e)}
            ))
            return False

    def _calculate_overall_compatibility(
        self,
        platform_results: Dict[str, PlatformValidationResult]
    ) -> Dict[str, Any]:
        """Calculate overall compatibility metrics.

        Args:
            platform_results: Platform validation results

        Returns:
            Overall compatibility result
        """
        compatible_platforms = []
        incompatible_platforms = []
        total_score = 0.0

        for platform_id, result in platform_results.items():
            if result.valid:
                compatible_platforms.append(platform_id)
                # Score based on warnings and info (100 - warnings - info)
                score = 100.0 - (len(result.warnings) * 10) - (len(result.info) * 5)
                score = max(0, score)
                total_score += score
            else:
                incompatible_platforms.append(platform_id)

        platform_count = len(platform_results)
        if platform_count > 0:
            avg_score = total_score / platform_count
        else:
            avg_score = 0.0

        # Overall compatible if at least one platform is compatible
        overall_compatible = len(compatible_platforms) > 0

        return {
            "compatible": overall_compatible,
            "score": avg_score,
            "compatible_platforms": compatible_platforms,
            "incompatible_platforms": incompatible_platforms
        }

    def _generate_recommendations(
        self,
        platform_results: Dict[str, PlatformValidationResult],
        skill_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate compatibility recommendations.

        Args:
            platform_results: Platform validation results
            skill_data: Original skill data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze issues across platforms
        common_issues = {}
        for platform_id, result in platform_results.items():
            for issue in result.issues:
                issue_key = (issue.type, issue.field)
                if issue_key not in common_issues:
                    common_issues[issue_key] = []
                common_issues[issue_key].append(platform_id)

        # Generate recommendations for common issues
        for (issue_type, field), platforms in common_issues.items():
            if len(platforms) > 1:  # Common to multiple platforms
                if issue_type == IssueType.FORMAT_INCOMPATIBLE:
                    recommendations.append({
                        "type": "format_conversion",
                        "priority": "high",
                        "description": f"Convert format to be compatible with {', '.join(platforms)}",
                        "affected_platforms": platforms,
                        "field": field,
                        "action": "Convert to a universally supported format like JSON"
                    })
                elif issue_type == IssueType.SIZE_EXCEEDED:
                    recommendations.append({
                        "type": "size_optimization",
                        "priority": "medium",
                        "description": f"Reduce skill size for compatibility with {', '.join(platforms)}",
                        "affected_platforms": platforms,
                        "field": field,
                        "action": "Compress content or split into smaller components"
                    })
                elif issue_type == IssueType.FEATURE_UNSUPPORTED:
                    recommendations.append({
                        "type": "feature_removal",
                        "priority": "medium",
                        "description": f"Remove unsupported features for {', '.join(platforms)}",
                        "affected_platforms": platforms,
                        "field": field,
                        "action": "Use conditional feature detection or platform-specific versions"
                    })

        # Add recommendations for best platform choice
        best_platform = self._find_best_platform(platform_results)
        if best_platform:
            recommendations.append({
                "type": "platform_selection",
                "priority": "info",
                "description": f"Best compatible platform: {best_platform}",
                "action": f"Prioritize deployment to {best_platform} for optimal compatibility"
            })

        return recommendations

    def _find_best_platform(
        self,
        platform_results: Dict[str, PlatformValidationResult]
    ) -> Optional[str]:
        """Find the best compatible platform.

        Args:
            platform_results: Platform validation results

        Returns:
            Best platform ID or None
        """
        best_platform = None
        best_score = -1

        for platform_id, result in platform_results.items():
            if result.valid:
                # Calculate score: 100 - warnings*10 - info*5
                score = 100.0 - (len(result.warnings) * 10) - (len(result.info) * 5)
                if score > best_score:
                    best_score = score
                    best_platform = platform_id

        return best_platform

    def _generate_detailed_report(
        self,
        skill_data: Dict[str, Any],
        platform_results: Dict[str, PlatformValidationResult],
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate detailed compatibility report.

        Args:
            skill_data: Original skill data
            platform_results: Platform validation results
            recommendations: Recommendations list

        Returns:
            Detailed report
        """
        report = {
            "skill_summary": {
                "name": skill_data.get("name", "Unknown"),
                "format": skill_data.get("format", "json"),
                "size_bytes": len(json.dumps(skill_data, separators=(',', ':')).encode('utf-8')),
                "features": {
                    "streaming": skill_data.get("streaming", False),
                    "vision": skill_data.get("vision", False),
                    "function_calling": skill_data.get("function_calling", False)
                }
            },
            "platform_breakdown": {},
            "issue_summary": {
                "total_errors": 0,
                "total_warnings": 0,
                "total_info": 0,
                "by_type": {},
                "by_platform": {}
            },
            "recommendations": recommendations
        }

        # Platform breakdown
        for platform_id, result in platform_results.items():
            report["platform_breakdown"][platform_id] = {
                "valid": result.valid,
                "validation_time": result.validation_time,
                "checked_features": list(result.checked_features),
                "error_count": len(result.issues),
                "warning_count": len(result.warnings),
                "info_count": len(result.info),
                "issues": [
                    {
                        "severity": issue.severity.value,
                        "type": issue.type.value,
                        "message": issue.message,
                        "field": issue.field,
                        "suggestion": issue.suggestion
                    }
                    for issue in result.issues
                ],
                "warnings": [
                    {
                        "severity": issue.severity.value,
                        "type": issue.type.value,
                        "message": issue.message,
                        "field": issue.field
                    }
                    for issue in result.warnings
                ]
            }

        # Issue summary
        for result in platform_results.values():
            report["issue_summary"]["total_errors"] += len(result.issues)
            report["issue_summary"]["total_warnings"] += len(result.warnings)
            report["issue_summary"]["total_info"] += len(result.info)

            # By type
            for issue in result.issues:
                issue_type = issue.type.value
                if issue_type not in report["issue_summary"]["by_type"]:
                    report["issue_summary"]["by_type"][issue_type] = 0
                report["issue_summary"]["by_type"][issue_type] += 1

            # By platform
            platform_key = result.platform_id
            if platform_key not in report["issue_summary"]["by_platform"]:
                report["issue_summary"]["by_platform"][platform_key] = {
                    "errors": 0,
                    "warnings": 0,
                    "info": 0
                }
            report["issue_summary"]["by_platform"][platform_key]["errors"] += len(result.issues)
            report["issue_summary"]["by_platform"][platform_key]["warnings"] += len(result.warnings)
            report["issue_summary"]["by_platform"][platform_key]["info"] += len(result.info)

        return report

    async def _validate_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        skill_data: Dict[str, Any],
        target_platforms: Optional[List[str]],
        validate_func
    ) -> Dict[str, Any]:
        """Execute validation with semaphore control.

        Args:
            semaphore: Semaphore instance
            skill_data: Skill data
            target_platforms: Target platforms
            validate_func: Validation function

        Returns:
            Validation result
        """
        async with semaphore:
            return await validate_func(skill_data, target_platforms)

    def _update_avg_validation_time(self, validation_time: float) -> None:
        """Update average validation time statistic.

        Args:
            validation_time: Validation time in seconds
        """
        total = self.stats["total_validations"]
        current_avg = self.stats["avg_validation_time"]

        # Update running average
        self.stats["avg_validation_time"] = (
            (current_avg * (total - 1) + validation_time) / total
        )

    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()

        # Calculate compatibility rate
        if stats["total_validations"] > 0:
            stats["compatibility_rate"] = (
                stats["compatible_skills"] / stats["total_validations"] * 100
            )
        else:
            stats["compatibility_rate"] = 0.0

        return stats

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.executor.shutdown(wait=True)