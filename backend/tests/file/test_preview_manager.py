"""Tests for PreviewManager.

This module contains comprehensive unit tests for the PreviewManager class including
preview generation, format conversion, and thumbnail creation tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import base64

# Import manager and related classes
from app.file.preview_manager import (
    PreviewManager,
    PreviewType,
    ImageFormat,
    DocumentFormat,
    PreviewCache,
    PreviewMetadata,
    PreviewResult,
)
from app.file.services.conversion_service import (
    ConversionService,
    ConversionType,
    ConversionQuality,
    ConversionRule,
    ConversionResult,
)


class TestPreviewManager:
    """Test suite for PreviewManager."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def preview_manager(self, db_session):
        """Create PreviewManager instance with mocked database."""
        return PreviewManager(db_session)

    @pytest.fixture
    def sample_file_id(self):
        """Generate sample file ID."""
        return uuid4()

    @pytest.fixture
    def sample_image_file(self, sample_file_id):
        """Create sample image file."""
        file_mock = Mock()
        file_mock.id = sample_file_id
        file_mock.name = "test_image.jpg"
        file_mock.mime_type = "image/jpeg"
        return file_mock

    @pytest.fixture
    def sample_video_file(self, sample_file_id):
        """Create sample video file."""
        file_mock = Mock()
        file_mock.id = sample_file_id
        file_mock.name = "test_video.mp4"
        file_mock.mime_type = "video/mp4"
        return file_mock

    @pytest.fixture
    def sample_document_file(self, sample_file_id):
        """Create sample document file."""
        file_mock = Mock()
        file_mock.id = sample_file_id
        file_mock.name = "test_document.pdf"
        file_mock.mime_type = "application/pdf"
        return file_mock

    # Test preview generation

    @pytest.mark.asyncio
    async def test_generate_image_preview(
        self,
        preview_manager,
        sample_file_id,
        sample_image_file,
    ):
        """Test generating image preview."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_image_file):
            result = await preview_manager.generate_preview(sample_file_id)

            assert result is not None
            assert isinstance(result, PreviewResult)
            assert result.success is True
            assert result.preview_type == PreviewType.IMAGE
            assert result.preview_data is not None

    @pytest.mark.asyncio
    async def test_generate_video_preview(
        self,
        preview_manager,
        sample_file_id,
        sample_video_file,
    ):
        """Test generating video preview."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_video_file):
            result = await preview_manager.generate_preview(sample_file_id)

            assert result is not None
            assert isinstance(result, PreviewResult)
            assert result.success is True
            assert result.preview_type == PreviewType.VIDEO
            assert result.metadata is not None
            assert result.metadata.duration is not None

    @pytest.mark.asyncio
    async def test_generate_document_preview(
        self,
        preview_manager,
        sample_file_id,
        sample_document_file,
    ):
        """Test generating document preview."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_document_file):
            result = await preview_manager.generate_preview(sample_file_id)

            assert result is not None
            assert isinstance(result, PreviewResult)
            assert result.success is True
            assert result.preview_type == PreviewType.DOCUMENT
            assert result.metadata is not None
            assert result.metadata.pages is not None

    @pytest.mark.asyncio
    async def test_generate_preview_file_not_found(self, preview_manager, sample_file_id):
        """Test preview generation for non-existent file."""
        # Mock file info retrieval to return None
        with patch.object(preview_manager, '_get_file_info', return_value=None):
            result = await preview_manager.generate_preview(sample_file_id)

            assert result is not None
            assert result.success is False
            assert result.error_message == "File not found"

    @pytest.mark.asyncio
    async def test_generate_preview_with_custom_type(
        self,
        preview_manager,
        sample_file_id,
        sample_image_file,
    ):
        """Test preview generation with custom type."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_image_file):
            result = await preview_manager.generate_preview(
                sample_file_id,
                preview_type=PreviewType.IMAGE,
                include_thumbnail=True,
                max_size=(800, 600),
                quality=90,
            )

            assert result is not None
            assert result.success is True
            assert result.preview_type == PreviewType.IMAGE

    # Test thumbnail generation

    @pytest.mark.asyncio
    async def test_generate_thumbnail(
        self,
        preview_manager,
        sample_file_id,
        sample_image_file,
    ):
        """Test thumbnail generation."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_image_file):
            thumbnail = await preview_manager.generate_thumbnail(
                sample_file_id,
                size=(128, 128),
                format="png",
            )

            assert thumbnail is not None
            assert isinstance(thumbnail, bytes)
            assert len(thumbnail) > 0

    @pytest.mark.asyncio
    async def test_generate_thumbnail_video(
        self,
        preview_manager,
        sample_file_id,
        sample_video_file,
    ):
        """Test video thumbnail generation."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_video_file):
            thumbnail = await preview_manager.generate_thumbnail(
                sample_file_id,
                size=(128, 128),
                format="png",
            )

            assert thumbnail is not None
            assert isinstance(thumbnail, bytes)

    @pytest.mark.asyncio
    async def test_generate_thumbnail_document(
        self,
        preview_manager,
        sample_file_id,
        sample_document_file,
    ):
        """Test document thumbnail generation."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_document_file):
            thumbnail = await preview_manager.generate_thumbnail(
                sample_file_id,
                size=(128, 128),
                format="png",
            )

            assert thumbnail is not None
            assert isinstance(thumbnail, bytes)

    @pytest.mark.asyncio
    async def test_generate_thumbnail_file_not_found(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test thumbnail generation for non-existent file."""
        # Mock file info retrieval to return None
        with patch.object(preview_manager, '_get_file_info', return_value=None):
            thumbnail = await preview_manager.generate_thumbnail(sample_file_id)

            assert thumbnail is None

    # Test text extraction

    @pytest.mark.asyncio
    async def test_extract_text_from_code_file(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test text extraction from code file."""
        # Create code file
        code_file = Mock()
        code_file.id = sample_file_id
        code_file.name = "test.py"

        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=code_file):
            text = await preview_manager.extract_text(sample_file_id)

            assert text is not None
            assert isinstance(text, str)
            assert len(text) > 0

    @pytest.mark.asyncio
    async def test_extract_text_from_text_file(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test text extraction from text file."""
        # Create text file
        text_file = Mock()
        text_file.id = sample_file_id
        text_file.name = "test.txt"

        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=code_file):
            text = await preview_manager.extract_text(sample_file_id)

            assert text is not None
            assert isinstance(text, str)

    @pytest.mark.asyncio
    async def test_extract_text_unsupported_format(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test text extraction from unsupported format."""
        # Create unsupported file
        unsupported_file = Mock()
        unsupported_file.id = sample_file_id
        unsupported_file.name = "test.xyz"

        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=unsupported_file):
            text = await preview_manager.extract_text(sample_file_id)

            assert text is None

    @pytest.mark.asyncio
    async def test_extract_text_file_not_found(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test text extraction for non-existent file."""
        # Mock file info retrieval to return None
        with patch.object(preview_manager, '_get_file_info', return_value=None):
            text = await preview_manager.extract_text(sample_file_id)

            assert text is None

    # Test metadata extraction

    @pytest.mark.asyncio
    async def test_get_preview_metadata_image(
        self,
        preview_manager,
        sample_file_id,
        sample_image_file,
    ):
        """Test getting image preview metadata."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_image_file):
            metadata = await preview_manager.get_preview_metadata(sample_file_id)

            assert metadata is not None
            assert isinstance(metadata, PreviewMetadata)
            assert metadata.file_type == PreviewType.IMAGE
            assert metadata.dimensions is not None

    @pytest.mark.asyncio
    async def test_get_preview_metadata_video(
        self,
        preview_manager,
        sample_file_id,
        sample_video_file,
    ):
        """Test getting video preview metadata."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_video_file):
            metadata = await preview_manager.get_preview_metadata(sample_file_id)

            assert metadata is not None
            assert isinstance(metadata, PreviewMetadata)
            assert metadata.file_type == PreviewType.VIDEO
            assert metadata.duration is not None

    @pytest.mark.asyncio
    async def test_get_preview_metadata_audio(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test getting audio preview metadata."""
        # Create audio file
        audio_file = Mock()
        audio_file.id = sample_file_id
        audio_file.name = "test.mp3"
        audio_file.mime_type = "audio/mpeg"

        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=audio_file):
            metadata = await preview_manager.get_preview_metadata(sample_file_id)

            assert metadata is not None
            assert isinstance(metadata, PreviewMetadata)
            assert metadata.file_type == PreviewType.AUDIO
            assert metadata.duration is not None

    @pytest.mark.asyncio
    async def test_get_preview_metadata_document(
        self,
        preview_manager,
        sample_file_id,
        sample_document_file,
    ):
        """Test getting document preview metadata."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_document_file):
            metadata = await preview_manager.get_preview_metadata(sample_file_id)

            assert metadata is not None
            assert isinstance(metadata, PreviewMetadata)
            assert metadata.file_type == PreviewType.DOCUMENT
            assert metadata.pages is not None

    @pytest.mark.asyncio
    async def test_get_preview_metadata_file_not_found(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test getting metadata for non-existent file."""
        # Mock file info retrieval to return None
        with patch.object(preview_manager, '_get_file_info', return_value=None):
            metadata = await preview_manager.get_preview_metadata(sample_file_id)

            assert metadata is None

    # Test format detection

    @pytest.mark.asyncio
    async def test_detect_preview_type_image(self, preview_manager):
        """Test preview type detection for image files."""
        # Create image file
        image_file = Mock()
        image_file.name = "test.jpg"
        image_file.mime_type = "image/jpeg"

        preview_type = preview_manager._detect_preview_type(image_file)
        assert preview_type == PreviewType.IMAGE

    @pytest.mark.asyncio
    async def test_detect_preview_type_video(self, preview_manager):
        """Test preview type detection for video files."""
        # Create video file
        video_file = Mock()
        video_file.name = "test.mp4"
        video_file.mime_type = "video/mp4"

        preview_type = preview_manager._detect_preview_type(video_file)
        assert preview_type == PreviewType.VIDEO

    @pytest.mark.asyncio
    async def test_detect_preview_type_document(self, preview_manager):
        """Test preview type detection for document files."""
        # Create document file
        document_file = Mock()
        document_file.name = "test.pdf"
        document_file.mime_type = "application/pdf"

        preview_type = preview_manager._detect_preview_type(document_file)
        assert preview_type == PreviewType.DOCUMENT

    @pytest.mark.asyncio
    async def test_detect_preview_type_code(self, preview_manager):
        """Test preview type detection for code files."""
        # Create code file
        code_file = Mock()
        code_file.name = "test.py"
        code_file.mime_type = "text/x-python"

        preview_type = preview_manager._detect_preview_type(code_file)
        assert preview_type == PreviewType.CODE

    @pytest.mark.asyncio
    async def test_detect_preview_type_unknown(self, preview_manager):
        """Test preview type detection for unknown files."""
        # Create unknown file
        unknown_file = Mock()
        unknown_file.name = "test.xyz"
        unknown_file.mime_type = "application/x-unknown"

        preview_type = preview_manager._detect_preview_type(unknown_file)
        assert preview_type == PreviewType.UNKNOWN

    # Test cache functionality

    @pytest.mark.asyncio
    async def test_cache_preview(self, preview_manager, sample_file_id):
        """Test preview caching."""
        # Create cache entry
        cache_entry = PreviewCache(
            file_id=str(sample_file_id),
            preview_type=PreviewType.IMAGE,
            preview_data=b"test image data",
            thumbnail_data=b"test thumbnail data",
        )

        cache_key = "test_cache_key"
        preview_manager._add_to_cache(cache_key, cache_entry)

        # Verify cache entry exists
        cached_entry = preview_manager._get_from_cache(cache_key)
        assert cached_entry is not None
        assert cached_entry.preview_type == PreviewType.IMAGE

    @pytest.mark.asyncio
    async def test_cache_expiration(self, preview_manager, sample_file_id):
        """Test cache expiration."""
        # Create expired cache entry
        cache_entry = PreviewCache(
            file_id=str(sample_file_id),
            preview_type=PreviewType.IMAGE,
            preview_data=b"test image data",
            expires_at=datetime.utcnow() - timedelta(hours=1),  # Expired
        )

        cache_key = "test_expired_cache_key"
        preview_manager._add_to_cache(cache_key, cache_entry)

        # Verify expired entry is removed
        cached_entry = preview_manager._get_from_cache(cache_key)
        assert cached_entry is None

    @pytest.mark.asyncio
    async def test_clear_cache(self, preview_manager, sample_file_id):
        """Test cache clearing."""
        # Add some cache entries
        for i in range(5):
            cache_entry = PreviewCache(
                file_id=str(sample_file_id),
                preview_type=PreviewType.IMAGE,
                preview_data=f"test data {i}".encode(),
            )
            cache_key = f"test_cache_key_{i}"
            preview_manager._add_to_cache(cache_key, cache_entry)

        # Clear all cache
        cleared_count = await preview_manager.clear_cache()

        assert cleared_count == 5
        assert len(preview_manager.preview_cache) == 0

    @pytest.mark.asyncio
    async def test_clear_expired_cache(self, preview_manager, sample_file_id):
        """Test clearing expired cache entries."""
        # Add some cache entries
        for i in range(5):
            if i < 3:
                # Not expired
                cache_entry = PreviewCache(
                    file_id=str(sample_file_id),
                    preview_type=PreviewType.IMAGE,
                    preview_data=f"test data {i}".encode(),
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                )
            else:
                # Expired
                cache_entry = PreviewCache(
                    file_id=str(sample_file_id),
                    preview_type=PreviewType.IMAGE,
                    preview_data=f"test data {i}".encode(),
                    expires_at=datetime.utcnow() - timedelta(hours=1),
                )

            cache_key = f"test_cache_key_{i}"
            preview_manager._add_to_cache(cache_key, cache_entry)

        # Clear only expired cache
        cleared_count = await preview_manager.clear_cache(older_than_hours=30)

        assert cleared_count == 2  # Only the 2 expired entries
        assert len(preview_manager.preview_cache) == 3  # 3 entries remain

    def test_get_cache_stats(self, preview_manager, sample_file_id):
        """Test getting cache statistics."""
        # Add some cache entries
        for i in range(3):
            cache_entry = PreviewCache(
                file_id=str(sample_file_id),
                preview_type=PreviewType.IMAGE,
                preview_data=b"test image data",
                thumbnail_data=b"test thumbnail data",
            )
            cache_key = f"test_cache_key_{i}"
            preview_manager._add_to_cache(cache_key, cache_entry)

        stats = preview_manager.get_cache_stats()

        assert stats is not None
        assert isinstance(stats, dict)
        assert stats["total_entries"] == 3
        assert stats["total_size_bytes"] > 0
        assert "type_distribution" in stats
        assert stats["type_distribution"]["image"] == 3

    # Test error handling

    @pytest.mark.asyncio
    async def test_generate_preview_error_handling(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test error handling during preview generation."""
        # Mock file info retrieval to raise exception
        with patch.object(preview_manager, '_get_file_info', side_effect=Exception("Test error")):
            result = await preview_manager.generate_preview(sample_file_id)

            assert result is not None
            assert result.success is False
            assert "Test error" in result.error_message

    @pytest.mark.asyncio
    async def test_extract_text_error_handling(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test error handling during text extraction."""
        # Mock file info retrieval to raise exception
        with patch.object(preview_manager, '_get_file_info', side_effect=Exception("Test error")):
            text = await preview_manager.extract_text(sample_file_id)

            assert text is None

    @pytest.mark.asyncio
    async def test_get_metadata_error_handling(
        self,
        preview_manager,
        sample_file_id,
    ):
        """Test error handling during metadata extraction."""
        # Mock file info retrieval to raise exception
        with patch.object(preview_manager, '_get_file_info', side_effect=Exception("Test error")):
            metadata = await preview_manager.get_preview_metadata(sample_file_id)

            assert metadata is None

    # Test preview quality settings

    @pytest.mark.asyncio
    async def test_generate_preview_with_quality_settings(
        self,
        preview_manager,
        sample_file_id,
        sample_image_file,
    ):
        """Test preview generation with different quality settings."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_image_file):
            # Test with high quality
            result = await preview_manager.generate_preview(
                sample_file_id,
                quality=95,
                max_size=(1920, 1080),
            )

            assert result is not None
            assert result.success is True

    @pytest.mark.asyncio
    async def test_generate_preview_with_thumbnail(
        self,
        preview_manager,
        sample_file_id,
        sample_image_file,
    ):
        """Test preview generation with thumbnail."""
        # Mock file info retrieval
        with patch.object(preview_manager, '_get_file_info', return_value=sample_image_file):
            result = await preview_manager.generate_preview(
                sample_file_id,
                include_thumbnail=True,
            )

            assert result is not None
            assert result.success is True
            # Note: In mock implementation, thumbnail_data might be None

    # Test supported formats

    def test_supported_image_formats(self, preview_manager):
        """Test supported image formats."""
        assert ".jpg" in preview_manager.IMAGE_EXTENSIONS
        assert ".png" in preview_manager.IMAGE_EXTENSIONS
        assert ".gif" in preview_manager.IMAGE_EXTENSIONS
        assert ".webp" in preview_manager.IMAGE_EXTENSIONS
        assert ".svg" in preview_manager.IMAGE_EXTENSIONS

    def test_supported_video_formats(self, preview_manager):
        """Test supported video formats."""
        assert ".mp4" in preview_manager.VIDEO_EXTENSIONS
        assert ".avi" in preview_manager.VIDEO_EXTENSIONS
        assert ".mov" in preview_manager.VIDEO_EXTENSIONS
        assert ".webm" in preview_manager.VIDEO_EXTENSIONS

    def test_supported_audio_formats(self, preview_manager):
        """Test supported audio formats."""
        assert ".mp3" in preview_manager.AUDIO_EXTENSIONS
        assert ".wav" in preview_manager.AUDIO_EXTENSIONS
        assert ".flac" in preview_manager.AUDIO_EXTENSIONS
        assert ".aac" in preview_manager.AUDIO_EXTENSIONS

    def test_supported_document_formats(self, preview_manager):
        """Test supported document formats."""
        assert ".pdf" in preview_manager.DOCUMENT_EXTENSIONS
        assert ".doc" in preview_manager.DOCUMENT_EXTENSIONS
        assert ".docx" in preview_manager.DOCUMENT_EXTENSIONS
        assert ".xls" in preview_manager.DOCUMENT_EXTENSIONS

    def test_supported_code_formats(self, preview_manager):
        """Test supported code formats."""
        assert ".py" in preview_manager.CODE_EXTENSIONS
        assert ".js" in preview_manager.CODE_EXTENSIONS
        assert ".java" in preview_manager.CODE_EXTENSIONS
        assert ".cpp" in preview_manager.CODE_EXTENSIONS
        assert ".html" in preview_manager.CODE_EXTENSIONS

    # Test initialization

    def test_preview_manager_initialization(self, db_session):
        """Test PreviewManager initialization."""
        manager = PreviewManager(db_session)

        assert manager.db == db_session
        assert len(manager.preview_cache) == 0
        assert manager.supported_formats is not None
        assert len(manager.supported_formats) > 0

    def test_preview_manager_formats_initialization(self, db_session):
        """Test format initialization."""
        manager = PreviewManager(db_session)

        # Verify formats are initialized
        assert isinstance(manager.supported_formats, dict)

        # Check some common formats
        assert ".jpg" in manager.supported_formats
        assert ".png" in manager.supported_formats
        assert ".pdf" in manager.supported_formats
        assert ".py" in manager.supported_formats


class TestConversionService:
    """Test suite for ConversionService."""

    @pytest.fixture
    def conversion_service(self):
        """Create ConversionService instance."""
        return ConversionService()

    @pytest.fixture
    def sample_file_id(self):
        """Generate sample file ID."""
        return uuid4()

    # Test format detection

    @pytest.mark.asyncio
    async def test_detect_format_by_filename(self, conversion_service):
        """Test format detection by filename."""
        result = await conversion_service.detect_format(
            filename="test.jpg",
            mime_type="image/jpeg"
        )

        assert result is not None
        assert result["extension"] == "jpg"
        assert result["format_category"] == "image"
        assert result["confidence"] > 0

    @pytest.mark.asyncio
    async def test_detect_format_by_mime_type(self, conversion_service):
        """Test format detection by MIME type."""
        result = await conversion_service.detect_format(
            mime_type="application/pdf"
        )

        assert result is not None
        assert result["format_category"] == "document"

    @pytest.mark.asyncio
    async def test_detect_format_by_content(self, conversion_service):
        """Test format detection by file content."""
        # PNG file signature
        png_data = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100

        result = await conversion_service.detect_format(
            file_data=png_data,
            filename="test.png"
        )

        assert result is not None
        assert result["extension"] == "png"
        assert result["format_category"] == "image"

    @pytest.mark.asyncio
    async def test_detect_format_unknown(self, conversion_service):
        """Test format detection for unknown file."""
        result = await conversion_service.detect_format(
            filename="test.xyz"
        )

        assert result is not None
        assert result["format_category"] == "unknown"

    # Test file conversion

    @pytest.mark.asyncio
    async def test_convert_image_to_image(self, conversion_service, sample_file_id):
        """Test image to image conversion."""
        image_data = b"fake image data"

        result = await conversion_service.convert_file(
            file_id=sample_file_id,
            file_data=image_data,
            source_format="jpg",
            target_format="png",
            quality=ConversionQuality.MEDIUM,
        )

        assert result is not None
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.source_format == "jpg"
        assert result.target_format == "png"
        assert result.converted_data is not None

    @pytest.mark.asyncio
    async def test_convert_image_to_pdf(self, conversion_service, sample_file_id):
        """Test image to PDF conversion."""
        image_data = b"fake image data"

        result = await conversion_service.convert_file(
            file_id=sample_file_id,
            file_data=image_data,
            source_format="jpg",
            target_format="pdf",
            quality=ConversionQuality.HIGH,
        )

        assert result is not None
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.target_format == "pdf"

    @pytest.mark.asyncio
    async def test_convert_document_to_pdf(self, conversion_service, sample_file_id):
        """Test document to PDF conversion."""
        document_data = b"fake document data"

        result = await conversion_service.convert_file(
            file_id=sample_file_id,
            file_data=document_data,
            source_format="docx",
            target_format="pdf",
            quality=ConversionQuality.HIGH,
        )

        assert result is not None
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.target_format == "pdf"

    @pytest.mark.asyncio
    async def test_convert_code_to_text(self, conversion_service, sample_file_id):
        """Test code file to text conversion."""
        code_data = b"print('hello world')"

        result = await conversion_service.convert_file(
            file_id=sample_file_id,
            file_data=code_data,
            source_format="py",
            target_format="txt",
            quality=ConversionQuality.MEDIUM,
        )

        assert result is not None
        assert isinstance(result, ConversionResult)
        assert result.success is True
        assert result.target_format == "txt"

    @pytest.mark.asyncio
    async def test_convert_unsupported_format(self, conversion_service, sample_file_id):
        """Test conversion of unsupported format."""
        data = b"some data"

        result = await conversion_service.convert_file(
            file_id=sample_file_id,
            file_data=data,
            source_format="xyz",
            target_format="abc",
            quality=ConversionQuality.MEDIUM,
        )

        assert result is not None
        assert isinstance(result, ConversionResult)
        assert result.success is False
        assert "not supported" in result.error_message

    # Test conversion rules

    def test_get_conversion_rule(self, conversion_service):
        """Test getting conversion rule."""
        rule = conversion_service.get_conversion_rule("jpg", "png")

        assert rule is not None
        assert isinstance(rule, ConversionRule)
        assert rule.source_extension == "jpg"
        assert rule.target_extension == "png"

    def test_get_conversion_rule_not_found(self, conversion_service):
        """Test getting non-existent conversion rule."""
        rule = conversion_service.get_conversion_rule("xyz", "abc")

        assert rule is None

    def test_get_supported_conversions(self, conversion_service):
        """Test getting supported conversions."""
        conversions = conversion_service.get_supported_conversions("jpg")

        assert isinstance(conversions, list)
        assert len(conversions) > 0
        assert all("target_format" in conv for conv in conversions)

    def test_get_supported_conversions_not_found(self, conversion_service):
        """Test getting conversions for unsupported format."""
        conversions = conversion_service.get_supported_conversions("xyz")

        assert isinstance(conversions, list)
        assert len(conversions) == 0

    # Test statistics

    def test_get_conversion_statistics_empty(self, conversion_service):
        """Test getting statistics with no conversions."""
        stats = conversion_service.get_conversion_statistics()

        assert stats is not None
        assert isinstance(stats, dict)
        assert stats["total_conversions"] == 0
        assert stats["success_rate_percent"] == 0

    @pytest.mark.asyncio
    async def test_get_conversion_statistics_after_conversions(
        self,
        conversion_service,
        sample_file_id,
    ):
        """Test getting statistics after some conversions."""
        # Perform some conversions
        for i in range(3):
            result = await conversion_service.convert_file(
                file_id=sample_file_id,
                file_data=b"test data",
                source_format="jpg",
                target_format="png",
                quality=ConversionQuality.MEDIUM,
            )

        stats = conversion_service.get_conversion_statistics()

        assert stats is not None
        assert stats["total_conversions"] == 3
        assert stats["successful_conversions"] == 3
        assert stats["failed_conversions"] == 0

    # Test cache

    def test_clear_cache(self, conversion_service):
        """Test clearing conversion cache."""
        # Add some cache entries (mock)
        conversion_service.conversion_cache["key1"] = "value1"
        conversion_service.conversion_cache["key2"] = "value2"

        conversion_service.clear_cache()

        assert len(conversion_service.conversion_cache) == 0

    # Test error handling

    @pytest.mark.asyncio
    async def test_convert_file_error_handling(
        self,
        conversion_service,
        sample_file_id,
    ):
        """Test error handling during conversion."""
        # Mock conversion to raise exception
        with patch.object(conversion_service, '_convert_image_to_image', side_effect=Exception("Test error")):
            result = await conversion_service.convert_file(
                file_id=sample_file_id,
                file_data=b"test data",
                source_format="jpg",
                target_format="png",
            )

            assert result is not None
            assert result.success is False
            assert "Test error" in result.error_message

    # Test initialization

    def test_conversion_service_initialization(self):
        """Test ConversionService initialization."""
        service = ConversionService()

        assert service.conversion_rules is not None
        assert service.conversion_cache == {}
        assert service.stats is not None
        assert len(service.conversion_rules) > 0

    def test_conversion_rules_initialization(self):
        """Test conversion rules initialization."""
        service = ConversionService()

        # Verify some common rules exist
        assert "jpg" in service.conversion_rules
        assert "png" in service.conversion_rules
        assert "pdf" in service.conversion_rules

        # Check specific conversion
        jpg_to_png = service.conversion_rules.get("jpg", {}).get("png")
        assert jpg_to_png is not None
        assert jpg_to_png.conversion_type == ConversionType.IMAGE_TO_IMAGE
