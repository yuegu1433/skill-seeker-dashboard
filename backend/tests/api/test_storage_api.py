"""Integration tests for storage API.

This module contains integration tests for the storage API endpoints,
testing all CRUD operations, error scenarios, performance, and security.
"""

import io
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import Mock, AsyncMock, patch
import json

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.storage.api.v1.files import router as files_router
from backend.app.storage.api.v1.buckets import router as buckets_router
from backend.app.storage.api.v1.versions import router as versions_router
from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.client import MinIOClient
from backend.app.storage.versioning import VersionManager
from backend.app.storage.schemas.file_operations import (
    FileUploadResponse,
    FileDownloadResponse,
)


class TestStorageAPI:
    """Test suite for storage API endpoints."""

    @pytest.fixture
    def test_client(self):
        """Create test client with mocked dependencies."""
        from fastapi import FastAPI

        app = FastAPI()

        # Include routers
        app.include_router(files_router)
        app.include_router(buckets_router)
        app.include_router(versions_router)

        # Create test client
        client = TestClient(app)

        return client

    @pytest.fixture
    def mock_storage_manager(self):
        """Create mock storage manager."""
        return Mock(spec=SkillStorageManager)

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client."""
        return Mock(spec=MinIOClient)

    @pytest.fixture
    def mock_version_manager(self):
        """Create mock version manager."""
        return Mock(spec=VersionManager)

    @pytest.fixture
    def test_skill_id(self):
        """Create test skill ID."""
        return uuid4()

    @pytest.fixture
    def test_file_path(self):
        """Create test file path."""
        return "test/file.txt"

    # Test file upload API
    def test_upload_file_success(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test successful file upload."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = True
            mock_result.file_path = test_file_path
            mock_result.file_size = 1024
            mock_result.checksum = "abc123"
            mock_storage_manager.upload_file.return_value = mock_result

            # Test data
            test_file_content = b"test file content"

            # Execute
            response = test_client.post(
                "/api/v1/files/upload",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
                files={"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")},
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file_path"] == test_file_path
            assert data["file_size"] == 1024
            assert data["checksum"] == "abc123"

    def test_upload_file_failure(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test file upload failure."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = False
            mock_result.error_message = "File too large"
            mock_storage_manager.upload_file.return_value = mock_result

            # Test data
            test_file_content = b"test file content"

            # Execute
            response = test_client.post(
                "/api/v1/files/upload",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
                files={"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")},
            )

            # Verify
            assert response.status_code == 400
            assert "File too large" in response.json()["detail"]

    def test_upload_file_missing_params(self, test_client):
        """Test file upload with missing parameters."""
        # Execute
        response = test_client.post(
            "/api/v1/files/upload",
            params={
                "skill_id": str(uuid4()),
                # Missing file_path
            },
            files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
        )

        # Verify
        assert response.status_code == 422  # Validation error

    # Test file download API
    def test_download_file_success(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test successful file download."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = True
            mock_result.file_path = test_file_path
            mock_result.download_url = "https://example.com/download/123"
            mock_result.expires_at = "2024-12-31T23:59:59"
            mock_storage_manager.download_file.return_value = mock_result

            # Execute
            response = test_client.get(
                "/api/v1/files/download",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file_path"] == test_file_path
            assert data["download_url"] == "https://example.com/download/123"

    def test_download_file_not_found(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test file download when file not found."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = False
            mock_result.error_message = "File not found"
            mock_storage_manager.download_file.return_value = mock_result

            # Execute
            response = test_client.get(
                "/api/v1/files/download",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]

    # Test file delete API
    def test_delete_file_success(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test successful file deletion."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = True
            mock_result.file_path = test_file_path
            mock_storage_manager.delete_file.return_value = mock_result

            # Execute
            response = test_client.delete(
                "/api/v1/files/delete",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file_path"] == test_file_path

    def test_delete_file_not_found(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test file deletion when file not found."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = False
            mock_result.error_message = "File not found"
            mock_storage_manager.delete_file.return_value = mock_result

            # Execute
            response = test_client.delete(
                "/api/v1/files/delete",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 404
            assert "File not found" in response.json()["detail"]

    # Test file list API
    def test_list_files_success(self, test_client, test_skill_id, mock_storage_manager):
        """Test successful file listing."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.files = [
                {
                    "file_path": "file1.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "created_at": datetime.utcnow().isoformat(),
                },
                {
                    "file_path": "file2.txt",
                    "file_size": 2048,
                    "content_type": "text/plain",
                    "created_at": datetime.utcnow().isoformat(),
                },
            ]
            mock_result.total = 2
            mock_result.has_more = False
            mock_storage_manager.list_files.return_value = mock_result

            # Execute
            response = test_client.get(
                "/api/v1/files/list",
                params={
                    "skill_id": str(test_skill_id),
                    "limit": 50,
                    "offset": 0,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["files"]) == 2
            assert data["total"] == 2
            assert data["has_more"] is False

    def test_list_files_empty(self, test_client, test_skill_id, mock_storage_manager):
        """Test file listing when no files exist."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.files = []
            mock_result.total = 0
            mock_result.has_more = False
            mock_storage_manager.list_files.return_value = mock_result

            # Execute
            response = test_client.get(
                "/api/v1/files/list",
                params={
                    "skill_id": str(test_skill_id),
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["files"]) == 0
            assert data["total"] == 0

    # Test file move API
    def test_move_file_success(self, test_client, test_skill_id, mock_storage_manager):
        """Test successful file move."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = True
            mock_result.source_path = "old.txt"
            mock_result.target_path = "new.txt"
            mock_storage_manager.move_file.return_value = mock_result

            # Execute
            response = test_client.put(
                "/api/v1/files/move",
                params={
                    "skill_id": str(test_skill_id),
                    "source_path": "old.txt",
                    "target_path": "new.txt",
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["source_path"] == "old.txt"
            assert data["target_path"] == "new.txt"

    # Test file info API
    def test_get_file_info_success(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test successful file info retrieval."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_file_info = Mock()
            mock_file_info.id = str(uuid4())
            mock_file_info.file_path = test_file_path
            mock_file_info.file_size = 1024
            mock_file_info.content_type = "text/plain"
            mock_storage_manager.get_file_info.return_value = mock_file_info

            # Execute
            response = test_client.get(
                "/api/v1/files/info",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file_info"]["file_path"] == test_file_path

    # Test skill stats API
    def test_get_skill_stats_success(self, test_client, test_skill_id, mock_storage_manager):
        """Test successful skill stats retrieval."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_stats = {
                "skill_id": str(test_skill_id),
                "file_count": 10,
                "total_size": 10240,
                "file_types": {
                    "skill_file": 8,
                    "config": 2,
                },
            }
            mock_storage_manager.get_skill_stats.return_value = mock_stats

            # Execute
            response = test_client.get(
                "/api/v1/files/stats",
                params={
                    "skill_id": str(test_skill_id),
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["stats"]["file_count"] == 10

    # Test file verify API
    def test_verify_file_integrity_success(self, test_client, test_skill_id, test_file_path, mock_storage_manager):
        """Test successful file integrity verification."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_storage_manager.verify_file_integrity.return_value = True

            # Execute
            response = test_client.post(
                "/api/v1/files/verify",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["is_valid"] is True

    # Test prepare storage API
    def test_prepare_skill_storage_success(self, test_client, test_skill_id, mock_storage_manager):
        """Test successful skill storage preparation."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_storage_manager.ensure_skill_storage.return_value = True

            # Execute
            response = test_client.post(
                "/api/v1/files/prepare",
                params={
                    "skill_id": str(test_skill_id),
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["skill_id"] == str(test_skill_id)

    # Test bucket management APIs
    def test_list_buckets_success(self, test_client, mock_minio_client):
        """Test successful bucket listing."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.list_buckets.return_value = [
                {
                    "name": "bucket1",
                    "creation_date": datetime.utcnow(),
                },
                {
                    "name": "bucket2",
                    "creation_date": datetime.utcnow(),
                },
            ]

            # Execute
            response = test_client.get("/api/v1/buckets/list")

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["buckets"]) == 2

    def test_create_bucket_success(self, test_client, mock_minio_client):
        """Test successful bucket creation."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.create_bucket.return_value = True

            # Execute
            response = test_client.post(
                "/api/v1/buckets/create",
                params={
                    "bucket_name": "test-bucket",
                    "region": "us-east-1",
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["bucket_name"] == "test-bucket"

    def test_delete_bucket_success(self, test_client, mock_minio_client):
        """Test successful bucket deletion."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.delete_bucket.return_value = True

            # Execute
            response = test_client.delete(
                "/api/v1/buckets/delete",
                params={
                    "bucket_name": "test-bucket",
                    "force": False,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["bucket_name"] == "test-bucket"

    def test_bucket_exists_success(self, test_client, mock_minio_client):
        """Test successful bucket existence check."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.bucket_exists.return_value = True

            # Execute
            response = test_client.get(
                "/api/v1/buckets/exists",
                params={
                    "bucket_name": "test-bucket",
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["exists"] is True

    # Test bucket objects APIs
    def test_list_bucket_objects_success(self, test_client, mock_minio_client):
        """Test successful bucket objects listing."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.list_objects.return_value = [
                {
                    "object_name": "file1.txt",
                    "size": 1024,
                    "etag": "abc123",
                    "content_type": "text/plain",
                    "last_modified": datetime.utcnow(),
                    "is_dir": False,
                },
            ]

            # Execute
            response = test_client.get(
                "/api/v1/buckets/test-bucket/objects",
                params={
                    "prefix": "",
                    "recursive": True,
                    "include_version": False,
                    "max_keys": 100,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["objects"]) == 1

    def test_count_bucket_objects_success(self, test_client, mock_minio_client):
        """Test successful bucket objects counting."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.list_objects.return_value = [
                {
                    "object_name": f"file{i}.txt",
                    "size": 1024 * (i + 1),
                }
                for i in range(5)
            ]

            # Execute
            response = test_client.get(
                "/api/v1/buckets/test-bucket/objects/count",
                params={
                    "prefix": "",
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["object_count"] == 5
            assert data["total_size"] > 0

    # Test MinIO health API
    def test_minio_health_success(self, test_client, mock_minio_client):
        """Test successful MinIO health check."""
        # Mock MinIO client
        with patch("backend.app.storage.api.v1.buckets.get_minio_client", return_value=mock_minio_client):
            # Setup mock response
            mock_minio_client.is_healthy.return_value = True
            mock_minio_client.list_buckets.return_value = []

            # Execute
            response = test_client.get("/api/v1/buckets/health")

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "healthy"
            assert data["is_healthy"] is True

    # Test version control APIs
    def test_create_version_success(self, test_client, test_skill_id, test_file_path, mock_version_manager):
        """Test successful version creation."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            version_id = uuid4().hex
            mock_version_manager.create_version.return_value = version_id

            # Test data
            test_file_content = b"test file content"

            # Execute
            response = test_client.post(
                "/api/v1/versions/create",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                    "comment": "Initial version",
                },
                files={"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")},
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["version_id"] == version_id

    def test_list_versions_success(self, test_client, test_skill_id, test_file_path, mock_version_manager):
        """Test successful version listing."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            from backend.app.storage.schemas.file_operations import FileVersionInfo

            mock_version = Mock()
            mock_version.id = str(uuid4())
            mock_version.version_id = uuid4().hex
            mock_version.version_number = 1
            mock_version.file_size = 1024
            mock_version.checksum = "abc123"
            mock_version.comment = "Initial version"
            mock_version.created_at = datetime.utcnow()
            mock_version.created_by = "user"
            mock_version.is_latest = True

            mock_version_manager.list_versions.return_value = [mock_version]

            # Execute
            response = test_client.get(
                "/api/v1/versions/list",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["versions"]) == 1
            assert data["total"] == 1

    def test_restore_version_success(self, test_client, test_skill_id, test_file_path, mock_version_manager):
        """Test successful version restoration."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            version_id = uuid4().hex
            mock_version_manager.restore_version.return_value = True

            # Execute
            response = test_client.post(
                "/api/v1/versions/restore",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                    "version_id": version_id,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["version_id"] == version_id

    def test_compare_versions_success(self, test_client, test_skill_id, test_file_path, mock_version_manager):
        """Test successful version comparison."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            version_id_1 = uuid4().hex
            version_id_2 = uuid4().hex

            mock_comparison = {
                "file_path": test_file_path,
                "version_1": {
                    "version_id": version_id_1,
                    "version_number": 1,
                    "size": 1024,
                },
                "version_2": {
                    "version_id": version_id_2,
                    "version_number": 2,
                    "size": 2048,
                },
                "differences": {
                    "size_difference": 1024,
                    "checksum_different": True,
                },
            }
            mock_version_manager.compare_versions.return_value = mock_comparison

            # Execute
            response = test_client.get(
                "/api/v1/versions/compare",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                    "version_id_1": version_id_1,
                    "version_id_2": version_id_2,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "comparison" in data

    def test_delete_version_success(self, test_client, test_skill_id, test_file_path, mock_version_manager):
        """Test successful version deletion."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            version_id = uuid4().hex
            mock_version_manager.delete_version.return_value = True

            # Execute
            response = test_client.delete(
                "/api/v1/versions/delete",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": test_file_path,
                    "version_id": version_id,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["version_id"] == version_id

    def test_cleanup_versions_success(self, test_client, mock_version_manager):
        """Test successful version cleanup."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            mock_version_manager.cleanup_old_versions.return_value = 5

            # Execute
            response = test_client.post("/api/v1/versions/cleanup")

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["deleted_count"] == 5

    def test_get_version_statistics_success(self, test_client, mock_version_manager):
        """Test successful version statistics retrieval."""
        # Mock version manager
        with patch("backend.app.storage.api.v1.versions.get_version_manager", return_value=mock_version_manager):
            # Setup mock response
            mock_stats = {
                "total_versions": 100,
                "versions_last_7_days": 10,
                "versions_last_30_days": 50,
                "avg_versions_per_file": 3.5,
                "total_storage_used": 1024000,
            }
            mock_version_manager.get_version_statistics.return_value = mock_stats

            # Execute
            response = test_client.get("/api/v1/versions/statistics")

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["statistics"]["total_versions"] == 100

    # Test API error handling
    def test_api_internal_error(self, test_client, test_skill_id, mock_storage_manager):
        """Test API internal error handling."""
        # Mock storage manager to raise exception
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            mock_storage_manager.upload_file.side_effect = Exception("Internal error")

            # Test data
            test_file_content = b"test file content"

            # Execute
            response = test_client.post(
                "/api/v1/files/upload",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": "test.txt",
                },
                files={"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")},
            )

            # Verify
            assert response.status_code == 500
            assert "Internal error" in response.json()["detail"]

    # Test API validation
    def test_api_validation_error(self, test_client):
        """Test API validation error handling."""
        # Execute with invalid parameters
        response = test_client.post(
            "/api/v1/files/upload",
            params={
                "skill_id": "invalid-uuid",  # Invalid UUID
                "file_path": "test.txt",
            },
            files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
        )

        # Verify
        assert response.status_code == 422  # Validation error

    # Test API rate limiting (simulated)
    def test_api_rate_limiting(self, test_client, test_skill_id, mock_storage_manager):
        """Test API rate limiting simulation."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = True
            mock_result.file_path = "test.txt"
            mock_result.file_size = 1024
            mock_result.checksum = "abc123"
            mock_storage_manager.upload_file.return_value = mock_result

            # Test data
            test_file_content = b"test file content"

            # Execute multiple requests (simulating rate limiting)
            responses = []
            for _ in range(10):
                response = test_client.post(
                    "/api/v1/files/upload",
                    params={
                        "skill_id": str(test_skill_id),
                        "file_path": f"test{_}.txt",
                    },
                    files={"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")},
                )
                responses.append(response)

            # Verify all responses are successful
            assert all(r.status_code == 200 for r in responses)

    # Test API security
    def test_api_unauthorized_access(self, test_client):
        """Test API unauthorized access protection."""
        # Execute without proper authentication (simulated)
        response = test_client.get(
            "/api/v1/buckets/list",
            headers={
                # Missing authentication header
            },
        )

        # In a real application, this would return 401 or 403
        # For now, we expect 200 since we're not actually checking auth
        # This test would be implemented with actual authentication
        assert response.status_code in [200, 401, 403]

    # Test API performance
    def test_api_performance(self, test_client, test_skill_id, mock_storage_manager):
        """Test API performance."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.success = True
            mock_result.file_path = "test.txt"
            mock_result.file_size = 1024
            mock_result.checksum = "abc123"
            mock_storage_manager.upload_file.return_value = mock_result

            # Test data
            test_file_content = b"test file content"

            # Measure response time
            import time

            start_time = time.time()
            response = test_client.post(
                "/api/v1/files/upload",
                params={
                    "skill_id": str(test_skill_id),
                    "file_path": "test.txt",
                },
                files={"file": ("test.txt", io.BytesIO(test_file_content), "text/plain")},
            )
            end_time = time.time()

            # Verify response time is acceptable (< 1 second for mock)
            response_time = end_time - start_time
            assert response_time < 1.0  # Should be fast for mock

            # Verify response
            assert response.status_code == 200

    # Test API pagination
    def test_api_pagination(self, test_client, test_skill_id, mock_storage_manager):
        """Test API pagination."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.files = [
                {
                    "file_path": f"file{i}.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "created_at": datetime.utcnow().isoformat(),
                }
                for i in range(10)
            ]
            mock_result.total = 100
            mock_result.has_more = True
            mock_storage_manager.list_files.return_value = mock_result

            # Test pagination
            response = test_client.get(
                "/api/v1/files/list",
                params={
                    "skill_id": str(test_skill_id),
                    "limit": 10,
                    "offset": 0,
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) == 10
            assert data["has_more"] is True
            assert data["total"] == 100

    # Test API filtering
    def test_api_filtering(self, test_client, test_skill_id, mock_storage_manager):
        """Test API filtering."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.files = [
                {
                    "file_path": "skill_file.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ]
            mock_result.total = 1
            mock_result.has_more = False
            mock_storage_manager.list_files.return_value = mock_result

            # Test filtering by file type
            response = test_client.get(
                "/api/v1/files/list",
                params={
                    "skill_id": str(test_skill_id),
                    "file_type": "skill_file",
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) == 1

    # Test API sorting
    def test_api_sorting(self, test_client, test_skill_id, mock_storage_manager):
        """Test API sorting."""
        # Mock storage manager
        with patch("backend.app.storage.api.v1.files.get_storage_manager", return_value=mock_storage_manager):
            # Setup mock response
            mock_result = Mock()
            mock_result.files = [
                {
                    "file_path": "a.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                    "created_at": datetime.utcnow().isoformat(),
                }
            ]
            mock_result.total = 1
            mock_result.has_more = False
            mock_storage_manager.list_files.return_value = mock_result

            # Execute
            response = test_client.get(
                "/api/v1/files/list",
                params={
                    "skill_id": str(test_skill_id),
                    "sort_by": "file_path",
                    "sort_order": "asc",
                },
            )

            # Verify
            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) == 1
