"""Tests for SkillVersionManager.

This module contains comprehensive unit tests for the SkillVersionManager
version control functionality.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any

from app.skill.version_manager import (
    SkillVersionManager,
    VersionCommit,
    VersionTag,
    VersionBranch,
    VersionComparison,
    MergeConflict,
    VersionStatus,
    CompareType,
    MergeStrategy,
)
from app.skill.manager import SkillManager
from app.skill.event_manager import SkillEventManager


@pytest.fixture
def temp_dir():
    """Create temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def skill_manager():
    """Create mock skill manager."""
    manager = Mock(spec=SkillManager)
    manager.get_skill = AsyncMock(return_value={
        "id": "test-skill",
        "name": "Test Skill",
    })
    return manager


@pytest.fixture
def event_manager():
    """Create mock event manager."""
    manager = Mock(spec=SkillEventManager)
    manager.publish_event = AsyncMock(return_value="event_id")
    return manager


@pytest.fixture
def version_manager(skill_manager, event_manager, temp_dir):
    """Create SkillVersionManager instance for testing."""
    return SkillVersionManager(
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


class TestVersionCommit:
    """Test VersionCommit dataclass."""

    def test_create_commit(self):
        """Test creating a version commit."""
        commit = VersionCommit(
            commit_id="abc123",
            version="1.0.0",
            skill_id="test-skill",
            message="Initial commit",
            author="Test Author",
            file_hash="def456",
        )

        assert commit.commit_id == "abc123"
        assert commit.version == "1.0.0"
        assert commit.skill_id == "test-skill"
        assert commit.message == "Initial commit"
        assert commit.author == "Test Author"
        assert commit.file_hash == "def456"
        assert commit.timestamp is not None

    def test_commit_to_dict(self):
        """Test converting commit to dictionary."""
        commit = VersionCommit(
            commit_id="abc123",
            version="1.0.0",
            skill_id="test-skill",
            message="Initial commit",
            author="Test Author",
        )

        data = commit.to_dict()

        assert "commit_id" in data
        assert "version" in data
        assert "skill_id" in data
        assert "message" in data
        assert "author" in data
        assert "timestamp" in data
        assert isinstance(data["timestamp"], str)


class TestVersionTag:
    """Test VersionTag dataclass."""

    def test_create_tag(self):
        """Test creating a version tag."""
        tag = VersionTag(
            name="v1.0.0",
            version="1.0.0",
            message="Initial release",
            created_by="Test Author",
        )

        assert tag.name == "v1.0.0"
        assert tag.version == "1.0.0"
        assert tag.message == "Initial release"
        assert tag.created_by == "Test Author"
        assert tag.created_at is not None

    def test_tag_to_dict(self):
        """Test converting tag to dictionary."""
        tag = VersionTag(
            name="v1.0.0",
            version="1.0.0",
            message="Initial release",
        )

        data = tag.to_dict()

        assert "name" in data
        assert "version" in data
        assert "message" in data
        assert "created_at" in data
        assert isinstance(data["created_at"], str)


class TestVersionBranch:
    """Test VersionBranch dataclass."""

    def test_create_branch(self):
        """Test creating a version branch."""
        branch = VersionBranch(
            name="feature/new-ui",
            version="1.1.0",
            skill_id="test-skill",
            base_branch="main",
            created_by="Test Author",
        )

        assert branch.name == "feature/new-ui"
        assert branch.version == "1.1.0"
        assert branch.skill_id == "test-skill"
        assert branch.base_branch == "main"
        assert branch.created_by == "Test Author"
        assert branch.is_active is True
        assert branch.created_at is not None

    def test_branch_to_dict(self):
        """Test converting branch to dictionary."""
        branch = VersionBranch(
            name="feature/new-ui",
            version="1.1.0",
            skill_id="test-skill",
        )

        data = branch.to_dict()

        assert "name" in data
        assert "version" in data
        assert "skill_id" in data
        assert "created_at" in data
        assert isinstance(data["created_at"], str)


class TestVersionComparison:
    """Test VersionComparison dataclass."""

    def test_create_comparison(self):
        """Test creating a version comparison."""
        comparison = VersionComparison(
            from_version="1.0.0",
            to_version="1.1.0",
            compare_type=CompareType.UNIFIED,
            differences=[{"type": "diff", "content": "line1\n+line2"}],
            summary={"added_lines": 1},
        )

        assert comparison.from_version == "1.0.0"
        assert comparison.to_version == "1.1.0"
        assert comparison.compare_type == CompareType.UNIFIED
        assert len(comparison.differences) == 1
        assert comparison.summary["added_lines"] == 1
        assert comparison.created_at is not None

    def test_comparison_to_dict(self):
        """Test converting comparison to dictionary."""
        comparison = VersionComparison(
            from_version="1.0.0",
            to_version="1.1.0",
            compare_type=CompareType.UNIFIED,
        )

        data = comparison.to_dict()

        assert "from_version" in data
        assert "to_version" in data
        assert "compare_type" in data
        assert "created_at" in data
        assert isinstance(data["created_at"], str)


class TestMergeConflict:
    """Test MergeConflict dataclass."""

    def test_create_conflict(self):
        """Test creating a merge conflict."""
        conflict = MergeConflict(
            file_path="skill.yaml",
            conflict_type="content",
            from_content="old content",
            to_content="new content",
            merged_content="resolved content",
            resolution_strategy=MergeStrategy.MERGE,
        )

        assert conflict.file_path == "skill.yaml"
        assert conflict.conflict_type == "content"
        assert conflict.from_content == "old content"
        assert conflict.to_content == "new content"
        assert conflict.merged_content == "resolved content"
        assert conflict.resolution_strategy == MergeStrategy.MERGE

    def test_conflict_to_dict(self):
        """Test converting conflict to dictionary."""
        conflict = MergeConflict(
            file_path="skill.yaml",
            conflict_type="content",
            from_content="old",
            to_content="new",
        )

        data = conflict.to_dict()

        assert "file_path" in data
        assert "conflict_type" in data
        assert "from_content" in data
        assert "to_content" in data
        assert "merged_content" in data
        assert "resolution_strategy" in data


class TestSkillVersionManager:
    """Test SkillVersionManager class."""

    @pytest.mark.asyncio
    async def test_create_version(self, version_manager, temp_dir, sample_yaml_content):
        """Test creating a new version."""
        # Create test file
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        # Create version
        commit = await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
            status=VersionStatus.STABLE,
        )

        assert commit is not None
        assert commit.version == "1.0.0"
        assert commit.skill_id == "test-skill"
        assert commit.message == "Initial version"
        assert commit.author == "Test Author"
        assert commit.file_hash is not None

        # Check version was stored
        assert "test-skill" in version_manager.versions
        assert "1.0.0" in version_manager.versions["test-skill"]

        # Check event was published
        version_manager.event_manager.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_version_nonexistent_file(self, version_manager):
        """Test creating version for non-existent file."""
        commit = await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="nonexistent.yaml",
        )

        assert commit is None

    @pytest.mark.asyncio
    async def test_tag_version(self, version_manager, temp_dir, sample_yaml_content):
        """Test creating a version tag."""
        # Create test file and version
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Create tag
        tag = await version_manager.tag_version(
            skill_id="test-skill",
            version="1.0.0",
            tag_name="v1.0.0-stable",
            message="Stable release",
            created_by="Test Author",
        )

        assert tag is not None
        assert tag.name == "v1.0.0-stable"
        assert tag.version == "1.0.0"
        assert tag.message == "Stable release"
        assert tag.created_by == "Test Author"

        # Check tag was stored
        assert "test-skill" in version_manager.tags
        assert len(version_manager.tags["test-skill"]) == 1

    @pytest.mark.asyncio
    async def test_tag_nonexistent_version(self, version_manager):
        """Test tagging non-existent version."""
        tag = await version_manager.tag_version(
            skill_id="test-skill",
            version="1.0.0",
            tag_name="v1.0.0",
            message="Tag message",
        )

        assert tag is None

    @pytest.mark.asyncio
    async def test_create_branch(self, version_manager, temp_dir, sample_yaml_content):
        """Test creating a version branch."""
        # Create test file and version
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Create branch
        branch = await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/new-ui",
            created_by="Test Author",
            base_branch="main",
        )

        assert branch is not None
        assert branch.name == "feature/new-ui"
        assert branch.version == "1.0.0"
        assert branch.skill_id == "test-skill"
        assert branch.base_branch == "main"
        assert branch.created_by == "Test Author"
        assert branch.is_active is True

        # Check branch was stored
        assert "test-skill" in version_manager.branches
        assert len(version_manager.branches["test-skill"]) == 1

    @pytest.mark.asyncio
    async def test_create_branch_nonexistent_version(self, version_manager):
        """Test creating branch from non-existent version."""
        branch = await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/test",
        )

        assert branch is None

    @pytest.mark.asyncio
    async def test_compare_versions(self, version_manager, temp_dir):
        """Test comparing two versions."""
        # Create test files
        file1_content = "line1\nline2\nline3"
        file2_content = "line1\nline2\nline4"

        test_file1 = temp_dir / "test-skill.yaml"
        test_file1.write_text(file1_content)

        test_file2 = temp_dir / "test-skill.yaml"
        test_file2.write_text(file2_content)

        # Create versions
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Version 1",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.1.0",
            message="Version 2",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Compare versions
        comparison = await version_manager.compare_versions(
            skill_id="test-skill",
            from_version="1.0.0",
            to_version="1.1.0",
            compare_type=CompareType.UNIFIED,
        )

        assert comparison is not None
        assert comparison.from_version == "1.0.0"
        assert comparison.to_version == "1.1.0"
        assert comparison.compare_type == CompareType.UNIFIED
        assert len(comparison.differences) > 0
        assert "summary" in comparison.summary

        # Check event was published
        version_manager.event_manager.publish_event.assert_called()

    @pytest.mark.asyncio
    async def test_compare_nonexistent_versions(self, version_manager):
        """Test comparing non-existent versions."""
        comparison = await version_manager.compare_versions(
            skill_id="test-skill",
            from_version="1.0.0",
            to_version="1.1.0",
        )

        assert comparison is None

    @pytest.mark.asyncio
    async def test_rollback_version(self, version_manager, temp_dir, sample_yaml_content):
        """Test rolling back to a previous version."""
        # Create test file with initial content
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text("version: 1.0.0\ncontent: initial")

        # Create initial version
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Modify file
        test_file.write_text("version: 2.0.0\ncontent: modified")

        # Create new version
        await version_manager.create_version(
            skill_id="test-skill",
            version="2.0.0",
            message="Modified version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Rollback to version 1.0.0
        result = await version_manager.rollback_version(
            skill_id="test-skill",
            target_version="1.0.0",
            author="Test Author",
            reason="Bug found in version 2.0.0",
        )

        assert result is True

        # Check file was rolled back
        assert test_file.read_text() == "version: 1.0.0\ncontent: initial"

        # Check rollback version was created
        rollback_versions = [
            v for v in version_manager.versions["test-skill"].keys()
            if "rollback" in v
        ]
        assert len(rollback_versions) > 0

    @pytest.mark.asyncio
    async def test_rollback_nonexistent_version(self, version_manager):
        """Test rolling back to non-existent version."""
        result = await version_manager.rollback_version(
            skill_id="test-skill",
            target_version="1.0.0",
            author="Test Author",
            reason="Test rollback",
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_merge_branches(self, version_manager, temp_dir):
        """Test merging branches."""
        # Create test file with base content
        base_content = "name: test\nversion: 1.0.0"
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(base_content)

        # Create base version
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Base version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Create branch
        branch = await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/test",
        )

        assert branch is not None

        # Modify file for source branch
        test_file.write_text("name: test\nversion: 1.1.0\nfeature: new")

        # Create new version for source branch
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.1.0",
            message="Feature version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Merge branches
        success, conflicts = await version_manager.merge_branches(
            skill_id="test-skill",
            source_branch="feature/test",
            target_branch="main",
            author="Test Author",
            strategy=MergeStrategy.MERGE,
        )

        assert isinstance(success, bool)
        assert isinstance(conflicts, list)

        # Check merge commit was created
        merge_versions = [
            v for v in version_manager.versions["test-skill"].keys()
            if "merge" in v
        ]
        assert len(merge_versions) > 0

    @pytest.mark.asyncio
    async def test_get_version_history(self, version_manager, temp_dir, sample_yaml_content):
        """Test getting version history."""
        # Create test file
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        # Create multiple versions
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Version 1",
            author="Author1",
            file_path="test-skill.yaml",
        )

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.1.0",
            message="Version 2",
            author="Author2",
            file_path="test-skill.yaml",
        )

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.2.0",
            message="Version 3",
            author="Author1",
            file_path="test-skill.yaml",
        )

        # Get history
        history = await version_manager.get_version_history("test-skill")

        assert len(history) == 3
        assert history[0].version == "1.2.0"  # Newest first
        assert history[1].version == "1.1.0"
        assert history[2].version == "1.0.0"

        # Test limit
        history_limited = await version_manager.get_version_history(
            "test-skill",
            limit=2,
        )

        assert len(history_limited) == 2
        assert history_limited[0].version == "1.2.0"
        assert history_limited[1].version == "1.1.0"

    @pytest.mark.asyncio
    async def test_get_version_tags(self, version_manager, temp_dir, sample_yaml_content):
        """Test getting version tags."""
        # Create test file and version
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Create tags
        await version_manager.tag_version(
            skill_id="test-skill",
            version="1.0.0",
            tag_name="v1.0.0",
            message="Release 1",
        )

        await version_manager.tag_version(
            skill_id="test-skill",
            version="1.0.0",
            tag_name="v1.0.0-stable",
            message="Stable release",
        )

        # Get tags
        tags = await version_manager.get_version_tags("test-skill")

        assert len(tags) == 2
        assert any(tag.name == "v1.0.0" for tag in tags)
        assert any(tag.name == "v1.0.0-stable" for tag in tags)

    @pytest.mark.asyncio
    async def test_get_version_branches(self, version_manager, temp_dir, sample_yaml_content):
        """Test getting version branches."""
        # Create test file and version
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Create branches
        await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/branch1",
        )

        await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/branch2",
        )

        # Get branches
        branches = await version_manager.get_version_branches("test-skill")

        assert len(branches) == 2
        assert any(branch.name == "feature/branch1" for branch in branches)
        assert any(branch.name == "feature/branch2" for branch in branches)

    @pytest.mark.asyncio
    async def test_get_version_statistics(self, version_manager, temp_dir, sample_yaml_content):
        """Test getting version statistics."""
        # Create test file
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        # Create versions
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Version 1",
            author="Author1",
            file_path="test-skill.yaml",
            status=VersionStatus.STABLE,
        )

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.1.0",
            message="Version 2",
            author="Author2",
            file_path="test-skill.yaml",
            status=VersionStatus.DEVELOPMENT,
        )

        # Create tag
        await version_manager.tag_version(
            skill_id="test-skill",
            version="1.0.0",
            tag_name="v1.0.0",
            message="Release",
        )

        # Create branch
        await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/test",
        )

        # Get statistics
        stats = await version_manager.get_version_statistics("test-skill")

        assert stats is not None
        assert stats["skill_id"] == "test-skill"
        assert stats["total_versions"] == 2
        assert stats["total_tags"] == 1
        assert stats["total_branches"] == 1
        assert "status_distribution" in stats
        assert "author_statistics" in stats
        assert stats["latest_version"] == "1.1.0"

    @pytest.mark.asyncio
    async def test_export_version(self, version_manager, temp_dir, sample_yaml_content):
        """Test exporting version."""
        # Create test file
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        # Create version
        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Export as JSON
        export_json = await version_manager.export_version(
            "test-skill",
            "1.0.0",
            format_type="json",
        )

        assert export_json is not None
        export_data = json.loads(export_json)
        assert "version" in export_data
        assert "commit" in export_data
        assert "content" in export_data
        assert export_data["version"] == "1.0.0"

        # Export as YAML
        export_yaml = await version_manager.export_version(
            "test-skill",
            "1.0.0",
            format_type="yaml",
        )

        assert export_yaml is not None
        assert "# Version: 1.0.0" in export_yaml
        assert sample_yaml_content in export_yaml

        # Export as plain text
        export_text = await version_manager.export_version(
            "test-skill",
            "1.0.0",
            format_type="text",
        )

        assert export_text == sample_yaml_content

    @pytest.mark.asyncio
    async def test_export_nonexistent_version(self, version_manager):
        """Test exporting non-existent version."""
        export = await version_manager.export_version(
            "test-skill",
            "1.0.0",
        )

        assert export is None

    @pytest.mark.asyncio
    async def test_cleanup_old_versions(self, version_manager, temp_dir, sample_yaml_content):
        """Test cleaning up old versions."""
        # Create test file
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        # Create multiple versions
        for i in range(1, 11):
            await version_manager.create_version(
                skill_id="test-skill",
                version=f"1.{i}.0",
                message=f"Version {i}",
                author="Test Author",
                file_path="test-skill.yaml",
            )

        # Initially should have 10 versions
        assert len(version_manager.versions["test-skill"]) == 10

        # Clean up, keeping only 5
        cleaned = await version_manager.cleanup_old_versions(
            "test-skill",
            keep_count=5,
        )

        assert cleaned == 5
        assert len(version_manager.versions["test-skill"]) == 5

    @pytest.mark.asyncio
    async def test_cleanup_nonexistent_skill(self, version_manager):
        """Test cleaning up versions for non-existent skill."""
        cleaned = await version_manager.cleanup_old_versions(
            "nonexistent",
            keep_count=5,
        )

        assert cleaned == 0

    @pytest.mark.asyncio
    async def test_generate_commit_id(self, version_manager):
        """Test generating commit ID."""
        commit_id = version_manager._generate_commit_id(
            skill_id="test-skill",
            version="1.0.0",
            file_hash="abc123",
        )

        assert commit_id is not None
        assert len(commit_id) == 16
        assert isinstance(commit_id, str)

        # Different inputs should generate different IDs
        commit_id2 = version_manager._generate_commit_id(
            skill_id="test-skill",
            version="1.1.0",
            file_hash="def456",
        )

        assert commit_id != commit_id2

    @pytest.mark.asyncio
    async def test_merge_content_with_conflicts(self, version_manager):
        """Test merging content with conflicts."""
        source = "line1\nline2\nline3"
        target = "line1\nmodified\nline3"

        conflicts = []

        merged = await version_manager._merge_content(
            source,
            target,
            conflicts,
        )

        assert merged is not None
        assert len(conflicts) > 0
        assert isinstance(conflicts[0], MergeConflict)

    @pytest.mark.asyncio
    async def test_cache_version(self, version_manager):
        """Test caching version content."""
        content = "test content"

        await version_manager._cache_version(
            skill_id="test-skill",
            version="1.0.0",
            content=content,
        )

        assert "test-skill" in version_manager.version_cache
        assert "1.0.0" in version_manager.version_cache["test-skill"]
        assert version_manager.version_cache["test-skill"]["1.0.0"] == content

    @pytest.mark.asyncio
    async def test_get_version_content_from_cache(self, version_manager):
        """Test getting version content from cache."""
        content = "cached content"

        # Cache content
        await version_manager._cache_version(
            skill_id="test-skill",
            version="1.0.0",
            content=content,
        )

        # Retrieve from cache
        retrieved = await version_manager._get_version_content(
            "test-skill",
            "1.0.0",
        )

        assert retrieved == content

    @pytest.mark.asyncio
    async def test_get_version_content_from_file(self, version_manager, temp_dir):
        """Test getting version content from file system."""
        # Create version in manager (simulated)
        version_manager.versions["test-skill"] = {
            "1.0.0": VersionCommit(
                commit_id="abc123",
                version="1.0.0",
                skill_id="test-skill",
                message="Test",
                author="Test",
                changes={"file_path": "test-skill.yaml"},
            )
        }

        # Create file
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text("file content")

        # Retrieve from file
        content = await version_manager._get_version_content(
            "test-skill",
            "1.0.0",
        )

        assert content == "file content"

    @pytest.mark.asyncio
    async def test_get_branch_version(self, version_manager, temp_dir, sample_yaml_content):
        """Test getting branch version."""
        # Create test file and version
        test_file = temp_dir / "test-skill.yaml"
        test_file.write_text(sample_yaml_content)

        await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )

        # Create branch
        branch = await version_manager.create_branch(
            skill_id="test-skill",
            version="1.0.0",
            branch_name="feature/test",
        )

        # Get branch version
        retrieved = await version_manager._get_branch_version(
            "test-skill",
            "feature/test",
        )

        assert retrieved is not None
        assert retrieved.name == "feature/test"
        assert retrieved.version == "1.0.0"

    @pytest.mark.asyncio
    async def test_version_status_enum(self):
        """Test VersionStatus enum values."""
        assert VersionStatus.DRAFT.value == "draft"
        assert VersionStatus.DEVELOPMENT.value == "development"
        assert VersionStatus.STABLE.value == "stable"
        assert VersionStatus.DEPRECATED.value == "deprecated"
        assert VersionStatus.ARCHIVED.value == "archived"

    @pytest.mark.asyncio
    async def test_compare_type_enum(self):
        """Test CompareType enum values."""
        assert CompareType.UNIFIED.value == "unified"
        assert CompareType.SIDE_BY_SIDE.value == "side_by_side"
        assert CompareType.INLINE.value == "inline"

    @pytest.mark.asyncio
    async def test_merge_strategy_enum(self):
        """Test MergeStrategy enum values."""
        assert MergeStrategy.MERGE.value == "merge"
        assert MergeStrategy.REPLACE.value == "replace"
        assert MergeStrategy.KEEP_BOTH.value == "keep_both"
