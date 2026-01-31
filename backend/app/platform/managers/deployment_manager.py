"""Deployment manager for handling deployment operations.

This module provides the DeploymentManager class for managing skill deployments
to LLM platforms, tracking deployment status, and handling retry logic.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import asyncio
import logging

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func

from ..models.deployment import Deployment, DeploymentStatus
from ..models.platform import Platform
from ..schemas.platform_operations import (
    DeploymentCreateRequest,
    DeploymentUpdateRequest,
    DeploymentListRequest,
    DeploymentRetryRequest,
)
from ..utils.validators import (
    validate_deployment_config,
    validate_pagination_params,
)
from ..utils.serializers import (
    serialize_deployment,
    serialize_deployment_list,
    serialize_deployment_statistics,
)
from ..utils.formatters import (
    format_deployment_status,
    format_deployment_progress,
)


logger = logging.getLogger(__name__)


class DeploymentManager:
    """Manager for deployment operations.

    Handles deployment CRUD operations, status tracking, retry logic,
    and deployment-related queries.
    """

    def __init__(self, db_session: Session):
        """Initialize DeploymentManager.

        Args:
            db_session: Database session
        """
        self.db = db_session

    # CRUD Operations
    async def create_deployment(self, request: DeploymentCreateRequest) -> Deployment:
        """Create a new deployment.

        Args:
            request: Deployment creation request

        Returns:
            Created deployment instance

        Raises:
            ValueError: If validation fails
            Exception: If creation fails
        """
        try:
            # Validate deployment configuration
            validate_deployment_config(request.deployment_config)

            # Verify platform exists and is active
            platform = self.db.query(Platform).filter(
                Platform.id == request.platform_id
            ).first()

            if not platform:
                raise ValueError(f"Platform not found: {request.platform_id}")

            if not platform.is_active:
                raise ValueError(f"Platform is not active: {platform.name}")

            # Create deployment
            deployment = Deployment(
                platform_id=request.platform_id,
                skill_id=request.skill_id,
                skill_name=request.skill_name,
                skill_version=request.skill_version,
                original_format=request.original_format,
                target_format=request.target_format,
                file_size=request.file_size,
                checksum=request.checksum,
                deployment_config=request.deployment_config,
                metadata=request.metadata,
                max_retries=request.max_retries,
                status=DeploymentStatus.PENDING,
            )

            self.db.add(deployment)
            self.db.commit()
            self.db.refresh(deployment)

            logger.info(
                f"Created deployment: {deployment.skill_name} to {platform.name}"
            )
            return deployment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create deployment: {str(e)}")
            raise

    async def get_deployment(self, deployment_id: Union[str, UUID]) -> Optional[Deployment]:
        """Get deployment by ID.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment instance or None
        """
        return self.db.query(Deployment).filter(Deployment.id == deployment_id).first()

    async def update_deployment(
        self,
        deployment_id: Union[str, UUID],
        request: DeploymentUpdateRequest
    ) -> Optional[Deployment]:
        """Update deployment.

        Args:
            deployment_id: Deployment ID
            request: Deployment update request

        Returns:
            Updated deployment instance
        """
        try:
            deployment = await self.get_deployment(deployment_id)
            if not deployment:
                return None

            # Update fields
            update_data = request.dict(exclude_unset=True)

            for key, value in update_data.items():
                setattr(deployment, key, value)

            deployment.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(deployment)

            logger.info(f"Updated deployment: {deployment.id}")
            return deployment

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update deployment: {str(e)}")
            raise

    async def delete_deployment(self, deployment_id: Union[str, UUID]) -> bool:
        """Delete deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            True if deleted, False if not found
        """
        try:
            deployment = await self.get_deployment(deployment_id)
            if not deployment:
                return False

            # Can only delete completed or cancelled deployments
            if deployment.status in ['pending', 'deploying']:
                raise ValueError(
                    f"Cannot delete deployment with status: {deployment.status}"
                )

            self.db.delete(deployment)
            self.db.commit()

            logger.info(f"Deleted deployment: {deployment_id}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete deployment: {str(e)}")
            raise

    async def list_deployments(self, request: DeploymentListRequest) -> Dict[str, Any]:
        """List deployments with filtering and pagination.

        Args:
            request: List request with filters

        Returns:
            Dictionary with deployments and pagination info
        """
        query = self.db.query(Deployment)

        # Apply filters
        if request.platform_id:
            query = query.filter(Deployment.platform_id == request.platform_id)

        if request.skill_id:
            query = query.filter(Deployment.skill_id == request.skill_id)

        if request.status:
            query = query.filter(Deployment.status == request.status)

        if request.success is not None:
            query = query.filter(Deployment.success == request.success)

        if request.date_from:
            query = query.filter(Deployment.created_at >= request.date_from)

        if request.date_to:
            query = query.filter(Deployment.created_at <= request.date_to)

        # Get total count
        total = query.count()

        # Apply pagination
        skip, limit = validate_pagination_params(request.skip, request.limit)
        deployments = query.offset(skip).limit(limit).all()

        return {
            'deployments': serialize_deployment_list(deployments),
            'total': total,
            'skip': skip,
            'limit': limit,
        }

    # Deployment Lifecycle Management
    async def start_deployment(self, deployment_id: Union[str, UUID]) -> Optional[Deployment]:
        """Start a deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            Updated deployment instance
        """
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            return None

        if deployment.status != DeploymentStatus.PENDING:
            raise ValueError(f"Cannot start deployment with status: {deployment.status}")

        deployment.start_deployment()
        self.db.commit()

        logger.info(f"Started deployment: {deployment_id}")
        return deployment

    async def complete_deployment(
        self,
        deployment_id: Union[str, UUID],
        success: bool,
        platform_response: Optional[Dict[str, Any]] = None
    ) -> Optional[Deployment]:
        """Complete a deployment.

        Args:
            deployment_id: Deployment ID
            success: Whether deployment was successful
            platform_response: Platform response data

        Returns:
            Updated deployment instance
        """
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            return None

        deployment.complete_deployment(success, platform_response)
        self.db.commit()

        logger.info(
            f"Completed deployment: {deployment_id} - {'success' if success else 'failed'}"
        )
        return deployment

    async def fail_deployment(
        self,
        deployment_id: Union[str, UUID],
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Optional[Deployment]:
        """Fail a deployment.

        Args:
            deployment_id: Deployment ID
            error_message: Error message
            error_details: Additional error details

        Returns:
            Updated deployment instance
        """
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            return None

        deployment.fail_deployment(error_message, error_details)
        self.db.commit()

        logger.error(f"Failed deployment: {deployment_id} - {error_message}")
        return deployment

    async def cancel_deployment(self, deployment_id: Union[str, UUID]) -> Optional[Deployment]:
        """Cancel a deployment.

        Args:
            deployment_id: Deployment ID

        Returns:
            Updated deployment instance
        """
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            return None

        if deployment.status in [DeploymentStatus.SUCCESS, DeploymentStatus.FAILED]:
            raise ValueError(f"Cannot cancel deployment with status: {deployment.status}")

        deployment.cancel_deployment()
        self.db.commit()

        logger.info(f"Cancelled deployment: {deployment_id}")
        return deployment

    # Retry Logic
    async def retry_deployment(
        self,
        deployment_id: Union[str, UUID],
        request: DeploymentRetryRequest
    ) -> Optional[Deployment]:
        """Retry a failed deployment.

        Args:
            deployment_id: Deployment ID
            request: Retry request

        Returns:
            Updated deployment instance
        """
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            return None

        if not deployment.can_retry() and not request.force_retry:
            raise ValueError(
                f"Cannot retry deployment: max retries ({deployment.max_retries}) exceeded"
            )

        deployment.retry_deployment()
        self.db.commit()

        logger.info(f"Retrying deployment: {deployment_id}")
        return deployment

    async def retry_all_failed_deployments(
        self,
        platform_id: Optional[Union[str, UUID]] = None
    ) -> List[Deployment]:
        """Retry all failed deployments.

        Args:
            platform_id: Optional platform ID to filter by

        Returns:
            List of retried deployments
        """
        query = self.db.query(Deployment).filter(
            and_(
                Deployment.status == DeploymentStatus.FAILED,
                Deployment.retry_count < Deployment.max_retries
            )
        )

        if platform_id:
            query = query.filter(Deployment.platform_id == platform_id)

        failed_deployments = query.all()

        retried = []
        for deployment in failed_deployments:
            try:
                retried_deployment = await self.retry_deployment(
                    deployment.id,
                    DeploymentRetryRequest()
                )
                if retried_deployment:
                    retried.append(retried_deployment)
            except Exception as e:
                logger.error(
                    f"Failed to retry deployment {deployment.id}: {str(e)}"
                )

        logger.info(f"Retried {len(retried)} failed deployments")
        return retried

    # Query Operations
    async def get_deployments_by_platform(
        self,
        platform_id: Union[str, UUID],
        status: Optional[str] = None
    ) -> List[Deployment]:
        """Get deployments by platform.

        Args:
            platform_id: Platform ID
            status: Optional status filter

        Returns:
            List of deployments
        """
        query = self.db.query(Deployment).filter(Deployment.platform_id == platform_id)

        if status:
            query = query.filter(Deployment.status == status)

        return query.all()

    async def get_deployments_by_skill(
        self,
        skill_id: str,
        status: Optional[str] = None
    ) -> List[Deployment]:
        """Get deployments by skill.

        Args:
            skill_id: Skill ID
            status: Optional status filter

        Returns:
            List of deployments
        """
        query = self.db.query(Deployment).filter(Deployment.skill_id == skill_id)

        if status:
            query = query.filter(Deployment.status == status)

        return query.all()

    async def get_active_deployments(self) -> List[Deployment]:
        """Get all active (pending or deploying) deployments.

        Returns:
            List of active deployments
        """
        return self.db.query(Deployment).filter(
            Deployment.status.in_([DeploymentStatus.PENDING, DeploymentStatus.DEPLOYING])
        ).all()

    async def get_recent_deployments(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[Deployment]:
        """Get recent deployments.

        Args:
            hours: Number of hours to look back
            limit: Maximum number of deployments to return

        Returns:
            List of recent deployments
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Deployment).filter(
            Deployment.created_at >= since
        ).order_by(desc(Deployment.created_at)).limit(limit).all()

    async def get_deployment_statistics(
        self,
        platform_id: Optional[Union[str, UUID]] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get deployment statistics.

        Args:
            platform_id: Optional platform ID to filter by
            date_from: Optional start date
            date_to: Optional end date

        Returns:
            Deployment statistics
        """
        query = self.db.query(Deployment)

        if platform_id:
            query = query.filter(Deployment.platform_id == platform_id)

        if date_from:
            query = query.filter(Deployment.created_at >= date_from)

        if date_to:
            query = query.filter(Deployment.created_at <= date_to)

        deployments = query.all()
        return serialize_deployment_statistics(deployments)

    async def get_deployment_by_deployment_id(self, platform_deployment_id: str) -> Optional[Deployment]:
        """Get deployment by platform deployment ID.

        Args:
            platform_deployment_id: Platform-specific deployment ID

        Returns:
            Deployment instance or None
        """
        return self.db.query(Deployment).filter(
            Deployment.deployment_id == platform_deployment_id
        ).first()

    # Status and Progress Tracking
    async def get_deployment_progress(self, deployment_id: Union[str, UUID]) -> Dict[str, Any]:
        """Get deployment progress information.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment progress data
        """
        deployment = await self.get_deployment(deployment_id)
        if not deployment:
            return {}

        return format_deployment_progress(deployment)

    async def get_deployment_status(self, deployment_id: Union[str, UUID]) -> Optional[str]:
        """Get deployment status.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status or None
        """
        deployment = await self.get_deployment(deployment_id)
        return deployment.status if deployment else None

    async def is_deployment_active(self, deployment_id: Union[str, UUID]) -> bool:
        """Check if deployment is active (pending or deploying).

        Args:
            deployment_id: Deployment ID

        Returns:
            True if active, False otherwise
        """
        deployment = await self.get_deployment(deployment_id)
        return deployment.status in [DeploymentStatus.PENDING, DeploymentStatus.DEPLOYING] if deployment else False

    async def is_deployment_successful(self, deployment_id: Union[str, UUID]) -> bool:
        """Check if deployment was successful.

        Args:
            deployment_id: Deployment ID

        Returns:
            True if successful, False otherwise
        """
        deployment = await self.get_deployment(deployment_id)
        return deployment.success is True if deployment else False

    async def can_retry_deployment(self, deployment_id: Union[str, UUID]) -> bool:
        """Check if deployment can be retried.

        Args:
            deployment_id: Deployment ID

        Returns:
            True if can retry, False otherwise
        """
        deployment = await self.get_deployment(deployment_id)
        return deployment.can_retry() if deployment else False

    # Bulk Operations
    async def bulk_create_deployments(
        self,
        requests: List[DeploymentCreateRequest],
        parallel: bool = True
    ) -> List[Deployment]:
        """Create multiple deployments.

        Args:
            requests: List of deployment creation requests
            parallel: Whether to create deployments in parallel

        Returns:
            List of created deployments
        """
        created_deployments = []

        if parallel:
            # Create tasks for parallel execution
            tasks = [
                self.create_deployment(request)
                for request in requests
            ]
            created_deployments = await asyncio.gather(*tasks, return_exceptions=True)
            # Filter out exceptions
            created_deployments = [
                d for d in created_deployments
                if not isinstance(d, Exception)
            ]
        else:
            # Create deployments sequentially
            for request in requests:
                try:
                    deployment = await self.create_deployment(request)
                    created_deployments.append(deployment)
                except Exception as e:
                    logger.error(f"Failed to create deployment: {str(e)}")

        logger.info(f"Created {len(created_deployments)} deployments")
        return created_deployments

    async def bulk_cancel_deployments(
        self,
        deployment_ids: List[Union[str, UUID]]
    ) -> List[Deployment]:
        """Cancel multiple deployments.

        Args:
            deployment_ids: List of deployment IDs

        Returns:
            List of cancelled deployments
        """
        cancelled_deployments = []

        for deployment_id in deployment_ids:
            try:
                deployment = await self.cancel_deployment(deployment_id)
                if deployment:
                    cancelled_deployments.append(deployment)
            except Exception as e:
                logger.error(f"Failed to cancel deployment {deployment_id}: {str(e)}")

        logger.info(f"Cancelled {len(cancelled_deployments)} deployments")
        return cancelled_deployments

    # Utility Methods
    async def deployment_exists(self, deployment_id: Union[str, UUID]) -> bool:
        """Check if deployment exists.

        Args:
            deployment_id: Deployment ID

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(Deployment).filter(Deployment.id == deployment_id).first() is not None

    async def get_deployment_count_by_status(
        self,
        status: str,
        platform_id: Optional[Union[str, UUID]] = None
    ) -> int:
        """Get deployment count by status.

        Args:
            status: Deployment status
            platform_id: Optional platform ID to filter by

        Returns:
            Count of deployments with specified status
        """
        query = self.db.query(Deployment).filter(Deployment.status == status)

        if platform_id:
            query = query.filter(Deployment.platform_id == platform_id)

        return query.count()