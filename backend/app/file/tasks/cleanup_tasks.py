"""Cleanup Operations Celery Tasks.

This module contains Celery tasks for file cleanup operations including
cleanup of old versions, temporary files, orphaned files, and storage cleanup.
"""

import logging
import os
import shutil
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import asyncio
import glob

from celery import current_task
from celery.exceptions import Retry

from app.file.tasks import celery_app, update_task_state
from app.file.manager import FileManager
from app.file.version_manager import VersionManager
from app.file.preview_manager import PreviewManager
from app.database.session import get_db

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="cleanup_old_versions")
def cleanup_old_versions(
    self,
    retention_days: int = 30,
    keep_count: int = 5,
    file_ids: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Clean up old file versions.

    Args:
        self: Celery task instance
        retention_days: Number of days to retain versions
        keep_count: Minimum number of versions to keep
        file_ids: Specific file IDs to clean (None for all files)
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Cleanup operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting old versions cleanup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="version_cleanup")

        # Initialize managers
        db_session = get_db()
        version_manager = VersionManager(db_session=db_session)

        # Get files to clean
        if not file_ids:
            # Get all files from database
            file_manager = FileManager(db_session=db_session)
            file_list = asyncio.run(file_manager.list_files(filters={}))
            file_ids = [f.id for f in file_list.files]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            total_files=len(file_ids),
            processed_files=0,
            retention_days=retention_days,
            keep_count=keep_count,
        )

        # Process files
        total_cleaned = 0
        total_kept = 0
        failed_cleanups = 0
        cleanup_results = []

        for i, file_id in enumerate(file_ids):
            try:
                # Get file versions
                version_list = asyncio.run(
                    version_manager.list_versions(
                        file_id=file_id,
                        page=1,
                        size=1000,  # Get all versions
                    )
                )

                if not version_list.versions:
                    continue

                # Sort versions by creation date (newest first)
                sorted_versions = sorted(
                    version_list.versions,
                    key=lambda v: v.created_at,
                    reverse=True,
                )

                # Determine versions to delete
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                versions_to_delete = []

                for version in sorted_versions:
                    # Keep versions that are too recent
                    if version.created_at > cutoff_date:
                        continue

                    # Keep minimum count
                    if len(sorted_versions) - len(versions_to_delete) <= keep_count:
                        continue

                    versions_to_delete.append(version)

                # Delete old versions
                deleted_count = 0
                kept_count = len(sorted_versions) - len(versions_to_delete)

                for version in versions_to_delete:
                    try:
                        success = asyncio.run(version_manager.delete_version(version.id, force=True))
                        if success:
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete version {version.id}: {e}")
                        failed_cleanups += 1

                total_cleaned += deleted_count
                total_kept += kept_count

                cleanup_results.append({
                    "file_id": file_id,
                    "total_versions": len(sorted_versions),
                    "deleted_versions": deleted_count,
                    "kept_versions": kept_count,
                })

                # Update progress
                if (i + 1) % 10 == 0:
                    update_task_state.delay(
                        task_id,
                        "processing",
                        total_files=len(file_ids),
                        processed_files=i + 1,
                        total_cleaned=total_cleaned,
                        total_kept=total_kept,
                    )

            except Exception as e:
                logger.error(f"Failed to process file {file_id}: {e}")
                failed_cleanups += 1
                cleanup_results.append({
                    "file_id": file_id,
                    "status": "failed",
                    "error": str(e),
                })

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            total_files=len(file_ids),
            total_cleaned=total_cleaned,
            total_kept=total_kept,
            failed_cleanups=failed_cleanups,
            retention_days=retention_days,
            keep_count=keep_count,
            results=cleanup_results,
        )

        logger.info(f"Old versions cleanup task completed: {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "total_files": len(file_ids),
            "total_cleaned": total_cleaned,
            "total_kept": total_kept,
            "failed_cleanups": failed_cleanups,
            "retention_days": retention_days,
            "keep_count": keep_count,
            "results": cleanup_results,
        }

    except Exception as e:
        logger.error(f"Old versions cleanup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying old versions cleanup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=120, exc=e)

        raise


@celery_app.task(bind=True, name="cleanup_temporary_files")
def cleanup_temporary_files(
    self,
    older_than_hours: int = 24,
    temp_paths: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Clean up temporary files.

    Args:
        self: Celery task instance
        older_than_hours: Number of hours to keep temporary files
        temp_paths: List of temporary paths to clean
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Cleanup operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting temporary files cleanup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="temp_cleanup")

        # Default temporary paths
        if not temp_paths:
            temp_paths = [
                "/tmp/uploads",
                "/tmp/downloads",
                "/tmp/previews",
                "/tmp/cache",
            ]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            total_paths=len(temp_paths),
            processed_paths=0,
            older_than_hours=older_than_hours,
        )

        # Process each temporary path
        total_files_deleted = 0
        total_size_freed = 0
        failed_paths = 0
        cleanup_results = []

        for i, temp_path in enumerate(temp_paths):
            try:
                if not os.path.exists(temp_path):
                    cleanup_results.append({
                        "path": temp_path,
                        "status": "skipped",
                        "reason": "Path does not exist",
                    })
                    continue

                # Find old files
                cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

                # Recursively find files
                old_files = []
                for root, dirs, files in os.walk(temp_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mtime < cutoff_time:
                                old_files.append(file_path)
                        except OSError:
                            continue

                # Delete old files
                files_deleted = 0
                size_freed = 0

                for file_path in old_files:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_deleted += 1
                        size_freed += file_size
                    except OSError as e:
                        logger.error(f"Failed to delete temporary file {file_path}: {e}")

                total_files_deleted += files_deleted
                total_size_freed += size_freed

                cleanup_results.append({
                    "path": temp_path,
                    "status": "success",
                    "files_deleted": files_deleted,
                    "size_freed": size_freed,
                    "old_files_found": len(old_files),
                })

                # Update progress
                update_task_state.delay(
                    task_id,
                    "processing",
                    total_paths=len(temp_paths),
                    processed_paths=i + 1,
                    total_files_deleted=total_files_deleted,
                    total_size_freed=total_size_freed,
                )

            except Exception as e:
                logger.error(f"Failed to cleanup path {temp_path}: {e}")
                failed_paths += 1
                cleanup_results.append({
                    "path": temp_path,
                    "status": "failed",
                    "error": str(e),
                })

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            total_paths=len(temp_paths),
            total_files_deleted=total_files_deleted,
            total_size_freed=total_size_freed,
            failed_paths=failed_paths,
            older_than_hours=older_than_hours,
            results=cleanup_results,
        )

        logger.info(f"Temporary files cleanup task completed: {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "total_paths": len(temp_paths),
            "total_files_deleted": total_files_deleted,
            "total_size_freed": total_size_freed,
            "failed_paths": failed_paths,
            "older_than_hours": older_than_hours,
            "results": cleanup_results,
        }

    except Exception as e:
        logger.error(f"Temporary files cleanup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying temporary files cleanup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="cleanup_orphaned_files")
def cleanup_orphaned_files(
    self,
    storage_paths: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Clean up orphaned files (files in storage but not in database).

    Args:
        self: Celery task instance
        storage_paths: List of storage paths to check
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Cleanup operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting orphaned files cleanup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="orphaned_cleanup")

        # Initialize managers
        db_session = get_db()
        file_manager = FileManager(db_session=db_session)

        # Get all files from database
        file_list = asyncio.run(file_manager.list_files(filters={}))
        db_file_paths = {f.storage_path for f in file_list.files if f.storage_path}

        # Default storage paths
        if not storage_paths:
            storage_paths = [
                "/storage/files",
                "/storage/uploads",
            ]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            total_paths=len(storage_paths),
            processed_paths=0,
            db_file_count=len(db_file_paths),
        )

        # Process each storage path
        total_files_checked = 0
        total_orphaned_found = 0
        total_orphaned_deleted = 0
        failed_paths = 0
        cleanup_results = []

        for i, storage_path in enumerate(storage_paths):
            try:
                if not os.path.exists(storage_path):
                    cleanup_results.append({
                        "path": storage_path,
                        "status": "skipped",
                        "reason": "Path does not exist",
                    })
                    continue

                # Find all files in storage
                orphaned_files = []

                for root, dirs, files in os.walk(storage_path):
                    for file in files:
                        file_path = os.path.join(root, file)

                        # Check if file exists in database
                        if file_path not in db_file_paths:
                            orphaned_files.append(file_path)

                total_files_checked += sum(len(files) for _, _, files in os.walk(storage_path))
                total_orphaned_found += len(orphaned_files)

                # Delete orphaned files
                files_deleted = 0

                for file_path in orphaned_files:
                    try:
                        os.remove(file_path)
                        files_deleted += 1
                    except OSError as e:
                        logger.error(f"Failed to delete orphaned file {file_path}: {e}")

                total_orphaned_deleted += files_deleted

                cleanup_results.append({
                    "path": storage_path,
                    "status": "success",
                    "files_checked": sum(len(files) for _, _, files in os.walk(storage_path)),
                    "orphaned_found": len(orphaned_files),
                    "orphaned_deleted": files_deleted,
                })

                # Update progress
                update_task_state.delay(
                    task_id,
                    "processing",
                    total_paths=len(storage_paths),
                    processed_paths=i + 1,
                    total_files_checked=total_files_checked,
                    total_orphaned_found=total_orphaned_found,
                    total_orphaned_deleted=total_orphaned_deleted,
                )

            except Exception as e:
                logger.error(f"Failed to cleanup path {storage_path}: {e}")
                failed_paths += 1
                cleanup_results.append({
                    "path": storage_path,
                    "status": "failed",
                    "error": str(e),
                })

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            total_paths=len(storage_paths),
            total_files_checked=total_files_checked,
            total_orphaned_found=total_orphaned_found,
            total_orphaned_deleted=total_orphaned_deleted,
            failed_paths=failed_paths,
            db_file_count=len(db_file_paths),
            results=cleanup_results,
        )

        logger.info(f"Orphaned files cleanup task completed: {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "total_paths": len(storage_paths),
            "total_files_checked": total_files_checked,
            "total_orphaned_found": total_orphaned_found,
            "total_orphaned_deleted": total_orphaned_deleted,
            "failed_paths": failed_paths,
            "db_file_count": len(db_file_paths),
            "results": cleanup_results,
        }

    except Exception as e:
        logger.error(f"Orphaned files cleanup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying orphaned files cleanup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=120, exc=e)

        raise


@celery_app.task(bind=True, name="cleanup_old_backups")
def cleanup_old_backups(
    self,
    retention_days: int = 90,
    backup_paths: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Clean up old backup files.

    Args:
        self: Celery task instance
        retention_days: Number of days to retain backups
        backup_paths: List of backup paths to clean
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Cleanup operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting old backups cleanup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="backup_cleanup")

        # Default backup paths
        if not backup_paths:
            backup_paths = [
                "/backups",
            ]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            total_paths=len(backup_paths),
            processed_paths=0,
            retention_days=retention_days,
        )

        # Process each backup path
        total_backups_deleted = 0
        total_size_freed = 0
        failed_paths = 0
        cleanup_results = []

        for i, backup_path in enumerate(backup_paths):
            try:
                if not os.path.exists(backup_path):
                    cleanup_results.append({
                        "path": backup_path,
                        "status": "skipped",
                        "reason": "Path does not exist",
                    })
                    continue

                # Find old backups
                cutoff_time = datetime.utcnow() - timedelta(days=retention_days)

                old_backups = []
                for root, dirs, files in os.walk(backup_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mtime < cutoff_time:
                                old_backups.append(file_path)
                        except OSError:
                            continue

                # Delete old backups
                backups_deleted = 0
                size_freed = 0

                for file_path in old_backups:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        backups_deleted += 1
                        size_freed += file_size
                    except OSError as e:
                        logger.error(f"Failed to delete backup {file_path}: {e}")

                total_backups_deleted += backups_deleted
                total_size_freed += size_freed

                cleanup_results.append({
                    "path": backup_path,
                    "status": "success",
                    "backups_deleted": backups_deleted,
                    "size_freed": size_freed,
                    "old_backups_found": len(old_backups),
                })

                # Update progress
                update_task_state.delay(
                    task_id,
                    "processing",
                    total_paths=len(backup_paths),
                    processed_paths=i + 1,
                    total_backups_deleted=total_backups_deleted,
                    total_size_freed=total_size_freed,
                )

            except Exception as e:
                logger.error(f"Failed to cleanup backup path {backup_path}: {e}")
                failed_paths += 1
                cleanup_results.append({
                    "path": backup_path,
                    "status": "failed",
                    "error": str(e),
                })

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            total_paths=len(backup_paths),
            total_backups_deleted=total_backups_deleted,
            total_size_freed=total_size_freed,
            failed_paths=failed_paths,
            retention_days=retention_days,
            results=cleanup_results,
        )

        logger.info(f"Old backups cleanup task completed: {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "total_paths": len(backup_paths),
            "total_backups_deleted": total_backups_deleted,
            "total_size_freed": total_size_freed,
            "failed_paths": failed_paths,
            "retention_days": retention_days,
            "results": cleanup_results,
        }

    except Exception as e:
        logger.error(f"Old backups cleanup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying old backups cleanup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="cleanup_cache_files")
def cleanup_cache_files(
    self,
    older_than_hours: int = 168,  # 1 week
    cache_paths: Optional[List[str]] = None,
    user_id: Optional[str] = None,
    **kwargs,
):
    """Clean up cache files.

    Args:
        self: Celery task instance
        older_than_hours: Number of hours to keep cache files
        cache_paths: List of cache paths to clean
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Cleanup operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting cache files cleanup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="cache_cleanup")

        # Default cache paths
        if not cache_paths:
            cache_paths = [
                "/cache/previews",
                "/cache/thumbnails",
                "/cache/temp",
            ]

        # Update task state with progress
        update_task_state.delay(
            task_id,
            "processing",
            total_paths=len(cache_paths),
            processed_paths=0,
            older_than_hours=older_than_hours,
        )

        # Process each cache path
        total_files_deleted = 0
        total_size_freed = 0
        failed_paths = 0
        cleanup_results = []

        for i, cache_path in enumerate(cache_paths):
            try:
                if not os.path.exists(cache_path):
                    cleanup_results.append({
                        "path": cache_path,
                        "status": "skipped",
                        "reason": "Path does not exist",
                    })
                    continue

                # Find old cache files
                cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

                old_files = []
                for root, dirs, files in os.walk(cache_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_mtime < cutoff_time:
                                old_files.append(file_path)
                        except OSError:
                            continue

                # Delete old cache files
                files_deleted = 0
                size_freed = 0

                for file_path in old_files:
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_deleted += 1
                        size_freed += file_size
                    except OSError as e:
                        logger.error(f"Failed to delete cache file {file_path}: {e}")

                total_files_deleted += files_deleted
                total_size_freed += size_freed

                cleanup_results.append({
                    "path": cache_path,
                    "status": "success",
                    "files_deleted": files_deleted,
                    "size_freed": size_freed,
                    "old_files_found": len(old_files),
                })

                # Update progress
                update_task_state.delay(
                    task_id,
                    "processing",
                    total_paths=len(cache_paths),
                    processed_paths=i + 1,
                    total_files_deleted=total_files_deleted,
                    total_size_freed=total_size_freed,
                )

            except Exception as e:
                logger.error(f"Failed to cleanup cache path {cache_path}: {e}")
                failed_paths += 1
                cleanup_results.append({
                    "path": cache_path,
                    "status": "failed",
                    "error": str(e),
                })

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            total_paths=len(cache_paths),
            total_files_deleted=total_files_deleted,
            total_size_freed=total_size_freed,
            failed_paths=failed_paths,
            older_than_hours=older_than_hours,
            results=cleanup_results,
        )

        logger.info(f"Cache files cleanup task completed: {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "total_paths": len(cache_paths),
            "total_files_deleted=total_files_deleted,
            total_size_freed=total_size_freed,
            "failed_paths": failed_paths,
            "older_than_hours": older_than_hours,
            "results": cleanup_results,
        }

    except Exception as e:
        logger.error(f"Cache files cleanup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying cache files cleanup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60, exc=e)

        raise


@celery_app.task(bind=True, name="full_system_cleanup")
def full_system_cleanup(
    self,
    config: Dict[str, Any],
    user_id: Optional[str] = None,
    **kwargs,
):
    """Perform a full system cleanup.

    Args:
        self: Celery task instance
        config: Cleanup configuration
        user_id: User ID
        **kwargs: Additional arguments

    Returns:
        Full cleanup operation result
    """
    task_id = str(uuid4())
    logger.info(f"Starting full system cleanup task: {task_id}")

    try:
        # Update task state
        update_task_state.delay(task_id, "started", type="full_cleanup")

        # Extract configuration
        version_retention_days = config.get("version_retention_days", 30)
        temp_retention_hours = config.get("temp_retention_hours", 24)
        cache_retention_hours = config.get("cache_retention_hours", 168)
        backup_retention_days = config.get("backup_retention_days", 90)

        # Update task state
        update_task_state.delay(
            task_id,
            "processing",
            stage="initializing",
            config=config,
        )

        cleanup_results = {}

        # 1. Clean up old versions
        update_task_state.delay(task_id, "processing", stage="versions")
        try:
            result = cleanup_old_versions.delay(
                retention_days=version_retention_days,
                keep_count=5,
            )
            cleanup_results["versions"] = result.get()
        except Exception as e:
            logger.error(f"Version cleanup failed: {e}")
            cleanup_results["versions"] = {"status": "failed", "error": str(e)}

        # 2. Clean up temporary files
        update_task_state.delay(task_id, "processing", stage="temp_files")
        try:
            result = cleanup_temporary_files.delay(
                older_than_hours=temp_retention_hours,
            )
            cleanup_results["temp_files"] = result.get()
        except Exception as e:
            logger.error(f"Temporary files cleanup failed: {e}")
            cleanup_results["temp_files"] = {"status": "failed", "error": str(e)}

        # 3. Clean up cache files
        update_task_state.delay(task_id, "processing", stage="cache")
        try:
            result = cleanup_cache_files.delay(
                older_than_hours=cache_retention_hours,
            )
            cleanup_results["cache"] = result.get()
        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")
            cleanup_results["cache"] = {"status": "failed", "error": str(e)}

        # 4. Clean up old backups
        update_task_state.delay(task_id, "processing", stage="backups")
        try:
            result = cleanup_old_backups.delay(
                retention_days=backup_retention_days,
            )
            cleanup_results["backups"] = result.get()
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            cleanup_results["backups"] = {"status": "failed", "error": str(e)}

        # 5. Clean up orphaned files (only if enabled)
        if config.get("cleanup_orphaned", True):
            update_task_state.delay(task_id, "processing", stage="orphaned")
            try:
                result = cleanup_orphaned_files.delay()
                cleanup_results["orphaned"] = result.get()
            except Exception as e:
                logger.error(f"Orphaned files cleanup failed: {e}")
                cleanup_results["orphaned"] = {"status": "failed", "error": str(e)}

        # Calculate summary statistics
        total_files_cleaned = 0
        total_size_freed = 0
        successful_stages = 0
        failed_stages = 0

        for stage, result in cleanup_results.items():
            if isinstance(result, dict):
                if result.get("status") == "completed":
                    successful_stages += 1
                    total_files_cleaned += result.get("total_files_deleted", 0)
                    total_files_cleaned += result.get("total_cleaned", 0)
                    total_files_cleaned += result.get("total_backups_deleted", 0)
                    total_size_freed += result.get("total_size_freed", 0)
                else:
                    failed_stages += 1

        # Update task state
        update_task_state.delay(
            task_id,
            "completed",
            total_stages=len(cleanup_results),
            successful_stages=successful_stages,
            failed_stages=failed_stages,
            total_files_cleaned=total_files_cleaned,
            total_size_freed=total_size_freed,
            results=cleanup_results,
        )

        logger.info(f"Full system cleanup task completed: {task_id}")

        return {
            "task_id": task_id,
            "status": "completed",
            "total_stages": len(cleanup_results),
            "successful_stages": successful_stages,
            "failed_stages": failed_stages,
            "total_files_cleaned": total_files_cleaned,
            "total_size_freed": total_size_freed,
            "results": cleanup_results,
        }

    except Exception as e:
        logger.error(f"Full system cleanup task failed: {task_id}, error: {e}")

        update_task_state.delay(task_id, "failed", error=str(e))

        if self.request.retries < self.max_retries:
            logger.info(f"Retrying full system cleanup task: {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(countdown=180, exc=e)

        raise
