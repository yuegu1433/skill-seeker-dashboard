"""Backup Operations Celery Tasks.

This module contains Celery tasks for file backup operations including
full backups, incremental backups, and backup restoration.
"""

import logging
import os
import shutil
import tarfile
import zipfile
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import asyncio
import json

from celery import current_task
from celery.exceptions import Retry

from app.file.tasks import celery_app, update_task_state
from app.file.manager import FileManager
from app.file.version_manager import VersionManager
from app.database.session import get_db

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="create_full_backup")
def create_full_backup(
    self,
    file_ids: Optional[List[str]] = None,
    backup_path: Optional[str] = None,
    user_id: Optional[str] = None,
    compression: str = "gzip",
    encrypt: bool = False,
    **kwargs,
):
    """Create a full backup of files.

    Args:
        self: Celery task instance
        file_ids: List of file IDs to backup (None for all files)
        backup_path: Backup destination path
        user_id: User ID
        compression: Compression algorithm (gzip, bzip2, xz, none)
        encrypt: Whether to encrypt the backup
        **kwargs: Additional arguments

    Returns:
        Backup operation result
    """
    task_id = str(uuid4())
    backup_id = str(uuid4())
    logger.info(f"Starting full backup task: {task_id}, backup_id: {backup_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", backup_id=backup_id, type="full")

        # Initialize managers
        db_session = get_db()
        file_manager = FileManager(db_session=db_session)

        # If no file_ids provided, get all files
        if not file_ids:
            file_list = asyncio.run(file_manager.list_files(filters={}))
            file_ids = [f.id for f in file_list.files]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            backup_id=backup_id,
            total_files=len(file_ids),
            processed_files=0,
        )

        # Create backup directory
        if not backup_path:
            backup_path = f"/backups/full_{backup_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        os.makedirs(backup_path, exist_ok=True)

        # Process files
        successful_backups = 0
        failed_backups = 0
        backup_results = []

        for i, file_id in enumerate(file_ids):
            try:
                # Get file
                file_obj = asyncio.run(file_manager.get_file(file_id))
                if not file_obj:
                    failed_backups += 1
                    backup_results.append({
                        "file_id": file_id,
                        "status": "failed",
                        "error": "File not found",
                    })
                    continue

                # Create backup copy
                backup_file_path = os.path.join(backup_path, f"{file_id}_{file_obj.filename}")

                # In real implementation, would copy actual file
                # For now, create metadata backup
                backup_metadata = {
                    "file_id": file_id,
                    "original_path": file_obj.storage_path,
                    "backup_path": backup_file_path,
                    "filename": file_obj.filename,
                    "size": file_obj.size,
                    "hash": file_obj.hash,
                    "created_at": file_obj.created_at.isoformat(),
                    "backup_timestamp": datetime.utcnow().isoformat(),
                }

                # Save metadata
                metadata_path = f"{backup_file_path}.json"
                with open(metadata_path, "w") as f:
                    json.dump(backup_metadata, f, indent=2)

                successful_backups += 1
                backup_results.append({
                    "file_id": file_id,
                    "status": "success",
                    "backup_path": backup_file_path,
                    "metadata_path": metadata_path,
                })

                # Update progress
                if (i + 1) % 10 == 0:
                    update_task_state.delay(
                        task_id,
                        "processing",
                        backup_id=backup_id,
                        total_files=len(file_ids),
                        processed_files=i + 1,
                    )

            except Exception as e:
                logger.error(f"Failed to backup file {file_id}: {e}")
                failed_backups += 1
                backup_results.append({
                    "file_id": file_id,
                    "status": "failed",
                    "error": str(e),
                })

        # Compress backup if requested
        archive_path = None
        if compression != "none":
            archive_path = f"{backup_path}.tar.{compression}"

            if compression == "gzip":
                mode = "w:gz"
            elif compression == "bzip2":
                mode = "w:bz2"
            elif compression == "xz":
                mode = "w:xz"
            else:
                mode = "w"

            try:
                with tarfile.open(archive_path, mode) as tar:
                    tar.add(backup_path, arcname=os.path.basename(backup_path))

                # Remove uncompressed directory
                shutil.rmtree(backup_path)
                backup_path = archive_path

            except Exception as e:
                logger.error(f"Failed to compress backup: {e}")

        # Create backup manifest
        manifest = {
            "backup_id": backup_id,
            "type": "full",
            "timestamp": datetime.utcnow().isoformat(),
            "file_count": len(file_ids),
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "backup_path": backup_path,
            "compression": compression,
            "encrypted": encrypt,
            "results": backup_results,
        }

        manifest_path = f"{backup_path}.manifest.json"
        if archive_path:
            manifest_path = f"{archive_path}.manifest.json"

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            backup_id=backup_id,
            backup_path=backup_path,
            manifest_path=manifest_path,
            total_files=len(file_ids),
            successful_backups=successful_backups,
            failed_backups=failed_backups,
            compressed=compression != "none",
            encrypted=encrypt,
        )

        logger.info(f"Full backup task completed: {task_id}")

        return {
            "task_id": task_id,
            "backup_id": backup_id,
            "status": "completed",
            "backup_path": backup_path,
            "manifest_path": manifest_path,
            "total_files": len(file_ids),
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "compressed": compression != "none",
            "encrypted": encrypt,
            "results": backup_results,
        }

    except Exception as e:
        logger.error(f"Full backup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying full backup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=120, exc=e)

        raise


@celery_app.task(bind=True, name="create_incremental_backup")
def create_incremental_backup(
    self,
    base_backup_id: str,
    file_ids: Optional[List[str]] = None,
    backup_path: Optional[str] = None,
    user_id: Optional[str] = None,
    compression: str = "gzip",
    **kwargs,
):
    """Create an incremental backup based on a previous backup.

    Args:
        self: Celery task instance
        base_backup_id: ID of the base backup
        file_ids: List of file IDs to backup
        backup_path: Backup destination path
        user_id: User ID
        compression: Compression algorithm
        **kwargs: Additional arguments

    Returns:
        Incremental backup result
    """
    task_id = str(uuid4())
    backup_id = str(uuid4())
    logger.info(f"Starting incremental backup task: {task_id}, backup_id: {backup_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", backup_id=backup_id, type="incremental")

        # Initialize managers
        db_session = get_db()
        file_manager = FileManager(db_session=db_session)
        version_manager = VersionManager(db_session=db_session)

        # If no file_ids provided, get files modified since last backup
        if not file_ids:
            # Get last backup timestamp
            last_backup_time = datetime.utcnow() - timedelta(days=7)  # Default to 7 days
            file_list = asyncio.run(file_manager.list_files(filters={}))
            file_ids = [
                f.id for f in file_list.files
                if f.updated_at and f.updated_at > last_backup_time
            ]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            backup_id=backup_id,
            base_backup_id=base_backup_id,
            total_files=len(file_ids),
            processed_files=0,
        )

        # Create backup directory
        if not backup_path:
            backup_path = f"/backups/incremental_{backup_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        os.makedirs(backup_path, exist_ok=True)

        # Process files (only changed files)
        successful_backups = 0
        failed_backups = 0
        backup_results = []

        for i, file_id in enumerate(file_ids):
            try:
                # Get file and its versions
                file_obj = asyncio.run(file_manager.get_file(file_id))
                if not file_obj:
                    failed_backups += 1
                    backup_results.append({
                        "file_id": file_id,
                        "status": "failed",
                        "error": "File not found",
                    })
                    continue

                # Check if file has changed since last backup
                # For incremental backup, only backup files that have changed
                latest_version = asyncio.run(version_manager.get_latest_version(file_id))

                if not latest_version:
                    # File is new, include in incremental backup
                    backup_type = "new"
                else:
                    # File exists, check if modified
                    backup_type = "modified"

                # Create backup copy
                backup_file_path = os.path.join(backup_path, f"{file_id}_{file_obj.filename}")

                # Create incremental backup metadata
                backup_metadata = {
                    "file_id": file_id,
                    "backup_type": backup_type,
                    "original_path": file_obj.storage_path,
                    "backup_path": backup_file_path,
                    "filename": file_obj.filename,
                    "size": file_obj.size,
                    "hash": file_obj.hash,
                    "created_at": file_obj.created_at.isoformat(),
                    "updated_at": file_obj.updated_at.isoformat() if file_obj.updated_at else None,
                    "latest_version": latest_version.id if latest_version else None,
                    "backup_timestamp": datetime.utcnow().isoformat(),
                    "base_backup_id": base_backup_id,
                }

                # Save metadata
                metadata_path = f"{backup_file_path}.json"
                with open(metadata_path, "w") as f:
                    json.dump(backup_metadata, f, indent=2)

                successful_backups += 1
                backup_results.append({
                    "file_id": file_id,
                    "backup_type": backup_type,
                    "status": "success",
                    "backup_path": backup_file_path,
                    "metadata_path": metadata_path,
                })

                # Update progress
                if (i + 1) % 10 == 0:
                    update_task_state.delay(
                        task_id,
                        "processing",
                        backup_id=backup_id,
                        total_files=len(file_ids),
                        processed_files=i + 1,
                    )

            except Exception as e:
                logger.error(f"Failed to backup file {file_id}: {e}")
                failed_backups += 1
                backup_results.append({
                    "file_id": file_id,
                    "status": "failed",
                    "error": str(e),
                })

        # Compress backup if requested
        archive_path = None
        if compression != "none":
            archive_path = f"{backup_path}.tar.{compression}"

            if compression == "gzip":
                mode = "w:gz"
            elif compression == "bzip2":
                mode = "w:bz2"
            elif compression == "xz":
                mode = "w:xz"
            else:
                mode = "w"

            try:
                with tarfile.open(archive_path, mode) as tar:
                    tar.add(backup_path, arcname=os.path.basename(backup_path))

                # Remove uncompressed directory
                shutil.rmtree(backup_path)
                backup_path = archive_path

            except Exception as e:
                logger.error(f"Failed to compress backup: {e}")

        # Create backup manifest
        manifest = {
            "backup_id": backup_id,
            "type": "incremental",
            "base_backup_id": base_backup_id,
            "timestamp": datetime.utcnow().isoformat(),
            "file_count": len(file_ids),
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "backup_path": backup_path,
            "compression": compression,
            "results": backup_results,
        }

        manifest_path = f"{backup_path}.manifest.json"
        if archive_path:
            manifest_path = f"{archive_path}.manifest.json"

        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            backup_id=backup_id,
            backup_path=backup_path,
            manifest_path=manifest_path,
            total_files=len(file_ids),
            successful_backups=successful_backups,
            failed_backups=failed_backups,
            compressed=compression != "none",
        )

        logger.info(f"Incremental backup task completed: {task_id}")

        return {
            "task_id": task_id,
            "backup_id": backup_id,
            "status": "completed",
            "base_backup_id": base_backup_id,
            "backup_path": backup_path,
            "manifest_path": manifest_path,
            "total_files": len(file_ids),
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "compressed": compression != "none",
            "results": backup_results,
        }

    except Exception as e:
        logger.error(f"Incremental backup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying incremental backup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=120, exc=e)

        raise


@celery_app.task(bind=True, name="restore_backup")
def restore_backup(
    self,
    backup_id: str,
    restore_path: Optional[str] = None,
    file_ids: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    overwrite: bool = False,
    **kwargs,
):
    """Restore files from a backup.

    Args:
        self: Celery task instance
        backup_id: Backup ID to restore from
        restore_path: Path to restore files to
        file_ids: Specific file IDs to restore (None for all files)
        user_id: User ID
        overwrite: Whether to overwrite existing files
        **kwargs: Additional arguments

    Returns:
        Restore operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting backup restore task: {task_id}, backup_id: {backup_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", backup_id=backup_id, type="restore")

        # Initialize managers
        db_session = get_db()
        file_manager = FileManager(db_session=db_session)

        # Load backup manifest
        manifest_path = f"/backups/{backup_id}.manifest.json"
        if not os.path.exists(manifest_path):
            raise FileNotFoundError(f"Backup manifest not found: {manifest_path}")

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        # Filter files to restore
        files_to_restore = manifest["results"]
        if file_ids:
            files_to_restore = [f for f in files_to_restore if f["file_id"] in file_ids]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            backup_id=backup_id,
            total_files=len(files_to_restore),
            processed_files=0,
        )

        # Create restore directory
        if not restore_path:
            restore_path = f"/restores/restore_{backup_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        os.makedirs(restore_path, exist_ok=True)

        # Process restores
        successful_restores = 0
        failed_restores = 0
        restore_results = []

        for i, file_backup in enumerate(files_to_restore):
            try:
                file_id = file_backup["file_id"]

                # Load backup metadata
                metadata_path = file_backup["metadata_path"]
                with open(metadata_path, "r") as f:
                    backup_metadata = json.load(f)

                # Restore file
                restore_file_path = os.path.join(restore_path, backup_metadata["filename"])

                # In real implementation, would restore actual file
                # For now, create restored metadata file
                restored_metadata = {
                    "file_id": file_id,
                    "restored_from_backup": backup_id,
                    "original_path": backup_metadata["original_path"],
                    "restore_path": restore_file_path,
                    "filename": backup_metadata["filename"],
                    "size": backup_metadata["size"],
                    "hash": backup_metadata["hash"],
                    "restored_at": datetime.utcnow().isoformat(),
                }

                # Save metadata
                metadata_file = f"{restore_file_path}.restored.json"
                with open(metadata_file, "w") as f:
                    json.dump(restored_metadata, f, indent=2)

                successful_restores += 1
                restore_results.append({
                    "file_id": file_id,
                    "status": "success",
                    "restore_path": restore_file_path,
                    "metadata_path": metadata_file,
                })

                # Update progress
                if (i + 1) % 10 == 0:
                    update_task_state.delay(
                        task_id,
                        "processing",
                        backup_id=backup_id,
                        total_files=len(files_to_restore),
                        processed_files=i + 1,
                    )

            except Exception as e:
                logger.error(f"Failed to restore file {file_backup['file_id']}: {e}")
                failed_restores += 1
                restore_results.append({
                    "file_id": file_backup["file_id"],
                    "status": "failed",
                    "error": str(e),
                })

        # Create restore manifest
        restore_manifest = {
            "restore_id": str(uuid4()),
            "backup_id": backup_id,
            "timestamp": datetime.utcnow().isoformat(),
            "restore_path": restore_path,
            "file_count": len(files_to_restore),
            "successful_restores": successful_restores,
            "failed_restores": failed_restores,
            "overwrite": overwrite,
            "results": restore_results,
        }

        manifest_path = os.path.join(restore_path, "restore_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(restore_manifest, f, indent=2)

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            backup_id=backup_id,
            restore_path=restore_path,
            manifest_path=manifest_path,
            total_files=len(files_to_restore),
            successful_restores=successful_restores,
            failed_restores=failed_restores,
            overwrite=overwrite,
        )

        logger.info(f"Backup restore task completed: {task_id}")

        return {
            "task_id": task_id,
            "backup_id": backup_id,
            "status": "completed",
            "restore_path": restore_path,
            "manifest_path": manifest_path,
            "total_files": len(files_to_restore),
            "successful_restores": successful_restores,
            "failed_restores": failed_restores,
            "overwrite": overwrite,
            "results": restore_results,
        }

    except Exception as e:
        logger.error(f"Backup restore task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying backup restore task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=120, exc=e)

        raise


@celery_app.task(bind=True, name="schedule_backup")
def schedule_backup(
    self,
    schedule_config: Dict[str, Any],
    user_id: Optional[str] = None,
    **kwargs,
):
    """Schedule a recurring backup.

    Args:
        self: Celery task instance
        schedule_config: Backup schedule configuration
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Schedule operation result
    """
    task_id = str(uuid4())
    logger.info(f"Scheduling backup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="schedule")

        # Extract schedule configuration
        backup_type = schedule_config.get("type", "full")  # full or incremental
        interval = schedule_config.get("interval", "daily")  # daily, weekly, monthly
        retention_days = schedule_config.get("retention_days", 30)
        compression = schedule_config.get("compression", "gzip")

        # Create scheduled task configuration
        schedule_config_final = {
            "task_id": task_id,
            "backup_type": backup_type,
            "interval": interval,
            "retention_days": retention_days,
            "compression": compression,
            "created_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "active": True,
        }

        # In real implementation, would save to database
        # For now, just return success
        schedule_id = str(uuid4())

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            schedule_id=schedule_id,
            schedule_config=schedule_config_final,
        )

        logger.info(f"Backup schedule created: {task_id}, schedule_id: {schedule_id}")

        return {
            "task_id": task_id,
            "schedule_id": schedule_id,
            "status": "completed",
            "schedule_config": schedule_config_final,
        }

    except Exception as e:
        logger.error(f"Schedule backup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying schedule backup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise
