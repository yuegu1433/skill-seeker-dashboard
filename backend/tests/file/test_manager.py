"""Tests for FileManager.

This module contains unit tests for the FileManager class using mocks
to simulate database and storage operations.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List

# Import manager and schemas
from app.file.manager import FileManager
from app.file.schemas.file_operations import (
    FileCreate,
    FileUpdate,
    FileDelete,
    FileRestore,
    FileMove,
    FileCopy,
    FileFilter,
    FileSearch,
    FileBulkOperation,
)
from app.file.models.file import File, FileStatus, FileType


class TestFileManager:
    """Test suite for FileManager."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_manager(self, db_session):
        """Create FileManager instance with mocked database."""
        return FileManager(db_session)

    @pytest.fixture
    def sample_file_id(self):
        """Generate sample file ID."""
        return uuid4()

    @pytest.fixture
    def sample_user_id(self):
        """Generate sample user ID."""
        return "user123"

    @pytest.fixture
    def sample_file_create(self):
        """Create sample file creation data."""
        return FileCreate(
            name="test.txt",
            content=b"test content",
            mime_type="text/plain",
            size=12,
            owner_id="user123",
            storage_key="test/user123/test.txt",
            bucket="files",
        )

    @pytest.fixture
    def sample_file(self, sample_file_id, sample_user_id):
        """Create sample file model."""
        file = Mock()
        file.id = sample_file_id
        file.name = "test.txt"
        file.original_name = "test.txt"
        file.path = "test/user123/test.txt"
        file.size = 12
        file.mime_type = "text/plain"
        file.extension = ".txt"
        file.type = FileType.DOCUMENT
        file.status = FileStatus.ACTIVE
        file.owner_id = sample_user_id
        file.parent_id = None
        file.folder_id = "folder1"
        file.bucket = "files"
        file.storage_key = "test/user123/test.txt"
        file.checksum = "abc123"
        file.description = "Test file"
        file.tags = ["test"]
        file.metadata = {"key": "value"}
        file.is_public = False
        file.is_deleted = False
        file.is_folder = False
        file.is_file = True
        file.deleted_at = None
        file.created_at = datetime.utcnow()
        file.updated_at = datetime.utcnow()
        file.accessed_at = None
        file.version_count = 1
        file.download_count = 0
        file.preview_count = 0
        file.age_days = 0
        file.update_access_time = Mock()
        file.soft_delete = Mock()
        file.restore = Mock()
        return file

    @pytest.mark.asyncio
    async def test_create_file_success(self, file_manager, db_session, sample_file_create, sample_user_id):
        """Test successful file creation."""
        # Setup
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.refresh = AsyncMock()

        # Mock file creation
        with patch('app.file.manager.File.create_file') as mock_create:
            mock_file = Mock()
            mock_create.return_value = mock_file

            # Mock get_file_by_path to return None (file doesn't exist)
            with patch.object(file_manager, 'get_file_by_path', return_value=None):
                # Mock business validations
                with patch.object(file_manager.business_validator, 'validate_user_file_limit', return_value=(True, None)):
                    with patch.object(file_manager.business_validator, 'validate_user_storage_limit', return_value=(True, None)):
                        with patch.object(file_manager.file_validator, 'validate_file_name', return_value=(True, None)):
                            with patch.object(file_manager.file_validator, 'validate_file_size', return_value=(True, None)):
                                with patch.object(file_manager.file_validator, 'validate_file_type', return_value=(True, None)):
                                    with patch.object(file_manager.file_validator, 'validate_storage_path', return_value=(True, None)):
                                        # Mock FileResponse creation
                                        with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
                                            mock_response = Mock()
                                            mock_validate.return_value = mock_response

                                            # Execute
                                            result = await file_manager.create_file(sample_file_create, sample_user_id)

                                            # Assert
                                            assert result == mock_response
                                            mock_create.assert_called_once()
                                            db_session.add.assert_called_once_with(mock_file)
                                            db_session.commit.assert_called_once()
                                            db_session.refresh.assert_called_once_with(mock_file)

    @pytest.mark.asyncio
    async def test_create_file_validation_error(self, file_manager, db_session, sample_file_create, sample_user_id):
        """Test file creation with validation error."""
        # Setup
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.rollback = AsyncMock()

        # Mock validation failure
        with patch.object(file_manager.file_validator, 'validate_file_name', return_value=(False, "Invalid name")):
            # Execute and assert
            with pytest.raises(ValueError, match="Invalid file name"):
                await file_manager.create_file(sample_file_create, sample_user_id)

            db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_file_already_exists(self, file_manager, db_session, sample_file_create, sample_user_id):
        """Test file creation when file already exists."""
        # Setup
        db_session.add = Mock()
        db_session.commit = AsyncMock()
        db_session.rollback = AsyncMock()

        # Mock existing file
        with patch.object(file_manager, 'get_file_by_path', return_value=Mock()):
            # Execute and assert
            with pytest.raises(ValueError, match="File already exists"):
                await file_manager.create_file(sample_file_create, sample_user_id)

            db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_success(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test successful file retrieval."""
        # Setup
        query_result = Mock()
        query_result.scalar_one_or_none.return_value = sample_file
        db_session.execute = AsyncMock(return_value=query_result)

        # Mock permission check
        with patch.object(file_manager, '_check_file_permission', return_value=True):
            # Mock FileResponse creation
            with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
                mock_response = Mock()
                mock_validate.return_value = mock_response

                # Execute
                result = await file_manager.get_file(sample_file_id, sample_user_id)

                # Assert
                assert result == mock_response
                sample_file.update_access_time.assert_called_once()
                db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_not_found(self, file_manager, db_session, sample_file_id, sample_user_id):
        """Test file retrieval when file doesn't exist."""
        # Setup
        query_result = Mock()
        query_result.scalar_one_or_none.return_value = None
        db_session.execute = AsyncMock(return_value=query_result)

        # Execute
        result = await file_manager.get_file(sample_file_id, sample_user_id)

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_file_no_permission(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test file retrieval without permission."""
        # Setup
        query_result = Mock()
        query_result.scalar_one_or_none.return_value = sample_file
        db_session.execute = AsyncMock(return_value=query_result)

        # Mock permission denied
        with patch.object(file_manager, '_check_file_permission', return_value=False):
            # Execute
            result = await file_manager.get_file(sample_file_id, sample_user_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_update_file_success(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test successful file update."""
        # Setup
        update_data = FileUpdate(
            name="updated.txt",
            description="Updated description"
        )

        with patch.object(file_manager, '_get_file_by_id', return_value=sample_file):
            with patch.object(file_manager, '_check_file_permission', return_value=True):
                with patch.object(file_manager.file_validator, 'validate_file_name', return_value=(True, None)):
                    db_session.commit = AsyncMock()
                    db_session.refresh = AsyncMock()

                    # Mock FileResponse creation
                    with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
                        mock_response = Mock()
                        mock_validate.return_value = mock_response

                        # Execute
                        result = await file_manager.update_file(sample_file_id, update_data, sample_user_id)

                        # Assert
                        assert result == mock_response
                        assert sample_file.name == "updated.txt"
                        assert sample_file.description == "Updated description"
                        db_session.commit.assert_called_once()
                        db_session.refresh.assert_called_once_with(sample_file)

    @pytest.mark.asyncio
    async def test_update_file_not_found(self, file_manager, db_session, sample_file_id, sample_user_id):
        """Test file update when file doesn't exist."""
        # Setup
        update_data = FileUpdate(name="updated.txt")

        with patch.object(file_manager, '_get_file_by_id', return_value=None):
            # Execute
            result = await file_manager.update_file(sample_file_id, update_data, sample_user_id)

            # Assert
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test successful file deletion."""
        # Setup
        delete_data = FileDelete(permanent=False)

        with patch.object(file_manager, '_get_file_by_id', return_value=sample_file):
            with patch.object(file_manager, '_check_file_permission', return_value=True):
                db_session.commit = AsyncMock()

                # Execute
                result = await file_manager.delete_file(sample_file_id, sample_user_id, delete_data)

                # Assert
                assert result is True
                sample_file.soft_delete.assert_called_once()
                db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_file_permanent(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test permanent file deletion."""
        # Setup
        delete_data = FileDelete(permanent=True)

        with patch.object(file_manager, '_get_file_by_id', return_value=sample_file):
            with patch.object(file_manager, '_check_file_permission', return_value=True):
                db_session.delete = Mock()
                db_session.commit = AsyncMock()

                # Execute
                result = await file_manager.delete_file(sample_file_id, sample_user_id, delete_data)

                # Assert
                assert result is True
                db_session.delete.assert_called_once_with(sample_file)

    @pytest.mark.asyncio
    async def test_delete_file_not_found(self, file_manager, db_session, sample_file_id, sample_user_id):
        """Test file deletion when file doesn't exist."""
        # Setup
        delete_data = FileDelete()

        with patch.object(file_manager, '_get_file_by_id', return_value=None):
            # Execute
            result = await file_manager.delete_file(sample_file_id, sample_user_id, delete_data)

            # Assert
            assert result is False

    @pytest.mark.asyncio
    async def test_restore_file_success(self, file_manager, db_session, sample_file_id, sample_user_id):
        """Test successful file restoration."""
        # Setup
        deleted_file = Mock()
        deleted_file.is_deleted = True

        query_result = Mock()
        query_result.scalar_one_or_none.return_value = deleted_file
        db_session.execute = AsyncMock(return_value=query_result)

        restore_data = FileRestore()

        with patch.object(file_manager, '_check_file_permission', return_value=True):
            db_session.commit = AsyncMock()
            db_session.refresh = AsyncMock()

            with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
                mock_response = Mock()
                mock_validate.return_value = mock_response

                # Execute
                result = await file_manager.restore_file(sample_file_id, sample_user_id, restore_data)

                # Assert
                assert result == mock_response
                deleted_file.restore.assert_called_once()
                db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_files_success(self, file_manager, db_session, sample_user_id):
        """Test successful file listing."""
        # Setup
        files = [Mock(), Mock()]
        total = 2

        # Mock query execution
        query_result = Mock()
        query_result.scalars.return_value.all.return_value = files
        db_session.execute = AsyncMock(return_value=query_result)

        # Mock count query
        count_result = Mock()
        count_result.scalar.return_value = total
        db_session.execute = AsyncMock(return_value=count_result)

        filters = FileFilter()

        # Mock FileResponse creation
        with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response

            # Execute
            result = await file_manager.list_files(filters, sample_user_id)

            # Assert
            assert result.total == total
            assert len(result.files) == 2
            assert result.page == 1
            assert result.page_size == 20

    @pytest.mark.asyncio
    async def test_search_files_success(self, file_manager, db_session, sample_user_id):
        """Test successful file search."""
        # Setup
        files = [Mock()]
        total = 1

        # Mock query execution
        query_result = Mock()
        query_result.scalars.return_value.all.return_value = files
        db_session.execute = AsyncMock(return_value=query_result)

        # Mock count query
        count_result = Mock()
        count_result.scalar.return_value = total
        db_session.execute = AsyncMock(return_value=count_result)

        search = FileSearch(
            query="test",
            page=1,
            page_size=10
        )

        # Mock FileResponse creation
        with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
            mock_response = Mock()
            mock_validate.return_value = mock_response

            # Execute
            result = await file_manager.search_files(search, sample_user_id)

            # Assert
            assert result.total == total
            assert len(result.files) == 1
            assert result.query == "test"
            assert result.search_time >= 0

    @pytest.mark.asyncio
    async def test_bulk_operation_success(self, file_manager, db_session, sample_user_id):
        """Test successful bulk operation."""
        # Setup
        file_ids = [uuid4(), uuid4()]
        operation = FileBulkOperation(
            operation="delete",
            file_ids=file_ids
        )

        # Mock _process_batch
        results = [
            {"file_id": str(file_ids[0]), "status": "success"},
            {"file_id": str(file_ids[1]), "status": "success"}
        ]
        errors = []

        with patch.object(file_manager, '_process_batch', return_value=(results, errors)):
            # Execute
            result = await file_manager.bulk_operation(operation, sample_user_id)

            # Assert
            assert result.operation == "delete"
            assert result.total_files == 2
            assert result.successful == 2
            assert result.failed == 0
            assert len(result.results) == 2
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_move_file_success(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test successful file move."""
        # Setup
        move_data = FileMove(
            target_folder_id="new_folder",
            new_name="moved.txt"
        )

        with patch.object(file_manager, '_get_file_by_id', return_value=sample_file):
            with patch.object(file_manager, '_check_file_permission', return_value=True):
                db_session.commit = AsyncMock()
                db_session.refresh = AsyncMock()

                # Mock FileResponse creation
                with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
                    mock_response = Mock()
                    mock_validate.return_value = mock_response

                    # Execute
                    result = await file_manager.move_file(sample_file_id, move_data, sample_user_id)

                    # Assert
                    assert result == mock_response
                    assert sample_file.folder_id == "new_folder"
                    assert sample_file.name == "moved.txt"
                    db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_copy_file_success(self, file_manager, db_session, sample_file_id, sample_user_id, sample_file):
        """Test successful file copy."""
        # Setup
        copy_data = FileCopy(
            target_folder_id="new_folder",
            new_name="copy.txt"
        )

        # Mock _get_file_by_id
        with patch.object(file_manager, '_get_file_by_id', return_value=sample_file):
            with patch.object(file_manager, '_check_file_permission', return_value=True):
                # Mock File.create_file
                with patch('app.file.manager.File.create_file') as mock_create:
                    new_file = Mock()
                    new_file.id = uuid4()
                    mock_create.return_value = new_file

                    db_session.add = Mock()
                    db_session.commit = AsyncMock()
                    db_session.refresh = AsyncMock()

                    # Mock FileResponse creation
                    with patch('app.file.schemas.file_operations.FileResponse.model_validate') as mock_validate:
                        mock_response = Mock()
                        mock_validate.return_value = mock_response

                        # Execute
                        result = await file_manager.copy_file(sample_file_id, copy_data, sample_user_id)

                        # Assert
                        assert result == mock_response
                        mock_create.assert_called_once()
                        db_session.add.assert_called_once_with(new_file)
                        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_file_statistics(self, file_manager, db_session, sample_user_id):
        """Test getting file statistics."""
        # Setup
        db_session.execute = AsyncMock()

        # Mock total files query
        total_result = Mock()
        total_result.scalar.return_value = 100
        db_session.execute.return_value = total_result

        # Mock storage query
        storage_result = Mock()
        storage_result.scalar.return_value = 1024 * 1024  # 1MB
        db_session.execute.return_value = storage_result

        # Mock type query
        type_result = Mock()
        type_result.all.return_value = [("document", 50), ("image", 30)]
        db_session.execute.return_value = type_result

        # Mock status query
        status_result = Mock()
        status_result.all.return_value = [("active", 90), ("archived", 10)]
        db_session.execute.return_value = status_result

        # Execute
        result = await file_manager.get_file_statistics(sample_user_id)

        # Assert
        assert result["total_files"] == 100
        assert result["total_storage"] == 1024 * 1024
        assert "total_storage_formatted" in result
        assert result["files_by_type"]["document"] == 50
        assert result["files_by_type"]["image"] == 30
        assert result["files_by_status"]["active"] == 90
        assert result["files_by_status"]["archived"] == 10

    @pytest.mark.asyncio
    async def test_get_user_file_count(self, file_manager, db_session, sample_user_id):
        """Test getting user file count."""
        # Setup
        count_result = Mock()
        count_result.scalar.return_value = 42
        db_session.execute = AsyncMock(return_value=count_result)

        # Execute
        result = await file_manager.get_user_file_count(sample_user_id)

        # Assert
        assert result == 42

    @pytest.mark.asyncio
    async def test_get_user_storage_used(self, file_manager, db_session, sample_user_id):
        """Test getting user storage usage."""
        # Setup
        storage_result = Mock()
        storage_result.scalar.return_value = 2048 * 1024  # 2MB
        db_session.execute = AsyncMock(return_value=storage_result)

        # Execute
        result = await file_manager.get_user_storage_used(sample_user_id)

        # Assert
        assert result == 2048 * 1024

    @pytest.mark.asyncio
    async def test_check_file_permission_owner(self, file_manager, sample_file, sample_user_id):
        """Test permission check for file owner."""
        # Setup
        sample_file.owner_id = sample_user_id

        # Execute
        result = await file_manager._check_file_permission(sample_file, sample_user_id, "read")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_check_file_permission_public(self, file_manager, sample_file, sample_user_id):
        """Test permission check for public file."""
        # Setup
        sample_file.owner_id = "other_user"
        sample_file.is_public = True

        # Execute
        result = await file_manager._check_file_permission(sample_file, sample_user_id, "read")

        # Assert
        assert result is True

    @pytest.mark.asyncio
    async def test_apply_filters(self, file_manager):
        """Test filter application."""
        # Setup
        from sqlalchemy import select
        query = select(File)

        filters = FileFilter(
            name="test",
            type=FileType.DOCUMENT,
            status=FileStatus.ACTIVE,
            owner_id="user123",
            is_public=True
        )

        # Execute
        result = await file_manager._apply_filters(query, filters)

        # The result should be a modified query
        # In a real implementation, we would check the WHERE clauses
        assert result is not None

    @pytest.mark.asyncio
    async def test_error_handling(self, file_manager, db_session, sample_file_id, sample_user_id):
        """Test error handling in various operations."""
        # Setup
        db_session.commit = AsyncMock(side_effect=Exception("Database error"))

        sample_file_create = FileCreate(
            name="test.txt",
            content=b"test",
            mime_type="text/plain",
            size=4,
            owner_id=sample_user_id,
            storage_key="test.txt"
        )

        # Execute and assert
        with pytest.raises(Exception, match="Database error"):
            await file_manager.create_file(sample_file_create, sample_user_id)

        db_session.rollback.assert_called_once()
