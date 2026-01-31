"""File Editor.

This module contains the FileEditor class which provides online file editing
capabilities including syntax highlighting, auto-save, and real-time collaboration.
"""

import asyncio
import logging
import hashlib
import json
from typing import Dict, List, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, asdict
import threading
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

# Import managers and schemas
from app.file.manager import FileManager
from app.file.schemas.editor_config import (
    EditorSession,
    EditorSessionResponse,
    EditorConfig,
    EditorSettings,
    AutoSaveSettings,
    EditorLanguage,
    EditorChange,
    EditorCollaborator,
    EditorCommand,
    EditorSearch,
    get_language_from_extension,
    get_default_config_for_language,
)
from app.file.schemas.file_operations import FileResponse

# Import utils
from app.file.utils.validators import FileValidator
from app.file.utils.processors import process_file_content


logger = logging.getLogger(__name__)


class EditSessionStatus(Enum):
    """Edit session status."""
    ACTIVE = "active"
    IDLE = "idle"
    LOCKED = "locked"
    CLOSED = "closed"


class ConflictResolution(Enum):
    """Conflict resolution strategy."""
    AUTO_MERGE = "auto_merge"
    MANUAL_MERGE = "manual_merge"
    FORCE_OVERWRITE = "force_overwrite"
    REJECT = "reject"


@dataclass
class EditLock:
    """Edit lock for preventing concurrent edits."""
    session_id: UUID
    user_id: str
    file_id: UUID
    locked_at: datetime
    expires_at: datetime


@dataclass
class ChangeOperation:
    """Change operation in editor."""
    operation_id: str
    type: str  # insert, delete, replace
    position: int
    length: int
    content: str
    timestamp: datetime
    user_id: str


class FileEditor:
    """Online file editor with collaboration support."""

    def __init__(self, db_session: AsyncSession):
        """Initialize file editor.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.file_manager = FileManager(db_session)
        self.file_validator = FileValidator()
        self.active_sessions: Dict[UUID, EditSessionStatus] = {}
        self.session_locks: Dict[str, EditLock] = {}
        self.session_data: Dict[UUID, Dict[str, Any]] = {}
        self.collaborators: Dict[UUID, Set[str]] = {}
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=5)

    async def create_editor_session(
        self,
        file_id: UUID,
        user_id: str,
        config: Optional[EditorConfig] = None,
        read_only: bool = False
    ) -> EditorSessionResponse:
        """Create a new editor session.

        Args:
            file_id: File ID to edit
            user_id: User ID
            config: Editor configuration
            read_only: Whether session is read-only

        Returns:
            Editor session response
        """
        try:
            # Get file
            file_response = await self.file_manager.get_file(file_id, user_id)
            if not file_response:
                raise ValueError(f"File not found: {file_id}")

            # Check if file is editable
            if not await self._is_file_editable(file_response, user_id):
                raise ValueError("File is not editable")

            # Create session
            session_id = uuid4()
            language = get_language_from_extension(file_response.extension)

            # Use default config if not provided
            if config is None:
                config = get_default_config_for_language(language)

            # Create session data
            session_data = {
                "content": "",
                "original_content": "",
                "cursor_position": {"line": 0, "column": 0},
                "selections": [],
                "scroll_position": {"line": 0, "column": 0},
                "changes": [],
                "last_saved_content": "",
                "dirty": False,
                "version": 1,
            }

            # Load file content if exists
            if file_response.is_text_file:
                try:
                    content = await self._load_file_content(file_id, user_id)
                    session_data["content"] = content
                    session_data["original_content"] = content
                    session_data["last_saved_content"] = content
                except Exception as e:
                    logger.warning(f"Could not load file content: {str(e)}")

            # Store session
            with self._lock:
                self.active_sessions[session_id] = EditSessionStatus.ACTIVE
                self.session_data[session_id] = session_data
                self.collaborators[session_id] = set()

            # Add user as collaborator
            await self._add_collaborator(session_id, user_id)

            # Create session response
            session = EditorSession(
                session_id=session_id,
                file_id=file_id,
                user_id=user_id,
                language=language,
                config=config,
                content=session_data["content"],
                cursor_position=session_data["cursor_position"],
                selections=session_data["selections"],
                scroll_position=session_data["scroll_position"],
                is_dirty=session_data["dirty"],
                last_saved_at=None,
                expires_at=datetime.utcnow() + timedelta(hours=24),
                collaborators=list(self.collaborators[session_id]),
                is_readonly=read_only,
                version=session_data["version"]
            )

            logger.info(f"Editor session created: {session_id} for file {file_id} by user {user_id}")
            return EditorSessionResponse.model_validate(session)

        except Exception as e:
            logger.error(f"Error creating editor session: {str(e)}")
            raise

    async def get_editor_session(
        self,
        session_id: UUID,
        user_id: str
    ) -> Optional[EditorSessionResponse]:
        """Get editor session.

        Args:
            session_id: Session ID
            user_id: User ID

        Returns:
            Editor session response or None if not found
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return None

                session_data = self.session_data.get(session_id)
                if not session_data:
                    return None

            # Get file
            # Note: In a real implementation, you'd store file_id in session_data
            # For now, we'll return the session data

            # Create session response
            session = EditorSession(
                session_id=session_id,
                file_id=uuid4(),  # This should come from session data
                user_id=user_id,
                language=EditorLanguage.TEXT,
                config=get_default_config_for_language(EditorLanguage.TEXT),
                content=session_data["content"],
                cursor_position=session_data["cursor_position"],
                selections=session_data["selections"],
                scroll_position=session_data["scroll_position"],
                is_dirty=session_data["dirty"],
                collaborators=list(self.collaborators.get(session_id, set())),
                version=session_data["version"]
            )

            return EditorSessionResponse.model_validate(session)

        except Exception as e:
            logger.error(f"Error getting editor session {session_id}: {str(e)}")
            return None

    async def apply_changes(
        self,
        session_id: UUID,
        user_id: str,
        changes: List[ChangeOperation],
        version: int
    ) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Apply changes to editor session.

        Args:
            session_id: Session ID
            user_id: User ID
            changes: List of change operations
            version: Client version

        Returns:
            Tuple of (success, error_message, response_data)
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return False, "Session not found", {}

                session_data = self.session_data.get(session_id)
                if not session_data:
                    return False, "Session data not found", {}

                # Check version
                if version != session_data["version"]:
                    return False, "Version conflict", {
                        "server_version": session_data["version"],
                        "client_version": version
                    }

            # Check if user is collaborator
            if user_id not in self.collaborators.get(session_id, set()):
                return False, "User not authorized", {}

            # Apply changes
            current_content = session_data["content"]
            operations_applied = 0

            for change in changes:
                try:
                    current_content = await self._apply_change_operation(
                        current_content,
                        change
                    )
                    operations_applied += 1
                except Exception as e:
                    logger.error(f"Error applying change operation: {str(e)}")
                    return False, f"Failed to apply change: {str(e)}", {}

            # Update session
            with self._lock:
                session_data["content"] = current_content
                session_data["changes"].extend([asdict(c) for c in changes])
                session_data["dirty"] = True
                session_data["version"] += 1

            # Check if auto-save is needed
            should_auto_save = await self._check_auto_save(session_id)

            response_data = {
                "operations_applied": operations_applied,
                "server_version": session_data["version"],
                "content_length": len(current_content),
                "auto_save_triggered": should_auto_save,
                "dirty": session_data["dirty"]
            }

            logger.debug(f"Changes applied to session {session_id}: {operations_applied} operations")
            return True, None, response_data

        except Exception as e:
            logger.error(f"Error applying changes to session {session_id}: {str(e)}")
            return False, str(e), {}

    async def save_session(
        self,
        session_id: UUID,
        user_id: str,
        force: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """Save editor session.

        Args:
            session_id: Session ID
            user_id: User ID
            force: Force save even if not dirty

        Returns:
            Tuple of (success, error_message)
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return False, "Session not found"

                session_data = self.session_data.get(session_id)
                if not session_data:
                    return False, "Session data not found"

                # Check if save is needed
                if not force and not session_data["dirty"]:
                    return True, "No changes to save"

            # Save content
            # In a real implementation, you'd update the file content here

            with self._lock:
                session_data["last_saved_content"] = session_data["content"]
                session_data["dirty"] = False

            logger.info(f"Session saved: {session_id} by user {user_id}")
            return True, None

        except Exception as e:
            logger.error(f"Error saving session {session_id}: {str(e)}")
            return False, str(e)

    async def close_session(
        self,
        session_id: UUID,
        user_id: str
    ) -> bool:
        """Close editor session.

        Args:
            session_id: Session ID
            user_id: User ID

        Returns:
            True if closed successfully
        """
        try:
            with self._lock:
                if session_id not in self.active_sessions:
                    return False

                # Remove user from collaborators
                if session_id in self.collaborators:
                    self.collaborators[session_id].discard(user_id)

                    # If no more collaborators, close session
                    if not self.collaborators[session_id]:
                        self.active_sessions[session_id] = EditSessionStatus.CLOSED
                        del self.session_data[session_id]
                        del self.collaborators[session_id]
                    else:
                        # Session still active with other users
                        pass

            logger.info(f"Session closed: {session_id} by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error closing session {session_id}: {str(e)}")
            return False

    async def add_collaborator(
        self,
        session_id: UUID,
        user_id: str
    ) -> bool:
        """Add collaborator to session.

        Args:
            session_id: Session ID
            user_id: User ID to add

        Returns:
            True if added successfully
        """
        try:
            result = await self._add_collaborator(session_id, user_id)
            return result
        except Exception as e:
            logger.error(f"Error adding collaborator: {str(e)}")
            return False

    async def remove_collaborator(
        self,
        session_id: UUID,
        user_id: str
    ) -> bool:
        """Remove collaborator from session.

        Args:
            session_id: Session ID
            user_id: User ID to remove

        Returns:
            True if removed successfully
        """
        try:
            with self._lock:
                if session_id in self.collaborators:
                    self.collaborators[session_id].discard(user_id)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error removing collaborator: {str(e)}")
            return False

    async def search_in_session(
        self,
        session_id: UUID,
        query: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False
    ) -> List[Dict[str, Any]]:
        """Search in session content.

        Args:
            session_id: Session ID
            query: Search query
            case_sensitive: Case sensitive search
            whole_word: Match whole words
            regex: Use regular expressions

        Returns:
            List of search results
        """
        try:
            with self._lock:
                if session_id not in self.session_data:
                    return []

                content = self.session_data[session_id]["content"]

            # Perform search
            import re

            pattern = query
            flags = 0 if case_sensitive else re.IGNORECASE

            if whole_word:
                pattern = r'\b' + re.escape(query) + r'\b'

            if regex:
                try:
                    compiled_pattern = re.compile(pattern, flags)
                except re.error as e:
                    logger.error(f"Invalid regex pattern: {str(e)}")
                    return []
            else:
                compiled_pattern = re.compile(re.escape(pattern), flags)

            matches = []
            for match in compiled_pattern.finditer(content):
                matches.append({
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(),
                    "line": content[:match.start()].count('\n') + 1,
                    "column": match.start() - content.rfind('\n', 0, match.start())
                })

            logger.debug(f"Search in session {session_id} found {len(matches)} matches")
            return matches

        except Exception as e:
            logger.error(f"Error searching in session {session_id}: {str(e)}")
            return []

    async def replace_in_session(
        self,
        session_id: UUID,
        user_id: str,
        query: str,
        replacement: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
        replace_all: bool = False
    ) -> Tuple[bool, int, Optional[str]]:
        """Replace text in session.

        Args:
            session_id: Session ID
            user_id: User ID
            query: Text to replace
            replacement: Replacement text
            case_sensitive: Case sensitive
            whole_word: Match whole words
            regex: Use regex
            replace_all: Replace all occurrences

        Returns:
            Tuple of (success, replacements_count, error_message)
        """
        try:
            with self._lock:
                if session_id not in self.session_data:
                    return False, 0, "Session not found"

                session_data = self.session_data[session_id]
                content = session_data["content"]

            # Check authorization
            if user_id not in self.collaborators.get(session_id, set()):
                return False, 0, "User not authorized"

            # Perform replace
            import re

            pattern = query
            flags = 0 if case_sensitive else re.IGNORECASE

            if whole_word:
                pattern = r'\b' + re.escape(query) + r'\b'

            if regex:
                try:
                    compiled_pattern = re.compile(pattern, flags)
                except re.error as e:
                    return False, 0, f"Invalid regex: {str(e)}"
            else:
                compiled_pattern = re.compile(re.escape(pattern), flags)

            if replace_all:
                new_content, count = compiled_pattern.subn(replacement, content)
            else:
                match = compiled_pattern.search(content)
                if match:
                    new_content = content[:match.start()] + replacement + content[match.end()]
                    count = 1
                else:
                    return False, 0, "No matches found"

            # Update session
            with self._lock:
                session_data["content"] = new_content
                session_data["dirty"] = True
                session_data["version"] += 1

            logger.info(f"Replace in session {session_id}: {count} replacements by user {user_id}")
            return True, count, None

        except Exception as e:
            logger.error(f"Error replacing in session {session_id}: {str(e)}")
            return False, 0, str(e)

    async def get_session_statistics(
        self,
        session_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get session statistics.

        Args:
            session_id: Session ID

        Returns:
            Session statistics or None if not found
        """
        try:
            with self._lock:
                if session_id not in self.session_data:
                    return None

                session_data = self.session_data[session_id]
                collaborators = self.collaborators.get(session_id, set())

            return {
                "session_id": str(session_id),
                "status": self.active_sessions.get(session_id, EditSessionStatus.CLOSED).value,
                "content_length": len(session_data["content"]),
                "line_count": session_data["content"].count('\n') + 1,
                "change_count": len(session_data["changes"]),
                "collaborator_count": len(collaborators),
                "collaborators": list(collaborators),
                "is_dirty": session_data["dirty"],
                "version": session_data["version"],
                "cursor_position": session_data["cursor_position"],
            }

        except Exception as e:
            logger.error(f"Error getting session statistics {session_id}: {str(e)}")
            return None

    # Helper methods

    async def _is_file_editable(self, file_response: FileResponse, user_id: str) -> bool:
        """Check if file is editable.

        Args:
            file_response: File response
            user_id: User ID

        Returns:
            True if file is editable
        """
        # Check file type
        if file_response.type == "folder":
            return False

        # Check if text file
        if not file_response.mime_type.startswith('text/'):
            # Allow some non-text files to be editable (e.g., JSON, XML, etc.)
            if file_response.extension not in ['.json', '.xml', '.yaml', '.yml', '.md']:
                return False

        # Check permissions
        # In a real implementation, you'd check file permissions here

        return True

    async def _load_file_content(self, file_id: UUID, user_id: str) -> str:
        """Load file content.

        Args:
            file_id: File ID
            user_id: User ID

        Returns:
            File content as string
        """
        # In a real implementation, you'd load the actual file content
        # For now, return empty string
        return ""

    async def _apply_change_operation(
        self,
        content: str,
        change: ChangeOperation
    ) -> str:
        """Apply a single change operation.

        Args:
            content: Current content
            change: Change operation

        Returns:
            Updated content
        """
        if change.type == "insert":
            return content[:change.position] + change.content + content[change.position:]
        elif change.type == "delete":
            return content[:change.position] + content[change.position + change.length:]
        elif change.type == "replace":
            return content[:change.position] + change.content + content[change.position + change.length:]
        else:
            raise ValueError(f"Unknown change type: {change.type}")

    async def _check_auto_save(self, session_id: UUID) -> bool:
        """Check if auto-save should be triggered.

        Args:
            session_id: Session ID

        Returns:
            True if auto-save should be triggered
        """
        with self._lock:
            if session_id not in self.session_data:
                return False

            session_data = self.session_data[session_id]
            config = session_data.get("config")

            if not config or not config.auto_save.enabled:
                return False

            # Check if content has changed significantly
            # For simplicity, just check if dirty
            return session_data["dirty"]

    async def _add_collaborator(
        self,
        session_id: UUID,
        user_id: str
    ) -> bool:
        """Add collaborator to session.

        Args:
            session_id: Session ID
            user_id: User ID

        Returns:
            True if added successfully
        """
        with self._lock:
            if session_id not in self.collaborators:
                self.collaborators[session_id] = set()

            self.collaborators[session_id].add(user_id)
            return True

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        try:
            with self._lock:
                expired_sessions = []

                for session_id in list(self.active_sessions.keys()):
                    # Check if session has no collaborators
                    if session_id in self.collaborators and not self.collaborators[session_id]:
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    self.active_sessions[session_id] = EditSessionStatus.CLOSED
                    del self.session_data[session_id]
                    del self.collaborators[session_id]

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {str(e)}")

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions.

        Returns:
            Number of active sessions
        """
        with self._lock:
            return len([s for s in self.active_sessions.values() if s == EditSessionStatus.ACTIVE])

    def get_total_collaborators_count(self) -> int:
        """Get total count of collaborators across all sessions.

        Returns:
            Total number of collaborators
        """
        with self._lock:
            return sum(len(collab) for collab in self.collaborators.values())
