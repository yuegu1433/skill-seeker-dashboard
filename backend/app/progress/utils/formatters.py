"""Data formatting utilities for progress tracking system.

This module provides formatting functions for displaying progress tracking
data in a human-readable format including durations, percentages,
timestamps, and more.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def format_duration(seconds: Union[int, float, None]) -> str:
    """Format duration in seconds to human-readable string.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string

    Examples:
        >>> format_duration(3661)
        '1h 1m 1s'
        >>> format_duration(65)
        '1m 5s'
        >>> format_duration(5)
        '5s'
        >>> format_duration(None)
        'N/A'
    """
    if seconds is None:
        return "N/A"

    try:
        seconds = int(seconds)
    except (ValueError, TypeError):
        return "Invalid"

    if seconds < 0:
        return "Invalid"

    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes < 60:
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    if remaining_minutes == 0 and remaining_seconds == 0:
        return f"{hours}h"

    result = f"{hours}h"

    if remaining_minutes > 0:
        result += f" {remaining_minutes}m"

    if remaining_seconds > 0:
        result += f" {remaining_seconds}s"

    return result


def format_percentage(value: Union[int, float, None], precision: int = 1) -> str:
    """Format percentage with specified precision.

    Args:
        value: Percentage value
        precision: Decimal places

    Returns:
        Formatted percentage string

    Examples:
        >>> format_percentage(75.5)
        '75.5%'
        >>> format_percentage(100)
        '100%'
        >>> format_percentage(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return "Invalid"

    if value_float < 0:
        value_float = 0
    elif value_float > 100:
        value_float = 100

    return f"{value_float:.{precision}f}%"


def format_timestamp(timestamp: Optional[datetime], include_time: bool = True) -> str:
    """Format timestamp to human-readable string.

    Args:
        timestamp: Timestamp to format
        include_time: Whether to include time

    Returns:
        Formatted timestamp string

    Examples:
        >>> format_timestamp(datetime(2024, 1, 15, 14, 30, 0))
        '2024-01-15 14:30:00'
        >>> format_timestamp(datetime(2024, 1, 15, 14, 30, 0), False)
        '2024-01-15'
    """
    if timestamp is None:
        return "N/A"

    if not isinstance(timestamp, datetime):
        return "Invalid"

    if include_time:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return timestamp.strftime("%Y-%m-%d")


def format_file_size(size_bytes: Union[int, float, None]) -> str:
    """Format file size in bytes to human-readable string.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted file size string

    Examples:
        >>> format_file_size(1024)
        '1.0 KB'
        >>> format_file_size(1048576)
        '1.0 MB'
        >>> format_file_size(1073741824)
        '1.0 GB'
        >>> format_file_size(None)
        'N/A'
    """
    if size_bytes is None:
        return "N/A"

    try:
        size_bytes = float(size_bytes)
    except (ValueError, TypeError):
        return "Invalid"

    if size_bytes < 0:
        return "Invalid"

    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    unit_index = 0

    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size_bytes)} B"

    return f"{size_bytes:.1f} {units[unit_index]}"


def format_speed(value: Union[int, float, None], unit: str = "ops") -> str:
    """Format speed/rate value.

    Args:
        value: Speed value
        unit: Unit (e.g., 'ops', 'req/s', 'MB/s')

    Returns:
        Formatted speed string

    Examples:
        >>> format_speed(1500, 'ops')
        '1.5K ops/s'
        >>> format_speed(2500000, 'req/s')
        '2.5M req/s'
        >>> format_speed(95.5, 'MB/s')
        '95.5 MB/s'
    """
    if value is None:
        return f"N/A {unit}/s"

    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return f"Invalid {unit}/s"

    if value_float < 0:
        return f"Invalid {unit}/s"

    # Format large numbers with K, M, B suffixes
    if value_float >= 1_000_000_000:
        return f"{value_float / 1_000_000_000:.1f}B {unit}/s"
    elif value_float >= 1_000_000:
        return f"{value_float / 1_000_000:.1f}M {unit}/s"
    elif value_float >= 1_000:
        return f"{value_float / 1_000:.1f}K {unit}/s"
    else:
        return f"{value_float:.1f} {unit}/s"


def format_progress_bar(
    progress: Union[int, float],
    width: int = 20,
    show_percentage: bool = True
) -> str:
    """Format progress as a visual progress bar.

    Args:
        progress: Progress percentage (0-100)
        width: Width of progress bar in characters
        show_percentage: Whether to show percentage

    Returns:
        Formatted progress bar string

    Examples:
        >>> format_progress_bar(50, 10)
        '█████░░░░ 50%'
        >>> format_progress_bar(75, 15, False)
        '███████░░░░░░░░░'
    """
    try:
        progress_float = float(progress)
    except (ValueError, TypeError):
        return "Invalid progress bar"

    if progress_float < 0:
        progress_float = 0
    elif progress_float > 100:
        progress_float = 100

    filled_width = int((progress_float / 100) * width)
    bar = "█" * filled_width + "░" * (width - filled_width)

    if show_percentage:
        return f"{bar} {format_percentage(progress_float, 0)}"

    return bar


def format_status_badge(status: str) -> str:
    """Format status as a colored badge.

    Args:
        status: Status to format

    Returns:
        Formatted status badge

    Examples:
        >>> format_status_badge('completed')
        '✅ Completed'
        >>> format_status_badge('running')
        '🔄 Running'
        >>> format_status_badge('failed')
        '❌ Failed'
    """
    status_icons = {
        "pending": "⏳",
        "running": "🔄",
        "completed": "✅",
        "failed": "❌",
        "paused": "⏸️",
        "cancelled": "🚫",
    }

    icon = status_icons.get(status.lower(), "📋")
    return f"{icon} {status.title()}"


def format_priority_badge(priority: str) -> str:
    """Format priority as a colored badge.

    Args:
        priority: Priority to format

    Returns:
        Formatted priority badge

    Examples:
        >>> format_priority_badge('high')
        '🔴 High'
        >>> format_priority_badge('normal')
        '🟡 Normal'
        >>> format_priority_badge('low')
        '🟢 Low'
    """
    priority_colors = {
        "urgent": "🔴",
        "high": "🟠",
        "normal": "🟡",
        "low": "🟢",
    }

    color = priority_colors.get(priority.lower(), "⚪")
    return f"{color} {priority.title()}"


def format_log_level(level: str) -> str:
    """Format log level with color indicator.

    Args:
        level: Log level

    Returns:
        Formatted log level

    Examples:
        >>> format_log_level('ERROR')
        '🔴 ERROR'
        >>> format_log_level('INFO')
        '🔵 INFO'
        >>> format_log_level('DEBUG')
        '⚪ DEBUG'
    """
    level_colors = {
        "DEBUG": "⚪",
        "INFO": "🔵",
        "WARNING": "🟡",
        "ERROR": "🔴",
        "CRITICAL": "🟣",
    }

    color = level_colors.get(level.upper(), "⚫")
    return f"{color} {level.upper()}"


def format_notification_title(title: str, max_length: int = 50) -> str:
    """Format notification title with truncation.

    Args:
        title: Notification title
        max_length: Maximum length

    Returns:
        Formatted title

    Examples:
        >>> format_notification_title('This is a long notification title')
        'This is a long notification title...'
        >>> format_notification_title('Short title')
        'Short title'
    """
    if len(title) <= max_length:
        return title

    return title[:max_length - 3] + "..."



def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating

    Returns:
        Truncated text

    Examples:
        >>> truncate_text('This is a very long text that needs truncation')
        'This is a very long text that needs truncation'
        >>> truncate_text('This is a very long text that needs truncation', 20)
        'This is a very lon...'
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix


def format_error_message(error: Union[str, Exception, None]) -> str:
    """Format error message for display.

    Args:
        error: Error to format

    Returns:
        Formatted error message

    Examples:
        >>> format_error_message('Connection failed')
        'Connection failed'
        >>> format_error_message(ValueError('Invalid input'))
        'Invalid input'
        >>> format_error_message(None)
        'Unknown error'
    """
    if error is None:
        return "Unknown error"

    if isinstance(error, Exception):
        return str(error)

    return str(error)


def format_summary(
    items: List[str],
    max_items: int = 5,
    separator: str = ", ",
    suffix: str = "..."
) -> str:
    """Format list of items as a summary.

    Args:
        items: List of items
        max_items: Maximum items to show
        separator: Separator between items
        suffix: Suffix when truncating

    Returns:
        Formatted summary

    Examples:
        >>> format_summary(['item1', 'item2', 'item3', 'item4', 'item5', 'item6'])
        'item1, item2, item3, item4, item5...'
        >>> format_summary(['single'])
        'single'
    """
    if not items:
        return ""

    if len(items) <= max_items:
        return separator.join(items)

    truncated = items[:max_items]
    return separator.join(truncated) + suffix


def format_relative_time(timestamp: Optional[datetime]) -> str:
    """Format timestamp as relative time (e.g., '2 hours ago').

    Args:
        timestamp: Timestamp to format

    Returns:
        Formatted relative time

    Examples:
        >>> from datetime import datetime, timedelta
        >>> now = datetime.now()
        >>> past = now - timedelta(hours=2)
        >>> format_relative_time(past)
        '2 hours ago'
        >>> format_relative_time(None)
        'Unknown'
    """
    if timestamp is None:
        return "Unknown"

    if not isinstance(timestamp, datetime):
        return "Invalid"

    now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
    delta = now - timestamp

    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"

    if delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"

    if delta.days > 0:
        return f"{delta.days} day{'s' if delta.days != 1 else ''} ago"

    seconds = delta.seconds

    if seconds > 3600:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"

    if seconds > 60:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"

    if seconds > 0:
        return f"{seconds} second{'s' if seconds != 1 else ''} ago"

    return "just now"


def format_byte_rate(bytes_per_second: Union[int, float, None]) -> str:
    """Format byte rate to human-readable string.

    Args:
        bytes_per_second: Bytes per second

    Returns:
        Formatted byte rate

    Examples:
        >>> format_byte_rate(1024)
        '1.0 KB/s'
        >>> format_byte_rate(1048576)
        '1.0 MB/s'
        >>> format_byte_rate(None)
        'N/A'
    """
    if bytes_per_second is None:
        return "N/A"

    return format_file_size(bytes_per_second) + "/s"


def format_number(value: Union[int, float, None], precision: int = 2) -> str:
    """Format number with thousand separators.

    Args:
        value: Number to format
        precision: Decimal places

    Returns:
        Formatted number

    Examples:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.567)
        '1,234.57'
        >>> format_number(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    try:
        value_float = float(value)
    except (ValueError, TypeError):
        return "Invalid"

    if value_float.is_integer():
        return f"{int(value_float):,}"

    return f"{value_float:,.{precision}f}"


def format_latency(milliseconds: Union[int, float, None]) -> str:
    """Format latency in milliseconds.

    Args:
        milliseconds: Latency in milliseconds

    Returns:
        Formatted latency

    Examples:
        >>> format_latency(1500)
        '1.5s'
        >>> format_latency(500)
        '500ms'
        >>> format_latency(None)
        'N/A'
    """
    if milliseconds is None:
        return "N/A"

    try:
        ms = float(milliseconds)
    except (ValueError, TypeError):
        return "Invalid"

    if ms < 1000:
        return f"{ms:.0f}ms"

    seconds = ms / 1000
    return f"{seconds:.1f}s"


def format_throughput(items_per_second: Union[int, float, None]) -> str:
    """Format throughput as items per second.

    Args:
        items_per_second: Items per second

    Returns:
        Formatted throughput

    Examples:
        >>> format_throughput(1500)
        '1.5K/s'
        >>> format_throughput(2500000)
        '2.5M/s'
        >>> format_throughput(None)
        'N/A'
    """
    if items_per_second is None:
        return "N/A"

    return format_speed(items_per_second, "ops")
