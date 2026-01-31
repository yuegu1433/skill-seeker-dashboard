"""Platform deployer for unified multi-platform skill deployment.

This module provides PlatformDeployer class that implements unified
deployment management with status tracking and error handling.
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .registry import get_registry
from .converter import FormatConverter
from .validator import CompatibilityValidator
from .adapters import (
    PlatformAdapter,
    ValidationError,
    DeploymentError,
    PlatformError,
)

logger = logging.getLogger(__name__)


class DeploymentStatus(Enum):
    """Deployment status enumeration."""
    PENDING = "pending"
    VALIDATING = "validating"
    CONVERTING = "converting"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    CANCELLING = "cancelling"


class DeploymentPriority(Enum):
    """Deployment priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class DeploymentTask:
    """Deployment task representation."""
    deployment_id: str
    skill_data: Dict[str, Any]
    source_format: str
    target_platform: str
    target_format: Optional[str] = None
    priority: DeploymentPriority = DeploymentPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    status: DeploymentStatus = DeploymentStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    platform_response: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate deployment duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def can_retry(self) -> bool:
        """Check if deployment can be retried."""
        return (
            self.status == DeploymentStatus.FAILED
            and self.retry_count < self.max_retries
        )


class DeploymentStatistics:
    """Deployment statistics tracker."""

    def __init__(self):
        """Initialize statistics tracker."""
        self.total_deployments = 0
        self.successful_deployments = 0
        self.failed_deployments = 0
        self.cancelled_deployments = 0
        self.retry_attempts = 0
        self.avg_duration = 0.0
        self.status_history: Dict[DeploymentStatus, int] = {
            status: 0 for status in DeploymentStatus
        }
        self.platform_stats: Dict[str, Dict[str, int]] = {}

    def update(self, task: DeploymentTask) -> None:
        """Update statistics with deployment task."""
        self.total_deployments += 1
        self.status_history[task.status] += 1

        # Update success/failure counts
        if task.status == DeploymentStatus.SUCCESS:
            self.successful_deployments += 1
        elif task.status == DeploymentStatus.FAILED:
            self.failed_deployments += 1
        elif task.status == DeploymentStatus.CANCELLED:
            self.cancelled_deployments += 1

        # Update retry count
        if task.retry_count > 0:
            self.retry_attempts += task.retry_count

        # Update platform stats
        platform = task.target_platform
        if platform not in self.platform_stats:
            self.platform_stats[platform] = {
                "total": 0,
                "success": 0,
                "failed": 0
            }

        self.platform_stats[platform]["total"] += 1
        if task.status == DeploymentStatus.SUCCESS:
            self.platform_stats[platform]["success"] += 1
        elif task.status == DeploymentStatus.FAILED:
            self.platform_stats[platform]["failed"] += 1

        # Update average duration
        duration = task.duration_seconds
        if duration:
            self.avg_duration = (
                (self.avg_duration * (self.total_deployments - 1) + duration)
                / self.total_deployments
            )

    def get_success_rate(self) -> float:
        """Calculate success rate percentage."""
        if self.total_deployments == 0:
            return 0.0
        return (self.successful_deployments / self.total_deployments) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert statistics to dictionary."""
        return {
            "total_deployments": self.total_deployments,
            "successful_deployments": self.successful_deployments,
            "failed_deployments": self.failed_deployments,
            "cancelled_deployments": self.cancelled_deployments,
            "retry_attempts": self.retry_attempts,
            "success_rate": self.get_success_rate(),
            "avg_duration_seconds": self.avg_duration,
            "status_history": {k.value: v for k, v in self.status_history.items()},
            "platform_stats": self.platform_stats
        }


class PlatformDeployer:
    """Unified platform deployer for multi-platform skill deployment.

    Provides comprehensive deployment management including:
    - Deployment orchestration
    - Status tracking
    - Error handling
    - Retry mechanisms
    - Batch operations
    """

    def __init__(
        self,
        registry: Optional[PlatformAdapter] = None,
        converter: Optional[FormatConverter] = None,
        validator: Optional[CompatibilityValidator] = None
    ):
        """Initialize platform deployer.

        Args:
            registry: Platform registry instance
            converter: Format converter instance
            validator: Compatibility validator instance
        """
        self.registry = registry or get_registry()
        self.converter = converter or FormatConverter(self.registry)
        self.validator = validator or CompatibilityValidator(self.registry)

        # Active deployments
        self.active_deployments: Dict[str, DeploymentTask] = {}
        self.completed_deployments: Dict[str, DeploymentTask] = {}

        # Deployment queue
        self.deployment_queue: List[DeploymentTask] = []
        self.max_queue_size = 1000

        # Concurrency control
        self.max_concurrent_deployments = 10
        self.executor = ThreadPoolExecutor(max_workers=10)

        # Statistics
        self.stats = DeploymentStatistics()

        # Event handlers
        self.event_handlers = {
            "deployment_start": [],
            "deployment_complete": [],
            "deployment_error": [],
            "deployment_retry": [],
            "deployment_cancel": []
        }

    async def deploy_skill(
        self,
        skill_data: Dict[str, Any],
        target_platform: str,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        deployment_config: Optional[Dict[str, Any]] = None,
        priority: DeploymentPriority = DeploymentPriority.NORMAL,
        max_retries: int = 3,
        async_mode: bool = True
    ) -> Union[DeploymentTask, Dict[str, Any]]:
        """Deploy skill to target platform.

        Args:
            skill_data: Skill data to deploy
            target_platform: Target platform ID
            source_format: Source format (auto-detect if None)
            target_format: Target format (auto-select if None)
            deployment_config: Deployment configuration
            priority: Deployment priority
            max_retries: Maximum retry attempts
            async_mode: If True, returns task immediately (async deployment)

        Returns:
            DeploymentTask (if async_mode) or deployment result (if sync)

        Raises:
            ValidationError: If skill data is invalid
            DeploymentError: If deployment fails
        """
        deployment_id = str(uuid4())

        # Auto-detect source format
        if source_format is None:
            source_format = skill_data.get("format", "json")

        # Auto-select target format
        if target_format is None:
            target_format = await self._select_target_format(
                skill_data,
                source_format,
                target_platform
            )

        # Create deployment task
        task = DeploymentTask(
            deployment_id=deployment_id,
            skill_data=skill_data,
            source_format=source_format,
            target_platform=target_platform,
            target_format=target_format,
            priority=priority,
            max_retries=max_retries,
            metadata=deployment_config or {}
        )

        # Add to active deployments
        self.active_deployments[deployment_id] = task

        if async_mode:
            # Start async deployment
            asyncio.create_task(self._deploy_skill_async(task))
            return task
        else:
            # Perform synchronous deployment
            result = await self._execute_deployment(task)
            return result

    async def deploy_batch(
        self,
        deployments: List[Dict[str, Any]],
        max_concurrent: int = 5,
        wait_for_all: bool = True
    ) -> List[Dict[str, Any]]:
        """Deploy multiple skills concurrently.

        Args:
            deployments: List of deployment requests
            max_concurrent: Maximum concurrent deployments
            wait_for_all: If True, wait for all deployments to complete

        Returns:
            List of deployment results

        Raises:
            DeploymentError: If batch deployment fails
        """
        logger.info(f"Starting batch deployment of {len(deployments)} skills")

        # Create deployment tasks
        tasks = []
        for deployment_request in deployments:
            try:
                task = await self._create_deployment_task(deployment_request)
                tasks.append(task)
                self.active_deployments[task.deployment_id] = task
            except Exception as e:
                logger.error(f"Failed to create deployment task: {str(e)}")
                tasks.append({
                    "deployment_id": str(uuid4()),
                    "status": "failed",
                    "error": str(e),
                    "success": False
                })

        if not wait_for_all:
            # Return task IDs immediately
            return [
                {
                    "deployment_id": task.deployment_id,
                    "status": task.status.value,
                    "success": True
                }
                for task in tasks if isinstance(task, DeploymentTask)
            ]

        # Wait for all deployments to complete
        semaphore = asyncio.Semaphore(max_concurrent)

        async def deploy_with_semaphore(task: DeploymentTask):
            async with semaphore:
                result = await self._execute_deployment(task)
                return result

        # Execute deployments
        deployment_coroutines = [
            deploy_with_semaphore(task) if isinstance(task, DeploymentTask) else task
            for task in tasks
        ]

        results = await asyncio.gather(*deployment_coroutines, return_exceptions=True)

        # Process results
        successful_results = []
        failed_results = []

        for result in results:
            if isinstance(result, Exception):
                failed_results.append({
                    "error": str(result),
                    "success": False
                })
            else:
                successful_results.append(result)

        logger.info(
            f"Batch deployment completed: "
            f"{len(successful_results)} successful, {len(failed_results)} failed"
        )

        return successful_results + failed_results

    async def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status or None if not found
        """
        # Check active deployments
        if deployment_id in self.active_deployments:
            task = self.active_deployments[deployment_id]
            return self._task_to_dict(task)

        # Check completed deployments
        if deployment_id in self.completed_deployments:
            task = self.completed_deployments[deployment_id]
            return self._task_to_dict(task)

        return None

    async def cancel_deployment(
        self,
        deployment_id: str,
        force: bool = False
    ) -> bool:
        """Cancel deployment.

        Args:
            deployment_id: Deployment ID
            force: If True, force cancellation even if in progress

        Returns:
            True if cancellation successful
        """
        # Check active deployments
        if deployment_id not in self.active_deployments:
            logger.warning(f"Deployment not found: {deployment_id}")
            return False

        task = self.active_deployments[deployment_id]

        # Check if can be cancelled
        if not force and task.status in [
            DeploymentStatus.SUCCESS,
            DeploymentStatus.FAILED,
            DeploymentStatus.CANCELLED
        ]:
            logger.warning(f"Deployment cannot be cancelled: {deployment_id}")
            return False

        # Update status
        task.status = DeploymentStatus.CANCELLING
        task.completed_at = datetime.utcnow()

        # Cancel via platform adapter
        try:
            adapter = self.registry.get_adapter(task.target_platform)
            if adapter and hasattr(adapter, "cancel_deployment"):
                await adapter.cancel_deployment(deployment_id)

            task.status = DeploymentStatus.CANCELLED
            logger.info(f"Deployment cancelled: {deployment_id}")

            # Move to completed
            self.completed_deployments[deployment_id] = task
            del self.active_deployments[deployment_id]

            # Update statistics
            self.stats.update(task)

            # Emit event
            await self._emit_event("deployment_cancel", {
                "deployment_id": deployment_id,
                "task": task
            })

            return True

        except Exception as e:
            logger.error(f"Failed to cancel deployment: {str(e)}")
            task.error_message = f"Cancellation failed: {str(e)}"
            task.status = DeploymentStatus.FAILED
            return False

    async def retry_deployment(
        self,
        deployment_id: str,
        new_config: Optional[Dict[str, Any]] = None
    ) -> Optional[DeploymentTask]:
        """Retry failed deployment.

        Args:
            deployment_id: Original deployment ID
            new_config: New deployment configuration

        Returns:
            New deployment task or None if retry not possible
        """
        # Get original task
        if deployment_id not in self.completed_deployments:
            logger.error(f"Deployment not found for retry: {deployment_id}")
            return None

        original_task = self.completed_deployments[deployment_id]

        if not original_task.can_retry:
            logger.warning(f"Deployment cannot be retried: {deployment_id}")
            return None

        # Create new deployment task
        new_task = DeploymentTask(
            deployment_id=str(uuid4()),
            skill_data=original_task.skill_data,
            source_format=original_task.source_format,
            target_platform=original_task.target_platform,
            target_format=original_task.target_format,
            priority=original_task.priority,
            max_retries=original_task.max_retries,
            retry_count=original_task.retry_count + 1,
            metadata=new_config or original_task.metadata
        )

        # Add to active deployments
        self.active_deployments[new_task.deployment_id] = new_task

        # Start retry deployment
        asyncio.create_task(self._deploy_skill_async(new_task))

        # Update original task
        original_task.status = DeploymentStatus.RETRYING

        logger.info(f"Retrying deployment: {deployment_id} -> {new_task.deployment_id}")

        # Emit event
        await self._emit_event("deployment_retry", {
            "original_deployment_id": deployment_id,
            "new_deployment_id": new_task.deployment_id,
            "retry_count": new_task.retry_count
        })

        return new_task

    async def list_deployments(
        self,
        status: Optional[DeploymentStatus] = None,
        platform: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List deployments.

        Args:
            status: Filter by status
            platform: Filter by platform
            limit: Maximum number of deployments to return
            offset: Offset for pagination

        Returns:
            List of deployment summaries
        """
        all_deployments = list(self.active_deployments.values()) + list(
            self.completed_deployments.values()
        )

        # Apply filters
        if status:
            all_deployments = [t for t in all_deployments if t.status == status]

        if platform:
            all_deployments = [t for t in all_deployments if t.target_platform == platform]

        # Sort by creation time (newest first)
        all_deployments.sort(key=lambda t: t.created_at, reverse=True)

        # Apply pagination
        paginated = all_deployments[offset:offset + limit]

        return [self._task_to_dict(task) for task in paginated]

    def get_statistics(self) -> Dict[str, Any]:
        """Get deployment statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats.to_dict()

    def get_active_deployment_count(self) -> int:
        """Get number of active deployments.

        Returns:
            Number of active deployments
        """
        return len(self.active_deployments)

    def get_queue_size(self) -> int:
        """Get deployment queue size.

        Returns:
            Queue size
        """
        return len(self.deployment_queue)

    async def cleanup_completed_deployments(self, older_than_hours: int = 24) -> int:
        """Cleanup completed deployments older than specified hours.

        Args:
            older_than_hours: Remove deployments older than this many hours

        Returns:
            Number of deployments removed
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        to_remove = []

        for deployment_id, task in self.completed_deployments.items():
            if task.completed_at and task.completed_at < cutoff_time:
                to_remove.append(deployment_id)

        for deployment_id in to_remove:
            del self.completed_deployments[deployment_id]

        logger.info(f"Cleaned up {len(to_remove)} completed deployments")
        return len(to_remove)

    # Private methods

    async def _deploy_skill_async(self, task: DeploymentTask) -> None:
        """Execute deployment asynchronously.

        Args:
            task: Deployment task
        """
        try:
            await self._execute_deployment(task)
        except Exception as e:
            logger.error(f"Async deployment error: {str(e)}")
            task.status = DeploymentStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()

    async def _execute_deployment(self, task: DeploymentTask) -> Dict[str, Any]:
        """Execute deployment workflow.

        Args:
            task: Deployment task

        Returns:
            Deployment result

        Raises:
            DeploymentError: If deployment fails
        """
        task.started_at = datetime.utcnow()
        task.status = DeploymentStatus.PENDING

        logger.info(f"Starting deployment: {task.deployment_id} to {task.target_platform}")

        try:
            # Emit start event
            await self._emit_event("deployment_start", {
                "deployment_id": task.deployment_id,
                "task": task
            })

            # Step 1: Validate skill
            task.status = DeploymentStatus.VALIDATING
            await self._validate_skill(task)

            # Step 2: Convert format if needed
            if task.source_format != task.target_format:
                task.status = DeploymentStatus.CONVERTING
                await self._convert_skill(task)

            # Step 3: Deploy to platform
            task.status = DeploymentStatus.DEPLOYING
            result = await self._deploy_to_platform(task)

            # Update task
            task.status = DeploymentStatus.SUCCESS
            task.completed_at = datetime.utcnow()
            task.platform_response = result

            # Move to completed
            self.completed_deployments[task.deployment_id] = task
            if task.deployment_id in self.active_deployments:
                del self.active_deployments[task.deployment_id]

            # Update statistics
            self.stats.update(task)

            # Emit completion event
            await self._emit_event("deployment_complete", {
                "deployment_id": task.deployment_id,
                "task": task,
                "result": result
            })

            logger.info(f"Deployment completed: {task.deployment_id}")
            return self._task_to_dict(task)

        except Exception as e:
            # Handle error
            task.status = DeploymentStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error_message = str(e)

            # Update statistics
            self.stats.update(task)

            # Emit error event
            await self._emit_event("deployment_error", {
                "deployment_id": task.deployment_id,
                "task": task,
                "error": str(e)
            })

            # Check if can retry
            if task.can_retry:
                logger.warning(f"Deployment failed, can retry: {task.deployment_id}")
                # Don't retry automatically, let user decide
            else:
                logger.error(f"Deployment failed: {task.deployment_id}")

            # Move to completed
            self.completed_deployments[task.deployment_id] = task
            if task.deployment_id in self.active_deployments:
                del self.active_deployments[task.deployment_id]

            raise

    async def _validate_skill(self, task: DeploymentTask) -> None:
        """Validate skill for deployment.

        Args:
            task: Deployment task

        Raises:
            ValidationError: If validation fails
        """
        # Check if platform is available
        adapter = self.registry.get_adapter(task.target_platform)
        if not adapter:
            raise ValidationError(
                f"Platform adapter not found: {task.target_platform}",
                platform=task.target_platform
            )

        # Validate with platform adapter
        if hasattr(adapter, "validate_skill"):
            validation_result = await adapter.validate_skill(task.skill_data)
            if not validation_result["valid"]:
                raise ValidationError(
                    f"Skill validation failed: {validation_result['errors']}",
                    platform=task.target_platform,
                    details=validation_result
                )

        # Validate format compatibility
        if hasattr(adapter, "validate_skill_format"):
            format_result = await adapter.validate_skill_format(
                task.skill_data,
                task.source_format
            )
            if not format_result["valid"]:
                raise ValidationError(
                    f"Format validation failed: {format_result['errors']}",
                    platform=task.target_platform,
                    details=format_result
                )

    async def _convert_skill(self, task: DeploymentTask) -> None:
        """Convert skill to target format.

        Args:
            task: Deployment task

        Raises:
            ConversionError: If conversion fails
        """
        # Get platform adapter
        adapter = self.registry.get_adapter(task.target_platform)
        if not adapter:
            raise ValidationError(
                f"Platform adapter not found: {task.target_platform}",
                platform=task.target_platform
            )

        # Try adapter conversion first
        if hasattr(adapter, "convert_skill"):
            try:
                converted = await adapter.convert_skill(
                    task.skill_data,
                    task.source_format,
                    task.target_format
                )
                task.skill_data = converted
                return
            except Exception as e:
                logger.warning(f"Adapter conversion failed, trying converter: {str(e)}")

        # Fallback to format converter
        try:
            converted = await self.converter.convert(
                task.skill_data,
                task.source_format,
                task.target_format,
                platform_id=task.target_platform
            )
            task.skill_data = converted
        except Exception as e:
            raise ConversionError(
                f"Skill conversion failed: {str(e)}",
                source_format=task.source_format,
                target_format=task.target_format,
                platform=task.target_platform
            )

    async def _deploy_to_platform(self, task: DeploymentTask) -> Dict[str, Any]:
        """Deploy skill to target platform.

        Args:
            task: Deployment task

        Returns:
            Platform deployment result

        Raises:
            DeploymentError: If deployment fails
        """
        adapter = self.registry.get_adapter(task.target_platform)
        if not adapter:
            raise DeploymentError(
                f"Platform adapter not found: {task.target_platform}",
                platform=task.target_platform
            )

        # Deploy via adapter
        if hasattr(adapter, "deploy_skill"):
            try:
                result = await adapter.deploy_skill(
                    task.skill_data,
                    deployment_config=task.metadata
                )
                return result
            except Exception as e:
                raise DeploymentError(
                    f"Platform deployment failed: {str(e)}",
                    platform=task.target_platform,
                    details={"error": str(e)}
                )
        else:
            raise DeploymentError(
                f"Adapter does not support deployment: {task.target_platform}",
                platform=task.target_platform
            )

    async def _create_deployment_task(
        self,
        deployment_request: Dict[str, Any]
    ) -> DeploymentTask:
        """Create deployment task from request.

        Args:
            deployment_request: Deployment request

        Returns:
            Deployment task

        Raises:
            ValidationError: If request is invalid
        """
        required_fields = ["skill_data", "target_platform"]
        for field in required_fields:
            if field not in deployment_request:
                raise ValidationError(
                    f"Missing required field: {field}",
                    details={"request": deployment_request}
                )

        return DeploymentTask(
            deployment_id=str(uuid4()),
            skill_data=deployment_request["skill_data"],
            source_format=deployment_request.get("source_format", "json"),
            target_platform=deployment_request["target_platform"],
            target_format=deployment_request.get("target_format"),
            priority=DeploymentPriority(
                deployment_request.get("priority", DeploymentPriority.NORMAL.value)
            ),
            max_retries=deployment_request.get("max_retries", 3),
            metadata=deployment_request.get("deployment_config", {})
        )

    async def _select_target_format(
        self,
        skill_data: Dict[str, Any],
        source_format: str,
        target_platform: str
    ) -> str:
        """Auto-select target format for platform.

        Args:
            skill_data: Skill data
            source_format: Source format
            target_platform: Target platform

        Returns:
            Selected target format
        """
        # Get platform adapter
        adapter = self.registry.get_adapter(target_platform)
        if not adapter:
            return source_format  # Fallback to source format

        # Check if source format is supported
        if source_format in adapter.supported_formats:
            return source_format

        # Find best matching format
        format_preferences = ["json", "yaml", "markdown"]

        for preferred_format in format_preferences:
            if preferred_format in adapter.supported_formats:
                return preferred_format

        # Return first supported format
        return adapter.supported_formats[0] if adapter.supported_formats else source_format

    def _task_to_dict(self, task: DeploymentTask) -> Dict[str, Any]:
        """Convert deployment task to dictionary.

        Args:
            task: Deployment task

        Returns:
            Task dictionary
        """
        return {
            "deployment_id": task.deployment_id,
            "skill_name": task.skill_data.get("name", "Unknown"),
            "source_format": task.source_format,
            "target_platform": task.target_platform,
            "target_format": task.target_format,
            "status": task.status.value,
            "priority": task.priority.value,
            "retry_count": task.retry_count,
            "max_retries": task.max_retries,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "duration_seconds": task.duration_seconds,
            "error_message": task.error_message,
            "error_details": task.error_details,
            "platform_response": task.platform_response,
            "metadata": task.metadata,
            "can_retry": task.can_retry
        }

    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit deployment event.

        Args:
            event_type: Event type
            event_data: Event data
        """
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_data)
                else:
                    handler(event_data)
            except Exception as e:
                logger.warning(f"Event handler error: {str(e)}")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        self.executor.shutdown(wait=True)