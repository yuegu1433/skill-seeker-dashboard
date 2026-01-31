"""Platform monitor for real-time platform health monitoring.

This module provides PlatformMonitor class that implements
real-time platform status monitoring and health checks.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from .registry import get_registry
from .adapters import (
    PlatformAdapter,
    PlatformError,
)

logger = logging.getLogger(__name__)


class PlatformStatus(Enum):
    """Platform status enumeration."""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class HealthCheckStatus(Enum):
    """Health check status enumeration."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass
class HealthCheckResult:
    """Health check result representation."""
    platform_id: str
    status: HealthCheckStatus
    message: str
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def is_healthy(self) -> bool:
        """Check if health check indicates healthy status."""
        return self.status in [HealthCheckStatus.PASS, HealthCheckStatus.WARN]


@dataclass
class PlatformHealthSnapshot:
    """Platform health snapshot."""
    platform_id: str
    status: PlatformStatus
    last_check: datetime
    consecutive_failures: int = 0
    health_checks: List[HealthCheckResult] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        """Check if platform is healthy."""
        return self.status == PlatformStatus.HEALTHY


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert representation."""
    alert_id: str
    platform_id: str
    severity: AlertSeverity
    title: str
    message: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_active(self) -> bool:
        """Check if alert is still active."""
        return self.resolved_at is None


class PlatformMonitor:
    """Platform health monitor for real-time status monitoring.

    Provides comprehensive monitoring including:
    - Periodic health checks
    - Status tracking
    - Alert generation
    - Performance metrics
    - Real-time notifications
    """

    def __init__(self, registry: Optional[PlatformAdapter] = None):
        """Initialize platform monitor.

        Args:
            registry: Platform registry instance
        """
        self.registry = registry or get_registry()

        # Health snapshots
        self.health_snapshots: Dict[str, PlatformHealthSnapshot] = {}

        # Alert management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Monitoring configuration
        self.check_interval = 60  # seconds
        self.alert_threshold_failures = 3
        self.response_time_threshold = 5000  # milliseconds
        self.monitoring_enabled = True

        # Health check definitions
        self.health_checks = self._init_health_checks()

        # Event handlers
        self.event_handlers = {
            "health_check": [],
            "status_change": [],
            "alert_triggered": [],
            "alert_resolved": []
        }

        # Background monitoring task
        self.monitoring_task: Optional[asyncio.Task] = None
        self.is_monitoring = False

    def _init_health_checks(self) -> Dict[str, Dict[str, Any]]:
        """Initialize health check definitions.

        Returns:
            Health checks configuration
        """
        return {
            "connectivity": {
                "name": "Platform Connectivity",
                "description": "Check if platform is reachable",
                "method": "api_call",
                "timeout": 30,
                "weight": 10
            },
            "capability": {
                "name": "Platform Capabilities",
                "description": "Verify platform capabilities",
                "method": "capability_check",
                "timeout": 15,
                "weight": 8
            },
            "performance": {
                "name": "Platform Performance",
                "description": "Check platform response time",
                "method": "performance_check",
                "timeout": 10,
                "weight": 5
            },
            "limits": {
                "name": "Platform Limits",
                "description": "Verify platform limits",
                "method": "limits_check",
                "timeout": 5,
                "weight": 3
            }
        }

    async def start_monitoring(self, check_interval: Optional[int] = None) -> None:
        """Start monitoring all platforms.

        Args:
            check_interval: Override default check interval
        """
        if self.is_monitoring:
            logger.warning("Monitoring already started")
            return

        if check_interval:
            self.check_interval = check_interval

        self.monitoring_enabled = True
        self.is_monitoring = True

        # Initialize health snapshots for all registered platforms
        for platform_id in self.registry.get_registered_platforms():
            if platform_id not in self.health_snapshots:
                self.health_snapshots[platform_id] = PlatformHealthSnapshot(
                    platform_id=platform_id,
                    status=PlatformStatus.UNKNOWN,
                    last_check=datetime.utcnow()
                )

        # Start monitoring task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        logger.info(f"Platform monitoring started with interval {self.check_interval}s")

    async def stop_monitoring(self) -> None:
        """Stop monitoring all platforms."""
        if not self.is_monitoring:
            logger.warning("Monitoring not running")
            return

        self.monitoring_enabled = False
        self.is_monitoring = False

        # Cancel monitoring task
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Platform monitoring stopped")

    async def check_platform_health(self, platform_id: str) -> PlatformHealthSnapshot:
        """Perform health check for a specific platform.

        Args:
            platform_id: Platform ID

        Returns:
            Platform health snapshot

        Raises:
            PlatformError: If health check fails
        """
        logger.info(f"Checking health for platform: {platform_id}")

        # Get platform adapter
        adapter = self.registry.get_adapter(platform_id)
        if not adapter:
            raise PlatformError(
                f"Platform adapter not found: {platform_id}",
                error_code="ADAPTER_NOT_FOUND",
                platform=platform_id
            )

        # Perform health checks
        health_checks = await self._run_health_checks(adapter, platform_id)

        # Update snapshot
        snapshot = self.health_snapshots.get(platform_id)
        if not snapshot:
            snapshot = PlatformHealthSnapshot(
                platform_id=platform_id,
                status=PlatformStatus.UNKNOWN,
                last_check=datetime.utcnow()
            )
            self.health_snapshots[platform_id] = snapshot

        old_status = snapshot.status
        snapshot.health_checks = health_checks
        snapshot.last_check = datetime.utcnow()

        # Determine overall status
        snapshot.status = self._determine_platform_status(health_checks)

        # Update consecutive failures
        if snapshot.status == PlatformStatus.UNHEALTHY:
            snapshot.consecutive_failures += 1
        else:
            snapshot.consecutive_failures = 0

        # Check for status change
        if old_status != snapshot.status:
            logger.info(f"Platform status changed: {platform_id} {old_status.value} -> {snapshot.status.value}")
            await self._emit_event("status_change", {
                "platform_id": platform_id,
                "old_status": old_status.value,
                "new_status": snapshot.status.value,
                "snapshot": snapshot
            })

        # Check for alerts
        await self._check_and_generate_alerts(snapshot)

        # Emit health check event
        await self._emit_event("health_check", {
            "platform_id": platform_id,
            "snapshot": snapshot
        })

        return snapshot

    async def check_all_platforms_health(self) -> Dict[str, PlatformHealthSnapshot]:
        """Check health for all registered platforms.

        Returns:
            Dictionary of platform health snapshots
        """
        logger.info("Checking health for all platforms")

        # Get all registered platforms
        platforms = self.registry.get_registered_platforms()

        # Check health for each platform
        tasks = [self.check_platform_health(platform_id) for platform_id in platforms]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        snapshots = {}
        for platform_id, result in zip(platforms, results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {platform_id}: {str(result)}")
                # Create error snapshot
                snapshots[platform_id] = PlatformHealthSnapshot(
                    platform_id=platform_id,
                    status=PlatformStatus.UNHEALTHY,
                    last_check=datetime.utcnow(),
                    health_checks=[
                        HealthCheckResult(
                            platform_id=platform_id,
                            status=HealthCheckStatus.FAIL,
                            message=str(result),
                            response_time_ms=0,
                            error=str(result)
                        )
                    ]
                )
            else:
                snapshots[platform_id] = result

        return snapshots

    def get_platform_status(self, platform_id: str) -> Optional[PlatformHealthSnapshot]:
        """Get current platform status.

        Args:
            platform_id: Platform ID

        Returns:
            Platform health snapshot or None if not monitored
        """
        return self.health_snapshots.get(platform_id)

    def get_all_platforms_status(self) -> Dict[str, PlatformHealthSnapshot]:
        """Get status for all monitored platforms.

        Returns:
            Dictionary of all platform health snapshots
        """
        return self.health_snapshots.copy()

    def get_active_alerts(self, platform_id: Optional[str] = None) -> List[Alert]:
        """Get active alerts.

        Args:
            platform_id: Optional platform filter

        Returns:
            List of active alerts
        """
        alerts = [alert for alert in self.active_alerts.values() if alert.is_active]

        if platform_id:
            alerts = [alert for alert in alerts if alert.platform_id == platform_id]

        return sorted(alerts, key=lambda a: a.created_at, reverse=True)

    def get_alert_history(
        self,
        platform_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """Get alert history.

        Args:
            platform_id: Optional platform filter
            limit: Maximum number of alerts to return

        Returns:
            List of historical alerts
        """
        alerts = self.alert_history.copy()

        if platform_id:
            alerts = [alert for alert in alerts if alert.platform_id == platform_id]

        # Sort by creation time (newest first)
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    def acknowledge_alert(self, alert_id: str, user: str) -> bool:
        """Acknowledge an alert.

        Args:
            alert_id: Alert ID
            user: User acknowledging the alert

        Returns:
            True if alert was acknowledged
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.acknowledged = True
        alert.metadata["acknowledged_by"] = user
        alert.metadata["acknowledged_at"] = datetime.utcnow().isoformat()

        logger.info(f"Alert acknowledged: {alert_id} by {user}")
        return True

    def resolve_alert(self, alert_id: str, user: str, notes: Optional[str] = None) -> bool:
        """Resolve an alert.

        Args:
            alert_id: Alert ID
            user: User resolving the alert
            notes: Optional resolution notes

        Returns:
            True if alert was resolved
        """
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.resolved_at = datetime.utcnow()
        alert.metadata["resolved_by"] = user
        if notes:
            alert.metadata["resolution_notes"] = notes

        # Move to history
        self.alert_history.append(alert)
        del self.active_alerts[alert_id]

        # Emit event
        asyncio.create_task(self._emit_event("alert_resolved", {
            "alert": alert
        }))

        logger.info(f"Alert resolved: {alert_id} by {user}")
        return True

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary statistics.

        Returns:
            Monitoring summary dictionary
        """
        total_platforms = len(self.health_snapshots)
        healthy_platforms = sum(
            1 for snapshot in self.health_snapshots.values()
            if snapshot.status == PlatformStatus.HEALTHY
        )
        degraded_platforms = sum(
            1 for snapshot in self.health_snapshots.values()
            if snapshot.status == PlatformStatus.DEGRADED
        )
        unhealthy_platforms = sum(
            1 for snapshot in self.health_snapshots.values()
            if snapshot.status == PlatformStatus.UNHEALTHY
        )

        active_alerts = len(self.get_active_alerts())
        critical_alerts = len([
            alert for alert in self.active_alerts.values()
            if alert.severity == AlertSeverity.CRITICAL
        ])

        return {
            "monitoring_enabled": self.monitoring_enabled,
            "is_monitoring": self.is_monitoring,
            "check_interval_seconds": self.check_interval,
            "total_platforms": total_platforms,
            "healthy_platforms": healthy_platforms,
            "degraded_platforms": degraded_platforms,
            "unhealthy_platforms": unhealthy_platforms,
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "last_check": max(
                [s.last_check for s in self.health_snapshots.values()],
                default=None
            )
        }

    def add_event_handler(
        self,
        event_type: str,
        handler: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Add event handler.

        Args:
            event_type: Event type
            handler: Event handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []

        self.event_handlers[event_type].append(handler)

    # Private methods

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        try:
            while self.is_monitoring:
                if self.monitoring_enabled:
                    try:
                        # Check all platforms
                        await self.check_all_platforms_health()

                        # Clean up old alerts
                        await self._cleanup_old_alerts()

                    except Exception as e:
                        logger.error(f"Error in monitoring loop: {str(e)}")

                # Wait for next check
                await asyncio.sleep(self.check_interval)

        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Monitoring loop error: {str(e)}")
        finally:
            self.is_monitoring = False

    async def _run_health_checks(
        self,
        adapter: PlatformAdapter,
        platform_id: str
    ) -> List[HealthCheckResult]:
        """Run all health checks for a platform.

        Args:
            adapter: Platform adapter
            platform_id: Platform ID

        Returns:
            List of health check results
        """
        results = []

        # Connectivity check
        result = await self._check_connectivity(adapter, platform_id)
        results.append(result)

        # Capability check
        result = await self._check_capabilities(adapter, platform_id)
        results.append(result)

        # Performance check
        result = await self._check_performance(adapter, platform_id)
        results.append(result)

        # Limits check
        result = await self._check_limits(adapter, platform_id)
        results.append(result)

        return results

    async def _check_connectivity(
        self,
        adapter: PlatformAdapter,
        platform_id: str
    ) -> HealthCheckResult:
        """Check platform connectivity.

        Args:
            adapter: Platform adapter
            platform_id: Platform ID

        Returns:
            Health check result
        """
        start_time = asyncio.get_event_loop().time()

        try:
            if hasattr(adapter, "health_check"):
                health_result = await adapter.health_check()
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000

                if health_result.get("healthy", False):
                    return HealthCheckResult(
                        platform_id=platform_id,
                        status=HealthCheckStatus.PASS,
                        message="Platform is reachable",
                        response_time_ms=response_time,
                        details=health_result
                    )
                else:
                    return HealthCheckResult(
                        platform_id=platform_id,
                        status=HealthCheckStatus.FAIL,
                        message=health_result.get("message", "Platform health check failed"),
                        response_time_ms=response_time,
                        details=health_result
                    )
            else:
                # No health check method, assume healthy
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.WARN,
                    message="No health check method available",
                    response_time_ms=response_time
                )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheckResult(
                platform_id=platform_id,
                status=HealthCheckStatus.FAIL,
                message=f"Connectivity check failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )

    async def _check_capabilities(
        self,
        adapter: PlatformAdapter,
        platform_id: str
    ) -> HealthCheckResult:
        """Check platform capabilities.

        Args:
            adapter: Platform adapter
            platform_id: Platform ID

        Returns:
            Health check result
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Check if adapter has required methods
            required_methods = [
                "validate_skill",
                "convert_skill",
                "deploy_skill"
            ]

            missing_methods = [
                method for method in required_methods
                if not hasattr(adapter, method)
            ]

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            if missing_methods:
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.FAIL,
                    message=f"Missing required methods: {', '.join(missing_methods)}",
                    response_time_ms=response_time,
                    details={"missing_methods": missing_methods}
                )
            else:
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.PASS,
                    message="All required capabilities available",
                    response_time_ms=response_time,
                    details={"supported_formats": adapter.supported_formats}
                )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheckResult(
                platform_id=platform_id,
                status=HealthCheckStatus.FAIL,
                message=f"Capability check failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )

    async def _check_performance(
        self,
        adapter: PlatformAdapter,
        platform_id: str
    ) -> HealthCheckResult:
        """Check platform performance.

        Args:
            adapter: Platform adapter
            platform_id: Platform ID

        Returns:
            Health check result
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Simulate a lightweight operation to check performance
            # In a real implementation, this might check API rate limits, etc.
            await asyncio.sleep(0.1)  # Simulate operation

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000

            if response_time > self.response_time_threshold:
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.WARN,
                    message=f"Response time ({response_time:.2f}ms) exceeds threshold ({self.response_time_threshold}ms)",
                    response_time_ms=response_time
                )
            else:
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.PASS,
                    message=f"Response time within acceptable range: {response_time:.2f}ms",
                    response_time_ms=response_time
                )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheckResult(
                platform_id=platform_id,
                status=HealthCheckStatus.FAIL,
                message=f"Performance check failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )

    async def _check_limits(
        self,
        adapter: PlatformAdapter,
        platform_id: str
    ) -> HealthCheckResult:
        """Check platform limits.

        Args:
            adapter: Platform adapter
            platform_id: Platform ID

        Returns:
            Health check result
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # Check if adapter has reasonable limits
            if not hasattr(adapter, "max_file_size"):
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.WARN,
                    message="No file size limit configured",
                    response_time_ms=response_time
                )

            max_size = adapter.max_file_size
            if max_size <= 0:
                response_time = (asyncio.get_event_loop().time() - start_time) * 1000
                return HealthCheckResult(
                    platform_id=platform_id,
                    status=HealthCheckStatus.FAIL,
                    message="Invalid file size limit",
                    response_time_ms=response_time
                )

            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheckResult(
                platform_id=platform_id,
                status=HealthCheckStatus.PASS,
                message=f"File size limit: {max_size} bytes",
                response_time_ms=response_time,
                details={"max_file_size": max_size}
            )

        except Exception as e:
            response_time = (asyncio.get_event_loop().time() - start_time) * 1000
            return HealthCheckResult(
                platform_id=platform_id,
                status=HealthCheckStatus.FAIL,
                message=f"Limits check failed: {str(e)}",
                response_time_ms=response_time,
                error=str(e)
            )

    def _determine_platform_status(
        self,
        health_checks: List[HealthCheckResult]
    ) -> PlatformStatus:
        """Determine overall platform status from health checks.

        Args:
            health_checks: List of health check results

        Returns:
            Overall platform status
        """
        if not health_checks:
            return PlatformStatus.UNKNOWN

        # Count check results
        fail_count = sum(1 for check in health_checks if check.status == HealthCheckStatus.FAIL)
        warn_count = sum(1 for check in health_checks if check.status == HealthCheckStatus.WARN)
        pass_count = sum(1 for check in health_checks if check.status == HealthCheckStatus.PASS)

        total_checks = len(health_checks)

        # Determine status based on results
        if fail_count > 0:
            if fail_count >= total_checks // 2:
                return PlatformStatus.UNHEALTHY
            else:
                return PlatformStatus.DEGRADED
        elif warn_count > 0:
            if warn_count >= total_checks // 2:
                return PlatformStatus.DEGRADED
            else:
                return PlatformStatus.HEALTHY
        else:
            return PlatformStatus.HEALTHY

    async def _check_and_generate_alerts(self, snapshot: PlatformHealthSnapshot) -> None:
        """Check for conditions that should trigger alerts.

        Args:
            snapshot: Platform health snapshot
        """
        platform_id = snapshot.platform_id

        # Check for unhealthy status
        if snapshot.status == PlatformStatus.UNHEALTHY:
            if snapshot.consecutive_failures >= self.alert_threshold_failures:
                # Check if alert already exists
                alert_key = f"{platform_id}:unhealthy"
                if alert_key not in self.active_alerts:
                    alert = Alert(
                        alert_id=str(uuid4()),
                        platform_id=platform_id,
                        severity=AlertSeverity.CRITICAL,
                        title="Platform Unhealthy",
                        message=f"Platform {platform_id} has been unhealthy for {snapshot.consecutive_failures} consecutive checks",
                        metadata={"consecutive_failures": snapshot.consecutive_failures}
                    )
                    self.active_alerts[alert_key] = alert
                    await self._emit_event("alert_triggered", {"alert": alert})

        # Check for degraded status
        elif snapshot.status == PlatformStatus.DEGRADED:
            alert_key = f"{platform_id}:degraded"
            if alert_key not in self.active_alerts:
                alert = Alert(
                    alert_id=str(uuid4()),
                    platform_id=platform_id,
                    severity=AlertSeverity.WARNING,
                    title="Platform Degraded",
                    message=f"Platform {platform_id} is operating with degraded performance",
                    metadata={"status": snapshot.status.value}
                )
                self.active_alerts[alert_key] = alert
                await self._emit_event("alert_triggered", {"alert": alert})

        # Resolve alerts if platform is now healthy
        elif snapshot.status == PlatformStatus.HEALTHY:
            # Resolve unhealthy alert
            alert_key = f"{platform_id}:unhealthy"
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                alert.resolved_at = datetime.utcnow()
                self.alert_history.append(alert)
                del self.active_alerts[alert_key]
                await self._emit_event("alert_resolved", {"alert": alert})

            # Resolve degraded alert
            alert_key = f"{platform_id}:degraded"
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                alert.resolved_at = datetime.utcnow()
                self.alert_history.append(alert)
                del self.active_alerts[alert_key]
                await self._emit_event("alert_resolved", {"alert": alert})

    async def _cleanup_old_alerts(self, older_than_hours: int = 168) -> None:
        """Clean up old alerts from history.

        Args:
            older_than_hours: Remove alerts older than this many hours
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        # Clean up old alerts from history
        self.alert_history = [
            alert for alert in self.alert_history
            if alert.created_at > cutoff_time
        ]

        # Limit history size
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    async def _emit_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Emit monitoring event.

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
        await self.start_monitoring()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_monitoring()