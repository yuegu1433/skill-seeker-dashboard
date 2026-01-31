"""Platform manager for handling platform operations.

This module provides the PlatformManager class for managing LLM platform
configurations, health checks, and platform-related operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import asyncio
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

from ..models.platform import Platform
from ..models.deployment import Deployment
from ..schemas.platform_operations import (
    PlatformCreateRequest,
    PlatformUpdateRequest,
    PlatformListRequest,
    PlatformHealthCheckRequest,
)
from ..utils.validators import (
    validate_platform_name,
    validate_api_endpoint,
    validate_platform_config,
    validate_health_check_params,
)
from ..utils.serializers import serialize_platform, serialize_platform_list
from ..utils.formatters import format_platform_status, format_health_status


logger = logging.getLogger(__name__)


class PlatformManager:
    """Manager for platform operations.

    Handles platform CRUD operations, health checks, status management,
    and platform-related queries.
    """

    def __init__(self, db_session: Session):
        """Initialize PlatformManager.

        Args:
            db_session: Database session
        """
        self.db = db_session

    # CRUD Operations
    async def create_platform(self, request: PlatformCreateRequest) -> Platform:
        """Create a new platform.

        Args:
            request: Platform creation request

        Returns:
            Created platform instance

        Raises:
            ValueError: If validation fails
            Exception: If creation fails
        """
        try:
            # Validate platform name
            validate_platform_name(request.name)

            # Validate API endpoint if provided
            if request.api_endpoint:
                validate_api_endpoint(request.api_endpoint)

            # Validate configuration
            validate_platform_config(request.configuration)

            # Check if platform name already exists
            existing = self.db.query(Platform).filter(
                Platform.name == request.name.lower()
            ).first()

            if existing:
                raise ValueError(f"Platform with name '{request.name}' already exists")

            # Create platform
            platform = Platform(
                name=request.name.lower(),
                display_name=request.display_name,
                platform_type=request.platform_type,
                api_endpoint=request.api_endpoint,
                api_version=request.api_version,
                authentication_type=request.authentication_type,
                supported_formats=request.supported_formats,
                max_file_size=request.max_file_size,
                features=request.features,
                is_active=request.is_active,
                configuration=request.configuration,
                validation_rules=request.validation_rules,
                conversion_templates=request.conversion_templates,
            )

            self.db.add(platform)
            self.db.commit()
            self.db.refresh(platform)

            logger.info(f"Created platform: {platform.name}")
            return platform

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create platform: {str(e)}")
            raise

    async def get_platform(self, platform_id: Union[str, UUID]) -> Optional[Platform]:
        """Get platform by ID.

        Args:
            platform_id: Platform ID

        Returns:
            Platform instance or None
        """
        return self.db.query(Platform).filter(Platform.id == platform_id).first()

    async def get_platform_by_name(self, name: str) -> Optional[Platform]:
        """Get platform by name.

        Args:
            name: Platform name

        Returns:
            Platform instance or None
        """
        return self.db.query(Platform).filter(Platform.name == name.lower()).first()

    async def update_platform(
        self,
        platform_id: Union[str, UUID],
        request: PlatformUpdateRequest
    ) -> Optional[Platform]:
        """Update platform.

        Args:
            platform_id: Platform ID
            request: Platform update request

        Returns:
            Updated platform instance

        Raises:
            ValueError: If validation fails
        """
        try:
            platform = await self.get_platform(platform_id)
            if not platform:
                return None

            # Update fields
            update_data = request.dict(exclude_unset=True)

            # Validate API endpoint if being updated
            if 'api_endpoint' in update_data and update_data['api_endpoint']:
                validate_api_endpoint(update_data['api_endpoint'])

            # Validate configuration if being updated
            if 'configuration' in update_data:
                validate_platform_config(update_data['configuration'])

            # Update platform
            for key, value in update_data.items():
                setattr(platform, key, value)

            platform.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(platform)

            logger.info(f"Updated platform: {platform.name}")
            return platform

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update platform: {str(e)}")
            raise

    async def delete_platform(self, platform_id: Union[str, UUID]) -> bool:
        """Delete platform.

        Args:
            platform_id: Platform ID

        Returns:
            True if deleted, False if not found
        """
        try:
            platform = await self.get_platform(platform_id)
            if not platform:
                return False

            # Check if platform has active deployments
            active_deployments = self.db.query(Deployment).filter(
                and_(
                    Deployment.platform_id == platform_id,
                    Deployment.status.in_(['pending', 'deploying'])
                )
            ).count()

            if active_deployments > 0:
                raise ValueError(
                    f"Cannot delete platform with {active_deployments} active deployments"
                )

            self.db.delete(platform)
            self.db.commit()

            logger.info(f"Deleted platform: {platform.name}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete platform: {str(e)}")
            raise

    async def list_platforms(self, request: PlatformListRequest) -> Dict[str, Any]:
        """List platforms with filtering and pagination.

        Args:
            request: List request with filters

        Returns:
            Dictionary with platforms and pagination info
        """
        query = self.db.query(Platform)

        # Apply filters
        if request.platform_type:
            query = query.filter(Platform.platform_type == request.platform_type)

        if request.is_active is not None:
            query = query.filter(Platform.is_active == request.is_active)

        if request.is_healthy is not None:
            query = query.filter(Platform.is_healthy == request.is_healthy)

        if request.search:
            search_term = f"%{request.search.lower()}%"
            query = query.filter(
                or_(
                    Platform.name.ilike(search_term),
                    Platform.display_name.ilike(search_term)
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        platforms = query.offset(request.skip).limit(request.limit).all()

        return {
            'platforms': serialize_platform_list(platforms),
            'total': total,
            'skip': request.skip,
            'limit': request.limit,
        }

    # Health Check Operations
    async def check_platform_health(
        self,
        platform_id: Union[str, UUID],
        request: PlatformHealthCheckRequest
    ) -> Dict[str, Any]:
        """Perform health check on platform.

        Args:
            platform_id: Platform ID
            request: Health check request

        Returns:
            Health check result
        """
        try:
            platform = await self.get_platform(platform_id)
            if not platform:
                raise ValueError(f"Platform not found: {platform_id}")

            # Validate parameters
            timeout, check_depth = validate_health_check_params(
                request.check_timeout,
                request.check_depth
            )

            # Perform health check
            start_time = datetime.utcnow()

            # Simple health check - verify platform is active
            is_healthy = platform.is_active

            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Update platform health status
            platform.update_health_status(is_healthy)
            self.db.commit()

            result = {
                'platform_id': str(platform_id),
                'platform_name': platform.name,
                'is_healthy': is_healthy,
                'response_time_ms': round(response_time, 2),
                'check_depth': check_depth,
                'timestamp': datetime.utcnow().isoformat(),
            }

            if not is_healthy:
                result['error_message'] = 'Platform is not active'

            logger.info(
                f"Health check completed for {platform.name}: "
                f"{'healthy' if is_healthy else 'unhealthy'}"
            )

            return result

        except Exception as e:
            logger.error(f"Health check failed for platform {platform_id}: {str(e)}")
            raise

    async def check_all_platforms_health(self) -> List[Dict[str, Any]]:
        """Perform health check on all active platforms.

        Returns:
            List of health check results
        """
        platforms = self.db.query(Platform).filter(Platform.is_active == True).all()

        results = []
        for platform in platforms:
            try:
                result = await self.check_platform_health(
                    platform.id,
                    PlatformHealthCheckRequest()
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Health check failed for {platform.name}: {str(e)}")
                results.append({
                    'platform_id': str(platform.id),
                    'platform_name': platform.name,
                    'is_healthy': False,
                    'error_message': str(e),
                    'timestamp': datetime.utcnow().isoformat(),
                })

        return results

    # Status Management
    async def activate_platform(self, platform_id: Union[str, UUID]) -> Optional[Platform]:
        """Activate platform.

        Args:
            platform_id: Platform ID

        Returns:
            Updated platform instance
        """
        return await self.update_platform(
            platform_id,
            PlatformUpdateRequest(is_active=True)
        )

    async def deactivate_platform(self, platform_id: Union[str, UUID]) -> Optional[Platform]:
        """Deactivate platform.

        Args:
            platform_id: Platform ID

        Returns:
                Updated platform instance
        """
        # Check for active deployments before deactivating
        active_deployments = self.db.query(Deployment).filter(
            and_(
                Deployment.platform_id == platform_id,
                Deployment.status.in_(['pending', 'deploying'])
            )
        ).count()

        if active_deployments > 0:
            raise ValueError(
                f"Cannot deactivate platform with {active_deployments} active deployments"
            )

        return await self.update_platform(
            platform_id,
            PlatformUpdateRequest(is_active=False)
        )

    async def mark_platform_healthy(self, platform_id: Union[str, UUID]) -> Optional[Platform]:
        """Mark platform as healthy.

        Args:
            platform_id: Platform ID

        Returns:
            Updated platform instance
        """
        platform = await self.get_platform(platform_id)
        if not platform:
            return None

        platform.update_health_status(True)
        self.db.commit()

        return platform

    async def mark_platform_unhealthy(
        self,
        platform_id: Union[str, UUID],
        reason: Optional[str] = None
    ) -> Optional[Platform]:
        """Mark platform as unhealthy.

        Args:
            platform_id: Platform ID
            reason: Reason for marking unhealthy

        Returns:
            Updated platform instance
        """
        platform = await self.get_platform(platform_id)
        if not platform:
            return None

        platform.update_health_status(False)
        if reason:
            platform.configuration = platform.configuration or {}
            platform.configuration['unhealthy_reason'] = reason

        self.db.commit()

        return platform

    # Query Operations
    async def get_active_platforms(self) -> List[Platform]:
        """Get all active platforms.

        Returns:
            List of active platforms
        """
        return self.db.query(Platform).filter(Platform.is_active == True).all()

    async def get_healthy_platforms(self) -> List[Platform]:
        """Get all healthy platforms.

        Returns:
            List of healthy platforms
        """
        return self.db.query(Platform).filter(
            and_(
                Platform.is_active == True,
                Platform.is_healthy == True
            )
        ).all()

    async def get_platforms_by_type(self, platform_type: str) -> List[Platform]:
        """Get platforms by type.

        Args:
            platform_type: Platform type

        Returns:
            List of platforms with specified type
        """
        return self.db.query(Platform).filter(Platform.platform_type == platform_type).all()

    async def get_platform_statistics(self) -> Dict[str, Any]:
        """Get platform statistics.

        Returns:
            Platform statistics
        """
        total = self.db.query(Platform).count()
        active = self.db.query(Platform).filter(Platform.is_active == True).count()
        healthy = self.db.query(Platform).filter(
            and_(
                Platform.is_active == True,
                Platform.is_healthy == True
            )
        ).count()
        unhealthy = self.db.query(Platform).filter(
            and_(
                Platform.is_active == True,
                Platform.is_healthy == False
            )
        ).count()
        inactive = total - active

        availability_rate = (healthy / total * 100) if total > 0 else 0.0

        return {
            'total': total,
            'active': active,
            'healthy': healthy,
            'unhealthy': unhealthy,
            'inactive': inactive,
            'availability_rate': round(availability_rate, 2),
        }

    async def get_platform_usage_stats(self, platform_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get platform usage statistics.

        Args:
            platform_id: Platform ID

        Returns:
            Platform usage statistics
        """
        # Total deployments
        total_deployments = self.db.query(Deployment).filter(
            Deployment.platform_id == platform_id
        ).count()

        # Successful deployments
        successful_deployments = self.db.query(Deployment).filter(
            and_(
                Deployment.platform_id == platform_id,
                Deployment.success == True
            )
        ).count()

        # Failed deployments
        failed_deployments = self.db.query(Deployment).filter(
            and_(
                Deployment.platform_id == platform_id,
                Deployment.success == False
            )
        ).count()

        # Recent deployments (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_deployments = self.db.query(Deployment).filter(
            and_(
                Deployment.platform_id == platform_id,
                Deployment.created_at >= thirty_days_ago
            )
        ).count()

        # Success rate
        success_rate = (
            (successful_deployments / total_deployments * 100)
            if total_deployments > 0 else 0
        )

        return {
            'total_deployments': total_deployments,
            'successful_deployments': successful_deployments,
            'failed_deployments': failed_deployments,
            'recent_deployments': recent_deployments,
            'success_rate': round(success_rate, 2),
        }

    # Utility Methods
    async def platform_exists(self, platform_id: Union[str, UUID]) -> bool:
        """Check if platform exists.

        Args:
            platform_id: Platform ID

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(Platform).filter(Platform.id == platform_id).first() is not None

    async def is_platform_active(self, platform_id: Union[str, UUID]) -> bool:
        """Check if platform is active.

        Args:
            platform_id: Platform ID

        Returns:
            True if active, False otherwise
        """
        platform = await self.get_platform(platform_id)
        return platform.is_active if platform else False

    async def is_platform_healthy(self, platform_id: Union[str, UUID]) -> bool:
        """Check if platform is healthy.

        Args:
            platform_id: Platform ID

        Returns:
            True if healthy, False otherwise
        """
        platform = await self.get_platform(platform_id)
        return platform.is_healthy if platform else False

    async def supports_format(self, platform_id: Union[str, UUID], format_name: str) -> bool:
        """Check if platform supports a format.

        Args:
            platform_id: Platform ID
            format_name: Format name

        Returns:
            True if supported, False otherwise
        """
        platform = await self.get_platform(platform_id)
        if not platform:
            return False

        return platform.supports_format(format_name)

    async def get_max_file_size(self, platform_id: Union[str, UUID], format_name: str) -> int:
        """Get maximum file size for platform and format.

        Args:
            platform_id: Platform ID
            format_name: Format name

        Returns:
            Maximum file size in bytes
        """
        platform = await self.get_platform(platform_id)
        if not platform:
            return 0

        return platform.get_max_size_for_format(format_name)