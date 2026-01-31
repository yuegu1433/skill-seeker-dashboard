"""Platform serialization utilities.

This module provides serialization functions for platform operations,
deployment data, and compatibility checks.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal


def serialize_platform(platform) -> Dict[str, Any]:
    """Serialize Platform model to dictionary.

    Args:
        platform: Platform model instance

    Returns:
        Serialized platform data as dictionary
    """
    return {
        'id': str(platform.id),
        'name': platform.name,
        'display_name': platform.display_name,
        'platform_type': platform.platform_type,
        'api_endpoint': platform.api_endpoint,
        'api_version': platform.api_version,
        'authentication_type': platform.authentication_type,
        'supported_formats': platform.supported_formats or [],
        'max_file_size': platform.max_file_size,
        'features': platform.features or {},
        'is_active': platform.is_active,
        'is_healthy': platform.is_healthy,
        'last_health_check': platform.last_health_check.isoformat() if platform.last_health_check else None,
        'configuration': platform.configuration or {},
        'validation_rules': platform.validation_rules or {},
        'conversion_templates': platform.conversion_templates or {},
        'created_at': platform.created_at.isoformat() if platform.created_at else None,
        'updated_at': platform.updated_at.isoformat() if platform.updated_at else None,
    }


def serialize_deployment(deployment) -> Dict[str, Any]:
    """Serialize Deployment model to dictionary.

    Args:
        deployment: Deployment model instance

    Returns:
        Serialized deployment data as dictionary
    """
    return {
        'id': str(deployment.id),
        'platform_id': str(deployment.platform_id),
        'platform_name': deployment.platform.name if deployment.platform else None,
        'skill_id': deployment.skill_id,
        'skill_name': deployment.skill_name,
        'skill_version': deployment.skill_version,
        'deployment_id': deployment.deployment_id,
        'status': deployment.status,
        'original_format': deployment.original_format,
        'target_format': deployment.target_format,
        'file_size': deployment.file_size,
        'checksum': deployment.checksum,
        'deployment_config': deployment.deployment_config or {},
        'metadata': deployment.metadata or {},
        'started_at': deployment.started_at.isoformat() if deployment.started_at else None,
        'completed_at': deployment.completed_at.isoformat() if deployment.completed_at else None,
        'duration_seconds': deployment.duration_seconds,
        'success': deployment.success,
        'error_message': deployment.error_message,
        'error_details': deployment.error_details or {},
        'platform_response': deployment.platform_response or {},
        'retry_count': deployment.retry_count,
        'max_retries': deployment.max_retries,
        'created_at': deployment.created_at.isoformat() if deployment.created_at else None,
        'updated_at': deployment.updated_at.isoformat() if deployment.updated_at else None,
    }


def serialize_compatibility_check(check) -> Dict[str, Any]:
    """Serialize CompatibilityCheck model to dictionary.

    Args:
        check: CompatibilityCheck model instance

    Returns:
        Serialized compatibility check data as dictionary
    """
    # Serialize platform results
    platform_results = {}
    if check.platform_results:
        for platform_name, result_data in check.platform_results.items():
            platform_results[platform_name] = {
                'platform_name': platform_name,
                'compatible': result_data.get('compatible', False),
                'score': result_data.get('score'),
                'issues': result_data.get('issues', []),
                'warnings': result_data.get('warnings', []),
                'limitations': result_data.get('limitations', []),
                'supported_features': result_data.get('supported_features', []),
                'unsupported_features': result_data.get('unsupported_features', []),
            }

    return {
        'id': str(check.id),
        'skill_id': check.skill_id,
        'check_id': check.check_id,
        'platforms_checked': check.platforms_checked or [],
        'skill_version': check.skill_version,
        'overall_compatible': check.overall_compatible,
        'compatibility_score': check.get_compatibility_score(),
        'platform_results': platform_results,
        'compatibility_issues': check.compatibility_issues or [],
        'warnings': check.warnings or [],
        'recommendations': check.recommendations or [],
        'code_suggestions': check.code_suggestions or {},
        'feature_analysis': check.feature_analysis or {},
        'dependency_analysis': check.dependency_analysis or {},
        'limitation_analysis': check.limitation_analysis or {},
        'detailed_report': check.detailed_report or {},
        'check_duration_seconds': check.check_duration_seconds,
        'check_version': check.check_version,
        'checked_at': check.checked_at.isoformat() if check.checked_at else None,
        'created_at': check.created_at.isoformat() if check.created_at else None,
        'updated_at': check.updated_at.isoformat() if check.updated_at else None,
    }


def serialize_platform_list(platforms: List) -> List[Dict[str, Any]]:
    """Serialize list of Platform models.

    Args:
        platforms: List of Platform model instances

    Returns:
        List of serialized platform data
    """
    return [serialize_platform(platform) for platform in platforms]


def serialize_deployment_list(deployments: List) -> List[Dict[str, Any]]:
    """Serialize list of Deployment models.

    Args:
        deployments: List of Deployment model instances

    Returns:
        List of serialized deployment data
    """
    return [serialize_deployment(deployment) for deployment in deployments]


def serialize_compatibility_check_list(checks: List) -> List[Dict[str, Any]]:
    """Serialize list of CompatibilityCheck models.

    Args:
        checks: List of CompatibilityCheck model instances

    Returns:
        List of serialized compatibility check data
    """
    return [serialize_compatibility_check(check) for check in checks]


def serialize_platform_summary(platform) -> Dict[str, Any]:
    """Serialize Platform model to summary format.

    Args:
        platform: Platform model instance

    Returns:
        Serialized platform summary data
    """
    return {
        'id': str(platform.id),
        'name': platform.name,
        'display_name': platform.display_name,
        'platform_type': platform.platform_type,
        'is_active': platform.is_active,
        'is_healthy': platform.is_healthy,
        'last_health_check': platform.last_health_check.isoformat() if platform.last_health_check else None,
        'supported_formats_count': len(platform.supported_formats or []),
    }


def serialize_deployment_summary(deployment) -> Dict[str, Any]:
    """Serialize Deployment model to summary format.

    Args:
        deployment: Deployment model instance

    Returns:
        Serialized deployment summary data
    """
    return {
        'id': str(deployment.id),
        'platform_name': deployment.platform.name if deployment.platform else None,
        'skill_id': deployment.skill_id,
        'skill_name': deployment.skill_name,
        'status': deployment.status,
        'success': deployment.success,
        'started_at': deployment.started_at.isoformat() if deployment.started_at else None,
        'completed_at': deployment.completed_at.isoformat() if deployment.completed_at else None,
        'duration_seconds': deployment.duration_seconds,
    }


def serialize_compatibility_summary(check) -> Dict[str, Any]:
    """Serialize CompatibilityCheck model to summary format.

    Args:
        check: CompatibilityCheck model instance

    Returns:
        Serialized compatibility check summary data
    """
    return {
        'id': str(check.id),
        'skill_id': check.skill_id,
        'overall_compatible': check.overall_compatible,
        'compatibility_score': check.get_compatibility_score(),
        'platforms_checked': len(check.platforms_checked or []),
        'issues_count': len(check.compatibility_issues or []),
        'warnings_count': len(check.warnings or []),
        'critical_issues': len(check.get_issues_by_severity('critical')),
        'checked_at': check.checked_at.isoformat() if check.checked_at else None,
    }


def serialize_deployment_progress(deployment) -> Dict[str, Any]:
    """Serialize deployment progress information.

    Args:
        deployment: Deployment model instance

    Returns:
        Deployment progress data
    """
    progress = 0
    if deployment.status == 'pending':
        progress = 0
    elif deployment.status == 'deploying':
        # Estimate progress based on status and time
        if deployment.started_at:
            elapsed = (datetime.utcnow() - deployment.started_at).total_seconds()
            # Assume deployment takes 5 minutes on average
            estimated_total = 300
            progress = min(90, (elapsed / estimated_total) * 90)
        else:
            progress = 10
    elif deployment.status == 'success':
        progress = 100
    elif deployment.status in ['failed', 'cancelled']:
        progress = 100

    return {
        'deployment_id': str(deployment.id),
        'status': deployment.status,
        'progress': round(progress, 2),
        'current_step': get_deployment_current_step(deployment),
        'estimated_completion': estimate_completion_time(deployment, progress),
    }


def serialize_platform_health(platform) -> Dict[str, Any]:
    """Serialize platform health status.

    Args:
        platform: Platform model instance

    Returns:
        Platform health data
    """
    health_status = 'unknown'
    if not platform.is_active:
        health_status = 'inactive'
    elif platform.is_healthy:
        health_status = 'healthy'
    else:
        health_status = 'unhealthy'

    return {
        'platform_id': str(platform.id),
        'platform_name': platform.name,
        'is_active': platform.is_active,
        'is_healthy': platform.is_healthy,
        'health_status': health_status,
        'last_health_check': platform.last_health_check.isoformat() if platform.last_health_check else None,
    }


def serialize_compatibility_report(check) -> Dict[str, Any]:
    """Serialize detailed compatibility report.

    Args:
        check: CompatibilityCheck model instance

    Returns:
        Detailed compatibility report
    """
    # Group issues by severity
    issues_by_severity = {}
    for issue in (check.compatibility_issues or []):
        severity = issue.get('severity', 'unknown')
        if severity not in issues_by_severity:
            issues_by_severity[severity] = []
        issues_by_severity[severity].append(issue)

    # Group issues by platform
    issues_by_platform = {}
    for issue in (check.compatibility_issues or []):
        affected_platforms = issue.get('affected_platforms', [])
        for platform in affected_platforms:
            if platform not in issues_by_platform:
                issues_by_platform[platform] = []
            issues_by_platform[platform].append(issue)

    return {
        'summary': serialize_compatibility_summary(check),
        'platform_results': check.platform_results or {},
        'issues_by_severity': issues_by_severity,
        'issues_by_platform': issues_by_platform,
        'recommendations': check.recommendations or [],
        'code_suggestions': check.code_suggestions or {},
        'detailed_report': check.detailed_report or {},
    }


def serialize_to_json(data: Any, **kwargs) -> str:
    """Serialize data to JSON string.

    Args:
        data: Data to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        JSON string representation
    """
    def json_serializer(obj):
        """Custom JSON serializer for datetime and Decimal."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'isoformat'):  # datetime-like objects
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Custom objects
            return obj.__dict__
        return str(obj)

    kwargs.setdefault('default', json_serializer)
    kwargs.setdefault('ensure_ascii', False)
    kwargs.setdefault('separators', (',', ':'))

    return json.dumps(data, **kwargs)


def serialize_to_pretty_json(data: Any, **kwargs) -> str:
    """Serialize data to pretty-formatted JSON string.

    Args:
        data: Data to serialize
        **kwargs: Additional arguments for json.dumps

    Returns:
        Pretty-formatted JSON string
    """
    return serialize_to_json(data, indent=2, **kwargs)


def deserialize_from_json(json_str: str) -> Any:
    """Deserialize data from JSON string.

    Args:
        json_str: JSON string to deserialize

    Returns:
        Deserialized data

    Raises:
        ValueError: If JSON is invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {str(e)}")


def serialize_deployment_statistics(deployments: List) -> Dict[str, Any]:
    """Serialize deployment statistics.

    Args:
        deployments: List of Deployment model instances

    Returns:
        Deployment statistics
    """
    if not deployments:
        return {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'pending': 0,
            'deploying': 0,
            'success_rate': 0.0,
            'average_duration': 0.0,
        }

    total = len(deployments)
    successful = sum(1 for d in deployments if d.success is True)
    failed = sum(1 for d in deployments if d.success is False)
    pending = sum(1 for d in deployments if d.status == 'pending')
    deploying = sum(1 for d in deployments if d.status == 'deploying')

    # Calculate average duration for completed deployments
    completed_deployments = [d for d in deployments if d.duration_seconds]
    average_duration = (
        sum(d.duration_seconds for d in completed_deployments) / len(completed_deployments)
        if completed_deployments else 0
    )

    success_rate = (successful / total * 100) if total > 0 else 0.0

    return {
        'total': total,
        'successful': successful,
        'failed': failed,
        'pending': pending,
        'deploying': deploying,
        'success_rate': round(success_rate, 2),
        'average_duration': round(average_duration, 2),
    }


def serialize_platform_statistics(platforms: List) -> Dict[str, Any]:
    """Serialize platform statistics.

    Args:
        platforms: List of Platform model instances

    Returns:
        Platform statistics
    """
    if not platforms:
        return {
            'total': 0,
            'active': 0,
            'healthy': 0,
            'unhealthy': 0,
            'inactive': 0,
            'availability_rate': 0.0,
        }

    total = len(platforms)
    active = sum(1 for p in platforms if p.is_active)
    healthy = sum(1 for p in platforms if p.is_healthy)
    unhealthy = sum(1 for p in platforms if p.is_active and not p.is_healthy)
    inactive = sum(1 for p in platforms if not p.is_active)

    availability_rate = (healthy / total * 100) if total > 0 else 0.0

    return {
        'total': total,
        'active': active,
        'healthy': healthy,
        'unhealthy': unhealthy,
        'inactive': inactive,
        'availability_rate': round(availability_rate, 2),
    }


def serialize_compatibility_statistics(checks: List) -> Dict[str, Any]:
    """Serialize compatibility check statistics.

    Args:
        checks: List of CompatibilityCheck model instances

    Returns:
        Compatibility check statistics
    """
    if not checks:
        return {
            'total': 0,
            'compatible': 0,
            'incompatible': 0,
            'average_score': 0.0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0,
        }

    total = len(checks)
    compatible = sum(1 for c in checks if c.overall_compatible is True)
    incompatible = sum(1 for c in checks if c.overall_compatible is False)

    # Calculate average compatibility score
    scores = [c.get_compatibility_score() for c in checks if c.get_compatibility_score() is not None]
    average_score = sum(scores) / len(scores) if scores else 0.0

    # Count issues by severity
    critical_issues = sum(len(c.get_issues_by_severity('critical')) for c in checks)
    high_issues = sum(len(c.get_issues_by_severity('high')) for c in checks)
    medium_issues = sum(len(c.get_issues_by_severity('medium')) for c in checks)
    low_issues = sum(len(c.get_issues_by_severity('low')) for c in checks)

    return {
        'total': total,
        'compatible': compatible,
        'incompatible': incompatible,
        'average_score': round(average_score, 2),
        'critical_issues': critical_issues,
        'high_issues': high_issues,
        'medium_issues': medium_issues,
        'low_issues': low_issues,
    }


# Helper functions
def get_deployment_current_step(deployment) -> Optional[str]:
    """Get current deployment step description.

    Args:
        deployment: Deployment model instance

    Returns:
        Current step description
    """
    step_mapping = {
        'pending': 'Waiting to start',
        'deploying': 'Deployment in progress',
        'success': 'Deployment completed',
        'failed': 'Deployment failed',
        'cancelled': 'Deployment cancelled',
    }
    return step_mapping.get(deployment.status)


def estimate_completion_time(deployment, progress: float) -> Optional[str]:
    """Estimate deployment completion time.

    Args:
        deployment: Deployment model instance
        progress: Current progress percentage

    Returns:
        ISO format estimated completion time
    """
    if deployment.status not in ['deploying'] or not deployment.started_at or progress <= 0:
        return None

    elapsed = (datetime.utcnow() - deployment.started_at).total_seconds()
    estimated_total = elapsed / (progress / 100)
    remaining = estimated_total - elapsed

    completion_time = datetime.utcnow().timestamp() + remaining
    return datetime.fromtimestamp(completion_time).isoformat()