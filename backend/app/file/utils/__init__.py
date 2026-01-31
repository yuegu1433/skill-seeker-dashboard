"""File Management System Utils.

This module contains utility functions for the file management system,
including validators, formatters, processors, and helpers.
"""

from .validators import (
    FileValidator,
    ContentValidator,
    BusinessRuleValidator,
    validate_file_name,
    validate_file_size,
    validate_file_type,
    validate_mime_type,
    validate_file_permissions,
    validate_storage_path,
    is_safe_filename,
    is_valid_file_extension,
)
from .formatters import (
    format_file_size,
    format_duration,
    format_timestamp,
    format_percentage,
    format_bytes_per_second,
    format_file_count,
    format_permissions,
    get_human_readable_size,
    format_file_path,
    format_file_type,
)
from .processors import (
    FileProcessor,
    ContentProcessor,
    MetadataProcessor,
    ThumbnailProcessor,
    HashProcessor,
    CompressProcessor,
    process_file_content,
    extract_metadata,
    generate_thumbnail,
    calculate_checksum,
    compress_data,
    decompress_data,
)

__all__ = [
    # Validators
    "FileValidator",
    "ContentValidator",
    "BusinessRuleValidator",
    "validate_file_name",
    "validate_file_size",
    "validate_file_type",
    "validate_mime_type",
    "validate_file_permissions",
    "validate_storage_path",
    "is_safe_filename",
    "is_valid_file_extension",
    # Formatters
    "format_file_size",
    "format_duration",
    "format_timestamp",
    "format_percentage",
    "format_bytes_per_second",
    "format_file_count",
    "format_permissions",
    "get_human_readable_size",
    "format_file_path",
    "format_file_type",
    # Processors
    "FileProcessor",
    "ContentProcessor",
    "MetadataProcessor",
    "ThumbnailProcessor",
    "HashProcessor",
    "CompressProcessor",
    "process_file_content",
    "extract_metadata",
    "generate_thumbnail",
    "calculate_checksum",
    "compress_data",
    "decompress_data",
]

# Utility constants
FILE_UTILS_CONSTANTS = {
    "MAX_FILE_NAME_LENGTH": 255,
    "MAX_FILE_PATH_LENGTH": 500,
    "MAX_FILE_SIZE": 1024 * 1024 * 1024,  # 1GB
    "MIN_FILE_SIZE": 0,
    "ALLOWED_FILE_TYPES": {
        "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf"],
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"],
        "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"],
        "audio": [".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"],
        "code": [".py", ".java", ".js", ".ts", ".css", ".html", ".xml", ".json", ".yaml", ".yml"],
        "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    },
    "DISALLOWED_FILE_NAMES": [
        "CON", "PRN", "AUX", "NUL",
        "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ],
    "INVALID_CHARACTERS": ['<', '>', ':', '"', '|', '?', '*', '\\', '/'],
    "MAX_METADATA_SIZE": 10000,  # bytes
    "MAX_TAGS_PER_FILE": 20,
    "MAX_TAG_LENGTH": 50,
}

# Hash algorithms
HASH_ALGORITHMS = {
    "md5": "MD5",
    "sha1": "SHA-1",
    "sha256": "SHA-256",
    "sha512": "SHA-512",
}

# Compression algorithms
COMPRESSION_ALGORITHMS = {
    "gzip": "GZIP",
    "bz2": "BZ2",
    "lzma": "LZMA",
    "zip": "ZIP",
}

# MIME type mappings
MIME_TYPE_MAP = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
    ".mp4": "video/mp4",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".zip": "application/zip",
    ".json": "application/json",
    ".xml": "application/xml",
    ".yaml": "application/x-yaml",
    ".yml": "application/x-yaml",
    ".py": "text/x-python",
    ".js": "text/javascript",
    ".ts": "text/typescript",
    ".html": "text/html",
    ".css": "text/css",
}

# File type icons
FILE_TYPE_ICONS = {
    "document": "📄",
    "image": "🖼️",
    "video": "🎬",
    "audio": "🎵",
    "code": "💻",
    "archive": "🗜️",
    "folder": "📁",
    "other": "📎",
}

# Status colors
STATUS_COLORS = {
    "active": "green",
    "archived": "gray",
    "deleted": "red",
    "pending": "yellow",
    "processing": "blue",
    "error": "red",
}

# Utility functions
def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return filename.lower().split('.')[-1] if '.' in filename else ''


def get_file_type_from_extension(extension: str) -> str:
    """Get file type from extension."""
    extension = extension.lower().lstrip('.')
    for file_type, extensions in FILE_UTILS_CONSTANTS["ALLOWED_FILE_TYPES"].items():
        if extension in [ext.lstrip('.') for ext in extensions]:
            return file_type
    return "other"


def get_mime_type_from_extension(extension: str) -> str:
    """Get MIME type from file extension."""
    extension = extension.lower()
    return MIME_TYPE_MAP.get(extension, "application/octet-stream")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    import re

    # Remove invalid characters
    for char in FILE_UTILS_CONSTANTS["INVALID_CHARACTERS"]:
        filename = filename.replace(char, '_')

    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')

    # Replace multiple underscores with single underscore
    filename = re.sub(r'_+', '_', filename)

    # Limit length
    if len(filename) > FILE_UTILS_CONSTANTS["MAX_FILE_NAME_LENGTH"]:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = FILE_UTILS_CONSTANTS["MAX_FILE_NAME_LENGTH"] - len(ext) - 1
        filename = name[:max_name_length] + ('.' + ext if ext else '')

    return filename


def is_valid_filename(filename: str) -> bool:
    """Check if filename is valid."""
    if not filename or len(filename) == 0:
        return False

    if len(filename) > FILE_UTILS_CONSTANTS["MAX_FILE_NAME_LENGTH"]:
        return False

    # Check for invalid characters
    for char in filename:
        if char in FILE_UTILS_CONSTANTS["INVALID_CHARACTERS"]:
            return False

    # Check for reserved names (Windows)
    name_without_ext = filename.split('.')[0].upper()
    if name_without_ext in FILE_UTILS_CONSTANTS["DISALLOWED_FILE_NAMES"]:
        return False

    return True


def calculate_storage_path(file_id: str, filename: str, bucket: str = "files") -> str:
    """Calculate storage path for file."""
    import uuid
    from datetime import datetime

    # Create directory structure based on date and file ID
    date_str = datetime.now().strftime("%Y/%m/%d")
    file_uuid = str(uuid.UUID(file_id))

    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    # Construct path
    path = f"{bucket}/{date_str}/{file_uuid}/{safe_filename}"

    # Ensure path length is within limits
    if len(path) > FILE_UTILS_CONSTANTS["MAX_FILE_PATH_LENGTH"]:
        name, ext = safe_filename.rsplit('.', 1) if '.' in safe_filename else (safe_filename, '')
        max_name_length = FILE_UTILS_CONSTANTS["MAX_FILE_PATH_LENGTH"] - len(f"{bucket}/{date_str}/{file_uuid}/") - len(ext) - 1
        safe_filename = name[:max_name_length] + ('.' + ext if ext else '')

    return f"{bucket}/{date_str}/{file_uuid}/{safe_filename}"


def get_file_type_icon(file_type: str) -> str:
    """Get icon for file type."""
    return FILE_TYPE_ICONS.get(file_type, FILE_TYPE_ICONS["other"])


def get_status_color(status: str) -> str:
    """Get color for status."""
    return STATUS_COLORS.get(status, "gray")


def format_operation_summary(operation_type: str, count: int, success: int, failed: int) -> Dict[str, Any]:
    """Format operation summary."""
    return {
        "operation": operation_type,
        "total": count,
        "successful": success,
        "failed": failed,
        "success_rate": round((success / count * 100) if count > 0 else 0, 2),
        "status": "completed" if failed == 0 else "completed_with_errors",
    }


# Initialize logging
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
