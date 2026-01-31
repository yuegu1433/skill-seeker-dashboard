"""File validators for MinIO storage system.

This module contains validation functions for file operations,
ensuring data integrity and security.
"""

import re
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Constants
ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "text/html",
    "text/css",
    "text/javascript",
    "application/json",
    "application/xml",
    "application/pdf",
    "application/zip",
    "application/gzip",
    "application/x-tar",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
}

ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".html", ".htm", ".css", ".js", ".jsx",
    ".ts", ".tsx", ".json", ".xml", ".csv", ".yml", ".yaml",
    ".pdf", ".doc", ".docx", ".zip", ".tar", ".gz",
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg",
    ".py", ".java", ".cpp", ".c", ".h", ".hpp",
    ".go", ".rs", ".php", ".rb", ".swift", ".kt",
    ".sh", ".bash", ".zsh", ".fish", ".bat", ".cmd",
}

MAX_FILE_SIZE = 104857600  # 100MB
MAX_PATH_LENGTH = 500
MAX_FILENAME_LENGTH = 255
MAX_METADATA_KEYS = 50
MAX_METADATA_VALUE_LENGTH = 1000
MAX_TAGS_COUNT = 20
MAX_TAG_LENGTH = 50


def validate_file_path(file_path: str) -> str:
    """Validate and sanitize file path.

    Args:
        file_path: The file path to validate

    Returns:
        The sanitized file path

    Raises:
        ValueError: If file path is invalid
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError("File path must be a non-empty string")

    # Remove leading/trailing whitespace
    file_path = file_path.strip()

    # Check length
    if len(file_path) > MAX_PATH_LENGTH:
        raise ValueError(f"File path too long (max {MAX_PATH_LENGTH} characters)")

    # Check for dangerous patterns
    if ".." in file_path or file_path.startswith("/") or file_path.startswith("\\"):
        raise ValueError("Invalid file path: contains dangerous patterns")

    # Check for null bytes
    if "\x00" in file_path:
        raise ValueError("Invalid file path: contains null bytes")

    # Normalize path separators
    file_path = file_path.replace("\\", "/")

    # Remove duplicate slashes
    while "//" in file_path:
        file_path = file_path.replace("//", "/")

    # Remove trailing slash except for root
    if len(file_path) > 1 and file_path.endswith("/"):
        file_path = file_path[:-1]

    # Check for valid characters
    if not re.match(r"^[a-zA-Z0-9._\-\/\s]+$", file_path):
        logger.warning(f"File path contains unusual characters: {file_path}")

    logger.debug(f"Validated file path: {file_path}")
    return file_path


def validate_content_type(content_type: str) -> str:
    """Validate content type.

    Args:
        content_type: The content type to validate

    Returns:
        The validated content type

    Raises:
        ValueError: If content type is invalid
    """
    if not content_type or not isinstance(content_type, str):
        raise ValueError("Content type must be a non-empty string")

    content_type = content_type.strip().lower()

    # Check length
    if len(content_type) > 100:
        raise ValueError("Content type too long (max 100 characters)")

    # Check format (basic validation)
    if not re.match(r"^[a-z]+\/[a-z0-9\.\-\+]+$", content_type):
        logger.warning(f"Unusual content type format: {content_type}")

    logger.debug(f"Validated content type: {content_type}")
    return content_type


def validate_file_size(size: int) -> int:
    """Validate file size.

    Args:
        size: The file size in bytes

    Returns:
        The validated file size

    Raises:
        ValueError: If file size is invalid
    """
    if not isinstance(size, int) or size < 0:
        raise ValueError("File size must be a non-negative integer")

    if size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)")

    logger.debug(f"Validated file size: {size} bytes")
    return size


def validate_skill_id(skill_id: str | UUID) -> UUID:
    """Validate skill ID.

    Args:
        skill_id: The skill ID to validate

    Returns:
        The validated UUID

    Raises:
        ValueError: If skill ID is invalid
    """
    if isinstance(skill_id, UUID):
        return skill_id

    if not skill_id or not isinstance(skill_id, str):
        raise ValueError("Skill ID must be a non-empty string or UUID")

    try:
        return UUID(skill_id)
    except ValueError as e:
        raise ValueError(f"Invalid skill ID format: {e}")


def validate_bucket_name(bucket_name: str) -> str:
    """Validate bucket name.

    Args:
        bucket_name: The bucket name to validate

    Returns:
        The validated bucket name

    Raises:
        ValueError: If bucket name is invalid
    """
    if not bucket_name or not isinstance(bucket_name, str):
        raise ValueError("Bucket name must be a non-empty string")

    bucket_name = bucket_name.strip().lower()

    # Check length
    if len(bucket_name) < 3 or len(bucket_name) > 63:
        raise ValueError("Bucket name must be between 3 and 63 characters")

    # Check for valid characters (S3 compatible)
    if not re.match(r"^[a-z0-9][a-z0-9\.\-]*[a-z0-9]$", bucket_name):
        raise ValueError(
            "Bucket name must start and end with lowercase letter or number, "
            "and contain only lowercase letters, numbers, dots, and hyphens"
        )

    # Check for reserved names
    reserved_names = {
        "localhost", "bucket", "buckets", "minio", "console",
        "admin", "root", "public", "private"
    }
    if bucket_name in reserved_names:
        raise ValueError(f"Bucket name '{bucket_name}' is reserved")

    logger.debug(f"Validated bucket name: {bucket_name}")
    return bucket_name


def validate_metadata(metadata: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Validate metadata dictionary.

    Args:
        metadata: The metadata to validate

    Returns:
        The validated metadata dictionary

    Raises:
        ValueError: If metadata is invalid
    """
    if metadata is None:
        return {}

    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be a dictionary")

    if len(metadata) > MAX_METADATA_KEYS:
        raise ValueError(f"Metadata too many keys (max {MAX_METADATA_KEYS})")

    validated_metadata: Dict[str, str] = {}

    for key, value in metadata.items():
        # Validate key
        if not isinstance(key, str) or not key.strip():
            raise ValueError("Metadata keys must be non-empty strings")

        key = key.strip()

        if len(key) > 100:
            raise ValueError(f"Metadata key too long (max 100 characters)")

        # Validate value
        if value is None:
            continue

        if not isinstance(value, str):
            value = str(value)

        if len(value) > MAX_METADATA_VALUE_LENGTH:
            logger.warning(f"Metadata value for key '{key}' truncated")
            value = value[:MAX_METADATA_VALUE_LENGTH]

        # Remove null bytes
        value = value.replace("\x00", "")

        validated_metadata[key] = value

    logger.debug(f"Validated metadata: {validated_metadata}")
    return validated_metadata


def validate_tags(tags: Optional[List[str]]) -> List[str]:
    """Validate tags list.

    Args:
        tags: The tags to validate

    Returns:
        The validated tags list

    Raises:
        ValueError: If tags are invalid
    """
    if tags is None:
        return []

    if not isinstance(tags, list):
        raise ValueError("Tags must be a list")

    if len(tags) > MAX_TAGS_COUNT:
        raise ValueError(f"Too many tags (max {MAX_TAGS_COUNT})")

    validated_tags: List[str] = []

    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            continue

        tag = tag.strip()

        if len(tag) > MAX_TAG_LENGTH:
            raise ValueError(f"Tag too long (max {MAX_TAG_LENGTH} characters)")

        # Remove null bytes and special characters
        tag = tag.replace("\x00", "").replace(",", "")

        if tag and tag not in validated_tags:
            validated_tags.append(tag)

    logger.debug(f"Validated tags: {validated_tags}")
    return validated_tags


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage.

    Args:
        filename: The filename to sanitize

    Returns:
        The sanitized filename
    """
    if not filename:
        return "unnamed_file"

    # Remove path components
    filename = Path(filename).name

    # Remove null bytes and control characters
    filename = "".join(char for char in filename if ord(char) >= 32 or char in "\t\n\r")

    # Replace dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

    # Remove multiple consecutive underscores
    filename = re.sub(r"_{2,}", "_", filename)

    # Remove leading/trailing underscores and dots
    filename = filename.strip("_.")

    # Ensure not empty after sanitization
    if not filename:
        filename = "unnamed_file"

    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        max_name_length = MAX_FILENAME_LENGTH - len(ext) - 1
        filename = f"{name[:max_name_length]}.{ext}" if ext else name[:MAX_FILENAME_LENGTH]

    logger.debug(f"Sanitized filename: {filename}")
    return filename


def validate_file_extension(file_path: str) -> str:
    """Validate file extension.

    Args:
        file_path: The file path to check

    Returns:
        The file extension

    Raises:
        ValueError: If extension is not allowed
    """
    file_path = validate_file_path(file_path)
    extension = Path(file_path).suffix.lower()

    if extension and extension not in ALLOWED_EXTENSIONS:
        logger.warning(f"File extension '{extension}' not in allowed list")

    return extension


def validate_object_name(object_name: str) -> str:
    """Validate MinIO object name.

    Args:
        object_name: The object name to validate

    Returns:
        The validated object name

    Raises:
        ValueError: If object name is invalid
    """
    if not object_name or not isinstance(object_name, str):
        raise ValueError("Object name must be a non-empty string")

    # URL encode spaces and special characters
    object_name = quote(object_name, safe="")

    # Check length (MinIO limit is 1024 characters)
    if len(object_name) > 1024:
        raise ValueError("Object name too long (max 1024 characters)")

    # Check for null bytes
    if "\x00" in object_name:
        raise ValueError("Object name contains null bytes")

    logger.debug(f"Validated object name: {object_name}")
    return object_name


def validate_version_id(version_id: str) -> str:
    """Validate version ID.

    Args:
        version_id: The version ID to validate

    Returns:
        The validated version ID

    Raises:
        ValueError: If version ID is invalid
    """
    if not version_id or not isinstance(version_id, str):
        raise ValueError("Version ID must be a non-empty string")

    version_id = version_id.strip()

    # Check format (alphanumeric, hyphens, underscores, dots)
    if not re.match(r"^[a-zA-Z0-9._\-]+$", version_id):
        raise ValueError("Version ID contains invalid characters")

    # Check length
    if len(version_id) > 50:
        raise ValueError("Version ID too long (max 50 characters)")

    logger.debug(f"Validated version ID: {version_id}")
    return version_id
