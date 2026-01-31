"""Tests for File Services.

This module contains comprehensive unit tests for file services including
upload service, download service, streaming transmission, and resumable transfers.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock, mock_open
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, BinaryIO
import io
import tempfile
import hashlib
import time

# Import services and related classes
from app.file.services.upload_service import (
    UploadService,
    UploadStatus,
    UploadMode,
    UploadChunk,
    UploadProgress,
    UploadSession,
)
from app.file.services.download_service import (
    DownloadService,
    DownloadStatus,
    DownloadChunk,
    DownloadProgress,
    DownloadSession,
)


class TestUploadService:
    """Test suite for UploadService."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_manager(self):
        """Mock file manager."""
        mock_manager = Mock()
        mock_manager.create_file = AsyncMock()
        mock_manager.get_file = AsyncMock()
        mock_manager.update_file = AsyncMock()
        return mock_manager

    @pytest.fixture
    def upload_service(self, db_session, file_manager):
        """Create UploadService instance with mocked dependencies."""
        return UploadService(
            db_session=db_session,
            file_manager=file_manager,
            max_chunk_size=1024 * 1024,  # 1MB
            max_concurrent_uploads=3,
            upload_timeout=300,
        )

    @pytest.fixture
    def sample_file_data(self):
        """Create sample file data."""
        return b"This is test file content" * 100  # 2.8KB

    @pytest.fixture
    def sample_file_info(self):
        """Create sample file information."""
        return {
            "filename": "test_file.txt",
            "content_type": "text/plain",
            "size": 2800,
            "hash": "sha256:abc123def456",
        }

    # Test Upload Service Initialization
    def test_upload_service_initialization(self, upload_service):
        """Test upload service initialization."""
        assert upload_service.max_chunk_size == 1024 * 1024
        assert upload_service.max_concurrent_uploads == 3
        assert upload_service.upload_timeout == 300
        assert upload_service.active_uploads == {}
        assert upload_service.upload_sessions == {}

    # Test Normal Upload
    @pytest.mark.asyncio
    async def test_normal_upload_success(self, upload_service, sample_file_data, sample_file_info):
        """Test successful normal upload."""
        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = True

            with patch.object(upload_service, '_process_normal_upload') as mock_process:
                mock_process.return_value = {"file_id": str(uuid4()), "status": "completed"}

                result = await upload_service.upload_file(
                    file_data=sample_file_data,
                    file_info=sample_file_info,
                    mode=UploadMode.NORMAL,
                )

                assert "file_id" in result
                assert result["status"] == "completed"
                mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_normal_upload_validation_failure(self, upload_service, sample_file_data, sample_file_info):
        """Test normal upload with validation failure."""
        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = False

            with pytest.raises(ValueError, match="File validation failed"):
                await upload_service.upload_file(
                    file_data=sample_file_data,
                    file_info=sample_file_info,
                    mode=UploadMode.NORMAL,
                )

    # Test Chunked Upload
    @pytest.mark.asyncio
    async def test_chunked_upload_initiation(self, upload_service, sample_file_data, sample_file_info):
        """Test chunked upload initiation."""
        upload_id = str(uuid4())

        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = True

            session = await upload_service.initiate_chunked_upload(
                file_info=sample_file_info,
                chunk_size=1024,
            )

            assert session.session_id == upload_id
            assert session.mode == UploadMode.CHUNKED
            assert session.status == UploadStatus.PENDING
            assert upload_id in upload_service.upload_sessions

    @pytest.mark.asyncio
    async def test_chunked_upload_success(self, upload_service, sample_file_data):
        """Test successful chunked upload."""
        upload_id = str(uuid4())
        chunk_data = sample_file_data[:1024]
        chunk_index = 0

        # Create upload session
        upload_service.upload_sessions[upload_id] = UploadSession(
            session_id=upload_id,
            filename="test.txt",
            total_size=len(sample_file_data),
            chunk_size=1024,
            total_chunks=3,
            mode=UploadMode.CHUNKED,
            status=UploadStatus.UPLOADING,
            created_at=datetime.utcnow(),
            chunks={},
        )

        with patch.object(upload_service, '_save_chunk') as mock_save:
            mock_save.return_value = True

            result = await upload_service.upload_chunk(
                upload_id=upload_id,
                chunk_index=chunk_index,
                chunk_data=chunk_data,
            )

            assert result["success"] is True
            assert chunk_index in upload_service.upload_sessions[upload_id].chunks

    @pytest.mark.asyncio
    async def test_chunked_upload_invalid_upload_id(self, upload_service, sample_file_data):
        """Test chunked upload with invalid upload ID."""
        upload_id = "invalid_upload_id"

        with pytest.raises(ValueError, match="Upload session not found"):
            await upload_service.upload_chunk(
                upload_id=upload_id,
                chunk_index=0,
                chunk_data=sample_file_data,
            )

    @pytest.mark.asyncio
    async def test_chunked_upload_out_of_range(self, upload_service, sample_file_data):
        """Test chunked upload with out of range chunk index."""
        upload_id = str(uuid4())

        upload_service.upload_sessions[upload_id] = UploadSession(
            session_id=upload_id,
            filename="test.txt",
            total_size=len(sample_file_data),
            chunk_size=1024,
            total_chunks=3,
            mode=UploadMode.CHUNKED,
            status=UploadStatus.UPLOADING,
            created_at=datetime.utcnow(),
            chunks={},
        )

        with pytest.raises(ValueError, match="Chunk index out of range"):
            await upload_service.upload_chunk(
                upload_id=upload_id,
                chunk_index=10,  # Out of range
                chunk_data=sample_file_data,
            )

    # Test Resumable Upload
    @pytest.mark.asyncio
    async def test_resumable_upload_initiation(self, upload_service, sample_file_info):
        """Test resumable upload initiation."""
        file_hash = "abc123def456"

        session = await upload_service.initiate_resumable_upload(
            file_info=sample_file_info,
            file_hash=file_hash,
        )

        assert session.mode == UploadMode.RESUMABLE
        assert session.file_hash == file_hash
        assert session.status == UploadStatus.PENDING

    @pytest.mark.asyncio
    async def test_resumable_upload_with_existing_session(self, upload_service, sample_file_info):
        """Test resumable upload with existing session."""
        file_hash = "abc123def456"
        upload_id = str(uuid4())

        # Create existing session
        existing_session = UploadSession(
            session_id=upload_id,
            filename=sample_file_info["filename"],
            total_size=sample_file_info["size"],
            chunk_size=1024,
            total_chunks=3,
            mode=UploadMode.RESUMABLE,
            status=UploadStatus.UPLOADING,
            created_at=datetime.utcnow(),
            chunks={0: UploadChunk(
                chunk_id="chunk_0",
                chunk_index=0,
                start_byte=0,
                end_byte=1023,
                size=1024,
                data=b"chunk_data",
                uploaded_at=datetime.utcnow(),
            )},
            file_hash=file_hash,
        )
        upload_service.upload_sessions[upload_id] = existing_session

        session = await upload_service.initiate_resumable_upload(
            file_info=sample_file_info,
            file_hash=file_hash,
        )

        assert session.session_id == upload_id
        assert len(session.chunks) == 1  # Existing chunk preserved

    # Test Progress Tracking
    @pytest.mark.asyncio
    async def test_get_upload_progress(self, upload_service):
        """Test getting upload progress."""
        upload_id = str(uuid4())

        upload_service.active_uploads[upload_id] = UploadProgress(
            upload_id=upload_id,
            status=UploadStatus.UPLOADING,
            total_size=10240,
            uploaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            uploaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            upload_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        progress = upload_service.get_upload_progress(upload_id)

        assert progress.upload_id == upload_id
        assert progress.progress_percentage == 50.0
        assert progress.status == UploadStatus.UPLOADING

    @pytest.mark.asyncio
    async def test_get_progress_nonexistent_upload(self, upload_service):
        """Test getting progress for nonexistent upload."""
        upload_id = "nonexistent_id"

        with pytest.raises(ValueError, match="Upload not found"):
            upload_service.get_upload_progress(upload_id)

    # Test Upload Control
    @pytest.mark.asyncio
    async def test_pause_upload(self, upload_service):
        """Test pausing an upload."""
        upload_id = str(uuid4())

        upload_service.active_uploads[upload_id] = UploadProgress(
            upload_id=upload_id,
            status=UploadStatus.UPLOADING,
            total_size=10240,
            uploaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            uploaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            upload_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        result = await upload_service.pause_upload(upload_id)

        assert result["success"] is True
        assert upload_service.active_uploads[upload_id].status == UploadStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_upload(self, upload_service):
        """Test resuming a paused upload."""
        upload_id = str(uuid4())

        upload_service.active_uploads[upload_id] = UploadProgress(
            upload_id=upload_id,
            status=UploadStatus.PAUSED,
            total_size=10240,
            uploaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            uploaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            upload_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        result = await upload_service.resume_upload(upload_id)

        assert result["success"] is True
        assert upload_service.active_uploads[upload_id].status == UploadStatus.UPLOADING

    @pytest.mark.asyncio
    async def test_cancel_upload(self, upload_service):
        """Test canceling an upload."""
        upload_id = str(uuid4())

        upload_service.active_uploads[upload_id] = UploadProgress(
            upload_id=upload_id,
            status=UploadStatus.UPLOADING,
            total_size=10240,
            uploaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            uploaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            upload_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        result = await upload_service.cancel_upload(upload_id)

        assert result["success"] is True
        assert upload_service.active_uploads[upload_id].status == UploadStatus.CANCELLED
        assert upload_id not in upload_service.active_uploads

    # Test Upload Completion
    @pytest.mark.asyncio
    async def test_complete_upload_success(self, upload_service):
        """Test successful upload completion."""
        upload_id = str(uuid4())

        # Create upload session with all chunks
        session = UploadSession(
            session_id=upload_id,
            filename="test.txt",
            total_size=2048,
            chunk_size=1024,
            total_chunks=2,
            mode=UploadMode.CHUNKED,
            status=UploadStatus.UPLOADING,
            created_at=datetime.utcnow(),
            chunks={
                0: UploadChunk(
                    chunk_id="chunk_0",
                    chunk_index=0,
                    start_byte=0,
                    end_byte=1023,
                    size=1024,
                    data=b"chunk_0_data",
                    uploaded_at=datetime.utcnow(),
                    verified=True,
                ),
                1: UploadChunk(
                    chunk_id="chunk_1",
                    chunk_index=1,
                    start_byte=1024,
                    end_byte=2047,
                    size=1024,
                    data=b"chunk_1_data",
                    uploaded_at=datetime.utcnow(),
                    verified=True,
                ),
            },
        )
        upload_service.upload_sessions[upload_id] = session

        with patch.object(upload_service, '_finalize_upload') as mock_finalize:
            mock_finalize.return_value = {"file_id": str(uuid4()), "status": "completed"}

            result = await upload_service.complete_upload(upload_id)

            assert result["status"] == "completed"
            mock_finalize.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_upload_incomplete_chunks(self, upload_service):
        """Test upload completion with incomplete chunks."""
        upload_id = str(uuid4())

        session = UploadSession(
            session_id=upload_id,
            filename="test.txt",
            total_size=2048,
            chunk_size=1024,
            total_chunks=2,
            mode=UploadMode.CHUNKED,
            status=UploadStatus.UPLOADING,
            created_at=datetime.utcnow(),
            chunks={
                0: UploadChunk(
                    chunk_id="chunk_0",
                    chunk_index=0,
                    start_byte=0,
                    end_byte=1023,
                    size=1024,
                    data=b"chunk_0_data",
                    uploaded_at=datetime.utcnow(),
                    verified=True,
                ),
                # Missing chunk 1
            },
        )
        upload_service.upload_sessions[upload_id] = session

        with pytest.raises(ValueError, match="Upload incomplete"):
            await upload_service.complete_upload(upload_id)

    # Test Error Handling
    @pytest.mark.asyncio
    async def test_upload_file_not_found(self, upload_service, sample_file_info):
        """Test upload with missing file data."""
        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.side_effect = FileNotFoundError("File not found")

            with pytest.raises(FileNotFoundError):
                await upload_service.upload_file(
                    file_data=None,
                    file_info=sample_file_info,
                )

    @pytest.mark.asyncio
    async def test_upload_storage_full(self, upload_service, sample_file_data, sample_file_info):
        """Test upload when storage is full."""
        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = True

            with patch.object(upload_service, '_process_normal_upload') as mock_process:
                mock_process.side_effect = OSError("No space left on device")

                with pytest.raises(OSError, match="No space left on device"):
                    await upload_service.upload_file(
                        file_data=sample_file_data,
                        file_info=sample_file_info,
                    )

    # Test Upload Speed Calculation
    @pytest.mark.asyncio
    async def test_upload_speed_calculation(self, upload_service):
        """Test upload speed calculation."""
        upload_id = str(uuid4())

        # Create progress with initial state
        progress = UploadProgress(
            upload_id=upload_id,
            status=UploadStatus.UPLOADING,
            total_size=10240,
            uploaded_size=0,
            chunk_size=1024,
            total_chunks=10,
            uploaded_chunks=0,
            verified_chunks=0,
            progress_percentage=0.0,
            upload_speed=0.0,
            estimated_time_remaining=0.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )
        upload_service.active_uploads[upload_id] = progress

        # Simulate upload progress
        await asyncio.sleep(0.1)  # Small delay for realistic timing

        progress.uploaded_size = 5120
        progress.uploaded_chunks = 5
        progress.progress_percentage = 50.0
        progress.last_update = datetime.utcnow()

        # Speed should be calculated
        assert progress.upload_speed > 0

    # Test Concurrent Uploads
    @pytest.mark.asyncio
    async def test_concurrent_upload_limit(self, upload_service, sample_file_data, sample_file_info):
        """Test that concurrent upload limit is enforced."""
        # Fill up to the limit
        for i in range(upload_service.max_concurrent_uploads):
            upload_id = str(uuid4())
            upload_service.active_uploads[upload_id] = UploadProgress(
                upload_id=upload_id,
                status=UploadStatus.UPLOADING,
                total_size=10240,
                uploaded_size=0,
                chunk_size=1024,
                total_chunks=10,
                uploaded_chunks=0,
                verified_chunks=0,
                progress_percentage=0.0,
                upload_speed=0.0,
                estimated_time_remaining=0.0,
                start_time=datetime.utcnow(),
                last_update=datetime.utcnow(),
            )

        # Try to start another upload
        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = True

            with pytest.raises(OSError, match="Maximum concurrent uploads reached"):
                await upload_service.upload_file(
                    file_data=sample_file_data,
                    file_info=sample_file_info,
                )


class TestDownloadService:
    """Test suite for DownloadService."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_manager(self):
        """Mock file manager."""
        mock_manager = Mock()
        mock_manager.get_file = AsyncMock()
        mock_manager.update_file = AsyncMock()
        return mock_manager

    @pytest.fixture
    def download_service(self, db_session, file_manager):
        """Create DownloadService instance with mocked dependencies."""
        return DownloadService(
            db_session=db_session,
            file_manager=file_manager,
            chunk_size=1024 * 1024,  # 1MB
            max_concurrent_downloads=3,
            download_timeout=300,
            rate_limit=10 * 1024 * 1024,  # 10MB/s
        )

    @pytest.fixture
    def sample_file(self):
        """Create sample file object."""
        file_mock = Mock()
        file_mock.id = str(uuid4())
        file_mock.filename = "test_file.txt"
        file_mock.size = 10240
        file_mock.storage_path = "/tmp/test_file.txt"
        file_mock.hash = "abc123def456"
        return file_mock

    # Test Download Service Initialization
    def test_download_service_initialization(self, download_service):
        """Test download service initialization."""
        assert download_service.chunk_size == 1024 * 1024
        assert download_service.max_concurrent_downloads == 3
        assert download_service.download_timeout == 300
        assert download_service.rate_limit == 10 * 1024 * 1024
        assert download_service.active_downloads == {}
        assert download_service.download_sessions == {}

    # Test Normal Download
    @pytest.mark.asyncio
    async def test_normal_download_success(self, download_service, sample_file):
        """Test successful normal download."""
        file_data = b"Test file content" * 100

        with patch("builtins.open", mock_open(read_data=file_data)):
            with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
                mock_get_file.return_value = sample_file

                result = await download_service.download_file(
                    file_id=sample_file.id,
                )

                assert result["file_id"] == sample_file.id
                assert result["status"] == "completed"
                assert len(result["data"]) == len(file_data)

    @pytest.mark.asyncio
    async def test_download_file_not_found(self, download_service):
        """Test download with nonexistent file."""
        with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
            mock_get_file.return_value = None

            with pytest.raises(ValueError, match="File not found"):
                await download_service.download_file(
                    file_id="nonexistent_id",
                )

    # Test Stream Download
    @pytest.mark.asyncio
    async def test_stream_download_success(self, download_service, sample_file):
        """Test successful streaming download."""
        file_data = b"Test file content" * 100
        chunk_size = 1024

        async def mock_read_chunks():
            for i in range(0, len(file_data), chunk_size):
                yield file_data[i:i + chunk_size]

        with patch.object(download_service, '_stream_file_chunks', mock_read_chunks):
            chunks_received = []
            async for chunk in download_service.stream_file(sample_file.id):
                chunks_received.append(chunk)

            # Verify chunks were received
            assert len(chunks_received) > 0
            assert b"".join(chunks_received) == file_data

    @pytest.mark.asyncio
    async def test_stream_download_with_progress(self, download_service, sample_file):
        """Test streaming download with progress tracking."""
        download_id = str(uuid4())

        download_service.active_downloads[download_id] = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=sample_file.size,
            downloaded_size=0,
            chunk_size=1024,
            total_chunks=10,
            downloaded_chunks=0,
            verified_chunks=0,
            progress_percentage=0.0,
            download_speed=0.0,
            estimated_time_remaining=0.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        file_data = b"Test file content" * 100
        chunk_size = 1024

        async def mock_read_chunks():
            for i in range(0, len(file_data), chunk_size):
                # Update progress
                progress = download_service.active_downloads[download_id]
                progress.downloaded_size = min(i + chunk_size, len(file_data))
                progress.downloaded_chunks = (i // chunk_size) + 1
                progress.progress_percentage = (progress.downloaded_size / progress.total_size) * 100
                progress.last_update = datetime.utcnow()

                yield file_data[i:i + chunk_size]

        with patch.object(download_service, '_stream_file_chunks', mock_read_chunks):
            chunks_received = []
            async for chunk in download_service.stream_file(sample_file.id, download_id=download_id):
                chunks_received.append(chunk)

            # Verify progress was updated
            progress = download_service.active_downloads[download_id]
            assert progress.progress_percentage > 0
            assert progress.downloaded_size > 0

    # Test Chunked Download
    @pytest.mark.asyncio
    async def test_chunked_download_initiation(self, download_service, sample_file):
        """Test chunked download initiation."""
        session = await download_service.initiate_chunked_download(
            file_id=sample_file.id,
            chunk_size=1024,
        )

        assert session.session_id is not None
        assert session.file_id == sample_file.id
        assert session.filename == sample_file.filename
        assert session.total_size == sample_file.size
        assert session.status == DownloadStatus.PENDING
        assert session.chunk_size == 1024

    @pytest.mark.asyncio
    async def test_chunked_download_success(self, download_service, sample_file):
        """Test successful chunked download."""
        session_id = str(uuid4())
        chunk_data = b"Test chunk data"

        # Create download session
        session = DownloadSession(
            session_id=session_id,
            file_id=sample_file.id,
            filename=sample_file.filename,
            total_size=sample_file.size,
            chunk_size=1024,
            total_chunks=10,
            status=DownloadStatus.DOWNLOADING,
            created_at=datetime.utcnow(),
            chunks={},
        )
        download_service.download_sessions[session_id] = session

        with patch.object(download_service, '_download_chunk') as mock_download:
            mock_download.return_value = chunk_data

            result = await download_service.download_chunk(
                session_id=session_id,
                chunk_index=0,
            )

            assert result["chunk_index"] == 0
            assert result["data"] == chunk_data
            assert 0 in session.chunks

    @pytest.mark.asyncio
    async def test_chunked_download_invalid_session(self, download_service, sample_file):
        """Test chunked download with invalid session."""
        with pytest.raises(ValueError, match="Download session not found"):
            await download_service.download_chunk(
                session_id="invalid_session",
                chunk_index=0,
            )

    # Test Download Control
    @pytest.mark.asyncio
    async def test_pause_download(self, download_service):
        """Test pausing a download."""
        download_id = str(uuid4())

        download_service.active_downloads[download_id] = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=10240,
            downloaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            downloaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            download_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        result = await download_service.pause_download(download_id)

        assert result["success"] is True
        assert download_service.active_downloads[download_id].status == DownloadStatus.PAUSED

    @pytest.mark.asyncio
    async def test_resume_download(self, download_service):
        """Test resuming a paused download."""
        download_id = str(uuid4())

        download_service.active_downloads[download_id] = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.PAUSED,
            total_size=10240,
            downloaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            downloaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            download_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        result = await download_service.resume_download(download_id)

        assert result["success"] is True
        assert download_service.active_downloads[download_id].status == DownloadStatus.DOWNLOADING

    @pytest.mark.asyncio
    async def test_cancel_download(self, download_service):
        """Test canceling a download."""
        download_id = str(uuid4())

        download_service.active_downloads[download_id] = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=10240,
            downloaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            downloaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            download_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        result = await download_service.cancel_download(download_id)

        assert result["success"] is True
        assert download_service.active_downloads[download_id].status == DownloadStatus.CANCELLED
        assert download_id not in download_service.active_downloads

    # Test Rate Limiting
    @pytest.mark.asyncio
    async def test_rate_limiting(self, download_service, sample_file):
        """Test download rate limiting."""
        download_id = str(uuid4())
        chunk_data = b"x" * 10240  # 10KB chunk

        download_service.active_downloads[download_id] = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=102400,  # 100KB
            downloaded_size=0,
            chunk_size=10240,
            total_chunks=10,
            downloaded_chunks=0,
            verified_chunks=0,
            progress_percentage=0.0,
            download_speed=0.0,
            estimated_time_remaining=0.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        start_time = time.time()

        # Simulate downloading with rate limiting
        with patch.object(download_service, '_enforce_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = True

            await download_service._enforce_rate_limit(
                download_id=download_id,
                chunk_size=len(chunk_data),
            )

            # Rate limit should have been enforced
            mock_rate_limit.assert_called_once()

        # Verify that rate limiting adds appropriate delay
        elapsed = time.time() - start_time
        assert elapsed > 0  # Some time should have passed

    @pytest.mark.asyncio
    async def test_rate_limit_calculation(self, download_service):
        """Test rate limit calculation."""
        download_id = str(uuid4())

        # Create progress with high download speed
        progress = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=102400,
            downloaded_size=51200,
            chunk_size=10240,
            total_chunks=10,
            downloaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            download_speed=20 * 1024 * 1024,  # 20MB/s (exceeds 10MB/s limit)
            estimated_time_remaining=2.5,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )
        download_service.active_downloads[download_id] = progress

        # Should enforce rate limiting
        assert progress.download_speed > download_service.rate_limit

    # Test Progress Tracking
    @pytest.mark.asyncio
    async def test_get_download_progress(self, download_service):
        """Test getting download progress."""
        download_id = str(uuid4())

        download_service.active_downloads[download_id] = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=10240,
            downloaded_size=5120,
            chunk_size=1024,
            total_chunks=10,
            downloaded_chunks=5,
            verified_chunks=5,
            progress_percentage=50.0,
            download_speed=1024.0,
            estimated_time_remaining=5.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )

        progress = download_service.get_download_progress(download_id)

        assert progress.download_id == download_id
        assert progress.progress_percentage == 50.0
        assert progress.status == DownloadStatus.DOWNLOADING

    @pytest.mark.asyncio
    async def test_get_progress_nonexistent_download(self, download_service):
        """Test getting progress for nonexistent download."""
        download_id = "nonexistent_id"

        with pytest.raises(ValueError, match="Download not found"):
            download_service.get_download_progress(download_id)

    # Test Download Completion
    @pytest.mark.asyncio
    async def test_complete_download_success(self, download_service):
        """Test successful download completion."""
        session_id = str(uuid4())

        # Create download session with all chunks
        session = DownloadSession(
            session_id=session_id,
            file_id=str(uuid4()),
            filename="test.txt",
            total_size=2048,
            chunk_size=1024,
            total_chunks=2,
            status=DownloadStatus.DOWNLOADING,
            created_at=datetime.utcnow(),
            chunks={
                0: DownloadChunk(
                    chunk_id="chunk_0",
                    start_byte=0,
                    end_byte=1023,
                    size=1024,
                    data=b"chunk_0_data",
                    downloaded_at=datetime.utcnow(),
                    verified=True,
                ),
                1: DownloadChunk(
                    chunk_id="chunk_1",
                    start_byte=1024,
                    end_byte=2047,
                    size=1024,
                    data=b"chunk_1_data",
                    downloaded_at=datetime.utcnow(),
                    verified=True,
                ),
            },
        )
        download_service.download_sessions[session_id] = session

        with patch.object(download_service, '_finalize_download') as mock_finalize:
            mock_finalize.return_value = {"status": "completed", "file_path": "/tmp/test.txt"}

            result = await download_service.complete_download(session_id)

            assert result["status"] == "completed"
            mock_finalize.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_download_incomplete_chunks(self, download_service):
        """Test download completion with incomplete chunks."""
        session_id = str(uuid4())

        session = DownloadSession(
            session_id=session_id,
            file_id=str(uuid4()),
            filename="test.txt",
            total_size=2048,
            chunk_size=1024,
            total_chunks=2,
            status=DownloadStatus.DOWNLOADING,
            created_at=datetime.utcnow(),
            chunks={
                0: DownloadChunk(
                    chunk_id="chunk_0",
                    start_byte=0,
                    end_byte=1023,
                    size=1024,
                    data=b"chunk_0_data",
                    downloaded_at=datetime.utcnow(),
                    verified=True,
                ),
                # Missing chunk 1
            },
        )
        download_service.download_sessions[session_id] = session

        with pytest.raises(ValueError, match="Download incomplete"):
            await download_service.complete_download(session_id)

    # Test Error Handling
    @pytest.mark.asyncio
    async def test_download_permission_denied(self, download_service, sample_file):
        """Test download with permission denied."""
        with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
            mock_get_file.side_effect = PermissionError("Permission denied")

            with pytest.raises(PermissionError, match="Permission denied"):
                await download_service.download_file(
                    file_id=sample_file.id,
                )

    @pytest.mark.asyncio
    async def test_download_storage_error(self, download_service, sample_file):
        """Test download with storage error."""
        with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
            mock_get_file.return_value = sample_file

            with patch("builtins.open", side_effect=OSError("I/O error")):
                with pytest.raises(OSError, match="I/O error"):
                    await download_service.download_file(
                        file_id=sample_file.id,
                    )

    # Test Download Speed Calculation
    @pytest.mark.asyncio
    async def test_download_speed_calculation(self, download_service):
        """Test download speed calculation."""
        download_id = str(uuid4())

        # Create progress with initial state
        progress = DownloadProgress(
            download_id=download_id,
            status=DownloadStatus.DOWNLOADING,
            total_size=10240,
            downloaded_size=0,
            chunk_size=1024,
            total_chunks=10,
            downloaded_chunks=0,
            verified_chunks=0,
            progress_percentage=0.0,
            download_speed=0.0,
            estimated_time_remaining=0.0,
            start_time=datetime.utcnow(),
            last_update=datetime.utcnow(),
        )
        download_service.active_downloads[download_id] = progress

        # Simulate download progress
        await asyncio.sleep(0.1)  # Small delay for realistic timing

        progress.downloaded_size = 5120
        progress.downloaded_chunks = 5
        progress.progress_percentage = 50.0
        progress.last_update = datetime.utcnow()

        # Speed should be calculated
        assert progress.download_speed > 0

    # Test Concurrent Downloads
    @pytest.mark.asyncio
    async def test_concurrent_download_limit(self, download_service, sample_file):
        """Test that concurrent download limit is enforced."""
        # Fill up to the limit
        for i in range(download_service.max_concurrent_downloads):
            download_id = str(uuid4())
            download_service.active_downloads[download_id] = DownloadProgress(
                download_id=download_id,
                status=DownloadStatus.DOWNLOADING,
                total_size=10240,
                downloaded_size=0,
                chunk_size=1024,
                total_chunks=10,
                downloaded_chunks=0,
                verified_chunks=0,
                progress_percentage=0.0,
                download_speed=0.0,
                estimated_time_remaining=0.0,
                start_time=datetime.utcnow(),
                last_update=datetime.utcnow(),
            )

        # Try to start another download
        with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
            mock_get_file.return_value = sample_file

            with pytest.raises(OSError, match="Maximum concurrent downloads reached"):
                await download_service.download_file(
                    file_id=sample_file.id,
                )


class TestIntegration:
    """Integration tests for file services."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_manager(self):
        """Mock file manager."""
        mock_manager = Mock()
        mock_manager.create_file = AsyncMock()
        mock_manager.get_file = AsyncMock()
        mock_manager.update_file = AsyncMock()
        return mock_manager

    @pytest.fixture
    def upload_service(self, db_session, file_manager):
        """Create UploadService instance."""
        return UploadService(
            db_session=db_session,
            file_manager=file_manager,
            max_chunk_size=1024,
            max_concurrent_uploads=2,
            upload_timeout=60,
        )

    @pytest.fixture
    def download_service(self, db_session, file_manager):
        """Create DownloadService instance."""
        return DownloadService(
            db_session=db_session,
            file_manager=file_manager,
            chunk_size=1024,
            max_concurrent_downloads=2,
            download_timeout=60,
            rate_limit=1024 * 1024,  # 1MB/s
        )

    @pytest.mark.asyncio
    async def test_upload_download_round_trip(self, upload_service, download_service):
        """Test complete upload-download round trip."""
        file_data = b"Round trip test data" * 10
        file_info = {
            "filename": "roundtrip.txt",
            "content_type": "text/plain",
            "size": len(file_data),
            "hash": "sha256:test123",
        }

        # Upload file
        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = True

            with patch.object(upload_service, '_process_normal_upload') as mock_process:
                mock_process.return_value = {"file_id": "test_file_id", "status": "completed"}

                upload_result = await upload_service.upload_file(
                    file_data=file_data,
                    file_info=file_info,
                    mode=UploadMode.NORMAL,
                )

                assert upload_result["status"] == "completed"

        # Create mock file for download
        mock_file = Mock()
        mock_file.id = "test_file_id"
        mock_file.filename = file_info["filename"]
        mock_file.size = file_info["size"]
        mock_file.storage_path = "/tmp/roundtrip.txt"
        mock_file.hash = file_info["hash"]

        # Download file
        with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
            mock_get_file.return_value = mock_file

            with patch("builtins.open", mock_open(read_data=file_data)):
                download_result = await download_service.download_file(
                    file_id="test_file_id",
                )

                assert download_result["status"] == "completed"
                assert download_result["data"] == file_data

    @pytest.mark.asyncio
    async def test_chunked_upload_download(self, upload_service, download_service):
        """Test chunked upload and download."""
        file_data = b"Chunked test data" * 50  # 2KB
        file_info = {
            "filename": "chunked.txt",
            "content_type": "text/plain",
            "size": len(file_data),
            "hash": "sha256:chunked123",
        }

        # Initiate chunked upload
        session = await upload_service.initiate_chunked_upload(
            file_info=file_info,
            chunk_size=512,
        )

        assert session.total_chunks == 4  # 2000 / 512 = 3.9 -> 4 chunks

        # Upload chunks
        chunk_size = 512
        for i in range(session.total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(file_data))
            chunk_data = file_data[start:end]

            result = await upload_service.upload_chunk(
                upload_id=session.session_id,
                chunk_index=i,
                chunk_data=chunk_data,
            )

            assert result["success"] is True

        # Complete upload
        with patch.object(upload_service, '_finalize_upload') as mock_finalize:
            mock_finalize.return_value = {"file_id": "chunked_file_id", "status": "completed"}

            upload_result = await upload_service.complete_upload(session.session_id)
            assert upload_result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_concurrent_uploads_and_downloads(self, upload_service, download_service):
        """Test concurrent uploads and downloads."""
        file_data = b"Concurrent test data" * 20  # 560 bytes

        # Create multiple upload sessions
        upload_sessions = []
        for i in range(3):
            file_info = {
                "filename": f"concurrent_{i}.txt",
                "content_type": "text/plain",
                "size": len(file_data),
                "hash": f"sha256:hash_{i}",
            }

            session = await upload_service.initiate_chunked_upload(
                file_info=file_info,
                chunk_size=256,
            )
            upload_sessions.append(session)

        # Verify sessions were created
        assert len(upload_sessions) == 3
        assert len(upload_service.upload_sessions) == 3

        # Verify no session conflicts
        session_ids = [s.session_id for s in upload_sessions]
        assert len(session_ids) == len(set(session_ids))  # All unique

    @pytest.mark.asyncio
    async def test_upload_pause_resume_download(self, upload_service, download_service):
        """Test upload pause/resume with download."""
        file_data = b"Pause resume test data" * 30  # 840 bytes
        file_info = {
            "filename": "pause_resume.txt",
            "content_type": "text/plain",
            "size": len(file_data),
            "hash": "sha256:pause123",
        }

        # Initiate chunked upload
        session = await upload_service.initiate_chunked_upload(
            file_info=file_info,
            chunk_size=256,
        )

        upload_id = session.session_id

        # Upload first chunk
        chunk_data = file_data[:256]
        await upload_service.upload_chunk(
            upload_id=upload_id,
            chunk_index=0,
            chunk_data=chunk_data,
        )

        # Pause upload
        pause_result = await upload_service.pause_upload(upload_id)
        assert pause_result["success"] is True

        # Verify pause
        assert upload_service.active_uploads[upload_id].status == UploadStatus.PAUSED

        # Resume upload
        resume_result = await upload_service.resume_upload(upload_id)
        assert resume_result["success"] is True

        # Verify resume
        assert upload_service.active_uploads[upload_id].status == UploadStatus.UPLOADING


class TestPerformance:
    """Performance tests for file services."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_manager(self):
        """Mock file manager."""
        mock_manager = Mock()
        mock_manager.create_file = AsyncMock()
        mock_manager.get_file = AsyncMock()
        mock_manager.update_file = AsyncMock()
        return mock_manager

    @pytest.mark.asyncio
    async def test_large_file_upload_performance(self, upload_service):
        """Test performance with large file upload."""
        # Create 1MB file data
        file_data = b"x" * (1024 * 1024)  # 1MB
        file_info = {
            "filename": "large_file.bin",
            "content_type": "application/octet-stream",
            "size": len(file_data),
            "hash": "sha256:large123",
        }

        start_time = time.time()

        with patch.object(upload_service, '_validate_file') as mock_validate:
            mock_validate.return_value = True

            with patch.object(upload_service, '_process_normal_upload') as mock_process:
                mock_process.return_value = {"file_id": "large_file_id", "status": "completed"}

                result = await upload_service.upload_file(
                    file_data=file_data,
                    file_info=file_info,
                    mode=UploadMode.NORMAL,
                )

                elapsed = time.time() - start_time

                assert result["status"] == "completed"
                # Should complete quickly with mocked processing
                assert elapsed < 1.0  # Less than 1 second

    @pytest.mark.asyncio
    async def test_large_file_download_performance(self, download_service):
        """Test performance with large file download."""
        # Create 1MB file data
        file_data = b"x" * (1024 * 1024)  # 1MB

        mock_file = Mock()
        mock_file.id = "large_file_id"
        mock_file.filename = "large_file.bin"
        mock_file.size = len(file_data)
        mock_file.storage_path = "/tmp/large_file.bin"
        mock_file.hash = "sha256:large123"

        start_time = time.time()

        with patch.object(download_service.file_manager, 'get_file') as mock_get_file:
            mock_get_file.return_value = mock_file

            with patch("builtins.open", mock_open(read_data=file_data)):
                result = await download_service.download_file(
                    file_id="large_file_id",
                )

                elapsed = time.time() - start_time

                assert result["status"] == "completed"
                # Should complete quickly with mocked file I/O
                assert elapsed < 1.0  # Less than 1 second

    @pytest.mark.asyncio
    async def test_many_small_chunks_performance(self, upload_service):
        """Test performance with many small chunks."""
        file_data = b"Small chunk data" * 10  # 208 bytes
        chunk_size = 64  # Very small chunks

        file_info = {
            "filename": "many_chunks.txt",
            "content_type": "text/plain",
            "size": len(file_data),
            "hash": "sha256:many123",
        }

        start_time = time.time()

        # Initiate chunked upload
        session = await upload_service.initiate_chunked_upload(
            file_info=file_info,
            chunk_size=chunk_size,
        )

        # Upload all chunks
        for i in range(session.total_chunks):
            start = i * chunk_size
            end = min(start + chunk_size, len(file_data))
            chunk_data = file_data[start:end]

            result = await upload_service.upload_chunk(
                upload_id=session.session_id,
                chunk_index=i,
                chunk_data=chunk_data,
            )

            assert result["success"] is True

        elapsed = time.time() - start_time

        # Should handle many small chunks efficiently
        assert elapsed < 2.0  # Less than 2 seconds for all chunks

    @pytest.mark.asyncio
    async def test_memory_usage_large_files(self, upload_service):
        """Test memory usage with large files."""
        # Create progressively larger files to test memory usage
        file_sizes = [
            1024,      # 1KB
            10240,     # 10KB
            102400,    # 100KB
            1048576,   # 1MB
        ]

        for size in file_sizes:
            file_data = b"x" * size
            file_info = {
                "filename": f"memory_test_{size}.bin",
                "content_type": "application/octet-stream",
                "size": size,
                "hash": f"sha256:mem_{size}",
            }

            with patch.object(upload_service, '_validate_file') as mock_validate:
                mock_validate.return_value = True

                with patch.object(upload_service, '_process_normal_upload') as mock_process:
                    mock_process.return_value = {"file_id": f"mem_file_{size}", "status": "completed"}

                    result = await upload_service.upload_file(
                        file_data=file_data,
                        file_info=file_info,
                        mode=UploadMode.NORMAL,
                    )

                    assert result["status"] == "completed"

                    # Clean up after each test
                    upload_service.active_uploads.clear()
                    upload_service.upload_sessions.clear()


if __name__ == "__main__":
    pytest.main([__file__])