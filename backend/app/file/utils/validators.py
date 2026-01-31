"""File Validation Utilities.

This module contains validation functions for file operations,
including file validation, content validation, and business rule validation.
"""

import re
import os
import mimetypes
from typing import Optional, List, Dict, Any, Tuple, Union
from datetime import datetime
from pathlib import Path
from enum import Enum

from . import FILE_UTILS_CONSTANTS, HASH_ALGORITHMS, MIME_TYPE_MAP


class ValidationError(Exception):
    """Custom validation error."""
    pass


class FileValidator:
    """Validator for file operations."""

    def __init__(self):
        """Initialize file validator."""
        self.max_name_length = FILE_UTILS_CONSTANTS["MAX_FILE_NAME_LENGTH"]
        self.max_path_length = FILE_UTILS_CONSTANTS["MAX_FILE_PATH_LENGTH"]
        self.max_file_size = FILE_UTILS_CONSTANTS["MAX_FILE_SIZE"]
        self.min_file_size = FILE_UTILS_CONSTANTS["MIN_FILE_SIZE"]
        self.allowed_file_types = FILE_UTILS_CONSTANTS["ALLOWED_FILE_TYPES"]
        self.disallowed_names = FILE_UTILS_CONSTANTS["DISALLOWED_FILE_NAMES"]
        self.invalid_chars = FILE_UTILS_CONSTANTS["INVALID_CHARACTERS"]
        self.max_metadata_size = FILE_UTILS_CONSTANTS["MAX_METADATA_SIZE"]
        self.max_tags = FILE_UTILS_CONSTANTS["MAX_TAGS_PER_FILE"]
        self.max_tag_length = FILE_UTILS_CONSTANTS["MAX_TAG_LENGTH"]

    def validate_file_name(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate file name."""
        if not filename or len(filename.strip()) == 0:
            return False, "File name cannot be empty"

        if len(filename) > self.max_name_length:
            return False, f"File name cannot exceed {self.max_name_length} characters"

        # Check for invalid characters
        for char in filename:
            if char in self.invalid_chars:
                return False, f"Invalid character '{char}' in file name"

        # Check for reserved names
        name_without_ext = filename.split('.')[0].upper()
        if name_without_ext in self.disallowed_names:
            return False, f"File name '{filename}' is reserved"

        # Check for leading/trailing spaces or dots
        if filename.startswith('.') or filename.startswith(' ') or filename.endswith(' '):
            return False, "File name cannot start or end with spaces or dots"

        # Check for double extensions
        parts = filename.split('.')
        if len(parts) > 2:
            return False, "File name cannot have multiple extensions"

        return True, None

    def validate_file_size(self, size: int) -> Tuple[bool, Optional[str]]:
        """Validate file size."""
        if not isinstance(size, int):
            return False, "File size must be an integer"

        if size < self.min_file_size:
            return False, f"File size cannot be less than {self.min_file_size} bytes"

        if size > self.max_file_size:
            return False, f"File size cannot exceed {self.max_file_size} bytes"

        return True, None

    def validate_file_type(self, filename: str, mime_type: str = None) -> Tuple[bool, Optional[str]]:
        """Validate file type."""
        # Get file extension
        extension = self._get_extension(filename)
        if not extension:
            return False, "File must have an extension"

        # Check if extension is allowed
        if not self._is_allowed_extension(extension):
            return False, f"File type '.{extension}' is not allowed"

        # Validate MIME type if provided
        if mime_type:
            valid_mime, mime_error = self.validate_mime_type(mime_type)
            if not valid_mime:
                return False, mime_error

        return True, None

    def validate_mime_type(self, mime_type: str) -> Tuple[bool, Optional[str]]:
        """Validate MIME type."""
        if not mime_type or len(mime_type.strip()) == 0:
            return False, "MIME type cannot be empty"

        if len(mime_type) > 100:
            return False, "MIME type cannot exceed 100 characters"

        # Basic MIME type format validation
        if not re.match(r'^[a-zA-Z0-9]+\/[a-zA-Z0-9\-\.+]+$', mime_type):
            return False, "Invalid MIME type format"

        return True, None

    def validate_storage_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """Validate storage path."""
        if not path or len(path.strip()) == 0:
            return False, "Storage path cannot be empty"

        if len(path) > self.max_path_length:
            return False, f"Storage path cannot exceed {self.max_path_length} characters"

        # Check for absolute paths
        if os.path.isabs(path):
            return False, "Storage path must be relative"

        # Check for path traversal
        if '..' in path or path.startswith('/'):
            return False, "Invalid path traversal detected"

        # Check for invalid characters
        for char in path:
            if char in self.invalid_chars:
                return False, f"Invalid character '{char}' in storage path"

        return True, None

    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate file metadata."""
        if metadata is None:
            return True, None

        if not isinstance(metadata, dict):
            return False, "Metadata must be a dictionary"

        # Check metadata size
        try:
            import json
            metadata_str = json.dumps(metadata)
            if len(metadata_str) > self.max_metadata_size:
                return False, f"Metadata size cannot exceed {self.max_metadata_size} bytes"
        except (TypeError, ValueError) as e:
            return False, f"Invalid metadata format: {str(e)}"

        # Validate metadata values
        for key, value in metadata.items():
            if not isinstance(key, str):
                return False, "Metadata keys must be strings"

            if len(key) > 100:
                return False, "Metadata key cannot exceed 100 characters"

            if not self._is_valid_metadata_value(value):
                return False, f"Invalid metadata value for key '{key}'"

        return True, None

    def validate_tags(self, tags: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate file tags."""
        if tags is None:
            return True, None

        if not isinstance(tags, list):
            return False, "Tags must be a list"

        if len(tags) > self.max_tags:
            return False, f"Cannot have more than {self.max_tags} tags"

        seen_tags = set()
        for tag in tags:
            if not isinstance(tag, str):
                return False, "All tags must be strings"

            if len(tag) > self.max_tag_length:
                return False, f"Tag '{tag}' cannot exceed {self.max_tag_length} characters"

            if tag in seen_tags:
                return False, f"Duplicate tag '{tag}'"

            seen_tags.add(tag)

        return True, None

    def validate_file_content(self, content: bytes, mime_type: str) -> Tuple[bool, Optional[str]]:
        """Validate file content."""
        if content is None:
            return True, None

        if not isinstance(content, bytes):
            return False, "Content must be bytes"

        # Check content size
        size_valid, size_error = self.validate_file_size(len(content))
        if not size_valid:
            return False, size_error

        # Check for empty content
        if len(content) == 0:
            return False, "File content cannot be empty"

        # Check for valid text content
        if mime_type.startswith('text/'):
            try:
                content.decode('utf-8')
            except UnicodeDecodeError:
                return False, "Invalid text content encoding"

        return True, None

    def _get_extension(self, filename: str) -> str:
        """Get file extension."""
        return filename.lower().split('.')[-1] if '.' in filename else ''

    def _is_allowed_extension(self, extension: str) -> bool:
        """Check if extension is allowed."""
        extension = extension.lower().lstrip('.')
        for extensions in self.allowed_file_types.values():
            if extension in [ext.lstrip('.') for ext in extensions]:
                return True
        return False

    def _is_valid_metadata_value(self, value: Any) -> bool:
        """Check if metadata value is valid."""
        if value is None:
            return True

        if isinstance(value, (str, int, float, bool)):
            return True

        if isinstance(value, list):
            return all(isinstance(item, (str, int, float, bool)) for item in value)

        if isinstance(value, dict):
            return all(isinstance(k, str) and self._is_valid_metadata_value(v) for k, v in value.items())

        return False


class ContentValidator:
    """Validator for file content."""

    def __init__(self):
        """Initialize content validator."""
        self.text_encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'ascii']
        self.max_text_size = 10 * 1024 * 1024  # 10MB

    def validate_text_content(self, content: bytes, encoding: str = 'utf-8') -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate text content and return decoded text."""
        if not isinstance(content, bytes):
            return False, "Content must be bytes", None

        if len(content) > self.max_text_size:
            return False, f"Text content cannot exceed {self.max_text_size} bytes", None

        # Try to decode content
        try:
            decoded_text = content.decode(encoding)
            return True, None, decoded_text
        except UnicodeDecodeError:
            # Try alternative encodings
            for alt_encoding in self.text_encodings:
                if alt_encoding != encoding:
                    try:
                        decoded_text = content.decode(alt_encoding)
                        return True, f"Content decoded with {alt_encoding} encoding", decoded_text
                    except UnicodeDecodeError:
                        continue

            return False, "Unable to decode text content with any supported encoding", None

    def validate_binary_content(self, content: bytes, mime_type: str) -> Tuple[bool, Optional[str]]:
        """Validate binary content."""
        if not isinstance(content, bytes):
            return False, "Content must be bytes"

        if len(content) == 0:
            return False, "Binary content cannot be empty"

        # Check for valid binary signatures
        if mime_type.startswith('image/'):
            return self._validate_image_content(content)

        elif mime_type.startswith('video/'):
            return self._validate_video_content(content)

        elif mime_type.startswith('audio/'):
            return self._validate_audio_content(content)

        elif mime_type == 'application/pdf':
            return self._validate_pdf_content(content)

        elif mime_type == 'application/zip':
            return self._validate_zip_content(content)

        return True, None

    def _validate_image_content(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate image content."""
        # Check for common image signatures
        image_signatures = {
            b'\xff\xd8\xff': 'JPEG',
            b'\x89PNG\r\n\x1a\n': 'PNG',
            b'GIF87a': 'GIF87a',
            b'GIF89a': 'GIF89a',
            b'RIFF': 'WebP/AVI',
        }

        for signature, img_type in image_signatures.items():
            if content.startswith(signature):
                return True, None

        return False, "Invalid image file signature"

    def _validate_video_content(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate video content."""
        # Check for common video signatures
        video_signatures = {
            b'\x00\x00\x00\x20ftypmp4': 'MP4',
            b'\x00\x00\x00\x18ftypmp4': 'MP4',
            b'RIFF': 'AVI',
            b'OggS': 'Ogg',
        }

        for signature, video_type in video_signatures.items():
            if content.startswith(signature):
                return True, None

        return False, "Invalid video file signature"

    def _validate_audio_content(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate audio content."""
        # Check for common audio signatures
        audio_signatures = {
            b'ID3': 'MP3',
            b'RIFF': 'WAV',
            b'OggS': 'Ogg',
            b'fLaC': 'FLAC',
        }

        for signature, audio_type in audio_signatures.items():
            if content.startswith(signature):
                return True, None

        return False, "Invalid audio file signature"

    def _validate_pdf_content(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate PDF content."""
        if content.startswith(b'%PDF'):
            return True, None
        return False, "Invalid PDF file signature"

    def _validate_zip_content(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate ZIP content."""
        if content.startswith(b'PK'):
            return True, None
        return False, "Invalid ZIP file signature"


class BusinessRuleValidator:
    """Validator for business rules."""

    def __init__(self):
        """Initialize business rule validator."""
        self.max_files_per_user = 10000
        self.max_storage_per_user = 1024 * 1024 * 1024 * 10  # 10GB
        self.max_versions_per_file = 50
        self.max_backup_size = 1024 * 1024 * 1024 * 5  # 5GB

    def validate_user_file_limit(self, current_file_count: int) -> Tuple[bool, Optional[str]]:
        """Validate user file count limit."""
        if current_file_count >= self.max_files_per_user:
            return False, f"User file limit reached ({self.max_files_per_user} files)"

        return True, None

    def validate_user_storage_limit(self, current_storage: int, additional_size: int = 0) -> Tuple[bool, Optional[str]]:
        """Validate user storage limit."""
        total_storage = current_storage + additional_size
        if total_storage > self.max_storage_per_user:
            return False, f"User storage limit exceeded ({self.max_storage_per_user} bytes)"

        return True, None

    def validate_version_limit(self, current_version_count: int) -> Tuple[bool, Optional[str]]:
        """Validate file version limit."""
        if current_version_count >= self.max_versions_per_file:
            return False, f"File version limit reached ({self.max_versions_per_file} versions)"

        return True, None

    def validate_backup_size(self, backup_size: int) -> Tuple[bool, Optional[str]]:
        """Validate backup size."""
        if backup_size > self.max_backup_size:
            return False, f"Backup size cannot exceed {self.max_backup_size} bytes"

        return True, None

    def validate_file_ownership(self, file_owner_id: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """Validate file ownership."""
        if file_owner_id != user_id:
            return False, "User does not own this file"

        return True, None

    def validate_file_status(self, file_status: str, allowed_statuses: List[str]) -> Tuple[bool, Optional[str]]:
        """Validate file status."""
        if file_status not in allowed_statuses:
            return False, f"File status '{file_status}' not allowed"

        return True, None


# Convenience functions
def validate_file_name(filename: str) -> bool:
    """Convenience function to validate file name."""
    validator = FileValidator()
    is_valid, _ = validator.validate_file_name(filename)
    return is_valid


def validate_file_size(size: int) -> bool:
    """Convenience function to validate file size."""
    validator = FileValidator()
    is_valid, _ = validator.validate_file_size(size)
    return is_valid


def validate_file_type(filename: str, mime_type: str = None) -> bool:
    """Convenience function to validate file type."""
    validator = FileValidator()
    is_valid, _ = validator.validate_file_type(filename, mime_type)
    return is_valid


def validate_mime_type(mime_type: str) -> bool:
    """Convenience function to validate MIME type."""
    validator = FileValidator()
    is_valid, _ = validator.validate_mime_type(mime_type)
    return is_valid


def validate_file_permissions(user_id: str, file_owner_id: str, operation: str) -> bool:
    """Convenience function to validate file permissions."""
    validator = BusinessRuleValidator()
    is_valid, _ = validator.validate_file_ownership(file_owner_id, user_id)
    return is_valid


def validate_storage_path(path: str) -> bool:
    """Convenience function to validate storage path."""
    validator = FileValidator()
    is_valid, _ = validator.validate_storage_path(path)
    return is_valid


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe."""
    return validate_file_name(filename)


def is_valid_file_extension(extension: str) -> bool:
    """Check if file extension is valid."""
    validator = FileValidator()
    return validator._is_allowed_extension(extension)
