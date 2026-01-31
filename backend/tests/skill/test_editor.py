"""Tests for SkillEditor.

This module contains comprehensive unit tests for the SkillEditor
online editor functionality.
"""

import pytest
import asyncio
import json
import yaml
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from app.skill.editor import (
    SkillEditor,
    EditorFile,
    EditorSession,
    EditorMode,
    SaveStatus,
    LockStatus,
)
from app.skill.manager import SkillManager
from app.skill.event_manager import SkillEventManager, EventType


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def skill_manager():
    """Create mock skill manager."""
    return Mock(spec=SkillManager)


@pytest.fixture
def event_manager():
    """Create mock event manager."""
    manager = Mock(spec=SkillEventManager)
    manager.publish_event = AsyncMock(return_value="event_id")
    return manager


@pytest.fixture
def editor(skill_manager, event_manager, temp_dir):
    """Create SkillEditor instance for testing."""
    return SkillEditor(
        skill_manager=skill_manager,
        event_manager=event_manager,
        workspace_path=temp_dir,
    )


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content for testing."""
    return """name: test-skill
version: 1.0.0
description: Test skill
author: Test Author
dependencies:
  - click
  - pydantic
config:
  enabled: true
  timeout: 30
"""


@pytest.fixture
def sample_json_content():
    """Sample JSON content for testing."""
    return json.dumps({
        "name": "test-skill",
        "version": "1.0.0",
        "description": "Test skill",
        "author": "Test Author",
    }, indent=2)


class TestEditorFile:
    """Test EditorFile dataclass."""

    def test_create_editor_file(self):
        """Test creating a new editor file."""
        file = EditorFile(
            file_id="test123",
            file_path="/test/file.yaml",
            content="test content",
            original_content="test content",
            mode=EditorMode.YAML,
            language="yaml",
        )

        assert file.file_id == "test123"
        assert file.file_path == "/test/file.yaml"
        assert file.content == "test content"
        assert file.mode == EditorMode.YAML
        assert not file.is_modified
        assert file.version == 1

    def test_is_dirty_returns_true_when_modified(self):
        """Test is_dirty returns True when file is modified."""
        file = EditorFile(
            file_id="test123",
            file_path="/test/file.yaml",
            content="original",
            original_content="original",
            mode=EditorMode.YAML,
            language="yaml",
        )

        # Not dirty initially
        assert not file.is_dirty()

        # Dirty after content change
        file.content = "modified"
        assert file.is_dirty()

    def test_mark_saved_updates_state(self):
        """Test mark_saved updates file state."""
        file = EditorFile(
            file_id="test123",
            file_path="/test/file.yaml",
            content="modified",
            original_content="original",
            mode=EditorMode.YAML,
            language="yaml",
        )

        assert file.is_dirty()

        file.mark_saved()

        assert not file.is_dirty()
        assert not file.is_modified
        assert file.original_content == "modified"


class TestEditorSession:
    """Test EditorSession dataclass."""

    def test_create_session(self):
        """Test creating a new editor session."""
        session = EditorSession(
            session_id="session123",
            user_id="user456",
        )

        assert session.session_id == "session123"
        assert session.user_id == "user456"
        assert len(session.files) == 0
        assert session.active_file_id is None

    def test_add_file(self):
        """Test adding file to session."""
        session = EditorSession(
            session_id="session123",
            user_id="user456",
        )

        file = EditorFile(
            file_id="test123",
            file_path="/test/file.yaml",
            content="test",
            original_content="test",
            mode=EditorMode.YAML,
            language="yaml",
        )

        session.add_file(file)

        assert len(session.files) == 1
        assert file in session.files.values()
        assert session.active_file_id == file.file_id

    def test_remove_file(self):
        """Test removing file from session."""
        session = EditorSession(
            session_id="session123",
            user_id="user456",
        )

        file = EditorFile(
            file_id="test123",
            file_path="/test/file.yaml",
            content="test",
            original_content="test",
            mode=EditorMode.YAML,
            language="yaml",
        )

        session.add_file(file)
        session.remove_file(file.file_id)

        assert len(session.files) == 0
        assert session.active_file_id is None


class TestSkillEditor:
    """Test SkillEditor class."""

    @pytest.mark.asyncio
    async def test_create_session(self, editor):
        """Test creating a new editing session."""
        session_id = await editor.create_session("user123")

        assert session_id is not None
        assert session_id in editor.sessions
        assert editor.sessions[session_id].user_id == "user123"

        # Check event was published
        editor.event_manager.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_session(self, editor, temp_dir):
        """Test closing an editing session."""
        # Create a test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("test content")

        # Create session
        session_id = await editor.create_session("user123")

        # Open file
        await editor.open_file(session_id, "test.yaml")

        # Close session
        result = await editor.close_session(session_id)

        assert result is True
        assert session_id not in editor.sessions

    @pytest.mark.asyncio
    async def test_close_nonexistent_session(self, editor):
        """Test closing a non-existent session."""
        result = await editor.close_session("nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_get_session(self, editor):
        """Test getting session by ID."""
        session_id = await editor.create_session("user123")

        session = editor.get_session(session_id)

        assert session is not None
        assert session.session_id == session_id

        # Test non-existent session
        session = editor.get_session("nonexistent")
        assert session is None

    def test_detect_mode(self, editor):
        """Test detecting editor mode from file extension."""
        assert editor._detect_mode("test.yaml") == EditorMode.YAML
        assert editor._detect_mode("test.json") == EditorMode.JSON
        assert editor._detect_mode("test.md") == EditorMode.MARKDOWN
        assert editor._detect_mode("test.py") == EditorMode.PYTHON
        assert editor._detect_mode("test.txt") == EditorMode.TEXT
        assert editor._detect_mode("test.unknown") == EditorMode.TEXT

    @pytest.mark.asyncio
    async def test_open_file(self, editor, temp_dir, sample_yaml_content):
        """Test opening a file."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text(sample_yaml_content)

        # Create session
        session_id = await editor.create_session("user123")

        # Open file
        file = await editor.open_file(session_id, "test.yaml")

        assert file is not None
        assert file.file_path == "test.yaml"
        assert file.mode == EditorMode.YAML
        assert file.content == sample_yaml_content

        # Check session has file
        session = editor.get_session(session_id)
        assert len(session.files) == 1

    @pytest.mark.asyncio
    async def test_open_nonexistent_file(self, editor):
        """Test opening a non-existent file."""
        session_id = await editor.create_session("user123")

        file = await editor.open_file(session_id, "nonexistent.yaml")

        assert file is None

    @pytest.mark.asyncio
    async def test_close_file(self, editor, temp_dir):
        """Test closing a file."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("test content")

        # Create session and open file
        session_id = await editor.create_session("user123")
        await editor.open_file(session_id, "test.yaml")

        # Get file ID
        session = editor.get_session(session_id)
        file_id = next(iter(session.files.keys()))

        # Close file
        result = await editor.close_file(session_id, file_id)

        assert result is True
        assert len(session.files) == 0

    @pytest.mark.asyncio
    async def test_save_file(self, editor, temp_dir):
        """Test saving a file."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("original content")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Modify content
        await editor.update_content(session_id, file.file_id, "modified content")

        # Save file
        result = await editor.save_file(session_id, file.file_id)

        assert result is True

        # Check file was saved
        test_file = temp_dir / "test.yaml"
        assert test_file.read_text() == "modified content"

        # Check file is no longer modified
        assert not file.is_modified

    @pytest.mark.asyncio
    async def test_update_content(self, editor, temp_dir):
        """Test updating file content."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("original")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Update content
        result = await editor.update_content(
            session_id,
            file.file_id,
            "new content",
            cursor_position=(10, 5),
        )

        assert result is True
        assert file.content == "new content"
        assert file.is_modified
        assert file.cursor_position == (10, 5)

    @pytest.mark.asyncio
    async def test_update_readonly_file(self, editor, temp_dir):
        """Test updating a read-only file."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("original")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Lock file as read-only
        editor.file_locks[file.file_path] = {
            "status": LockStatus.READONLY,
            "user_id": "other_user",
        }

        # Try to update
        result = await editor.update_content(
            session_id,
            file.file_id,
            "new content",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_validate_yaml_content(self, editor):
        """Test validating YAML content."""
        valid_yaml = "name: test\nversion: 1.0"
        is_valid, errors = await editor._validate_content(valid_yaml, EditorMode.YAML)

        assert is_valid
        assert len(errors) == 0

        # Test invalid YAML
        invalid_yaml = "name: test\n  invalid: indent"
        is_valid, errors = await editor._validate_content(invalid_yaml, EditorMode.YAML)

        assert not is_valid
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_json_content(self, editor):
        """Test validating JSON content."""
        valid_json = '{"name": "test", "version": "1.0"}'
        is_valid, errors = await editor._validate_content(valid_json, EditorMode.JSON)

        assert is_valid
        assert len(errors) == 0

        # Test invalid JSON
        invalid_json = '{"name": "test", "version":}'
        is_valid, errors = await editor._validate_content(invalid_json, EditorMode.JSON)

        assert not is_valid
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_validate_python_content(self, editor):
        """Test validating Python content."""
        valid_python = "def hello():\n    print('hello')"
        is_valid, errors = await editor._validate_content(valid_python, EditorMode.PYTHON)

        assert is_valid
        assert len(errors) == 0

        # Test invalid Python
        invalid_python = "def hello(\n    print('hello')"
        is_valid, errors = await editor._validate_content(invalid_python, EditorMode.PYTHON)

        assert not is_valid
        assert len(errors) > 0

    @pytest.mark.asyncio
    async def test_file_locking(self, editor, temp_dir):
        """Test file locking mechanism."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Check file is locked
        assert editor._get_file_lock(file.file_path) == LockStatus.LOCKED

        # Close file
        await editor.close_file(session_id, file.file_id)

        # Check file is unlocked
        assert editor._get_file_lock(file.file_path) == LockStatus.UNLOCKED

    @pytest.mark.asyncio
    async def test_add_remove_bookmark(self, editor, temp_dir):
        """Test adding and removing bookmarks."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("line1\nline2\nline3")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Add bookmark
        result = await editor.add_bookmark(session_id, file.file_id, 2)

        assert result is True
        assert 2 in file.bookmarks

        # Remove bookmark
        result = await editor.remove_bookmark(session_id, file.file_id, 2)

        assert result is True
        assert 2 not in file.bookmarks

    @pytest.mark.asyncio
    async def test_format_yaml_file(self, editor, temp_dir):
        """Test formatting YAML file."""
        # Create test file with unformatted YAML
        unformatted = "name: test\nversion: 1.0\ndependencies:\n  - click"
        test_file = temp_dir / "test.yaml"
        test_file.write_text(unformatted)

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Format file
        result = await editor.format_file(session_id, file.file_id)

        assert result is True

        # Check content is formatted
        formatted = yaml.safe_load(file.content)
        assert formatted["name"] == "test"
        assert formatted["version"] == "1.0"

    @pytest.mark.asyncio
    async def test_format_json_file(self, editor, temp_dir):
        """Test formatting JSON file."""
        # Create test file with unformatted JSON
        unformatted = '{"name": "test", "version": "1.0"}'
        test_file = temp_dir / "test.json"
        test_file.write_text(unformatted)

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.json")

        # Format file
        result = await editor.format_file(session_id, file.file_id)

        assert result is True

        # Check content is formatted (should have proper indentation)
        assert "\n" in file.content
        assert "  " in file.content

    @pytest.mark.asyncio
    async def test_export_file(self, editor, temp_dir):
        """Test exporting file in different formats."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("name: test")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Export as JSON
        exported = await editor.export_file(session_id, file.file_id, "json")

        assert exported is not None
        exported_data = json.loads(exported)
        assert "content" in exported_data
        assert "metadata" in exported_data

        # Export as YAML
        exported = await editor.export_file(session_id, file.file_id, "yaml")

        assert exported is not None

        # Export as plain text
        exported = await editor.export_file(session_id, file.file_id, "text")

        assert exported == "name: test"

    @pytest.mark.asyncio
    async def test_get_file_status(self, editor, temp_dir):
        """Test getting file status."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Get status
        status = await editor.get_file_status(session_id, file.file_id)

        assert status is not None
        assert status["file_id"] == file.file_id
        assert status["file_path"] == file.file_path
        assert status["mode"] == "yaml"
        assert status["is_modified"] is False
        assert status["lines"] == 1

    @pytest.mark.asyncio
    async def test_list_open_files(self, editor, temp_dir):
        """Test listing open files in session."""
        # Create test files
        test_file1 = temp_dir / "test1.yaml"
        test_file1.write_text("content1")
        test_file2 = temp_dir / "test2.json"
        test_file2.write_text("content2")

        # Create session and open files
        session_id = await editor.create_session("user123")
        await editor.open_file(session_id, "test1.yaml")
        await editor.open_file(session_id, "test2.json")

        # List files
        files = await editor.list_open_files(session_id)

        assert len(files) == 2
        assert any(f["file_path"] == "test1.yaml" for f in files)
        assert any(f["file_path"] == "test2.json" for f in files)

    @pytest.mark.asyncio
    async def test_get_editor_statistics(self, editor, temp_dir):
        """Test getting editor statistics."""
        # Create test files
        test_file1 = temp_dir / "test1.yaml"
        test_file1.write_text("line1\nline2")
        test_file2 = temp_dir / "test2.json"
        test_file2.write_text("content")

        # Create session and open files
        session_id = await editor.create_session("user123")
        await editor.open_file(session_id, "test1.yaml")
        await editor.open_file(session_id, "test2.json")

        # Get statistics
        stats = await editor.get_editor_statistics(session_id)

        assert stats is not None
        assert stats["total_files"] == 2
        assert stats["total_lines"] == 3
        assert stats["total_characters"] > 0

    def test_get_syntax_highlighting(self, editor):
        """Test getting syntax highlighting configuration."""
        # Test YAML
        config = asyncio.run(editor.get_syntax_highlighting(EditorMode.YAML))

        assert config["language"] == "yaml"
        assert "keywords" in config
        assert "lineNumbers" in config

        # Test Python
        config = asyncio.run(editor.get_syntax_highlighting(EditorMode.PYTHON))

        assert config["language"] == "python"
        assert "def" in config["keywords"]

    @pytest.mark.asyncio
    async def test_callbacks(self, editor, temp_dir):
        """Test editor callbacks."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create session and open file
        session_id = await editor.create_session("user123")
        file = await editor.open_file(session_id, "test.yaml")

        # Set up callbacks
        file_changed_called = False
        file_saved_called = False
        preview_update_called = False

        async def on_file_changed(sid, f):
            nonlocal file_changed_called
            file_changed_called = True

        async def on_file_saved(sid, f):
            nonlocal file_saved_called
            file_saved_called = True

        async def on_preview_update(sid, f):
            nonlocal preview_update_called
            preview_update_called = True

        editor.on_file_changed = on_file_changed
        editor.on_file_saved = on_file_saved
        editor.on_preview_update = on_preview_update

        # Update content
        await editor.update_content(session_id, file.file_id, "new content")

        # Wait a bit for callback
        await asyncio.sleep(0.1)

        # Check callbacks were called
        assert file_changed_called

        # Save file
        await editor.save_file(session_id, file.file_id)

        # Check save callback was called
        assert file_saved_called

    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(self, editor, temp_dir):
        """Test cleaning up inactive sessions."""
        # Create session
        session_id = await editor.create_session("user123")

        # Manually set last activity to past
        session = editor.get_session(session_id)
        session.last_activity = datetime.now() - timedelta(hours=25)

        # Clean up
        await editor.cleanup_inactive_sessions(max_age_hours=24)

        # Session should be removed
        assert session_id not in editor.sessions

    @pytest.mark.asyncio
    async def test_auto_save(self, editor, temp_dir):
        """Test auto-save functionality."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create session with auto-save enabled
        session_id = await editor.create_session(
            "user123",
            settings={"auto_save": True, "auto_save_interval": 1},
        )

        # Open file
        file = await editor.open_file(session_id, "test.yaml")

        # Update content
        await editor.update_content(session_id, file.file_id, "modified")

        # Wait for auto-save
        await asyncio.sleep(2)

        # Check file was saved
        assert not file.is_modified
        assert temp_dir / "test.yaml".read_text() == "modified"

    @pytest.mark.asyncio
    async def test_live_preview(self, editor, temp_dir):
        """Test live preview functionality."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create session with live preview enabled
        session_id = await editor.create_session(
            "user123",
            settings={"live_preview": True},
        )

        # Open file
        file = await editor.open_file(session_id, "test.yaml")

        # Set up preview callback
        preview_called = False

        async def on_preview(sid, f):
            nonlocal preview_called
            preview_called = True

        editor.on_preview_update = on_preview

        # Update content
        await editor.update_content(session_id, file.file_id, "new content")

        # Wait a bit for callback
        await asyncio.sleep(0.1)

        # Check preview callback was called
        assert preview_called

    @pytest.mark.asyncio
    async def test_file_lock_by_different_users(self, editor, temp_dir):
        """Test file locking with multiple users."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create two sessions
        session1_id = await editor.create_session("user1")
        session2_id = await editor.create_session("user2")

        # Open file in first session
        file1 = await editor.open_file(session1_id, "test.yaml")

        # Lock should be acquired by user1
        assert editor._get_file_lock(file1.file_path) == LockStatus.LOCKED

        # Try to open file in second session (should work but can't modify)
        file2 = await editor.open_file(session2_id, "test.yaml")

        # File is open but locked by user1
        assert file2 is not None

        # Update should fail for user2
        result = await editor.update_content(
            session2_id,
            file2.file_id,
            "new content",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_error_handling_invalid_content(self, editor, temp_dir):
        """Test error handling with invalid content."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("invalid: content\n  bad_indent")

        # Create session and open file
        session_id = await editor.create_session("user123")
        await editor.open_file(session_id, "test.yaml")

        # Try to save invalid content
        result = await editor.save_file(session_id, "test.yaml")

        # Should fail because content is invalid
        assert result is False

    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self, editor, temp_dir):
        """Test concurrent file operations."""
        # Create test file
        test_file = temp_dir / "test.yaml"
        test_file.write_text("content")

        # Create session
        session_id = await editor.create_session("user123")

        # Open file multiple times (should return same instance)
        file1 = await editor.open_file(session_id, "test.yaml")
        file2 = await editor.open_file(session_id, "test.yaml")

        assert file1.file_id == file2.file_id

        # Update content concurrently
        await asyncio.gather(
            editor.update_content(session_id, file1.file_id, "content1"),
            editor.update_content(session_id, file2.file_id, "content2"),
        )

        # Last write wins
        assert file1.content == file2.content
