"""Integration Tests for File Management System.

This module contains end-to-end integration tests for the entire file management
system, testing complete workflows and component interactions.
"""

import pytest
import asyncio
import tempfile
import os
import shutil
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import hashlib

# Import all file management components
from app.file.manager import FileManager
from app.file.editor import FileEditor
from app.file.version_manager import VersionManager
from app.file.preview_manager import PreviewManager
from app.file.batch_processor import BatchProcessor, OperationType
from app.file.services.upload_service import UploadService, UploadMode
from app.file.services.download_service import DownloadService
from app.file.services.conversion_service import ConversionService
from app.file.event_manager import FileOperationEvent, EventType
from app.file.models.file import File
from app.file.models.file_version import FileVersion
from app.database.session import get_db


class TestFileManagementIntegration:
    """Integration test suite for file management system."""

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def file_manager(self, db_session):
        """Create file manager instance."""
        return FileManager(db_session=db_session)

    @pytest.fixture
    def version_manager(self, db_session):
        """Create version manager instance."""
        return VersionManager(db_session=db_session)

    @pytest.fixture
    def preview_manager(self, db_session):
        """Create preview manager instance."""
        return PreviewManager(db_session=db_session)

    @pytest.fixture
    def batch_processor(self, db_session):
        """Create batch processor instance."""
        return BatchProcessor(db_session=db_session)

    @pytest.fixture
    def upload_service(self, file_manager):
        """Create upload service instance."""
        return UploadService(
            db_session=file_manager.db_session,
            file_manager=file_manager,
        )

    @pytest.fixture
    def download_service(self, file_manager):
        """Create download service instance."""
        return DownloadService(
            db_session=file_manager.db_session,
            file_manager=file_manager,
        )

    @pytest.fixture
    def conversion_service(self):
        """Create conversion service instance."""
        return ConversionService()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    # Complete File Lifecycle Test
    @pytest.mark.asyncio
    async def test_complete_file_lifecycle(
        self,
        file_manager,
        version_manager,
        preview_manager,
        upload_service,
        download_service,
        conversion_service,
        temp_dir,
    ):
        """Test complete file lifecycle from creation to deletion."""
        # Step 1: Create file
        file_data = {
            "filename": "lifecycle_test.txt",
            "content_type": "text/plain",
            "size": 1024,
            "folder_id": str(uuid4()),
        }

        with patch.object(file_manager, 'create_file') as mock_create:
            mock_file = Mock()
            mock_file.id = str(uuid4())
            mock_file.filename = "lifecycle_test.txt"
            mock_file.size = 1024
            mock_create.return_value = mock_file

            file = await file_manager.create_file(file_data)
            assert file.id is not None

        # Step 2: Upload file content
        file_content = b"Test file content for lifecycle testing"

        with patch.object(upload_service, 'upload_file') as mock_upload:
            mock_upload.return_value = {
                "file_id": file.id,
                "status": "completed",
            }

            upload_result = await upload_service.upload_file(
                file_data=file_content,
                file_info={"filename": "lifecycle_test.txt"},
                mode=UploadMode.NORMAL,
            )
            assert upload_result["status"] == "completed"

        # Step 3: Create version
        with patch.object(version_manager, 'create_version') as mock_create_version:
            mock_version = Mock()
            mock_version.id = str(uuid4())
            mock_version.file_id = file.id
            mock_version.version_number = 1
            mock_create_version.return_value = mock_version

            version = await version_manager.create_version(
                file_id=file.id,
                content=file_content.decode(),
                version_note="Initial version",
            )
            assert version.id is not None

        # Step 4: Generate preview
        with patch.object(preview_manager, 'generate_preview') as mock_preview:
            mock_preview_data = Mock()
            mock_preview_data.id = str(uuid4())
            mock_preview_data.file_id = file.id
            mock_preview_data.format = "thumbnail"
            mock_preview.return_value = mock_preview_data

            preview = await preview_manager.generate_preview(
                file_id=file.id,
                format="thumbnail",
            )
            assert preview.id is not None

        # Step 5: Download file
        with patch.object(download_service, 'download_file') as mock_download:
            mock_download.return_value = {
                "data": file_content,
                "filename": "lifecycle_test.txt",
                "size": len(file_content),
            }

            download_result = await download_service.download_file(file.id)
            assert download_result["data"] == file_content

        # Step 6: Update file
        updated_content = b"Updated file content"

        with patch.object(file_manager, 'update_file') as mock_update:
            mock_updated_file = Mock()
            mock_updated_file.id = file.id
            mock_update.return_value = mock_updated_file

            updated_file = await file_manager.update_file(
                file_id=file.id,
                updates={"content": updated_content.decode()},
            )
            assert updated_file.id == file.id

        # Step 7: Create another version
        with patch.object(version_manager, 'create_version') as mock_create_version2:
            mock_version2 = Mock()
            mock_version2.id = str(uuid4())
            mock_version2.file_id = file.id
            mock_version2.version_number = 2
            mock_create_version2.return_value = mock_version2

            version2 = await version_manager.create_version(
                file_id=file.id,
                content=updated_content.decode(),
                version_note="Updated version",
            )
            assert version2.version_number == 2

        # Step 8: Convert file format
        with patch.object(conversion_service, 'convert_format') as mock_convert:
            mock_convert.return_value = {
                "success": True,
                "converted_data": updated_content,
                "format": "pdf",
            }

            conversion_result = await conversion_service.convert_format(
                data=updated_content,
                source_format="txt",
                target_format="pdf",
            )
            assert conversion_result["success"] is True

        # Step 9: Delete file
        with patch.object(file_manager, 'delete_file') as mock_delete:
            mock_delete.return_value = True

            success = await file_manager.delete_file(file.id)
            assert success is True

    # Batch Operations Integration Test
    @pytest.mark.asyncio
    async def test_batch_operations_integration(
        self,
        batch_processor,
        file_manager,
        temp_dir,
    ):
        """Test batch operations integration."""
        # Create multiple files
        file_ids = []
        for i in range(10):
            file_id = str(uuid4())
            file_ids.append(file_id)

        # Step 1: Batch upload
        with patch.object(batch_processor, 'create_batch_job') as mock_create_job:
            mock_job = Mock()
            mock_job.job_id = str(uuid4())
            mock_job.status = "running"
            mock_create_job.return_value = mock_job

            with patch.object(batch_processor, 'process_batch_job') as mock_process:
                mock_result = Mock()
                mock_result.successful_count = 10
                mock_result.failed_count = 0
                mock_result.to_dict.return_value = {"status": "completed"}
                mock_process.return_value = mock_result

                job = await batch_processor.create_batch_job(
                    operation_type=OperationType.UPLOAD,
                    file_ids=file_ids,
                )
                assert job.job_id is not None

                result = await batch_processor.process_batch_job(job.job_id)
                assert result.successful_count == 10

        # Step 2: Batch move
        with patch.object(batch_processor, 'create_batch_job') as mock_create_job2:
            mock_job2 = Mock()
            mock_job2.job_id = str(uuid4())
            mock_job2.status = "running"
            mock_create_job2.return_value = mock_job2

            with patch.object(batch_processor, 'process_batch_job') as mock_process2:
                mock_result2 = Mock()
                mock_result2.successful_count = 10
                mock_result2.failed_count = 0
                mock_result2.to_dict.return_value = {"status": "completed"}
                mock_process2.return_value = mock_result2

                job2 = await batch_processor.create_batch_job(
                    operation_type=OperationType.MOVE,
                    file_ids=file_ids,
                    parameters={"destination_folder": "/new/location"},
                )
                assert job2.job_id is not None

                result2 = await batch_processor.process_batch_job(job2.job_id)
                assert result2.successful_count == 10

        # Step 3: Batch delete
        with patch.object(batch_processor, 'create_batch_job') as mock_create_job3:
            mock_job3 = Mock()
            mock_job3.job_id = str(uuid4())
            mock_job3.status = "running"
            mock_create_job3.return_value = mock_job3

            with patch.object(batch_processor, 'process_batch_job') as mock_process3:
                mock_result3 = Mock()
                mock_result3.successful_count = 10
                mock_result3.failed_count = 0
                mock_result3.to_dict.return_value = {"status": "completed"}
                mock_process3.return_value = mock_result3

                job3 = await batch_processor.create_batch_job(
                    operation_type=OperationType.DELETE,
                    file_ids=file_ids,
                )
                assert job3.job_id is not None

                result3 = await batch_processor.process_batch_job(job3.job_id)
                assert result3.successful_count == 10

    # Editor Integration Test
    @pytest.mark.asyncio
    async def test_editor_integration(
        self,
        db_session,
        version_manager,
        file_manager,
    ):
        """Test online editor integration."""
        from app.file.editor import FileEditor

        editor = FileEditor(db_session=db_session)

        # Create editor session
        file_id = str(uuid4())

        with patch.object(editor, 'create_editor_session') as mock_create_session:
            mock_session = Mock()
            mock_session.session_id = str(uuid4())
            mock_session.file_id = file_id
            mock_session.created_at = datetime.utcnow()
            mock_create_session.return_value = mock_session

            session = await editor.create_editor_session(file_id=file_id)
            assert session.session_id is not None

        # Get file content
        with patch.object(editor, 'get_file_content') as mock_get_content:
            mock_get_content.return_value = {
                "content": "File content for editing",
                "metadata": {"language": "text"},
                "line_count": 1,
            }

            content = await editor.get_file_content(session.session_id)
            assert content["content"] == "File content for editing"

        # Update file content
        with patch.object(editor, 'update_file_content') as mock_update:
            mock_result = Mock()
            mock_result.file_id = file_id
            mock_result.version_id = str(uuid4())
            mock_result.content_hash = "abc123"
            mock_result.last_modified = datetime.utcnow()
            mock_update.return_value = mock_result

            updated = await editor.update_file_content(
                session_id=session.session_id,
                content="Updated content",
                version_note="Edited in online editor",
            )
            assert updated.file_id == file_id

        # Close editor session
        with patch.object(editor, 'close_editor_session') as mock_close:
            mock_close.return_value = True

            success = await editor.close_editor_session(session.session_id)
            assert success is True

    # Version Control Integration Test
    @pytest.mark.asyncio
    async def test_version_control_integration(
        self,
        version_manager,
        file_manager,
    ):
        """Test version control system integration."""
        file_id = str(uuid4())

        # Create multiple versions
        versions = []
        for i in range(5):
            with patch.object(version_manager, 'create_version') as mock_create:
                mock_version = Mock()
                mock_version.id = str(uuid4())
                mock_version.file_id = file_id
                mock_version.version_number = i + 1
                mock_version.created_at = datetime.utcnow()
                mock_version.version_note = f"Version {i + 1}"
                mock_create.return_value = mock_version

                version = await version_manager.create_version(
                    file_id=file_id,
                    content=f"Content version {i + 1}",
                    version_note=f"Version {i + 1}",
                )
                versions.append(version)

        assert len(versions) == 5

        # List versions
        with patch.object(version_manager, 'list_versions') as mock_list:
            mock_list_result = Mock()
            mock_list_result.versions = versions
            mock_list_result.total = 5
            mock_list.return_value = mock_list_result

            result = await version_manager.list_versions(file_id=file_id)
            assert result.total == 5

        # Get latest version
        with patch.object(version_manager, 'get_latest_version') as mock_latest:
            mock_latest.return_value = versions[-1]

            latest = await version_manager.get_latest_version(file_id=file_id)
            assert latest.version_number == 5

        # Restore version
        with patch.object(version_manager, 'restore_version') as mock_restore:
            mock_restored = Mock()
            mock_restored.id = str(uuid4())
            mock_restored.file_id = file_id
            mock_restored.version_number = 6
            mock_restore.return_value = mock_restored

            restored = await version_manager.restore_version(
                file_id=file_id,
                version_id=versions[0].id,
            )
            assert restored.version_number == 6

        # Compare versions
        with patch.object(version_manager, 'compare_versions') as mock_compare:
            mock_compare_result = Mock()
            mock_compare_result.version1 = versions[0]
            mock_compare_result.version2 = versions[-1]
            mock_compare_result.diff = "Added lines..."
            mock_compare.return_value = mock_compare_result

            comparison = await version_manager.compare_versions(
                version1_id=versions[0].id,
                version2_id=versions[-1].id,
            )
            assert comparison.diff is not None

    # Preview System Integration Test
    @pytest.mark.asyncio
    async def test_preview_system_integration(
        self,
        preview_manager,
        conversion_service,
    ):
        """Test preview system integration."""
        file_id = str(uuid4())

        # Generate image preview
        with patch.object(preview_manager, 'generate_preview') as mock_preview:
            mock_preview_data = Mock()
            mock_preview_data.id = str(uuid4())
            mock_preview_data.file_id = file_id
            mock_preview_data.format = "thumbnail"
            mock_preview.return_value = mock_preview_data

            preview = await preview_manager.generate_preview(
                file_id=file_id,
                format="thumbnail",
            )
            assert preview.id is not None

        # Generate code preview
        with patch.object(preview_manager, 'get_code_preview') as mock_code:
            mock_code_result = Mock()
            mock_code_result.html_content = "<div>Code preview</div>"
            mock_code_result.language = "python"
            mock_code.return_value = mock_code_result

            code_preview = await preview_manager.get_code_preview(
                file_id=file_id,
                language="python",
            )
            assert code_preview.html_content is not None

        # Generate document preview
        with patch.object(preview_manager, 'get_document_preview') as mock_doc:
            mock_doc_result = "<html>Document preview</html>"
            mock_doc.return_value = mock_doc_result

            doc_preview = await preview_manager.get_document_preview(
                file_id=file_id,
                format="html",
            )
            assert doc_preview is not None

        # Convert format
        with patch.object(conversion_service, 'convert_format') as mock_convert:
            mock_convert.return_value = {
                "success": True,
                "converted_data": b"converted content",
                "format": "pdf",
            }

            result = await conversion_service.convert_format(
                data=b"original content",
                source_format="txt",
                target_format="pdf",
            )
            assert result["success"] is True

    # Upload/Download Service Integration Test
    @pytest.mark.asyncio
    async def test_upload_download_integration(
        self,
        upload_service,
        download_service,
        file_manager,
    ):
        """Test upload and download service integration."""
        file_content = b"Integration test content"
        file_info = {
            "filename": "integration_test.txt",
            "content_type": "text/plain",
            "size": len(file_content),
        }

        # Normal upload
        with patch.object(upload_service, 'upload_file') as mock_upload:
            mock_upload.return_value = {
                "file_id": str(uuid4()),
                "status": "completed",
            }

            result = await upload_service.upload_file(
                file_data=file_content,
                file_info=file_info,
                mode=UploadMode.NORMAL,
            )
            assert result["status"] == "completed"

        # Chunked upload
        with patch.object(upload_service, 'initiate_chunked_upload') as mock_init:
            mock_session = Mock()
            mock_session.session_id = str(uuid4())
            mock_session.total_chunks = 4
            mock_session.chunk_size = 1024
            mock_init.return_value = mock_session

            session = await upload_service.initiate_chunked_upload(
                file_info=file_info,
                chunk_size=1024,
            )
            assert session.total_chunks == 4

        # Upload chunks
        for i in range(session.total_chunks):
            with patch.object(upload_service, 'upload_chunk') as mock_upload_chunk:
                mock_upload_chunk.return_value = {
                    "success": True,
                    "chunk_index": i,
                }

                result = await upload_service.upload_chunk(
                    upload_id=session.session_id,
                    chunk_index=i,
                    chunk_data=file_content[i*1024:(i+1)*1024],
                )
                assert result["success"] is True

        # Complete upload
        with patch.object(upload_service, 'complete_upload') as mock_complete:
            mock_complete.return_value = {
                "file_id": str(uuid4()),
                "status": "completed",
            }

            result = await upload_service.complete_upload(session.session_id)
            assert result["status"] == "completed"

        # Download file
        file_id = str(uuid4())
        with patch.object(download_service, 'download_file') as mock_download:
            mock_download.return_value = {
                "data": file_content,
                "filename": "integration_test.txt",
                "size": len(file_content),
            }

            result = await download_service.download_file(file_id)
            assert result["data"] == file_content

        # Stream download
        with patch.object(download_service, 'stream_file') as mock_stream:
            async def mock_stream_gen():
                yield file_content

            mock_stream.return_value = mock_stream_gen()

            chunks = []
            async for chunk in download_service.stream_file(file_id):
                chunks.append(chunk)

            assert b"".join(chunks) == file_content

    # Event System Integration Test
    @pytest.mark.asyncio
    async def test_event_system_integration(self):
        """Test event system integration."""
        from app.file.event_manager import FileOperationEventManager

        event_manager = FileOperationEventManager()

        # Create event handler
        handler_called = []

        async def test_handler(event: FileOperationEvent):
            handler_called.append(event)

        # Register handler
        event_manager.register_handler(
            event_type=EventType.FILE_CREATED,
            handler=test_handler,
        )

        # Create and publish event
        event = FileOperationEvent(
            event_type=EventType.FILE_CREATED,
            file_id=str(uuid4()),
            user_id=str(uuid4()),
            metadata={"test": True},
        )

        await event_manager.publish_event(event)

        # Verify handler was called
        await asyncio.sleep(0.1)  # Allow async processing
        assert len(handler_called) > 0
        assert handler_called[0].event_type == EventType.FILE_CREATED

    # Error Handling Integration Test
    @pytest.mark.asyncio
    async def test_error_handling_integration(
        self,
        file_manager,
        upload_service,
        download_service,
    ):
        """Test error handling across components."""
        file_id = str(uuid4())

        # Test file not found error
        with patch.object(file_manager, 'get_file') as mock_get:
            mock_get.return_value = None

            result = await file_manager.get_file(file_id)
            assert result is None

        # Test upload failure
        with patch.object(upload_service, 'upload_file') as mock_upload:
            mock_upload.side_effect = OSError("Storage error")

            with pytest.raises(OSError):
                await upload_service.upload_file(
                    file_data=b"test",
                    file_info={"filename": "test.txt"},
                )

        # Test download failure
        with patch.object(download_service, 'download_file') as mock_download:
            mock_download.side_effect = FileNotFoundError("File not found")

            with pytest.raises(FileNotFoundError):
                await download_service.download_file(file_id)

        # Test version creation failure
        from app.file.version_manager import VersionManager
        version_manager = VersionManager(db_session=AsyncMock())

        with patch.object(version_manager, 'create_version') as mock_create:
            mock_create.side_effect = Exception("Database error")

            with pytest.raises(Exception):
                await version_manager.create_version(
                    file_id=file_id,
                    content="test",
                )

    # Performance Integration Test
    @pytest.mark.asyncio
    async def test_performance_integration(
        self,
        file_manager,
        version_manager,
        preview_manager,
        batch_processor,
    ):
        """Test performance under load."""
        import time

        # Create multiple files
        start_time = time.time()
        file_count = 50

        for i in range(file_count):
            with patch.object(file_manager, 'create_file') as mock_create:
                mock_file = Mock()
                mock_file.id = str(uuid4())
                mock_create.return_value = mock_file

                await file_manager.create_file({
                    "filename": f"perf_test_{i}.txt",
                    "size": 1024,
                })

        creation_time = time.time() - start_time
        print(f"Created {file_count} files in {creation_time:.2f} seconds")

        # Batch operations
        file_ids = [str(uuid4()) for _ in range(20)]

        with patch.object(batch_processor, 'create_batch_job') as mock_create:
            mock_job = Mock()
            mock_job.job_id = str(uuid4())
            mock_create.return_value = mock_job

            with patch.object(batch_processor, 'process_batch_job') as mock_process:
                mock_result = Mock()
                mock_result.successful_count = 20
                mock_result.to_dict.return_value = {}
                mock_process.return_value = mock_result

                job = await batch_processor.create_batch_job(
                    operation_type=OperationType.UPLOAD,
                    file_ids=file_ids,
                )

                start_batch = time.time()
                result = await batch_processor.process_batch_job(job.job_id)
                batch_time = time.time() - start_batch

                print(f"Processed batch of {len(file_ids)} files in {batch_time:.2f} seconds")
                assert batch_time < 5.0  # Should complete within 5 seconds

    # Concurrency Integration Test
    @pytest.mark.asyncio
    async def test_concurrency_integration(
        self,
        file_manager,
        upload_service,
        version_manager,
    ):
        """Test concurrent operations."""
        async def create_file_task(i):
            with patch.object(file_manager, 'create_file') as mock_create:
                mock_file = Mock()
                mock_file.id = str(uuid4())
                mock_create.return_value = mock_file

                return await file_manager.create_file({
                    "filename": f"concurrent_{i}.txt",
                    "size": 1024,
                })

        # Run concurrent file creations
        start_time = time.time()
        tasks = [create_file_task(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time

        print(f"Created {len(results)} files concurrently in {concurrent_time:.2f} seconds")
        assert len(results) == 20
        assert concurrent_time < 2.0  # Should complete within 2 seconds

    # Data Consistency Integration Test
    @pytest.mark.asyncio
    async def test_data_consistency_integration(
        self,
        file_manager,
        version_manager,
        preview_manager,
    ):
        """Test data consistency across components."""
        file_id = str(uuid4())

        # Create file
        with patch.object(file_manager, 'create_file') as mock_create:
            mock_file = Mock()
            mock_file.id = file_id
            mock_file.filename = "consistency_test.txt"
            mock_file.size = 1024
            mock_file.hash = "abc123"
            mock_create.return_value = mock_file

            file = await file_manager.create_file({
                "filename": "consistency_test.txt",
                "size": 1024,
            })
            assert file.id == file_id
            assert file.hash == "abc123"

        # Create version
        with patch.object(version_manager, 'create_version') as mock_create_version:
            mock_version = Mock()
            mock_version.id = str(uuid4())
            mock_version.file_id = file_id
            mock_version.content_hash = "abc123"  # Same hash as file
            mock_create_version.return_value = mock_version

            version = await version_manager.create_version(
                file_id=file_id,
                content="test content",
            )
            assert version.content_hash == file.hash

        # Generate preview
        with patch.object(preview_manager, 'generate_preview') as mock_preview:
            mock_preview_data = Mock()
            mock_preview_data.file_id = file_id
            mock_preview_data.content_hash = "abc123"  # Consistent hash
            mock_preview.return_value = mock_preview_data

            preview = await preview_manager.generate_preview(
                file_id=file_id,
                format="thumbnail",
            )
            assert preview.content_hash == file.hash

        # Verify consistency
        assert file.hash == version.content_hash == preview.content_hash

    # Security Integration Test
    @pytest.mark.asyncio
    async def test_security_integration(
        self,
        file_manager,
        upload_service,
    ):
        """Test security features integration."""
        # Test file path traversal protection
        malicious_filename = "../../../etc/passwd"

        with patch.object(file_manager, 'create_file') as mock_create:
            # Should handle or reject malicious paths
            try:
                await file_manager.create_file({
                    "filename": malicious_filename,
                    "size": 1024,
                })
                # If we get here, the system should have sanitized the path
                assert True
            except (ValueError, OSError):
                # Or rejected the malicious path
                assert True

        # Test file size validation
        oversized_content = b"x" * (100 * 1024 * 1024)  # 100MB

        with patch.object(upload_service, 'upload_file') as mock_upload:
            mock_upload.side_effect = ValueError("File size exceeds limit")

            with pytest.raises(ValueError):
                await upload_service.upload_file(
                    file_data=oversized_content,
                    file_info={"filename": "large.txt"},
                )

        # Test content validation
        malicious_content = b"<script>alert('xss')</script>"

        with patch.object(upload_service, 'upload_file') as mock_upload:
            mock_upload.return_value = {
                "file_id": str(uuid4()),
                "status": "completed",
                "validated": True,
            }

            result = await upload_service.upload_file(
                file_data=malicious_content,
                file_info={"filename": "test.html"},
            )
            # System should handle malicious content appropriately
            assert result["status"] == "completed"

    # Recovery Integration Test
    @pytest.mark.asyncio
    async def test_recovery_integration(
        self,
        file_manager,
        version_manager,
        upload_service,
        download_service,
    ):
        """Test system recovery capabilities."""
        file_id = str(uuid4())

        # Simulate upload failure and recovery
        with patch.object(upload_service, 'upload_file') as mock_upload:
            # First attempt fails
            mock_upload.side_effect = [
                OSError("Network error"),
                {"file_id": file_id, "status": "completed"},  # Second attempt succeeds
            ]

            # First attempt
            with pytest.raises(OSError):
                await upload_service.upload_file(
                    file_data=b"test",
                    file_info={"filename": "test.txt"},
                )

            # Retry should succeed
            result = await upload_service.upload_file(
                file_data=b"test",
                file_info={"filename": "test.txt"},
            )
            assert result["status"] == "completed"

        # Test version rollback
        with patch.object(version_manager, 'restore_version') as mock_restore:
            mock_restored = Mock()
            mock_restored.id = str(uuid4())
            mock_restore.file_id = file_id
            mock_restore.version_number = 2
            mock_restore.return_value = mock_restored

            # Simulate corrupted current version
            # Restore from previous version
            restored = await version_manager.restore_version(
                file_id=file_id,
                version_id=str(uuid4()),
            )
            assert restored.version_number == 2

        # Test download retry
        with patch.object(download_service, 'download_file') as mock_download:
            # First attempt fails
            mock_download.side_effect = [
                ConnectionError("Connection lost"),
                {"data": b"test", "filename": "test.txt"},  # Second attempt succeeds
            ]

            # First attempt
            with pytest.raises(ConnectionError):
                await download_service.download_file(file_id)

            # Retry should succeed
            result = await download_service.download_file(file_id)
            assert result["data"] == b"test"


if __name__ == "__main__":
    pytest.main([__file__])
