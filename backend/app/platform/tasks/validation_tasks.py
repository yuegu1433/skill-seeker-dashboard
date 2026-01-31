"""Validation-related Celery tasks.

This module contains Celery tasks for asynchronous validation operations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from celery import current_task

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


# Validation Tasks

def validate_compatibility_task(
    skill_data: Dict[str, Any],
    target_platforms: Optional[List[str]] = None,
    validation_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Validate skill compatibility asynchronously.

    Args:
        skill_data: Skill data to validate
        target_platforms: List of target platforms
        validation_config: Validation configuration

    Returns:
        Compatibility validation result
    """
    try:
        # Update task state
        update_task_state('STARTED', {
            'status': 'Starting compatibility validation',
            'skill_name': skill_data.get('name', 'Unknown'),
            'target_platforms': target_platforms
        })

        # Get platform manager
        manager = get_platform_manager()

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Step 1: Initialize validation
            update_task_state('PROGRESS', {
                'status': 'Initializing validation',
                'step': 'initialization'
            })

            # Step 2: Perform compatibility validation
            update_task_state('PROGRESS', {
                'status': 'Validating compatibility',
                'step': 'validation'
            })

            report = loop.run_until_complete(
                manager.validate_skill_compatibility(
                    skill_data=skill_data,
                    target_platforms=target_platforms,
                    validation_config=validation_config
                )
            )

            # Step 3: Process validation results
            update_task_state('PROGRESS', {
                'status': 'Processing validation results',
                'step': 'processing'
            })

            # Extract key metrics
            overall_compatible = report['overall_compatible']
            compatibility_score = report['compatibility_score']
            compatible_platforms = report['compatible_platforms']
            incompatible_platforms = report['incompatible_platforms']

            # Generate summary
            summary = {
                'overall_compatible': overall_compatible,
                'compatibility_score': compatibility_score,
                'compatible_platforms': compatible_platforms,
                'incompatible_platforms': incompatible_platforms,
                'platform_count': len(target_platforms or []),
                'compatible_count': len(compatible_platforms),
                'incompatible_count': len(incompatible_platforms),
                'validation_time': report.get('validation_time', 0)
            }

            # Step 4: Complete validation
            update_task_state('SUCCESS', {
                'status': 'Validation completed',
                'step': 'completion',
                'summary': summary
            })

            return {
                'success': True,
                'summary': summary,
                'detailed_report': report,
                'skill_name': skill_data.get('name', 'Unknown')
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Compatibility validation failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'skill_name': skill_data.get('name', 'Unknown')
        })

        return {
            'success': False,
            'error': str(e),
            'skill_name': skill_data.get('name', 'Unknown')
        }


def batch_validate_compatibility_task(
    skills_data: List[Dict[str, Any]],
    target_platforms: Optional[List[str]] = None,
    max_concurrent: int = 10
) -> Dict[str, Any]:
    """Batch validate multiple skills compatibility asynchronously.

    Args:
        skills_data: List of skill data to validate
        target_platforms: List of target platforms
        max_concurrent: Maximum concurrent validations

    Returns:
        Batch validation result
    """
    try:
        # Update task state
        update_task_state('STARTED', {
            'status': 'Starting batch compatibility validation',
            'total_skills': len(skills_data),
            'target_platforms': target_platforms,
            'max_concurrent': max_concurrent
        })

        # Get platform manager
        manager = get_platform_manager()

        # Create event loop for async operations
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Step 1: Prepare batch validation
            update_task_state('PROGRESS', {
                'status': 'Preparing batch validation',
                'step': 'preparation'
            })

            # Step 2: Perform batch validation
            update_task_state('PROGRESS', {
                'status': 'Executing batch validation',
                'step': 'validation',
                'total_skills': len(skills_data)
            })

            results = loop.run_until_complete(
                manager.validator.validate_batch_compatibility(
                    skills_data=skills_data,
                    target_platforms=target_platforms,
                    max_concurrent=max_concurrent
                )
            )

            # Step 3: Process results
            update_task_state('PROGRESS', {
                'status': 'Processing batch results',
                'step': 'processing'
            })

            # Separate successful and failed validations
            successful_validations = []
            failed_validations = []

            for i, result in enumerate(results):
                if isinstance(result, dict) and result.get('success', True):
                    successful_validations.append(result)
                else:
                    failed_validations.append({
                        'index': i,
                        'skill_name': skills_data[i].get('name', f'Skill {i}'),
                        'error': result.get('error', 'Unknown error') if isinstance(result, dict) else str(result)
                    })

            # Generate batch summary
            batch_summary = {
                'total_skills': len(skills_data),
                'successful_validations': len(successful_validations),
                'failed_validations': len(failed_validations),
                'success_rate': (len(successful_validations) / len(skills_data) * 100) if skills_data else 0
            }

            # Calculate overall compatibility statistics
            compatible_count = 0
            incompatible_count = 0
            total_score = 0

            for result in successful_validations:
                if result.get('overall_compatible', False):
                    compatible_count += 1
                else:
                    incompatible_count += 1

                score = result.get('compatibility_score', 0)
                if isinstance(score, (int, float)):
                    total_score += score

            avg_compatibility_score = total_score / len(successful_validations) if successful_validations else 0

            # Step 4: Complete batch validation
            update_task_state('SUCCESS', {
                'status': 'Batch validation completed',
                'step': 'completion',
                'summary': batch_summary,
                'avg_compatibility_score': avg_compatibility_score
            })

            return {
                'success': True,
                'summary': batch_summary,
                'successful_validations': successful_validations,
                'failed_validations': failed_validations,
                'avg_compatibility_score': avg_compatibility_score,
                'compatible_count': compatible_count,
                'incompatible_count': incompatible_count
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Batch compatibility validation failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'total_skills': len(skills_data)
        })

        return {
            'success': False,
            'error': str(e),
            'total_skills': len(skills_data)
        }


# Format Validation Tasks

def validate_skill_format_task(
    skill_data: Dict[str, Any],
    format_type: str,
    platform_id: Optional[str] = None
) -> Dict[str, Any]:
    """Validate skill format asynchronously.

    Args:
        skill_data: Skill data to validate
        format_type: Format type to validate
        platform_id: Optional platform ID

    Returns:
        Format validation result
    """
    try:
        update_task_state('STARTED', {
            'status': 'Starting format validation',
            'skill_name': skill_data.get('name', 'Unknown'),
            'format_type': format_type,
            'platform_id': platform_id
        })

        manager = get_platform_manager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get platform adapter if specified
            adapter = None
            if platform_id:
                adapter = manager.registry.get_adapter(platform_id)
                if not adapter:
                    raise Exception(f"Platform adapter not found: {platform_id}")

            # Perform validation
            if adapter and hasattr(adapter, 'validate_skill_format'):
                result = loop.run_until_complete(
                    adapter.validate_skill_format(skill_data, format_type)
                )
            else:
                # Use converter validation
                result = loop.run_until_complete(
                    manager.converter.validate_conversion(
                        skill_data,
                        skill_data.get('format', 'json'),
                        format_type,
                        platform_id=platform_id
                    )
                )

            update_task_state('SUCCESS', {
                'status': 'Format validation completed',
                'result': result
            })

            return {
                'success': True,
                'result': result,
                'skill_name': skill_data.get('name', 'Unknown'),
                'format_type': format_type,
                'platform_id': platform_id
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Format validation failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'skill_name': skill_data.get('name', 'Unknown')
        })

        return {
            'success': False,
            'error': str(e),
            'skill_name': skill_data.get('name', 'Unknown')
        }


def check_format_compatibility_task(
    format_type: str,
    target_platforms: List[str]
) -> Dict[str, Any]:
    """Check format compatibility across platforms.

    Args:
        format_type: Format to check
        target_platforms: List of platforms to check

    Returns:
        Format compatibility result
    """
    try:
        update_task_state('STARTED', {
            'status': 'Checking format compatibility',
            'format_type': format_type,
            'target_platforms': target_platforms
        })

        manager = get_platform_manager()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Get all registered platforms
            all_platforms = manager.registry.get_registered_platforms()

            # Check compatibility for each platform
            compatible_platforms = []
            incompatible_platforms = []

            for platform_id in target_platforms:
                if platform_id not in all_platforms:
                    incompatible_platforms.append({
                        'platform_id': platform_id,
                        'reason': 'Platform not registered'
                    })
                    continue

                adapter = manager.registry.get_adapter(platform_id)
                if not adapter:
                    incompatible_platforms.append({
                        'platform_id': platform_id,
                        'reason': 'Platform adapter not available'
                    })
                    continue

                # Check if format is supported
                if format_type in adapter.supported_formats:
                    compatible_platforms.append({
                        'platform_id': platform_id,
                        'supported_formats': adapter.supported_formats
                    })
                else:
                    incompatible_platforms.append({
                        'platform_id': platform_id,
                        'reason': f'Format {format_type} not supported',
                        'supported_formats': adapter.supported_formats
                    })

            compatibility_rate = (
                len(compatible_platforms) / len(target_platforms) * 100
            ) if target_platforms else 0

            update_task_state('SUCCESS', {
                'status': 'Format compatibility check completed',
                'compatibility_rate': compatibility_rate
            })

            return {
                'success': True,
                'format_type': format_type,
                'compatible_platforms': compatible_platforms,
                'incompatible_platforms': incompatible_platforms,
                'compatibility_rate': compatibility_rate,
                'total_platforms': len(target_platforms)
            }

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Format compatibility check failed: {str(e)}")
        update_task_state('FAILURE', {
            'error': str(e),
            'format_type': format_type
        })

        return {
            'success': False,
            'error': str(e),
            'format_type': format_type
        }


# Task configuration
VALIDATION_TASK_CONFIG = {
    'queue': 'platform_validation',
    'routing_key': 'platform.validation',
    'priority': 3,
    'time_limit': 600,  # 10 minutes
    'soft_time_limit': 540,  # 9 minutes
    'retry_backoff': True,
    'max_retries': 3,
    'ignore_result': False,
}

BATCH_VALIDATION_TASK_CONFIG = {
    'queue': 'platform_validation',
    'routing_key': 'platform.validation.batch',
    'priority': 2,
    'time_limit': 1200,  # 20 minutes
    'soft_time_limit': 1080,  # 18 minutes
    'retry_backoff': True,
    'max_retries': 2,
    'ignore_result': False,
}

FORMAT_VALIDATION_TASK_CONFIG = {
    'queue': 'platform_validation',
    'routing_key': 'platform.validation.format',
    'priority': 4,
    'time_limit': 300,  # 5 minutes
    'soft_time_limit': 240,  # 4 minutes
    'retry_backoff': True,
    'max_retries': 2,
    'ignore_result': False,
}