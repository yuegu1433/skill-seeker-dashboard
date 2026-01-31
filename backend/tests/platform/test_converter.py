"""Tests for FormatConverter.

Tests the format conversion capabilities across multiple platforms.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from backend.app.platform.converter import FormatConverter
from backend.app.platform.adapters import PlatformAdapter, ValidationError, ConversionError


class MockAdapter(PlatformAdapter):
    """Mock platform adapter for testing."""

    platform_id = "test_platform"
    display_name = "Test Platform"
    platform_type = "test"
    supported_formats = ["json", "yaml", "test"]

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.is_initialized = True

    async def initialize(self) -> bool:
        return True

    async def validate_configuration(self) -> Dict[str, Any]:
        return {"valid": True, "errors": [], "warnings": []}

    async def validate_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        return {"valid": True, "errors": [], "warnings": []}

    async def convert_skill(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_format: str
    ) -> Dict[str, Any]:
        if target_format == "test":
            return {
                "format": "test",
                "data": f"converted_from_{source_format}",
                "metadata": {"source_format": source_format}
            }
        raise ConversionError(f"Unsupported conversion: {source_format} -> {target_format}")

    async def get_conversion_template(
        self,
        source_format: str,
        target_format: str
    ) -> Dict[str, Any]:
        return {
            "template_type": "test_conversion",
            "fields": {"output": "data"}
        }


@pytest.fixture
def converter():
    """Create a FormatConverter instance for testing."""
    return FormatConverter()


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
        "content": {
            "type": "test",
            "data": "sample data"
        }
    }


class TestFormatConverter:
    """Test FormatConverter class."""

    @pytest.mark.asyncio
    async def test_initialization(self, converter):
        """Test converter initialization."""
        assert converter is not None
        assert converter.registry is not None
        assert len(converter.conversion_paths) > 0
        assert converter.stats["total_conversions"] == 0

    @pytest.mark.asyncio
    async def test_supported_formats(self, converter):
        """Test getting supported formats."""
        formats = converter.get_supported_formats()
        assert isinstance(formats, set)
        assert "json" in formats
        assert "yaml" in formats

    @pytest.mark.asyncio
    async def test_json_to_yaml_conversion(self, converter, sample_skill_data):
        """Test JSON to YAML conversion."""
        result = await converter.convert(
            sample_skill_data,
            "json",
            "yaml"
        )

        assert "conversion_metadata" in result
        assert result["format"] == "yaml"
        assert "data" in result
        assert isinstance(result["data"], str)

    @pytest.mark.asyncio
    async def test_yaml_to_json_conversion(self, converter, sample_skill_data):
        """Test YAML to JSON conversion."""
        # Convert to YAML first
        yaml_data = await converter.convert(
            sample_skill_data,
            "json",
            "yaml"
        )

        # Convert back to JSON
        result = await converter.convert(
            yaml_data["data"],
            "yaml",
            "json"
        )

        assert "conversion_metadata" in result
        assert result["format"] == "json"

    @pytest.mark.asyncio
    async def test_platform_conversion(self, converter, mock_registry, sample_skill_data):
        """Test platform-specific conversion."""
        converter.registry = mock_registry

        result = await converter.convert(
            sample_skill_data,
            "json",
            "test",
            platform_id="test_platform"
        )

        assert "conversion_metadata" in result
        assert result["format"] == "test"

    @pytest.mark.asyncio
    async def test_multi_step_conversion(self, converter, sample_skill_data):
        """Test multi-step conversion via intermediate format."""
        # Test conversion that requires intermediate step
        result = await converter.convert(
            sample_skill_data,
            "test1",
            "test2"
        )

        # Should find conversion path via intermediate
        paths = converter.get_conversion_paths("test1", "test2")
        assert len(paths) > 0

    @pytest.mark.asyncio
    async def test_batch_conversion(self, converter, sample_skill_data):
        """Test batch conversion."""
        conversions = [
            {
                "skill_data": sample_skill_data,
                "source_format": "json",
                "target_format": "yaml"
            },
            {
                "skill_data": sample_skill_data,
                "source_format": "json",
                "target_format": "yaml"
            }
        ]

        results = await converter.convert_batch(conversions, max_concurrent=2)

        assert len(results) == 2
        assert all("success" in result for result in results)

    @pytest.mark.asyncio
    async def test_conversion_validation(self, converter, sample_skill_data):
        """Test conversion validation."""
        validation_result = await converter.validate_conversion(
            sample_skill_data,
            "json",
            "yaml"
        )

        assert "valid" in validation_result
        assert "source_format" in validation_result
        assert "target_format" in validation_result
        assert "conversion_path" in validation_result

    @pytest.mark.asyncio
    async def test_unsupported_conversion(self, converter, sample_skill_data):
        """Test unsupported conversion raises error."""
        with pytest.raises(ConversionError):
            await converter.convert(
                sample_skill_data,
                "unsupported_format",
                "another_unsupported"
            )

    @pytest.mark.asyncio
    async def test_invalid_input(self, converter):
        """Test invalid input validation."""
        with pytest.raises(ValidationError):
            await converter.convert(
                None,
                "json",
                "yaml"
            )

        with pytest.raises(ValidationError):
            await converter.convert(
                {"name": "test"},
                "",
                "yaml"
            )

    @pytest.mark.asyncio
    async def test_cache_functionality(self, converter, sample_skill_data):
        """Test conversion caching."""
        # First conversion
        result1 = await converter.convert(
            sample_skill_data,
            "json",
            "yaml"
        )

        # Second conversion (should use cache)
        result2 = await converter.convert(
            sample_skill_data,
            "json",
            "yaml"
        )

        # Check statistics
        assert converter.stats["cache_hits"] > 0
        assert converter.stats["cache_misses"] > 0

    @pytest.mark.asyncio
    async def test_conversion_statistics(self, converter, sample_skill_data):
        """Test conversion statistics."""
        # Perform conversions
        await converter.convert(sample_skill_data, "json", "yaml")
        await converter.convert(sample_skill_data, "json", "yaml")

        stats = converter.get_conversion_statistics()

        assert "total_conversions" in stats
        assert "successful_conversions" in stats
        assert "cache_hit_rate" in stats
        assert "success_rate" in stats
        assert stats["total_conversions"] >= 0

    @pytest.mark.asyncio
    async def test_clear_cache(self, converter, sample_skill_data):
        """Test cache clearing."""
        # Perform conversion to populate cache
        await converter.convert(sample_skill_data, "json", "yaml")

        # Clear cache
        converter.clear_cache()

        # Verify cache is cleared
        assert len(converter.conversion_cache) == 0

    @pytest.mark.asyncio
    async def test_custom_conversion_rule(self, converter):
        """Test adding custom conversion rule."""
        custom_rule = {
            "method": "custom_conversion",
            "priority": 1
        }

        converter.add_conversion_rule("custom1", "custom2", custom_rule)

        # Verify rule was added
        assert ("custom1", "custom2") in converter.conversion_paths
        assert converter.conversion_paths[("custom1", "custom2")] == custom_rule

    @pytest.mark.asyncio
    async def test_conversion_paths(self, converter):
        """Test getting conversion paths."""
        paths = converter.get_conversion_paths("json", "yaml")

        assert isinstance(paths, list)
        assert len(paths) > 0

        # Verify path structure
        for path in paths:
            assert "type" in path
            assert "priority" in path

    @pytest.mark.asyncio
    async def test_conversion_time_tracking(self, converter, sample_skill_data):
        """Test conversion time tracking."""
        result = await converter.convert(
            sample_skill_data,
            "json",
            "yaml"
        )

        # Verify conversion time is recorded
        assert "conversion_metadata" in result
        assert "conversion_time" in result["conversion_metadata"]
        assert result["conversion_metadata"]["conversion_time"] >= 0

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager."""
        async with FormatConverter() as converter:
            assert converter is not None
            assert converter.executor is not None

    @pytest.mark.asyncio
    async def test_concurrent_conversions(self, converter, sample_skill_data):
        """Test concurrent conversions."""
        tasks = []
        for _ in range(5):
            task = converter.convert(sample_skill_data, "json", "yaml")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert all("conversion_metadata" in result for result in results)

    @pytest.mark.asyncio
    async def test_error_handling(self, converter, sample_skill_data):
        """Test error handling in conversions."""
        # Test with invalid platform
        with patch.object(converter.registry, 'get_adapter', return_value=None):
            with pytest.raises(ConversionError):
                await converter.convert(
                    sample_skill_data,
                    "json",
                    "test",
                    platform_id="invalid_platform"
                )

    @pytest.mark.asyncio
    async def test_conversion_with_config(self, converter, sample_skill_data):
        """Test conversion with configuration."""
        conversion_config = {
            "preserve_metadata": True,
            "include_timestamps": True
        }

        result = await converter.convert(
            sample_skill_data,
            "json",
            "yaml",
            conversion_config=conversion_config
        )

        assert "conversion_metadata" in result
        assert result["conversion_metadata"]["timestamp"] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])