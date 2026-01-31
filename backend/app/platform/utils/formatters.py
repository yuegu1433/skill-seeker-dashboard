"""Platform formatting utilities.

This module provides formatting functions for displaying platform data,
deployment status, and compatibility information.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import humanize


def format_platform_display_name(platform) -> str:
    """Format platform display name.

    Args:
        platform: Platform model instance

    Returns:
        Formatted display name
    """
    return platform.display_name or platform.name


def format_platform_status(platform) -> str:
    """Format platform status for display.

    Args:
        platform: Platform model instance

    Returns:
        Formatted status string
    """
    if not platform.is_active:
        return "Inactive"
    elif platform.is_healthy:
        return "Healthy"
    else:
        return "Unhealthy"


def format_platform_type(platform_type: str) -> str:
    """Format platform type for display.

    Args:
        platform_type: Platform type string

    Returns:
        Formatted platform type
    """
    type_mapping = {
        'claude': 'Claude',
        'gemini': 'Gemini',
        'openai': 'OpenAI',
        'markdown': 'Markdown',
    }
    return type_mapping.get(platform_type, platform_type.title())


def format_deployment_status(deployment) -> str:
    """Format deployment status for display.

    Args:
        deployment: Deployment model instance

    Returns:
        Formatted status string
    """
    status_mapping = {
        'pending': 'Pending',
        'deploying': 'Deploying',
        'success': 'Success',
        'failed': 'Failed',
        'cancelled': 'Cancelled',
    }
    return status_mapping.get(deployment.status, deployment.status.title())


def format_deployment_status_with_details(deployment) -> Dict[str, str]:
    """Format deployment status with additional details.

    Args:
        deployment: Deployment model instance

    Returns:
        Dictionary with status and details
    """
    status = format_deployment_status(deployment)
    details = {}

    if deployment.status == 'deploying' and deployment.started_at:
        elapsed = datetime.utcnow() - deployment.started_at
        details['elapsed'] = humanize.precisedelta(elapsed)
    elif deployment.status == 'success' and deployment.duration_seconds:
        details['duration'] = humanize.precisedelta(
            timedelta(seconds=deployment.duration_seconds)
        )
    elif deployment.status == 'failed' and deployment.error_message:
        details['error'] = deployment.error_message

    return {'status': status, 'details': details}


def format_compatibility_status(check) -> str:
    """Format compatibility status for display.

    Args:
        check: CompatibilityCheck model instance

    Returns:
        Formatted compatibility status
    """
    if check.overall_compatible is True:
        return "Compatible"
    elif check.overall_compatible is False:
        return "Incompatible"
    else:
        return "Unknown"


def format_compatibility_score(score: Optional[float]) -> str:
    """Format compatibility score for display.

    Args:
        score: Compatibility score (0-100)

    Returns:
        Formatted score string
    """
    if score is None:
        return "N/A"

    score = round(score, 1)

    if score >= 90:
        return f"{score}% (Excellent)"
    elif score >= 70:
        return f"{score}% (Good)"
    elif score >= 50:
        return f"{score}% (Fair)"
    else:
        return f"{score}% (Poor)"


def format_file_size(size_bytes: Optional[int]) -> str:
    """Format file size for display.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted file size string
    """
    if size_bytes is None:
        return "Unknown"

    return humanize.naturalsize(size_bytes)


def format_duration(seconds: Optional[int]) -> str:
    """Format duration in seconds for display.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds is None:
        return "Unknown"

    return humanize.precisedelta(timedelta(seconds=seconds))


def format_datetime(dt: Optional[datetime], relative: bool = True) -> str:
    """Format datetime for display.

    Args:
        dt: Datetime to format
        relative: Whether to show relative time

    Returns:
        Formatted datetime string
    """
    if dt is None:
        return "Never"

    if relative:
        return humanize.naturaltime(dt)
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_datetime_short(dt: Optional[datetime]) -> str:
    """Format datetime for short display.

    Args:
        dt: Datetime to format

    Returns:
        Short formatted datetime string
    """
    if dt is None:
        return "N/A"

    now = datetime.utcnow()
    diff = now - dt

    if diff.days == 0:
        if diff.seconds < 60:
            return f"{diff.seconds}s ago"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}m ago"
        else:
            return f"{diff.seconds // 3600}h ago"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days}d ago"
    elif diff.days < 30:
        return f"{diff.days // 7}w ago"
    else:
        return dt.strftime("%Y-%m-%d")


def format_health_status(platform) -> Dict[str, Any]:
    """Format comprehensive health status.

    Args:
        platform: Platform model instance

    Returns:
        Dictionary with health status information
    """
    status_info = {
        'is_active': platform.is_active,
        'is_healthy': platform.is_healthy,
        'status': format_platform_status(platform),
        'last_check': format_datetime(platform.last_health_check),
    }

    if platform.last_health_check:
        time_since = datetime.utcnow() - platform.last_health_check
        status_info['time_since_check'] = humanize.precisedelta(time_since)

    return status_info


def format_platform_list_display(platforms: List) -> List[Dict[str, Any]]:
    """Format list of platforms for display.

    Args:
        platforms: List of Platform model instances

    Returns:
        List of formatted platform display data
    """
    return [
        {
            'id': str(p.id),
            'name': p.name,
            'display_name': format_platform_display_name(p),
            'type': format_platform_type(p.platform_type),
            'status': format_platform_status(p),
            'supported_formats': len(p.supported_formats or []),
            'last_health_check': format_datetime_short(p.last_health_check),
        }
        for p in platforms
    ]


def format_deployment_list_display(deployments: List) -> List[Dict[str, Any]]:
    """Format list of deployments for display.

    Args:
        deployments: List of Deployment model instances

    Returns:
        List of formatted deployment display data
    """
    return [
        {
            'id': str(d.id),
            'platform_name': d.platform.name if d.platform else 'Unknown',
            'skill_name': d.skill_name,
            'skill_version': d.skill_version,
            'status': format_deployment_status(d),
            'started_at': format_datetime_short(d.started_at),
            'duration': format_duration(d.duration_seconds),
            'success': d.success,
        }
        for d in deployments
    ]


def format_compatibility_list_display(checks: List) -> List[Dict[str, Any]]:
    """Format list of compatibility checks for display.

    Args:
        checks: List of CompatibilityCheck model instances

    Returns:
        List of formatted compatibility check display data
    """
    return [
        {
            'id': str(c.id),
            'skill_id': c.skill_id,
            'overall_status': format_compatibility_status(c),
            'score': format_compatibility_score(c.get_compatibility_score()),
            'platforms_count': len(c.platforms_checked or []),
            'issues_count': len(c.compatibility_issues or []),
            'critical_issues': len(c.get_issues_by_severity('critical')),
            'checked_at': format_datetime_short(c.checked_at),
        }
        for c in checks
    ]


def format_deployment_progress(deployment) -> Dict[str, Any]:
    """Format deployment progress information.

    Args:
        deployment: Deployment model instance

    Returns:
        Formatted progress information
    """
    progress = 0
    if deployment.status == 'pending':
        progress = 0
        message = "Waiting to start"
    elif deployment.status == 'deploying':
        progress = 25  # Starting deployment
        message = "Initializing deployment"
    elif deployment.status == 'success':
        progress = 100
        message = "Deployment completed"
    elif deployment.status == 'failed':
        progress = 100
        message = "Deployment failed"
    elif deployment.status == 'cancelled':
        progress = 100
        message = "Deployment cancelled"
    else:
        message = "Unknown status"

    return {
        'progress': progress,
        'message': message,
        'status': format_deployment_status(deployment),
        'started_at': format_datetime(deployment.started_at),
        'completed_at': format_datetime(deployment.completed_at),
        'duration': format_duration(deployment.duration_seconds),
    }


def format_issues_by_severity(issues: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Format issues grouped by severity.

    Args:
        issues: List of issue dictionaries

    Returns:
        Dictionary with issues grouped by severity
    """
    grouped = {
        'critical': [],
        'high': [],
        'medium': [],
        'low': [],
    }

    for issue in issues:
        severity = issue.get('severity', 'unknown')
        if severity in grouped:
            grouped[severity].append(issue)

    return grouped


def format_recommendations_by_priority(recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Format recommendations grouped by priority.

    Args:
        recommendations: List of recommendation dictionaries

    Returns:
        Dictionary with recommendations grouped by priority
    """
    grouped = {
        'high': [],
        'medium': [],
        'low': [],
    }

    for rec in recommendations:
        priority = rec.get('priority', 'medium')
        if priority in grouped:
            grouped[priority].append(rec)

    return grouped


def format_platform_comparison(platforms: List) -> Dict[str, Any]:
    """Format platform comparison data.

    Args:
        platforms: List of Platform model instances

    Returns:
        Dictionary with comparison data
    """
    comparison = {
        'platforms': [],
        'summary': {
            'total': len(platforms),
            'active': sum(1 for p in platforms if p.is_active),
            'healthy': sum(1 for p in platforms if p.is_healthy),
        },
        'features': {},
    }

    # Collect all unique features
    all_features = set()
    for p in platforms:
        if p.features:
            all_features.update(p.features.keys())

    # Format each platform
    for p in platforms:
        platform_data = {
            'id': str(p.id),
            'name': p.name,
            'display_name': format_platform_display_name(p),
            'type': format_platform_type(p.platform_type),
            'status': format_platform_status(p),
            'features': {},
            'supported_formats': p.supported_formats or [],
            'max_file_size': format_file_size(p.max_file_size),
        }

        # Add feature values
        for feature in all_features:
            platform_data['features'][feature] = p.features.get(feature) if p.features else None

        comparison['platforms'].append(platform_data)

    return comparison


def format_deployment_statistics(statistics: Dict[str, Any]) -> Dict[str, Any]:
    """Format deployment statistics for display.

    Args:
        statistics: Raw statistics dictionary

    Returns:
        Formatted statistics dictionary
    """
    formatted = statistics.copy()

    # Format success rate
    if 'success_rate' in formatted:
        formatted['success_rate_display'] = f"{formatted['success_rate']:.1f}%"

    # Format average duration
    if 'average_duration' in formatted:
        formatted['average_duration_display'] = format_duration(formatted['average_duration'])

    # Add visual indicators
    if formatted.get('success_rate', 0) >= 90:
        formatted['success_indicator'] = 'excellent'
    elif formatted.get('success_rate', 0) >= 70:
        formatted['success_indicator'] = 'good'
    elif formatted.get('success_rate', 0) >= 50:
        formatted['success_indicator'] = 'fair'
    else:
        formatted['success_indicator'] = 'poor'

    return formatted


def format_platform_statistics(statistics: Dict[str, Any]) -> Dict[str, Any]:
    """Format platform statistics for display.

    Args:
        statistics: Raw statistics dictionary

    Returns:
        Formatted statistics dictionary
    """
    formatted = statistics.copy()

    # Format availability rate
    if 'availability_rate' in formatted:
        formatted['availability_rate_display'] = f"{formatted['availability_rate']:.1f}%"

    # Add visual indicators
    if formatted.get('availability_rate', 0) >= 95:
        formatted['availability_indicator'] = 'excellent'
    elif formatted.get('availability_rate', 0) >= 80:
        formatted['availability_indicator'] = 'good'
    elif formatted.get('availability_rate', 0) >= 60:
        formatted['availability_indicator'] = 'fair'
    else:
        formatted['availability_indicator'] = 'poor'

    return formatted


def format_compatibility_statistics(statistics: Dict[str, Any]) -> Dict[str, Any]:
    """Format compatibility statistics for display.

    Args:
        statistics: Raw statistics dictionary

    Returns:
        Formatted statistics dictionary
    """
    formatted = statistics.copy()

    # Format average score
    if 'average_score' in formatted:
        formatted['average_score_display'] = format_compatibility_score(formatted['average_score'])

    # Calculate total issues
    total_issues = (
        formatted.get('critical_issues', 0) +
        formatted.get('high_issues', 0) +
        formatted.get('medium_issues', 0) +
        formatted.get('low_issues', 0)
    )
    formatted['total_issues'] = total_issues

    # Add visual indicators
    if formatted.get('average_score', 0) >= 90:
        formatted['compatibility_indicator'] = 'excellent'
    elif formatted.get('average_score', 0) >= 70:
        formatted['compatibility_indicator'] = 'good'
    elif formatted.get('average_score', 0) >= 50:
        formatted['compatibility_indicator'] = 'fair'
    else:
        formatted['compatibility_indicator'] = 'poor'

    return formatted


def format_error_message(error: Optional[str], error_details: Optional[Dict[str, Any]] = None) -> str:
    """Format error message for display.

    Args:
        error: Error message
        error_details: Additional error details

    Returns:
        Formatted error message
    """
    if not error:
        return "Unknown error"

    message = error

    if error_details:
        # Add context from error details
        if 'error_code' in error_details:
            message = f"[{error_details['error_code']}] {message}"
        if 'platform' in error_details:
            message = f"{message} (Platform: {error_details['platform']})"

    return message


def format_notification_message(notification_type: str, data: Dict[str, Any]) -> Dict[str, str]:
    """Format notification message for display.

    Args:
        notification_type: Type of notification
        data: Notification data

    Returns:
        Formatted notification message
    """
    message_templates = {
        'deployment_success': 'Deployment of {skill_name} to {platform_name} completed successfully',
        'deployment_failure': 'Deployment of {skill_name} to {platform_name} failed: {error}',
        'deployment_status': 'Deployment of {skill_name} to {platform_name} is now {status}',
        'platform_health': 'Platform {platform_name} health status: {status}',
        'compatibility_check': 'Compatibility check for {skill_id} completed with score {score}',
    }

    template = message_templates.get(notification_type, '{message}')

    try:
        formatted_message = template.format(**data)
    except KeyError:
        formatted_message = f"Notification: {notification_type}"

    return {
        'title': formatted_message.split(':')[0] if ':' in formatted_message else notification_type.replace('_', ' ').title(),
        'message': formatted_message,
        'type': notification_type,
    }