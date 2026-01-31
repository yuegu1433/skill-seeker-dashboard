"""Data validation utilities for progress tracking system.

This module provides validation functions for progress tracking data
including task IDs, user IDs, progress values, status codes, and more.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ValidationResult:
    """Container for validation results."""

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        """Initialize validation result.

        Args:
            is_valid: Whether validation passed
            errors: List of validation errors (if any)
        """
        self.is_valid = is_valid
        self.errors = errors or []

    def __bool__(self) -> bool:
        """Return True if validation passed."""
        return self.is_valid

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ValidationResult(is_valid={self.is_valid}, errors={self.errors})"


# Validation patterns
TASK_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
METRIC_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Status constants
VALID_STATUSES = [
    "pending",
    "running",
    "completed",
    "failed",
    "paused",
    "cancelled",
]

VALID_LOG_LEVELS = [
    "DEBUG",
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
]

VALID_NOTIFICATION_TYPES = [
    "info",
    "success",
    "warning",
    "error",
    "progress",
]

VALID_PRIORITIES = [
    "low",
    "normal",
    "high",
    "urgent",
]

VALID_TASK_TYPES = [
    "skill_creation",
    "skill_deployment",
    "file_processing",
    "data_analysis",
    "model_training",
    "backup",
    "cleanup",
    "custom",
]


def validate_task_id(task_id: str) -> ValidationResult:
    """Validate task ID format.

    Args:
        task_id: Task ID to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not task_id:
        errors.append("Task ID is required")
    elif len(task_id) > 100:
        errors.append("Task ID must be less than 100 characters")
    elif not TASK_ID_PATTERN.match(task_id):
        errors.append("Task ID must contain only alphanumeric characters, hyphens, and underscores")

    return ValidationResult(len(errors) == 0, errors)


def validate_user_id(user_id: str) -> ValidationResult:
    """Validate user ID format.

    Args:
        user_id: User ID to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not user_id:
        errors.append("User ID is required")
    elif len(user_id) > 100:
        errors.append("User ID must be less than 100 characters")
    elif not USER_ID_PATTERN.match(user_id):
        errors.append("User ID must contain only alphanumeric characters, hyphens, and underscores")

    return ValidationResult(len(errors) == 0, errors)


def validate_progress_value(progress: Union[int, float]) -> ValidationResult:
    """Validate progress percentage value.

    Args:
        progress: Progress value to validate

    Returns:
        ValidationResult
    """
    errors = []

    try:
        progress_float = float(progress)
    except (ValueError, TypeError):
        errors.append("Progress must be a number")
        return ValidationResult(False, errors)

    if progress_float < 0.0:
        errors.append("Progress cannot be negative")
    elif progress_float > 100.0:
        errors.append("Progress cannot exceed 100.0")

    return ValidationResult(len(errors) == 0, errors)


def validate_status(status: str) -> ValidationResult:
    """Validate task status.

    Args:
        status: Status to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not status:
        errors.append("Status is required")
    elif status not in VALID_STATUSES:
        errors.append(f"Invalid status '{status}'. Valid statuses: {', '.join(VALID_STATUSES)}")

    return ValidationResult(len(errors) == 0, errors)


def validate_log_level(level: str) -> ValidationResult:
    """Validate log level.

    Args:
        level: Log level to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not level:
        errors.append("Log level is required")
    elif level not in VALID_LOG_LEVELS:
        errors.append(f"Invalid log level '{level}'. Valid levels: {', '.join(VALID_LOG_LEVELS)}")

    return ValidationResult(len(errors) == 0, errors)


def validate_notification_type(notification_type: str) -> ValidationResult:
    """Validate notification type.

    Args:
        notification_type: Notification type to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not notification_type:
        errors.append("Notification type is required")
    elif notification_type not in VALID_NOTIFICATION_TYPES:
        errors.append(f"Invalid notification type '{notification_type}'. Valid types: {', '.join(VALID_NOTIFICATION_TYPES)}")

    return ValidationResult(len(errors) == 0, errors)


def validate_metric_name(metric_name: str) -> ValidationResult:
    """Validate metric name format.

    Args:
        metric_name: Metric name to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not metric_name:
        errors.append("Metric name is required")
    elif len(metric_name) > 100:
        errors.append("Metric name must be less than 100 characters")
    elif not METRIC_NAME_PATTERN.match(metric_name):
        errors.append("Metric name must contain only alphanumeric characters, hyphens, and underscores")

    return ValidationResult(len(errors) == 0, errors)


def validate_task_metadata(metadata: Optional[Dict[str, Any]]) -> ValidationResult:
    """Validate task metadata.

    Args:
        metadata: Metadata to validate

    Returns:
        ValidationResult
    """
    errors = []

    if metadata is None:
        return ValidationResult(True)

    if not isinstance(metadata, dict):
        errors.append("Metadata must be a dictionary")
        return ValidationResult(False, errors)

    # Check for overly large metadata
    try:
        metadata_str = str(metadata)
        if len(metadata_str) > 10000:  # 10KB limit
            errors.append("Metadata is too large (max 10KB)")
    except Exception:
        errors.append("Metadata is not serializable")

    # Check for nested depth
    def check_depth(obj: Any, depth: int = 0) -> bool:
        if depth > 5:  # Max 5 levels deep
            return False
        if isinstance(obj, dict):
            return all(check_depth(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return all(check_depth(item, depth + 1) for item in obj)
        return True

    if not check_depth(metadata):
        errors.append("Metadata has too many nested levels (max 5)")

    return ValidationResult(len(errors) == 0, errors)


def validate_duration(duration: Optional[int]) -> ValidationResult:
    """Validate duration in seconds.

    Args:
        duration: Duration to validate

    Returns:
        ValidationResult
    """
    errors = []

    if duration is None:
        return ValidationResult(True)

    try:
        duration_int = int(duration)
    except (ValueError, TypeError):
        errors.append("Duration must be an integer")
        return ValidationResult(False, errors)

    if duration_int < 0:
        errors.append("Duration cannot be negative")
    elif duration_int > 86400 * 365:  # Max 1 year
        errors.append("Duration is too large (max 1 year)")

    return ValidationResult(len(errors) == 0, errors)


def validate_timestamp(timestamp: Optional[Union[str, datetime]]) -> ValidationResult:
    """Validate timestamp.

    Args:
        timestamp: Timestamp to validate

    Returns:
        ValidationResult
    """
    errors = []

    if timestamp is None:
        return ValidationResult(True)

    try:
        if isinstance(timestamp, str):
            # Try to parse as ISO format
            dt = datetime.fromisoformat(timestamp)
        elif isinstance(timestamp, datetime):
            dt = timestamp
        else:
            errors.append("Timestamp must be a string or datetime object")
            return ValidationResult(False, errors)

        # Check if timestamp is in the future (allow some tolerance)
        now = datetime.now(timezone.utc)
        if dt > now:
            errors.append("Timestamp cannot be in the future")

        # Check if timestamp is too old (allow up to 1 year)
        min_timestamp = now.replace(year=now.year - 1)
        if dt < min_timestamp:
            errors.append("Timestamp is too old")

    except ValueError as e:
        errors.append(f"Invalid timestamp format: {e}")
    except Exception as e:
        errors.append(f"Timestamp validation failed: {e}")

    return ValidationResult(len(errors) == 0, errors)


def validate_priority(priority: str) -> ValidationResult:
    """Validate priority level.

    Args:
        priority: Priority to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not priority:
        errors.append("Priority is required")
    elif priority not in VALID_PRIORITIES:
        errors.append(f"Invalid priority '{priority}'. Valid priorities: {', '.join(VALID_PRIORITIES)}")

    return ValidationResult(len(errors) == 0, errors)


def validate_task_type(task_type: str) -> ValidationResult:
    """Validate task type.

    Args:
        task_type: Task type to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not task_type:
        errors.append("Task type is required")
    elif task_type not in VALID_TASK_TYPES:
        errors.append(f"Invalid task type '{task_type}'. Valid types: {', '.join(VALID_TASK_TYPES)}")

    return ValidationResult(len(errors) == 0, errors)


def validate_email(email: str) -> ValidationResult:
    """Validate email address format.

    Args:
        email: Email to validate

    Returns:
        ValidationResult
    """
    errors = []
    email_pattern = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if not email:
        errors.append("Email is required")
    elif len(email) > 254:  # RFC 5321 limit
        errors.append("Email is too long")
    elif not email_pattern.match(email):
        errors.append("Invalid email format")

    return ValidationResult(len(errors) == 0, errors)


def validate_url(url: str) -> ValidationResult:
    """Validate URL format.

    Args:
        url: URL to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not url:
        errors.append("URL is required")
    elif len(url) > 2048:  # Common URL length limit
        errors.append("URL is too long")
    elif not (url.startswith("http://") or url.startswith("https://")):
        errors.append("URL must start with http:// or https://")

    return ValidationResult(len(errors) == 0, errors)


def validate_uuid(uuid_str: str) -> ValidationResult:
    """Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        ValidationResult
    """
    errors = []

    if not uuid_str:
        errors.append("UUID is required")
    else:
        try:
            from uuid import UUID
            UUID(uuid_str)
        except ValueError:
            errors.append("Invalid UUID format")

    return ValidationResult(len(errors) == 0, errors)


def validate_tags(tags: Optional[List[str]]) -> ValidationResult:
    """Validate list of tags.

    Args:
        tags: Tags to validate

    Returns:
        ValidationResult
    """
    errors = []

    if tags is None:
        return ValidationResult(True)

    if not isinstance(tags, list):
        errors.append("Tags must be a list")
        return ValidationResult(False, errors)

    if len(tags) > 20:  # Max 20 tags
        errors.append("Too many tags (max 20)")
    elif len(tags) == 0:
        errors.append("At least one tag is required")

    for i, tag in enumerate(tags):
        if not isinstance(tag, str):
            errors.append(f"Tag at index {i} must be a string")
        elif len(tag) > 50:
            errors.append(f"Tag at index {i} is too long (max 50 characters)")
        elif not tag.strip():
            errors.append(f"Tag at index {i} cannot be empty")

    return ValidationResult(len(errors) == 0, errors)


def validate_labels(labels: Optional[Dict[str, str]]) -> ValidationResult:
    """Validate dictionary of labels.

    Args:
        labels: Labels to validate

    Returns:
        ValidationResult
    """
    errors = []

    if labels is None:
        return ValidationResult(True)

    if not isinstance(labels, dict):
        errors.append("Labels must be a dictionary")
        return ValidationResult(False, errors)

    if len(labels) > 20:  # Max 20 labels
        errors.append("Too many labels (max 20)")

    for key, value in labels.items():
        if not isinstance(key, str):
            errors.append(f"Label key must be a string")
        elif len(key) > 50:
            errors.append(f"Label key '{key}' is too long (max 50 characters)")
        elif not isinstance(value, str):
            errors.append(f"Label value for key '{key}' must be a string")
        elif len(value) > 100:
            errors.append(f"Label value for key '{key}' is too long (max 100 characters)")

    return ValidationResult(len(errors) == 0, errors)


def validate_batch_size(size: int, max_size: int = 1000) -> ValidationResult:
    """Validate batch size.

    Args:
        size: Batch size to validate
        max_size: Maximum allowed size

    Returns:
        ValidationResult
    """
    errors = []

    try:
        size_int = int(size)
    except (ValueError, TypeError):
        errors.append("Batch size must be an integer")
        return ValidationResult(False, errors)

    if size_int < 1:
        errors.append("Batch size must be at least 1")
    elif size_int > max_size:
        errors.append(f"Batch size cannot exceed {max_size}")

    return ValidationResult(len(errors) == 0, errors)


def validate_date_range(
    date_from: Optional[datetime],
    date_to: Optional[datetime]
) -> ValidationResult:
    """Validate date range.

    Args:
        date_from: Start date
        date_to: End date

    Returns:
        ValidationResult
    """
    errors = []

    if date_from and date_to and date_from > date_to:
        errors.append("Start date cannot be after end date")

    return ValidationResult(len(errors) == 0, errors)


def validate_file_size(size: int) -> ValidationResult:
    """Validate file size in bytes.

    Args:
        size: File size to validate

    Returns:
        ValidationResult
    """
    errors = []

    try:
        size_int = int(size)
    except (ValueError, TypeError):
        errors.append("File size must be an integer")
        return ValidationResult(False, errors)

    if size_int < 0:
        errors.append("File size cannot be negative")
    elif size_int > 100 * 1024 * 1024:  # 100MB limit
        errors.append("File size cannot exceed 100MB")

    return ValidationResult(len(errors) == 0, errors)
