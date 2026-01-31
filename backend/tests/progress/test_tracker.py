"""Test cases for task tracking functionality.

This module contains comprehensive unit tests for TaskTracker and ProgressManager
including progress updates, status management, and caching mechanisms.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List
from datetime import datetime, timezone

from backend.app.progress.tracker import (
    TaskTracker,
    TaskCache,
    ProgressAggregator,
    TaskNotFoundError,
    TaskUpdateError,
)
from backend.app.progress.progress_manager import ProgressManager
from backend.app.progress.models.task import TaskProgress, TaskStatus
from backend.app.progress.schemas.progress_operations import (
    CreateTaskRequest,
    UpdateProgressRequest,
)


class TestTaskCache:
    """Test cases for TaskCache."""

    def test_cache_initialization(self):
        """Test TaskCache initialization."""
        cache = TaskCache(max_size=500, ttl=1800)
        assert cache.max_size == 500
        assert cache.ttl == 1800
        assert len(cache._cache) == 0
        assert len(cache._access_times) == 0

    def test_cache_default_values(self):
        """Test TaskCache with default values."""
        cache = TaskCache()
        assert cache.max_size == 10000
        assert cache.ttl == 3600

    @pytest.mark.asyncio
    async def test_set_and_get(self):
        """Test setting and getting cache entries."""
        cache = TaskCache()
        task_data = {"task_id": "task-001", "progress": 50.0, "status": "running"}

        await cache.set("task-001", task_data)
        result = await cache.get("task-001")

        assert result is not None
        assert result["task_id"] == "task-001"
        assert result["progress"] == 50.0
        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self):
        """Test getting nonexistent cache entry."""
        cache = TaskCache()
        result = await cache.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_remove(self):
        """Test removing cache entry."""
        cache = TaskCache()
        task_data = {"task_id": "task-001", "progress": 50.0}

        await cache.set("task-001", task_data)
        await cache.remove("task-001")
        result = await cache.get("task-001")

        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        """Test cache TTL expiration."""
        cache = TaskCache(ttl=1)  # 1 second TTL
        task_data = {"task_id": "task-001", "progress": 50.0}

        await cache.set("task-001", task_data)

        # Should still be there
        result = await cache.get("task-001")
        assert result is not None

        # Wait for TTL to expire
        await asyncio.sleep(1.1)

        # Should be expired
        result = await cache.get("task-001")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Test cache size eviction."""
        cache = TaskCache(max_size=2)
        task_data_template = {"task_id": "task-{:03d}", "progress": 50.0}

        # Fill cache to capacity
        await cache.set("task-001", task_data_template.format("001"))
        await cache.set("task-002", task_data_template.format("002"))

        # Add third task (should evict oldest)
        await cache.set("task-003", task_data_template.format("003"))

        # Oldest task should be evicted
        result = await cache.get("task-001")
        assert result is None

        # Other tasks should still be there
        result = await cache.get("task-002")
        assert result is not None
        assert result["task_id"] == "task-002"

        result = await cache.get("task-003")
        assert result is not None
        assert result["task_id"] == "task-003"

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing cache."""
        cache = TaskCache()
        await cache.set("task-001", {"task_id": "task-001"})
        await cache.set("task-002", {"task_id": "task-002"})

        await cache.clear()

        assert len(cache._cache) == 0
        assert len(cache._access_times) == 0


class TestProgressAggregator:
    """Test cases for ProgressAggregator."""

    def test_aggregator_initialization(self):
        """Test ProgressAggregator initialization."""
        aggregator = ProgressAggregator()
        assert len(aggregator._aggregated_data) == 0

    @pytest.mark.asyncio
    async def test_add_task_progress(self):
        """Test adding task progress to aggregation."""
        aggregator = ProgressAggregator()

        await aggregator.add_task_progress(
            task_id="task-001",
            task_type="skill_creation",
            progress=50.0,
            status="running",
            weight=1.0,
        )

        data = await aggregator.get_aggregation("skill_creation")
        assert data["total_progress"] == 50.0
        assert data["weighted_progress"] == 50.0
        assert data["total_weight"] == 1.0
        assert data["running_count"] == 1
        assert len(data["tasks"]) == 1

    @pytest.mark.asyncio
    async def test_multiple_tasks_same_type(self):
        """Test adding multiple tasks of same type."""
        aggregator = ProgressAggregator()

        # Add multiple tasks
        for i in range(3):
            await aggregator.add_task_progress(
                task_id=f"task-{i:03d}",
                task_type="skill_creation",
                progress=25.0 * (i + 1),
                status="running",
                weight=1.0,
            )

        data = await aggregator.get_aggregation("skill_creation")
        # Average of (25, 50, 75) = 50
        assert data["total_progress"] == 50.0
        assert len(data["tasks"]) == 3

    @pytest.mark.asyncio
    async def test_weighted_progress(self):
        """Test weighted progress calculation."""
        aggregator = ProgressAggregator()

        # Add tasks with different weights
        await aggregator.add_task_progress(
            task_id="task-001",
            task_type="skill_creation",
            progress=100.0,
            status="completed",
            weight=1.0,
        )

        await aggregator.add_task_progress(
            task_id="task-002",
            task_type="skill_creation",
            progress=0.0,
            status="pending",
            weight=3.0,
        )

        data = await aggregator.get_aggregation("skill_creation")
        # Weighted average: (100*1 + 0*3) / (1+3) = 25
        assert data["weighted_progress"] == 25.0
        assert data["total_progress"] == 50.0  # Simple average

    @pytest.mark.asyncio
    async def test_status_counts(self):
        """Test status count tracking."""
        aggregator = ProgressAggregator()

        await aggregator.add_task_progress(
            task_id="task-001",
            task_type="skill_creation",
            progress=100.0,
            status="completed",
        )

        await aggregator.add_task_progress(
            task_id="task-002",
            task_type="skill_creation",
            progress=50.0,
            status="running",
        )

        await aggregator.add_task_progress(
            task_id="task-003",
            task_type="skill_creation",
            progress=0.0,
            status="failed",
        )

        data = await aggregator.get_aggregation("skill_creation")
        assert data["completed_count"] == 1
        assert data["running_count"] == 1
        assert data["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_remove_task(self):
        """Test removing task from aggregation."""
        aggregator = ProgressAggregator()

        await aggregator.add_task_progress(
            task_id="task-001",
            task_type="skill_creation",
            progress=50.0,
            status="running",
        )

        await aggregator.add_task_progress(
            task_id="task-002",
            task_type="skill_creation",
            progress=75.0,
            status="running",
        )

        # Remove one task
        await aggregator.remove_task("task-001")

        data = await aggregator.get_aggregation("skill_creation")
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["task_id"] == "task-002"
        assert data["total_progress"] == 75.0

    @pytest.mark.asyncio
    async def test_clear(self):
        """Test clearing aggregated data."""
        aggregator = ProgressAggregator()

        await aggregator.add_task_progress(
            task_id="task-001",
            task_type="skill_creation",
            progress=50.0,
            status="running",
        )

        await aggregator.add_task_progress(
            task_id="task-002",
            task_type="file_processing",
            progress=25.0,
            status="running",
        )

        await aggregator.clear()

        data = await aggregator.get_aggregation()
        assert len(data) == 0


class TestTaskTracker:
    """Test cases for TaskTracker."""

    @pytest.fixture
    def task_tracker(self):
        """Create TaskTracker instance for testing."""
        return TaskTracker(db_session=None, cache_size=100, cache_ttl=3600)

    def test_task_tracker_initialization(self, task_tracker):
        """Test TaskTracker initialization."""
        assert task_tracker.db_session is None
        assert task_tracker.batch_size == 100
        assert task_tracker.batch_timeout == 5.0
        assert len(task_tracker._pending_updates) == 0
        assert len(task_tracker._update_handlers) == 0

    @pytest.mark.asyncio
    async def test_create_task(self, task_tracker):
        """Test creating a new task."""
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
            description="Testing task creation",
            estimated_duration=300,
            total_steps=5,
            metadata={"priority": "high"},
            tags=["test", "automation"],
        )

        task_data = await task_tracker.create_task(request)

        assert task_data["task_id"] == "task-001"
        assert task_data["user_id"] == "user-001"
        assert task_data["task_type"] == "skill_creation"
        assert task_data["task_name"] == "Test Task"
        assert task_data["description"] == "Testing task creation"
        assert task_data["progress"] == 0.0
        assert task_data["status"] == "pending"
        assert task_data["estimated_duration"] == 300
        assert task_data["total_steps"] == 5
        assert task_data["metadata"]["priority"] == "high"
        assert "test" in task_data["tags"]
        assert "automation" in task_data["tags"]

    @pytest.mark.asyncio
    async def test_create_task_minimal(self, task_tracker):
        """Test creating task with minimal data."""
        request = CreateTaskRequest(
            task_id="task-002",
            user_id="user-002",
            task_type="file_processing",
            task_name="Simple Task",
        )

        task_data = await task_tracker.create_task(request)

        assert task_data["task_id"] == "task-002"
        assert task_data["user_id"] == "user-002"
        assert task_data["progress"] == 0.0
        assert task_data["status"] == "pending"
        assert task_data["metadata"] == {}
        assert task_data["tags"] == []

    @pytest.mark.asyncio
    async def test_create_task_validation_error(self, task_tracker):
        """Test task creation with invalid data."""
        # Invalid task_id (empty)
        request = CreateTaskRequest(
            task_id="",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )

        with pytest.raises(Exception):  # ValidationError
            await task_tracker.create_task(request)

    @pytest.mark.asyncio
    async def test_update_progress(self, task_tracker):
        """Test updating task progress."""
        # Create task first
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )
        await task_tracker.create_task(request)

        # Update progress
        update_request = UpdateProgressRequest(
            task_id="task-001",
            progress=50.0,
            status="running",
            current_step="step_2",
            message="Processing step 2",
            metadata={"current_operation": "validation"},
        )

        task_data = await task_tracker.update_task_progress(update_request)

        assert task_data["progress"] == 50.0
        assert task_data["status"] == "running"
        assert task_data["current_step"] == "step_2"
        assert task_data["metadata"]["current_operation"] == "validation"

    @pytest.mark.asyncio
    async def test_update_progress_invalid(self, task_tracker):
        """Test updating progress with invalid data."""
        # Invalid progress value
        update_request = UpdateProgressRequest(
            task_id="task-001",
            progress=-10.0,  # Invalid: negative
            status="running",
        )

        with pytest.raises(Exception):  # ValidationError
            await task_tracker.update_task_progress(update_request)

    @pytest.mark.asyncio
    async def test_get_task(self, task_tracker):
        """Test getting task by ID."""
        # Create task
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )
        await task_tracker.create_task(request)

        # Get task
        task_data = await task_tracker.get_task("task-001")

        assert task_data["task_id"] == "task-001"
        assert task_data["user_id"] == "user-001"
        assert task_data["task_type"] == "skill_creation"
        assert task_data["task_name"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_nonexistent_task(self, task_tracker):
        """Test getting nonexistent task."""
        with pytest.raises(TaskNotFoundError):
            await task_tracker.get_task("nonexistent")

    @pytest.mark.asyncio
    async def test_get_user_tasks(self, task_tracker):
        """Test getting tasks for a user."""
        # Create multiple tasks for same user
        for i in range(3):
            request = CreateTaskRequest(
                task_id=f"task-{i:03d}",
                user_id="user-001",
                task_type="skill_creation",
                task_name=f"Task {i}",
            )
            await task_tracker.create_task(request)

        # Create task for different user
        request = CreateTaskRequest(
            task_id="task-user2",
            user_id="user-002",
            task_type="skill_creation",
            task_name="Other User Task",
        )
        await task_tracker.create_task(request)

        # Get tasks for user-001
        tasks = await task_tracker.get_user_tasks("user-001")

        assert len(tasks) == 3
        for task in tasks:
            assert task["user_id"] == "user-001"
            assert task["task_type"] == "skill_creation"

    @pytest.mark.asyncio
    async def test_get_user_tasks_with_filter(self, task_tracker):
        """Test getting tasks with status filter."""
        # Create tasks with different statuses
        await task_tracker.create_task(
            CreateTaskRequest(
                task_id="task-001",
                user_id="user-001",
                task_type="skill_creation",
                task_name="Task 1",
            )
        )

        await task_tracker.create_task(
            CreateTaskRequest(
                task_id="task-002",
                user_id="user-001",
                task_type="skill_creation",
                task_name="Task 2",
            )
        )

        # Update one task to running
        await task_tracker.update_task_progress(
            UpdateProgressRequest(
                task_id="task-001",
                progress=50.0,
                status="running",
            )
        )

        # Get only running tasks
        running_tasks = await task_tracker.get_user_tasks(
            "user-001",
            status_filter=["running"],
        )

        assert len(running_tasks) == 1
        assert running_tasks[0]["task_id"] == "task-001"
        assert running_tasks[0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, task_tracker):
        """Test getting tasks by status."""
        # Create tasks with different statuses
        await task_tracker.create_task(
            CreateTaskRequest(
                task_id="task-001",
                user_id="user-001",
                task_type="skill_creation",
                task_name="Task 1",
            )
        )

        await task_tracker.create_task(
            CreateTaskRequest(
                task_id="task-002",
                user_id="user-002",
                task_type="skill_creation",
                task_name="Task 2",
            )
        )

        # Update one task
        await task_tracker.update_task_progress(
            UpdateProgressRequest(
                task_id="task-001",
                progress=100.0,
                status="completed",
            )
        )

        # Get completed tasks
        completed_tasks = await task_tracker.get_tasks_by_status("completed")

        assert len(completed_tasks) == 1
        assert completed_tasks[0]["task_id"] == "task-001"
        assert completed_tasks[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_delete_task(self, task_tracker):
        """Test deleting a task."""
        # Create task
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )
        await task_tracker.create_task(request)

        # Verify task exists
        task = await task_tracker.get_task("task-001")
        assert task["task_id"] == "task-001"

        # Delete task
        result = await task_tracker.delete_task("task-001")

        assert result is True

        # Verify task is deleted
        with pytest.raises(TaskNotFoundError):
            await task_tracker.get_task("task-001")

    @pytest.mark.asyncio
    async def test_get_progress_statistics(self, task_tracker):
        """Test getting progress statistics."""
        # Create tasks
        for i in range(5):
            await task_tracker.create_task(
                CreateTaskRequest(
                    task_id=f"task-{i:03d}",
                    user_id="user-001",
                    task_type="skill_creation",
                    task_name=f"Task {i}",
                )
            )

        # Update some tasks
        await task_tracker.update_task_progress(
            UpdateProgressRequest(
                task_id="task-000",
                progress=100.0,
                status="completed",
            )
        )

        await task_tracker.update_task_progress(
            UpdateProgressRequest(
                task_id="task-001",
                progress=50.0,
                status="running",
            )
        )

        # Get statistics
        stats = await task_tracker.get_progress_statistics()

        assert stats["total_tasks"] == 5
        assert stats["completed_tasks"] == 1
        assert stats["running_tasks"] == 1
        assert stats["failed_tasks"] == 0
        assert stats["paused_tasks"] == 0
        assert stats["success_rate"] == 20.0  # 1/5 = 20%
        assert 0 <= stats["average_progress"] <= 100

    @pytest.mark.asyncio
    async def test_aggregate_progress(self, task_tracker):
        """Test aggregating progress across multiple tasks."""
        # Create tasks
        for i in range(3):
            await task_tracker.create_task(
                CreateTaskRequest(
                    task_id=f"task-{i:03d}",
                    user_id="user-001",
                    task_type="skill_creation",
                    task_name=f"Task {i}",
                )
            )

        # Update tasks with different progress
        for i, progress in enumerate([25, 50, 75]):
            await task_tracker.update_task_progress(
                UpdateProgressRequest(
                    task_id=f"task-{i:03d}",
                    progress=progress,
                    status="running",
                )
            )

        # Aggregate progress
        task_ids = ["task-000", "task-001", "task-002"]
        aggregation = await task_tracker.aggregate_progress(task_ids)

        assert aggregation["total_tasks"] == 3
        assert aggregation["average_progress"] == 50.0  # (25+50+75)/3
        assert len(aggregation["tasks"]) == 3

    @pytest.mark.asyncio
    async def test_update_handler_registration(self, task_tracker):
        """Test registering and unregistering update handlers."""
        handler_called = False

        async def update_handler(event_type: str, task_data: Dict[str, Any]):
            nonlocal handler_called
            handler_called = True

        # Register handler
        task_tracker.register_update_handler(update_handler)

        # Create task (should trigger handler)
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )
        await task_tracker.create_task(request)

        # Handler should have been called
        assert handler_called is True

        # Unregister handler
        task_tracker.unregister_update_handler(update_handler)
        handler_called = False

        # Update task (handler should not be called)
        await task_tracker.update_task_progress(
            UpdateProgressRequest(
                task_id="task-001",
                progress=50.0,
                status="running",
            )
        )

        # Handler should not have been called
        assert handler_called is False

    def test_get_statistics(self, task_tracker):
        """Test getting task tracker statistics."""
        stats = task_tracker.get_statistics()

        assert "tasks_created" in stats
        assert "tasks_updated" in stats
        assert "tasks_completed" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "cached_tasks" in stats
        assert "active_handlers" in stats


class TestProgressManager:
    """Test cases for ProgressManager."""

    @pytest.fixture
    def progress_manager(self):
        """Create ProgressManager instance for testing."""
        return ProgressManager(db_session=None)

    def test_progress_manager_initialization(self, progress_manager):
        """Test ProgressManager initialization."""
        assert progress_manager.db_session is None
        assert len(progress_manager.active_tasks) == 0
        assert len(progress_manager.task_update_handlers) == 0

    @pytest.mark.asyncio
    async def test_start_and_stop(self, progress_manager):
        """Test starting and stopping progress manager."""
        await progress_manager.start()
        assert progress_manager._is_running is True
        assert progress_manager._cleanup_task is not None

        await progress_manager.stop()
        assert progress_manager._is_running is False

    @pytest.mark.asyncio
    async def test_create_task_progress(self, progress_manager):
        """Test creating task progress."""
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
            description="Testing progress manager",
            estimated_duration=300,
            total_steps=5,
        )

        result = await progress_manager.create_task_progress(request)

        assert result is not None
        assert "task_id" in result
        assert result["task_id"] == "task-001"

    @pytest.mark.asyncio
    async def test_update_task_progress(self, progress_manager):
        """Test updating task progress."""
        # Create task first
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )
        await progress_manager.create_task_progress(request)

        # Update progress
        update_request = UpdateProgressRequest(
            task_id="task-001",
            progress=50.0,
            status="running",
            current_step="step_2",
            message="Processing...",
        )

        result = await progress_manager.update_task_progress(update_request)

        assert result is not None
        assert result["progress"] == 50.0
        assert result["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_task_progress(self, progress_manager):
        """Test getting task progress."""
        # Create task
        request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
        )
        await progress_manager.create_task_progress(request)

        # Get task progress
        result = await progress_manager.get_task_progress("task-001")

        assert result is not None
        assert result["task_id"] == "task-001"
        assert result["user_id"] == "user-001"

    @pytest.mark.asyncio
    async def test_get_task_statistics(self, progress_manager):
        """Test getting task statistics."""
        # Create some tasks
        for i in range(3):
            request = CreateTaskRequest(
                task_id=f"task-{i:03d}",
                user_id="user-001",
                task_type="skill_creation",
                task_name=f"Task {i}",
            )
            await progress_manager.create_task_progress(request)

        # Get statistics
        stats = await progress_manager.get_task_statistics()

        assert "total" in stats
        assert "completed" in stats
        assert "running" in stats
        assert "failed" in stats
        assert "success_rate" in stats

    def test_register_update_handler(self, progress_manager):
        """Test registering update handler."""
        handler_called = False

        def update_handler(event_type: str, task: Dict[str, Any]):
            nonlocal handler_called
            handler_called = True

        progress_manager.register_update_handler(update_handler)
        assert len(progress_manager.task_update_handlers) == 1

        progress_manager.unregister_update_handler(update_handler)
        assert len(progress_manager.task_update_handlers) == 0


class TestTrackerIntegration:
    """Integration tests for task tracking system."""

    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self):
        """Test complete task lifecycle."""
        tracker = TaskTracker()

        # Create task
        create_request = CreateTaskRequest(
            task_id="task-001",
            user_id="user-001",
            task_type="skill_creation",
            task_name="Test Task",
            description="Testing complete lifecycle",
            estimated_duration=600,
            total_steps=6,
        )

        task = await tracker.create_task(create_request)
        assert task["task_id"] == "task-001"
        assert task["progress"] == 0.0
        assert task["status"] == "pending"

        # Update progress multiple times
        for i in range(1, 6):
            progress = (i / 5) * 100
            update_request = UpdateProgressRequest(
                task_id="task-001",
                progress=progress,
                status="running",
                current_step=f"step_{i}",
                message=f"Processing step {i}",
            )

            updated_task = await tracker.update_task_progress(update_request)
            assert updated_task["progress"] == progress
            assert updated_task["current_step"] == f"step_{i}"

        # Complete task
        complete_request = UpdateProgressRequest(
            task_id="task-001",
            progress=100.0,
            status="completed",
            current_step="step_6",
            message="Task completed successfully",
        )

        completed_task = await tracker.update_task_progress(complete_request)
        assert completed_task["progress"] == 100.0
        assert completed_task["status"] == "completed"

        # Verify final task
        final_task = await tracker.get_task("task-001")
        assert final_task["progress"] == 100.0
        assert final_task["status"] == "completed"

    @pytest.mark.asyncio
    async def test_multiple_users(self):
        """Test tracking tasks for multiple users."""
        tracker = TaskTracker()

        # Create tasks for different users
        users = ["user-001", "user-002", "user-003"]
        for user_id in users:
            for i in range(2):
                request = CreateTaskRequest(
                    task_id=f"{user_id}-task-{i:03d}",
                    user_id=user_id,
                    task_type="skill_creation",
                    task_name=f"{user_id} Task {i}",
                )
                await tracker.create_task(request)

        # Get tasks for each user
        for user_id in users:
            tasks = await tracker.get_user_tasks(user_id)
            assert len(tasks) == 2
            for task in tasks:
                assert task["user_id"] == user_id

    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test cache performance with multiple operations."""
        tracker = TaskTracker(cache_size=100, cache_ttl=10)

        # Create many tasks
        for i in range(50):
            request = CreateTaskRequest(
                task_id=f"task-{i:03d}",
                user_id="user-001",
                task_type="skill_creation",
                task_name=f"Task {i}",
            )
            await tracker.create_task(request)

        # Get tasks (should use cache)
        for i in range(50):
            task = await tracker.get_task(f"task-{i:03d}")
            assert task["task_id"] == f"task-{i:03d}"

        # Check statistics
        stats = tracker.get_statistics()
        assert stats["cache_hits"] > 0
        assert stats["cached_tasks"] == 50

    @pytest.mark.asyncio
    async def test_progress_aggregation(self):
        """Test progress aggregation across tasks."""
        tracker = TaskTracker()

        # Create tasks for same type
        task_type = "batch_processing"
        task_ids = []
        for i in range(5):
            request = CreateTaskRequest(
                task_id=f"batch-task-{i:03d}",
                user_id="user-001",
                task_type=task_type,
                task_name=f"Batch Task {i}",
            )
            await tracker.create_task(request)
            task_ids.append(f"batch-task-{i:03d}")

        # Update with different progress
        for i, progress in enumerate([20, 40, 60, 80, 100]):
            await tracker.update_task_progress(
                UpdateProgressRequest(
                    task_id=f"batch-task-{i:03d}",
                    progress=progress,
                    status="running" if progress < 100 else "completed",
                )
            )

        # Aggregate progress
        aggregation = await tracker.aggregate_progress(task_ids)

        assert aggregation["total_tasks"] == 5
        assert aggregation["average_progress"] == 60.0  # Average of (20,40,60,80,100)
        assert aggregation["completed_count"] == 1
        assert aggregation["running_count"] == 4

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various scenarios."""
        tracker = TaskTracker()

        # Test getting nonexistent task
        with pytest.raises(TaskNotFoundError):
            await tracker.get_task("nonexistent")

        # Test updating nonexistent task
        with pytest.raises(TaskNotFoundError):
            await tracker.update_task_progress(
                UpdateProgressRequest(
                    task_id="nonexistent",
                    progress=50.0,
                    status="running",
                )
            )

        # Test creating task with invalid data
        with pytest.raises(Exception):  # ValidationError
            await tracker.create_task(
                CreateTaskRequest(
                    task_id="invalid@task",  # Invalid characters
                    user_id="user-001",
                    task_type="skill_creation",
                    task_name="Test Task",
                )
            )

    @pytest.mark.asyncio
    async def test_concurrent_updates(self):
        """Test concurrent task updates."""
        tracker = TaskTracker()

        # Create task
        await tracker.create_task(
            CreateTaskRequest(
                task_id="task-001",
                user_id="user-001",
                task_type="skill_creation",
                task_name="Concurrent Task",
            )
        )

        # Perform concurrent updates
        async def update_task(progress: float):
            return await tracker.update_task_progress(
                UpdateProgressRequest(
                    task_id="task-001",
                    progress=progress,
                    status="running",
                )
            )

        # Run concurrent updates
        tasks = [update_task(i * 10) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)

        # All updates should succeed
        assert len(results) == 10
        for result in results:
            assert result["task_id"] == "task-001"

        # Final progress should be 100%
        final_task = await tracker.get_task("task-001")
        assert final_task["progress"] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
