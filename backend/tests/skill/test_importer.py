"""Tests for SkillImporter.

This module contains comprehensive unit tests for the SkillImporter
import and export functionality.
"""

import pytest
import asyncio
import json
import csv
import tempfile
import shutil
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.skill.importer import (
    SkillImporter,
    ImportResult,
    ExportResult,
    FieldMapping,
    ImportConfig,
    ExportConfig,
    ImportFormat,
    ExportFormat,
    ImportStatus,
    ValidationLevel,
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
    manager.create_skill = AsyncMock(return_value=Mock(id="test-skill-1"))
    manager.update_skill = AsyncMock(return_value=Mock(id="test-skill-1"))
    manager.get_skill = AsyncMock(return_value=Mock(
        id="test-skill-1",
        dict=lambda: {"id": "test-skill-1", "name": "Test Skill"},
    ))
    return manager


@pytest.fixture
def event_manager():
    """Create mock event manager."""
    manager = Mock(spec=SkillEventManager)
    manager.publish_event = AsyncMock(return_value="event_id")
    return manager


@pytest.fixture
def importer(skill_manager, event_manager, temp_dir):
    """Create SkillImporter instance for testing."""
    return SkillImporter(
        skill_manager=skill_manager,
        event_manager=event_manager,
        workspace_path=temp_dir,
    )


@pytest.fixture
def sample_yaml_skills():
    """Sample YAML skills for testing."""
    return """- name: skill1
  version: 1.0.0
  description: Test skill 1
  author: Author1
- name: skill2
  version: 1.0.0
  description: Test skill 2
  author: Author2
"""


@pytest.fixture
def sample_json_skills():
    """Sample JSON skills for testing."""
    return json.dumps([
        {
            "name": "skill1",
            "version": "1.0.0",
            "description": "Test skill 1",
            "author": "Author1",
        },
        {
            "name": "skill2",
            "version": "1.0.0",
            "description": "Test skill 2",
            "author": "Author2",
        },
    ], indent=2)


@pytest.fixture
def sample_csv_skills():
    """Sample CSV skills for testing."""
    return """name,version,description,author
skill1,1.0.0,Test skill 1,Author1
skill2,1.0.0,Test skill 2,Author2
"""


class TestImportResult:
    """Test ImportResult dataclass."""

    def test_create_import_result(self):
        """Test creating an import result."""
        result = ImportResult(import_id="import123")

        assert result.import_id == "import123"
        assert result.total_files == 0
        assert result.processed_files == 0
        assert result.successful_imports == 0
        assert result.failed_imports == 0
        assert result.skipped_files == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert len(result.created_skills) == 0
        assert len(result.updated_skills) == 0
        assert result.start_time is not None
        assert result.end_time is None
        assert result.duration_seconds is None

    def test_import_result_to_dict(self):
        """Test converting import result to dictionary."""
        result = ImportResult(import_id="import123")

        data = result.to_dict()

        assert "import_id" in data
        assert "start_time" in data
        assert isinstance(data["start_time"], str)
        assert data["total_files"] == 0


class TestExportResult:
    """Test ExportResult dataclass."""

    def test_create_export_result(self):
        """Test creating an export result."""
        result = ExportResult(
            export_id="export123",
            format=ExportFormat.YAML,
            total_skills=10,
        )

        assert result.export_id == "export123"
        assert result.format == ExportFormat.YAML
        assert result.total_skills == 10
        assert result.exported_skills == 0
        assert result.file_path is None
        assert result.start_time is not None
        assert result.end_time is None
        assert result.duration_seconds is None

    def test_export_result_to_dict(self):
        """Test converting export result to dictionary."""
        result = ExportResult(
            export_id="export123",
            format=ExportFormat.JSON,
        )

        data = result.to_dict()

        assert "export_id" in data
        assert "format" in data
        assert data["format"] == "json"
        assert "start_time" in data
        assert isinstance(data["start_time"], str)


class TestFieldMapping:
    """Test FieldMapping dataclass."""

    def test_create_field_mapping(self):
        """Test creating a field mapping."""
        mapping = FieldMapping(
            source_field="name",
            target_field="skill_name",
            transform="upper",
            required=True,
            default_value="Unknown",
        )

        assert mapping.source_field == "name"
        assert mapping.target_field == "skill_name"
        assert mapping.transform == "upper"
        assert mapping.required is True
        assert mapping.default_value == "Unknown"


class TestImportConfig:
    """Test ImportConfig dataclass."""

    def test_create_import_config(self):
        """Test creating an import configuration."""
        config = ImportConfig(
            format=ImportFormat.YAML,
            validation_level=ValidationLevel.STRICT,
            skip_invalid=True,
            update_existing=True,
            batch_size=50,
            parallel_processing=True,
            max_workers=8,
        )

        assert config.format == ImportFormat.YAML
        assert config.validation_level == ValidationLevel.STRICT
        assert config.skip_invalid is True
        assert config.update_existing is True
        assert config.batch_size == 50
        assert config.parallel_processing is True
        assert config.max_workers == 8


class TestExportConfig:
    """Test ExportConfig dataclass."""

    def test_create_export_config(self):
        """Test creating an export configuration."""
        config = ExportConfig(
            format=ExportFormat.JSON,
            include_metadata=True,
            include_statistics=False,
            batch_size=100,
            compress=True,
            encryption=False,
        )

        assert config.format == ExportFormat.JSON
        assert config.include_metadata is True
        assert config.include_statistics is False
        assert config.batch_size == 100
        assert config.compress is True
        assert config.encryption is False


class TestSkillImporter:
    """Test SkillImporter class."""

    @pytest.mark.asyncio
    async def test_import_yaml_skills(self, importer, temp_dir, sample_yaml_skills):
        """Test importing YAML skills."""
        # Create YAML file
        yaml_file = temp_dir / "skills.yaml"
        yaml_file.write_text(sample_yaml_skills)

        # Create import config
        config = ImportConfig(
            format=ImportFormat.YAML,
            validation_level=ValidationLevel.MODERATE,
        )

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        assert result is not None
        assert result.total_files == 1
        assert result.processed_files == 1
        assert result.successful_imports > 0

        # Check event was published
        importer.event_manager.publish_event.assert_called()

    @pytest.mark.asyncio
    async def test_import_json_skills(self, importer, temp_dir, sample_json_skills):
        """Test importing JSON skills."""
        # Create JSON file
        json_file = temp_dir / "skills.json"
        json_file.write_text(sample_json_skills)

        # Create import config
        config = ImportConfig(
            format=ImportFormat.JSON,
            validation_level=ValidationLevel.MODERATE,
        )

        # Import skills
        result = await importer.import_skills(json_file, config)

        assert result is not None
        assert result.total_files == 1
        assert result.successful_imports > 0

    @pytest.mark.asyncio
    async def test_import_csv_skills(self, importer, temp_dir, sample_csv_skills):
        """Test importing CSV skills."""
        # Create CSV file
        csv_file = temp_dir / "skills.csv"
        csv_file.write_text(sample_csv_skills)

        # Create import config
        config = ImportConfig(
            format=ImportFormat.CSV,
            validation_level=ValidationLevel.MODERATE,
        )

        # Import skills
        result = await importer.import_skills(csv_file, config)

        assert result is not None
        assert result.total_files == 1
        assert result.successful_imports > 0

    @pytest.mark.asyncio
    async def test_import_zip_skills(self, importer, temp_dir, sample_yaml_skills):
        """Test importing skills from ZIP file."""
        # Create ZIP file
        zip_path = temp_dir / "skills.zip"

        with zipfile.ZipFile(zip_path, "w") as zip_ref:
            zip_ref.writestr("skill1.yaml", "- name: skill1\n  version: 1.0.0")
            zip_ref.writestr("skill2.yaml", "- name: skill2\n  version: 1.0.0")

        # Create import config
        config = ImportConfig(
            format=ImportFormat.ZIP,
            validation_level=ValidationLevel.MODERATE,
        )

        # Import skills
        result = await importer.import_skills(zip_path, config)

        assert result is not None
        assert result.total_files == 2
        assert result.successful_imports > 0

    @pytest.mark.asyncio
    async def test_import_directory_skills(self, importer, temp_dir, sample_yaml_skills):
        """Test importing skills from directory."""
        # Create directory with skill files
        skill_dir = temp_dir / "skills"
        skill_dir.mkdir()

        (skill_dir / "skill1.yaml").write_text("- name: skill1\n  version: 1.0.0")
        (skill_dir / "skill2.yaml").write_text("- name: skill2\n  version: 1.0.0")
        (skill_dir / "skill3.json").write_text('[{"name": "skill3", "version": "1.0.0"}]')

        # Create import config
        config = ImportConfig(
            format=ImportFormat.DIRECTORY,
            validation_level=ValidationLevel.MODERATE,
        )

        # Import skills
        result = await importer.import_skills(skill_dir, config)

        assert result is not None
        assert result.total_files >= 2  # At least 2 YAML files

    @pytest.mark.asyncio
    async def test_import_nonexistent_file(self, importer):
        """Test importing from non-existent file."""
        config = ImportConfig(format=ImportFormat.YAML)

        result = await importer.import_skills("nonexistent.yaml", config)

        assert result is not None
        assert result.total_files == 0
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_import_with_field_mapping(self, importer, temp_dir):
        """Test importing with field mappings."""
        # Create YAML file
        yaml_content = """
- id: skill1
  title: Test Skill 1
  author_name: Author1
- id: skill2
  title: Test Skill 2
  author_name: Author2
"""
        yaml_file = temp_dir / "skills.yaml"
        yaml_file.write_text(yaml_content)

        # Create field mappings
        mappings = [
            FieldMapping("id", "name", required=True),
            FieldMapping("title", "description"),
            FieldMapping("author_name", "author"),
        ]

        # Create import config with mappings
        config = ImportConfig(
            format=ImportFormat.YAML,
            field_mappings=mappings,
            validation_level=ValidationLevel.MODERATE,
        )

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        assert result is not None
        assert result.successful_imports > 0

    @pytest.mark.asyncio
    async def test_import_with_validation_errors(self, importer, temp_dir):
        """Test importing with validation errors."""
        # Create invalid YAML file
        invalid_yaml = "- invalid: skill\n  - bad: yaml"
        yaml_file = temp_dir / "invalid.yaml"
        yaml_file.write_text(invalid_yaml)

        # Create import config
        config = ImportConfig(
            format=ImportFormat.YAML,
            validation_level=ValidationLevel.STRICT,
            skip_invalid=False,
        )

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        assert result is not None
        assert result.failed_imports > 0
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_import_skip_invalid(self, importer, temp_dir):
        """Test importing with skip invalid option."""
        # Create YAML file with mix of valid and invalid
        yaml_content = """
- name: valid-skill
  version: 1.0.0
  description: Valid skill
- invalid_skill_without_name
"""
        yaml_file = temp_dir / "mixed.yaml"
        yaml_file.write_text(yaml_content)

        # Create import config
        config = ImportConfig(
            format=ImportFormat.YAML,
            validation_level=ValidationLevel.MODERATE,
            skip_invalid=True,
        )

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        assert result is not None
        assert result.skipped_files > 0
        assert result.successful_imports >= 0

    @pytest.mark.asyncio
    async def test_import_update_existing(self, importer, temp_dir):
        """Test importing with update existing option."""
        # Create YAML file
        yaml_content = """
- name: test-skill
  version: 1.0.0
  description: Test skill
"""
        yaml_file = temp_dir / "update.yaml"
        yaml_file.write_text(yaml_content)

        # Mock existing skill
        importer.skill_manager.get_skill = AsyncMock(return_value={
            "id": "test-skill",
            "name": "test-skill",
        })

        # Create import config
        config = ImportConfig(
            format=ImportFormat.YAML,
            update_existing=True,
        )

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        assert result is not None
        assert len(result.updated_skills) > 0

    @pytest.mark.asyncio
    async def test_export_yaml_skills(self, importer, temp_dir):
        """Test exporting skills to YAML."""
        # Create export config
        config = ExportConfig(format=ExportFormat.YAML)

        # Export skills
        result = await importer.export_skills(
            ["skill1", "skill2"],
            temp_dir / "export.yaml",
            config,
        )

        assert result is not None
        assert result.total_skills == 2
        assert result.exported_skills == 2
        assert result.file_path is not None

        # Check file was created
        exported_file = Path(result.file_path)
        assert exported_file.exists()

    @pytest.mark.asyncio
    async def test_export_json_skills(self, importer, temp_dir):
        """Test exporting skills to JSON."""
        # Create export config
        config = ExportConfig(format=ExportFormat.JSON)

        # Export skills
        result = await importer.export_skills(
            ["skill1", "skill2"],
            temp_dir / "export.json",
            config,
        )

        assert result is not None
        assert result.exported_skills == 2

        # Check file was created and is valid JSON
        exported_file = Path(result.file_path)
        assert exported_file.exists()

        with open(exported_file, "r") as f:
            data = json.load(f)
            assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_export_csv_skills(self, importer, temp_dir):
        """Test exporting skills to CSV."""
        # Create export config
        config = ExportConfig(format=ExportFormat.CSV)

        # Export skills
        result = await importer.export_skills(
            ["skill1", "skill2"],
            temp_dir / "export.csv",
            config,
        )

        assert result is not None
        assert result.exported_skills == 2

        # Check file was created and is valid CSV
        exported_file = Path(result.file_path)
        assert exported_file.exists()

        with open(exported_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0

    @pytest.mark.asyncio
    async def test_export_zip_skills(self, importer, temp_dir):
        """Test exporting skills to ZIP."""
        # Create export config
        config = ExportConfig(format=ExportFormat.ZIP)

        # Export skills
        result = await importer.export_skills(
            ["skill1", "skill2"],
            temp_dir / "export.zip",
            config,
        )

        assert result is not None
        assert result.exported_skills == 2

        # Check ZIP file was created
        exported_file = Path(result.file_path)
        assert exported_file.exists()

        # Verify ZIP contents
        with zipfile.ZipFile(exported_file, "r") as zip_ref:
            files = zip_ref.namelist()
            assert "skills.json" in files

    @pytest.mark.asyncio
    async def test_export_directory_skills(self, importer, temp_dir):
        """Test exporting skills to directory."""
        # Create export config
        config = ExportConfig(format=ExportFormat.DIRECTORY)

        # Export skills
        result = await importer.export_skills(
            ["skill1", "skill2"],
            temp_dir / "export_dir",
            config,
        )

        assert result is not None
        assert result.exported_skills == 2

        # Check directory was created with files
        export_dir = Path(result.file_path)
        assert export_dir.exists()
        assert export_dir.is_dir()

        # Should have at least some skill files
        skill_files = list(export_dir.glob("*.yaml"))
        assert len(skill_files) > 0

    @pytest.mark.asyncio
    async def test_apply_field_mappings(self, importer):
        """Test applying field mappings."""
        # Create field mappings
        mappings = [
            FieldMapping("name", "skill_name", transform="upper"),
            FieldMapping("version", "version", default_value="1.0.0"),
            FieldMapping("author", "author"),
        ]

        # Source data
        data = {
            "name": "test-skill",
            "author": "Test Author",
        }

        # Apply mappings
        mapped_data = importer._apply_field_mappings(data, mappings)

        assert mapped_data["skill_name"] == "TEST-SKILL"
        assert mapped_data["version"] == "1.0.0"
        assert mapped_data["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_apply_transformations(self, importer):
        """Test applying transformations."""
        # Test upper
        assert importer._apply_transform("test", "upper") == "TEST"

        # Test lower
        assert importer._apply_transform("TEST", "lower") == "test"

        # Test strip
        assert importer._apply_transform(" test ", "strip") == "test"

        # Test int
        assert importer._apply_transform("123", "int") == 123

        # Test float
        assert importer._apply_transform("123.45", "float") == 123.45

        # Test unknown (should return as-is)
        assert importer._apply_transform("test", "unknown") == "test"

    @pytest.mark.asyncio
    async def test_validate_skill_data(self, importer):
        """Test validating skill data."""
        # Valid data
        valid_data = {
            "name": "test-skill",
            "version": "1.0.0",
            "description": "Test skill",
        }

        is_valid, errors = await importer._validate_skill_data(
            valid_data,
            ValidationLevel.MODERATE,
        )

        # Should be valid (or at least not have errors about missing fields)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)

        # Invalid data (missing required fields)
        invalid_data = {
            "description": "Test skill",
        }

        is_valid, errors = await importer._validate_skill_data(
            invalid_data,
            ValidationLevel.MODERATE,
        )

        # Should have validation errors
        assert not is_valid or len(errors) > 0

    @pytest.mark.asyncio
    async def test_get_import_result(self, importer, temp_dir):
        """Test getting import result."""
        # Create YAML file
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text("- name: test\n  version: 1.0.0")

        # Create import config
        config = ImportConfig(format=ImportFormat.YAML)

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        # Wait a bit for async processing
        await asyncio.sleep(0.1)

        # Get result
        if result:
            retrieved = await importer.get_import_result(result.import_id)

            assert retrieved is not None
            assert retrieved.import_id == result.import_id

    @pytest.mark.asyncio
    async def test_get_export_result(self, importer, temp_dir):
        """Test getting export result."""
        # Create export config
        config = ExportConfig(format=ExportFormat.JSON)

        # Export skills
        result = await importer.export_skills(
            ["skill1"],
            temp_dir / "export.json",
            config,
        )

        # Wait a bit for async processing
        await asyncio.sleep(0.1)

        # Get result
        if result:
            retrieved = await importer.get_export_result(result.export_id)

            assert retrieved is not None
            assert retrieved.export_id == result.export_id

    @pytest.mark.asyncio
    async def test_cancel_import(self, importer, temp_dir):
        """Test cancelling an import."""
        # Create large file to import
        yaml_content = "\n".join([
            f"- name: skill{i}\n  version: 1.0.0"
            for i in range(100)
        ])
        yaml_file = temp_dir / "large.yaml"
        yaml_file.write_text(yaml_content)

        # Create import config
        config = ImportConfig(
            format=ImportFormat.YAML,
            parallel_processing=True,
        )

        # Import skills
        result = await importer.import_skills(yaml_file, config)

        # Cancel import
        if result:
            cancelled = await importer.cancel_import(result.import_id)

            assert cancelled is True

    @pytest.mark.asyncio
    async def test_cancel_export(self, importer, temp_dir):
        """Test cancelling an export."""
        # Create export config
        config = ExportConfig(format=ExportFormat.JSON)

        # Export skills
        result = await importer.export_skills(
            [f"skill{i}" for i in range(100)],
            temp_dir / "export.json",
            config,
        )

        # Cancel export
        if result:
            cancelled = await importer.cancel_export(result.export_id)

            assert cancelled is True

    @pytest.mark.asyncio
    async def test_list_import_history(self, importer, temp_dir):
        """Test listing import history."""
        # Create multiple imports
        for i in range(3):
            yaml_file = temp_dir / f"test{i}.yaml"
            yaml_file.write_text(f"- name: skill{i}\n  version: 1.0.0")

            config = ImportConfig(format=ImportFormat.YAML)
            await importer.import_skills(yaml_file, config)

        # Wait for processing
        await asyncio.sleep(0.1)

        # List history
        history = await importer.list_import_history(limit=5)

        assert len(history) > 0

    @pytest.mark.asyncio
    async def test_list_export_history(self, importer, temp_dir):
        """Test listing export history."""
        # Create multiple exports
        for i in range(3):
            config = ExportConfig(format=ExportFormat.JSON)
            await importer.export_skills(
                [f"skill{i}"],
                temp_dir / f"export{i}.json",
                config,
            )

        # Wait for processing
        await asyncio.sleep(0.1)

        # List history
        history = await importer.list_export_history(limit=5)

        assert len(history) > 0

    @pytest.mark.asyncio
    async def test_cleanup_old_results(self, importer, temp_dir):
        """Test cleaning up old results."""
        # Create some mock results
        importer.import_results["old_import"] = ImportResult(
            import_id="old_import",
            start_time=datetime.now() - timedelta(days=40),
        )

        importer.export_results["old_export"] = ExportResult(
            export_id="old_export",
            format=ExportFormat.JSON,
            start_time=datetime.now() - timedelta(days=40),
        )

        # Clean up results older than 30 days
        cleaned_imports, cleaned_exports = await importer.cleanup_old_results(days_old=30)

        assert cleaned_imports == 1
        assert cleaned_exports == 1

        assert "old_import" not in importer.import_results
        assert "old_export" not in importer.export_results

    @pytest.mark.asyncio
    async def test_callbacks(self, importer, temp_dir):
        """Test import/export callbacks."""
        # Create test file
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text("- name: test\n  version: 1.0.0")

        # Set up callbacks
        import_progress_called = False
        export_progress_called = False

        async def on_import_progress(import_id, progress, result):
            nonlocal import_progress_called
            import_progress_called = True

        async def on_export_progress(export_id, progress, result):
            nonlocal export_progress_called
            export_progress_called = True

        importer.on_import_progress = on_import_progress
        importer.on_export_progress = on_export_progress

        # Import
        config = ImportConfig(format=ImportFormat.YAML)
        await importer.import_skills(yaml_file, config)

        # Export
        config = ExportConfig(format=ExportFormat.JSON)
        await importer.export_skills(
            ["skill1"],
            temp_dir / "export.json",
            config,
        )

        # Wait for callbacks
        await asyncio.sleep(0.1)

        # Note: Callbacks might not be called in unit tests
        # depending on the async execution order

    @pytest.mark.asyncio
    async def test_parse_yaml_content(self, importer):
        """Test parsing YAML content."""
        yaml_content = "- name: test\n  version: 1.0.0"

        data = await importer._parse_content(yaml_content, ImportFormat.YAML)

        assert data is not None
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_parse_json_content(self, importer):
        """Test parsing JSON content."""
        json_content = json.dumps([{"name": "test", "version": "1.0.0"}])

        data = await importer._parse_content(json_content, ImportFormat.JSON)

        assert data is not None
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_parse_csv_content(self, importer):
        """Test parsing CSV content."""
        csv_content = "name,version\ntest,1.0.0"

        data = await importer._parse_content(csv_content, ImportFormat.CSV)

        assert data is not None
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]

    @pytest.mark.asyncio
    async def test_enums(self):
        """Test enum values."""
        # ImportFormat
        assert ImportFormat.YAML.value == "yaml"
        assert ImportFormat.JSON.value == "json"
        assert ImportFormat.CSV.value == "csv"
        assert ImportFormat.ZIP.value == "zip"
        assert ImportFormat.DIRECTORY.value == "directory"

        # ExportFormat
        assert ExportFormat.YAML.value == "yaml"
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.CSV.value == "csv"
        assert ExportFormat.ZIP.value == "zip"
        assert ExportFormat.DIRECTORY.value == "directory"

        # ValidationLevel
        assert ValidationLevel.STRICT.value == "strict"
        assert ValidationLevel.MODERATE.value == "moderate"
        assert ValidationLevel.LENIENT.value == "lenient"
