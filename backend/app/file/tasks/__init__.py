"""File Management Celery Tasks.

This module contains Celery tasks for file management operations including
batch processing, backup operations, and cleanup tasks.
"""

from celery import Celery
import logging

logger = logging.getLogger(__name__)

# Create Celery app
celery_app = Celery(
    "file_management_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=[
        "app.file.tasks.batch_tasks",
        "app.file.tasks.backup_tasks",
        "app.file.tasks.cleanup_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.file.tasks.batch_tasks.*": {"queue": "batch_operations"},
        "app.file.tasks.backup_tasks.*": {"queue": "backup_operations"},
        "app.file.tasks.cleanup_tasks.*": {"queue": "cleanup_operations"},
    },
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_max_tasks_per_child=1000,
    worker_prefetch_multiplier=1,
)

# Task state tracking
task_states = {}

# Task callback registry
task_callbacks = {}


@celery_app.task(bind=True, max_retries=3)
def update_task_state(self, task_id: str, state: str, **kwargs):
    """Update task state.

    Args:
        task_id: Task ID
        state: Task state
        **kwargs: Additional state data
    """
    task_states[task_id] = {
        "state": state,
        "timestamp": self.request.id,
        "data": kwargs,
    }

    # Call registered callbacks
    if task_id in task_callbacks:
        for callback in task_callbacks[task_id]:
            try:
                callback(task_id, state, **kwargs)
            except Exception as e:
                logger.error(f"Task callback failed: {e}")


def register_task_callback(task_id: str, callback):
    """Register a callback for task completion.

    Args:
        task_id: Task ID
        callback: Callback function
    """
    if task_id not in task_callbacks:
        task_callbacks[task_id] = []
    task_callbacks[task_id].append(callback)


def get_task_state(task_id: str):
    """Get task state.

    Args:
        task_id: Task ID

    Returns:
        Task state or None
    """
    return task_states.get(task_id)


def cleanup_task_state(task_id: str):
    """Clean up task state.

    Args:
        task_id: Task ID
    """
    task_states.pop(task_id, None)
    task_callbacks.pop(task_id, None)


if __name__ == "__main__":
    celery_app.start()
