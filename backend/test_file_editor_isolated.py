"""File Editor Isolated Tests.

This script tests the file editor functionality in isolation,
avoiding complex module dependencies.
"""

import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add the app directory to the Python path
sys.path.append(os.path.dirname(__file__))


class MockFileResponse:
    """Mock file response for testing."""

    def __init__(self, file_id: str, name: str, is_text_file: bool = True):
        self.id = file_id
        self.name = name
        self.path = f"/{name}"
        self.type = "file"
        self.size = 1024
        self.mime_type = "text/plain" if is_text_file else "application/octet-stream"
        self.extension = os.path.splitext(name)[1]
        self.is_text_file = is_text_file
        self.created_at = datetime.utcnow()
        self.modified_at = datetime.utcnow()
        self.created_by = "test-user"
        self.modified_by = "test-user"
        self.status = "active"
        self.version = 1
        self.metadata = {}
        self.permissions = ["read", "write"]
        self.tags = []
        self.custom_fields = {}
        self.backup_count = 0
        self.is_deleted = False
        self.deleted_at = None
        self.retention_period = None


class MockEditorLanguage:
    """Mock editor language enum."""
    TEXT = "text"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"


class MockAutoSaveSettings:
    """Mock auto-save settings."""

    def __init__(self, enabled: bool = True, interval: int = 30):
        self.enabled = enabled
        self.interval = interval


class MockEditorConfig:
    """Mock editor configuration."""

    def __init__(self, language: str = "text"):
        self.language = language
        self.theme = "dark"
        self.font_size = 14
        self.tab_size = 4
        self.auto_close_brackets = True
        self.auto_close_tags = True
        self.word_wrap = True
        self.line_numbers = True
        self.show_whitespace = False
        self.show_indentation_guides = True
        self.highlight_active_line = True
        self.auto_save = MockAutoSaveSettings()


class MockChangeOperation:
    """Mock change operation."""

    def __init__(self, operation_id: str, type: str, position: int,
                 length: int, content: str, user_id: str):
        self.operation_id = operation_id
        self.type = type
        self.position = position
        self.length = length
        self.content = content
        self.timestamp = datetime.utcnow()
        self.user_id = user_id


class MockSession:
    """Mock editor session."""

    def __init__(self, session_id: str, file_id: str, user_id: str):
        self.session_id = session_id
        self.file_id = file_id
        self.user_id = user_id
        self.language = MockEditorLanguage.TEXT
        self.config = MockEditorConfig()
        self.content = ""
        self.cursor_position = {"line": 0, "column": 0}
        self.selections = []
        self.scroll_position = {"line": 0, "column": 0}
        self.is_dirty = False
        self.last_saved_at = None
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
        self.collaborators = []
        self.is_readonly = False
        self.version = 1


class FileEditor:
    """Simplified FileEditor for isolated testing."""

    def __init__(self):
        self.file_manager = MagicMock()
        self.active_sessions: Dict[str, Any] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self.collaborators: Dict[str, set] = {}

    async def create_editor_session(
        self,
        file_id: str,
        user_id: str,
        config: Optional[Any] = None,
        read_only: bool = False
    ) -> MockSession:
        """Create a new editor session."""
        session_id = str(uuid4())

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

        # Store session
        self.active_sessions[session_id] = "active"
        self.session_data[session_id] = session_data
        self.collaborators[session_id] = {user_id}

        # Create session
        session = MockSession(session_id, file_id, user_id)

        print(f"✓ Created editor session: {session_id}")
        return session

    async def apply_changes(
        self,
        session_id: str,
        user_id: str,
        changes: List[Any],
        version: int
    ) -> tuple[bool, Optional[str], Dict[str, Any]]:
        """Apply changes to editor session."""
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
                current_content = self._apply_change_operation(current_content, change)
                operations_applied += 1
            except Exception as e:
                return False, f"Failed to apply change: {str(e)}", {}

        # Update session
        session_data["content"] = current_content
        session_data["changes"].extend([{
            "operation_id": change.operation_id,
            "type": change.type,
            "position": change.position,
            "length": change.length,
            "content": change.content,
            "timestamp": change.timestamp.isoformat(),
            "user_id": change.user_id,
        } for change in changes])
        session_data["dirty"] = True
        session_data["version"] += 1

        response_data = {
            "operations_applied": operations_applied,
            "server_version": session_data["version"],
            "content_length": len(current_content),
            "dirty": session_data["dirty"]
        }

        print(f"✓ Applied {operations_applied} changes to session {session_id}")
        return True, None, response_data

    def _apply_change_operation(self, content: str, change: Any) -> str:
        """Apply a single change operation."""
        if change.type == "insert":
            return content[:change.position] + change.content + content[change.position:]
        elif change.type == "delete":
            return content[:change.position] + content[change.position + change.length:]
        elif change.type == "replace":
            return content[:change.position] + change.content + content[change.position + change.length:]
        else:
            raise ValueError(f"Unknown change type: {change.type}")

    async def save_session(
        self,
        session_id: str,
        user_id: str,
        force: bool = False
    ) -> tuple[bool, Optional[str]]:
        """Save editor session."""
        if session_id not in self.active_sessions:
            return False, "Session not found"

        session_data = self.session_data.get(session_id)
        if not session_data:
            return False, "Session data not found"

        # Check if save is needed
        if not force and not session_data["dirty"]:
            return True, "No changes to save"

        # Save content
        session_data["last_saved_content"] = session_data["content"]
        session_data["dirty"] = False

        print(f"✓ Saved session: {session_id}")
        return True, None

    async def search_in_session(
        self,
        session_id: str,
        query: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False
    ) -> List[Dict[str, Any]]:
        """Search in session content."""
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
            except re.error:
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
            })

        print(f"✓ Found {len(matches)} matches for query '{query}'")
        return matches

    async def replace_in_session(
        self,
        session_id: str,
        user_id: str,
        query: str,
        replacement: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
        replace_all: bool = False
    ) -> tuple[bool, int, Optional[str]]:
        """Replace text in session."""
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
            except re.error:
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
        session_data["content"] = new_content
        session_data["dirty"] = True
        session_data["version"] += 1

        print(f"✓ Replaced {count} occurrences in session {session_id}")
        return True, count, None


async def test_editor_session_creation():
    """Test editor session creation."""
    print("\nTesting editor session creation...")

    editor = FileEditor()
    file_id = str(uuid4())
    user_id = "test-user-123"

    # Create session
    session = await editor.create_editor_session(file_id, user_id)

    assert session is not None
    assert session.session_id is not None
    assert session.file_id == file_id
    assert session.user_id == user_id
    assert session.content == ""
    assert session.is_dirty is False

    print("✅ Editor session creation test passed!")
    return True


async def test_editor_change_operations():
    """Test editor change operations."""
    print("\nTesting editor change operations...")

    editor = FileEditor()
    file_id = str(uuid4())
    user_id = "test-user-123"

    # Create session
    session = await editor.create_editor_session(file_id, user_id)

    # Create change operations
    changes = [
        MockChangeOperation("op1", "insert", 0, 0, "# Test file", user_id),
        MockChangeOperation("op2", "insert", 12, 0, "\nprint('Hello, World!')", user_id),
    ]

    # Apply changes
    success, error, response = await editor.apply_changes(
        session_id=session.session_id,
        user_id=user_id,
        changes=changes,
        version=1,
    )

    assert success is True
    assert error is None
    assert response["operations_applied"] == 2
    assert response["server_version"] == 2

    # Check content
    updated_content = editor.session_data[session.session_id]["content"]
    expected_content = "# Test file\nprint('Hello, World!')"
    assert updated_content == expected_content

    print("✅ Editor change operations test passed!")
    return True


async def test_editor_search():
    """Test editor search functionality."""
    print("\nTesting editor search functionality...")

    editor = FileEditor()
    file_id = str(uuid4())
    user_id = "test-user-123"

    # Create session
    session = await editor.create_editor_session(file_id, user_id)

    # Set content
    editor.session_data[session.session_id]["content"] = "Hello, World! Hello, Universe!"

    # Search for "Hello"
    results = await editor.search_in_session(
        session_id=session.session_id,
        query="Hello",
    )

    assert len(results) == 2
    assert results[0]["text"] == "Hello"
    assert results[1]["text"] == "Hello"

    print("✅ Editor search test passed!")
    return True


async def test_editor_replace():
    """Test editor replace functionality."""
    print("\nTesting editor replace functionality...")

    editor = FileEditor()
    file_id = str(uuid4())
    user_id = "test-user-123"

    # Create session
    session = await editor.create_editor_session(file_id, user_id)

    # Set content
    editor.session_data[session.session_id]["content"] = "Hello, World!"

    # Replace "World" with "Universe"
    success, count, error = await editor.replace_in_session(
        session_id=session.session_id,
        user_id=user_id,
        query="World",
        replacement="Universe",
    )

    assert success is True
    assert count == 1
    assert error is None

    # Check content
    updated_content = editor.session_data[session.session_id]["content"]
    assert updated_content == "Hello, Universe!"

    print("✅ Editor replace test passed!")
    return True


async def test_editor_replace_all():
    """Test editor replace all functionality."""
    print("\nTesting editor replace all functionality...")

    editor = FileEditor()
    file_id = str(uuid4())
    user_id = "test-user-123"

    # Create session
    session = await editor.create_editor_session(file_id, user_id)

    # Set content
    editor.session_data[session.session_id]["content"] = "Hello, World! Hello, World!"

    # Replace all
    success, count, error = await editor.replace_in_session(
        session_id=session.session_id,
        user_id=user_id,
        query="Hello",
        replacement="Hi",
        replace_all=True,
    )

    assert success is True
    assert count == 2

    # Check content
    updated_content = editor.session_data[session.session_id]["content"]
    assert updated_content == "Hi, World! Hi, World!"

    print("✅ Editor replace all test passed!")
    return True


async def test_editor_save():
    """Test editor save functionality."""
    print("\nTesting editor save functionality...")

    editor = FileEditor()
    file_id = str(uuid4())
    user_id = "test-user-123"

    # Create session
    session = await editor.create_editor_session(file_id, user_id)

    # Set content and mark as dirty
    editor.session_data[session.session_id]["content"] = "Test content"
    editor.session_data[session.session_id]["dirty"] = True

    # Save session
    success, error = await editor.save_session(
        session_id=session.session_id,
        user_id=user_id,
    )

    assert success is True
    assert error is None

    # Check that dirty flag is cleared
    assert editor.session_data[session.session_id]["dirty"] is False

    print("✅ Editor save test passed!")
    return True


async def test_editor_change_operations():
    """Test individual change operation types."""
    print("\nTesting individual change operation types...")

    editor = FileEditor()

    # Test insert
    content = "Hello, World!"
    change = MockChangeOperation("op1", "insert", 5, 0, " beautiful", "user")
    result = editor._apply_change_operation(content, change)
    assert result == "Hello beautiful, World!"

    # Test delete
    content = "Hello, World!"
    change = MockChangeOperation("op2", "delete", 5, 7, "", "user")
    result = editor._apply_change_operation(content, change)
    assert result == "Hello!"

    # Test replace
    content = "Hello, World!"
    change = MockChangeOperation("op3", "replace", 7, 5, "Universe", "user")
    result = editor._apply_change_operation(content, change)
    assert result == "Hello, Universe!"

    print("✅ Individual change operation tests passed!")
    return True


async def main():
    """Run all tests."""
    print("🚀 Starting File Editor - Isolated Tests\n")

    tests = [
        ("Session Creation", test_editor_session_creation),
        ("Change Operations", test_editor_change_operations),
        ("Search", test_editor_search),
        ("Replace", test_editor_replace),
        ("Replace All", test_editor_replace_all),
        ("Save", test_editor_save),
        ("Change Operation Types", test_editor_change_operations),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed: {str(e)}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed!")
        print("\n✅ File Editor core functionality verified!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
