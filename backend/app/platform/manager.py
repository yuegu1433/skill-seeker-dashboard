"""Platform manager for unified multi-platform skill management.

This module provides PlatformManager class that orchestrates all
platform components for comprehensive management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union
from dataclasses import dataclass, field

from .registry import get_registry
from .converter import FormatConverter
from .validator import CompatibilityValidator
from .deployer import PlatformDeployer, DeploymentTask, DeploymentPriority
from .monitor import PlatformMonitor, Alert, AlertSeverity
from .adapters import (
    PlatformAdapter,
    ValidationError,
    DeploymentError,
    PlatformError,
)

logger = logging.getLogger(__name__)


@dataclass
class PlatformStatistics:
    """Platform management statistics."""
    total_platforms: int = 0
    active_platforms: int = 0
    total_skills: int = 0
    active_deployments: int = 0
    completed_deployments: int = 0
    successful_deployments: int = 0
    failed_deployments: int = 0
    active_alerts: int = 0
    format_conversions: int = 0
    compatibility_checks: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)


class PlatformManager:
    """Unified platform manager for multi-platform skill management.

    Orchestrates all platform components including:
    - Platform registry management
    - Format conversion
    - Compatibility validation
    - Skill deployment
    - Health monitoring
    - Analytics and reporting
    """

    def __init__(
        self,
        registry: Optional[PlatformAdapter] = None,
        converter: Optional[FormatConverter] = None,
        validator: Optional[CompatibilityValidator] = None,
        deployer: Optional[PlatformDeployer] = None,
        monitor: Optional[PlatformMonitor] = None
    ):
        """Initialize platform manager.

        Args:
            registry: Platform registry instance
            converter: Format converter instance
            validator: Compatibility validator instance
            deployer: Platform deployer instance
            monitor: Platform monitor instance
        """
        # Initialize components
        self.registry = registry or get_registry()
        self.converter = converter or FormatConverter(self.registry)
        self.validator = validator or CompatibilityValidator(self.registry)
        self.deployer = deployer or PlatformDeployer(
            self.registry,
            self.converter,
            self.validator
        )
        self.monitor = monitor or PlatformMonitor(self.registry)

        # Management statistics
        self.stats = PlatformStatistics()

        # Event handlers
        self.event_handlers = {
            "skill_deployed": [],
            "deployment_completed": [],
            "platform_status_changed": [],
            "alert_triggered": []
        }

        # Auto-start monitoring
        self._monitoring_started = False

    async def initialize(self) -> bool:
        """Initialize the platform manager.

        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing platform manager...")

            # Initialize registry
            if not hasattr(self.registry, 'initialized') or not self.registry.initialized:
                # Register default adapters
                await self._register_default_adapters()

            # Start monitoring
            if not self._monitoring_started:
                await self.monitor.start_monitoring()
                self._monitoring_started = True

            # Update statistics
            await self._update_statistics()

            logger.info("Platform manager initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize platform manager: {str(e)}")
            return False

    async def shutdown(self) -> None:
        """Shutdown the platform manager."""
        try:
            logger.info("Shutting down platform manager...")

            # Stop monitoring
            if self._monitoring_started:
                await self.monitor.stop_monitoring()
                self._monitoring_started = False

            logger.info("Platform manager shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")

    # Core Management Methods

    async def deploy_skill(
        self,
        skill_data: Dict[str, Any],
        target_platforms: Union[str, List[str]],
        source_format: Optional[str] = None,
        target_formats: Optional[Dict[str, str]] = None,
        deployment_config: Optional[Dict[str, Any]] = None,
        validate_compatibility: bool = True,
        auto_retry: bool = True,
        async_mode: bool = True
    ) -> Union[List[DeploymentTask], List[Dict[str, Any]]]:
        """Deploy skill to one or more platforms.

        Args:
            skill_data: Skill data to deploy
            target_platforms: Target platform(s)
            source_format: Source format (auto-detect if None)
            target_formats: Map of platform to target format
            deployment_config: Deployment configuration
            validate_compatibility: If True, validate compatibility first
            auto_retry: If True, enable auto-retry for deployments
            async_mode: If True, return tasks immediately

        Returns:
            List of deployment tasks (if async_mode) or results (if sync)

        Raises:
            ValidationError: If skill validation fails
            DeploymentError: If deployment fails
        """
        logger.info(f"Deploying skill to platforms: {target_platforms}")

        # Normalize target platforms
        if isinstance(target_platforms, str):
            target_platforms = [target_platforms]

        # Validate compatibility if requested
        if validate_compatibility:
            compatibility_report = await self.validator.validate_compatibility(
                skill_data,
                target_platforms=target_platforms
            )

            if not compatibility_report["overall_compatible"]:
                raise ValidationError(
                    f"Skill compatibility validation failed: {compatibility_report['incompatible_platforms']}",
                    details=compatibility_report
                )

        # Prepare deployments
        deployments = []
        for platform in target_platforms:
            target_format = target_formats.get(platform) if target_formats else None
            priority = DeploymentPriority.NORMAL

            # Deploy skill
            task = await self.deployer.deploy_skill(
                skill_data=skill_data,
                target_platform=platform,
                source_format=source_format,
                target_format=target_format,
                deployment_config=deployment_config,
                priority=priority,
                async_mode=async_mode
            )

            deployments.append(task)

        # Update statistics
        await self._update_statistics()

        # Emit event
        await self._emit_event("skill_deployed", {
            "skill_name": skill_data.get("name", "Unknown"),
            "target_platforms": target_platforms,
            "deployments": deployments
        })

        if async_mode:
            return deployments
        else:
            return [await self.deployer.get_deployment_status(task.deployment_id) for task in deployments]

    async def deploy_with_fallback(
        self,
        skill_data: Dict[str, Any],
        preferred_platforms: List[str],
        fallback_platforms: Optional[List[str]] = None,
        source_format: Optional[str] = None,
        deployment_config: Optional[Dict[str, Any]] = None,
        validate_compatibility: bool = True
    ) -> Dict[str, Any]:
        """Deploy skill with fallback strategy.

        Args:
            skill_data: Skill data
            preferred_platforms: List of preferred platforms in order
            fallback_platforms: List of fallback platforms
            source_format: Source format
            deployment_config: Deployment configuration
            validate_compatibility: If True, validate compatibility first

        Returns:
            Deployment result with fallback information

        Raises:
            ValidationError: If skill validation fails
            DeploymentError: If all deployments fail
        """
        logger.info(f"Deploying skill with fallback: {preferred_platforms}")

        # Combine platforms
        all_platforms = preferred_platforms.copy()
        if fallback_platforms:
            all_platforms.extend(fallback_platforms)

        # Remove duplicates while preserving order
        seen = set()
        unique_platforms = [p for p in all_platforms if not (p in seen or seen.add(p))]

        # Validate compatibility
        if validate_compatibility:
            compatibility_report = await self.validator.validate_compatibility(
                skill_data,
                target_platforms=unique_platforms
            )

            # Filter to compatible platforms
            compatible_platforms = compatibility_report["compatible_platforms"]

            # Filter preferred platforms to only compatible ones
            preferred_compatible = [
                p for p in preferred_platforms if p in compatible_platforms
            ]

            if not preferred_compatible and compatible_platforms:
                logger.warning("No preferred platforms compatible, using compatible platforms")
                preferred_compatible = compatible_platforms[:1]  # Use first compatible

            if not preferred_compatible:
                raise DeploymentError(
                    "No compatible platforms found for deployment",
                    details=compatibility_report
                )
        else:
            preferred_compatible = preferred_platforms

        # Try deployment to preferred platforms
        successful_deployments = []
        failed_deployments = []

        for platform in preferred_compatible:
            try:
                result = await self.deploy_skill(
                    skill_data=skill_data,
                    target_platforms=platform,
                    source_format=source_format,
                    deployment_config=deployment_config,
                    validate_compatibility=False,  # Already validated
                    async_mode=False
                )

                successful_deployments.append({
                    "platform": platform,
                    "deployment": result[0] if isinstance(result, list) else result
                })

                logger.info(f"Successfully deployed to {platform}")

            except Exception as e:
                logger.error(f"Failed to deploy to {platform}: {str(e)}")
                failed_deployments.append({
                    "platform": platform,
                    "error": str(e)
                })

        # If no successful deployments and fallback available, try fallback
        if not successful_deployments and fallback_platforms:
            logger.info("Attempting fallback deployment...")

            for platform in fallback_platforms:
                try:
                    result = await self.deploy_skill(
                        skill_data=skill_data,
                        target_platforms=platform,
                        source_format=source_format,
                        deployment_config=deployment_config,
                        validate_compatibility=False,
                        async_mode=False
                    )

                    successful_deployments.append({
                        "platform": platform,
                        "deployment": result[0] if isinstance(result, list) else result,
                        "fallback": True
                    })

                    logger.info(f"Fallback deployment successful to {platform}")
                    break

                except Exception as e:
                    logger.error(f"Fallback deployment failed to {platform}: {str(e)}")
                    failed_deployments.append({
                        "platform": platform,
                        "error": str(e),
                        "fallback": True
                    })

        # Return result
        result = {
            "skill_name": skill_data.get("name", "Unknown"),
            "successful_deployments": successful_deployments,
            "failed_deployments": failed_deployments,
            "total_attempted": len(unique_platforms),
            "success": len(successful_deployments) > 0
        }

        if not result["success"]:
            raise DeploymentError(
                "All deployment attempts failed",
                details=result
            )

        return result

    async def convert_skill_format(
        self,
        skill_data: Dict[str, Any],
        target_format: str,
        source_format: Optional[str] = None,
        platform_id: Optional[str] = None,
        conversion_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convert skill to different format.

        Args:
            skill_data: Skill data to convert
            target_format: Target format
            source_format: Source format (auto-detect if None)
            platform_id: Optional platform for platform-specific conversion
            conversion_config: Conversion configuration

        Returns:
            Converted skill data

        Raises:
            ConversionError: If conversion fails
        """
        if source_format is None:
            source_format = skill_data.get("format", "json")

        logger.info(f"Converting skill from {source_format} to {target_format}")

        result = await self.converter.convert(
            skill_data=skill_data,
            source_format=source_format,
            target_format=target_format,
            platform_id=platform_id,
            conversion_config=conversion_config
        )

        # Update statistics
        self.stats.format_conversions += 1
        await self._update_statistics()

        return result

    async def validate_skill_compatibility(
        self,
        skill_data: Dict[str, Any],
        target_platforms: Optional[List[str]] = None,
        validation_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Validate skill compatibility across platforms.

        Args:
            skill_data: Skill data to validate
            target_platforms: List of platforms to validate against
            validation_config: Validation configuration

        Returns:
            Compatibility validation report

        Raises:
            ValidationError: If validation fails
        """
        logger.info(f"Validating skill compatibility for platforms: {target_platforms}")

        result = await self.validator.validate_compatibility(
            skill_data=skill_data,
            target_platforms=target_platforms,
            validation_config=validation_config
        )

        # Update statistics
        self.stats.compatibility_checks += 1
        await self._update_statistics()

        return result

    async def get_platform_health(self) -> Dict[str, Any]:
        """Get health status for all platforms.

        Returns:
            Dictionary of platform health snapshots
        """
        return self.monitor.get_all_platforms_status()

    async def get_deployment_status(
        self,
        deployment_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get deployment status.

        Args:
            deployment_id: Deployment ID

        Returns:
            Deployment status or None if not found
        """
        return await self.deployer.get_deployment_status(deployment_id)

    async def cancel_deployment(
        self,
        deployment_id: str,
        force: bool = False
    ) -> bool:
        """Cancel deployment.

        Args:
            deployment_id: Deployment ID
            force: Force cancellation

        Returns:
            True if cancellation successful
        """
        return await self.deployer.cancel_deployment(deployment_id, force)

    async def retry_deployment(
        self,
        deployment_id: str,
        new_config: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Retry failed deployment.

        Args:
            deployment_id: Original deployment ID
            new_config: New deployment configuration

        Returns:
            New deployment task or None if retry not possible
        """
        task = await self.deployer.retry_deployment(deployment_id, new_config)
        if task:
            return await self.deployer.get_deployment_status(task.deployment_id)
        return None

    async def list_deployments(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List deployments.

        Args:
            status: Filter by status
            platform: Filter by platform
            limit: Maximum number of deployments
            offset: Offset for pagination

        Returns:
            List of deployment summaries
        """
        from .deployer import DeploymentStatus

        status_enum = None
        if status:
            try:
                status_enum = DeploymentStatus(status)
            except ValueError:
                logger.warning(f"Invalid status filter: {status}")

        return await self.deployer.list_deployments(
            status=status_enum,
            platform=platform,
            limit=limit,
            offset=offset
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get platform management statistics.

        Returns:
            Statistics dictionary
        """
        # Merge statistics from all components
        deployer_stats = self.deployer.get_statistics()
        monitor_summary = self.monitor.get_monitoring_summary()

        return {
            "platform_manager": self.stats.__dict__,
            "registry": {
                "registered_platforms": len(self.registry.get_registered_platforms())
            },
            "deployer": deployer_stats,
            "monitor": monitor_summary,
            "converter": self.converter.get_conversion_statistics(),
            "validator": self.validator.get_validation_statistics()
        }

    async def get_platform_summary(self) -> Dict[str, Any]:
        """Get comprehensive platform summary.

        Returns:
            Platform summary dictionary
        """
        # Get platform health
        health_status = await self.get_platform_health()

        # Get active deployments
        active_deployments = await self.deployer.list_deployments(limit=10)

        # Get active alerts
        active_alerts = self.monitor.get_active_alerts()

        # Compile summary
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "platforms": {
                "total": len(health_status),
                "healthy": sum(1 for s in health_status.values() if s.status.value == "healthy"),
                "degraded": sum(1 for s in health_status.values() if s.status.value == "degraded"),
                "unhealthy": sum(1 for s in health_status.values() if s.status.value == "unhealthy")
            },
            "deployments": {
                "active": len([d for d in active_deployments if d["status"] in ["pending", "validating", "converting", "deploying"]]),
                "recent": active_deployments
            },
            "alerts": {
                "active": len(active_alerts),
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "list": [
                    {
                        "alert_id": a.alert_id,
                        "platform_id": a.platform_id,
                        "severity": a.severity.value,
                        "title": a.title,
                        "message": a.message,
                        "created_at": a.created_at.isoformat(),
                        "acknowledged": a.acknowledged
                    }
                    for a in active_alerts[:10]  # Latest 10 alerts
                ]
            },
            "platform_details": {
                platform_id: {
                    "status": snapshot.status.value,
                    "last_check": snapshot.last_check.isoformat(),
                    "consecutive_failures": snapshot.consecutive_failures,
                    "health_checks": [
                        {
                            "name": check.status.value,
                            "message": check.message,
                            "response_time_ms": check.response_time_ms
                        }
                        for check in snapshot.health_checks
                    ]
                }
                for platform_id, snapshot in health_status.items()
            }
        }

        return summary

    async def health_check(self) -> Dict[str, Any]:
        """Perform overall health check.

        Returns:
            Health check result
        """
        try:
            # Check all components
            registry_healthy = len(self.registry.get_registered_platforms()) > 0
            monitor_healthy = self.monitor.is_monitoring
            deployer_healthy = self.deployer.get_active_deployment_count() >= 0

            overall_healthy = registry_healthy and monitor_healthy and deployer_healthy

            return {
                "healthy": overall_healthy,
                "timestamp": datetime.utcnow().isoformat(),
                "components": {
                    "registry": {
                        "healthy": registry_healthy,
                        "registered_platforms": len(self.registry.get_registered_platforms())
                    },
                    "monitor": {
                        "healthy": monitor_healthy,
                        "check_interval": self.monitor.check_interval
                    },
                    "deployer": {
                        "healthy": deployer_healthy,
                        "active_deployments": self.deployer.get_active_deployment_count()
                    },
                    "converter": {
                        "healthy": True,
                        "supported_formats": len(self.converter.get_supported_formats())
                    },
                    "validator": {
                        "healthy": True
                    }
                }
            }

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    # Event Handling

    def add_event_handler(
        self,
        event_type: str,
        handler: callable
    ) -> None:
        """Add event handler.

        Args:
            event_type: Event type
            handler: Event handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)

        # Also add to underlying components
        self.monitor.add_event_handler(event_type, handler)

    # Private Methods

    async def _register_default_adapters(self) -> None:
        """Register default platform adapters."""
        try:
            # Import adapters
            from .adapters import (
                ClaudeAdapter,
                GeminiAdapter,
                OpenAIAdapter,
                MarkdownAdapter
            )

            # Register adapters
            adapters = [
                ClaudeAdapter,
                GeminiAdapter,
                OpenAIAdapter,
                MarkdownAdapter
            ]

            for adapter_class in adapters:
                try:
                    self.registry.register_adapter(adapter_class)
                    logger.info(f"Registered adapter: {adapter_class.platform_id}")
                except Exception as e:
                    logger.warning(f"Failed to register adapter {adapter_class.platform_id}: {str(e)}")

        except ImportError as e:
            logger.warning(f"Could not import default adapters: {str(e)}")

    async def _update_statistics(self) -> None:
        """Update management statistics."""
        try:
            # Get current stats
            deployer_stats = self.deployer.get_statistics()
            monitor_summary = self.monitor.get_monitoring_summary()

            # Update stats
            self.stats.total_platforms = monitor_summary.get("total_platforms", 0)
            self.stats.active_platforms = (
                monitor_summary.get("healthy_platforms", 0) +
                monitor_summary.get("degraded_platforms", 0)
            )
            self.stats.active_deployments = deployer_stats.get("total_deployments", 0) - (
                deployer_stats.get("successful_deployments", 0) +
                deployer_stats.get("failed_deployments", 0) +
                deployer_stats.get("cancelled_deployments", 0)
            )
            self.stats.completed_deployments = (
                deployer_stats.get("successful_deployments", 0) +
                deployer_stats.get("failed_deployments", 0) +
                deployer_stats.get("cancelled_deployments", 0)
            )
            self.stats.successful_deployments = deployer_stats.get("successful_deployments", 0)
            self.stats.failed_deployments = deployer_stats.get("failed_deployments", 0)
            self.stats.active_alerts = monitor_summary.get("active_alerts", 0)
            self.stats.last_updated = datetime.utcnow()

        except Exception as e:
            logger.warning(f"Failed to update statistics: {str(e)}")

    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit event to handlers.

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
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()