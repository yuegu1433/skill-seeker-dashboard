"""File Formatting Utilities.

This module contains formatting functions for file operations,
including file size formatting, timestamp formatting, and display formatting.
"""

import os
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path

from . import FILE_UTILS_CONSTANTS


def format_file_size(size_bytes: Union[int, float], decimal_places: int = 2) -> str:
    """Format file size to human-readable string.

    Args:
        size_bytes: Size in bytes
        decimal_places: Number of decimal places

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes == 0:
        return "0 B"

    size = float(size_bytes)

    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0

    return f"{size:.{decimal_places}f} EB"


def format_duration(seconds: Union[int, float], include_ms: bool = False) -> str:
    """Format duration to human-readable string.

    Args:
        seconds: Duration in seconds
        include_ms: Whether to include milliseconds

    Returns:
        Formatted duration string (e.g., "1h 30m 45s")
    """
    if seconds < 0:
        return "0s"

    seconds = int(seconds)
    ms = int((seconds % 1) * 1000) if include_ms else 0

    # Calculate time units
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []

    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or (days == 0 and hours == 0 and minutes == 0):
        if include_ms and ms > 0:
            parts.append(f"{secs}.{ms:03d}s")
        else:
            parts.append(f"{secs}s")

    return " ".join(parts)


def format_timestamp(timestamp: Optional[Union[datetime, int, float]],
                     format_type: str = "relative") -> str:
    """Format timestamp to human-readable string.

    Args:
        timestamp: Timestamp (datetime object or Unix timestamp)
        format_type: Format type ('relative', 'absolute', 'date', 'time')

    Returns:
        Formatted timestamp string
    """
    if timestamp is None:
        return "Never"

    # Convert to datetime if needed
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)

    now = datetime.now()
    diff = now - timestamp

    if format_type == "relative":
        return format_relative_time(diff)
    elif format_type == "absolute":
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return timestamp.strftime("%Y-%m-%d")
    elif format_type == "time":
        return timestamp.strftime("%H:%M:%S")
    else:
        return str(timestamp)


def format_relative_time(time_diff: timedelta) -> str:
    """Format relative time from timedelta.

    Args:
        time_diff: Time difference

    Returns:
        Relative time string (e.g., "2 hours ago", "in 3 days")
    """
    seconds = int(time_diff.total_seconds())

    if seconds < 0:
        # Future time
        seconds = abs(seconds)
        future = True
    else:
        future = False

    if seconds < 60:
        return "in a few seconds" if future else "a few seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"in {minutes} minute{'s' if minutes != 1 else ''}" if future else f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"in {hours} hour{'s' if hours != 1 else ''}" if future else f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:
        days = seconds // 86400
        return f"in {days} day{'s' if days != 1 else ''}" if future else f"{days} day{'s' if days != 1 else ''} ago"
    elif seconds < 31536000:
        months = seconds // 2592000
        return f"in {months} month{'s' if months != 1 else ''}" if future else f"{months} month{'s' if months != 1 else ''} ago"
    else:
        years = seconds // 31536000
        return f"in {years} year{'s' if years != 1 else ''}" if future else f"{years} year{'s' if years != 1 else ''} ago"


def format_percentage(value: Union[int, float], total: Union[int, float],
                     decimal_places: int = 1) -> str:
    """Format percentage.

    Args:
        value: Current value
        total: Total value
        decimal_places: Number of decimal places

    Returns:
        Formatted percentage string (e.g., "75.5%")
    """
    if total == 0:
        return "0%"

    percentage = (value / total) * 100
    return f"{percentage:.{decimal_places}f}%"


def format_bytes_per_second(bytes_per_sec: Union[int, float],
                           decimal_places: int = 2) -> str:
    """Format bytes per second.

    Args:
        bytes_per_sec: Bytes per second
        decimal_places: Number of decimal places

    Returns:
        Formatted speed string (e.g., "1.5 MB/s")
    """
    if bytes_per_sec == 0:
        return "0 B/s"

    size = float(bytes_per_sec)

    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s', 'TB/s']:
        if size < 1024.0:
            return f"{size:.{decimal_places}f} {unit}"
        size /= 1024.0

    return f"{size:.{decimal_places}f} EB/s"


def format_file_count(count: int, total: Optional[int] = None) -> str:
    """Format file count.

    Args:
        count: Number of files
        total: Total number of files (optional)

    Returns:
        Formatted count string (e.g., "15 files", "15 of 100 files")
    """
    if total is not None:
        return f"{count} of {total} files"
    else:
        return f"{count} file{'s' if count != 1 else ''}"


def format_permissions(permissions: Dict[str, bool]) -> str:
    """Format file permissions.

    Args:
        permissions: Dictionary of permissions

    Returns:
        Formatted permissions string (e.g., "rwxr-xr-x")
    """
    # Unix-style permissions
    result = []

    # Owner permissions
    result.append('r' if permissions.get('read', False) else '-')
    result.append('w' if permissions.get('write', False) else '-')
    result.append('x' if permissions.get('execute', False) else '-')

    # Group permissions
    result.append('r' if permissions.get('group_read', False) else '-')
    result.append('w' if permissions.get('group_write', False) else '-')
    result.append('x' if permissions.get('group_execute', False) else '-')

    # Other permissions
    result.append('r' if permissions.get('other_read', False) else '-')
    result.append('w' if permissions.get('other_write', False) else '-')
    result.append('x' if permissions.get('other_execute', False) else '-')

    return ''.join(result)


def get_human_readable_size(size_bytes: Union[int, float]) -> Dict[str, Any]:
    """Get detailed file size information.

    Args:
        size_bytes: Size in bytes

    Returns:
        Dictionary with size information
    """
    return {
        "bytes": int(size_bytes),
        "size": format_file_size(size_bytes),
        "kb": round(size_bytes / 1024, 2),
        "mb": round(size_bytes / (1024 * 1024), 2),
        "gb": round(size_bytes / (1024 * 1024 * 1024), 2),
        "tb": round(size_bytes / (1024 * 1024 * 1024 * 1024), 2),
    }


def format_file_path(path: str, max_length: int = 50) -> str:
    """Format file path for display.

    Args:
        path: File path
        max_length: Maximum length

    Returns:
        Truncated path with ellipsis if needed
    """
    if len(path) <= max_length:
        return path

    # Truncate from the middle
    half = (max_length - 3) // 2
    return f"{path[:half]}...{path[-half:]}"


def format_file_type(file_type: str) -> str:
    """Format file type for display.

    Args:
        file_type: File type

    Returns:
        Formatted file type string
    """
    type_mapping = {
        "document": "Document",
        "image": "Image",
        "video": "Video",
        "audio": "Audio",
        "code": "Code",
        "archive": "Archive",
        "folder": "Folder",
        "other": "Other",
    }

    return type_mapping.get(file_type, file_type.capitalize())


def format_file_status(status: str) -> str:
    """Format file status for display.

    Args:
        status: File status

    Returns:
        Formatted status string
    """
    status_mapping = {
        "active": "Active",
        "archived": "Archived",
        "deleted": "Deleted",
        "pending": "Pending",
        "processing": "Processing",
        "error": "Error",
    }

    return status_mapping.get(status, status.capitalize())


def format_search_results(results: List[Dict[str, Any]],
                         max_results: int = 10) -> str:
    """Format search results summary.

    Args:
        results: List of search results
        max_results: Maximum results to show

    Returns:
        Formatted search results summary
    """
    if not results:
        return "No results found"

    total = len(results)
    display_count = min(total, max_results)

    if total > max_results:
        return f"Showing {display_count} of {total} results"
    else:
        return f"Showing {total} result{'s' if total != 1 else ''}"


def format_batch_operation(operation_type: str, file_count: int,
                          success_count: int, failed_count: int) -> str:
    """Format batch operation summary.

    Args:
        operation_type: Type of operation
        file_count: Total file count
        success_count: Successful operations count
        failed_count: Failed operations count

    Returns:
        Formatted operation summary
    """
    operation_name = operation_type.capitalize()
    success_rate = format_percentage(success_count, file_count)

    if failed_count == 0:
        return f"{operation_name}: {file_count} files processed successfully ({success_rate})"
    else:
        return f"{operation_name}: {success_count} succeeded, {failed_count} failed ({success_rate})"


def format_version_info(version: str, is_current: bool = False) -> str:
    """Format version information.

    Args:
        version: Version string
        is_current: Whether this is the current version

    Returns:
        Formatted version string
    """
    if is_current:
        return f"{version} (current)"
    return version


def format_metadata(metadata: Dict[str, Any], max_items: int = 5) -> str:
    """Format metadata for display.

    Args:
        metadata: Metadata dictionary
        max_items: Maximum items to show

    Returns:
        Formatted metadata string
    """
    if not metadata:
        return "No metadata"

    items = list(metadata.items())
    display_count = min(len(items), max_items)

    formatted_items = [f"{k}: {v}" for k, v in items[:display_count]]

    if len(items) > max_items:
        formatted_items.append(f"... and {len(items) - max_items} more")

    return ", ".join(formatted_items)


def format_tags(tags: List[str], max_tags: int = 5) -> str:
    """Format tags for display.

    Args:
        tags: List of tags
        max_tags: Maximum tags to show

    Returns:
        Formatted tags string
    """
    if not tags:
        return "No tags"

    display_count = min(len(tags), max_tags)
    display_tags = tags[:display_count]

    if len(tags) > max_tags:
        return ", ".join(display_tags) + f", ... +{len(tags) - max_tags} more"
    else:
        return ", ".join(display_tags)


def format_table(data: List[Dict[str, Any]],
                columns: Optional[List[str]] = None,
                max_rows: int = 10) -> str:
    """Format data as a simple table.

    Args:
        data: List of dictionaries
        columns: Column names to display
        max_rows: Maximum rows to show

    Returns:
        Formatted table string
    """
    if not data:
        return "No data"

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    # Calculate column widths
    widths = {}
    for col in columns:
        widths[col] = max(len(str(col)),
                         max(len(str(row.get(col, ""))) for row in data[:max_rows]))

    # Format header
    header = " | ".join(col.ljust(widths[col]) for col in columns)
    separator = "-+-".join("-" * widths[col] for col in columns)

    # Format rows
    rows = []
    for row in data[:max_rows]:
        row_str = " | ".join(str(row.get(col, "")).ljust(widths[col]) for col in columns)
        rows.append(row_str)

    # Build table
    table = [header, separator]
    table.extend(rows)

    if len(data) > max_rows:
        table.append(f"... and {len(data) - max_rows} more rows")

    return "\n".join(table)


def format_json_pretty(data: Any, indent: int = 2) -> str:
    """Format data as pretty-printed JSON.

    Args:
        data: Data to format
        indent: Indentation size

    Returns:
        Pretty-printed JSON string
    """
    import json

    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)


def format_yaml_pretty(data: Any) -> str:
    """Format data as YAML.

    Args:
        data: Data to format

    Returns:
        YAML string
    """
    try:
        import yaml
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    except ImportError:
        # Fallback to JSON if PyYAML is not available
        return format_json_pretty(data)


def format_csv(data: List[Dict[str, Any]],
              columns: Optional[List[str]] = None) -> str:
    """Format data as CSV.

    Args:
        data: List of dictionaries
        columns: Column names

    Returns:
        CSV string
    """
    if not data:
        return ""

    # Determine columns
    if columns is None:
        columns = list(data[0].keys())

    import csv
    from io import StringIO

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()
