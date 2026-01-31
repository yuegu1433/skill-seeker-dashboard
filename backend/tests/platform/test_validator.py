"""Tests for CompatibilityValidator.

Tests the cross-platform compatibility validation capabilities.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backend.app.platform.validator import (
    CompatibilityValidator,
    IssueSeverity,
    IssueType,
    CompatibilityIssue,
    PlatformValidationResult
)
from backend.app.platform.adapters import PlatformAdapter, ValidationError


class MockAdapter(PlatformAdapter):
    """Mock platform adapter for testing."""

    platform_id = "test_platform"
    display_name = "Test Platform"
    platform_type = "test"
    supported_formats = ["json", "yaml", "test"]
    features = ["streaming", "vision", "function_calling"]
    max_file_size = 100 * 1024 * 1024  # 100MB
    format_size_limits = {
        "json": 50 * 1024 * 1024,
        "yaml": 50 * 1024 * 1024,
        "test": 100 * 1024 * 1024
    }

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.is_initialized = True

    async def initialize(self) -> bool:
        return True

    async def validate_configuration(self) -> Dict[str, Any]:
        return {"valid": True, "errors": [], "warnings": []}

    async def validate_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        # Simulate validation logic
        errors = []
        warnings = []

        # Check required fields
        if "name" not in skill_data or not skill_data["name"]:
            errors.append("Name is required")

        # Check format
        skill_format = skill_data.get("format", "json")
        if skill_format not in self.supported_formats:
            errors.append(f"Format {skill_format} not supported")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    async def validate_skill_format(
        self,
        skill_data: Dict[str, Any],
        format_type: str
    ) -> Dict[str, Any]:
        errors = []
        warnings = []

        if format_type not in self.supported_formats:
            errors.append(f"Format {format_type} not supported")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }


@pytest.fixture
def validator():
    """Create a CompatibilityValidator instance for testing."""
    return CompatibilityValidator()


@pytest.fixture
def mock_registry():
    """Create a mock registry with test adapter."""
    registry = MagicMock()
    registry.get_registered_platforms.return_value = ["test_platform"]
    registry.get_adapter.return_value = MockAdapter()
    return registry


@pytest.fixture
def sample_skill_data():
    """Create sample skill data for testing."""
    return {
        "name": "Test Skill",
        "description": "A test skill for validation",
        "format": "json",
        "version": "1.0.0",
        "streaming": False,
        "vision": False,
        "function_calling": True,
        "content": {
            "type": "test",
            "data": "sample data"
        }
    }


@pytest.fixture
def incompatible_skill_data():
    """Create skill data with compatibility issues."""
    return {
        "name": "",  # Invalid: empty name
        "description": "A test skill",
        "format": "unsupported_format",  # Invalid: unsupported format
        "version": "invalid_version",  # Invalid: bad version format
        "streaming": True,
        "content": {
            "type": "test"
        }
    }


class TestCompatibilityIssue:
    """Test CompatibilityIssue dataclass."""

    def test_issue_creation(self):
        """Test creating a CompatibilityIssue."""
        issue = CompatibilityIssue(
            severity=IssueSeverity.ERROR,
            type=IssueType.FORMAT_INCOMPATIBLE,
            message="Test error message",
            platform="test_platform",
            field="format",
            suggestion="Use a supported format"
        )

        assert issue.severity == IssueSeverity.ERROR
        assert issue.type == IssueType.FORMAT_INCOMPATIBLE
        assert issue.message == "Test error message"
        assert issue.platform == "test_platform"
        assert issue.field == "format"
        assert issue.suggestion == "Use a supported format"


class TestPlatformValidationResult:
    """Test PlatformValidationResult dataclass."""

    def test_result_creation(self):
        """Test creating a PlatformValidationResult."""
        issues = [
            CompatibilityIssue(
                severity=IssueSeverity.ERROR,
                type=IssueType.FORMAT_INCOMPATIBLE,
                message="Test error"
            )
        ]

        result = PlatformValidationResult(
            platform_id="test_platform",
            valid=False,
            issues=issues,
            validation_time=0.5
        )

        assert result.platform_id == "test_platform"
        assert result.valid is False
        assert len(result.issues) == 1
        assert result.validation_time == 0.5


class TestCompatibilityValidator:
    """Test CompatibilityValidator class."""

    @pytest.mark.asyncio
    async def test_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert validator.registry is not None
        assert len(validator.validation_rules) > 0
        assert len(validator.platform_rules) > 0
        assert validator.stats["total_validations"] == 0

    @pytest.mark.asyncio
    async def test_validate_compatibility_success(self, validator, mock_registry, sample_skill_data):
        """Test successful compatibility validation."""
        validator.registry = mock_registry

        result = await validator.validate_compatibility(
            sample_skill_data,
            target_platforms=["test_platform"]
        )

        assert "overall_compatible" in result
        assert "compatibility_score" in result
        assert "platform_results" in result
        assert "recommendations" in result
        assert "detailed_report" in result

        # Check platform results
        assert "test_platform" in result["platform_results"]
        platform_result = result["platform_results"]["test_platform"]
        assert platform_result["platform_id"] == "test_platform"

    @pytest.mark.asyncio
    async def test_validate_compatibility_with_issues(self, validator, mock_registry, incompatible_skill_data):
        """Test validation with compatibility issues."""
        validator.registry = mock_registry

        result = await validator.validate_compatibility(
            incompatible_skill_data,
            target_platforms=["test_platform"]
        )

        # Should have issues
        platform_result = result["platform_results"]["test_platform"]
        assert len(platform_result["issues"]) > 0 or len(platform_result["warnings"]) > 0

        # Overall compatibility may be false
        if platform_result["valid"]:
            assert result["overall_compatible"] is True
        else:
            assert result["overall_compatible"] is False

    @pytest.mark.asyncio
    async def test_validate_batch_compatibility(self, validator, mock_registry, sample_skill_data):
        """Test batch compatibility validation."""
        validator.registry = mock_registry

        skills_data = [sample_skill_data, sample_skill_data]

        results = await validator.validate_batch_compatibility(
            skills_data,
            target_platforms=["test_platform"],
            max_concurrent=2
        )

        assert len(results) == 2
        assert all("success" in result for result in results)

    @pytest.mark.asyncio
    async def test_platform_validation_structure(self, validator, mock_registry, sample_skill_data):
        """Test platform validation structure."""
        validator.registry = mock_registry

        result = await validator._validate_platform(
            sample_skill_data,
            "test_platform",
            {}
        )

        assert isinstance(result, PlatformValidationResult)
        assert result.platform_id == "test_platform"
        assert "checked_features" in result.checked_features
        assert isinstance(result.issues, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.info, list)
        assert result.validation_time >= 0

    @pytest.mark.asyncio
    async def test_basic_structure_validation(self, validator):
        """Test basic structure validation."""
        issues = []
        warnings = []

        # Valid data
        skill_data = {
            "name": "Test Skill",
            "description": "Test description"
        }

        validator._validate_basic_structure(skill_data, "test_platform", issues, warnings)
        assert len(issues) == 0

        # Invalid data (missing required field)
        issues.clear()
        skill_data = {"description": "Test"}  # Missing name

        validator._validate_basic_structure(skill_data, "test_platform", issues, warnings)
        assert len(issues) > 0
        assert any("name" in str(issue.message) for issue in issues)

    @pytest.mark.asyncio
    async def test_format_compatibility_validation(self, validator, mock_registry):
        """Test format compatibility validation."""
        adapter = MockAdapter()

        # Valid format
        skill_data = {"format": "json"}
        issues = []
        warnings = []

        await validator._validate_format_compatibility(
            skill_data,
            adapter,
            "test_platform",
            issues,
            warnings
        )

        # Should not have errors for valid format
        format_errors = [i for i in issues if i.type == IssueType.FORMAT_INCOMPATIBLE]
        assert len(format_errors) == 0

        # Invalid format
        issues.clear()
        skill_data = {"format": "unsupported_format"}

        await validator._validate_format_compatibility(
            skill_data,
            adapter,
            "test_platform",
            issues,
            warnings
        )

        # Should have errors for unsupported format
        format_errors = [i for i in issues if i.type == IssueType.FORMAT_INCOMPATIBLE]
        assert len(format_errors) > 0

    @pytest.mark.asyncio
    async def test_size_constraint_validation(self, validator):
        """Test size constraint validation."""
        adapter = MockAdapter()

        # Small data
        skill_data = {"name": "Test", "format": "json"}
        issues = []
        warnings = []

        validator._validate_size_constraints(
            skill_data,
            adapter,
            "test_platform",
            issues,
            warnings
        )

        # Should not have size errors
        size_errors = [i for i in issues if i.type == IssueType.SIZE_EXCEEDED]
        assert len(size_errors) == 0

        # Large data
        issues.clear()
        warnings.clear()
        large_content = "x" * (200 * 1024 * 1024)  # 200MB
        skill_data = {"name": "Test", "format": "json", "content": large_content}

        validator._validate_size_constraints(
            skill_data,
            adapter,
            "test_platform",
            issues,
            warnings
        )

        # Should have size errors
        size_errors = [i for i in issues if i.type == IssueType.SIZE_EXCEEDED]
        assert len(size_errors) > 0

    @pytest.mark.asyncio
    async def test_overall_compatibility_calculation(self, validator):
        """Test overall compatibility calculation."""
        # Create mock results
        platform_results = {
            "platform1": PlatformValidationResult(
                platform_id="platform1",
                valid=True,
                issues=[],
                warnings=[],
                info=[]
            ),
            "platform2": PlatformValidationResult(
                platform_id="platform2",
                valid=False,
                issues=[
                    CompatibilityIssue(
                        severity=IssueSeverity.ERROR,
                        type=IssueType.FORMAT_INCOMPATIBLE,
                        message="Format error"
                    )
                ],
                warnings=[],
                info=[]
            )
        }

        result = validator._calculate_overall_compatibility(platform_results)

        assert "compatible" in result
        assert "score" in result
        assert "compatible_platforms" in result
        assert "incompatible_platforms" in result

        # Should be compatible because platform1 is valid
        assert result["compatible"] is True
        assert "platform1" in result["compatible_platforms"]
        assert "platform2" in result["incompatible_platforms"]

    @pytest.mark.asyncio
    async def test_recommendations_generation(self, validator, mock_registry, sample_skill_data):
        """Test recommendations generation."""
        validator.registry = mock_registry

        # Create platform results with common issues
        platform_results = {
            "platform1": PlatformValidationResult(
                platform_id="platform1",
                valid=False,
                issues=[
                    CompatibilityIssue(
                        severity=IssueSeverity.ERROR,
                        type=IssueType.FORMAT_INCOMPATIBLE,
                        message="Format error",
                        field="format"
                    )
                ],
                warnings=[],
                info=[]
            ),
            "platform2": PlatformValidationResult(
                platform_id="platform2",
                valid=False,
                issues=[
                    CompatibilityIssue(
                        severity=IssueSeverity.ERROR,
                        type=IssueType.FORMAT_INCOMPATIBLE,
                        message="Format error",
                        field="format"
                    )
                ],
                warnings=[],
                info=[]
            )
        }

        recommendations = validator._generate_recommendations(platform_results, sample_skill_data)

        assert isinstance(recommendations, list)
        # Should have recommendations for common issues
        if recommendations:
            assert "type" in recommendations[0]
            assert "priority" in recommendations[0]
            assert "description" in recommendations[0]

    @pytest.mark.asyncio
    async def test_best_platform_selection(self, validator):
        """Test best platform selection."""
        platform_results = {
            "platform1": PlatformValidationResult(
                platform_id="platform1",
                valid=True,
                issues=[],
                warnings=[],
                info=[]
            ),
            "platform2": PlatformValidationResult(
                platform_id="platform2",
                valid=True,
                issues=[],
                warnings=[
                    CompatibilityIssue(
                        severity=IssueSeverity.WARNING,
                        type=IssueType.FEATURE_UNSUPPORTED,
                        message="Feature warning"
                    )
                ],
                info=[]
            )
        }

        best_platform = validator._find_best_platform(platform_results)

        # platform1 should be best (no warnings)
        assert best_platform == "platform1"

    @pytest.mark.asyncio
    async def test_detailed_report_generation(self, validator, mock_registry, sample_skill_data):
        """Test detailed report generation."""
        validator.registry = mock_registry

        # Create mock validation
        platform_results = {
            "test_platform": PlatformValidationResult(
                platform_id="test_platform",
                valid=True,
                issues=[],
                warnings=[],
                info=[]
            )
        }

        recommendations = []
        report = validator._generate_detailed_report(sample_skill_data, platform_results, recommendations)

        assert "skill_summary" in report
        assert "platform_breakdown" in report
        assert "issue_summary" in report
        assert "recommendations" in report

        # Check skill summary
        assert "name" in report["skill_summary"]
        assert "format" in report["skill_summary"]
        assert "size_bytes" in report["skill_summary"]

    @pytest.mark.asyncio
    async def test_validation_statistics(self, validator, mock_registry, sample_skill_data):
        """Test validation statistics."""
        validator.registry = mock_registry

        # Perform validation
        await validator.validate_compatibility(
            sample_skill_data,
            target_platforms=["test_platform"]
        )

        stats = validator.get_validation_statistics()

        assert "total_validations" in stats
        assert "compatible_skills" in stats
        assert "incompatible_skills" in stats
        assert "compatibility_rate" in stats
        assert stats["total_validations"] >= 0

    @pytest.mark.asyncio
    async def test_all_platforms_validation(self, validator, mock_registry, sample_skill_data):
        """Test validation against all registered platforms."""
        validator.registry = mock_registry

        # Validate against all platforms (None)
        result = await validator.validate_compatibility(
            sample_skill_data,
            target_platforms=None
        )

        # Should use registered platforms
        assert "platform_results" in result
        assert "test_platform" in result["platform_results"]

    @pytest.mark.asyncio
    async def test_empty_skill_data(self, validator):
        """Test validation with empty skill data."""
        skill_data = {}

        with pytest.raises(Exception):
            await validator.validate_compatibility(
                skill_data,
                target_platforms=["test_platform"]
            )

    @pytest.mark.asyncio
    async def test_no_platforms_specified(self, validator, mock_registry, sample_skill_data):
        """Test validation with no platforms specified."""
        validator.registry = mock_registry

        # Mock registry to return no platforms
        validator.registry.get_registered_platforms.return_value = []

        result = await validator.validate_compatibility(
            sample_skill_data,
            target_platforms=None
        )

        assert result["platform_count"] == 0
        assert result["compatible_count"] == 0
        assert result["incompatible_count"] == 0

    @pytest.mark.asyncio
    async def test_platform_adapter_not_found(self, validator, sample_skill_data):
        """Test validation when platform adapter is not found."""
        # Mock registry to return invalid platform
        validator.registry.get_registered_platforms.return_value = ["nonexistent_platform"]
        validator.registry.get_adapter.return_value = None

        result = await validator.validate_compatibility(
            sample_skill_data,
            target_platforms=["nonexistent_platform"]
        )

        # Should handle missing adapter gracefully
        assert "platform_results" in result
        assert "nonexistent_platform" in result["platform_results"]
        assert result["platform_results"]["nonexistent_platform"]["valid"] is False

    @pytest.mark.asyncio
    async def test_validation_with_config(self, validator, mock_registry, sample_skill_data):
        """Test validation with custom configuration."""
        validator.registry = mock_registry

        validation_config = {
            "strict_mode": True,
            "check_dependencies": True
        }

        result = await validator.validate_compatibility(
            sample_skill_data,
            target_platforms=["test_platform"],
            validation_config=validation_config
        )

        assert "validation_config" in result
        assert result["validation_config"] == validation_config

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        async with CompatibilityValidator() as validator:
            assert validator is not None
            assert validator.executor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])