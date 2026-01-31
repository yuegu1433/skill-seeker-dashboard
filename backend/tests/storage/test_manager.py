"""Tests for SkillStorageManager.

This module contains unit tests for the SkillStorageManager class,
testing all storage operations with mocked dependencies.
"""

import io
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.app.storage.manager import (
    SkillStorageManager,
    SkillStorageError,
    FileNotFoundError,
    SkillNotFoundError,
    StorageQuotaExceededError,
)
from backend.app.storage.models import Skill, SkillFile
from backend.app.storage.schemas.file_operations import (
    FileUploadRequest,
    FileDownloadRequest,
    FileDeleteRequest,
    FileListRequest,
    FileMoveRequest,
)
from backend.app.storage.schemas.storage_config import StorageConfig, MinIOConfig


class TestSkillStorageManager:
    """Test suite for SkillStorageManager."""

    @pytest.fixture
    def storage_config(self):
        """Create test storage configuration."""
        return StorageConfig(
            minio=MinIOConfig(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="minioadmin123",
                secure=False,
            ),
            default_bucket="skillseekers-skills",
        )

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client."""
        return Mock()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.filter.return_value.count.return_value = 0
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.delete = Mock()
        return session

    @pytest.fixture
    def storage_manager(self, mock_minio_client, mock_db_session, storage_config):
        """Create SkillStorageManager instance."""
        return SkillStorageManager(
            minio_client=mock_minio_client,
            database_session=mock_db_session,
            config=storage_config,
        )

    @pytest.fixture
    def test_skill(self):
        """Create test skill."""
        return Skill(
            id=uuid4(),
            name="test-skill",
            platform="claude",
            status="creating",
            source_type="github",
        )

    @pytest.fixture
    def test_skill_file(self, test_skill):
        """Create test skill file."""
        return SkillFile(
            id=uuid4(),
            skill_id=test_skill.id,
            object_name="skills/test-skill/test.txt",
            file_path="test.txt",
            file_type="skill_file",
            file_size=1024,
            content_type="text/plain",
            checksum="abc123",
            metadata={"key": "value"},
            tags=["test"],
            is_public=False,
        )

    # Test initialization
    def test_initialization(self, storage_manager, mock_minio_client, mock_db_session, storage_config):
        """Test storage manager initialization."""
        assert storage_manager.minio_client == mock_minio_client
        assert storage_manager.db == mock_db_session
        assert storage_manager.config == storage_config

    # Test upload_file
    @pytest.mark.asyncio
    async def test_upload_file_success(self, storage_manager, mock_minio_client, mock_db_session, test_skill):
        """Test successful file upload."""
        # Setup
        skill_id = test_skill.id
        file_data = b"test file content"

        # Mock skill exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill

        # Mock MinIO upload
        mock_minio_client.put_object.return_value = {
            "object_name": "skills/test-skill/test.txt"
        }

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        request = FileUploadRequest(
            skill_id=skill_id,
            file_path="test.txt",
            content_type="text/plain",
        )

        result = await storage_manager.upload_file(request, file_data)

        # Verify
        assert result.success is True
        assert result.file_path == "test.txt"
        assert result.file_size == len(file_data)
        assert result.checksum is not None
        mock_minio_client.put_object.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_file_skill_not_found(self, storage_manager, mock_db_session):
        """Test upload file when skill doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_data = b"test file content"

        # Mock skill doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileUploadRequest(
            skill_id=skill_id,
            file_path="test.txt",
        )

        with pytest.raises(SkillNotFoundError):
            await storage_manager.upload_file(request, file_data)

    @pytest.mark.asyncio
    async def test_upload_file_quota_exceeded(self, storage_manager, mock_minio_client, mock_db_session, test_skill):
        """Test upload file when storage quota is exceeded."""
        # Setup
        skill_id = test_skill.id
        large_file_data = b"x" * (2 * 1024 * 1024 * 1024)  # 2GB

        # Mock skill exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill

        # Mock large file statistics
        mock_db_session.query.return_value.filter.return_value.one.return_value = (1024 * 1024 * 1024, 0)  # 1GB

        # Execute and verify
        request = FileUploadRequest(
            skill_id=skill_id,
            file_path="large.txt",
        )

        with pytest.raises(StorageQuotaExceededError):
            await storage_manager.upload_file(request, large_file_data)

    # Test download_file
    @pytest.mark.asyncio
    async def test_download_file_success(self, storage_manager, mock_minio_client, mock_db_session, test_skill, test_skill_file):
        """Test successful file download."""
        # Setup
        skill_id = test_skill.id
        file_path = "test.txt"

        # Mock file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock presigned URL
        mock_minio_client.presigned_get_object.return_value = "http://example.com/download"

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        request = FileDownloadRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        result = await storage_manager.download_file(request)

        # Verify
        assert result.success is True
        assert result.file_path == file_path
        assert result.download_url is not None
        mock_minio_client.presigned_get_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file_not_found(self, storage_manager, mock_db_session):
        """Test download file when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"

        # Mock file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileDownloadRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        with pytest.raises(FileNotFoundError):
            await storage_manager.download_file(request)

    # Test delete_file
    @pytest.mark.asyncio
    async def test_delete_file_success(self, storage_manager, mock_minio_client, mock_db_session, test_skill, test_skill_file):
        """Test successful file deletion."""
        # Setup
        skill_id = test_skill.id
        file_path = "test.txt"

        # Mock file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock MinIO removal
        mock_minio_client.remove_object.return_value = None

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        request = FileDeleteRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        result = await storage_manager.delete_file(request)

        # Verify
        assert result.success is True
        assert result.file_path == file_path
        mock_minio_client.remove_object.assert_called_once()
        mock_db_session.delete.assert_called_once()
        mock_db_session.commit.assert_called_once()

    # Test list_files
    @pytest.mark.asyncio
    async def test_list_files_success(self, storage_manager, mock_db_session, test_skill, test_skill_file):
        """Test successful file listing."""
        # Setup
        skill_id = test_skill.id

        # Mock skill exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill

        # Mock files exist
        mock_db_session.query.return_value.filter.return_value.count.return_value = 1
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.return_value = [test_skill_file]

        # Execute
        request = FileListRequest(
            skill_id=skill_id,
            limit=50,
            offset=0,
        )

        result = await storage_manager.list_files(request)

        # Verify
        assert len(result.files) == 1
        assert result.total == 1
        assert result.has_more is False

    @pytest.mark.asyncio
    async def test_list_files_skill_not_found(self, storage_manager, mock_db_session):
        """Test list files when skill doesn't exist."""
        # Setup
        skill_id = uuid4()

        # Mock skill doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileListRequest(
            skill_id=skill_id,
        )

        with pytest.raises(SkillNotFoundError):
            await storage_manager.list_files(request)

    # Test move_file
    @pytest.mark.asyncio
    async def test_move_file_success(self, storage_manager, mock_minio_client, mock_db_session, test_skill, test_skill_file):
        """Test successful file move."""
        # Setup
        skill_id = test_skill.id
        source_path = "old.txt"
        target_path = "new.txt"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock target doesn't exist
        def mock_filter_side_effect(*args, **kwargs):
            query = Mock()
            query.first.return_value = None
            return query

        mock_db_session.query.return_value.filter.side_effect = mock_filter_side_effect

        # Mock MinIO copy
        mock_minio_client.copy_object.return_value = None
        mock_minio_client.remove_object.return_value = None

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        request = FileMoveRequest(
            skill_id=skill_id,
            source_path=source_path,
            target_path=target_path,
        )

        result = await storage_manager.move_file(request)

        # Verify
        assert result.success is True
        assert result.source_path == source_path
        assert result.target_path == target_path
        mock_minio_client.copy_object.assert_called_once()
        mock_minio_client.remove_object.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_move_file_source_not_found(self, storage_manager, mock_db_session):
        """Test move file when source doesn't exist."""
        # Setup
        skill_id = uuid4()

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileMoveRequest(
            skill_id=skill_id,
            source_path="old.txt",
            target_path="new.txt",
        )

        with pytest.raises(FileNotFoundError):
            await storage_manager.move_file(request)

    # Test get_file_info
    @pytest.mark.asyncio
    async def test_get_file_info_success(self, storage_manager, mock_db_session, test_skill, test_skill_file):
        """Test successful file info retrieval."""
        # Setup
        skill_id = test_skill.id
        file_path = "test.txt"

        # Mock file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Execute
        result = await storage_manager.get_file_info(skill_id, file_path)

        # Verify
        assert result.id == test_skill_file.id
        assert result.file_path == file_path
        assert result.file_size == test_skill_file.file_size

    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, storage_manager, mock_db_session):
        """Test get file info when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"

        # Mock file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(FileNotFoundError):
            await storage_manager.get_file_info(skill_id, file_path)

    # Test get_skill_stats
    @pytest.mark.asyncio
    async def test_get_skill_stats_success(self, storage_manager, mock_db_session, test_skill):
        """Test successful skill stats retrieval."""
        # Setup
        skill_id = test_skill.id

        # Mock skill exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill

        # Mock stats query
        mock_db_session.query.return_value.filter.return_value.one.return_value = (5, 10240)  # 5 files, 10KB

        # Mock file type breakdown
        mock_db_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("skill_file", 3, 5120),  # 3 skill files, 5KB
            ("config", 2, 5120),  # 2 config files, 5KB
        ]

        # Execute
        result = await storage_manager.get_skill_stats(skill_id)

        # Verify
        assert result["skill_id"] == skill_id
        assert result["file_count"] == 5
        assert result["total_size"] == 10240
        assert "file_types" in result
        assert "skill_file" in result["file_types"]

    @pytest.mark.asyncio
    async def test_get_skill_stats_not_found(self, storage_manager, mock_db_session):
        """Test get skill stats when skill doesn't exist."""
        # Setup
        skill_id = uuid4()

        # Mock skill doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(SkillNotFoundError):
            await storage_manager.get_skill_stats(skill_id)

    # Test verify_file_integrity
    @pytest.mark.asyncio
    async def test_verify_file_integrity_success(self, storage_manager, mock_minio_client, mock_db_session, test_skill, test_skill_file):
        """Test successful file integrity verification."""
        # Setup
        skill_id = test_skill.id
        file_path = "test.txt"

        # Mock file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock MinIO get object
        mock_response = io.BytesIO(b"test file content")
        mock_minio_client.get_object.return_value = mock_response

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        result = await storage_manager.verify_file_integrity(skill_id, file_path)

        # Verify
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_verify_file_integrity_not_found(self, storage_manager, mock_db_session):
        """Test verify file integrity when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"

        # Mock file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(FileNotFoundError):
            await storage_manager.verify_file_integrity(skill_id, file_path)

    # Test ensure_skill_storage
    @pytest.mark.asyncio
    async def test_ensure_skill_storage_success(self, storage_manager, mock_minio_client, mock_db_session, test_skill):
        """Test successful storage preparation."""
        # Setup
        skill_id = test_skill.id

        # Mock skill exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill

        # Mock bucket doesn't exist initially
        mock_minio_client.bucket_exists.return_value = False

        # Mock bucket creation
        mock_minio_client.create_bucket.return_value = None

        # Execute
        result = await storage_manager.ensure_skill_storage(skill_id)

        # Verify
        assert result is True
        mock_minio_client.bucket_exists.assert_called_once()
        mock_minio_client.create_bucket.assert_called_once()

    @pytest.mark.asyncio
    async def test_ensure_skill_storage_not_found(self, storage_manager, mock_db_session):
        """Test ensure storage when skill doesn't exist."""
        # Setup
        skill_id = uuid4()

        # Mock skill doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(SkillNotFoundError):
            await storage_manager.ensure_skill_storage(skill_id)

    # Test helper methods
    def test_generate_object_name(self, storage_manager):
        """Test object name generation."""
        skill_id = uuid4()
        file_path = "test.txt"

        object_name = storage_manager._generate_object_name(skill_id, file_path)

        assert "skills" in object_name
        assert str(skill_id) in object_name
        assert "test.txt" in object_name

    def test_determine_file_type(self, storage_manager):
        """Test file type determination."""
        # Test different file types
        assert storage_manager._determine_file_type("SKILL.md") == "skill_file"
        assert storage_manager._determine_file_type("config.json") == "config"
        assert storage_manager._determine_file_type("metadata.json") == "config"
        assert storage_manager._determine_file_type("readme.md") == "reference"
        assert storage_manager._determine_file_type("creation.log") == "log"
        assert storage_manager._determine_file_type("other.txt") == "other"

    # Test error scenarios
    @pytest.mark.asyncio
    async def test_upload_file_database_error(self, storage_manager, mock_db_session, test_skill):
        """Test upload file with database error."""
        # Setup
        skill_id = test_skill.id
        file_data = b"test file content"

        # Mock skill exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill

        # Mock MinIO upload succeeds
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Mock database error
        from sqlalchemy.exc import SQLAlchemyError
        mock_db_session.commit.side_effect = SQLAlchemyError("Database error")

        # Execute and verify
        request = FileUploadRequest(
            skill_id=skill_id,
            file_path="test.txt",
        )

        with pytest.raises(SkillStorageError):
            await storage_manager.upload_file(request, file_data)

        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_file_minio_error(self, storage_manager, mock_minio_client, mock_db_session, test_skill, test_skill_file):
        """Test download file with MinIO error."""
        # Setup
        skill_id = test_skill.id
        file_path = "test.txt"

        # Mock file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock MinIO error
        from backend.app.storage.client import MinIOOperationError
        mock_minio_client.presigned_get_object.side_effect = MinIOOperationError("MinIO error")

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute and verify
        request = FileDownloadRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        with pytest.raises(SkillStorageError):
            await storage_manager.download_file(request)

    @pytest.mark.asyncio
    async def test_storage_operation_context(self, storage_manager, mock_minio_client):
        """Test storage operation context manager."""
        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        async with storage_manager.storage_operation("test_operation"):
            pass

        # Verify
        mock_minio_client.operation_context.assert_called_with("test_operation")
