"""Data formatters for MinIO storage system.

This module contains formatting functions for displaying file sizes,
timestamps, durations, and other data in human-readable formats.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Union

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Human-readable file size string
    """
    if not isinstance(size_bytes, int) or size_bytes < 0:
        return "0 B"

    size = float(size_bytes)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]

    for unit in units:
        if size < 1024:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size:.2f} EB"


def format_duration(seconds: Union[int, float]) -> str:
    """Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Human-readable duration string
    """
    if not isinstance(seconds, (int, float)) or seconds < 0:
        return "0s"

    seconds = float(seconds)

    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    else:
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        return f"{days}d {hours}h"


def format_timestamp(timestamp: Optional[datetime], include_timezone: bool = True) -> str:
    """Format timestamp in ISO format.

    Args:
        timestamp: datetime object or None
        include_timezone: Whether to include timezone info

    Returns:
        ISO formatted timestamp string
    """
    if timestamp is None:
        return "N/A"

    if not isinstance(timestamp, datetime):
        raise ValueError("Timestamp must be a datetime object")

    if include_timezone and timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp.isoformat() if include_timezone else timestamp.strftime("%Y-%m-%d %H:%M:%S")


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage value.

    Args:
        value: Percentage value (0.0 to 1.0)
        decimals: Number of decimal places

    Returns:
        Percentage string with % symbol
    """
    if not isinstance(value, (int, float)) or value < 0:
        return "0.00%"

    if value > 1:
        value = value / 100

    return f"{value*100:.{decimals}f}%"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating

    Returns:
        Truncated string
    """
    if not isinstance(text, str):
        text = str(text)

    if len(text) <= max_length:
        return text

    if len(suffix) >= max_length:
        return text[:max_length]

    return text[: max_length - len(suffix)] + suffix


def format_list(items: list, max_items: int = 5, separator: str = ", ") -> str:
    """Format list of items as comma-separated string.

    Args:
        items: List of items to format
        max_items: Maximum number of items to display
        separator: Separator between items

    Returns:
        Formatted string
    """
    if not items:
        return ""

    if len(items) <= max_items:
        return separator.join(str(item) for item in items)

    displayed_items = items[:max_items]
    return separator.join(str(item) for item in displayed_items) + f" +{len(items) - max_items} more"


def format_version_number(version_number: int) -> str:
    """Format version number.

    Args:
        version_number: Version number

    Returns:
        Formatted version string
    """
    if not isinstance(version_number, int) or version_number < 1:
        return "v0"

    return f"v{version_number}"


def format_file_type(file_type: str) -> str:
    """Format file type for display.

    Args:
        file_type: File type string

    Returns:
        Formatted file type
    """
    if not file_type:
        return "Unknown"

    file_type = file_type.lower().replace("_", " ").title()
    return file_type


def format_storage_bucket(bucket_name: str) -> str:
    """Format storage bucket name for display.

    Args:
        bucket_name: Bucket name

    Returns:
        Formatted bucket name
    """
    if not bucket_name:
        return "Unknown"

    # Remove prefix if present
    if bucket_name.startswith("skillseekers-"):
        return bucket_name.replace("skillseekers-", "").title()

    return bucket_name.title()


def format_checksum(checksum: str, length: int = 8) -> str:
    """Format checksum for display (first and last characters).

    Args:
        checksum: Full checksum string
        length: Number of characters to show

    Returns:
        Formatted checksum string
    """
    if not checksum or len(checksum) < length:
        return checksum or "N/A"

    prefix_length = length // 2
    suffix_length = length - prefix_length

    return f"{checksum[:prefix_length]}...{checksum[-suffix_length:]}"


def format_speed(bytes_per_second: float) -> str:
    """Format transfer speed.

    Args:
        bytes_per_second: Transfer speed in bytes per second

    Returns:
        Formatted speed string
    """
    if bytes_per_second <= 0:
        return "0 B/s"

    size = float(bytes_per_second)
    units = ["B/s", "KB/s", "MB/s", "GB/s", "TB/s"]

    for unit in units:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024

    return f"{size:.2f} PB/s"


def format_number(number: Union[int, float], precision: int = 2) -> str:
    """Format number with thousands separator.

    Args:
        number: Number to format
        precision: Number of decimal places

    Returns:
        Formatted number string
    """
    if not isinstance(number, (int, float)):
        return "0"

    if isinstance(number, int):
        return f"{number:,}"

    return f"{number:,.{precision}f}"


def format_percentage_of_total(part: Union[int, float], total: Union[int, float]) -> str:
    """Format part as percentage of total.

    Args:
        part: Part value
        total: Total value

    Returns:
        Percentage string
    """
    if total <= 0:
        return "0%"

    percentage = (part / total) * 100
    return f"{percentage:.1f}%"


def format_datetime_ago(timestamp: datetime) -> str:
    """Format datetime as "time ago" string.

    Args:
        timestamp: datetime object

    Returns:
        Time ago string (e.g., "2 hours ago")
    """
    if not isinstance(timestamp, datetime):
        return "Unknown"

    now = datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    diff = now - timestamp

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def format_error_message(error: Exception) -> str:
    """Format error message for display.

    Args:
        error: Exception object

    Returns:
        Formatted error message
    """
    if not error:
        return "Unknown error"

    error_type = type(error).__name__
    error_message = str(error)

    if error_message:
        return f"{error_type}: {error_message}"

    return error_type


def format_quota(used: Union[int, float], quota: Union[int, float]) -> str:
    """Format quota usage.

    Args:
        used: Amount used
        quota: Total quota

    Returns:
        Formatted quota string
    """
    if quota <= 0:
        return "No quota"

    used_formatted = format_file_size(used)
    quota_formatted = format_file_size(quota)
    percentage = format_percentage_of_total(used, quota)

    return f"{used_formatted} / {quota_formatted} ({percentage})"


def format_mime_type(mime_type: str) -> str:
    """Format MIME type for display.

    Args:
        mime_type: MIME type string

    Returns:
        Formatted MIME type
    """
    if not mime_type:
        return "Unknown"

    # Convert to more readable format
    mime_type = mime_type.lower()

    # Common MIME type mappings
    mime_mappings = {
        "text/plain": "Text",
        "text/markdown": "Markdown",
        "application/json": "JSON",
        "application/pdf": "PDF",
        "image/jpeg": "JPEG Image",
        "image/png": "PNG Image",
        "image/gif": "GIF Image",
        "application/zip": "ZIP Archive",
        "text/html": "HTML",
        "text/css": "CSS",
        "application/javascript": "JavaScript",
    }

    if mime_type in mime_mappings:
        return mime_mappings[mime_type]

    # Generic formatting
    parts = mime_type.split("/")
    if len(parts) == 2:
        main_type, sub_type = parts
        return f"{main_type.title()} {sub_type.title()}"

    return mime_type.title()
