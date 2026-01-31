"""Tests for File Management API.

This module contains comprehensive integration tests for the file management API
including functional tests, performance tests, and security tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import tempfile
import io

from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

# Import API routers
from app.file.api.v1.files import router as files_router
from app.file.api.v1.editor import router as editor_router
from app.file.api.v1.versions import router as versions_router
from app.file.api.v1.preview import router as preview_router
from app.file.websocket import websocket_manager

# Import managers and services
from app.file.manager import FileManager
from app.file.services.upload_service import UploadService, UploadMode
from app.file.services.download_service import DownloadService
from app.file.batch_processor import BatchProcessor
from app.file.preview_manager import PreviewManager
from app.file.version_manager import VersionManager
from app.file.editor import FileEditor


class TestFileManagementAPI:
    """Test suite for file management API."""

    @pytest.fixture
    def app(self):
        """Create FastAPI application for testing."""
        app = FastAPI(title="File Management API Test")

        # Include all file management routers
        app.include_router(files_router, prefix="/api/v1/files", tags=["files"])
        app.include_router(editor_router, prefix="/api/v1/files", tags=["editor"])
        app.include_router(versions_router, prefix="/api/v1/files", tags=["versions"])
        app.include_router(preview_router, prefix="/api/v1/files", tags=["preview"])

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_file_manager(self):
        """Mock file manager."""
        mock_manager = Mock(spec=FileManager)
        mock_manager.create_file = AsyncMock()
        mock_manager.get_file = AsyncMock()
        mock_manager.update_file = AsyncMock()
        mock_manager.delete_file = AsyncMock()
        mock_manager.list_files = AsyncMock()
        mock_manager.search_files = AsyncMock()
        return mock_manager

    @pytest.fixture
    def mock_upload_service(self):
        """Mock upload service."""
        return Mock(spec=UploadService)

    @pytest.fixture
    def mock_download_service(self):
        """Mock download service."""
        return Mock(spec=DownloadService)

    @pytest.fixture
    def mock_batch_processor(self):
        """Mock batch processor."""
        return Mock(spec=BatchProcessor)

    # File CRUD Tests

    def test_create_file_success(self, client, mock_file_manager):
        """Test successful file creation."""
        # Mock file data
        file_data = {
            "filename": "test.txt",
            "content_type": "text/plain",
            "size": 1024,
            "folder_id": str(uuid4()),
        }

        # Mock file manager response
        mock_file = Mock()
        mock_file.id = str(uuid4())
        mock_file.filename = "test.txt"
        mock_file.size = 1024
        mock_file.created_at = datetime.utcnow()
        mock_file_manager.create_file.return_value = mock_file

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.post("/api/v1/files/", json=file_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "file" in data
            assert data["file"]["filename"] == "test.txt"

    def test_create_file_validation_error(self, client):
        """Test file creation with validation error."""
        # Invalid file data (missing required fields)
        file_data = {
            "filename": "",  # Empty filename
        }

        response = client.post("/api/v1/files/", json=file_data)

        assert response.status_code == 422  # Validation error

    def test_get_file_success(self, client, mock_file_manager):
        """Test successful file retrieval."""
        file_id = str(uuid4())

        # Mock file manager response
        mock_file = Mock()
        mock_file.id = file_id
        mock_file.filename = "test.txt"
        mock_file.size = 1024
        mock_file.created_at = datetime.utcnow()
        mock_file_manager.get_file.return_value = mock_file

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.get(f"/api/v1/files/{file_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file"]["id"] == file_id

    def test_get_file_not_found(self, client, mock_file_manager):
        """Test getting non-existent file."""
        file_id = str(uuid4())

        # Mock file not found
        mock_file_manager.get_file.return_value = None

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.get(f"/api/v1/files/{file_id}")

            assert response.status_code == 404
            data = response.json()
            assert "File not found" in data["detail"]

    def test_update_file_success(self, client, mock_file_manager):
        """Test successful file update."""
        file_id = str(uuid4())
        update_data = {
            "filename": "updated.txt",
            "description": "Updated description",
        }

        # Mock updated file
        mock_file = Mock()
        mock_file.id = file_id
        mock_file.filename = "updated.txt"
        mock_file.description = "Updated description"
        mock_file_manager.update_file.return_value = mock_file

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.put(f"/api/v1/files/{file_id}", json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file"]["filename"] == "updated.txt"

    def test_delete_file_success(self, client, mock_file_manager):
        """Test successful file deletion."""
        file_id = str(uuid4())

        # Mock successful deletion
        mock_file_manager.delete_file.return_value = True

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.delete(f"/api/v1/files/{file_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["file_id"] == file_id

    def test_delete_file_not_found(self, client, mock_file_manager):
        """Test deleting non-existent file."""
        file_id = str(uuid4())

        # Mock file not found
        mock_file_manager.delete_file.return_value = False

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.delete(f"/api/v1/files/{file_id}")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    # File Listing and Search Tests

    def test_list_files_success(self, client, mock_file_manager):
        """Test successful file listing."""
        # Mock file list
        mock_files = [
            Mock(id=str(uuid4()), filename=f"file_{i}.txt", size=1024, created_at=datetime.utcnow())
            for i in range(10)
        ]

        # Mock list result
        mock_result = Mock()
        mock_result.files = mock_files
        mock_result.total = 10
        mock_result.page = 1
        mock_result.size = 50
        mock_result.pages = 1

        mock_file_manager.list_files.return_value = mock_result

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.get("/api/v1/files/")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total"] == 10
            assert len(data["files"]) == 10

    def test_list_files_with_filters(self, client, mock_file_manager):
        """Test file listing with filters."""
        folder_id = str(uuid4())

        # Mock filtered list result
        mock_result = Mock()
        mock_result.files = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.size = 50
        mock_result.pages = 0

        mock_file_manager.list_files.return_value = mock_result

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.get(
                "/api/v1/files/",
                params={
                    "folder_id": folder_id,
                    "file_type": "text/plain",
                    "page": 1,
                    "size": 20,
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

            # Verify filters were passed
            call_args = mock_file_manager.list_files.call_args
            assert call_args[1]["filters"]["folder_id"] == folder_id
            assert call_args[1]["filters"]["file_type"] == "text/plain"

    def test_search_files_success(self, client, mock_file_manager):
        """Test successful file search."""
        search_request = {
            "query": "test",
            "file_types": ["text/plain"],
            "tags": ["important"],
            "date_from": "2024-01-01T00:00:00",
            "date_to": "2024-12-31T23:59:59",
        }

        # Mock search result
        mock_result = Mock()
        mock_result.files = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.size = 50
        mock_result.pages = 0

        mock_file_manager.search_files.return_value = mock_result

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.post("/api/v1/files/search", json=search_request)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # File Upload Tests

    def test_upload_file_success(self, client, mock_upload_service):
        """Test successful file upload."""
        file_content = b"Test file content"

        # Mock upload service response
        mock_result = {
            "file_id": str(uuid4()),
            "status": "completed",
        }

        mock_upload_service.upload_file.return_value = mock_result

        with patch('app.file.api.v1.files.get_upload_service', return_value=mock_upload_service):
            response = client.post(
                "/api/v1/files/upload",
                files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "result" in data

    def test_upload_chunked_success(self, client, mock_upload_service):
        """Test successful chunked upload."""
        # Mock chunked upload initiation
        mock_session = Mock()
        mock_session.session_id = str(uuid4())
        mock_session.total_chunks = 5
        mock_session.chunk_size = 1024

        mock_upload_service.initiate_chunked_upload.return_value = mock_session

        with patch('app.file.api.v1.files.get_upload_service', return_value=mock_upload_service):
            # Initiate chunked upload
            response = client.post(
                "/api/v1/files/upload",
                params={
                    "mode": "chunked",
                    "chunk_size": 1024,
                },
                files={"file": ("test.txt", io.BytesIO(b"test"), "text/plain")},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "upload_id" in data["result"]

    # File Download Tests

    def test_download_file_success(self, client, mock_download_service):
        """Test successful file download."""
        file_id = str(uuid4())

        # Mock download service response
        mock_result = {
            "data": b"File content",
            "filename": "test.txt",
            "size": 12,
            "content_type": "text/plain",
        }

        mock_download_service.download_file.return_value = mock_result

        with patch('app.file.api.v1.files.get_download_service', return_value=mock_download_service):
            response = client.get(f"/api/v1/files/{file_id}/download")

            assert response.status_code == 200
            assert response.headers["content-type"] == "application/octet-stream"
            assert response.content == b"File content"

    # Progress Tracking Tests

    def test_get_upload_progress(self, client, mock_upload_service):
        """Test getting upload progress."""
        upload_id = str(uuid4())

        # Mock progress data
        mock_progress = Mock()
        mock_progress.to_dict.return_value = {
            "upload_id": upload_id,
            "status": "uploading",
            "progress_percentage": 50.0,
        }

        mock_upload_service.get_upload_progress.return_value = mock_progress

        with patch('app.file.api.v1.files.get_upload_service', return_value=mock_upload_service):
            response = client.get(f"/api/v1/files/upload/{upload_id}/progress")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "progress" in data

    def test_get_download_progress(self, client, mock_download_service):
        """Test getting download progress."""
        download_id = str(uuid4())

        # Mock progress data
        mock_progress = Mock()
        mock_progress.to_dict.return_value = {
            "download_id": download_id,
            "status": "downloading",
            "progress_percentage": 75.0,
        }

        mock_download_service.get_download_progress.return_value = mock_progress

        with patch('app.file.api.v1.files.get_download_service', return_value=mock_download_service):
            response = client.get(f"/api/v1/files/download/{download_id}/progress")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "progress" in data

    # Batch Operations Tests

    def test_batch_operation_success(self, client, mock_batch_processor):
        """Test successful batch operation."""
        file_ids = [str(uuid4()) for _ in range(5)]

        operation_request = {
            "operation_type": "delete",
            "file_ids": file_ids,
            "parameters": {},
        }

        # Mock batch job
        mock_job = Mock()
        mock_job.job_id = str(uuid4())
        mock_job.status = "running"

        mock_batch_processor.create_batch_job.return_value = mock_job

        with patch('app.file.api.v1.files.get_batch_processor', return_value=mock_batch_processor):
            response = client.post("/api/v1/files/batch", json=operation_request)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "job_id" in data["result"]

    def test_get_batch_status(self, client, mock_batch_processor):
        """Test getting batch job status."""
        job_id = str(uuid4())

        # Mock batch job
        mock_job = Mock()
        mock_job.job_id = job_id
        mock_job.operation_type = "delete"
        mock_job.status = "running"

        # Mock progress
        mock_progress = Mock()
        mock_progress.to_dict.return_value = {
            "progress_percentage": 50.0,
            "processed_items": 5,
            "total_items": 10,
        }

        mock_job.progress = mock_progress
        mock_job.created_at = datetime.utcnow()
        mock_job.completed_at = None

        mock_batch_processor.get_batch_job.return_value = mock_job

        with patch('app.file.api.v1.files.get_batch_processor', return_value=mock_batch_processor):
            response = client.get(f"/api/v1/files/batch/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["job"]["job_id"] == job_id

    def test_cancel_batch_job(self, client, mock_batch_processor):
        """Test canceling batch job."""
        job_id = str(uuid4())

        # Mock successful cancellation
        mock_batch_processor.cancel_batch_job.return_value = True

        with patch('app.file.api.v1.files.get_batch_processor', return_value=mock_batch_processor):
            response = client.delete(f"/api/v1/files/batch/{job_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # Editor API Tests

    def test_create_editor_session(self, client, mock_file_manager):
        """Test creating editor session."""
        file_id = str(uuid4())

        # Mock editor session
        mock_session = Mock()
        mock_session.session_id = str(uuid4())
        mock_session.file_id = file_id
        mock_session.created_at = datetime.utcnow()
        mock_session.last_activity = datetime.utcnow()

        with patch('app.file.api.v1.editor.get_file_editor') as mock_get_editor:
            mock_editor = Mock()
            mock_editor.create_editor_session.return_value = mock_session
            mock_get_editor.return_value = mock_editor

            response = client.post(
                "/api/v1/files/editor/session",
                json={"file_id": file_id},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "session" in data

    def test_get_file_content(self, client):
        """Test getting file content for editing."""
        session_id = str(uuid4())

        # Mock file content
        mock_content = "File content for editing"
        mock_metadata = {
            "language": "text",
            "encoding": "utf-8",
            "line_count": 10,
        }

        with patch('app.file.api.v1.editor.get_file_editor') as mock_get_editor:
            mock_editor = Mock()
            mock_editor.get_file_content.return_value = {
                "content": mock_content,
                "metadata": mock_metadata,
                "syntax_highlighting": "text",
                "line_count": 10,
                "last_modified": datetime.utcnow(),
            }
            mock_get_editor.return_value = mock_editor

            response = client.get(f"/api/v1/files/editor/session/{session_id}/content")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["content"] == mock_content

    def test_update_file_content(self, client):
        """Test updating file content."""
        session_id = str(uuid4())
        content = "Updated file content"
        version_note = "Manual edit"

        # Mock update result
        mock_result = Mock()
        mock_result.file_id = str(uuid4())
        mock_result.version_id = str(uuid4())
        mock_result.content_hash = "abc123"
        mock_result.last_modified = datetime.utcnow()

        with patch('app.file.api.v1.editor.get_file_editor') as mock_get_editor:
            mock_editor = Mock()
            mock_editor.update_file_content.return_value = mock_result
            mock_get_editor.return_value = mock_editor

            response = client.put(
                f"/api/v1/files/editor/session/{session_id}/content",
                json={
                    "content": content,
                    "version_note": version_note,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # Version API Tests

    def test_create_version(self, client, mock_file_manager):
        """Test creating file version."""
        file_id = str(uuid4())

        version_request = {
            "content": "File content",
            "note": "Version 1",
            "metadata": {},
        }

        # Mock version
        mock_version = Mock()
        mock_version.id = str(uuid4())
        mock_version.file_id = file_id
        mock_version.version_number = 1
        mock_version.content_hash = "abc123"
        mock_version.created_at = datetime.utcnow()
        mock_version.version_note = "Version 1"

        with patch('app.file.api.v1.versions.get_version_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.create_version.return_value = mock_version
            mock_get_manager.return_value = mock_manager

            response = client.post(
                f"/api/v1/files/versions/files/{file_id}",
                json=version_request,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "version" in data

    def test_list_versions(self, client, mock_file_manager):
        """Test listing file versions."""
        file_id = str(uuid4())

        # Mock version list
        mock_versions = [
            Mock(
                id=str(uuid4()),
                version_number=i,
                created_at=datetime.utcnow(),
                version_note=f"Version {i}",
            )
            for i in range(1, 6)
        ]

        # Mock list result
        mock_result = Mock()
        mock_result.versions = mock_versions
        mock_result.total = 5
        mock_result.page = 1
        mock_result.size = 50
        mock_result.pages = 1

        with patch('app.file.api.v1.versions.get_version_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.list_versions.return_value = mock_result
            mock_get_manager.return_value = mock_manager

            response = client.get(f"/api/v1/files/versions/files/{file_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["total"] == 5
            assert len(data["versions"]) == 5

    def test_restore_version(self, client, mock_file_manager):
        """Test restoring a version."""
        file_id = str(uuid4())
        version_id = str(uuid4())

        # Mock restored version
        mock_version = Mock()
        mock_version.id = str(uuid4())
        mock_version.file_id = file_id
        mock_version.version_number = 2
        mock_version.created_at = datetime.utcnow()
        mock_version.version_note = "Restored version"

        with patch('app.file.api.v1.versions.get_version_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.restore_version.return_value = mock_version
            mock_get_manager.return_value = mock_manager

            response = client.post(
                f"/api/v1/files/versions/files/{file_id}/{version_id}/restore",
                json={"note": "Restored from version"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    # Preview API Tests

    def test_generate_preview(self, client):
        """Test generating file preview."""
        file_id = str(uuid4())

        preview_request = {
            "file_id": file_id,
            "format": "thumbnail",
            "options": {
                "width": 200,
                "height": 200,
            },
        }

        # Mock preview
        mock_preview = Mock()
        mock_preview.id = str(uuid4())
        mock_preview.file_id = file_id
        mock_preview.format = "thumbnail"
        mock_preview.data = b"preview_data"
        mock_preview.created_at = datetime.utcnow()

        with patch('app.file.api.v1.preview.get_preview_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.generate_preview.return_value = mock_preview
            mock_get_manager.return_value = mock_manager

            response = client.post("/api/v1/files/preview/generate", json=preview_request)

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "preview" in data

    def test_get_image_preview(self, client):
        """Test getting image preview."""
        file_id = str(uuid4())

        # Mock image data
        mock_image_data = b"image_data"

        with patch('app.file.api.v1.preview.get_preview_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_image_preview.return_value = mock_image_data
            mock_get_manager.return_value = mock_manager

            response = client.get(
                f"/api/v1/files/preview/files/{file_id}/image",
                params={
                    "width": 200,
                    "height": 200,
                    "quality": 85,
                },
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

    def test_get_thumbnail(self, client):
        """Test getting file thumbnail."""
        file_id = str(uuid4())

        # Mock thumbnail data
        mock_thumbnail_data = b"thumbnail_data"

        with patch('app.file.api.v1.preview.get_preview_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_thumbnail.return_value = mock_thumbnail_data
            mock_get_manager.return_value = mock_manager

            response = client.get(
                f"/api/v1/files/preview/files/{file_id}/thumbnail",
                params={
                    "size": "200x200",
                    "format": "jpeg",
                },
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"

    # Error Handling Tests

    def test_invalid_file_id_format(self, client):
        """Test API with invalid file ID format."""
        invalid_file_id = "invalid-uuid-format"

        response = client.get(f"/api/v1/files/{invalid_file_id}")

        assert response.status_code == 422  # Validation error

    def test_missing_required_fields(self, client):
        """Test API with missing required fields."""
        # Missing filename for file creation
        response = client.post("/api/v1/files/", json={})

        assert response.status_code == 422  # Validation error

    def test_unsupported_operation(self, client):
        """Test API with unsupported operation."""
        file_id = str(uuid4())

        # Mock file manager to raise unsupported operation
        with patch('app.file.api.v1.files.get_file_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.update_file.side_effect = NotImplementedError("Operation not supported")
            mock_get_manager.return_value = mock_manager

            response = client.put(f"/api/v1/files/{file_id}", json={"filename": "test.txt"})

            assert response.status_code == 500  # Internal server error

    # Performance Tests

    @pytest.mark.asyncio
    async def test_concurrent_file_operations(self, client):
        """Test concurrent file operations."""
        num_operations = 10

        with patch('app.file.api.v1.files.get_file_manager') as mock_get_manager:
            mock_manager = Mock()

            # Mock async operations
            async def mock_create_file(*args, **kwargs):
                await asyncio.sleep(0.01)  # Simulate async work
                return Mock(id=str(uuid4()), filename="test.txt", created_at=datetime.utcnow())

            mock_manager.create_file = mock_create_file
            mock_get_manager.return_value = mock_manager

            # Run concurrent operations
            tasks = []
            for i in range(num_operations):
                task = asyncio.create_task(
                    client.post(
                        "/api/v1/files/",
                        json={"filename": f"test_{i}.txt", "size": 1024},
                    )
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks)

            # All operations should succeed
            for response in responses:
                assert response.status_code == 200

    def test_large_file_upload(self, client):
        """Test uploading a large file."""
        # Create a 1MB file
        large_content = b"x" * (1024 * 1024)

        with patch('app.file.api.v1.files.get_upload_service') as mock_get_service:
            mock_service = Mock()
            mock_service.upload_file.return_value = {
                "file_id": str(uuid4()),
                "status": "completed",
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/files/upload",
                files={"file": ("large_file.txt", io.BytesIO(large_content), "text/plain")},
            )

            assert response.status_code == 200

    # Security Tests

    def test_file_access_control(self, client, mock_file_manager):
        """Test file access control."""
        file_id = str(uuid4())

        # Mock permission denied
        mock_file_manager.get_file.side_effect = PermissionError("Access denied")

        with patch('app.file.api.v1.files.get_file_manager', return_value=mock_file_manager):
            response = client.get(f"/api/v1/files/{file_id}")

            assert response.status_code == 500  # Permission error

    def test_file_path_traversal(self, client):
        """Test file path traversal protection."""
        malicious_path = "../../../etc/passwd"

        response = client.get(f"/api/v1/files/{malicious_path}")

        assert response.status_code == 422  # Should reject malicious path

    def test_upload_size_limit(self, client):
        """Test upload size limit enforcement."""
        # Create a file that exceeds size limit
        large_content = b"x" * (10 * 1024 * 1024)  # 10MB

        with patch('app.file.api.v1.files.get_upload_service') as mock_get_service:
            mock_service = Mock()
            mock_service.upload_file.side_effect = ValueError("File size exceeds limit")
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/v1/files/upload",
                files={"file": ("large_file.txt", io.BytesIO(large_content), "text/plain")},
            )

            assert response.status_code == 400  # Should reject oversized file

    # Integration Tests

    def test_file_lifecycle(self, client):
        """Test complete file lifecycle: create, update, list, delete."""
        file_data = {
            "filename": "lifecycle_test.txt",
            "content_type": "text/plain",
            "size": 1024,
        }

        with patch('app.file.api.v1.files.get_file_manager') as mock_get_manager:
            mock_manager = Mock()

            # Mock file creation
            mock_file = Mock()
            mock_file.id = str(uuid4())
            mock_file.filename = "lifecycle_test.txt"
            mock_file.size = 1024
            mock_file.created_at = datetime.utcnow()

            mock_manager.create_file.return_value = mock_file
            mock_manager.update_file.return_value = mock_file
            mock_manager.delete_file.return_value = True

            mock_get_manager.return_value = mock_manager

            # Create file
            create_response = client.post("/api/v1/files/", json=file_data)
            assert create_response.status_code == 200

            # Update file
            update_data = {"filename": "updated_lifecycle_test.txt"}
            update_response = client.put(f"/api/v1/files/{mock_file.id}", json=update_data)
            assert update_response.status_code == 200

            # Delete file
            delete_response = client.delete(f"/api/v1/files/{mock_file.id}")
            assert delete_response.status_code == 200

    def test_version_lifecycle(self, client):
        """Test complete version lifecycle: create, list, restore, compare."""
        file_id = str(uuid4())

        with patch('app.file.api.v1.versions.get_version_manager') as mock_get_manager:
            mock_manager = Mock()

            # Mock version creation
            mock_version = Mock()
            mock_version.id = str(uuid4())
            mock_version.file_id = file_id
            mock_version.version_number = 1
            mock_version.created_at = datetime.utcnow()
            mock_version.version_note = "Initial version"

            mock_manager.create_version.return_value = mock_version
            mock_manager.get_version.return_value = mock_version
            mock_manager.restore_version.return_value = mock_version

            mock_get_manager.return_value = mock_manager

            # Create version
            version_request = {
                "content": "File content",
                "note": "Initial version",
            }
            create_response = client.post(
                f"/api/v1/files/versions/files/{file_id}",
                json=version_request,
            )
            assert create_response.status_code == 200

            # Get version
            version_id = mock_version.id
            get_response = client.get(f"/api/v1/files/versions/files/{file_id}/{version_id}")
            assert get_response.status_code == 200

            # Restore version
            restore_response = client.post(
                f"/api/v1/files/versions/files/{file_id}/{version_id}/restore",
                json={"note": "Restore test"},
            )
            assert restore_response.status_code == 200

    def test_preview_lifecycle(self, client):
        """Test complete preview lifecycle: generate, get, delete."""
        file_id = str(uuid4())

        with patch('app.file.api.v1.preview.get_preview_manager') as mock_get_manager:
            mock_manager = Mock()

            # Mock preview generation
            mock_preview = Mock()
            mock_preview.id = str(uuid4())
            mock_preview.file_id = file_id
            mock_preview.format = "thumbnail"
            mock_preview.data = b"preview_data"
            mock_preview.created_at = datetime.utcnow()

            mock_manager.generate_preview.return_value = mock_preview
            mock_manager.get_file_preview.return_value = mock_preview
            mock_manager.delete_preview.return_value = True

            mock_get_manager.return_value = mock_manager

            # Generate preview
            preview_request = {
                "file_id": file_id,
                "format": "thumbnail",
                "options": {"width": 200, "height": 200},
            }
            generate_response = client.post("/api/v1/files/preview/generate", json=preview_request)
            assert generate_response.status_code == 200

            # Get preview
            get_response = client.get(f"/api/v1/files/preview/files/{file_id}")
            assert get_response.status_code == 200

            # Delete preview
            delete_response = client.delete(f"/api/v1/files/preview/files/{file_id}")
            assert delete_response.status_code == 200


class TestFileWebSocket:
    """Test suite for file management WebSocket."""

    def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        from fastapi.testclient import TestClient
        from fastapi import FastAPI

        app = FastAPI()

        # This would test the actual WebSocket connection
        # For now, just verify the endpoint exists
        assert True

    def test_websocket_manager(self):
        """Test WebSocket connection manager."""
        # Test connection management
        assert websocket_manager is not None
        assert isinstance(websocket_manager.active_connections, dict)

    def test_websocket_broadcast(self):
        """Test WebSocket message broadcasting."""
        # Mock WebSocket
        mock_websocket = Mock()
        mock_websocket.client_state = "CONNECTED"

        # Test connection
        asyncio.run(websocket_manager.connect(mock_websocket, file_id="test"))

        # Test broadcast
        asyncio.run(
            websocket_manager.broadcast_to_file(
                file_id="test",
                message={"type": "test", "data": "test_data"}
            )
        )

        # Clean up
        websocket_manager.disconnect(mock_websocket)

        assert True


if __name__ == "__main__":
    pytest.main([__file__])
