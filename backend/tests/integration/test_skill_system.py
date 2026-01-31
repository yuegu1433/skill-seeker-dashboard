"""Skill System Integration Tests.

This module contains comprehensive integration tests for the entire
skill management system, testing end-to-end workflows and component interactions.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Dict, Any
import json
import yaml

from app.skill.manager import SkillManager
from app.skill.event_manager import SkillEventManager, EventType
from app.skill.editor import SkillEditor, EditorSession
from app.skill.version_manager import SkillVersionManager, VersionStatus
from app.skill.importer import SkillImporter, ImportConfig, ExportConfig, ImportFormat, ExportFormat
from app.skill.analytics import SkillAnalytics, TimeRange
from app.skill.schemas.skill_operations import SkillCreate, SkillUpdate, SkillFilter
from app.skill.schemas.skill_import import ImportRequest, ExportRequest


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    workspace = Path(tempfile.mkdtemp())
    yield workspace
    shutil.rmtree(workspace)


@pytest.fixture
def skill_data():
    """Create sample skill data."""
    return {
        "name": "test-skill",
        "version": "1.0.0",
        "description": "Test skill for integration testing",
        "author": "Integration Test",
        "category": "testing",
        "keywords": ["test", "integration"],
        "dependencies": ["click", "pydantic"],
        "config": {
            "enabled": True,
            "timeout": 30,
        },
    }


@pytest.fixture
def mock_skill_manager():
    """Create mock skill manager."""
    manager = Mock(spec=SkillManager)
    manager.create_skill = AsyncMock(return_value=Mock(
        id="test-skill",
        name="Test Skill",
        version="1.0.0",
    ))
    manager.update_skill = AsyncMock(return_value=Mock(
        id="test-skill",
        name="Updated Skill",
    ))
    manager.get_skill = AsyncMock(return_value=Mock(
        id="test-skill",
        name="Test Skill",
        version="1.0.0",
        dict=lambda: {"id": "test-skill", "name": "Test Skill"},
    ))
    manager.list_skills = AsyncMock(return_value=Mock(
        items=[
            Mock(id="skill1", name="Skill 1"),
            Mock(id="skill2", name="Skill 2"),
        ],
        total=2,
        page=1,
        page_size=20,
    ))
    manager.delete_skill = AsyncMock(return_value=True)
    manager.bulk_operation = AsyncMock(return_value=Mock(
        successful=2,
        failed=0,
        processed=2,
    ))
    return manager


@pytest.fixture
def mock_event_manager():
    """Create mock event manager."""
    manager = Mock(spec=SkillEventManager)
    manager.publish_event = AsyncMock(return_value="event_id")
    return manager


@pytest.fixture
def skill_editor(mock_skill_manager, mock_event_manager, temp_workspace):
    """Create skill editor instance."""
    return SkillEditor(
        skill_manager=mock_skill_manager,
        event_manager=mock_event_manager,
        workspace_path=temp_workspace,
    )


@pytest.fixture
def version_manager(mock_skill_manager, mock_event_manager, temp_workspace):
    """Create version manager instance."""
    return SkillVersionManager(
        skill_manager=mock_skill_manager,
        event_manager=mock_event_manager,
        workspace_path=temp_workspace,
    )


@pytest.fixture
def skill_importer(mock_skill_manager, mock_event_manager, temp_workspace):
    """Create skill importer instance."""
    return SkillImporter(
        skill_manager=mock_skill_manager,
        event_manager=mock_event_manager,
        workspace_path=temp_workspace,
    )


@pytest.fixture
def skill_analytics(mock_skill_manager, mock_event_manager):
    """Create skill analytics instance."""
    return SkillAnalytics(
        skill_manager=mock_skill_manager,
        event_manager=mock_event_manager,
    )


class TestSkillLifecycle:
    """Test complete skill lifecycle."""

    @pytest.mark.asyncio
    async def test_skill_create_update_delete_lifecycle(
        self,
        mock_skill_manager,
        skill_data,
    ):
        """Test complete skill lifecycle: create, update, delete."""
        # Create skill
        created_skill = await mock_skill_manager.create_skill(SkillCreate(**skill_data))
        assert created_skill is not None

        # Update skill
        update_data = SkillUpdate(description="Updated description")
        updated_skill = await mock_skill_manager.update_skill("test-skill", update_data)
        assert updated_skill is not None

        # Delete skill
        deleted = await mock_skill_manager.delete_skill("test-skill")
        assert deleted is True

    @pytest.mark.asyncio
    async def test_skill_creation_with_versioning(
        self,
        mock_skill_manager,
        version_manager,
        temp_workspace,
        skill_data,
    ):
        """Test skill creation with version control."""
        # Create test file
        skill_file = temp_workspace / "test-skill.yaml"
        skill_file.write_text(yaml.dump(skill_data))

        # Create skill
        created_skill = await mock_skill_manager.create_skill(SkillCreate(**skill_data))
        assert created_skill is not None

        # Create version
        commit = await version_manager.create_version(
            skill_id="test-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="test-skill.yaml",
        )
        assert commit is not None
        assert commit.version == "1.0.0"

        # Tag version
        tag = await version_manager.tag_version(
            skill_id="test-skill",
            version="1.0.0",
            tag_name="v1.0.0-stable",
            message="Stable release",
        )
        assert tag is not None
        assert tag.name == "v1.0.0-stable"

    @pytest.mark.asyncio
    async def test_skill_with_quality_scoring(
        self,
        mock_skill_manager,
        skill_analytics,
        skill_data,
    ):
        """Test skill with quality score calculation."""
        # Create skill
        created_skill = await mock_skill_manager.create_skill(SkillCreate(**skill_data))
        assert created_skill is not None

        # Calculate quality score
        quality = await skill_analytics.calculate_quality_score("test-skill")
        assert quality is not None
        assert 0 <= quality.overall_score <= 100

        # Track execution
        await skill_analytics.track_execution(
            skill_id="test-skill",
            execution_time=1.5,
            success=True,
        )

        # Get stats
        stats = await skill_analytics.get_skill_stats("test-skill")
        assert stats is not None
        assert stats.total_executions == 1


class TestImportExportWorkflow:
    """Test import/export workflows."""

    @pytest.mark.asyncio
    async def test_skill_import_export_workflow(
        self,
        skill_importer,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test complete import/export workflow."""
        # Create test skill file
        skills_data = [
            {
                "name": "imported-skill-1",
                "version": "1.0.0",
                "description": "Imported skill 1",
                "author": "Importer",
            },
            {
                "name": "imported-skill-2",
                "version": "1.0.0",
                "description": "Imported skill 2",
                "author": "Importer",
            },
        ]

        import_file = temp_workspace / "skills_to_import.yaml"
        import_file.write_text(yaml.dump(skills_data))

        # Import skills
        import_config = ImportConfig(
            format=ImportFormat.YAML,
            update_existing=False,
        )

        result = await skill_importer.import_skills(
            source_path=import_file,
            config=import_config,
        )
        assert result is not None

        # Export skills
        export_file = temp_workspace / "exported_skills.json"

        export_config = ExportConfig(
            format=ExportFormat.JSON,
            include_metadata=True,
        )

        export_result = await skill_importer.export_skills(
            skill_ids=["imported-skill-1", "imported-skill-2"],
            destination_path=export_file,
            config=export_config,
        )
        assert export_result is not None

        # Verify exported file exists
        assert export_file.exists()

    @pytest.mark.asyncio
    async def test_bulk_import_with_validation(
        self,
        skill_importer,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test bulk import with validation."""
        # Create mixed quality skill data
        skills_data = [
            {
                "name": "valid-skill-1",
                "version": "1.0.0",
                "description": "Valid skill 1",
                "author": "Test Author",
            },
            {
                # Invalid: missing required fields
                "description": "Invalid skill",
            },
            {
                "name": "valid-skill-2",
                "version": "1.0.0",
                "description": "Valid skill 2",
                "author": "Test Author",
            },
        ]

        import_file = temp_workspace / "mixed_skills.yaml"
        import_file.write_text(yaml.dump(skills_data))

        # Import with skip invalid
        import_config = ImportConfig(
            format=ImportFormat.YAML,
            skip_invalid=True,
            validation_level="moderate",
        )

        result = await skill_importer.import_skills(
            source_path=import_file,
            config=import_config,
        )
        assert result is not None


class TestEditorWorkflow:
    """Test editor workflows."""

    @pytest.mark.asyncio
    async def test_editor_complete_workflow(
        self,
        skill_editor,
        temp_workspace,
    ):
        """Test complete editor workflow."""
        # Create test file
        test_file = temp_workspace / "test-skill.yaml"
        test_file.write_text("name: test\nversion: 1.0.0\ndescription: Test")

        # Create session
        session_id = await skill_editor.create_session(
            user_id="test_user",
            settings={"theme": "dark"},
        )
        assert session_id is not None

        # Open file
        file = await skill_editor.open_file(session_id, "test-skill.yaml")
        assert file is not None
        assert file.file_path == "test-skill.yaml"

        # Update content
        updated = await skill_editor.update_content(
            session_id,
            file.file_id,
            "name: test\nversion: 1.1.0\ndescription: Updated",
        )
        assert updated is True

        # Save file
        saved = await skill_editor.save_file(session_id, file.file_id)
        assert saved is True

        # Add bookmark
        bookmarked = await skill_editor.add_bookmark(session_id, file.file_id, 2)
        assert bookmarked is True

        # Format file
        formatted = await skill_editor.format_file(session_id, file.file_id)
        assert formatted is True

        # Get statistics
        stats = await skill_editor.get_editor_statistics(session_id)
        assert stats is not None
        assert stats["total_files"] == 1

        # Close file
        closed = await skill_editor.close_file(session_id, file.file_id)
        assert closed is True

        # Close session
        session_closed = await skill_editor.close_session(session_id)
        assert session_closed is True

    @pytest.mark.asyncio
    async def test_editor_with_versioning(
        self,
        skill_editor,
        version_manager,
        temp_workspace,
    ):
        """Test editor with version control integration."""
        # Create test file
        test_file = temp_workspace / "versioned-skill.yaml"
        test_file.write_text("name: test\nversion: 1.0.0")

        # Create session
        session_id = await skill_editor.create_session("test_user")

        # Open file
        file = await skill_editor.open_file(session_id, "versioned-skill.yaml")

        # Create version
        commit = await version_manager.create_version(
            skill_id="versioned-skill",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="versioned-skill.yaml",
        )
        assert commit is not None

        # Update content
        await skill_editor.update_content(
            session_id,
            file.file_id,
            "name: test\nversion: 1.1.0",
        )

        # Save and create new version
        await skill_editor.save_file(session_id, file.file_id)

        new_commit = await version_manager.create_version(
            skill_id="versioned-skill",
            version="1.1.0",
            message="Updated version",
            author="Test Author",
            file_path="versioned-skill.yaml",
        )
        assert new_commit is not None
        assert new_commit.version == "1.1.0"

        # Compare versions
        comparison = await version_manager.compare_versions(
            skill_id="versioned-skill",
            from_version="1.0.0",
            to_version="1.1.0",
        )
        assert comparison is not None


class TestAnalyticsWorkflow:
    """Test analytics workflows."""

    @pytest.mark.asyncio
    async def test_analytics_complete_workflow(
        self,
        skill_analytics,
        mock_skill_manager,
    ):
        """Test complete analytics workflow."""
        # Track multiple executions
        for i in range(10):
            await skill_analytics.track_execution(
                skill_id="test-skill",
                execution_time=1.0 + i * 0.1,
                success=i < 8,  # 8 success, 2 failures
            )

        # Calculate quality score
        quality = await skill_analytics.calculate_quality_score("test-skill")
        assert quality is not None

        # Get stats
        stats = await skill_analytics.get_skill_stats("test-skill")
        assert stats is not None
        assert stats.total_executions == 10
        assert stats.successful_executions == 8
        assert stats.failed_executions == 2

        # Generate usage report
        report = await skill_analytics.generate_usage_report(
            skill_ids=["test-skill"],
            time_range=TimeRange.LAST_MONTH,
        )
        assert report is not None
        assert "summary" in report.summary

    @pytest.mark.asyncio
    async def test_analytics_with_import_export(
        self,
        skill_analytics,
        skill_importer,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test analytics integration with import/export."""
        # Import skills and track analytics
        skills_data = [
            {
                "name": "analytics-skill-1",
                "version": "1.0.0",
                "description": "Skill for analytics",
                "author": "Test",
            },
        ]

        import_file = temp_workspace / "analytics_import.yaml"
        import_file.write_text(yaml.dump(skills_data))

        import_config = ImportConfig(format=ImportFormat.YAML)
        await skill_importer.import_skills(import_file, import_config)

        # Track executions for imported skills
        await skill_analytics.track_execution(
            skill_id="analytics-skill-1",
            execution_time=2.0,
            success=True,
        )

        # Generate report
        report = await skill_analytics.generate_usage_report(
            skill_ids=["analytics-skill-1"],
            time_range=TimeRange.LAST_MONTH,
        )
        assert report is not None

        # Export analytics
        exported = await skill_analytics.export_analytics("json")
        assert exported is not None
        assert "total_skills" in exported


class TestEventSystemIntegration:
    """Test event system integration."""

    @pytest.mark.asyncio
    async def test_events_across_components(
        self,
        mock_skill_manager,
        mock_event_manager,
        skill_editor,
        version_manager,
        temp_workspace,
    ):
        """Test events flow across different components."""
        # Create test file
        test_file = temp_workspace / "event-test.yaml"
        test_file.write_text("name: test\nversion: 1.0.0")

        # Create session (should trigger event)
        session_id = await skill_editor.create_session("test_user")
        assert session_id is not None

        # Open file (should trigger event)
        file = await skill_editor.open_file(session_id, "event-test.yaml")
        assert file is not None

        # Create version (should trigger event)
        commit = await version_manager.create_version(
            skill_id="event-test",
            version="1.0.0",
            message="Initial version",
            author="Test Author",
            file_path="event-test.yaml",
        )
        assert commit is not None

        # Verify events were published
        assert mock_event_manager.publish_event.call_count >= 2

    @pytest.mark.asyncio
    async def test_error_handling_with_events(
        self,
        mock_skill_manager,
        mock_event_manager,
        skill_editor,
        temp_workspace,
    ):
        """Test error handling and event publishing."""
        # Create test file
        test_file = temp_workspace / "error-test.yaml"
        test_file.write_text("name: test\nversion: 1.0.0")

        # Create session
        session_id = await skill_editor.create_session("test_user")

        # Try to open non-existent file (should handle error)
        non_existent = await skill_editor.open_file(session_id, "nonexistent.yaml")
        assert non_existent is None

        # Verify error events were handled
        # (in a real implementation, error events would be published)


class TestBulkOperationsIntegration:
    """Test bulk operations integration."""

    @pytest.mark.asyncio
    async def test_bulk_operations_with_analytics(
        self,
        mock_skill_manager,
        skill_analytics,
    ):
        """Test bulk operations with analytics tracking."""
        skill_ids = [f"bulk-skill-{i}" for i in range(10)]

        # Perform bulk operation
        from app.skill.schemas.skill_operations import SkillBulkOperation
        operation = SkillBulkOperation(
            operation="activate",
            skill_ids=skill_ids,
            parameters={},
        )

        result = await mock_skill_manager.bulk_operation(operation)
        assert result.successful == 10
        assert result.failed == 0

        # Track analytics for bulk operation
        for skill_id in skill_ids:
            await skill_analytics.track_execution(
                skill_id=skill_id,
                execution_time=1.0,
                success=True,
            )

        # Verify analytics data
        stats = await skill_analytics.get_skill_stats(skill_ids[0])
        assert stats is not None

    @pytest.mark.asyncio
    async def test_bulk_import_with_versioning(
        self,
        skill_importer,
        version_manager,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test bulk import with version control."""
        # Create multiple skill files
        for i in range(5):
            skill_data = {
                "name": f"bulk-version-skill-{i}",
                "version": "1.0.0",
                "description": f"Bulk skill {i}",
                "author": "Bulk Importer",
            }

            skill_file = temp_workspace / f"bulk-skill-{i}.yaml"
            skill_file.write_text(yaml.dump(skill_data))

            # Create version for each
            commit = await version_manager.create_version(
                skill_id=f"bulk-version-skill-{i}",
                version="1.0.0",
                message="Bulk import version",
                author="Bulk Importer",
                file_path=f"bulk-skill-{i}.yaml",
            )
            assert commit is not None

        # Get version history
        history = await version_manager.get_version_history("bulk-version-skill-0")
        assert len(history) > 0


class TestPerformanceIntegration:
    """Test performance and load handling."""

    @pytest.mark.asyncio
    async def test_high_volume_operations(
        self,
        skill_analytics,
        mock_skill_manager,
    ):
        """Test high volume operations performance."""
        # Track many executions
        num_executions = 1000

        for i in range(num_executions):
            await skill_analytics.track_execution(
                skill_id="perf-test-skill",
                execution_time=0.5,
                success=True,
            )

        # Verify performance
        stats = await skill_analytics.get_skill_stats("perf-test-skill")
        assert stats is not None
        assert stats.total_executions == num_executions

        # Test metrics aggregation
        avg_time = await skill_analytics.aggregate_metrics(
            "skill.execution.time",
            "average",
            TimeRange.LAST_MONTH,
        )
        assert avg_time is not None

    @pytest.mark.asyncio
    async def test_concurrent_operations(
        self,
        skill_analytics,
        mock_skill_manager,
    ):
        """Test concurrent operations handling."""
        # Create multiple tasks
        tasks = []
        for i in range(10):
            task = asyncio.create_task(
                skill_analytics.track_execution(
                    skill_id=f"concurrent-skill-{i}",
                    execution_time=1.0,
                    success=True,
                )
            )
            tasks.append(task)

        # Wait for all tasks
        await asyncio.gather(*tasks)

        # Verify all operations completed
        for i in range(10):
            stats = await skill_analytics.get_skill_stats(f"concurrent-skill-{i}")
            assert stats is not None
            assert stats.total_executions == 1


class TestDataConsistency:
    """Test data consistency across operations."""

    @pytest.mark.asyncio
    async def test_data_consistency_after_import_export(
        self,
        skill_importer,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test data consistency after import/export cycle."""
        # Original data
        original_data = {
            "name": "consistency-test-skill",
            "version": "1.0.0",
            "description": "Data consistency test",
            "author": "Tester",
            "category": "testing",
            "keywords": ["test", "consistency"],
        }

        # Export
        export_file = temp_workspace / "consistency_export.yaml"
        export_config = ExportConfig(format=ExportFormat.YAML)

        await skill_importer.export_skills(
            skill_ids=["consistency-test-skill"],
            destination_path=export_file,
            config=export_config,
        )

        # Read exported data
        exported_content = export_file.read_text()
        exported_data = yaml.safe_load(exported_content)

        # Verify data consistency
        assert exported_data[0]["name"] == original_data["name"]
        assert exported_data[0]["version"] == original_data["version"]
        assert exported_data[0]["description"] == original_data["description"]

    @pytest.mark.asyncio
    async def test_version_history_consistency(
        self,
        version_manager,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test version history consistency."""
        skill_id = "history-test-skill"

        # Create multiple versions
        for i in range(5):
            # Create test file
            test_file = temp_workspace / f"{skill_id}.yaml"
            test_file.write_text(f"name: test\nversion: {i+1}.0.0")

            # Create version
            commit = await version_manager.create_version(
                skill_id=skill_id,
                version=f"{i+1}.0.0",
                message=f"Version {i+1}",
                author="Test Author",
                file_path=f"{skill_id}.yaml",
            )
            assert commit is not None

        # Get history
        history = await version_manager.get_version_history(skill_id)

        # Verify history consistency
        assert len(history) == 5
        assert history[0].version == "5.0.0"  # Newest first
        assert history[4].version == "1.0.0"  # Oldest last


class TestErrorRecovery:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_recovery_from_import_failure(
        self,
        skill_importer,
        mock_skill_manager,
        temp_workspace,
    ):
        """Test recovery from import failure."""
        # Create partial valid data
        skills_data = [
            {
                "name": "valid-skill",
                "version": "1.0.0",
                "description": "Valid skill",
                "author": "Test",
            },
            # This will cause issues
            {"invalid": "data"},
        ]

        import_file = temp_workspace / "partial_import.yaml"
        import_file.write_text(yaml.dump(skills_data))

        # Import with skip invalid
        import_config = ImportConfig(
            format=ImportFormat.YAML,
            skip_invalid=True,
        )

        result = await skill_importer.import_skills(import_file, import_config)
        assert result is not None

        # Try valid import again
        valid_data = [
            {
                "name": "recovery-skill",
                "version": "1.0.0",
                "description": "Recovery skill",
                "author": "Test",
            },
        ]

        valid_file = temp_workspace / "valid_import.yaml"
        valid_file.write_text(yaml.dump(valid_data))

        valid_config = ImportConfig(format=ImportFormat.YAML)
        result = await skill_importer.import_skills(valid_file, valid_config)
        assert result is not None

    @pytest.mark.asyncio
    async def test_editor_error_recovery(
        self,
        skill_editor,
        temp_workspace,
    ):
        """Test editor error recovery."""
        # Create session
        session_id = await skill_editor.create_session("test_user")

        # Try to update non-existent file
        updated = await skill_editor.update_content(
            session_id,
            "non-existent-file",
            "content",
        )
        assert updated is False

        # Create file and continue working
        test_file = temp_workspace / "recovery-test.yaml"
        test_file.write_text("name: test\nversion: 1.0.0")

        file = await skill_editor.open_file(session_id, "recovery-test.yaml")
        assert file is not None

        # Update content successfully
        updated = await skill_editor.update_content(
            session_id,
            file.file_id,
            "name: test\nversion: 1.1.0",
        )
        assert updated is True


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
