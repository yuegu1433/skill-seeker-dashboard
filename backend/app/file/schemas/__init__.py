"""File Management System Schemas.

This module contains all Pydantic schemas for the file management system,
including file operations, editor configuration, batch operations, etc.
"""

from .file_operations import (
    FileCreate,
    FileUpdate,
    FileResponse,
    FileListResponse,
    FileSearch,
    FileSearchResult,
    FileFilter,
    FileBulkOperation,
    FileBulkResult,
    FileDelete,
    FileRestore,
    FileMove,
    FileCopy,
    FilePermissionGrant,
    FilePermissionRevoke,
    FilePermissionResponse,
)
from .editor_config import (
    EditorSettings,
    EditorTheme,
    EditorMode,
    EditorConfig,
    EditorSession,
    EditorSessionResponse,
    AutoSaveSettings,
    SyntaxHighlightSettings,
    EditorPlugin,
    EditorKeyboardShortcut,
)
from .batch_config import (
    BatchOperationConfig,
    BatchUploadConfig,
    BatchDownloadConfig,
    BatchDeleteConfig,
    BatchMoveConfig,
    BatchCopyConfig,
    BatchProcessResult,
    BatchProgress,
    BatchOperationStatus,
    BatchFileItem,
)

__all__ = [
    # File operation schemas
    "FileCreate",
    "FileUpdate",
    "FileResponse",
    "FileListResponse",
    "FileSearch",
    "FileSearchResult",
    "FileFilter",
    "FileBulkOperation",
    "FileBulkResult",
    "FileDelete",
    "FileRestore",
    "FileMove",
    "FileCopy",
    "FilePermissionGrant",
    "FilePermissionRevoke",
    "FilePermissionResponse",
    # Editor configuration schemas
    "EditorSettings",
    "EditorTheme",
    "EditorMode",
    "EditorConfig",
    "EditorSession",
    "EditorSessionResponse",
    "AutoSaveSettings",
    "SyntaxHighlightSettings",
    "EditorPlugin",
    "EditorKeyboardShortcut",
    # Batch operation schemas
    "BatchOperationConfig",
    "BatchUploadConfig",
    "BatchDownloadConfig",
    "BatchDeleteConfig",
    "BatchMoveConfig",
    "BatchCopyConfig",
    "BatchProcessResult",
    "BatchProgress",
    "BatchOperationStatus",
    "BatchFileItem",
]

# Schema metadata
SCHEMA_METADATA = {
    "file_operations": {
        "description": "File CRUD operation schemas",
        "version": "1.0.0",
        "schemas": [
            "FileCreate",
            "FileUpdate",
            "FileResponse",
            "FileListResponse",
            "FileSearch",
            "FileSearchResult",
            "FileFilter",
            "FileBulkOperation",
            "FileBulkResult",
            "FileDelete",
            "FileRestore",
            "FileMove",
            "FileCopy",
            "FilePermissionGrant",
            "FilePermissionRevoke",
            "FilePermissionResponse",
        ],
    },
    "editor_config": {
        "description": "Online editor configuration schemas",
        "version": "1.0.0",
        "schemas": [
            "EditorSettings",
            "EditorTheme",
            "EditorMode",
            "EditorConfig",
            "EditorSession",
            "EditorSessionResponse",
            "AutoSaveSettings",
            "SyntaxHighlightSettings",
            "EditorPlugin",
            "EditorKeyboardShortcut",
        ],
    },
    "batch_config": {
        "description": "Batch operation configuration schemas",
        "version": "1.0.0",
        "schemas": [
            "BatchOperationConfig",
            "BatchUploadConfig",
            "BatchDownloadConfig",
            "BatchDeleteConfig",
            "BatchMoveConfig",
            "BatchCopyConfig",
            "BatchProcessResult",
            "BatchProgress",
            "BatchOperationStatus",
            "BatchFileItem",
        ],
    },
}

# Validation constants
VALIDATION_CONSTANTS = {
    "max_file_name_length": 255,
    "max_file_path_length": 500,
    "max_description_length": 1000,
    "max_tags_count": 20,
    "max_metadata_size": 10000,  # bytes
    "max_batch_size": 1000,
    "max_editor_sessions": 50,
    "default_page_size": 20,
    "max_page_size": 100,
    "default_auto_save_interval": 30,  # seconds
    "max_auto_save_interval": 300,  # seconds
}

# Supported file types
SUPPORTED_FILE_TYPES = {
    "document": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf"],
    "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"],
    "video": [".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm", ".mkv"],
    "audio": [".mp3", ".wav", ".ogg", ".aac", ".flac", ".m4a"],
    "code": [".py", ".java", ".js", ".ts", ".css", ".html", ".xml", ".json", ".yaml", ".yml", ".go", ".rs", ".cpp", ".c", ".h"],
    "archive": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "other": [],
}

# Default editor settings
DEFAULT_EDITOR_SETTINGS = {
    "theme": "light",
    "font_size": 14,
    "tab_size": 4,
    "auto_save": True,
    "auto_save_interval": 30,
    "word_wrap": True,
    "line_numbers": True,
    "syntax_highlight": True,
    "indent_guides": True,
    "code_folding": True,
    "vim_mode": False,
    "emmet": True,
}

# Default batch operation settings
DEFAULT_BATCH_SETTINGS = {
    "max_concurrent_operations": 10,
    "chunk_size": 100,
    "retry_attempts": 3,
    "retry_delay": 1,  # seconds
    "timeout": 300,  # seconds
}

# Export helper functions
def get_file_type_from_extension(extension: str) -> str:
    """Get file type from extension."""
    extension = extension.lower()
    for file_type, extensions in SUPPORTED_FILE_TYPES.items():
        if extension in extensions:
            return file_type
    return "other"


def validate_file_extension(extension: str) -> bool:
    """Validate file extension."""
    extension = extension.lower()
    for extensions in SUPPORTED_FILE_TYPES.values():
        if extension in extensions:
            return True
    return False


def get_max_file_size(file_type: str) -> int:
    """Get maximum file size for file type."""
    size_limits = {
        "document": 50 * 1024 * 1024,  # 50MB
        "image": 20 * 1024 * 1024,      # 20MB
        "video": 500 * 1024 * 1024,     # 500MB
        "audio": 100 * 1024 * 1024,     # 100MB
        "code": 10 * 1024 * 1024,       # 10MB
        "archive": 1024 * 1024 * 1024,  # 1GB
        "other": 50 * 1024 * 1024,      # 50MB
    }
    return size_limits.get(file_type, 50 * 1024 * 1024)
