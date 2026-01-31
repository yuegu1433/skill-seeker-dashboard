"""Tests for BackupManager.

This module contains unit and integration tests for the BackupManager class,
testing all backup operations including creation, restore, verification, and scheduling.
"""

import io
import json
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from backend.app.storage.backup import (
    BackupManager,
    BackupSchedule,
    BackupRecord,
    BackupError,
    BackupCreationError,
    BackupRestoreError,
    BackupVerificationError,
    BackupNotFoundError,
)
from backend.app.storage.manager import SkillStorageManager
from backend.app.storage.client import MinIOClient
from backend.app.storage.models import Skill, SkillFile


class TestBackupSchedule:
    """Test suite for BackupSchedule."""

    def test_initialization(self):
        """Test backup schedule initialization."""
        schedule = BackupSchedule(
            name="test_schedule",
            backup_type="full",
            frequency="daily",
            time="02:00",
            retention_days=30,
            enabled=True,
            skills=[uuid4(), uuid4()],
        )

        assert schedule.name == "test_schedule"
        assert schedule.backup_type == "full"
        assert schedule.frequency == "daily"
        assert schedule.time == "02:00"
        assert schedule.retention_days == 30
        assert schedule.enabled is True
        assert len(schedule.skills) == 2

    def test_default_values(self):
        """Test backup schedule with default values."""
        schedule = BackupSchedule(
            name="default_schedule",
            backup_type="incremental",
            frequency="weekly",
            time="01:00",
        )

        assert schedule.retention_days == 30
        assert schedule.enabled is True
        assert schedule.skills == []


class TestBackupRecord:
    """Test suite for BackupRecord."""

    def test_initialization(self):
        """Test backup record initialization."""
        backup_id = str(uuid4())
        skill_id = uuid4()
        created_at = datetime.utcnow()

        record = BackupRecord(
            backup_id=backup_id,
            skill_id=skill_id,
            backup_type="full",
            file_count=100,
            total_size=1024 * 1024,
            checksum="abc123",
            created_at=created_at,
            status="completed",
        )

        assert record.backup_id == backup_id
        assert record.skill_id == skill_id
        assert record.backup_type == "full"
        assert record.file_count == 100
        assert record.total_size == 1024 * 1024
        assert record.checksum == "abc123"
        assert record.created_at == created_at
        assert record.status == "completed"
        assert record.error_message is None

    def test_with_error(self):
        """Test backup record with error."""
        record = BackupRecord(
            backup_id=str(uuid4()),
            skill_id=uuid4(),
            backup_type="incremental",
            file_count=50,
            total_size=512 * 1024,
            checksum="def456",
            created_at=datetime.utcnow(),
            status="failed",
            error_message="Backup failed: disk full",
        )

        assert record.status == "failed"
        assert record.error_message == "Backup failed: disk full"


class TestBackupManager:
    """Test suite for BackupManager."""

    @pytest.fixture
    def mock_minio_client(self):
        """Create mock MinIO client."""
        return Mock(spec=MinIOClient)

    @pytest.fixture
    def mock_storage_manager(self):
        """Create mock storage manager."""
        return Mock(spec=SkillStorageManager)

    @pytest.fixture
    def mock_db_session(self):
        """Create mock database session."""
        session = Mock(spec=Session)
        session.query.return_value.filter.return_value.all.return_value = []
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        return session

    @pytest.fixture
    def backup_manager(self, mock_minio_client, mock_storage_manager, mock_db_session):
        """Create BackupManager instance."""
        return BackupManager(
            minio_client=mock_minio_client,
            storage_manager=mock_storage_manager,
            database_session=mock_db_session,
            backup_bucket="skillseekers-backups",
            backup_prefix="backups",
            max_concurrent_backups=5,
            verification_enabled=True,
        )

    @pytest.fixture
    def test_skill(self):
        """Create test skill."""
        return Skill(
            id=uuid4(),
            name="test-skill",
            platform="claude",
            status="active",
            source_type="github",
        )

    @pytest.fixture
    def test_files(self, test_skill):
        """Create test skill files."""
        return [
            SkillFile(
                id=uuid4(),
                skill_id=test_skill.id,
                object_name=f"skills/{test_skill.id}/file{i}.txt",
                file_path=f"file{i}.txt",
                file_type="skill_file",
                file_size=1024 * (i + 1),
                content_type="text/plain",
                checksum=f"checksum{i}",
                metadata={},
                tags=["test"],
                is_public=False,
            )
            for i in range(3)
        ]

    # Test initialization
    @pytest.mark.asyncio
    async def test_initialization(self, backup_manager, mock_minio_client):
        """Test backup manager initialization."""
        mock_minio_client.bucket_exists.return_value = False

        await backup_manager.initialize()

        assert backup_manager.backup_bucket == "skillseekers-backups"
        assert backup_manager.backup_prefix == "backups"
        assert backup_manager.max_concurrent_backups == 5
        assert backup_manager.verification_enabled is True

    @pytest.mark.asyncio
    async def test_initialization_bucket_exists(self, backup_manager, mock_minio_client):
        """Test backup manager initialization when bucket exists."""
        mock_minio_client.bucket_exists.return_value = True

        await backup_manager.initialize()

        mock_minio_client.bucket_exists.assert_called_once()
        mock_minio_client.create_bucket.assert_not_called()

    @pytest.mark.asyncio
    async def test_initialization_create_bucket(self, backup_manager, mock_minio_client):
        """Test backup manager initialization creates bucket."""
        mock_minio_client.bucket_exists.return_value = False

        await backup_manager.initialize()

        mock_minio_client.create_bucket.assert_called_once()

    # Test backup creation
    @pytest.mark.asyncio
    async def test_create_backup_success(self, backup_manager, mock_minio_client, mock_db_session, test_skill, test_files):
        """Test successful backup creation."""
        # Setup
        skill_id = test_skill.id

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to return files
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Mock MinIO operations
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "backups/test/manifest.json",
            "etag": "etag123",
            "size": 1024,
        }
        mock_minio_client.get_object.return_value = io.BytesIO(b"test file content")

        # Execute
        backup_id = await backup_manager.create_backup(skill_id=skill_id, backup_type="full")

        # Verify
        assert backup_id is not None
        assert mock_minio_client.put_object.called

    @pytest.mark.asyncio
    async def test_create_backup_no_files(self, backup_manager, mock_minio_client, mock_db_session):
        """Test backup creation with no files."""
        # Setup
        skill_id = uuid4()

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to return no files
        mock_db_session.query.return_value.filter.return_value.all.return_value = []

        # Execute
        backup_id = await backup_manager.create_backup(skill_id=skill_id)

        # Verify
        assert backup_id is not None

    @pytest.mark.asyncio
    async def test_create_backup_incremental(self, backup_manager, mock_minio_client, mock_db_session, test_skill, test_files):
        """Test incremental backup creation."""
        # Setup
        skill_id = test_skill.id

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to return files
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Mock MinIO operations
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "backups/test/manifest.json",
            "etag": "etag123",
            "size": 1024,
        }
        mock_minio_client.get_object.return_value = io.BytesIO(b"test file content")

        # Execute
        backup_id = await backup_manager.create_backup(skill_id=skill_id, backup_type="incremental")

        # Verify
        assert backup_id is not None

    @pytest.mark.asyncio
    async def test_create_backup_full_system(self, backup_manager, mock_minio_client, mock_db_session, test_files):
        """Test full system backup (no skill_id specified)."""
        # Setup
        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to return files
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Mock MinIO operations
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "backups/test/manifest.json",
            "etag": "etag123",
            "size": 1024,
        }
        mock_minio_client.get_object.return_value = io.BytesIO(b"test file content")

        # Execute
        backup_id = await backup_manager.create_backup(backup_type="full")

        # Verify
        assert backup_id is not None

    @pytest.mark.asyncio
    async def test_create_backup_failure(self, backup_manager, mock_minio_client, mock_db_session, test_skill):
        """Test backup creation failure."""
        # Setup
        skill_id = test_skill.id

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to raise exception
        mock_db_session.query.side_effect = Exception("Database error")

        # Execute and verify
        with pytest.raises(BackupCreationError):
            await backup_manager.create_backup(skill_id=skill_id)

    # Test backup restore
    @pytest.mark.asyncio
    async def test_restore_backup_success(self, backup_manager, mock_minio_client, mock_storage_manager):
        """Test successful backup restore."""
        # Setup
        backup_id = str(uuid4())

        # Create mock manifest
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            "file_count": 2,
            "total_size": 2048,
            "skills": [str(uuid4())],
            "files": [
                {
                    "file_path": "file1.txt",
                    "object_name": "skills/test/file1.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                },
                {
                    "file_path": "file2.txt",
                    "object_name": "skills/test/file2.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                },
            ],
        }

        # Mock MinIO operations
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))
        mock_minio_client.stat_object.return_value = Mock()
        mock_storage_manager.upload_file.return_value = Mock(success=True)

        # Execute
        result = await backup_manager.restore_backup(backup_id)

        # Verify
        assert result is True

    @pytest.mark.asyncio
    async def test_restore_backup_not_found(self, backup_manager, mock_minio_client):
        """Test restore backup not found."""
        # Setup
        backup_id = str(uuid4())

        # Mock MinIO get object to return None (no manifest)
        mock_minio_client.get_object.side_effect = Exception("Not found")

        # Execute and verify
        with pytest.raises(BackupNotFoundError):
            await backup_manager.restore_backup(backup_id)

    @pytest.mark.asyncio
    async def test_restore_backup_with_skill_filter(self, backup_manager, mock_minio_client, mock_storage_manager):
        """Test restore backup with skill filter."""
        # Setup
        backup_id = str(uuid4())
        skill_id = uuid4()

        # Create mock manifest
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            "file_count": 2,
            "total_size": 2048,
            "skills": [str(skill_id)],
            "files": [
                {
                    "file_path": "file1.txt",
                    "object_name": f"skills/{skill_id}/file1.txt",
                    "file_size": 1024,
                    "content_type": "text/plain",
                },
            ],
        }

        # Mock MinIO operations
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))
        mock_minio_client.stat_object.return_value = Mock()
        mock_storage_manager.upload_file.return_value = Mock(success=True)

        # Execute
        result = await backup_manager.restore_backup(backup_id, skill_id=skill_id)

        # Verify
        assert result is True

    @pytest.mark.asyncio
    async def test_restore_backup_failure(self, backup_manager, mock_minio_client):
        """Test backup restore failure."""
        # Setup
        backup_id = str(uuid4())

        # Mock MinIO get object to raise exception
        mock_minio_client.get_object.side_effect = Exception("Restore error")

        # Execute and verify
        with pytest.raises(BackupRestoreError):
            await backup_manager.restore_backup(backup_id)

    # Test backup verification
    @pytest.mark.asyncio
    async def test_verify_backup_success(self, backup_manager, mock_minio_client):
        """Test successful backup verification."""
        # Setup
        backup_id = str(uuid4())

        # Create mock manifest
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            "file_count": 2,
            "total_size": 2048,
            "checksum": "abc123",
            "files": [
                {
                    "file_path": "file1.txt",
                    "file_size": 1024,
                },
                {
                    "file_path": "file2.txt",
                    "file_size": 1024,
                },
            ],
        }

        # Mock MinIO operations
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))
        mock_minio_client.stat_object.return_value = Mock()

        # Execute
        result = await backup_manager.verify_backup(backup_id)

        # Verify
        assert result["backup_id"] == backup_id
        assert result["overall_status"] == "passed"
        assert result["manifest_verified"] is True
        assert result["files_verified"] is True
        assert result["checksum_verified"] is True

    @pytest.mark.asyncio
    async def test_verify_backup_not_found(self, backup_manager, mock_minio_client):
        """Test verify backup not found."""
        # Setup
        backup_id = str(uuid4())

        # Mock MinIO get object to return None
        mock_minio_client.get_object.return_value = None

        # Execute and verify
        with pytest.raises(BackupNotFoundError):
            await backup_manager.verify_backup(backup_id)

    @pytest.mark.asyncio
    async def test_verify_backup_failure(self, backup_manager, mock_minio_client):
        """Test backup verification failure."""
        # Setup
        backup_id = str(uuid4())

        # Mock MinIO get object to raise exception
        mock_minio_client.get_object.side_effect = Exception("Verification error")

        # Execute and verify
        with pytest.raises(BackupVerificationError):
            await backup_manager.verify_backup(backup_id)

    # Test backup listing
    @pytest.mark.asyncio
    async def test_list_backups_success(self, backup_manager, mock_minio_client):
        """Test successful backup listing."""
        # Setup
        backup_id = str(uuid4())

        # Create mock manifest
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            "file_count": 2,
            "total_size": 2048,
            "checksum": "abc123",
        }

        # Mock MinIO operations
        mock_minio_client.list_objects.return_value = [
            {
                "object_name": f"backups/{backup_id}/manifest.json",
                "size": 1024,
            }
        ]
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))

        # Execute
        backups = await backup_manager.list_backups()

        # Verify
        assert len(backups) == 1
        assert backups[0]["backup_id"] == backup_id
        assert backups[0]["backup_type"] == "full"

    @pytest.mark.asyncio
    async def test_list_backups_with_filters(self, backup_manager, mock_minio_client):
        """Test backup listing with filters."""
        # Setup
        backup_id = str(uuid4())
        skill_id = uuid4()

        # Create mock manifest
        manifest = {
            "backup_id": backup_id,
            "backup_type": "incremental",
            "skill_id": str(skill_id),
            "created_at": datetime.utcnow().isoformat(),
            "file_count": 2,
            "total_size": 2048,
            "checksum": "abc123",
        }

        # Mock MinIO operations
        mock_minio_client.list_objects.return_value = [
            {
                "object_name": f"backups/{backup_id}/manifest.json",
                "size": 1024,
            }
        ]
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))

        # Execute with filters
        backups = await backup_manager.list_backups(
            skill_id=skill_id,
            backup_type="incremental",
            limit=10,
        )

        # Verify
        assert len(backups) == 1

    @pytest.mark.asyncio
    async def test_list_backups_empty(self, backup_manager, mock_minio_client):
        """Test backup listing when empty."""
        # Setup - no backups
        mock_minio_client.list_objects.return_value = []

        # Execute
        backups = await backup_manager.list_backups()

        # Verify
        assert len(backups) == 0

    # Test backup deletion
    @pytest.mark.asyncio
    async def test_delete_backup_success(self, backup_manager, mock_minio_client):
        """Test successful backup deletion."""
        # Setup
        backup_id = str(uuid4())

        # Create mock manifest
        manifest = {
            "backup_id": backup_id,
            "files": [
                {
                    "file_path": "file1.txt",
                },
                {
                    "file_path": "file2.txt",
                },
            ],
        }

        # Mock MinIO operations
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))
        mock_minio_client.remove_object.return_value = True

        # Execute
        result = await backup_manager.delete_backup(backup_id)

        # Verify
        assert result is True
        # Should call remove_object for manifest + files
        assert mock_minio_client.remove_object.call_count == 3

    @pytest.mark.asyncio
    async def test_delete_backup_not_found(self, backup_manager, mock_minio_client):
        """Test delete backup not found."""
        # Setup
        backup_id = str(uuid4())

        # Mock MinIO get object to return None
        mock_minio_client.get_object.return_value = None

        # Execute and verify
        with pytest.raises(BackupNotFoundError):
            await backup_manager.delete_backup(backup_id)

    # Test backup scheduling
    @pytest.mark.asyncio
    async def test_schedule_backup(self, backup_manager):
        """Test backup scheduling."""
        # Setup
        schedule = BackupSchedule(
            name="test_schedule",
            backup_type="full",
            frequency="daily",
            time="02:00",
            retention_days=30,
        )

        # Execute
        result = await backup_manager.schedule_backup(schedule)

        # Verify
        assert result is True
        assert schedule.name in backup_manager.schedules

    @pytest.mark.asyncio
    async def test_unschedule_backup(self, backup_manager):
        """Test backup unscheduling."""
        # Setup - create a schedule first
        schedule = BackupSchedule(
            name="test_schedule",
            backup_type="full",
            frequency="daily",
            time="02:00",
        )
        backup_manager.schedules[schedule.name] = schedule

        # Execute
        result = await backup_manager.unschedule_backup(schedule.name)

        # Verify
        assert result is True
        assert schedule.name not in backup_manager.schedules

    @pytest.mark.asyncio
    async def test_unschedule_nonexistent(self, backup_manager):
        """Test unschedule nonexistent backup."""
        # Execute
        result = await backup_manager.unschedule_backup("nonexistent")

        # Verify
        assert result is False

    # Test statistics
    @pytest.mark.asyncio
    async def test_get_backup_statistics(self, backup_manager, mock_minio_client):
        """Test backup statistics retrieval."""
        # Setup - add some statistics
        backup_manager.stats["total_backups"] = 10
        backup_manager.stats["successful_backups"] = 8
        backup_manager.stats["failed_backups"] = 2
        backup_manager.stats["total_files_backed_up"] = 100
        backup_manager.stats["total_backup_size"] = 1024 * 1024
        backup_manager.stats["last_backup_time"] = datetime.utcnow()

        # Mock list backups
        mock_minio_client.list_objects.return_value = []
        backup_manager.schedules["test_schedule"] = BackupSchedule(
            name="test_schedule",
            backup_type="full",
            frequency="daily",
            time="02:00",
        )

        # Execute
        stats = await backup_manager.get_backup_statistics()

        # Verify
        assert stats["total_backups"] == 10
        assert stats["successful_backups"] == 8
        assert stats["failed_backups"] == 2
        assert stats["success_rate_percent"] == 80.0
        assert stats["total_files_backed_up"] == 100
        assert stats["total_backup_size"] == 1024 * 1024
        assert stats["active_schedules"] == 1
        assert stats["active_backups"] == 0

    # Test helper methods
    @pytest.mark.asyncio
    async def test_get_files_to_backup_full(self, backup_manager, mock_db_session, test_skill, test_files):
        """Test get files for full backup."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Execute
        files = await backup_manager._get_files_to_backup(test_skill.id, "full")

        # Verify
        assert len(files) == 3
        assert all("file_path" in f for f in files)

    @pytest.mark.asyncio
    async def test_get_files_to_backup_incremental(self, backup_manager, mock_db_session, test_skill, test_files):
        """Test get files for incremental backup."""
        # Setup
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Execute
        files = await backup_manager._get_files_to_backup(test_skill.id, "incremental")

        # Verify
        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_get_files_to_backup_no_skill(self, backup_manager, mock_db_session, test_files):
        """Test get files for backup without skill filter."""
        # Setup
        mock_db_session.query.return_value.all.return_value = test_files

        # Execute
        files = await backup_manager._get_files_to_backup(None, "full")

        # Verify
        assert len(files) == 3

    @pytest.mark.asyncio
    async def test_create_backup_manifest(self, backup_manager):
        """Test backup manifest creation."""
        # Setup
        backup_id = str(uuid4())
        files = [
            {
                "file_path": "file1.txt",
                "file_size": 1024,
                "skill_id": str(uuid4()),
            },
            {
                "file_path": "file2.txt",
                "file_size": 2048,
                "skill_id": str(uuid4()),
            },
        ]

        # Execute
        manifest = await backup_manager._create_backup_manifest(backup_id, files, "full")

        # Verify
        assert manifest["backup_id"] == backup_id
        assert manifest["backup_type"] == "full"
        assert manifest["file_count"] == 2
        assert manifest["total_size"] == 3072
        assert "total_size_human" in manifest
        assert "created_at" in manifest

    def test_get_backup_object_name(self, backup_manager):
        """Test backup object name generation."""
        # Setup
        backup_id = "backup123"
        backup_path = "files/test/file.txt"

        # Execute
        object_name = backup_manager._get_backup_object_name(backup_id, backup_path)

        # Verify
        assert "backups" in object_name
        assert "backup123" in object_name
        assert "files_test_file.txt" in object_name

    @pytest.mark.asyncio
    async def test_upload_backup_object(self, backup_manager, mock_minio_client):
        """Test backup object upload."""
        # Setup
        bucket_name = "test-bucket"
        object_name = "test-object"
        data = b"test data"
        content_type = "text/plain"

        # Mock operation context
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()

        # Execute
        result = await backup_manager._upload_backup_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data,
            content_type=content_type,
        )

        # Verify
        assert result is True
        mock_minio_client.put_object.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_backup_manifest(self, backup_manager):
        """Test backup manifest verification."""
        # Setup
        backup_id = str(uuid4())
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            "files": [],
        }

        # Execute
        result = await backup_manager._verify_backup_manifest(backup_id, manifest)

        # Verify
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_backup_manifest_invalid(self, backup_manager):
        """Test backup manifest verification with invalid manifest."""
        # Setup
        backup_id = str(uuid4())
        manifest = {
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            # Missing backup_id
        }

        # Execute
        result = await backup_manager._verify_backup_manifest(backup_id, manifest)

        # Verify
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_backup_files(self, backup_manager, mock_minio_client):
        """Test backup files verification."""
        # Setup
        backup_id = str(uuid4())
        manifest = {
            "files": [
                {
                    "file_path": "file1.txt",
                },
                {
                    "file_path": "file2.txt",
                },
            ],
        }

        # Mock MinIO stat_object to return success
        mock_minio_client.stat_object.return_value = Mock()

        # Execute
        results = await backup_manager._verify_backup_files(backup_id, manifest)

        # Verify
        assert len(results) == 2
        assert all(results.values())

    @pytest.mark.asyncio
    async def test_verify_backup_files_failure(self, backup_manager, mock_minio_client):
        """Test backup files verification with failure."""
        # Setup
        backup_id = str(uuid4())
        manifest = {
            "files": [
                {
                    "file_path": "file1.txt",
                },
                {
                    "file_path": "file2.txt",
                },
            ],
        }

        # Mock MinIO stat_object to raise exception for file2
        def stat_side_effect(bucket, object):
            if "file2.txt" in object:
                raise Exception("Not found")
            return Mock()

        mock_minio_client.stat_object.side_effect = stat_side_effect

        # Execute
        results = await backup_manager._verify_backup_files(backup_id, manifest)

        # Verify
        assert len(results) == 2
        assert results["file1.txt"] is True
        assert results["file2.txt"] is False

    @pytest.mark.asyncio
    async def test_filter_skills_for_restore(self, backup_manager):
        """Test skill filtering for restore."""
        # Setup
        skill_id = uuid4()
        manifest = {
            "skills": [str(skill_id), str(uuid4())],
            "files": [],
        }

        # Execute with skill filter
        result = backup_manager._filter_skills_for_restore(manifest, skill_id)

        # Verify
        assert len(result) == 1
        assert result[0]["skill_id"] == str(skill_id)

    @pytest.mark.asyncio
    async def test_filter_skills_for_restore_no_filter(self, backup_manager):
        """Test skill filtering without filter."""
        # Setup
        manifest = {
            "skills": [str(uuid4()), str(uuid4())],
            "files": [],
        }

        # Execute without filter
        result = backup_manager._filter_skills_for_restore(manifest, None)

        # Verify
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_calculate_backup_checksum(self, backup_manager):
        """Test backup checksum calculation."""
        # Setup
        backup_id = str(uuid4())
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "files": [],
        }

        # Execute
        checksum = await backup_manager._calculate_backup_checksum(backup_id, manifest)

        # Verify
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA-256 hex digest

    # Test load schedules
    @pytest.mark.asyncio
    async def test_load_schedules(self, backup_manager):
        """Test loading backup schedules."""
        # Execute
        await backup_manager._load_schedules()

        # Verify
        assert len(backup_manager.schedules) > 0
        assert "daily_backup" in backup_manager.schedules

    # Test backup operation context manager
    @pytest.mark.asyncio
    async def test_backup_operation_context_success(self, backup_manager):
        """Test backup operation context manager success."""
        # Execute
        async with backup_manager.backup_operation("test_operation"):
            # Do nothing
            pass

        # Verify - no exceptions raised

    @pytest.mark.asyncio
    async def test_backup_operation_context_failure(self, backup_manager):
        """Test backup operation context manager with failure."""
        # Execute and verify
        with pytest.raises(ValueError):
            async with backup_manager.backup_operation("test_operation"):
                raise ValueError("Test error")

    # Test integration scenarios
    @pytest.mark.asyncio
    async def test_full_backup_workflow(self, backup_manager, mock_minio_client, mock_db_session, mock_storage_manager, test_skill, test_files):
        """Test complete backup workflow: create -> verify -> list -> restore -> delete."""
        # Setup
        skill_id = test_skill.id

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to return files
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Mock MinIO operations
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "backups/test/manifest.json",
            "etag": "etag123",
            "size": 1024,
        }
        mock_minio_client.get_object.return_value = io.BytesIO(b"test file content")
        mock_minio_client.stat_object.return_value = Mock()
        mock_storage_manager.upload_file.return_value = Mock(success=True)

        # 1. Create backup
        backup_id = await backup_manager.create_backup(skill_id=skill_id)
        assert backup_id is not None

        # 2. Verify backup (create mock manifest)
        manifest = {
            "backup_id": backup_id,
            "backup_type": "full",
            "created_at": datetime.utcnow().isoformat(),
            "file_count": 3,
            "total_size": sum(f.file_size for f in test_files),
            "checksum": "abc123",
            "files": [
                {
                    "file_path": f.file_path,
                    "file_size": f.file_size,
                    "content_type": f.content_type,
                }
                for f in test_files
            ],
        }

        # Reset get_object to return manifest
        mock_minio_client.get_object.return_value = io.BytesIO(json.dumps(manifest).encode("utf-8"))

        verification_result = await backup_manager.verify_backup(backup_id)
        assert verification_result["overall_status"] == "passed"

        # 3. List backups
        mock_minio_client.list_objects.return_value = [
            {
                "object_name": f"backups/{backup_id}/manifest.json",
                "size": 1024,
            }
        ]

        backups = await backup_manager.list_backups()
        assert len(backups) == 1

        # 4. Restore backup
        restore_result = await backup_manager.restore_backup(backup_id)
        assert restore_result is True

        # 5. Delete backup
        mock_minio_client.remove_object.return_value = True
        delete_result = await backup_manager.delete_backup(backup_id)
        assert delete_result is True

    @pytest.mark.asyncio
    async def test_backup_with_verification_disabled(self, backup_manager, mock_minio_client, mock_db_session, test_skill, test_files):
        """Test backup creation with verification disabled."""
        # Setup
        backup_manager.verification_enabled = False
        skill_id = test_skill.id

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to return files
        mock_db_session.query.return_value.filter.return_value.all.return_value = test_files

        # Mock MinIO operations
        mock_minio_client.operation_context.return_value.__enter__ = Mock()
        mock_minio_client.operation_context.return_value.__exit__ = Mock()
        mock_minio_client.put_object.return_value = {
            "object_name": "backups/test/manifest.json",
            "etag": "etag123",
            "size": 1024,
        }
        mock_minio_client.get_object.return_value = io.BytesIO(b"test file content")

        # Execute
        backup_id = await backup_manager.create_backup(skill_id=skill_id, verify=False)

        # Verify
        assert backup_id is not None

    @pytest.mark.asyncio
    async def test_backup_error_handling(self, backup_manager, mock_minio_client, mock_db_session):
        """Test comprehensive error handling in backup operations."""
        # Setup
        skill_id = uuid4()

        # Mock bucket exists
        mock_minio_client.bucket_exists.return_value = True

        # Mock query to raise exception
        mock_db_session.query.side_effect = SQLAlchemyError("Database error")

        # Test backup creation error
        with pytest.raises(BackupCreationError):
            await backup_manager.create_backup(skill_id=skill_id)

        # Verify statistics
        assert backup_manager.stats["total_backups"] == 1
        assert backup_manager.stats["failed_backups"] == 1

    # Test configuration validation
    @pytest.mark.asyncio
    async def test_backup_manager_configuration(self, mock_minio_client, mock_storage_manager, mock_db_session):
        """Test BackupManager with different configurations."""
        # Test with custom configuration
        backup_manager = BackupManager(
            minio_client=mock_minio_client,
            storage_manager=mock_storage_manager,
            database_session=mock_db_session,
            backup_bucket="custom-backups",
            backup_prefix="custom",
            max_concurrent_backups=10,
            verification_enabled=False,
        )

        assert backup_manager.backup_bucket == "custom-backups"
        assert backup_manager.backup_prefix == "custom"
        assert backup_manager.max_concurrent_backups == 10
        assert backup_manager.verification_enabled is False
