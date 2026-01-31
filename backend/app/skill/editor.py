"""Skill Online Editor.

This module provides a comprehensive online editor for skill files,
including syntax highlighting, auto-save, real-time preview,
and concurrent editing support.
"""

import asyncio
import json
import yaml
import hashlib
import aiofiles
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import logging

from .utils import SkillFormatter, SkillValidator
from .event_manager import SkillEventManager, EventType
from .manager import SkillManager


logger = logging.getLogger(__name__)


class EditorMode(Enum):
    """Editor modes for different file types."""
    YAML = "yaml"
    JSON = "json"
    MARKDOWN = "markdown"
    PYTHON = "python"
    TEXT = "text"


class SaveStatus(Enum):
    """Save status enumeration."""
    CLEAN = "clean"
    DIRTY = "dirty"
    SAVING = "saving"
    ERROR = "error"


class LockStatus(Enum):
    """File lock status."""
    UNLOCKED = "unlocked"
    LOCKED = "locked"
    READONLY = "readonly"


@dataclass
class EditorFile:
    """Represents an open file in the editor."""

    file_id: str
    file_path: str
    content: str
    original_content: str
    mode: EditorMode
    language: str
    is_modified: bool = False
    last_modified: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)
    cursor_position: Tuple[int, int] = (0, 0)
    selection: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    bookmarks: Set[int] = field(default_factory=set)
    version: int = 1

    def __post_init__(self):
        """Initialize editor file after creation."""
        self._change_hash = self._calculate_change_hash()

    def _calculate_change_hash(self) -> str:
        """Calculate hash of current content."""
        return hashlib.sha256(self.content.encode()).hexdigest()

    def is_dirty(self) -> bool:
        """Check if file has unsaved changes."""
        return self._change_hash != self._calculate_change_hash()

    def mark_saved(self):
        """Mark file as saved and update original content."""
        self.original_content = self.content
        self._change_hash = self._calculate_change_hash()
        self.is_modified = False
        self.last_modified = datetime.now()

    def mark_modified(self):
        """Mark file as modified."""
        self.is_modified = True
        self.last_modified = datetime.now()


@dataclass
class EditorSession:
    """Represents an editing session."""

    session_id: str
    user_id: str
    files: Dict[str, EditorFile] = field(default_factory=dict)
    active_file_id: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)

    def add_file(self, file: EditorFile):
        """Add file to session."""
        self.files[file.file_id] = file
        if self.active_file_id is None:
            self.active_file_id = file.file_id

    def remove_file(self, file_id: str):
        """Remove file from session."""
        if file_id in self.files:
            del self.files[file_id]
            if self.active_file_id == file_id:
                self.active_file_id = next(iter(self.files.keys()), None)

    def get_active_file(self) -> Optional[EditorFile]:
        """Get currently active file."""
        if self.active_file_id:
            return self.files.get(self.active_file_id)
        return None

    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.now()


class SkillEditor:
    """Online skill editor with comprehensive editing features."""

    # Supported file extensions and their modes
    FILE_MODES = {
        ".yaml": EditorMode.YAML,
        ".json": EditorMode.JSON,
        ".md": EditorMode.MARKDOWN,
        ".py": EditorMode.PYTHON,
        ".txt": EditorMode.TEXT,
    }

    # Default editor settings
    DEFAULT_SETTINGS = {
        "auto_save_interval": 30,  # seconds
        "syntax_highlighting": True,
        "line_numbers": True,
        "auto_indent": True,
        "tab_size": 4,
        "word_wrap": True,
        "show_whitespace": False,
        "theme": "default",
        "font_size": 12,
        "auto_close_brackets": True,
        "auto_close_quotes": True,
        "vim_mode": False,
        "live_preview": True,
        "spell_check": False,
    }

    def __init__(
        self,
        skill_manager: SkillManager,
        event_manager: SkillEventManager,
        workspace_path: Path,
    ):
        """Initialize skill editor.

        Args:
            skill_manager: Skill manager instance
            event_manager: Event manager instance
            workspace_path: Workspace directory path
        """
        self.skill_manager = skill_manager
        self.event_manager = event_manager
        self.workspace_path = workspace_path

        # Active sessions
        self.sessions: Dict[str, EditorSession] = {}
        self._lock = asyncio.Lock()

        # File locks for concurrent editing
        self.file_locks: Dict[str, Dict[str, LockStatus]] = {}

        # Auto-save tasks
        self.auto_save_tasks: Dict[str, asyncio.Task] = {}

        # Callbacks
        self.on_file_changed: Optional[Callable] = None
        self.on_file_saved: Optional[Callable] = None
        self.on_preview_update: Optional[Callable] = None

    async def create_session(
        self,
        user_id: str,
        settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new editing session.

        Args:
            user_id: User identifier
            settings: Editor settings

        Returns:
            Session ID
        """
        session_id = f"session_{datetime.now().timestamp()}_{user_id}"

        merged_settings = self.DEFAULT_SETTINGS.copy()
        if settings:
            merged_settings.update(settings)

        session = EditorSession(
            session_id=session_id,
            user_id=user_id,
            settings=merged_settings,
        )

        self.sessions[session_id] = session

        # Publish event
        await self.event_manager.publish_event(
            EventType.EDITOR_SESSION_CREATED,
            session_id=session_id,
            user_id=user_id,
        )

        return session_id

    async def close_session(self, session_id: str) -> bool:
        """Close an editing session.

        Args:
            session_id: Session ID to close

        Returns:
            True if session was closed successfully
        """
        async with self._lock:
            if session_id not in self.sessions:
                return False

            session = self.sessions[session_id]

            # Save all unsaved files
            for file_id, file in list(session.files.items()):
                if file.is_modified:
                    await self.save_file(session_id, file_id)

            # Cancel auto-save tasks
            if session_id in self.auto_save_tasks:
                self.auto_save_tasks[session_id].cancel()
                del self.auto_save_tasks[session_id]

            # Remove session
            del self.sessions[session_id]

            # Publish event
            await self.event_manager.publish_event(
                EventType.EDITOR_SESSION_CLOSED,
                session_id=session_id,
                user_id=session.user_id,
            )

            return True

    def get_session(self, session_id: str) -> Optional[EditorSession]:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Editor session or None
        """
        return self.sessions.get(session_id)

    def _detect_mode(self, file_path: str) -> EditorMode:
        """Detect editor mode from file extension.

        Args:
            file_path: File path

        Returns:
            Editor mode
        """
        extension = Path(file_path).suffix.lower()
        return self.FILE_MODES.get(extension, EditorMode.TEXT)

    async def open_file(
        self,
        session_id: str,
        file_path: str,
        skill_id: Optional[str] = None,
    ) -> Optional[EditorFile]:
        """Open a file in the editor.

        Args:
            session_id: Session ID
            file_path: File path to open
            skill_id: Associated skill ID

        Returns:
            Editor file instance or None
        """
        session = self.get_session(session_id)
        if not session:
            logger.error(f"Session not found: {session_id}")
            return None

        # Check if file is already open
        file_id = self._generate_file_id(file_path)
        if file_id in session.files:
            session.active_file_id = file_id
            return session.files[file_id]

        try:
            # Check file lock
            lock_status = self._get_file_lock(file_path)
            if lock_status == LockStatus.READONLY:
                logger.warning(f"File is read-only: {file_path}")
                return None

            # Read file content
            full_path = self.workspace_path / file_path
            if not full_path.exists():
                logger.error(f"File not found: {full_path}")
                return None

            async with aiofiles.open(full_path, "r", encoding="utf-8") as f:
                content = await f.read()

            # Detect mode
            mode = self._detect_mode(file_path)

            # Create editor file
            editor_file = EditorFile(
                file_id=file_id,
                file_path=file_path,
                content=content,
                original_content=content,
                mode=mode,
                language=mode.value,
            )

            # Add to session
            session.add_file(editor_file)

            # Lock file if needed
            if lock_status == LockStatus.UNLOCKED:
                self._lock_file(file_path, session.user_id)

            # Publish event
            await self.event_manager.publish_event(
                EventType.EDITOR_FILE_OPENED,
                session_id=session_id,
                file_path=file_path,
                skill_id=skill_id,
                user_id=session.user_id,
            )

            return editor_file

        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            return None

    async def close_file(
        self,
        session_id: str,
        file_id: str,
    ) -> bool:
        """Close a file in the editor.

        Args:
            session_id: Session ID
            file_id: File ID to close

        Returns:
            True if file was closed successfully
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return False

        file = session.files[file_id]

        # Check for unsaved changes
        if file.is_modified:
            # Could prompt user to save here
            logger.warning(f"Closing file with unsaved changes: {file.file_path}")

        # Unlock file
        self._unlock_file(file.file_path, session.user_id)

        # Remove from session
        session.remove_file(file_id)

        # Publish event
        await self.event_manager.publish_event(
            EventType.EDITOR_FILE_CLOSED,
            session_id=session_id,
            file_path=file.file_path,
            user_id=session.user_id,
        )

        return True

    async def save_file(
        self,
        session_id: str,
        file_id: str,
    ) -> bool:
        """Save file to disk.

        Args:
            session_id: Session ID
            file_id: File ID to save

        Returns:
            True if saved successfully
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return False

        file = session.files[file_id]
        session.update_activity()

        try:
            # Validate content before saving
            if file.mode == EditorMode.YAML or file.mode == EditorMode.JSON:
                is_valid, errors = await self._validate_content(file.content, file.mode)
                if not is_valid:
                    logger.error(f"Validation errors: {errors}")
                    return False

            # Write to disk
            full_path = self.workspace_path / file.file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(full_path, "w", encoding="utf-8") as f:
                await f.write(file.content)

            # Mark as saved
            file.mark_saved()

            # Publish event
            await self.event_manager.publish_event(
                EventType.EDITOR_FILE_SAVED,
                session_id=session_id,
                file_path=file.file_path,
                user_id=session.user_id,
            )

            # Trigger callback
            if self.on_file_saved:
                await self.on_file_saved(session_id, file)

            return True

        except Exception as e:
            logger.error(f"Error saving file {file.file_path}: {e}")
            return False

    async def update_content(
        self,
        session_id: str,
        file_id: str,
        content: str,
        cursor_position: Optional[Tuple[int, int]] = None,
    ) -> bool:
        """Update file content.

        Args:
            session_id: Session ID
            file_id: File ID to update
            new content
            cursor_position: Current cursor position

        Returns:
            True if updated successfully
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return False

        file = session.files[file_id]
        session.update_activity()

        # Check file lock
        lock_status = self._get_file_lock(file.file_path)
        if lock_status == LockStatus.READONLY:
            logger.warning(f"Cannot update read-only file: {file.file_path}")
            return False

        # Update content
        file.content = content
        file.mark_modified()

        # Update cursor position
        if cursor_position:
            file.cursor_position = cursor_position

        # Trigger auto-save if enabled
        if session.settings.get("auto_save", False):
            await self._schedule_auto_save(session_id, file_id)

        # Trigger callback
        if self.on_file_changed:
            await self.on_file_changed(session_id, file)

        # Trigger live preview if enabled
        if session.settings.get("live_preview", False):
            await self._trigger_preview(session_id, file)

        return True

    async def _validate_content(
        self,
        content: str,
        mode: EditorMode,
    ) -> Tuple[bool, List[str]]:
        """Validate file content.

        Args:
            content: Content to validate
            mode: Editor mode

        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []

        try:
            if mode == EditorMode.YAML:
                yaml.safe_load(content)
            elif mode == EditorMode.JSON:
                json.loads(content)
            elif mode == EditorMode.PYTHON:
                # Basic Python syntax check
                compile(content, "<string>", "exec")
        except Exception as e:
            errors.append(str(e))

        return len(errors) == 0, errors

    async def _schedule_auto_save(
        self,
        session_id: str,
        file_id: str,
    ):
        """Schedule auto-save for a file.

        Args:
            session_id: Session ID
            file_id: File ID
        """
        session = self.get_session(session_id)
        if not session:
            return

        interval = session.settings.get("auto_save_interval", 30)

        async def auto_save():
            await asyncio.sleep(interval)
            if session_id in self.sessions:
                await self.save_file(session_id, file_id)

        # Cancel existing task if any
        if session_id in self.auto_save_tasks:
            self.auto_save_tasks[session_id].cancel()

        # Start new task
        self.auto_save_tasks[session_id] = asyncio.create_task(auto_save())

    async def _trigger_preview(
        self,
        session_id: str,
        file: EditorFile,
    ):
        """Trigger live preview update.

        Args:
            session_id: Session ID
            file: Editor file
        """
        if self.on_preview_update:
            await self.on_preview_update(session_id, file)

    async def get_file_status(
        self,
        session_id: str,
        file_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get file status information.

        Args:
            session_id: Session ID
            file_id: File ID

        Returns:
            Status dictionary or None
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return None

        file = session.files[file_id]

        return {
            "file_id": file.file_id,
            "file_path": file.file_path,
            "mode": file.mode.value,
            "language": file.language,
            "is_modified": file.is_modified,
            "is_dirty": file.is_dirty(),
            "last_modified": file.last_modified.isoformat(),
            "cursor_position": file.cursor_position,
            "version": file.version,
            "size": len(file.content),
            "lines": len(file.content.splitlines()),
            "lock_status": self._get_file_lock(file.file_path).value,
        }

    async def list_open_files(
        self,
        session_id: str,
    ) -> List[Dict[str, Any]]:
        """List all open files in a session.

        Args:
            session_id: Session ID

        Returns:
            List of file information dictionaries
        """
        session = self.get_session(session_id)
        if not session:
            return []

        return [
            {
                "file_id": file.file_id,
                "file_path": file.file_path,
                "mode": file.mode.value,
                "is_modified": file.is_modified,
                "is_active": file.file_id == session.active_file_id,
            }
            for file in session.files.values()
        ]

    def _generate_file_id(self, file_path: str) -> str:
        """Generate unique file ID.

        Args:
            file_path: File path

        Returns:
            Unique file ID
        """
        return hashlib.sha256(file_path.encode()).hexdigest()[:16]

    def _get_file_lock(self, file_path: str) -> LockStatus:
        """Get file lock status.

        Args:
            file_path: File path

        Returns:
            Lock status
        """
        return self.file_locks.get(file_path, {}).get("status", LockStatus.UNLOCKED)

    def _lock_file(self, file_path: str, user_id: str):
        """Lock file for editing.

        Args:
            file_path: File path
            user_id: User locking the file
        """
        if file_path not in self.file_locks:
            self.file_locks[file_path] = {}

        self.file_locks[file_path]["status"] = LockStatus.LOCKED
        self.file_locks[file_path]["user_id"] = user_id
        self.file_locks[file_path]["locked_at"] = datetime.now()

    def _unlock_file(self, file_path: str, user_id: str):
        """Unlock file.

        Args:
            file_path: File path
            user_id: User unlocking the file
        """
        if file_path in self.file_locks:
            lock_info = self.file_locks[file_path]
            if lock_info.get("user_id") == user_id:
                del self.file_locks[file_path]

    async def add_bookmark(
        self,
        session_id: str,
        file_id: str,
        line_number: int,
    ) -> bool:
        """Add bookmark to file.

        Args:
            session_id: Session ID
            file_id: File ID
            line_number: Line number

        Returns:
            True if bookmark added
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return False

        file = session.files[file_id]
        file.bookmarks.add(line_number)
        return True

    async def remove_bookmark(
        self,
        session_id: str,
        file_id: str,
        line_number: int,
    ) -> bool:
        """Remove bookmark from file.

        Args:
            session_id: Session ID
            file_id: File ID
            line_number: Line number

        Returns:
            True if bookmark removed
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return False

        file = session.files[file_id]
        if line_number in file.bookmarks:
            file.bookmarks.remove(line_number)
            return True
        return False

    async def format_file(
        self,
        session_id: str,
        file_id: str,
    ) -> bool:
        """Format file content.

        Args:
            session_id: Session ID
            file_id: File ID to format

        Returns:
            True if formatted successfully
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return False

        file = session.files[file_id]

        try:
            if file.mode == EditorMode.YAML:
                formatted = yaml.safe_dump(
                    yaml.safe_load(file.content),
                    default_flow_style=False,
                    sort_keys=False,
                )
            elif file.mode == EditorMode.JSON:
                formatted = json.dumps(
                    json.loads(file.content),
                    indent=2,
                    ensure_ascii=False,
                )
            else:
                return False

            file.content = formatted
            file.mark_modified()
            return True

        except Exception as e:
            logger.error(f"Error formatting file: {e}")
            return False

    async def get_syntax_highlighting(
        self,
        mode: EditorMode,
    ) -> Dict[str, Any]:
        """Get syntax highlighting configuration.

        Args:
            mode: Editor mode

        Returns:
            Syntax highlighting configuration
        """
        base_config = {
            "lineNumbers": True,
            "tabSize": 4,
            "insertSpaces": True,
            "autoIndent": True,
        }

        mode_configs = {
            EditorMode.YAML: {
                "language": "yaml",
                "keywords": ["name", "version", "description", "dependencies", "config"],
            },
            EditorMode.JSON: {
                "language": "json",
                "keywords": ["name", "version", "description", "dependencies", "config"],
            },
            EditorMode.PYTHON: {
                "language": "python",
                "keywords": [
                    "def", "class", "if", "else", "elif", "for", "while", "try", "except",
                ],
            },
            EditorMode.MARKDOWN: {
                "language": "markdown",
                "keywords": ["#", "##", "###", "-", "*", "```"],
            },
            EditorMode.TEXT: {
                "language": "text",
                "keywords": [],
            },
        }

        config = base_config.copy()
        config.update(mode_configs.get(mode, {}))
        return config

    async def export_file(
        self,
        session_id: str,
        file_id: str,
        format_type: str,
    ) -> Optional[str]:
        """Export file in specified format.

        Args:
            session_id: Session ID
            file_id: File ID
            format_type: Export format (json, yaml, etc.)

        Returns:
            Exported content or None
        """
        session = self.get_session(session_id)
        if not session or file_id not in session.files:
            return None

        file = session.files[file_id]

        try:
            if format_type == "json":
                return json.dumps(
                    {"content": file.content, "metadata": file.__dict__},
                    indent=2,
                    default=str,
                )
            elif format_type == "yaml":
                return yaml.dump(
                    {"content": file.content, "metadata": file.__dict__},
                    default_flow_style=False,
                )
            else:
                return file.content

        except Exception as e:
            logger.error(f"Error exporting file: {e}")
            return None

    async def get_editor_statistics(
        self,
        session_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get editor statistics for a session.

        Args:
            session_id: Session ID

        Returns:
            Statistics dictionary or None
        """
        session = self.get_session(session_id)
        if not session:
            return None

        total_files = len(session.files)
        modified_files = sum(1 for f in session.files.values() if f.is_modified)
        total_lines = sum(len(f.content.splitlines()) for f in session.files.values())
        total_chars = sum(len(f.content) for f in session.files.values())

        return {
            "session_id": session_id,
            "total_files": total_files,
            "modified_files": modified_files,
            "clean_files": total_files - modified_files,
            "total_lines": total_lines,
            "total_characters": total_chars,
            "active_file": session.active_file_id,
            "session_age": (datetime.now() - session.created_at).total_seconds(),
            "last_activity": (datetime.now() - session.last_activity).total_seconds(),
        }

    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Clean up inactive sessions.

        Args:
            max_age: Maximum age in hours
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)

        sessions_to_close = [
            session_id
            for session_id, session in self.sessions.items()
            if session.last_activity.timestamp() < cutoff_time
        ]

        for session_id in sessions_to_close:
            await self.close_session(session_id)

        logger.info(f"Cleaned up {len(sessions_to_close)} inactive sessions")
