"""Monitoring-related Celery tasks.

This module contains Celery tasks for asynchronous monitoring operations.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from celery import current_task, periodic_task
from celery.schedules import crontab

from ...manager import PlatformManager

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


# Monitoring Tasks

def check_platform_health_task(
    platform_id: str,
    check_interval: Optional[int] = None
) -> Dict[str, Any]:
    """Check health of a specific platform asynchronously.

    Args:
        platform_id: Platform ID to check
        check_interval: Optional check interval override

    Returns:
        Health check result
    """
    try:
        # Update task state
        update_task_state('STARTED', {
            'status': 'Starting platform health check',
            'platform_id': platform_id
        })

        # Get platform manager
        manager = get_platform_manager()

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Step 1: Initialize health check
            update_task_state('PROGRESS', {
                'status': 'Initializing health check',
                'step': 'initialization',
                'platform_id': platform_id
            })

            # Step 2: Perform health check
            update_task_state('PROGRESS', {
                'status': 'Performing health check',
                'step': 'health_check',
                'platform_id': platform_id
            })

            snapshot = loop.run_until_complete(
                manager.monitor.check_platform_health(platform_id)
            )

            # Step 3: Process health results
            update_task_state('PROGRESS', {
                'status': 'Processing health results',
                'step': 'processing',
                'platform_id': platform_id
            })

            # Extract health metrics
            health_status = snapshot.status.value
            is_healthy = snapshot.is_healthy
            consecutive_failures = snapshot.consecutive_failures
            last_check = snapshot.last_check

            # Count check results
            check_count = len(snapshot.health_checks)
            passed_checks = sum(1 for check in snapshot.health_checks if check.is_healthy)
            failed_checks = check_count - passed_checks

            # Generate health summary
            health_summary = {
                'platform_id': platform_id,
                'status': health_status,
                'is_healthy': is_healthy,
                'consecutive_failures': consecutive_failures,
                'last_check': last_check.isoformat(),
                'check_count': check_count,
                'passed_checks': passed_checks,
                'failed_checks': failed_checks,
                'success_rate': (passed_checks / check_count * 100) if check_count > 0 else 0
            }

            # Add individual check results
            check_results = []
            for check in snapshot.health_checks:
                check_results.append({
                    'name': check.status.value,
                    'message': check.message,
                    'response_time_ms': check.response_time_ms,
                    'is_healthy': check.is_healthy,
                    'details': check.details
                })

            # Step 4: Complete health check
            update_task_state('SUCCESS', {
                'status': 'Health check completed',
                'step': 'completion',
                'summary': health_summary,
                'check_results': check_results
            })

            return {
                'success': True,
                'health_summary': health_summary,
                'check_results': check_results,
                'snapshot': {
                    'platform_id': snapshot.platform_id,
                    'status': snapshot.status.value,
                    'is_healthy': snapshot.is_healthy,
                    'last_check': snapshot.last_check.isoformat(),
                    'consecutive_failures': snapshot.consecutive_failures
                }
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Platform health check failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'platform_id': platform_id
        })

        return {
            'success': False,
            'error': str(e),
            'platform_id': platform_id
        }


def check_all_platforms_health_task(
    check_interval: Optional[int] = None
) -> Dict[str, Any]:
    """Check health of all platforms asynchronously.

    Args:
        check_interval: Optional check interval override

    Returns:
        All platforms health check result
    """
    try:
        # Update task state
        update_task_state('STARTED', {
            'status': 'Starting all platforms health check'
        })

        # Get platform manager
        manager = get_platform_manager()

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Step 1: Initialize health check
            update_task_state('PROGRESS', {
                'status': 'Initializing health check for all platforms',
                'step': 'initialization'
            })

            # Get all registered platforms
            all_platforms = manager.registry.get_registered_platforms()

            if not all_platforms:
                return {
                    'success': True,
                    'message': 'No platforms registered',
                    'total_platforms': 0,
                    'healthy_platforms': 0,
                    'unhealthy_platforms': 0
                }

            # Step 2: Perform health checks
            update_task_state('PROGRESS', {
                'status': 'Performing health checks',
                'step': 'health_checks',
                'total_platforms': len(all_platforms)
            })

            health_snapshots = loop.run_until_complete(
                manager.monitor.check_all_platforms_health()
            )

            # Step 3: Process results
            update_task_state('PROGRESS', {
                'status': 'Processing health results',
                'step': 'processing',
                'total_platforms': len(all_platforms)
            })

            # Aggregate results
            total_platforms = len(all_platforms)
            healthy_platforms = 0
            degraded_platforms = 0
            unhealthy_platforms = 0
            offline_platforms = 0

            platform_results = []
            overall_health_score = 0

            for platform_id, snapshot in health_snapshots.items():
                status = snapshot.status.value
                is_healthy = snapshot.is_healthy
                check_count = len(snapshot.health_checks)
                passed_checks = sum(1 for check in snapshot.health_checks if check.is_healthy)

                # Count by status
                if status == 'healthy':
                    healthy_platforms += 1
                elif status == 'degraded':
                    degraded_platforms += 1
                elif status == 'unhealthy':
                    unhealthy_platforms += 1
                elif status == 'offline':
                    offline_platforms += 1

                # Calculate platform health score
                platform_score = (passed_checks / check_count * 100) if check_count > 0 else 0
                overall_health_score += platform_score

                platform_result = {
                    'platform_id': platform_id,
                    'status': status,
                    'is_healthy': is_healthy,
                    'consecutive_failures': snapshot.consecutive_failures,
                    'last_check': snapshot.last_check.isoformat(),
                    'health_score': platform_score,
                    'check_count': check_count,
                    'passed_checks': passed_checks
                }

                platform_results.append(platform_result)

            # Calculate overall health score
            overall_health_score = overall_health_score / total_platforms if total_platforms > 0 else 0

            # Generate summary
            summary = {
                'total_platforms': total_platforms,
                'healthy_platforms': healthy_platforms,
                'degraded_platforms': degraded_platforms,
                'unhealthy_platforms': unhealthy_platforms,
                'offline_platforms': offline_platforms,
                'overall_health_score': overall_health_score,
                'health_percentage': (healthy_platforms / total_platforms * 100) if total_platforms > 0 else 0
            }

            # Step 4: Complete health check
            update_task_state('SUCCESS', {
                'status': 'All platforms health check completed',
                'step': 'completion',
                'summary': summary
            })

            return {
                'success': True,
                'summary': summary,
                'platform_results': platform_results,
                'health_snapshots': {
                    platform_id: {
                        'status': snapshot.status.value,
                        'is_healthy': snapshot.is_healthy,
                        'last_check': snapshot.last_check.isoformat(),
                        'consecutive_failures': snapshot.consecutive_failures
                    }
                    for platform_id, snapshot in health_snapshots.items()
                }
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"All platforms health check failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e)
        })

        return {
            'success': False,
            'error': str(e)
        }


def cleanup_old_alerts_task(
    older_than_hours: int = 168
) -> Dict[str, Any]:
    """Cleanup old alerts asynchronously.

    Args:
        older_than_hours: Remove alerts older than this many hours

    Returns:
        Cleanup result
    """
    try:
        # Update task state
        update_task_state('STARTED', {
            'status': 'Starting alert cleanup',
            'older_than_hours': older_than_hours
        })

        # Get platform manager
        manager = get_platform_manager()

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get current alert count before cleanup
            before_count = len(manager.monitor.get_active_alerts())

            # Perform cleanup
            removed_count = loop.run_until_complete(
                manager.monitor.cleanup_old_alerts(older_than_hours)
            )

            # Get alert count after cleanup
            after_count = len(manager.monitor.get_active_alerts())

            update_task_state('SUCCESS', {
                'status': 'Alert cleanup completed',
                'removed_count': removed_count,
                'before_count': before_count,
                'after_count': after_count
            })

            return {
                'success': True,
                'removed_count': removed_count,
                'before_count': before_count,
                'after_count': after_count,
                'older_than_hours': older_than_hours
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Alert cleanup failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e)
        })

        return {
            'success': False,
            'error': str(e)
        }


# Periodic Tasks (automatically scheduled)

@periodic_task(
    run_every=crontab(minute='*/5'),  # Every 5 minutes
    name='platform.monitor.health_check',
    queue='platform_monitoring'
)
def periodic_health_check():
    """Periodic health check for all platforms."""
    logger.info("Starting periodic health check")
    try:
        result = check_all_platforms_health_task()
        if result['success']:
            logger.info(f"Periodic health check completed: {result['summary']}")
        else:
            logger.error(f"Periodic health check failed: {result['error']}")
    except Exception as e:
        logger.error(f"Periodic health check error: {str(e)}")


@periodic_task(
    run_every=crontab(hour='2', minute='0'),  # Daily at 2 AM
    name='platform.monitor.cleanup_alerts',
    queue='platform_monitoring'
)
def periodic_cleanup_alerts():
    """Periodic cleanup of old alerts."""
    logger.info("Starting periodic alert cleanup")
    try:
        result = cleanup_old_alerts_task(older_than_hours=168)  # 7 days
        if result['success']:
            logger.info(f"Periodic alert cleanup completed: {result['removed_count']} alerts removed")
        else:
            logger.error(f"Periodic alert cleanup failed: {result['error']}")
    except Exception as e:
        logger.error(f"Periodic alert cleanup error: {str(e)}")


@periodic_task(
    run_every=crontab(minute='*/10'),  # Every 10 minutes
    name='platform.monitor.deployment_status',
    queue='platform_monitoring'
)
def periodic_deployment_status_check():
    """Periodic check of deployment status."""
    logger.info("Starting periodic deployment status check")
    try:
        manager = get_platform_manager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get active deployments
            active_deployments = loop.run_until_complete(
                manager.deployer.list_deployments(
                    status=None,  # All statuses
                    limit=100
                )
            )

            # Check for stuck deployments
            stuck_deployments = []
            for deployment in active_deployments:
                created_at = datetime.fromisoformat(deployment['created_at'].replace('Z', '+00:00'))
                duration = (datetime.utcnow() - created_at).total_seconds()

                # Check if deployment has been running for more than 30 minutes
                if duration > 1800 and deployment['status'] in ['pending', 'validating', 'converting', 'deploying']:
                    stuck_deployments.append(deployment)

            if stuck_deployments:
                logger.warning(f"Found {len(stuck_deployments)} stuck deployments")

            return {
                'success': True,
                'total_active': len(active_deployments),
                'stuck_deployments': len(stuck_deployments),
                'stuck_details': stuck_deployments
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Periodic deployment status check error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# Task configuration
HEALTH_CHECK_TASK_CONFIG = {
    'queue': 'platform_monitoring',
    'routing_key': 'platform.monitoring.health_check',
    'priority': 5,
    'time_limit': 300,  # 5 minutes
    'soft_time_limit': 240,  # 4 minutes
    'retry_backoff': True,
    'max_retries': 3,
    'ignore_result': False,
}

ALL_PLATFORMS_CHECK_TASK_CONFIG = {
    'queue': 'platform_monitoring',
    'routing_key': 'platform.monitoring.all_platforms',
    'priority': 4,
    'time_limit': 600,  # 10 minutes
    'soft_time_limit': 540,  # 9 minutes
    'retry_backoff': True,
    'max_retries': 2,
    'ignore_result': False,
}

ALERT_CLEANUP_TASK_CONFIG = {
    'queue': 'platform_monitoring',
    'routing_key': 'platform.monitoring.alert_cleanup',
    'priority': 2,
    'time_limit': 180,  # 3 minutes
    'soft_time_limit': 120,  # 2 minutes
    'retry_backoff': True,
    'max_retries': 1,
    'ignore_result': True,
}