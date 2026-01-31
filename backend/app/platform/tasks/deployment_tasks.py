"""Deployment-related Celery tasks.

This module contains Celery tasks for asynchronous deployment operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from celery import current_task
from celery.exceptions import Retry

from ...manager import PlatformManager
from ...deployer import DeploymentPriority

logger = logging.getLogger(__name__)


# Global platform manager instance
_platform_manager = None


def get_platform_manager():
    """Get or create platform manager instance."""
    global _platform_manager
    if _platform_manager is None:
        _platform_manager = PlatformManager()
    return _platform_manager


def update_task_state(state: str, meta: Dict[str, Any] = None):
    """Update Celery task state with progress information.

    Args:
        state: Task state (PENDING, STARTED, SUCCESS, FAILURE, etc.)
        meta: Additional metadata for the state
    """
    if current_task:
        current_task.update_state(
            state=state,
            meta=meta or {}
        )


# Deployment Tasks

def deploy_skill_task(
    skill_data: Dict[str, Any],
    target_platforms: List[str],
    source_format: Optional[str] = None,
    target_formats: Optional[Dict[str, str]] = None,
    deployment_config: Optional[Dict[str, Any]] = None,
    validate_compatibility: bool = True,
    async_mode: bool = True,
    priority: int = DeploymentPriority.NORMAL.value,
    max_retries: int = 3
) -> Dict[str, Any]:
    """Deploy skill to platforms asynchronously.

    Args:
        skill_data: Skill data to deploy
        target_platforms: List of target platforms
        source_format: Source format
        target_formats: Target formats mapping
        deployment_config: Deployment configuration
        validate_compatibility: Whether to validate compatibility
        async_mode: Whether to use async mode
        priority: Deployment priority
        max_retries: Maximum retry attempts

    Returns:
        Deployment result dictionary
    """
    try:
        # Update task state
        update_task_state('STARTED', {
            'status': 'Initializing deployment',
            'skill_name': skill_data.get('name', 'Unknown'),
            'target_platforms': target_platforms
        })

        # Get platform manager
        manager = get_platform_manager()

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Step 1: Initialize deployment
            update_task_state('PROGRESS', {
                'status': 'Preparing deployment',
                'step': 'initialization'
            })

            # Step 2: Validate compatibility if requested
            if validate_compatibility:
                update_task_state('PROGRESS', {
                    'status': 'Validating compatibility',
                    'step': 'validation'
                })

                compatibility_report = loop.run_until_complete(
                    manager.validate_skill_compatibility(
                        skill_data=skill_data,
                        target_platforms=target_platforms
                    )
                )

                if not compatibility_report['overall_compatible']:
                    return {
                        'success': False,
                        'error': 'Skill compatibility validation failed',
                        'incompatible_platforms': compatibility_report['incompatible_platforms'],
                        'compatibility_report': compatibility_report
                    }

            # Step 3: Deploy skill
            update_task_state('PROGRESS', {
                'status': 'Starting deployment',
                'step': 'deployment'
            })

            deployment_tasks = loop.run_until_complete(
                manager.deploy_skill(
                    skill_data=skill_data,
                    target_platforms=target_platforms,
                    source_format=source_format,
                    target_formats=target_formats,
                    deployment_config=deployment_config,
                    validate_compatibility=False,  # Already validated
                    async_mode=async_mode
                )
            )

            # Step 4: Monitor deployment progress
            deployment_results = []
            deployment_ids = []

            if isinstance(deployment_tasks, list):
                for task in deployment_tasks:
                    deployment_ids.append(task.deployment_id)
            else:
                deployment_ids.append(deployment_tasks.deployment_id)

            # Monitor deployments
            update_task_state('PROGRESS', {
                'status': 'Monitoring deployment progress',
                'step': 'monitoring',
                'deployment_ids': deployment_ids
            })

            for deployment_id in deployment_ids:
                result = monitor_deployment_progress(loop, manager, deployment_id)
                deployment_results.append(result)

            # Step 5: Complete deployment
            update_task_state('PROGRESS', {
                'status': 'Deployment completed',
                'step': 'completion',
                'deployment_results': deployment_results
            })

            return {
                'success': True,
                'deployment_ids': deployment_ids,
                'results': deployment_results,
                'skill_name': skill_data.get('name', 'Unknown'),
                'target_platforms': target_platforms
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Deployment task failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'skill_name': skill_data.get('name', 'Unknown')
        })

        return {
            'success': False,
            'error': str(e),
            'skill_name': skill_data.get('name', 'Unknown')
        }


def cancel_deployment_task(deployment_id: str, force: bool = False) -> Dict[str, Any]:
    """Cancel deployment asynchronously.

    Args:
        deployment_id: Deployment ID to cancel
        force: Whether to force cancellation

    Returns:
        Cancellation result
    """
    try:
        update_task_state('STARTED', {
            'status': 'Cancelling deployment',
            'deployment_id': deployment_id
        })

        manager = get_platform_manager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            success = loop.run_until_complete(
                manager.cancel_deployment(deployment_id, force=force)
            )

            update_task_state('SUCCESS', {
                'success': success,
                'deployment_id': deployment_id,
                'cancelled': success
            })

            return {
                'success': success,
                'deployment_id': deployment_id,
                'cancelled': success
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Deployment cancellation failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'deployment_id': deployment_id
        })

        return {
            'success': False,
            'error': str(e),
            'deployment_id': deployment_id
        }


def retry_deployment_task(
    deployment_id: str,
    new_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Retry deployment asynchronously.

    Args:
        deployment_id: Original deployment ID
        new_config: New deployment configuration

    Returns:
        Retry result
    """
    try:
        update_task_state('STARTED', {
            'status': 'Retrying deployment',
            'original_deployment_id': deployment_id
        })

        manager = get_platform_manager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            new_task = loop.run_until_complete(
                manager.retry_deployment(deployment_id, new_config=new_config)
            )

            if not new_task:
                raise Exception("Deployment cannot be retried")

            # Monitor the new deployment
            result = monitor_deployment_progress(loop, manager, new_task.deployment_id)

            update_task_state('SUCCESS', {
                'success': True,
                'original_deployment_id': deployment_id,
                'new_deployment_id': new_task.deployment_id,
                'result': result
            })

            return {
                'success': True,
                'original_deployment_id': deployment_id,
                'new_deployment_id': new_task.deployment_id,
                'result': result
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Deployment retry failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'original_deployment_id': deployment_id
        })

        return {
            'success': False,
            'error': str(e),
            'original_deployment_id': deployment_id
        }


def batch_deploy_skills_task(
    deployments: List[Dict[str, Any]],
    max_concurrent: int = 5,
    wait_for_all: bool = True
) -> Dict[str, Any]:
    """Batch deploy multiple skills asynchronously.

    Args:
        deployments: List of deployment requests
        max_concurrent: Maximum concurrent deployments
        wait_for_all: Whether to wait for all deployments

    Returns:
        Batch deployment result
    """
    try:
        update_task_state('STARTED', {
            'status': 'Starting batch deployment',
            'total_deployments': len(deployments),
            'max_concurrent': max_concurrent
        })

        manager = get_platform_manager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Prepare batch deployments
            deployment_requests = []
            for i, deployment in enumerate(deployments):
                deployment_requests.append({
                    'skill_data': deployment['skill_data'],
                    'target_platform': deployment['target_platform'],
                    'source_format': deployment.get('source_format'),
                    'target_format': deployment.get('target_format'),
                    'priority': deployment.get('priority', DeploymentPriority.NORMAL.value),
                    'max_retries': deployment.get('max_retries', 3),
                    'deployment_config': deployment.get('deployment_config', {})
                })

            # Perform batch deployment
            update_task_state('PROGRESS', {
                'status': 'Executing batch deployment',
                'step': 'deployment'
            })

            results = loop.run_until_complete(
                manager.deployer.deploy_batch(
                    deployments=deployment_requests,
                    max_concurrent=max_concurrent,
                    wait_for_all=wait_for_all
                )
            )

            # Process results
            successful_deployments = []
            failed_deployments = []

            for i, result in enumerate(results):
                if isinstance(result, dict) and result.get('success', True):
                    successful_deployments.append(result)
                else:
                    failed_deployments.append({
                        'index': i,
                        'error': result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                    })

            update_task_state('SUCCESS', {
                'status': 'Batch deployment completed',
                'total_deployments': len(deployments),
                'successful': len(successful_deployments),
                'failed': len(failed_deployments)
            })

            return {
                'success': True,
                'total_deployments': len(deployments),
                'successful_deployments': successful_deployments,
                'failed_deployments': failed_deployments
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Batch deployment failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'total_deployments': len(deployments)
        })

        return {
            'success': False,
            'error': str(e),
            'total_deployments': len(deployments)
        }


def monitor_deployment_progress(
    loop: asyncio.AbstractEventLoop,
    manager: PlatformManager,
    deployment_id: str,
    check_interval: int = 5,
    max_checks: int = 60
) -> Dict[str, Any]:
    """Monitor deployment progress.

    Args:
        loop: Event loop
        manager: Platform manager
        deployment_id: Deployment ID to monitor
        check_interval: Check interval in seconds
        max_checks: Maximum number of checks

    Returns:
        Final deployment status
    """
    try:
        for check_count in range(max_checks):
            # Get deployment status
            status = loop.run_until_complete(
                manager.get_deployment_status(deployment_id)
            )

            if not status:
                raise Exception(f"Deployment not found: {deployment_id}")

            # Update task state with progress
            update_task_state('PROGRESS', {
                'status': f'Monitoring deployment (check {check_count + 1}/{max_checks})',
                'deployment_id': deployment_id,
                'current_status': status.get('status'),
                'progress': f"{check_count + 1}/{max_checks}"
            })

            # Check if deployment is complete
            deployment_status = status.get('status')

            if deployment_status in ['success', 'failed', 'cancelled']:
                return {
                    'deployment_id': deployment_id,
                    'final_status': deployment_status,
                    'completed_at': status.get('completed_at'),
                    'duration_seconds': status.get('duration_seconds'),
                    'error_message': status.get('error_message')
                }

            # Wait before next check
            loop.run_until_complete(asyncio.sleep(check_interval))

        # Timeout
        return {
            'deployment_id': deployment_id,
            'final_status': 'timeout',
            'error': 'Deployment monitoring timeout'
        }

    except Exception as e:
        logger.error(f"Deployment monitoring failed: {str(e)}")
        return {
            'deployment_id': deployment_id,
            'final_status': 'error',
            'error': str(e)
        }


# Task routing configuration
def get_deployment_queue():
    """Get deployment queue name."""
    return 'platform_deployment'


def get_validation_queue():
    """Get validation queue name."""
    return 'platform_validation'


def get_monitoring_queue():
    """Get monitoring queue name."""
    return 'platform_monitoring'


# Task configuration
DEPLOYMENT_TASK_CONFIG = {
    'queue': get_deployment_queue(),
    'routing_key': 'platform.deployment',
    'priority': 5,
    'time_limit': 1800,  # 30 minutes
    'soft_time_limit': 1500,  # 25 minutes
    'retry_backoff': True,
    'max_retries': 3,
    'ignore_result': False,
    'store_eager_result': False,
}

CANCEL_DEPLOYMENT_TASK_CONFIG = {
    'queue': get_deployment_queue(),
    'routing_key': 'platform.deployment.cancel',
    'priority': 8,
    'time_limit': 300,  # 5 minutes
    'soft_time_limit': 240,  # 4 minutes
    'retry_backoff': True,
    'max_retries': 2,
    'ignore_result': False,
}

RETRY_DEPLOYMENT_TASK_CONFIG = {
    'queue': get_deployment_queue(),
    'routing_key': 'platform.deployment.retry',
    'priority': 6,
    'time_limit': 1800,  # 30 minutes
    'soft_time_limit': 1500,  # 25 minutes
    'retry_backoff': True,
    'max_retries': 3,
    'ignore_result': False,
}

BATCH_DEPLOYMENT_TASK_CONFIG = {
    'queue': get_deployment_queue(),
    'routing_key': 'platform.deployment.batch',
    'priority': 4,
    'time_limit': 3600,  # 1 hour
    'soft_time_limit': 3300,  # 55 minutes
    'retry_backoff': True,
    'max_retries': 2,
    'ignore_result': False,
}