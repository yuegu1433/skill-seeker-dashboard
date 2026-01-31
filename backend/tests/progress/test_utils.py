"""Test cases for progress tracking utility functions.

This module contains comprehensive unit tests for all progress tracking
utility functions including serializers, validators, and formatters.
"""

import pytest
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID, uuid4

from backend.app.progress.utils.serializers import (
    BaseSerializer,
    TaskProgressSerializer,
    TaskLogSerializer,
    NotificationSerializer,
    ProgressMetricSerializer,
    SerializationError,
    DeserializationError
)
from backend.app.progress.utils.validators import (
    validate_task_id,
    validate_user_id,
    validate_progress_value,
    validate_status,
    validate_log_level,
    validate_metric_name,
    validate_metadata,
    validate_tags,
    validate_duration,
    ValidationError,
    ValidationResult
)
from backend.app.progress.utils.formatters import (
    format_duration,
    format_percentage,
    format_timestamp,
    format_status,
    format_log_level,
    format_priority,
    format_file_size,
    format_number,
    format_datetime_range,
    format_task_summary,
    format_log_summary
)


class TestSerializers:
    """Test cases for serialization utilities."""

    def test_base_serializer_to_json_serializable_datetime(self):
        """Test BaseSerializer with datetime objects."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = BaseSerializer.to_json_serializable(dt)
        assert result == "2024-01-15T10:30:00"

    def test_base_serializer_to_json_serializable_uuid(self):
        """Test BaseSerializer with UUID objects."""
        test_uuid = uuid4()
        result = BaseSerializer.to_json_serializable(test_uuid)
        assert result == str(test_uuid)
        assert isinstance(result, str)

    def test_base_serializer_to_json_serializable_dict(self):
        """Test BaseSerializer with dictionary."""
        data = {
            "datetime": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            "uuid": uuid4(),
            "string": "test",
            "number": 42,
            "nested": {
                "datetime": datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
                "list": [1, 2, 3]
            }
        }
        result = BaseSerializer.to_json_serializable(data)

        assert isinstance(result["datetime"], str)
        assert isinstance(result["uuid"], str)
        assert result["string"] == "test"
        assert result["number"] == 42
        assert isinstance(result["nested"]["datetime"], str)
        assert result["nested"]["list"] == [1, 2, 3]

    def test_base_serializer_to_json_serializable_list(self):
        """Test BaseSerializer with list."""
        data = [
            datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            uuid4(),
            "string",
            42,
            {"key": "value"}
        ]
        result = BaseSerializer.to_json_serializable(data)

        assert isinstance(result[0], str)
        assert isinstance(result[1], str)
        assert result[2] == "string"
        assert result[3] == 42
        assert result[4]["key"] == "value"

    def test_base_serializer_to_json_serializable_primitives(self):
        """Test BaseSerializer with primitive types."""
        # String
        assert BaseSerializer.to_json_serializable("test") == "test"

        # Integer
        assert BaseSerializer.to_json_serializable(42) == 42

        # Float
        assert BaseSerializer.to_json_serializable(3.14) == 3.14

        # Boolean
        assert BaseSerializer.to_json_serializable(True) is True

        # None
        assert BaseSerializer.to_json_serializable(None) is None

    def test_base_serializer_to_json_serializable_error(self):
        """Test BaseSerializer with non-serializable object."""
        class NonSerializable:
            pass

        obj = NonSerializable()
        with pytest.raises(SerializationError):
            BaseSerializer.to_json_serializable(obj)


class TestValidators:
    """Test cases for validation utilities."""

    def test_validate_task_id_valid(self):
        """Test validate_task_id with valid IDs."""
        valid_ids = [
            "task-001",
            "task_002",
            "task003",
            "a",
            "task-with-dashes",
            "task_with_underscores",
            "Task123",
            "task-123-abc"
        ]

        for task_id in valid_ids:
            result = validate_task_id(task_id)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_task_id_invalid(self):
        """Test validate_task_id with invalid IDs."""
        invalid_ids = [
            "",  # Empty string
            " ",  # Whitespace
            "task@001",  # Special character @
            "task.001",  # Special character .
            "task 001",  # Space
            "task\t001",  # Tab
            "task\n001",  # Newline
            "task-001-",  # Ends with dash
            "-task-001",  # Starts with dash
        ]

        for task_id in invalid_ids:
            result = validate_task_id(task_id)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_user_id_valid(self):
        """Test validate_user_id with valid IDs."""
        valid_ids = [
            "user-001",
            "user_002",
            "user003",
            "u",
            "user-with-dashes",
            "User123"
        ]

        for user_id in valid_ids:
            result = validate_user_id(user_id)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_user_id_invalid(self):
        """Test validate_user_id with invalid IDs."""
        invalid_ids = [
            "",
            " ",
            "user@001",
            "user.001",
            "user 001"
        ]

        for user_id in invalid_ids:
            result = validate_user_id(user_id)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_progress_value_valid(self):
        """Test validate_progress_value with valid values."""
        valid_values = [
            0.0,
            25.5,
            50.0,
            75.25,
            100.0
        ]

        for value in valid_values:
            result = validate_progress_value(value)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_progress_value_invalid(self):
        """Test validate_progress_value with invalid values."""
        invalid_values = [
            -1.0,  # Negative
            101.0,  # Greater than 100
            -0.1,  # Slightly negative
            100.1,  # Slightly greater than 100
            "50",  # String instead of number
            None,  # None value
            [],  # List
            {}  # Dict
        ]

        for value in invalid_values:
            result = validate_progress_value(value)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_status_valid(self):
        """Test validate_status with valid statuses."""
        valid_statuses = [
            "pending",
            "running",
            "completed",
            "failed",
            "paused",
            "cancelled"
        ]

        for status in valid_statuses:
            result = validate_status(status)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_status_invalid(self):
        """Test validate_status with invalid statuses."""
        invalid_statuses = [
            "",
            " ",
            "PENDING",  # Wrong case
            "Running",  # Wrong case
            "completed ",  # With trailing space
            " running",  # With leading space
            "unknown",  # Not in list
            "in_progress",  # Not in list
            123,  # Not a string
            None
        ]

        for status in invalid_statuses:
            result = validate_status(status)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_log_level_valid(self):
        """Test validate_log_level with valid levels."""
        valid_levels = [
            "DEBUG",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL"
        ]

        for level in valid_levels:
            result = validate_log_level(level)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_log_level_invalid(self):
        """Test validate_log_level with invalid levels."""
        invalid_levels = [
            "",
            "debug",  # Wrong case
            "Info",  # Wrong case
            "warn",  # Wrong case
            "debugging",  # Not in list
            "trace",  # Not in list
            123,  # Not a string
            None
        ]

        for level in invalid_levels:
            result = validate_log_level(level)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_metric_name_valid(self):
        """Test validate_metric_name with valid names."""
        valid_names = [
            "response_time",
            "cpu_usage",
            "memory-usage",
            "task_completion_rate",
            "a",
            "metric123",
            "test-metric-456"
        ]

        for name in valid_names:
            result = validate_metric_name(name)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_metric_name_invalid(self):
        """Test validate_metric_name with invalid names."""
        invalid_names = [
            "",
            " ",
            "metric@name",  # Special character @
            "metric.name",  # Special character .
            "metric name",  # Space
            "123metric",  # Starts with number
        ]

        for name in invalid_names:
            result = validate_metric_name(name)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_metadata_valid(self):
        """Test validate_metadata with valid metadata."""
        valid_metadata = [
            {},  # Empty dict
            {"key": "value"},
            {"key1": "value1", "key2": "value2"},
            {"nested": {"key": "value"}},
            {"list": [1, 2, 3]},
            {"number": 42},
            {"boolean": True},
            {"null": None}
        ]

        for metadata in valid_metadata:
            result = validate_metadata(metadata)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_metadata_invalid(self):
        """Test validate_metadata with invalid metadata."""
        invalid_metadata = [
            "string",  # Not a dict
            123,  # Not a dict
            None,  # None
            ["list"]  # Not a dict
        ]

        for metadata in invalid_metadata:
            result = validate_metadata(metadata)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_tags_valid(self):
        """Test validate_tags with valid tags."""
        valid_tags = [
            [],  # Empty list
            ["tag1"],
            ["tag1", "tag2"],
            ["a"],
            ["tag-with-dashes"],
            ["tag_with_underscores"],
            ["TAG123"]
        ]

        for tags in valid_tags:
            result = validate_tags(tags)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_tags_invalid(self):
        """Test validate_tags with invalid tags."""
        invalid_tags = [
            "string",  # Not a list
            123,  # Not a list
            None,  # None
            {"key": "value"},  # Not a list
            [""],  # Empty string in list
            ["tag@1"],  # Special character @
            ["tag.1"],  # Special character .
            ["tag 1"]  # Space
        ]

        for tags in invalid_tags:
            result = validate_tags(tags)
            assert result.is_valid is False
            assert len(result.errors) > 0

    def test_validate_duration_valid(self):
        """Test validate_duration with valid durations."""
        valid_durations = [
            0,
            1,
            60,
            3600,
            86400,
            999999
        ]

        for duration in valid_durations:
            result = validate_duration(duration)
            assert result.is_valid is True
            assert len(result.errors) == 0

    def test_validate_duration_invalid(self):
        """Test validate_duration with invalid durations."""
        invalid_durations = [
            -1,  # Negative
            -100,  # Negative
            "60",  # String
            None,  # None
            3.14,  # Float
            [],  # List
            {}  # Dict
        ]

        for duration in invalid_durations:
            result = validate_duration(duration)
            assert result.is_valid is False
            assert len(result.errors) > 0


class TestFormatters:
    """Test cases for formatting utilities."""

    def test_format_duration(self):
        """Test format_duration function."""
        # Test seconds
        assert format_duration(5) == "5s"
        assert format_duration(59) == "59s"

        # Test minutes
        assert format_duration(60) == "1m"
        assert format_duration(61) == "1m 1s"
        assert format_duration(119) == "1m 59s"
        assert format_duration(120) == "2m"

        # Test hours
        assert format_duration(3600) == "1h"
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(7200) == "2h"
        assert format_duration(7261) == "2h 1m 1s"

        # Test edge cases
        assert format_duration(0) == "0s"
        assert format_duration(None) == "N/A"
        assert format_duration(-1) == "Invalid"
        assert format_duration("invalid") == "Invalid"

    def test_format_percentage(self):
        """Test format_percentage function."""
        # Test basic percentages
        assert format_percentage(0) == "0%"
        assert format_percentage(25) == "25%"
        assert format_percentage(50) == "50%"
        assert format_percentage(75) == "75%"
        assert format_percentage(100) == "100%"

        # Test with decimals
        assert format_percentage(25.5) == "25.5%"
        assert format_percentage(33.33) == "33.33%"

        # Test edge cases
        assert format_percentage(None) == "N/A"
        assert format_percentage(-1) == "N/A"
        assert format_percentage(101) == "N/A"

    def test_format_timestamp(self):
        """Test format_timestamp function."""
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

        # Test with datetime object
        result = format_timestamp(dt)
        assert isinstance(result, str)
        assert "2024-01-15" in result
        assert "10:30:00" in result

        # Test with ISO format string
        iso_str = "2024-01-15T10:30:00"
        result = format_timestamp(iso_str)
        assert isinstance(result, str)

        # Test edge cases
        assert format_timestamp(None) == "N/A"
        assert format_timestamp("invalid") == "Invalid"

    def test_format_status(self):
        """Test format_status function."""
        # Test valid statuses
        assert format_status("pending") == "Pending"
        assert format_status("running") == "Running"
        assert format_status("completed") == "Completed"
        assert format_status("failed") == "Failed"
        assert format_status("paused") == "Paused"
        assert format_status("cancelled") == "Cancelled"

        # Test edge cases
        assert format_status("") == "Unknown"
        assert format_status(None) == "Unknown"
        assert format_status("invalid") == "Unknown"

    def test_format_log_level(self):
        """Test format_log_level function."""
        # Test valid levels
        assert format_log_level("DEBUG") == "Debug"
        assert format_log_level("INFO") == "Info"
        assert format_log_level("WARNING") == "Warning"
        assert format_log_level("ERROR") == "Error"
        assert format_log_level("CRITICAL") == "Critical"

        # Test edge cases
        assert format_log_level("") == "Unknown"
        assert format_log_level(None) == "Unknown"
        assert format_log_level("invalid") == "Unknown"

    def test_format_priority(self):
        """Test format_priority function."""
        # Test valid priorities
        assert format_priority("low") == "Low"
        assert format_priority("normal") == "Normal"
        assert format_priority("high") == "High"
        assert format_priority("urgent") == "Urgent"

        # Test edge cases
        assert format_priority("") == "Normal"
        assert format_priority(None) == "Normal"
        assert format_priority("invalid") == "Normal"

    def test_format_file_size(self):
        """Test format_file_size function."""
        # Test bytes
        assert format_file_size(0) == "0 B"
        assert format_file_size(1023) == "1023 B"

        # Test kilobytes
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
        assert format_file_size(1024 * 10) == "10.0 KB"

        # Test megabytes
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(1024 * 1024 * 2.5) == "2.5 MB"

        # Test gigabytes
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"
        assert format_file_size(1024 * 1024 * 1024 * 5.75) == "5.8 GB"

        # Test edge cases
        assert format_file_size(None) == "N/A"
        assert format_file_size(-1) == "N/A"
        assert format_file_size("invalid") == "N/A"

    def test_format_number(self):
        """Test format_number function."""
        # Test integers
        assert format_number(0) == "0"
        assert format_number(100) == "100"
        assert format_number(1000) == "1,000"
        assert format_number(1000000) == "1,000,000"

        # Test floats
        assert format_number(3.14) == "3.14"
        assert format_number(1000.5) == "1,000.5"
        assert format_number(1234567.89) == "1,234,567.89"

        # Test edge cases
        assert format_number(None) == "0"
        assert format_number("invalid") == "0"

    def test_format_datetime_range(self):
        """Test format_datetime_range function."""
        start = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 15, 11, 30, 0, tzinfo=timezone.utc)

        # Test normal range
        result = format_datetime_range(start, end)
        assert isinstance(result, str)
        assert "2024-01-15" in result
        assert "10:00" in result
        assert "11:30" in result

        # Test edge cases
        assert format_datetime_range(None, end) == "Invalid start time"
        assert format_datetime_range(start, None) == "Invalid end time"
        assert format_datetime_range(None, None) == "Invalid time range"

    def test_format_task_summary(self):
        """Test format_task_summary function."""
        # Test with minimal data
        summary = format_task_summary(
            task_name="Test Task",
            task_type="skill_creation",
            progress=50.0,
            status="running"
        )
        assert isinstance(summary, str)
        assert "Test Task" in summary
        assert "skill_creation" in summary
        assert "50%" in summary
        assert "Running" in summary

        # Test with all data
        summary = format_task_summary(
            task_name="Test Task",
            task_type="skill_creation",
            progress=75.0,
            status="running",
            current_step="validation",
            total_steps=4,
            estimated_duration=300,
            elapsed_time=150
        )
        assert isinstance(summary, str)
        assert "Test Task" in summary
        assert "75%" in summary
        assert "Validation" in summary

    def test_format_log_summary(self):
        """Test format_log_summary function."""
        # Test with minimal data
        summary = format_log_summary(
            level="INFO",
            message="Test message"
        )
        assert isinstance(summary, str)
        assert "Info" in summary
        assert "Test message" in summary

        # Test with all data
        summary = format_log_summary(
            level="ERROR",
            message="Error occurred",
            source="task_executor",
            task_id="task-001"
        )
        assert isinstance(summary, str)
        assert "Error" in summary
        assert "Error occurred" in summary
        assert "task_executor" in summary
        assert "task-001" in summary


class TestUtilsIntegration:
    """Integration tests for utils functions."""

    def test_validate_and_format_task_id(self):
        """Test validate task_id and then format it."""
        task_id = "task-001"

        # Validate
        result = validate_task_id(task_id)
        assert result.is_valid is True

        # Format (in real usage, might use different formatting)
        formatted = task_id  # Just return as is for this test
        assert formatted == "task-001"

    def test_validate_and_format_progress(self):
        """Test validate progress value and then format it."""
        progress = 50.0

        # Validate
        result = validate_progress_value(progress)
        assert result.is_valid is True

        # Format
        formatted = format_percentage(progress)
        assert formatted == "50%"

    def test_validate_and_format_status(self):
        """Test validate status and then format it."""
        status = "running"

        # Validate
        result = validate_status(status)
        assert result.is_valid is True

        # Format
        formatted = format_status(status)
        assert formatted == "Running"

    def test_validate_and_format_log_level(self):
        """Test validate log level and then format it."""
        level = "ERROR"

        # Validate
        result = validate_log_level(level)
        assert result.is_valid is True

        # Format
        formatted = format_log_level(level)
        assert formatted == "Error"

    def test_validate_metadata_and_serialize(self):
        """Test validate metadata and then serialize it."""
        metadata = {"key": "value", "number": 42}

        # Validate
        result = validate_metadata(metadata)
        assert result.is_valid is True

        # Serialize
        serialized = BaseSerializer.to_json_serializable(metadata)
        assert serialized["key"] == "value"
        assert serialized["number"] == 42

    def test_full_task_validation_flow(self):
        """Test complete task validation flow."""
        task_data = {
            "task_id": "task-001",
            "user_id": "user-001",
            "task_type": "skill_creation",
            "task_name": "Test Task",
            "progress": 50.0,
            "status": "running",
            "estimated_duration": 300,
            "metadata": {"priority": "high"},
            "tags": ["test", "automation"]
        }

        # Validate all fields
        assert validate_task_id(task_data["task_id"]).is_valid is True
        assert validate_user_id(task_data["user_id"]).is_valid is True
        assert validate_progress_value(task_data["progress"]).is_valid is True
        assert validate_status(task_data["status"]).is_valid is True
        assert validate_duration(task_data["estimated_duration"]).is_valid is True
        assert validate_metadata(task_data["metadata"]).is_valid is True
        assert validate_tags(task_data["tags"]).is_valid is True

        # Format for display
        assert format_percentage(task_data["progress"]) == "50%"
        assert format_status(task_data["status"]) == "Running"
        assert format_duration(task_data["estimated_duration"]) == "5m"

    def test_full_log_validation_flow(self):
        """Test complete log validation flow."""
        log_data = {
            "task_id": "task-001",
            "level": "INFO",
            "message": "Task started",
            "source": "task_executor"
        }

        # Validate all fields
        assert validate_task_id(log_data["task_id"]).is_valid is True
        assert validate_log_level(log_data["level"]).is_valid is True

        # Format for display
        assert format_log_level(log_data["level"]) == "Info"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
