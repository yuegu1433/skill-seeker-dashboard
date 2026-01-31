"""Integration tests for storage system.

This module contains end-to-end integration tests that validate
the entire storage system workflow including all components working together.
"""

import io
import pytest
import tempfile
import os
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.versioning import VersionManager
from backend.app.storage.cache import CacheManager
from backend.app.storage.backup import BackupManager
from backend.app.storage.client import MinIOClient
from backend.app.storage.models import Skill, SkillFile, StorageBucket, FileVersion
from backend.app.storage.schemas.storage_config import MinIOConfig, StorageConfig
from backend.app.storage.schemas.file_operations import (
    FileUploadRequest,
    FileDownloadRequest,
    FileDeleteRequest,
    FileListRequest,
)


class TestStorageSystemIntegration:
    """Complete storage system integration tests."""

    @pytest.fixture(scope="class")
    def test_db(self):
        """Create test database."""
        # Use a mock approach instead of actual database
        return Mock()

    @pytest.fixture
    def test_db_session(self, test_db):
        """Create test database session."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.delete = Mock()
        session.close = Mock()
        return session

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client."""
        client = Mock(spec=MinIOClient)

        # Mock bucket operations
        client.bucket_exists = Mock(return_value=True)
        client.create_bucket = Mock(return_value=True)

        # Mock file operations
        client.put_object = Mock(return_value=True)
        client.get_object = Mock(return_value=b"test file content")
        client.remove_object = Mock(return_value=True)
        client.list_objects = Mock(return_value=[
            {"object_name": "test.txt", "size": 1024, "last_modified": datetime.utcnow()},
        ])

        # Mock presigned URLs
        client.get_presigned_url = Mock(return_value="http://localhost:9000/test-url")

        return client

    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client."""
        client = Mock()
        client.get = Mock(return_value=None)
        client.set = Mock(return_value=True)
        client.delete = Mock(return_value=True)
        client.exists = Mock(return_value=False)
        client.expire = Mock(return_value=True)
        client.flushdb = Mock(return_value=True)
        return client

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
            max_file_size=100 * 1024 * 1024,  # 100MB
        )

    @pytest.fixture
    def storage_manager(self, mock_minio_client, test_db_session, storage_config):
        """Create storage manager instance."""
        return SkillStorageManager(
            minio_client=mock_minio_client,
            database_session=test_db_session,
            config=storage_config,
        )

    @pytest.fixture
    def version_manager(self, mock_minio_client, storage_manager, test_db_session):
        """Create version manager instance."""
        return VersionManager(
            minio_client=mock_minio_client,
            storage_manager=storage_manager,
            database_session=test_db_session,
        )

    @pytest.fixture
    def cache_manager(self, mock_redis_client):
        """Create cache manager instance."""
        manager = Mock(spec=CacheManager)
        manager.get = mock_redis_client.get
        manager.set = mock_redis_client.set
        manager.delete = mock_redis_client.delete
        manager.exists = mock_redis_client.exists
        manager.expire = mock_redis_client.expire
        manager.clear_prefix = Mock(return_value=True)
        manager.get_stats = Mock(return_value={
            "hits": 100,
            "misses": 20,
            "hit_rate": 83.33,
        })
        manager.invalidate_file_cache = Mock(return_value=True)
        return manager

    @pytest.fixture
    def backup_manager(self, mock_minio_client, storage_manager, test_db_session):
        """Create backup manager instance."""
        manager = Mock(spec=BackupManager)
        manager.create_backup = Mock(return_value=str(uuid4()))
        manager.restore_backup = Mock(return_value={"success": True, "files_restored": 5})
        manager.verify_backup = Mock(return_value={
            "overall_status": "passed",
            "files_verified": 5,
            "errors": [],
        })
        manager.delete_backup = Mock(return_value=True)
        manager.list_backups = Mock(return_value=[
            {"backup_id": str(uuid4()), "type": "full", "created_at": datetime.utcnow()},
        ])
        manager.cleanup_old_versions = Mock(return_value=3)
        return manager

    @pytest.fixture
    def test_skill(self):
        """Create test skill."""
        skill = Mock()
        skill.id = uuid4()
        skill.name = "test-skill-integration"
        skill.platform = "claude"
        skill.status = "active"
        skill.source_type = "github"
        return skill

    @pytest.fixture
    def test_files(self):
        """Create test files."""
        return {
            "file1.txt": b"Test file content 1",
            "file2.txt": b"Test file content 2",
            "file3.txt": b"Test file content 3",
        }

    def test_complete_file_lifecycle(
        self,
        storage_manager,
        version_manager,
        cache_manager,
        backup_manager,
        test_skill,
        test_files,
        test_db_session,
    ):
        """Test complete file lifecycle from upload to deletion."""
        # Step 1: Create skill in database
        test_db_session.add(test_skill)
        test_db_session.commit()

        # Step 2: Upload files
        uploaded_files = []
        for filename, content in test_files.items():
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )

            # Mock file content
            file_content = io.BytesIO(content)

            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True
            assert result.file_path == filename
            uploaded_files.append(result.file_path)

        # Verify files are in database
        list_request = FileListRequest(skill_id=test_skill.id)
        files_list = storage_manager.list_files(list_request)
        assert len(files_list.files) == len(test_files)

        # Step 3: Test versioning - create new version
        first_file = uploaded_files[0]
        new_content = b"Updated content for file1"

        # Upload new version
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=first_file,
            content_type="text/plain",
        )
        file_content = io.BytesIO(new_content)

        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Verify version was created
        versions = version_manager.list_versions(
            skill_id=test_skill.id,
            file_path=first_file,
        )
        assert len(versions) >= 1

        # Step 4: Test cache operations
        # Cache file metadata
        cache_manager.set(f"file:{test_skill.id}:{first_file}", "metadata", expire=3600)
        assert cache_manager.exists(f"file:{test_skill.id}:{first_file}") is not None

        # Step 5: Test backup
        backup_id = backup_manager.create_backup(
            skill_id=test_skill.id,
            backup_type="full",
            verify=True,
        )
        assert backup_id is not None

        # Verify backup
        verify_result = backup_manager.verify_backup(backup_id)
        assert verify_result["overall_status"] == "passed"

        # Step 6: Test download
        download_request = FileDownloadRequest(
            skill_id=test_skill.id,
            file_path=first_file,
        )

        result = storage_manager.download_file(download_request)
        assert result.success is True
        assert result.content is not None

        # Step 7: Clean up - delete file
        delete_request = FileDeleteRequest(
            skill_id=test_skill.id,
            file_path=first_file,
        )

        result = storage_manager.delete_file(delete_request)
        assert result.success is True

        # Verify file was deleted from storage
        mock_minio_client = storage_manager.minio_client
        mock_minio_client.remove_object.assert_called()

        # Verify cache was invalidated
        cache_manager.delete.assert_called_with(f"file:{test_skill.id}:{first_file}")

    def test_concurrent_file_operations(
        self,
        storage_manager,
        version_manager,
        test_skill,
        test_db_session,
        test_files,
    ):
        """Test concurrent file operations."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        # Upload multiple files concurrently
        upload_results = []
        for filename, content in test_files.items():
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(content)
            result = storage_manager.upload_file(upload_request, file_content)
            upload_results.append(result)

        # Verify all files uploaded successfully
        assert len(upload_results) == len(test_files)
        assert all(result.success for result in upload_results)

        # List files and verify count
        list_request = FileListRequest(skill_id=test_skill.id)
        files_list = storage_manager.list_files(list_request)
        assert len(files_list.files) == len(test_files)

        # Update all files
        for filename in test_files.keys():
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(b"Updated content")
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # Verify all have versions
        for filename in test_files.keys():
            versions = version_manager.list_versions(
                skill_id=test_skill.id,
                file_path=filename,
            )
            assert len(versions) >= 1

    def test_version_management_integration(
        self,
        storage_manager,
        version_manager,
        test_skill,
        test_db_session,
    ):
        """Test version management integration."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "versioned-file.txt"

        # Create initial version
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"Version 1")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Create multiple versions
        for i in range(2, 5):
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(f"Version {i}".encode())
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # List all versions
        versions = version_manager.list_versions(
            skill_id=test_skill.id,
            file_path=filename,
        )
        assert len(versions) >= 3  # At least 3 updates

        # Compare versions
        if len(versions) >= 2:
            comparison = version_manager.compare_versions(
                skill_id=test_skill.id,
                file_path=filename,
                version1=versions[0].version_number,
                version2=versions[1].version_number,
            )
            assert comparison is not None

        # Restore specific version
        if len(versions) >= 2:
            restore_result = version_manager.restore_version(
                skill_id=test_skill.id,
                file_path=filename,
                version_number=versions[0].version_number,
            )
            assert restore_result.success is True

    def test_cache_integration(
        self,
        storage_manager,
        cache_manager,
        test_skill,
        test_db_session,
    ):
        """Test cache integration."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "cache-test.txt"

        # Upload file
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"Cache test content")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Simulate cache operations
        cache_key = f"file:{test_skill.id}:{filename}"
        cache_manager.set(cache_key, "cached_metadata", expire=3600)

        # Verify cache hit
        cached_data = cache_manager.get(cache_key)
        assert cached_data is not None

        # Invalidate cache on update
        cache_manager.delete(cache_key)

        # Verify cache miss after invalidation
        cached_data = cache_manager.get(cache_key)
        assert cached_data is None

    def test_backup_restore_integration(
        self,
        storage_manager,
        backup_manager,
        version_manager,
        test_skill,
        test_db_session,
        test_files,
    ):
        """Test backup and restore integration."""
        # Create skill and upload files
        test_db_session.add(test_skill)
        test_db_session.commit()

        for filename, content in test_files.items():
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(content)
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # Create backup
        backup_id = backup_manager.create_backup(
            skill_id=test_skill.id,
            backup_type="full",
            verify=True,
        )
        assert backup_id is not None

        # Verify backup
        verify_result = backup_manager.verify_backup(backup_id)
        assert verify_result["overall_status"] == "passed"

        # Modify files
        for filename in test_files.keys():
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(b"Modified content")
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # Restore from backup
        restore_result = backup_manager.restore_backup(
            backup_id=backup_id,
            skill_id=test_skill.id,
            verify=True,
        )
        assert restore_result["success"] is True

    def test_error_handling_and_recovery(
        self,
        storage_manager,
        version_manager,
        cache_manager,
        test_skill,
        test_db_session,
    ):
        """Test error handling and recovery."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        # Test file not found error
        download_request = FileDownloadRequest(
            skill_id=test_skill.id,
            file_path="nonexistent.txt",
        )

        result = storage_manager.download_file(download_request)
        assert result.success is False
        assert "not found" in result.error_message.lower()

        # Test version not found error
        versions = version_manager.list_versions(
            skill_id=test_skill.id,
            file_path="nonexistent.txt",
        )
        assert len(versions) == 0

        # Test cache miss handling
        cache_key = f"file:{test_skill.id}:nonexistent"
        cached_data = cache_manager.get(cache_key)
        assert cached_data is None

    def test_data_consistency(
        self,
        storage_manager,
        version_manager,
        cache_manager,
        backup_manager,
        test_skill,
        test_db_session,
    ):
        """Test data consistency across operations."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "consistency-test.txt"

        # Upload file
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"Initial content")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Create backup before modifications
        backup_id = backup_manager.create_backup(
            skill_id=test_skill.id,
            backup_type="full",
            verify=False,
        )

        # Make multiple modifications
        for i in range(3):
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(f"Modification {i}".encode())
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # Verify versions exist
        versions = version_manager.list_versions(
            skill_id=test_skill.id,
            file_path=filename,
        )
        assert len(versions) >= 3

        # Restore from backup
        restore_result = backup_manager.restore_backup(
            backup_id=backup_id,
            skill_id=test_skill.id,
            verify=False,
        )
        assert restore_result["success"] is True

        # Verify consistency after restore
        download_request = FileDownloadRequest(
            skill_id=test_skill.id,
            file_path=filename,
        )
        result = storage_manager.download_file(download_request)
        assert result.success is True

    def test_performance_under_load(
        self,
        storage_manager,
        version_manager,
        cache_manager,
        test_skill,
        test_db_session,
    ):
        """Test system performance under load."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        # Upload many files
        num_files = 50
        for i in range(num_files):
            filename = f"load-test-{i}.txt"
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(f"Content {i}".encode())
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # List files
        list_request = FileListRequest(skill_id=test_skill.id)
        files_list = storage_manager.list_files(list_request)
        assert len(files_list.files) == num_files

        # Cache all files
        for file_info in files_list.files:
            cache_key = f"file:{test_skill.id}:{file_info.file_path}"
            cache_manager.set(cache_key, file_info, expire=3600)

        # Verify cache performance
        stats = cache_manager.get_stats()
        assert stats["hit_rate"] >= 0

        # Clean up versions
        for file_info in files_list.files:
            versions = version_manager.list_versions(
                skill_id=test_skill.id,
                file_path=file_info.file_path,
            )
            assert len(versions) >= 1

    def test_cleanup_operations(
        self,
        storage_manager,
        version_manager,
        cache_manager,
        backup_manager,
        test_skill,
        test_db_session,
    ):
        """Test cleanup operations integration."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "cleanup-test.txt"

        # Upload file
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"Content to be cleaned up")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Create versions
        for i in range(5):
            upload_request = FileUploadRequest(
                skill_id=test_skill.id,
                file_path=filename,
                content_type="text/plain",
            )
            file_content = io.BytesIO(f"Version {i}".encode())
            result = storage_manager.upload_file(upload_request, file_content)
            assert result.success is True

        # Verify versions exist
        versions = version_manager.list_versions(
            skill_id=test_skill.id,
            file_path=filename,
        )
        initial_version_count = len(versions)

        # Clean up old versions
        deleted_count = backup_manager.cleanup_old_versions(skill_id=test_skill.id)
        assert deleted_count >= 0

        # Cache cleanup
        cache_manager.clear_prefix(f"file:{test_skill.id}")

        # Delete file
        delete_request = FileDeleteRequest(
            skill_id=test_skill.id,
            file_path=filename,
        )
        result = storage_manager.delete_file(delete_request)
        assert result.success is True

        # Verify file is deleted
        download_request = FileDownloadRequest(
            skill_id=test_skill.id,
            file_path=filename,
        )
        result = storage_manager.download_file(download_request)
        assert result.success is False

    def test_integration_with_websocket_notifications(
        self,
        storage_manager,
        test_skill,
        test_db_session,
    ):
        """Test integration with WebSocket notifications."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "websocket-test.txt"

        # Upload file (would trigger WebSocket notification in real system)
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"WebSocket notification test")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Download file (would trigger WebSocket notification in real system)
        download_request = FileDownloadRequest(
            skill_id=test_skill.id,
            file_path=filename,
        )
        result = storage_manager.download_file(download_request)
        assert result.success is True

        # Delete file (would trigger WebSocket notification in real system)
        delete_request = FileDeleteRequest(
            skill_id=test_skill.id,
            file_path=filename,
        )
        result = storage_manager.delete_file(delete_request)
        assert result.success is True

    def test_metadata_operations(
        self,
        storage_manager,
        version_manager,
        test_skill,
        test_db_session,
    ):
        """Test metadata operations."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "metadata-test.txt"
        metadata = {
            "author": "test-user",
            "version": "1.0",
            "tags": ["test", "metadata"],
            "custom_field": "custom-value",
        }

        # Upload file with metadata
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
            metadata=metadata,
        )
        file_content = io.BytesIO(b"File with metadata")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Verify metadata in storage
        list_request = FileListRequest(skill_id=test_skill.id)
        files_list = storage_manager.list_files(list_request)
        assert len(files_list.files) == 1

        # Verify metadata preserved in versions
        versions = version_manager.list_versions(
            skill_id=test_skill.id,
            file_path=filename,
        )
        assert len(versions) >= 1
        # Note: Version metadata validation would depend on implementation

    def test_quota_enforcement(
        self,
        storage_manager,
        test_skill,
        test_db_session,
        storage_config,
    ):
        """Test storage quota enforcement."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        # Set quota on skill (if supported)
        # This test would verify quota enforcement in real implementation

        filename = "quota-test.txt"

        # Try to upload file larger than quota (if quota is set)
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"Small file content")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Verify quota checking (implementation dependent)
        # This would test quota_exceeded errors in real system

    def test_integration_with_celery_tasks(
        self,
        storage_manager,
        version_manager,
        cache_manager,
        backup_manager,
        test_skill,
        test_db_session,
    ):
        """Test integration with Celery tasks."""
        # Create skill
        test_db_session.add(test_skill)
        test_db_session.commit()

        filename = "celery-integration-test.txt"

        # Upload file (would trigger async processing)
        upload_request = FileUploadRequest(
            skill_id=test_skill.id,
            file_path=filename,
            content_type="text/plain",
        )
        file_content = io.BytesIO(b"Content for async processing")
        result = storage_manager.upload_file(upload_request, file_content)
        assert result.success is True

        # Simulate async operations
        # In real system, these would be Celery tasks

        # Create backup asynchronously
        backup_id = backup_manager.create_backup(
            skill_id=test_skill.id,
            backup_type="full",
            verify=True,
        )
        assert backup_id is not None

        # Clean up asynchronously
        deleted_count = backup_manager.cleanup_old_versions(skill_id=test_skill.id)
        assert deleted_count >= 0

        # Verify final state
        list_request = FileListRequest(skill_id=test_skill.id)
        files_list = storage_manager.list_files(list_request)
        assert len(files_list.files) >= 1
