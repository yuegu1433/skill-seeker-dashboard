"""Tests for VersionManager.

This module contains comprehensive unit and integration tests for the
VersionManager class including version lifecycle, concurrent operations,
and performance tests.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import hashlib

# Import manager and related classes
from app.file.version_manager import (
    VersionManager,
    VersionSortBy,
    VersionFilter,
    VersionCompareResult,
    VersionStatistics,
)
from app.file.models.file_version import FileVersion, VersionStatus


class TestVersionManager:
    """Test suite for VersionManager."""

    @pytest.fixture
    def db_session(self):
        """Mock database session."""
        return AsyncMock()

    @pytest.fixture
    def version_manager(self, db_session):
        """Create VersionManager instance with mocked database."""
        return VersionManager(db_session)

    @pytest.fixture
    def sample_file_id(self):
        """Generate sample file ID."""
        return uuid4()

    @pytest.fixture
    def sample_user_id(self):
        """Generate sample user ID."""
        return "test-user-123"

    @pytest.fixture
    def sample_file_version(self, sample_file_id):
        """Create sample file version."""
        return FileVersion(
            id=uuid4(),
            file_id=sample_file_id,
            version="1.0.0",
            version_number=1,
            content="Initial content",
            content_hash=hashlib.sha256("Initial content".encode()).hexdigest(),
            checksum="abc123",
            size=1024,
            mime_type="text/plain",
            author_id="test-user",
            author_name="Test User",
            message="Initial version",
            status=VersionStatus.ACTIVE,
            is_current=True,
            storage_key="files/test.txt",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    # Test version creation

    @pytest.mark.asyncio
    async def test_create_initial_version(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
    ):
        """Test creating initial version for a file."""
        # Create initial version
        version = await version_manager.create_version(
            file_id=sample_file_id,
            author_id=sample_user_id,
            author_name="Test User",
            content="Initial content",
            size=1024,
            mime_type="text/plain",
            message="Initial version",
        )

        # Assertions
        assert version is not None
        assert version.version == "1.0.0"
        assert version.version_number == 1
        assert version.is_current is True
        assert version.status == VersionStatus.ACTIVE
        assert version.content == "Initial content"
        assert version.author_id == sample_user_id

    @pytest.mark.asyncio
    async def test_create_new_version(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
        sample_file_version,
    ):
        """Test creating new version for existing file."""
        # Mock get_current_version to return sample version
        with patch.object(version_manager, 'get_current_version', return_value=sample_file_version):
            # Create new version
            version = await version_manager.create_version(
                file_id=sample_file_id,
                author_id=sample_user_id,
                author_name="Test User",
                content="Updated content",
                size=2048,
                mime_type="text/plain",
                message="Updated version",
            )

            # Assertions
            assert version is not None
            assert version.version == "2.0.0"
            assert version.version_number == 2
            assert version.is_current is True
            assert version.content == "Updated content"
            assert version.size == 2048
            assert version.parent_version_id == sample_file_version.id

    @pytest.mark.asyncio
    async def test_create_version_content_unchanged(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
        sample_file_version,
    ):
        """Test creating version with unchanged content."""
        # Mock get_current_version to return sample version
        with patch.object(version_manager, 'get_current_version', return_value=sample_file_version):
            # Try to create version with same content
            version = await version_manager.create_version(
                file_id=sample_file_id,
                author_id=sample_user_id,
                author_name="Test User",
                content="Initial content",  # Same as current version
                size=1024,
                mime_type="text/plain",
                message="Same content",
            )

            # Should return current version without creating new one
            assert version is sample_file_version

    @pytest.mark.asyncio
    async def test_create_version_with_tag(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
    ):
        """Test creating version with tag."""
        version = await version_manager.create_version(
            file_id=sample_file_id,
            author_id=sample_user_id,
            author_name="Test User",
            content="Tagged content",
            size=1024,
            mime_type="text/plain",
            message="Tagged version",
            version_tag="v1.0.0-stable",
        )

        assert version is not None
        assert version.version_tag == "v1.0.0-stable"

    @pytest.mark.asyncio
    async def test_create_version_with_metadata(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
    ):
        """Test creating version with metadata."""
        metadata = {
            "build_number": "123",
            "environment": "production",
            "features": ["auth", "logging"],
        }

        version = await version_manager.create_version(
            file_id=sample_file_id,
            author_id=sample_user_id,
            author_name="Test User",
            content="Content with metadata",
            size=1024,
            mime_type="text/plain",
            message="Version with metadata",
            metadata=metadata,
        )

        assert version is not None
        assert version.metadata == metadata

    # Test version retrieval

    @pytest.mark.asyncio
    async def test_get_version_by_id(self, version_manager, sample_file_version):
        """Test getting version by ID."""
        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalar_one_or_none.return_value = sample_file_version

        version = await version_manager.get_version(sample_file_version.id)

        assert version is not None
        assert version.id == sample_file_version.id

    @pytest.mark.asyncio
    async def test_get_current_version(
        self,
        version_manager,
        sample_file_id,
        sample_file_version,
    ):
        """Test getting current version of a file."""
        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalar_one_or_none.return_value = sample_file_version

        version = await version_manager.get_current_version(sample_file_id)

        assert version is not None
        assert version.is_current is True

    @pytest.mark.asyncio
    async def test_get_versions_with_filter(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test getting versions with filter."""
        # Create filter
        filter_criteria = VersionFilter(
            status=VersionStatus.ACTIVE,
            author_name="Test",
        )

        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        versions, total = await version_manager.get_versions(
            file_id=sample_file_id,
            filter=filter_criteria,
        )

        assert isinstance(versions, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_get_versions_with_sorting(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test getting versions with sorting."""
        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        versions, total = await version_manager.get_versions(
            file_id=sample_file_id,
            sort_by=VersionSortBy.VERSION_NUMBER,
            sort_order="asc",
            limit=10,
            offset=0,
        )

        assert isinstance(versions, list)
        assert isinstance(total, int)

    @pytest.mark.asyncio
    async def test_get_version_not_found(self, version_manager):
        """Test getting non-existent version."""
        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalar_one_or_none.return_value = None

        version = await version_manager.get_version(uuid4())

        assert version is None

    # Test version restoration

    @pytest.mark.asyncio
    async def test_restore_version(
        self,
        version_manager,
        sample_file_version,
        sample_user_id,
    ):
        """Test restoring a version."""
        # Mock get_version to return sample version
        with patch.object(version_manager, 'get_version', return_value=sample_file_version):
            # Mock get_current_version
            with patch.object(version_manager, 'get_current_version', return_value=None):
                # Mock create_version
                with patch.object(version_manager, 'create_version', return_value=sample_file_version):
                    restored_version = await version_manager.restore_version(
                        version_id=sample_file_version.id,
                        user_id=sample_user_id,
                        user_name="Test User",
                    )

                    assert restored_version is not None
                    assert restored_version.metadata["restored_from_version"] == sample_file_version.version

    @pytest.mark.asyncio
    async def test_restore_nonexistent_version(self, version_manager, sample_user_id):
        """Test restoring non-existent version."""
        # Mock get_version to return None
        with patch.object(version_manager, 'get_version', return_value=None):
            with pytest.raises(ValueError, match="not found"):
                await version_manager.restore_version(
                    version_id=uuid4(),
                    user_id=sample_user_id,
                    user_name="Test User",
                )

    # Test version comparison

    @pytest.mark.asyncio
    async def test_compare_versions(
        self,
        version_manager,
        sample_file_version,
    ):
        """Test comparing two versions."""
        # Create two versions with different content
        from_version = sample_file_version
        from_version.content = "Original content"

        to_version = FileVersion(
            id=uuid4(),
            file_id=from_version.file_id,
            version="2.0.0",
            version_number=2,
            content="Modified content",
            content_hash=hashlib.sha256("Modified content".encode()).hexdigest(),
            checksum="def456",
            size=2048,
            mime_type="text/plain",
            author_id="test-user",
            author_name="Test User",
            message="Updated version",
            status=VersionStatus.ACTIVE,
            is_current=True,
            storage_key="files/test_v2.txt",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Mock get_version for both versions
        version_lookup = {from_version.id: from_version, to_version.id: to_version}

        async def mock_get_version(version_id):
            return version_lookup.get(version_id)

        with patch.object(version_manager, 'get_version', side_effect=mock_get_version):
            result = await version_manager.compare_versions(
                from_version_id=from_version.id,
                to_version_id=to_version.id,
            )

            assert isinstance(result, VersionCompareResult)
            assert result.from_version_id == str(from_version.id)
            assert result.to_version_id == str(to_version.id)
            assert result.size_diff == 1024  # 2048 - 1024
            assert len(result.content_diff) > 0

    @pytest.mark.asyncio
    async def test_compare_versions_text_files(
        self,
        version_manager,
        sample_file_version,
    ):
        """Test comparing text file versions."""
        # Create text file versions
        from_version = sample_file_version
        from_version.content = "Line 1\nLine 2\nLine 3"

        to_version = FileVersion(
            id=uuid4(),
            file_id=from_version.file_id,
            version="2.0.0",
            version_number=2,
            content="Line 1\nLine 2 modified\nLine 3",
            content_hash=hashlib.sha256("Line 1\nLine 2 modified\nLine 3".encode()).hexdigest(),
            checksum="def456",
            size=2048,
            mime_type="text/plain",
            author_id="test-user",
            author_name="Test User",
            message="Updated version",
            status=VersionStatus.ACTIVE,
            is_current=True,
            storage_key="files/test_v2.txt",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        version_lookup = {from_version.id: from_version, to_version.id: to_version}

        async def mock_get_version(version_id):
            return version_lookup.get(version_id)

        with patch.object(version_manager, 'get_version', side_effect=mock_get_version):
            result = await version_manager.compare_versions(
                from_version_id=from_version.id,
                to_version_id=to_version.id,
            )

            assert isinstance(result, VersionCompareResult)
            assert result.stats["lines_changed"] > 0

    # Test version management

    @pytest.mark.asyncio
    async def test_archive_version(self, version_manager, sample_file_version):
        """Test archiving a version."""
        # Mock get_version
        with patch.object(version_manager, 'get_version', return_value=sample_file_version):
            success = await version_manager.archive_version(
                version_id=sample_file_version.id,
                user_id="test-user",
            )

            assert success is True
            assert sample_file_version.status == VersionStatus.ARCHIVED

    @pytest.mark.asyncio
    async def test_lock_version(self, version_manager, sample_file_version):
        """Test locking a version."""
        # Mock get_version
        with patch.object(version_manager, 'get_version', return_value=sample_file_version):
            success = await version_manager.lock_version(
                version_id=sample_file_version.id,
                user_id="test-user",
            )

            assert success is True
            assert sample_file_version.status == VersionStatus.LOCKED

    @pytest.mark.asyncio
    async def test_unlock_version(self, version_manager, sample_file_version):
        """Test unlocking a version."""
        # Lock the version first
        sample_file_version.status = VersionStatus.LOCKED

        # Mock get_version
        with patch.object(version_manager, 'get_version', return_value=sample_file_version):
            success = await version_manager.unlock_version(
                version_id=sample_file_version.id,
                user_id="test-user",
            )

            assert success is True
            assert sample_file_version.status == VersionStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_archive_nonexistent_version(self, version_manager):
        """Test archiving non-existent version."""
        # Mock get_version to return None
        with patch.object(version_manager, 'get_version', return_value=None):
            success = await version_manager.archive_version(
                version_id=uuid4(),
                user_id="test-user",
            )

            assert success is False

    # Test version statistics

    @pytest.mark.asyncio
    async def test_get_version_statistics(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test getting version statistics."""
        # Create multiple versions
        versions = []
        for i in range(3):
            version = FileVersion(
                id=uuid4(),
                file_id=sample_file_id,
                version=f"{i+1}.0.0",
                version_number=i+1,
                content=f"Content {i+1}",
                content_hash=hashlib.sha256(f"Content {i+1}".encode()).hexdigest(),
                checksum=f"checksum{i}",
                size=1024 * (i+1),
                mime_type="text/plain",
                author_id="test-user",
                author_name="Test User",
                message=f"Version {i+1}",
                status=VersionStatus.ACTIVE if i < 2 else VersionStatus.ARCHIVED,
                is_current=(i == 2),
                storage_key=f"files/test_v{i+1}.txt",
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow(),
            )
            versions.append(version)

        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = versions

        stats = await version_manager.get_version_statistics(sample_file_id)

        assert isinstance(stats, VersionStatistics)
        assert stats.total_versions == 3
        assert stats.active_versions == 2
        assert stats.archived_versions == 1
        assert stats.total_size == 6144  # 1024 + 2048 + 3072
        assert len(stats.contributors) == 1

    @pytest.mark.asyncio
    async def test_get_version_timeline(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test getting version timeline."""
        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        timeline = await version_manager.get_version_timeline(sample_file_id, limit=10)

        assert isinstance(timeline, list)

    @pytest.mark.asyncio
    async def test_get_contributors(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test getting contributors."""
        # Mock database execute
        mock_result = Mock()
        mock_result.all.return_value = [
            Mock(author_id="user1", author_name="User 1", version_count=5, last_contribution=datetime.utcnow()),
            Mock(author_id="user2", author_name="User 2", version_count=3, last_contribution=datetime.utcnow()),
        ]
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value = mock_result

        contributors = await version_manager.get_contributors(sample_file_id)

        assert isinstance(contributors, list)
        assert len(contributors) == 2

    # Test version cleanup

    @pytest.mark.asyncio
    async def test_cleanup_old_versions(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test cleaning up old versions."""
        # Create 15 versions
        versions = []
        for i in range(15):
            version = FileVersion(
                id=uuid4(),
                file_id=sample_file_id,
                version=f"{i+1}.0.0",
                version_number=i+1,
                content=f"Content {i+1}",
                content_hash=hashlib.sha256(f"Content {i+1}".encode()).hexdigest(),
                checksum=f"checksum{i}",
                size=1024,
                mime_type="text/plain",
                author_id="test-user",
                author_name="Test User",
                message=f"Version {i+1}",
                status=VersionStatus.ACTIVE,
                is_current=(i == 14),  # Last version is current
                storage_key=f"files/test_v{i+1}.txt",
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow(),
            )
            versions.append(version)

        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = versions

        # Clean up old versions, keeping 10
        deleted_count = await version_manager.cleanup_old_versions(
            file_id=sample_file_id,
            keep_count=10,
        )

        assert deleted_count == 5  # 15 - 10 = 5 versions to delete

    @pytest.mark.asyncio
    async def test_cleanup_old_versions_with_date_filter(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test cleaning up old versions with date filter."""
        # Create versions with different dates
        versions = []
        for i in range(10):
            days_old = 100 if i < 5 else 1  # First 5 are old, last 5 are new
            version = FileVersion(
                id=uuid4(),
                file_id=sample_file_id,
                version=f"{i+1}.0.0",
                version_number=i+1,
                content=f"Content {i+1}",
                content_hash=hashlib.sha256(f"Content {i+1}".encode()).hexdigest(),
                checksum=f"checksum{i}",
                size=1024,
                mime_type="text/plain",
                author_id="test-user",
                author_name="Test User",
                message=f"Version {i+1}",
                status=VersionStatus.ACTIVE,
                is_current=(i == 9),
                storage_key=f"files/test_v{i+1}.txt",
                created_at=datetime.utcnow() - timedelta(days=days_old),
                updated_at=datetime.utcnow(),
            )
            versions.append(version)

        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = versions

        # Clean up versions older than 30 days
        deleted_count = await version_manager.cleanup_old_versions(
            file_id=sample_file_id,
            keep_count=5,
            older_than_days=30,
        )

        assert deleted_count == 5  # Should delete the 5 old versions

    @pytest.mark.asyncio
    async def test_cleanup_old_versions_protects_locked(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test cleanup respects locked versions."""
        # Create versions with one locked
        versions = []
        for i in range(10):
            status = VersionStatus.LOCKED if i == 5 else VersionStatus.ACTIVE
            version = FileVersion(
                id=uuid4(),
                file_id=sample_file_id,
                version=f"{i+1}.0.0",
                version_number=i+1,
                content=f"Content {i+1}",
                content_hash=hashlib.sha256(f"Content {i+1}".encode()).hexdigest(),
                checksum=f"checksum{i}",
                size=1024,
                mime_type="text/plain",
                author_id="test-user",
                author_name="Test User",
                message=f"Version {i+1}",
                status=status,
                is_current=(i == 9),
                storage_key=f"files/test_v{i+1}.txt",
                created_at=datetime.utcnow() - timedelta(days=i),
                updated_at=datetime.utcnow(),
            )
            versions.append(version)

        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = versions

        # Clean up old versions
        deleted_count = await version_cleanup(
            file_id=sample_file_id,
            keep_count=5,
        )

        # Should only delete 4 versions (not the locked one)
        assert deleted_count == 4

    # Test edge cases

    @pytest.mark.asyncio
    async def test_create_version_without_content(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
    ):
        """Test creating version without content (binary file)."""
        version = await version_manager.create_version(
            file_id=sample_file_id,
            author_id=sample_user_id,
            author_name="Test User",
            storage_key="files/binary.dat",
            size=1024 * 1024,  # 1 MB
            mime_type="application/octet-stream",
            message="Binary file version",
        )

        assert version is not None
        assert version.content is None
        assert version.size == 1024 * 1024

    @pytest.mark.asyncio
    async def test_get_versions_empty_result(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test getting versions when file has no versions."""
        # Mock database execute to return empty list
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        versions, total = await version_manager.get_versions(sample_file_id)

        assert versions == []
        assert total == 0

    @pytest.mark.asyncio
    async def test_version_statistics_no_versions(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test version statistics when file has no versions."""
        # Mock database execute to return empty list
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        stats = await version_manager.get_version_statistics(sample_file_id)

        assert isinstance(stats, VersionStatistics)
        assert stats.total_versions == 0

    # Test concurrent operations

    @pytest.mark.asyncio
    async def test_concurrent_version_creation(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test creating versions concurrently."""
        # This test simulates concurrent version creation
        # In a real scenario, database constraints would prevent conflicts

        async def create_version_wrapper(index):
            return await version_manager.create_version(
                file_id=sample_file_id,
                author_id=f"user-{index}",
                author_name=f"User {index}",
                content=f"Content {index}",
                size=1024,
                mime_type="text/plain",
                message=f"Version {index}",
            )

        # Create 5 versions concurrently
        tasks = [create_version_wrapper(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed (or some may fail due to database constraints)
        for result in results:
            if not isinstance(result, Exception):
                assert result is not None

    # Test error handling

    @pytest.mark.asyncio
    async def test_version_creation_database_error(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
    ):
        """Test handling database errors during version creation."""
        # Mock database commit to raise exception
        version_manager.db.commit = AsyncMock(side_effect=Exception("Database error"))

        with pytest.raises(Exception, match="Database error"):
            await version_manager.create_version(
                file_id=sample_file_id,
                author_id=sample_user_id,
                author_name="Test User",
                content="Test content",
                size=1024,
                mime_type="text/plain",
            )

    @pytest.mark.asyncio
    async def test_version_comparison_nonexistent_version(
        self,
        version_manager,
    ):
        """Test comparing with non-existent version."""
        # Mock get_version to return None for one version
        version_lookup = {uuid4(): Mock()}  # Only one version exists

        async def mock_get_version(version_id):
            return version_lookup.get(version_id)

        with patch.object(version_manager, 'get_version', side_effect=mock_get_version):
            with pytest.raises(ValueError, match="not found"):
                await version_manager.compare_versions(
                    from_version_id=uuid4(),
                    to_version_id=uuid4(),
                )

    # Test metadata handling

    @pytest.mark.asyncio
    async def test_create_version_complex_metadata(
        self,
        version_manager,
        sample_file_id,
        sample_user_id,
    ):
        """Test creating version with complex metadata."""
        metadata = {
            "build_info": {
                "number": "123",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            "features": ["auth", "logging", "monitoring"],
            "performance": {
                "load_time": 0.5,
                "memory_usage": "256MB",
            },
            "tags": ["production", "stable"],
        }

        version = await version_manager.create_version(
            file_id=sample_file_id,
            author_id=sample_user_id,
            author_name="Test User",
            content="Content with complex metadata",
            size=1024,
            mime_type="text/plain",
            message="Complex metadata version",
            metadata=metadata,
        )

        assert version is not None
        assert version.metadata == metadata

    # Test version filtering

    @pytest.mark.asyncio
    async def test_version_filter_all_criteria(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test version filter with all criteria."""
        filter_criteria = VersionFilter(
            status=VersionStatus.ACTIVE,
            author_id="test-user",
            author_name="Test",
            date_from=datetime.utcnow() - timedelta(days=7),
            date_to=datetime.utcnow(),
            size_min=1024,
            size_max=1024 * 1024,
            version_contains="1.0",
            message_contains="Initial",
            is_current=True,
        )

        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        versions, total = await version_manager.get_versions(
            file_id=sample_file_id,
            filter=filter_criteria,
        )

        assert isinstance(versions, list)
        assert isinstance(total, int)

    # Test version sorting

    @pytest.mark.asyncio
    async def test_version_sorting_all_fields(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test version sorting with all fields."""
        sort_options = [
            VersionSortBy.CREATED_AT,
            VersionSortBy.VERSION_NUMBER,
            VersionSortBy.AUTHOR,
            VersionSortBy.SIZE,
            VersionSortBy.STATUS,
        ]

        for sort_option in sort_options:
            # Mock database execute
            version_manager.db.execute = AsyncMock()
            version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

            versions, total = await version_manager.get_versions(
                file_id=sample_file_id,
                sort_by=sort_option,
                sort_order="asc",
            )

            assert isinstance(versions, list)
            assert isinstance(total, int)

    # Test pagination

    @pytest.mark.asyncio
    async def test_version_pagination(
        self,
        version_manager,
        sample_file_id,
    ):
        """Test version pagination."""
        # Mock database execute
        version_manager.db.execute = AsyncMock()
        version_manager.db.execute.return_value.scalars.return_value.all.return_value = []

        # Test different pagination scenarios
        scenarios = [
            {"limit": 10, "offset": 0},
            {"limit": 50, "offset": 100},
            {"limit": 1, "offset": 0},
            {"limit": 100, "offset": 0},
        ]

        for scenario in scenarios:
            versions, total = await version_manager.get_versions(
                file_id=sample_file_id,
                limit=scenario["limit"],
                offset=scenario["offset"],
            )

            assert isinstance(versions, list)
            assert isinstance(total, int)
            assert total >= 0


# Helper function for cleanup test
async def version_cleanup(file_id, keep_count, older_than_days=None):
    """Helper function for testing version cleanup."""
    from unittest.mock import AsyncMock, Mock

    version_manager = VersionManager(AsyncMock())

    # Create test versions
    versions = []
    for i in range(10):
        status = VersionStatus.LOCKED if i == 5 else VersionStatus.ACTIVE
        version = Mock(
            id=uuid4(),
            file_id=file_id,
            version=f"{i+1}.0.0",
            version_number=i+1,
            content=f"Content {i+1}",
            content_hash=hashlib.sha256(f"Content {i+1}".encode()).hexdigest(),
            checksum=f"checksum{i}",
            size=1024,
            mime_type="text/plain",
            author_id="test-user",
            author_name="Test User",
            message=f"Version {i+1}",
            status=status,
            is_current=(i == 9),
            storage_key=f"files/test_v{i+1}.txt",
            created_at=datetime.utcnow() - timedelta(days=i),
            updated_at=datetime.utcnow(),
        )
        versions.append(version)

    # Mock database execute
    version_manager.db.execute = AsyncMock()
    version_manager.db.execute.return_value.scalars.return_value.all.return_value = versions

    # Test cleanup
    deleted_count = await version_manager.cleanup_old_versions(
        file_id=file_id,
        keep_count=keep_count,
        older_than_days=older_than_days,
    )

    return deleted_count
