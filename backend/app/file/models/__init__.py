"""File Management System Models.

This module contains all data models for the file management system,
including File, FileVersion, FilePermission, and FileBackup models.
"""

from .file import File, FileStatus, FileType
from .file_version import FileVersion, VersionStatus
from .file_permission import FilePermission, PermissionType
from .file_backup import FileBackup, BackupStatus

__all__ = [
    "File",
    "FileStatus",
    "FileType",
    "FileVersion",
    "VersionStatus",
    "FilePermission",
    "PermissionType",
    "FileBackup",
    "BackupStatus",
]

# Model metadata
FILE_MODELS = {
    "File": {
        "description": "Core file entity model",
        "fields": ["id", "name", "path", "size", "mime_type", "type"],
        "relationships": ["versions", "permissions", "backups"],
    },
    "FileVersion": {
        "description": "File version tracking model",
        "fields": ["id", "file_id", "version", "content", "checksum"],
        "relationships": ["file"],
    },
    "FilePermission": {
        "description": "File permission control model",
        "fields": ["id", "file_id", "user_id", "permission_type"],
        "relationships": ["file"],
    },
    "FileBackup": {
        "description": "File backup management model",
        "fields": ["id", "file_id", "backup_path", "size", "status"],
        "relationships": ["file"],
    },
}

# Default file type configurations
DEFAULT_FILE_TYPES = {
    FileType.DOCUMENT: {
        "mime_types": [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
        ],
        "max_size": 50 * 1024 * 1024,  # 50MB
        "preview_support": True,
    },
    FileType.IMAGE: {
        "mime_types": [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        "max_size": 20 * 1024 * 1024,  # 20MB
        "preview_support": True,
    },
    FileType.VIDEO: {
        "mime_types": [
            "video/mp4",
            "video/webm",
            "video/ogg",
        ],
        "max_size": 500 * 1024 * 1024,  # 500MB
        "preview_support": True,
    },
    FileType.AUDIO: {
        "mime_types": [
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "audio/mp4",
        ],
        "max_size": 100 * 1024 * 1024,  # 100MB
        "preview_support": True,
    },
    FileType.CODE: {
        "mime_types": [
            "text/x-python",
            "text/x-java-source",
            "text/javascript",
            "text/css",
            "text/html",
            "text/xml",
            "application/json",
            "application/yaml",
            "application/x-yaml",
        ],
        "max_size": 10 * 1024 * 1024,  # 10MB
        "preview_support": True,
    },
    FileType.ARCHIVE: {
        "mime_types": [
            "application/zip",
            "application/x-rar",
            "application/x-7z-compressed",
            "application/x-tar",
            "application/gzip",
        ],
        "max_size": 1 * 1024 * 1024 * 1024,  # 1GB
        "preview_support": False,
    },
}

# Default permission templates
DEFAULT_PERMISSIONS = {
    "public_read": {
        PermissionType.READ: True,
        PermissionType.WRITE: False,
        PermissionType.DELETE: False,
        PermissionType.SHARE: False,
    },
    "owner_full": {
        PermissionType.READ: True,
        PermissionType.WRITE: True,
        PermissionType.DELETE: True,
        PermissionType.SHARE: True,
    },
    "team_read": {
        PermissionType.READ: True,
        PermissionType.WRITE: False,
        PermissionType.DELETE: False,
        PermissionType.SHARE: False,
    },
}

# Backup retention policies
BACKUP_RETENTION_POLICIES = {
    "daily": {
        "retention_days": 30,
        "frequency": "daily",
        "max_backups": 30,
    },
    "weekly": {
        "retention_days": 90,
        "frequency": "weekly",
        "max_backups": 12,
    },
    "monthly": {
        "retention_days": 365,
        "frequency": "monthly",
        "max_backups": 12,
    },
    "yearly": {
        "retention_days": 2555,  # 7 years
        "frequency": "yearly",
        "max_backups": 7,
    },
}

# Version management settings
VERSION_SETTINGS = {
    "auto_versioning": True,
    "max_versions": 50,
    "version_threshold": 1024,  # bytes
    "compression_enabled": True,
    "diff_storage": True,
}

# File validation rules
FILE_VALIDATION_RULES = {
    "max_file_size": {
        FileType.DOCUMENT: 50 * 1024 * 1024,
        FileType.IMAGE: 20 * 1024 * 1024,
        FileType.VIDEO: 500 * 1024 * 1024,
        FileType.AUDIO: 100 * 1024 * 1024,
        FileType.CODE: 10 * 1024 * 1024,
        FileType.ARCHIVE: 1 * 1024 * 1024 * 1024,
    },
    "allowed_extensions": {
        FileType.DOCUMENT: [".pdf", ".doc", ".docx", ".txt"],
        FileType.IMAGE: [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        FileType.VIDEO: [".mp4", ".webm", ".ogg"],
        FileType.AUDIO: [".mp3", ".wav", ".ogg", ".m4a"],
        FileType.CODE: [".py", ".java", ".js", ".css", ".html", ".xml", ".json", ".yaml", ".yml"],
        FileType.ARCHIVE: [".zip", ".rar", ".7z", ".tar", ".gz"],
    },
    "disallowed_extensions": [".exe", ".bat", ".sh", ".ps1", ".dll", ".so", ".dylib"],
}
