"""Tests for VersionManager.

This module contains unit tests for the VersionManager class,
testing all version control operations with mocked dependencies.
"""

import io
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.storage.versioning import (
    VersionManager,
    VersioningError,
    VersionNotFoundError,
    VersionLimitExceededError,
    VersionRestoreError,
)
from backend.app.storage.models import SkillFile, FileVersion
from backend.app.storage.schemas.file_operations import (
    FileVersionCreateRequest,
    FileVersionRestoreRequest,
)
from backend.app.storage.client import MinIOClient


class TestVersionManager:
    """Test suite for VersionManager."""

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client."""
        return Mock(spec=MinIOClient)

    @pytest.fixture
    def mock_storage_manager(self):
        """Create mock storage manager."""
        return Mock()

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value.filter.return_value.first.return_value = None
        session.query.return_value.filter.return_value.count.return_value = 0
        session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.return_value = []
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.delete = Mock()
        return session

    @pytest.fixture
    def version_manager(self, mock_minio_client, mock_storage_manager, mock_db_session):
        """Create VersionManager instance."""
        return VersionManager(
            minio_client=mock_minio_client,
            storage_manager=mock_storage_manager,
            database_session=mock_db_session,
            max_versions=10,
            cleanup_threshold_days=90,
        )

    @pytest.fixture
    def test_skill_file(self):
        """Create test skill file."""
        return SkillFile(
            id=uuid4(),
            skill_id=uuid4(),
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

    @pytest.fixture
    def test_file_version(self, test_skill_file):
        """Create test file version."""
        return FileVersion(
            id=uuid4(),
            file_id=test_skill_file.id,
            version_id=uuid4().hex,
            version_number=1,
            object_name="versions/test.txt/abc123",
            file_size=1024,
            checksum="abc123",
            comment="Initial version",
            metadata={},
            created_by="system",
            created_at=datetime.utcnow(),
            is_latest=True,
        )

    # Test initialization
    def test_initialization(self, version_manager, mock_minio_client, mock_storage_manager, mock_db_session):
        """Test version manager initialization."""
        assert version_manager.minio_client == mock_minio_client
        assert version_manager.storage_manager == mock_storage_manager
        assert version_manager.db == mock_db_session
        assert version_manager.max_versions == 10
        assert version_manager.cleanup_threshold_days == 90
        assert version_manager.versions_bucket == "skillseekers-versions"
        assert version_manager.versions_prefix == "versions"

    # Test create_version
    @pytest.mark.asyncio
    async def test_create_version_success(self, version_manager, mock_minio_client, mock_db_session, test_skill_file):
        """Test successful version creation."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        file_data = b"test file content"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version number query
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock MinIO upload
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "versions/test.txt/abc123",
            "etag": "etag123",
            "size": 1024,
        }

        # Execute
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
            comment="Initial version",
            metadata={"version": "1.0"},
        )

        result = await version_manager.create_version(request, file_data)

        # Verify
        assert result is not None
        mock_minio_client.put_object.assert_called_once()
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_create_version_source_file_not_found(self, version_manager, mock_db_session):
        """Test create version when source file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"
        file_data = b"test file content"

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        with pytest.raises(VersionNotFoundError):
            await version_manager.create_version(request, file_data)

    @pytest.mark.asyncio
    async def test_create_version_limit_exceeded(self, version_manager, mock_minio_client, mock_db_session, test_skill_file):
        """Test create version when limit is exceeded."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        file_data = b"test file content"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version number query (exceeds max)
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 10

        # Execute and verify
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        with pytest.raises(VersionLimitExceededError):
            await version_manager.create_version(request, file_data)

    @pytest.mark.asyncio
    async def test_create_version_with_binary_io(self, version_manager, mock_minio_client, mock_db_session, test_skill_file):
        """Test create version with BinaryIO data."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        file_data = io.BytesIO(b"test file content")

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version number query
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock MinIO upload
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "versions/test.txt/abc123",
            "etag": "etag123",
            "size": 1024,
        }

        # Execute
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        result = await version_manager.create_version(request, file_data)

        # Verify
        assert result is not None
        mock_minio_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_version_database_error(self, version_manager, mock_minio_client, mock_db_session, test_skill_file):
        """Test create version with database error."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        file_data = b"test file content"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version number query
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock MinIO upload
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "versions/test.txt/abc123",
            "etag": "etag123",
            "size": 1024,
        }

        # Mock database error
        mock_db_session.commit.side_effect = SQLAlchemyError("Database error")

        # Execute and verify
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        with pytest.raises(VersioningError):
            await version_manager.create_version(request, file_data)

        mock_db_session.rollback.assert_called_once()

    # Test list_versions
    @pytest.mark.asyncio
    async def test_list_versions_success(self, version_manager, mock_db_session, test_skill_file, test_file_version):
        """Test successful version listing."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock versions exist
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.return_value = [test_file_version]

        # Execute
        result = await version_manager.list_versions(skill_id, file_path)

        # Verify
        assert len(result) == 1
        assert result[0].version_number == test_file_version.version_number

    @pytest.mark.asyncio
    async def test_list_versions_file_not_found(self, version_manager, mock_db_session):
        """Test list versions when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(VersionNotFoundError):
            await version_manager.list_versions(skill_id, file_path)

    @pytest.mark.asyncio
    async def test_list_versions_empty(self, version_manager, mock_db_session, test_skill_file):
        """Test list versions when no versions exist."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock no versions
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.return_value = []

        # Execute
        result = await version_manager.list_versions(skill_id, file_path)

        # Verify
        assert len(result) == 0

    # Test restore_version
    @pytest.mark.asyncio
    async def test_restore_version_success(self, version_manager, mock_minio_client, mock_db_session, mock_storage_manager, test_skill_file, test_file_version):
        """Test successful version restoration."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id = test_file_version.version_id

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_file_version

        # Mock MinIO get object
        mock_response = io.BytesIO(b"test file content")
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.get_object.return_value = mock_response

        # Mock storage manager upload
        mock_storage_manager.upload_file.return_value = Mock(success=True)

        # Execute
        request = FileVersionRestoreRequest(
            skill_id=skill_id,
            file_path=file_path,
            version_id=version_id,
        )

        result = await version_manager.restore_version(request)

        # Verify
        assert result is True
        mock_minio_client.get_object.assert_called_once()
        mock_storage_manager.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_restore_version_file_not_found(self, version_manager, mock_db_session):
        """Test restore version when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"
        version_id = uuid4().hex

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileVersionRestoreRequest(
            skill_id=skill_id,
            file_path=file_path,
            version_id=version_id,
        )

        with pytest.raises(VersionNotFoundError):
            await version_manager.restore_version(request)

    @pytest.mark.asyncio
    async def test_restore_version_not_found(self, version_manager, mock_db_session, test_skill_file):
        """Test restore version when version doesn't exist."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id = uuid4().hex

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        request = FileVersionRestoreRequest(
            skill_id=skill_id,
            file_path=file_path,
            version_id=version_id,
        )

        with pytest.raises(VersionNotFoundError):
            await version_manager.restore_version(request)

    @pytest.mark.asyncio
    async def test_restore_version_failure(self, version_manager, mock_minio_client, mock_db_session, test_skill_file, test_file_version):
        """Test restore version with failure."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id = test_file_version.version_id

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_file_version

        # Mock MinIO error
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.get_object.side_effect = Exception("MinIO error")

        # Execute and verify
        request = FileVersionRestoreRequest(
            skill_id=skill_id,
            file_path=file_path,
            version_id=version_id,
        )

        with pytest.raises(VersionRestoreError):
            await version_manager.restore_version(request)

    # Test compare_versions
    @pytest.mark.asyncio
    async def test_compare_versions_success(self, version_manager, mock_minio_client, mock_db_session, test_skill_file, test_file_version):
        """Test successful version comparison."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id_1 = test_file_version.version_id
        version_id_2 = uuid4().hex

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock both versions exist
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [test_file_version, test_file_version]

        # Mock MinIO get objects
        mock_response1 = io.BytesIO(b"content version 1")
        mock_response2 = io.BytesIO(b"content version 2")
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.get_object.side_effect = [mock_response1, mock_response2]

        # Execute
        result = await version_manager.compare_versions(
            skill_id, file_path, version_id_1, version_id_2
        )

        # Verify
        assert "file_path" in result
        assert "version_1" in result
        assert "version_2" in result
        assert "differences" in result
        assert result["differences"]["checksum_different"] is True
        assert result["differences"]["size_difference"] == 1

    @pytest.mark.asyncio
    async def test_compare_versions_version1_not_found(self, version_manager, mock_db_session, test_skill_file):
        """Test compare versions when first version doesn't exist."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id_1 = uuid4().hex
        version_id_2 = uuid4().hex

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(VersionNotFoundError):
            await version_manager.compare_versions(
                skill_id, file_path, version_id_1, version_id_2
            )

    @pytest.mark.asyncio
    async def test_compare_versions_version2_not_found(self, version_manager, mock_db_session, test_skill_file, test_file_version):
        """Test compare versions when second version doesn't exist."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id_1 = test_file_version.version_id
        version_id_2 = uuid4().hex

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock first version exists, second doesn't
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [test_file_version, None]

        # Execute and verify
        with pytest.raises(VersionNotFoundError):
            await version_manager.compare_versions(
                skill_id, file_path, version_id_1, version_id_2
            )

    @pytest.mark.asyncio
    async def test_compare_versions_file_not_found(self, version_manager, mock_db_session):
        """Test compare versions when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"
        version_id_1 = uuid4().hex
        version_id_2 = uuid4().hex

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(VersionNotFoundError):
            await version_manager.compare_versions(
                skill_id, file_path, version_id_1, version_id_2
            )

    # Test delete_version
    @pytest.mark.asyncio
    async def test_delete_version_success(self, version_manager, mock_minio_client, mock_db_session, test_skill_file, test_file_version):
        """Test successful version deletion."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id = test_file_version.version_id

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_file_version

        # Mock version count (multiple versions)
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 3

        # Mock MinIO remove
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.remove_object.return_value = None

        # Execute
        result = await version_manager.delete_version(skill_id, file_path, version_id)

        # Verify
        assert result is True
        mock_minio_client.remove_object.assert_called_once()
        mock_db_session.delete.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_version_file_not_found(self, version_manager, mock_db_session):
        """Test delete version when file doesn't exist."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"
        version_id = uuid4().hex

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(VersionNotFoundError):
            await version_manager.delete_version(skill_id, file_path, version_id)

    @pytest.mark.asyncio
    async def test_delete_version_not_found(self, version_manager, mock_db_session, test_skill_file):
        """Test delete version when version doesn't exist."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id = uuid4().hex

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        with pytest.raises(VersionNotFoundError):
            await version_manager.delete_version(skill_id, file_path, version_id)

    @pytest.mark.asyncio
    async def test_delete_version_only_version(self, version_manager, mock_db_session, test_skill_file, test_file_version):
        """Test delete version when it's the only version."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        version_id = test_file_version.version_id

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_file_version

        # Mock version count (only one version)
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 1

        # Execute and verify
        with pytest.raises(VersioningError):
            await version_manager.delete_version(skill_id, file_path, version_id)

    # Test cleanup_old_versions
    @pytest.mark.asyncio
    async def test_cleanup_old_versions_success(self, version_manager, mock_minio_client, mock_db_session, test_skill_file):
        """Test successful cleanup of old versions."""
        # Setup
        skill_id = test_skill_file.skill_id

        # Mock old versions
        old_version = Mock()
        old_version.id = uuid4()
        old_version.version_id = uuid4().hex
        old_version.object_name = "versions/old.txt/abc123"
        old_version.is_latest = False

        # Mock query results
        mock_db_session.query.return_value.filter.return_value.all.return_value = [old_version]
        mock_db_session.query.return_value.filter.return_value.join.return_value.filter.return_value.all.return_value = [old_version]

        # Mock MinIO remove
        mock_minio_client.remove_object.return_value = None

        # Execute
        result = await version_manager.cleanup_old_versions(skill_id)

        # Verify
        assert result >= 0
        mock_minio_client.remove_object.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_old_versions_no_skill_id(self, version_manager, mock_minio_client, mock_db_session):
        """Test cleanup old versions without skill filter."""
        # Setup
        # Mock old versions
        old_version = Mock()
        old_version.id = uuid4()
        old_version.version_id = uuid4().hex
        old_version.object_name = "versions/old.txt/abc123"
        old_version.is_latest = False

        # Mock query results
        mock_db_session.query.return_value.filter.return_value.all.return_value = [old_version]

        # Mock MinIO remove
        mock_minio_client.remove_object.return_value = None

        # Execute
        result = await version_manager.cleanup_old_versions()

        # Verify
        assert result >= 0
        mock_minio_client.remove_object.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_old_versions_failure(self, version_manager, mock_db_session):
        """Test cleanup old versions with failure."""
        # Setup
        skill_id = uuid4()

        # Mock database error
        mock_db_session.query.return_value.filter.return_value.all.side_effect = SQLAlchemyError("Database error")

        # Execute and verify
        with pytest.raises(VersioningError):
            await version_manager.cleanup_old_versions(skill_id)

        mock_db_session.rollback.assert_called_once()

    # Test get_version_statistics
    @pytest.mark.asyncio
    async def test_get_version_statistics_success(self, version_manager, mock_db_session, test_skill_file):
        """Test successful get version statistics."""
        # Setup
        skill_id = test_skill_file.skill_id

        # Mock query results
        mock_db_session.query.return_value.count.return_value = 5
        mock_db_session.query.return_value.filter.return_value.count.return_value = 2
        mock_db_session.query.return_value.filter.return_value.count.return_value = 3
        mock_db_session.query.return_value.join.return_value.filter.return_value.scalar.return_value = 1
        mock_db_session.query.return_value.with_entities.return_value.scalar.return_value = 10240
        mock_db_session.query.return_value.group_by.return_value.all.return_value = [
            (uuid4(), 3),
            (uuid4(), 2),
        ]

        # Execute
        result = await version_manager.get_version_statistics(skill_id)

        # Verify
        assert "total_versions" in result
        assert "versions_last_7_days" in result
        assert "versions_last_30_days" in result
        assert "avg_versions_per_file" in result
        assert "total_storage_used" in result
        assert "version_distribution" in result
        assert result["total_versions"] == 5

    @pytest.mark.asyncio
    async def test_get_version_statistics_no_skill_id(self, version_manager, mock_db_session):
        """Test get version statistics without skill filter."""
        # Setup
        # Mock query results
        mock_db_session.query.return_value.count.return_value = 10
        mock_db_session.query.return_value.filter.return_value.count.return_value = 3
        mock_db_session.query.return_value.filter.return_value.count.return_value = 7
        mock_db_session.query.return_value.with_entities.return_value.scalar.return_value = 20480
        mock_db_session.query.return_value.group_by.return_value.all.return_value = [
            (uuid4(), 1),
            (uuid4(), 5),
            (uuid4(), 10),
        ]

        # Execute
        result = await version_manager.get_version_statistics()

        # Verify
        assert "total_versions" in result
        assert result["total_versions"] == 10
        assert result["avg_versions_per_file"] == 0  # No skill filter

    @pytest.mark.asyncio
    async def test_get_version_statistics_no_files(self, version_manager, mock_db_session, test_skill_file):
        """Test get version statistics when skill has no files."""
        # Setup
        skill_id = test_skill_file.skill_id

        # Mock query results
        mock_db_session.query.return_value.count.return_value = 0
        mock_db_session.query.return_value.filter.return_value.count.return_value = 0
        mock_db_session.query.return_value.filter.return_value.count.return_value = 0
        mock_db_session.query.return_value.join.return_value.filter.return_value.scalar.return_value = 0
        mock_db_session.query.return_value.with_entities.return_value.scalar.return_value = 0
        mock_db_session.query.return_value.group_by.return_value.all.return_value = []

        # Execute
        result = await version_manager.get_version_statistics(skill_id)

        # Verify
        assert result["total_versions"] == 0
        assert result["avg_versions_per_file"] == 0

    # Test helper methods
    @pytest.mark.asyncio
    async def test_get_source_file_success(self, version_manager, mock_db_session, test_skill_file):
        """Test successful get source file."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Execute
        result = await version_manager._get_source_file(skill_id, file_path)

        # Verify
        assert result == test_skill_file

    @pytest.mark.asyncio
    async def test_get_source_file_not_found(self, version_manager, mock_db_session):
        """Test get source file when not found."""
        # Setup
        skill_id = uuid4()
        file_path = "nonexistent.txt"

        # Mock source file doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = await version_manager._get_source_file(skill_id, file_path)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_get_version_success(self, version_manager, mock_db_session, test_file_version):
        """Test successful get version."""
        # Setup
        file_id = test_file_version.file_id
        version_id = test_file_version.version_id

        # Mock version exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_file_version

        # Execute
        result = await version_manager._get_version(file_id, version_id)

        # Verify
        assert result == test_file_version

    @pytest.mark.asyncio
    async def test_get_version_not_found(self, version_manager, mock_db_session):
        """Test get version when not found."""
        # Setup
        file_id = uuid4()
        version_id = uuid4().hex

        # Mock version doesn't exist
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = await version_manager._get_version(file_id, version_id)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_get_next_version_number_success(self, version_manager, mock_db_session, test_skill_file):
        """Test successful get next version number."""
        # Setup
        file_id = test_skill_file.id

        # Mock max version number
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 5

        # Execute
        result = await version_manager._get_next_version_number(file_id)

        # Verify
        assert result == 6

    @pytest.mark.asyncio
    async def test_get_next_version_number_no_versions(self, version_manager, mock_db_session):
        """Test get next version number when no versions exist."""
        # Setup
        file_id = uuid4()

        # Mock no versions
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = None

        # Execute
        result = await version_manager._get_next_version_number(file_id)

        # Verify
        assert result == 1

    def test_generate_version_object_name(self, version_manager, test_skill_file):
        """Test version object name generation."""
        # Setup
        file_id = test_skill_file.id
        file_path = "test/subdir/file.txt"
        version_id = uuid4().hex

        # Execute
        result = version_manager._generate_version_object_name(file_id, file_path, version_id)

        # Verify
        assert "versions" in result
        assert str(file_id) in result
        assert "test_subdir_file.txt" in result
        assert version_id in result

    def test_generate_version_object_name_special_chars(self, version_manager):
        """Test version object name generation with special characters."""
        # Setup
        file_id = uuid4()
        file_path = "test\\path/with\\special.txt"
        version_id = uuid4().hex

        # Execute
        result = version_manager._generate_version_object_name(file_id, file_path, version_id)

        # Verify
        assert result is not None
        assert "/" in result or "_" in result

    # Test versioning operation context manager
    @pytest.mark.asyncio
    async def test_versioning_operation_context_success(self, version_manager):
        """Test versioning operation context manager success."""
        # Execute
        async with version_manager.versioning_operation("test_operation"):
            # Do nothing
            pass

        # Verify - no exceptions raised

    @pytest.mark.asyncio
    async def test_versioning_operation_context_failure(self, version_manager):
        """Test versioning operation context manager with failure."""
        # Execute and verify
        with pytest.raises(ValueError):
            async with version_manager.versioning_operation("test_operation"):
                raise ValueError("Test error")

    # Test integration scenarios
    @pytest.mark.asyncio
    async def test_full_version_lifecycle(self, version_manager, mock_minio_client, mock_db_session, mock_storage_manager, test_skill_file):
        """Test complete version lifecycle: create -> list -> compare -> restore -> delete."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        file_data = b"test file content"
        version_id = uuid4().hex

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version number query
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock MinIO operations
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "versions/test.txt/abc123",
            "etag": "etag123",
            "size": 1024,
        }

        # 1. Create version
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
        )
        result = await version_manager.create_version(request, file_data)
        assert result is not None

        # 2. List versions (reset mock for list operation)
        test_file_version = FileVersion(
            id=uuid4(),
            file_id=test_skill_file.id,
            version_id=version_id,
            version_number=1,
            object_name="versions/test.txt/abc123",
            file_size=1024,
            checksum="abc123",
            comment="Initial version",
            metadata={},
            created_by="system",
            created_at=datetime.utcnow(),
            is_latest=True,
        )
        mock_db_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.offset.return_value.return_value = [test_file_version]

        versions = await version_manager.list_versions(skill_id, file_path)
        assert len(versions) == 1

        # 3. Compare versions (reset mock for compare operation)
        test_file_version2 = FileVersion(
            id=uuid4(),
            file_id=test_skill_file.id,
            version_id=uuid4().hex,
            version_number=2,
            object_name="versions/test.txt/def456",
            file_size=1025,
            checksum="def456",
            comment="Second version",
            metadata={},
            created_by="system",
            created_at=datetime.utcnow(),
            is_latest=True,
        )
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [test_file_version, test_file_version2]

        mock_response1 = io.BytesIO(b"content version 1")
        mock_response2 = io.BytesIO(b"content version 2")
        mock_minio_client.get_object.side_effect = [mock_response1, mock_response2]

        comparison = await version_manager.compare_versions(
            skill_id, file_path, version_id, test_file_version2.version_id
        )
        assert "differences" in comparison

        # 4. Restore version (reset mock for restore operation)
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [test_skill_file, test_file_version]
        mock_response = io.BytesIO(b"test file content")
        mock_minio_client.get_object.return_value = mock_response
        mock_storage_manager.upload_file.return_value = Mock(success=True)

        restore_request = FileVersionRestoreRequest(
            skill_id=skill_id,
            file_path=file_path,
            version_id=version_id,
        )
        restore_result = await version_manager.restore_version(restore_request)
        assert restore_result is True

        # 5. Delete version (reset mock for delete operation)
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [test_skill_file, test_file_version]
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 2
        mock_minio_client.remove_object.return_value = None

        delete_result = await version_manager.delete_version(skill_id, file_path, version_id)
        assert delete_result is True

    @pytest.mark.asyncio
    async def test_versioning_with_database_transaction_rollback(self, version_manager, mock_minio_client, mock_db_session, test_skill_file):
        """Test version creation rollback on database error."""
        # Setup
        skill_id = test_skill_file.skill_id
        file_path = "test.txt"
        file_data = b"test file content"

        # Mock source file exists
        mock_db_session.query.return_value.filter.return_value.first.return_value = test_skill_file

        # Mock version number query
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0

        # Mock MinIO upload
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "versions/test.txt/abc123",
            "etag": "etag123",
            "size": 1024,
        }

        # Mock database error on commit
        mock_db_session.commit.side_effect = SQLAlchemyError("Transaction failed")

        # Execute and verify
        request = FileVersionCreateRequest(
            skill_id=skill_id,
            file_path=file_path,
        )

        with pytest.raises(VersioningError):
            await version_manager.create_version(request, file_data)

        # Verify rollback was called
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_versioning_error_handling(self, version_manager, mock_minio_client, mock_db_session):
        """Test comprehensive error handling in versioning."""
        # Test various error scenarios
        errors = [
            (VersionNotFoundError, mock_db_session, "File not found"),
            (VersionLimitExceededError, mock_minio_client, "Version limit exceeded"),
            (VersionRestoreError, mock_minio_client, "Version restore failed"),
        ]

        for expected_error, mock_obj, error_msg in errors:
            # Verify error classes exist and can be raised
            assert issubclass(expected_error, VersioningError)

    # Test configuration validation
    def test_version_manager_configuration(self, mock_minio_client, mock_storage_manager, mock_db_session):
        """Test VersionManager with different configurations."""
        # Test with custom max versions
        version_manager = VersionManager(
            minio_client=mock_minio_client,
            storage_manager=mock_storage_manager,
            database_session=mock_db_session,
            max_versions=50,
            cleanup_threshold_days=30,
        )
        assert version_manager.max_versions == 50
        assert version_manager.cleanup_threshold_days == 30

        # Test with default configuration
        version_manager = VersionManager(
            minio_client=mock_minio_client,
            storage_manager=mock_storage_manager,
            database_session=mock_db_session,
        )
        assert version_manager.max_versions == 10
        assert version_manager.cleanup_threshold_days == 90
