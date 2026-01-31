"""Platform validation utilities.

This module provides validation functions for platform operations,
deployment configurations, and compatibility checks.
"""

import re
import hashlib
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from urllib.parse import urlparse


def validate_platform_name(name: str) -> bool:
    """Validate platform name format.

    Args:
        name: Platform name to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValueError("Platform name must be a non-empty string")

    name = name.strip().lower()

    # Check length
    if len(name) < 1 or len(name) > 50:
        raise ValueError("Platform name must be between 1 and 50 characters")

    # Check allowed characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-z0-9_-]+$', name):
        raise ValueError(
            "Platform name must contain only lowercase letters, numbers, hyphens, and underscores"
        )

    # Check no consecutive hyphens or underscores
    if '--' in name or '__' in name:
        raise ValueError("Platform name cannot contain consecutive hyphens or underscores")

    # Check doesn't start or end with hyphen or underscore
    if name.startswith('-') or name.startswith('_') or name.endswith('-') or name.endswith('_'):
        raise ValueError("Platform name cannot start or end with hyphen or underscore")

    return True


def validate_api_endpoint(endpoint: str) -> bool:
    """Validate API endpoint URL format.

    Args:
        endpoint: API endpoint URL to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If endpoint is invalid
    """
    if not endpoint:
        return True  # Endpoint is optional

    if not isinstance(endpoint, str):
        raise ValueError("API endpoint must be a string")

    try:
        parsed = urlparse(endpoint)

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid URL format")

        # Must be HTTP or HTTPS
        if parsed.scheme not in ['http', 'https']:
            raise ValueError("API endpoint must use HTTP or HTTPS")

        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9._~:/?#[\]@!$&\'()*+,;=%-]+$', endpoint):
            raise ValueError("API endpoint contains invalid characters")

    except Exception as e:
        raise ValueError(f"Invalid API endpoint: {str(e)}")

    return True


def validate_checksum(checksum: str) -> bool:
    """Validate file checksum format (SHA-256).

    Args:
        checksum: Checksum to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If checksum is invalid
    """
    if not checksum:
        return True  # Checksum is optional

    if not isinstance(checksum, str):
        raise ValueError("Checksum must be a string")

    checksum = checksum.strip().lower()

    # Check length (SHA-256 is 64 hex characters)
    if len(checksum) != 64:
        raise ValueError("Checksum must be 64 hexadecimal characters (SHA-256)")

    # Check if all characters are hexadecimal
    if not re.match(r'^[a-f0-9]{64}$', checksum):
        raise ValueError("Checksum must contain only hexadecimal characters")

    return True


def validate_file_size(size: Union[int, float]) -> bool:
    """Validate file size.

    Args:
        size: File size in bytes

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If size is invalid
    """
    if size is None:
        return True  # Size is optional

    if not isinstance(size, (int, float)):
        raise ValueError("File size must be a number")

    if size < 0:
        raise ValueError("File size cannot be negative")

    # Check if size is reasonable (less than 10GB)
    if size > 10 * 1024 * 1024 * 1024:
        raise ValueError("File size cannot exceed 10GB")

    return True


def validate_skill_id(skill_id: str) -> bool:
    """Validate skill identifier format.

    Args:
        skill_id: Skill identifier to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If skill_id is invalid
    """
    if not skill_id or not isinstance(skill_id, str):
        raise ValueError("Skill ID must be a non-empty string")

    skill_id = skill_id.strip()

    # Check length
    if len(skill_id) < 1 or len(skill_id) > 100:
        raise ValueError("Skill ID must be between 1 and 100 characters")

    # Check allowed characters (alphanumeric, hyphens, underscores, dots)
    if not re.match(r'^[a-zA-Z0-9._-]+$', skill_id):
        raise ValueError(
            "Skill ID must contain only letters, numbers, dots, hyphens, and underscores"
        )

    return True


def validate_skill_version(version: str) -> bool:
    """Validate skill version format.

    Args:
        version: Skill version to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If version is invalid
    """
    if not version or not isinstance(version, str):
        raise ValueError("Skill version must be a non-empty string")

    version = version.strip()

    # Check length
    if len(version) > 50:
        raise ValueError("Skill version cannot exceed 50 characters")

    # Check allowed characters (alphanumeric, dots, hyphens, underscores)
    if not re.match(r'^[a-zA-Z0-9._-]+$', version):
        raise ValueError(
            "Skill version must contain only letters, numbers, dots, hyphens, and underscores"
        )

    return True


def validate_platform_config(config: Dict[str, Any]) -> bool:
    """Validate platform configuration dictionary.

    Args:
        config: Platform configuration to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If config is invalid
    """
    if not isinstance(config, dict):
        raise ValueError("Platform configuration must be a dictionary")

    # Check for reserved keys that shouldn't be in config
    reserved_keys = {'id', 'created_at', 'updated_at', 'name'}
    reserved_in_config = set(config.keys()) & reserved_keys
    if reserved_in_config:
        raise ValueError(
            f"Configuration cannot contain reserved keys: {', '.join(reserved_in_config)}"
        )

    # Check for reasonable depth (no deeply nested structures)
    def check_depth(d, current_depth=0, max_depth=5):
        if current_depth > max_depth:
            raise ValueError("Configuration structure too deeply nested")
        if isinstance(d, dict):
            for value in d.values():
                check_depth(value, current_depth + 1, max_depth)
        elif isinstance(d, list):
            for item in d:
                check_depth(item, current_depth + 1, max_depth)

    check_depth(config)

    # Check for reasonable size (config shouldn't be too large)
    import json
    config_size = len(json.dumps(config))
    if config_size > 100 * 1024:  # 100KB
        raise ValueError("Platform configuration cannot exceed 100KB")

    return True


def validate_deployment_config(config: Dict[str, Any]) -> bool:
    """Validate deployment configuration dictionary.

    Args:
        config: Deployment configuration to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If config is invalid
    """
    if not isinstance(config, dict):
        raise ValueError("Deployment configuration must be a dictionary")

    # Check for valid configuration keys
    valid_keys = {
        'timeout', 'retry_count', 'retry_delay', 'parallel_deployments',
        'rollback_on_failure', 'health_check_enabled', 'notification_enabled',
        'custom_params', 'environment', 'region', 'tags'
    }

    invalid_keys = set(config.keys()) - valid_keys
    if invalid_keys:
        # Allow unknown keys but warn (could be custom configuration)
        pass  # Silently allow for flexibility

    # Validate specific values
    if 'timeout' in config:
        timeout = config['timeout']
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("Timeout must be a positive number")

    if 'retry_count' in config:
        retry_count = config['retry_count']
        if not isinstance(retry_count, int) or retry_count < 0 or retry_count > 10:
            raise ValueError("Retry count must be an integer between 0 and 10")

    if 'retry_delay' in config:
        retry_delay = config['retry_delay']
        if not isinstance(retry_delay, (int, float)) or retry_delay < 0:
            raise ValueError("Retry delay must be a non-negative number")

    return True


def validate_platform_list(platforms: List[str]) -> bool:
    """Validate list of platform names.

    Args:
        platforms: List of platform names to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If platforms list is invalid
    """
    if not isinstance(platforms, list):
        raise ValueError("Platforms must be a list")

    if not platforms:
        raise ValueError("Platforms list cannot be empty")

    if len(platforms) > 20:
        raise ValueError("Cannot check more than 20 platforms at once")

    # Check for duplicates
    if len(platforms) != len(set(platforms)):
        raise ValueError("Platforms list cannot contain duplicates")

    # Validate each platform name
    valid_platform_types = {'claude', 'gemini', 'openai', 'markdown'}
    for platform in platforms:
        if platform not in valid_platform_types:
            raise ValueError(f"Invalid platform: {platform}. Must be one of {valid_platform_types}")

    return True


def validate_compatibility_score(score: Union[int, float, str]) -> bool:
    """Validate compatibility score format.

    Args:
        score: Compatibility score to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If score is invalid
    """
    if score is None:
        return True  # Score is optional

    try:
        # Convert to float for validation
        score_float = float(score)
    except (ValueError, TypeError):
        raise ValueError("Compatibility score must be a number")

    if score_float < 0 or score_float > 100:
        raise ValueError("Compatibility score must be between 0 and 100")

    return True


def validate_json_structure(data: Any, max_depth: int = 10, max_size: int = 1024 * 1024) -> bool:
    """Validate JSON data structure.

    Args:
        data: Data to validate
        max_depth: Maximum allowed nesting depth
        max_size: Maximum size in bytes

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If structure is invalid
    """
    import json

    # Check size
    try:
        data_json = json.dumps(data)
        if len(data_json) > max_size:
            raise ValueError(f"Data size cannot exceed {max_size} bytes")
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid JSON structure: {str(e)}")

    # Check depth
    def check_depth(item, current_depth=0):
        if current_depth > max_depth:
            raise ValueError(f"JSON structure too deeply nested (max depth: {max_depth})")
        if isinstance(item, dict):
            for value in item.values():
                check_depth(value, current_depth + 1)
        elif isinstance(item, list):
            for element in item:
                check_depth(element, current_depth + 1)

    check_depth(data)

    return True


def validate_datetime_range(start_time: Optional[datetime], end_time: Optional[datetime]) -> bool:
    """Validate datetime range.

    Args:
        start_time: Start datetime
        end_time: End datetime

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If datetime range is invalid
    """
    if start_time and end_time:
        if start_time >= end_time:
            raise ValueError("Start time must be before end time")

    # Check if datetimes are not too far in the past or future
    now = datetime.utcnow()
    if start_time:
        if start_time < now.replace(year=now.year - 1):
            raise ValueError("Start time cannot be more than 1 year in the past")
        if start_time > now.replace(year=now.year + 1):
            raise ValueError("Start time cannot be more than 1 year in the future")

    if end_time:
        if end_time < now.replace(year=now.year - 1):
            raise ValueError("End time cannot be more than 1 year in the past")
        if end_time > now.replace(year=now.year + 1):
            raise ValueError("End time cannot be more than 1 year in the future")

    return True


def validate_pagination_params(skip: Optional[int], limit: Optional[int]) -> Tuple[int, int]:
    """Validate and normalize pagination parameters.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (validated_skip, validated_limit)

    Raises:
        ValueError: If parameters are invalid
    """
    # Default values
    skip = skip or 0
    limit = limit or 100

    # Validate skip
    if not isinstance(skip, int) or skip < 0:
        raise ValueError("Skip must be a non-negative integer")

    # Validate limit
    if not isinstance(limit, int) or limit < 1 or limit > 1000:
        raise ValueError("Limit must be an integer between 1 and 1000")

    # Check if skip + limit is reasonable (to avoid loading too many records)
    if skip + limit > 10000:
        raise ValueError("Cannot retrieve more than 10,000 records at once")

    return skip, limit


def validate_skill_format(format_name: str) -> bool:
    """Validate skill format name.

    Args:
        format_name: Format name to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If format is invalid
    """
    if not format_name or not isinstance(format_name, str):
        raise ValueError("Format name must be a non-empty string")

    format_name = format_name.strip().lower()

    # Check length
    if len(format_name) < 1 or len(format_name) > 20:
        raise ValueError("Format name must be between 1 and 20 characters")

    # Check allowed characters (alphanumeric, hyphens, underscores)
    if not re.match(r'^[a-z0-9_-]+$', format_name):
        raise ValueError(
            "Format name must contain only lowercase letters, numbers, hyphens, and underscores"
        )

    return True


def validate_retry_config(retry_config: Dict[str, Any]) -> bool:
    """Validate retry configuration.

    Args:
        retry_config: Retry configuration to validate

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If retry_config is invalid
    """
    if not isinstance(retry_config, dict):
        raise ValueError("Retry configuration must be a dictionary")

    # Validate max_retries
    if 'max_retries' in retry_config:
        max_retries = retry_config['max_retries']
        if not isinstance(max_retries, int) or max_retries < 0 or max_retries > 10:
            raise ValueError("max_retries must be an integer between 0 and 10")

    # Validate initial_delay
    if 'initial_delay' in retry_config:
        initial_delay = retry_config['initial_delay']
        if not isinstance(initial_delay, (int, float)) or initial_delay < 0:
            raise ValueError("initial_delay must be a non-negative number")

    # Validate backoff_factor
    if 'backoff_factor' in retry_config:
        backoff_factor = retry_config['backoff_factor']
        if not isinstance(backoff_factor, (int, float)) or backoff_factor < 1:
            raise ValueError("backoff_factor must be a number greater than or equal to 1")

    # Validate max_delay
    if 'max_delay' in retry_config:
        max_delay = retry_config['max_delay']
        if not isinstance(max_delay, (int, float)) or max_delay < 0:
            raise ValueError("max_delay must be a non-negative number")

    # Validate timeout
    if 'timeout' in retry_config:
        timeout = retry_config['timeout']
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            raise ValueError("timeout must be a positive number")

    return True


def validate_health_check_params(timeout: Optional[int], check_depth: Optional[str]) -> Tuple[int, str]:
    """Validate health check parameters.

    Args:
        timeout: Health check timeout in seconds
        check_depth: Health check depth level

    Returns:
        Tuple of (validated_timeout, validated_check_depth)

    Raises:
        ValueError: If parameters are invalid
    """
    # Default values
    timeout = timeout or 30
    check_depth = check_depth or "standard"

    # Validate timeout
    if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
        raise ValueError("Timeout must be an integer between 1 and 300 seconds")

    # Validate check_depth
    valid_depths = {'basic', 'standard', 'comprehensive'}
    if check_depth not in valid_depths:
        raise ValueError(f"Check depth must be one of {valid_depths}")

    return timeout, check_depth