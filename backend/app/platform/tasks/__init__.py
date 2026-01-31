"""Platform tasks package.

This package contains Celery tasks for asynchronous platform operations.
"""

from .deployment_tasks import (
    deploy_skill_task,
    cancel_deployment_task,
    retry_deployment_task,
    batch_deploy_skills_task,
)

from .validation_tasks import (
    validate_compatibility_task,
    batch_validate_compatibility_task,
)

from .monitoring_tasks import (
    check_platform_health_task,
    check_all_platforms_health_task,
    cleanup_old_alerts_task,
)

__all__ = [
    # Deployment tasks
    "deploy_skill_task",
    "cancel_deployment_task",
    "retry_deployment_task",
    "batch_deploy_skills_task",

    # Validation tasks
    "validate_compatibility_task",
    "batch_validate_compatibility_task",

    # Monitoring tasks
    "check_platform_health_task",
    "check_all_platforms_health_task",
    "cleanup_old_alerts_task",
]