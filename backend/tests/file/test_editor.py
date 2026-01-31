"""Tests for FileEditor.

This module contains comprehensive unit tests for the FileEditor class including
editing functionality, auto-save, syntax validation, and collaboration features.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any
import re

# Import editor and related classes
from app.file.editor import (
    FileEditor,
    EditSessionStatus,
    ConflictResolution,
    EditLock,
    ChangeOperation,
)
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
from app.file.schemas.file_operations import FileResponse, FileType


class TestFileEditor:
    """Test suite for FileEditor."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_editor(self, db_session):
        """Create FileEditor instance with mocked database."""
        return FileEditor(db_session)

    @pytest.fixture
    def sample_file_id(self):
        """Generate sample file ID."""
        return uuid4()

    @pytest.fixture
    def sample_user_id(self):
        """Generate sample user ID."""
        return "test-user-123"

    @pytest.fixture
    def sample_file_response(self, sample_file_id):
        """Create sample file response."""
        return FileResponse(
            id=sample_file_id,
            name="test.txt",
            path="/test.txt",
            type="file",
            size=1024,
            mime_type="text/plain",
            extension=".txt",
            is_text_file=True,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by="test-user",
            modified_by="test-user",
            status="active",
            version=1,
            metadata={},
            permissions=["read", "write"],
            tags=[],
            custom_fields={},
            backup_count=0,
            is_deleted=False,
            deleted_at=None,
            retention_period=None,
        )

    @pytest.fixture
    def sample_config(self):
        """Create sample editor configuration."""
        return EditorConfig(
            language=EditorLanguage.PYTHON,
            theme="dark",
            font_size=14,
            tab_size=4,
            auto_close_brackets=True,
            auto_close_tags=True,
            word_wrap=True,
            line_numbers=True,
            show_whitespace=False,
            show_indentation_guides=True,
            highlight_active_line=True,
            auto_save=AutoSaveSettings(enabled=True, interval=30),
            settings=EditorSettings(
                vim_mode=False,
                emmet_enabled=True,
                linting_enabled=True,
                format_on_save=True,
                minimap_enabled=True,
                show_folding=True,
            ),
        )

    @pytest.fixture
    def sample_changes(self):
        """Create sample change operations."""
        return [
            ChangeOperation(
                operation_id="op1",
                type="insert",
                position=0,
                length=0,
                content="# Test file",
                timestamp=datetime.utcnow(),
                user_id="test-user",
            ),
            ChangeOperation(
                operation_id="op2",
                type="insert",
                position=12,
                length=0,
                content="\nprint('Hello, World!')",
                timestamp=datetime.utcnow(),
                user_id="test-user",
            ),
        ]

    # Test session creation

    @pytest.mark.asyncio
    async def test_create_editor_session_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test successful editor session creation."""
        # Mock file_manager.get_file
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            # Create session
            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Assertions
            assert session is not None
            assert session.session_id is not None
            assert session.file_id == sample_file_id
            assert session.user_id == sample_user_id
            assert session.language == EditorLanguage.TEXT
            assert session.content == ""
            assert session.is_dirty is False
            assert len(session.collaborators) == 1
            assert sample_user_id in session.collaborators

    @pytest.mark.asyncio
    async def test_create_editor_session_with_config(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
        sample_config,
    ):
        """Test editor session creation with custom configuration."""
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
                config=sample_config,
            )

            assert session is not None
            assert session.config == sample_config

    @pytest.mark.asyncio
    async def test_create_editor_session_file_not_found(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
    ):
        """Test editor session creation with non-existent file."""
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = None

            with pytest.raises(ValueError, match="File not found"):
                await file_editor.create_editor_session(
                    file_id=sample_file_id,
                    user_id=sample_user_id,
                )

    @pytest.mark.asyncio
    async def test_create_editor_session_non_editable_file(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
    ):
        """Test editor session creation with non-editable file."""
        # Create non-editable file response (binary file)
        non_editable_file = FileResponse(
            id=sample_file_id,
            name="test.bin",
            path="/test.bin",
            type="file",
            size=1024,
            mime_type="application/octet-stream",
            extension=".bin",
            is_text_file=False,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by="test-user",
            modified_by="test-user",
            status="active",
            version=1,
            metadata={},
            permissions=["read"],
            tags=[],
            custom_fields={},
            backup_count=0,
            is_deleted=False,
            deleted_at=None,
            retention_period=None,
        )

        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = non_editable_file

            with pytest.raises(ValueError, match="File is not editable"):
                await file_editor.create_editor_session(
                    file_id=sample_file_id,
                    user_id=sample_user_id,
                )

    @pytest.mark.asyncio
    async def test_create_editor_session_readonly(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test read-only editor session creation."""
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
                read_only=True,
            )

            assert session is not None
            assert session.is_readonly is True

    # Test session retrieval

    @pytest.mark.asyncio
    async def test_get_editor_session_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test successful session retrieval."""
        # First create a session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            created_session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Now retrieve it
            retrieved_session = await file_editor.get_editor_session(
                session_id=created_session.session_id,
                user_id=sample_user_id,
            )

            assert retrieved_session is not None
            assert retrieved_session.session_id == created_session.session_id

    @pytest.mark.asyncio
    async def test_get_editor_session_not_found(self, file_editor, sample_user_id):
        """Test retrieving non-existent session."""
        session_id = uuid4()

        retrieved_session = await file_editor.get_editor_session(
            session_id=session_id,
            user_id=sample_user_id,
        )

        assert retrieved_session is None

    # Test change operations

    @pytest.mark.asyncio
    async def test_apply_changes_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
        sample_changes,
    ):
        """Test successful change application."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Apply changes
            success, error, response = await file_editor.apply_changes(
                session_id=session.session_id,
                user_id=sample_user_id,
                changes=sample_changes,
                version=1,
            )

            assert success is True
            assert error is None
            assert response["operations_applied"] == 2
            assert response["server_version"] == 2

    @pytest.mark.asyncio
    async def test_apply_changes_session_not_found(
        self,
        file_editor,
        sample_user_id,
        sample_changes,
    ):
        """Test applying changes to non-existent session."""
        session_id = uuid4()

        success, error, response = await file_editor.apply_changes(
            session_id=session_id,
            user_id=sample_user_id,
            changes=sample_changes,
            version=1,
        )

        assert success is False
        assert error == "Session not found"

    @pytest.mark.asyncio
    async def test_apply_changes_version_conflict(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
        sample_changes,
    ):
        """Test applying changes with version conflict."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Try to apply changes with wrong version
            success, error, response = await file_editor.apply_changes(
                session_id=session.session_id,
                user_id=sample_user_id,
                changes=sample_changes,
                version=999,  # Wrong version
            )

            assert success is False
            assert error == "Version conflict"
            assert response["server_version"] == 1
            assert response["client_version"] == 999

    @pytest.mark.asyncio
    async def test_apply_changes_unauthorized_user(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
        sample_changes,
    ):
        """Test applying changes by unauthorized user."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Try to apply changes with different user
            other_user = "other-user"
            success, error, response = await file_editor.apply_changes(
                session_id=session.session_id,
                user_id=other_user,
                changes=sample_changes,
                version=1,
            )

            assert success is False
            assert error == "User not authorized"

    @pytest.mark.asyncio
    async def test_apply_changes_insert_operation(self, file_editor):
        """Test insert change operation."""
        content = "Hello, World!"
        change = ChangeOperation(
            operation_id="op1",
            type="insert",
            position=5,
            length=0,
            content=" beautiful",
            timestamp=datetime.utcnow(),
            user_id="test-user",
        )

        result = await file_editor._apply_change_operation(content, change)

        assert result == "Hello beautiful, World!"

    @pytest.mark.asyncio
    async def test_apply_changes_delete_operation(self, file_editor):
        """Test delete change operation."""
        content = "Hello, World!"
        change = ChangeOperation(
            operation_id="op1",
            type="delete",
            position=5,
            length=7,
            content="",
            timestamp=datetime.utcnow(),
            user_id="test-user",
        )

        result = await file_editor._apply_change_operation(content, change)

        assert result == "Hello!"

    @pytest.mark.asyncio
    async def test_apply_changes_replace_operation(self, file_editor):
        """Test replace change operation."""
        content = "Hello, World!"
        change = ChangeOperation(
            operation_id="op1",
            type="replace",
            position=7,
            length=5,
            content="Universe",
            timestamp=datetime.utcnow(),
            user_id="test-user",
        )

        result = await file_editor._apply_change_operation(content, change)

        assert result == "Hello, Universe!"

    # Test auto-save functionality

    @pytest.mark.asyncio
    async def test_save_session_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test successful session save."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Simulate changes
            with file_editor._lock:
                file_editor.session_data[session.session_id]["dirty"] = True
                file_editor.session_data[session.session_id]["content"] = "Test content"

            # Save session
            success, error = await file_editor.save_session(
                session_id=session.session_id,
                user_id=sample_user_id,
            )

            assert success is True
            assert error is None

            # Check that dirty flag is cleared
            assert file_editor.session_data[session.session_id]["dirty"] is False

    @pytest.mark.asyncio
    async def test_save_session_not_dirty(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test saving session without changes."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Save session without changes
            success, error = await file_editor.save_session(
                session_id=session.session_id,
                user_id=sample_user_id,
            )

            assert success is True
            assert error == "No changes to save"

    @pytest.mark.asyncio
    async def test_save_session_force(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test forced session save."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Force save without changes
            success, error = await file_editor.save_session(
                session_id=session.session_id,
                user_id=sample_user_id,
                force=True,
            )

            assert success is True
            assert error is None

    @pytest.mark.asyncio
    async def test_check_auto_save(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test auto-save check functionality."""
        # Create session with auto-save enabled
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Mark as dirty
            with file_editor._lock:
                file_editor.session_data[session.session_id]["dirty"] = True

            # Check auto-save
            should_auto_save = await file_editor._check_auto_save(session.session_id)

            assert should_auto_save is True

    # Test collaboration

    @pytest.mark.asyncio
    async def test_add_collaborator_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test adding collaborator to session."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add another collaborator
            other_user = "other-user-456"
            success = await file_editor.add_collaborator(
                session_id=session.session_id,
                user_id=other_user,
            )

            assert success is True
            assert other_user in file_editor.collaborators[session.session_id]

    @pytest.mark.asyncio
    async def test_remove_collaborator_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test removing collaborator from session."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add another collaborator
            other_user = "other-user-456"
            await file_editor.add_collaborator(
                session_id=session.session_id,
                user_id=other_user,
            )

            # Remove the collaborator
            success = await file_editor.remove_collaborator(
                session_id=session.session_id,
                user_id=other_user,
            )

            assert success is True
            assert other_user not in file_editor.collaborators[session.session_id]

    @pytest.mark.asyncio
    async def test_close_session_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test successful session closure."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Close session
            success = await file_editor.close_session(
                session_id=session.session_id,
                user_id=sample_user_id,
            )

            assert success is True
            # Session should be closed since no other collaborators
            assert file_editor.active_sessions[session.session_id] == EditSessionStatus.CLOSED

    @pytest.mark.asyncio
    async def test_close_session_with_multiple_collaborators(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test session closure with multiple collaborators."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add another collaborator
            other_user = "other-user-456"
            await file_editor.add_collaborator(
                session_id=session.session_id,
                user_id=other_user,
            )

            # Close session for first user
            success = await file_editor.close_session(
                session_id=session.session_id,
                user_id=sample_user_id,
            )

            assert success is True
            # Session should remain active for other collaborator
            assert file_editor.active_sessions[session.session_id] == EditSessionStatus.ACTIVE

    # Test search and replace

    @pytest.mark.asyncio
    async def test_search_in_session_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test successful search in session."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello, World! Hello, Universe!"

            # Search for "Hello"
            results = await file_editor.search_in_session(
                session_id=session.session_id,
                query="Hello",
            )

            assert len(results) == 2
            assert results[0]["text"] == "Hello"
            assert results[1]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_search_in_session_case_sensitive(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test case-sensitive search."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello, hello, HELLO"

            # Case-sensitive search
            results = await file_editor.search_in_session(
                session_id=session.session_id,
                query="Hello",
                case_sensitive=True,
            )

            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_in_session_whole_word(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test whole word search."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello world, hello world!"

            # Whole word search
            results = await file_editor.search_in_session(
                session_id=session.session_id,
                query="hello",
                whole_word=True,
            )

            assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_in_session_regex(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test regex search."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello123, World456, Test789"

            # Regex search for numbers
            results = await file_editor.search_in_session(
                session_id=session.session_id,
                query=r"\d+",
                regex=True,
            )

            assert len(results) == 3
            assert results[0]["text"] == "123"

    @pytest.mark.asyncio
    async def test_replace_in_session_success(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test successful text replacement."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello, World!"

            # Replace "World" with "Universe"
            success, count, error = await file_editor.replace_in_session(
                session_id=session.session_id,
                user_id=sample_user_id,
                query="World",
                replacement="Universe",
            )

            assert success is True
            assert count == 1
            assert error is None

            # Check content
            updated_content = file_editor.session_data[session.session_id]["content"]
            assert updated_content == "Hello, Universe!"

    @pytest.mark.asyncio
    async def test_replace_in_session_replace_all(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test replace all occurrences."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello, World! Hello, World!"

            # Replace all
            success, count, error = await file_editor.replace_in_session(
                session_id=session.session_id,
                user_id=sample_user_id,
                query="Hello",
                replacement="Hi",
                replace_all=True,
            )

            assert success is True
            assert count == 2

            # Check content
            updated_content = file_editor.session_data[session.session_id]["content"]
            assert updated_content == "Hi, World! Hi, World!"

    # Test session statistics

    @pytest.mark.asyncio
    async def test_get_session_statistics(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test getting session statistics."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content and changes
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Line 1\nLine 2\nLine 3"
                file_editor.session_data[session.session_id]["changes"] = [{"type": "insert"}]

            # Get statistics
            stats = await file_editor.get_session_statistics(session.session_id)

            assert stats is not None
            assert stats["content_length"] == 30  # "Line 1\nLine 2\nLine 3"
            assert stats["line_count"] == 3
            assert stats["change_count"] == 1
            assert stats["collaborator_count"] == 1
            assert stats["is_dirty"] is False
            assert stats["version"] == 1

    @pytest.mark.asyncio
    async def test_get_session_statistics_not_found(self, file_editor):
        """Test getting statistics for non-existent session."""
        session_id = uuid4()

        stats = await file_editor.get_session_statistics(session_id)

        assert stats is None

    # Test file validation

    @pytest.mark.asyncio
    async def test_is_file_editable_text_file(
        self,
        file_editor,
        sample_file_response,
    ):
        """Test file editable check for text file."""
        result = await file_editor._is_file_editable(
            sample_file_response,
            "test-user",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_is_file_editable_editable_extensions(
        self,
        file_editor,
    ):
        """Test file editable check for editable file extensions."""
        file_response = FileResponse(
            id=uuid4(),
            name="test.json",
            path="/test.json",
            type="file",
            size=1024,
            mime_type="application/json",
            extension=".json",
            is_text_file=False,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by="test-user",
            modified_by="test-user",
            status="active",
            version=1,
            metadata={},
            permissions=["read", "write"],
            tags=[],
            custom_fields={},
            backup_count=0,
            is_deleted=False,
            deleted_at=None,
            retention_period=None,
        )

        result = await file_editor._is_file_editable(
            file_response,
            "test-user",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_is_file_editable_non_editable_binary(
        self,
        file_editor,
    ):
        """Test file editable check for binary file."""
        file_response = FileResponse(
            id=uuid4(),
            name="test.jpg",
            path="/test.jpg",
            type="file",
            size=1024,
            mime_type="image/jpeg",
            extension=".jpg",
            is_text_file=False,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by="test-user",
            modified_by="test-user",
            status="active",
            version=1,
            metadata={},
            permissions=["read"],
            tags=[],
            custom_fields={},
            backup_count=0,
            is_deleted=False,
            deleted_at=None,
            retention_period=None,
        )

        result = await file_editor._is_file_editable(
            file_response,
            "test-user",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_is_file_editable_folder(
        self,
        file_editor,
    ):
        """Test file editable check for folder."""
        file_response = FileResponse(
            id=uuid4(),
            name="folder",
            path="/folder",
            type="folder",
            size=0,
            mime_type="",
            extension="",
            is_text_file=False,
            created_at=datetime.utcnow(),
            modified_at=datetime.utcnow(),
            created_by="test-user",
            modified_by="test-user",
            status="active",
            version=1,
            metadata={},
            permissions=["read"],
            tags=[],
            custom_fields={},
            backup_count=0,
            is_deleted=False,
            deleted_at=None,
            retention_period=None,
        )

        result = await file_editor._is_file_editable(
            file_response,
            "test-user",
        )

        assert result is False

    # Test session cleanup

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test cleanup of expired sessions."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Verify session is active
            assert len(file_editor.active_sessions) == 1

            # Close the session (removes collaborator)
            await file_editor.close_session(
                session_id=session.session_id,
                user_id=sample_user_id,
            )

            # Cleanup expired sessions
            await file_editor.cleanup_expired_sessions()

            # Verify session is cleaned up
            assert len(file_editor.active_sessions) == 0

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_with_collaborators(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test cleanup with multiple collaborators."""
        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add another collaborator
            other_user = "other-user-456"
            await file_editor.add_collaborator(
                session_id=session.session_id,
                user_id=other_user,
            )

            # Remove first user
            await file_editor.remove_collaborator(
                session_id=session.session_id,
                user_id=sample_user_id,
            )

            # Cleanup expired sessions
            await file_editor.cleanup_expired_sessions()

            # Session should still exist with remaining collaborator
            assert len(file_editor.active_sessions) == 1
            assert session.session_id in file_editor.active_sessions

    # Test utility methods

    @pytest.mark.asyncio
    async def test_get_active_sessions_count(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test getting active sessions count."""
        initial_count = file_editor.get_active_sessions_count()

        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

        new_count = file_editor.get_active_sessions_count()
        assert new_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_get_total_collaborators_count(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test getting total collaborators count."""
        initial_count = file_editor.get_total_collaborators_count()

        # Create session
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

        new_count = file_editor.get_total_collaborators_count()
        assert new_count == initial_count + 1

    # Test edge cases

    @pytest.mark.asyncio
    async def test_apply_change_unknown_operation_type(
        self,
        file_editor,
    ):
        """Test applying unknown change operation type."""
        content = "Hello, World!"
        change = ChangeOperation(
            operation_id="op1",
            type="unknown",
            position=0,
            length=0,
            content="",
            timestamp=datetime.utcnow(),
            user_id="test-user",
        )

        with pytest.raises(ValueError, match="Unknown change type"):
            await file_editor._apply_change_operation(content, change)

    @pytest.mark.asyncio
    async def test_replace_in_session_no_matches(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test replace with no matches found."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Add content
            with file_editor._lock:
                file_editor.session_data[session.session_id]["content"] = "Hello, World!"

            # Try to replace non-existent text
            success, count, error = await file_editor.replace_in_session(
                session_id=session.session_id,
                user_id=sample_user_id,
                query="Universe",
                replacement="World",
            )

            assert success is False
            assert count == 0
            assert error == "No matches found"

    @pytest.mark.asyncio
    async def test_replace_in_session_invalid_regex(
        self,
        file_editor,
        sample_file_id,
        sample_user_id,
        sample_file_response,
    ):
        """Test replace with invalid regex."""
        # Create session with content
        with patch.object(file_editor.file_manager, 'get_file', new_callable=AsyncMock) as mock_get_file:
            mock_get_file.return_value = sample_file_response

            session = await file_editor.create_editor_session(
                file_id=sample_file_id,
                user_id=sample_user_id,
            )

            # Try to replace with invalid regex
            success, count, error = await file_editor.replace_in_session(
                session_id=session.session_id,
                user_id=sample_user_id,
                query="[invalid",
                replacement="text",
                regex=True,
            )

            assert success is False
            assert count == 0
            assert "Invalid regex" in error

    # Test language detection

    def test_get_language_from_extension_python(self):
        """Test language detection for Python files."""
        language = get_language_from_extension(".py")
        assert language == EditorLanguage.PYTHON

    def test_get_language_from_extension_javascript(self):
        """Test language detection for JavaScript files."""
        language = get_language_from_extension(".js")
        assert language == EditorLanguage.JAVASCRIPT

    def test_get_language_from_extension_java(self):
        """Test language detection for Java files."""
        language = get_language_from_extension(".java")
        assert language == EditorLanguage.JAVA

    def test_get_language_from_extension_text(self):
        """Test language detection for unknown extension."""
        language = get_language_from_extension(".unknown")
        assert language == EditorLanguage.TEXT

    def test_get_default_config_for_language_python(self):
        """Test default config for Python."""
        config = get_default_config_for_language(EditorLanguage.PYTHON)

        assert config is not None
        assert config.language == EditorLanguage.PYTHON
        assert config.tab_size == 4
        assert config.auto_close_brackets is True

    def test_get_default_config_for_language_javascript(self):
        """Test default config for JavaScript."""
        config = get_default_config_for_language(EditorLanguage.JAVASCRIPT)

        assert config is not None
        assert config.language == EditorLanguage.JAVASCRIPT
        assert config.tab_size == 2
        assert config.auto_close_brackets is True
