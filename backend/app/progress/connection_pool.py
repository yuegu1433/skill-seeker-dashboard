"""Advanced connection pool and resource management for WebSocket connections.

This module provides comprehensive connection pooling, resource monitoring,
and automatic cleanup to optimize performance for 1000+ concurrent connections.

Key Features:
- Multi-tier connection pooling
- Resource usage monitoring
- Automatic connection cleanup
- Connection reuse strategies
- Performance metrics and alerting
"""

import asyncio
import gc
import logging
import psutil
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from threading import Lock
import weakref

logger = logging.getLogger(__name__)


class PoolStatus(Enum):
    """Connection pool status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"


class ResourceType(Enum):
    """Types of resources managed by the pool."""
    WEBSOCKET_CONNECTION = "websocket_connection"
    MEMORY_POOL = "memory_pool"
    MESSAGE_QUEUE = "message_queue"
    CPU_TIME = "cpu_time"
    NETWORK_BANDWIDTH = "network_bandwidth"


@dataclass
class ResourceMetrics:
    """Resource usage metrics."""
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_percent: float = 0.0
    active_connections: int = 0
    queued_messages: int = 0
    bandwidth_mbps: float = 0.0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pool."""
    max_connections: int = 1000
    max_connections_per_user: int = 50
    max_connections_per_task: int = 10
    min_idle_connections: int = 50
    max_idle_connections: int = 200
    connection_timeout: float = 300.0
    heartbeat_interval: float = 30.0
    cleanup_interval: float = 60.0
    max_message_queue_size: int = 1000
    memory_limit_mb: float = 1024.0
    cpu_threshold: float = 80.0
    enable_auto_scaling: bool = True
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    health_check_interval: float = 10.0


class ResourceMonitor:
    """Monitors system and application resource usage."""

    def __init__(self, config: ConnectionPoolConfig):
        """Initialize resource monitor.

        Args:
            config: Connection pool configuration
        """
        self.config = config
        self.metrics_history: deque = deque(maxlen=1000)
        self._lock = Lock()
        self._callbacks: List[Callable[[ResourceMetrics], None]] = []

    def add_callback(self, callback: Callable[[ResourceMetrics], None]):
        """Add callback for resource alerts.

        Args:
            callback: Function to call when resource threshold is exceeded
        """
        with self._lock:
            self._callbacks.append(callback)

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics.

        Returns:
            Current resource metrics
        """
        process = psutil.Process()

        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory_info = psutil.virtual_memory()
        process_memory = process.memory_info()

        # Get application-specific metrics from global state
        from .websocket import websocket_manager

        active_connections = 0
        queued_messages = 0

        if websocket_manager:
            active_connections = websocket_manager.connection_pool.get_connection_count()

            # Count queued messages across all connections
            for conn in websocket_manager.connection_pool.connections.values():
                queued_messages += len(conn.message_queue)

        metrics = ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_mb=process_memory.rss / 1024 / 1024,
            memory_percent=memory_info.percent,
            active_connections=active_connections,
            queued_messages=queued_messages,
            bandwidth_mbps=self._estimate_bandwidth(),
            gc_collections=dict(zip(range(3), gc.get_count())),
        )

        with self._lock:
            self.metrics_history.append(metrics)

        return metrics

    def _estimate_bandwidth(self) -> float:
        """Estimate network bandwidth usage.

        Returns:
            Estimated bandwidth in Mbps
        """
        try:
            net_io = psutil.net_io_counters()
            if net_io:
                # Simple bandwidth estimation based on bytes transferred
                # This is a rough approximation
                return (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024
        except Exception:
            pass
        return 0.0

    def check_thresholds(self, metrics: ResourceMetrics) -> Tuple[bool, List[str]]:
        """Check if resource thresholds are exceeded.

        Args:
            metrics: Resource metrics to check

        Returns:
            Tuple of (is_critical, list_of_warnings)
        """
        warnings = []

        if metrics.memory_mb > self.config.memory_limit_mb:
            warnings.append(f"Memory usage ({metrics.memory_mb:.1f}MB) exceeds limit ({self.config.memory_limit_mb:.1f}MB)")

        if metrics.cpu_percent > self.config.cpu_threshold:
            warnings.append(f"CPU usage ({metrics.cpu_percent:.1f}%) exceeds threshold ({self.config.cpu_threshold:.1f}%)")

        if metrics.active_connections > self.config.max_connections * self.config.scale_up_threshold:
            warnings.append(f"Connection count ({metrics.active_connections}) is high")

        if metrics.queued_messages > self.config.max_message_queue_size * self.config.scale_up_threshold:
            warnings.append(f"Message queue size ({metrics.queued_messages}) is high")

        is_critical = len(warnings) > 0

        return is_critical, warnings

    def get_average_metrics(self, window_size: int = 10) -> ResourceMetrics:
        """Get average metrics over a window.

        Args:
            window_size: Number of recent samples to average

        Returns:
            Average resource metrics
        """
        with self._lock:
            recent_metrics = list(self.metrics_history)[-window_size:]

        if not recent_metrics:
            return self.get_current_metrics()

        # Calculate averages
        avg_metrics = ResourceMetrics()
        for metric in recent_metrics:
            avg_metrics.cpu_percent += metric.cpu_percent
            avg_metrics.memory_mb += metric.memory_mb
            avg_metrics.memory_percent += metric.memory_percent
            avg_metrics.active_connections += metric.active_connections
            avg_metrics.queued_messages += metric.queued_messages
            avg_metrics.bandwidth_mbps += metric.bandwidth_mbp

        count = len(recent_metrics)
        avg_metrics.cpu_percent /= count
        avg_metrics.memory_mb /= count
        avg_metrics.memory_percent /= count
        avg_metrics.active_connections //= count
        avg_metrics.queued_messages //= count
        avg_metrics.bandwidth_mbps /= count

        return avg_metrics


class ConnectionPoolManager:
    """Advanced connection pool manager with auto-scaling and optimization."""

    def __init__(self, config: ConnectionPoolConfig):
        """Initialize connection pool manager.

        Args:
            config: Connection pool configuration
        """
        self.config = config
        self.resource_monitor = ResourceMonitor(config)
        self.status = PoolStatus.HEALTHY
        self._lock = asyncio.Lock()

        # Pool statistics
        self.stats = {
            "total_connections_created": 0,
            "total_connections_reused": 0,
            "total_connections_closed": 0,
            "peak_connections": 0,
            "avg_connection_lifetime": 0.0,
            "total_messages_processed": 0,
            "total_bytes_transferred": 0,
            "resource_alerts": 0,
            "auto_scale_events": 0,
        }

        # Connection reuse tracking
        self.connection_reuse_tracker: Dict[str, int] = defaultdict(int)
        self.connection_lifetimes: deque = deque(maxlen=10000)

        # Background tasks
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._is_running = False

    async def start(self):
        """Start the connection pool manager."""
        if self._is_running:
            return

        self._is_running = True

        # Start background tasks
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Register resource alert callback
        self.resource_monitor.add_callback(self._handle_resource_alert)

        logger.info("Connection pool manager started")

    async def stop(self):
        """Stop the connection pool manager."""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel background tasks
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("Connection pool manager stopped")

    async def acquire_connection(
        self,
        connection_id: str,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> bool:
        """Acquire a connection slot.

        Args:
            connection_id: Connection identifier
            user_id: Associated user ID
            task_id: Associated task ID

        Returns:
            True if connection slot acquired, False otherwise
        """
        async with self._lock:
            from .websocket import websocket_manager

            if not websocket_manager:
                return False

            connection = websocket_manager.connection_pool.connections.get(connection_id)
            if not connection:
                return False

            # Check limits
            if user_id:
                user_connections = websocket_manager.connection_pool.get_user_connection_count(user_id)
                if user_connections >= self.config.max_connections_per_user:
                    logger.warning(f"User {user_id} has reached connection limit")
                    return False

            if task_id:
                task_connections = websocket_manager.connection_pool.get_task_connection_count(task_id)
                if task_connections >= self.config.max_connections_per_task:
                    logger.warning(f"Task {task_id} has reached connection limit")
                    return False

            # Track connection for reuse
            self.connection_reuse_tracker[connection_id] += 1
            self.stats["total_connections_created"] += 1

            # Update peak connections
            current_count = websocket_manager.connection_pool.get_connection_count()
            if current_count > self.stats["peak_connections"]:
                self.stats["peak_connections"] = current_count

            return True

    async def release_connection(
        self,
        connection_id: str,
        connection_lifetime: float,
    ):
        """Release a connection slot.

        Args:
            connection_id: Connection identifier
            connection_lifetime: Connection lifetime in seconds
        """
        async with self._lock:
            self.connection_lifetimes.append(connection_lifetime)

            # Update average lifetime
            if self.connection_lifetimes:
                self.stats["avg_connection_lifetime"] = sum(self.connection_lifetimes) / len(self.connection_lifetimes)

            self.stats["total_connections_closed"] += 1

    async def optimize_connections(self):
        """Optimize connection pool based on current usage."""
        async with self._lock:
            from .websocket import websocket_manager

            if not websocket_manager:
                return

            current_metrics = self.resource_monitor.get_current_metrics()
            is_critical, warnings = self.resource_monitor.check_thresholds(current_metrics)

            if is_critical:
                await self._trigger_emergency_cleanup(warnings)
            else:
                await self._perform_routine_optimization(current_metrics)

    async def _trigger_emergency_cleanup(self, warnings: List[str]):
        """Trigger emergency cleanup due to resource constraints.

        Args:
            warnings: List of warning messages
        """
        logger.warning(f"Emergency cleanup triggered: {', '.join(warnings)}")
        self.stats["resource_alerts"] += 1

        from .websocket import websocket_manager

        if not websocket_manager:
            return

        # Close idle connections
        idle_connections = []
        for connection_id, connection in websocket_manager.connection_pool.connections.items():
            if connection.get_idle_time() > self.config.connection_timeout / 2:
                idle_connections.append(connection_id)

        # Close oldest idle connections first
        for connection_id in idle_connections[:50]:  # Close up to 50 at once
            await websocket_manager.disconnect(connection_id, code=1001, reason="Emergency cleanup")

        logger.info(f"Emergency cleanup: closed {len(idle_connections)} idle connections")

    async def _perform_routine_optimization(self, metrics: ResourceMetrics):
        """Perform routine optimization.

        Args:
            metrics: Current resource metrics
        """
        from .websocket import websocket_manager

        if not websocket_manager:
            return

        # Check if we should scale down
        connection_utilization = metrics.active_connections / self.config.max_connections

        if (
            self.config.enable_auto_scaling
            and connection_utilization < self.config.scale_down_threshold
            and metrics.active_connections > self.config.min_idle_connections
        ):
            await self._scale_down_connections(metrics)

        # Check if we should scale up
        elif (
            self.config.enable_auto_scaling
            and connection_utilization > self.config.scale_up_threshold
        ):
            await self._prepare_for_scale_up()

    async def _scale_down_connections(self, metrics: ResourceMetrics):
        """Scale down connection pool.

        Args:
            metrics: Current resource metrics
        """
        from .websocket import websocket_manager

        if not websocket_manager:
            return

        # Identify candidates for cleanup
        cleanup_candidates = []
        for connection_id, connection in websocket_manager.connection_pool.connections.items():
            if connection.get_idle_time() > 60:  # Idle for more than 1 minute
                cleanup_candidates.append((connection_id, connection.get_idle_time()))

        # Sort by idle time (longest first)
        cleanup_candidates.sort(key=lambda x: x[1], reverse=True)

        # Close oldest connections until we reach desired level
        target_count = max(
            self.config.min_idle_connections,
            int(self.config.max_connections * self.config.scale_down_threshold)
        )

        current_count = websocket_manager.connection_pool.get_connection_count()
        to_close = min(current_count - target_count, len(cleanup_candidates))

        for i in range(to_close):
            connection_id = cleanup_candidates[i][0]
            await websocket_manager.disconnect(connection_id, code=1001, reason="Scale down")

        if to_close > 0:
            self.stats["auto_scale_events"] += 1
            logger.info(f"Scaled down: closed {to_close} idle connections")

    async def _prepare_for_scale_up(self):
        """Prepare for potential scale up."""
        # Pre-allocate resources if needed
        # This could involve warming up connections or preparing buffers
        logger.debug("Preparing for scale up")

    async def _monitor_loop(self):
        """Background task for resource monitoring."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                metrics = self.resource_monitor.get_current_metrics()
                is_critical, warnings = self.resource_monitor.check_thresholds(metrics)

                if is_critical:
                    self.status = PoolStatus.CRITICAL
                    logger.warning(f"Pool status is CRITICAL: {', '.join(warnings)}")
                elif metrics.cpu_percent > 50 or metrics.memory_percent > 70:
                    self.status = PoolStatus.DEGRADED
                elif metrics.active_connections > self.config.max_connections * 0.9:
                    self.status = PoolStatus.OVERLOADED
                else:
                    self.status = PoolStatus.HEALTHY

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")

    async def _cleanup_loop(self):
        """Background task for periodic cleanup."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval)

                await self.optimize_connections()

                # Force garbage collection
                collected = gc.collect()
                if collected > 0:
                    logger.debug(f"Garbage collection freed {collected} objects")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def _handle_resource_alert(self, metrics: ResourceMetrics):
        """Handle resource alert.

        Args:
            metrics: Resource metrics that triggered alert
        """
        logger.warning(f"Resource alert: {metrics}")

    async def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and statistics.

        Returns:
            Dictionary containing pool status and statistics
        """
        current_metrics = self.resource_monitor.get_current_metrics()
        is_critical, warnings = self.resource_monitor.check_thresholds(current_metrics)

        return {
            "status": self.status.value,
            "is_critical": is_critical,
            "warnings": warnings,
            "metrics": {
                "cpu_percent": current_metrics.cpu_percent,
                "memory_mb": current_metrics.memory_mb,
                "memory_percent": current_metrics.memory_percent,
                "active_connections": current_metrics.active_connections,
                "queued_messages": current_metrics.queued_messages,
                "bandwidth_mbps": current_metrics.bandwidth_mbps,
            },
            "stats": self.stats.copy(),
            "config": {
                "max_connections": self.config.max_connections,
                "max_connections_per_user": self.config.max_connections_per_user,
                "max_connections_per_task": self.config.max_connections_per_task,
                "min_idle_connections": self.config.min_idle_connections,
                "max_idle_connections": self.config.max_idle_connections,
            },
        }

    def get_connection_reuse_stats(self) -> Dict[str, Any]:
        """Get connection reuse statistics.

        Returns:
            Dictionary containing reuse statistics
        """
        reuse_counts = list(self.connection_reuse_tracker.values())
        if not reuse_counts:
            return {
                "total_tracked": 0,
                "avg_reuse_count": 0,
                "max_reuse_count": 0,
                "min_reuse_count": 0,
            }

        return {
            "total_tracked": len(reuse_counts),
            "avg_reuse_count": sum(reuse_counts) / len(reuse_counts),
            "max_reuse_count": max(reuse_counts),
            "min_reuse_count": min(reuse_counts),
        }

    async def force_cleanup(self):
        """Force immediate cleanup of resources."""
        logger.info("Forcing immediate cleanup")

        from .websocket import websocket_manager

        if websocket_manager:
            # Close all dead connections
            dead_connections = []
            for connection_id, connection in websocket_manager.connection_pool.connections.items():
                if not connection.is_alive:
                    dead_connections.append(connection_id)

            for connection_id in dead_connections:
                await websocket_manager.disconnect(connection_id, code=1001, reason="Force cleanup")

        # Force garbage collection
        gc.collect()

        logger.info(f"Force cleanup completed: closed {len(dead_connections)} dead connections")


# Global connection pool manager instance
connection_pool_manager = ConnectionPoolManager(ConnectionPoolConfig())


class ConnectionReuseStrategy:
    """Manages connection reuse strategies for optimization."""

    def __init__(self, manager: ConnectionPoolManager):
        """Initialize reuse strategy.

        Args:
            manager: Connection pool manager
        """
        self.manager = manager
        self._lock = asyncio.Lock()
        self.reuse_patterns: Dict[str, List[float]] = defaultdict(list)

    async def analyze_reuse_pattern(self, connection_id: str, user_id: str, task_id: str):
        """Analyze connection reuse pattern.

        Args:
            connection_id: Connection identifier
            user_id: User identifier
            task_id: Task identifier
        """
        async with self._lock:
            pattern_key = f"{user_id}:{task_id}"
            current_time = time.time()
            self.reuse_patterns[pattern_key].append(current_time)

            # Keep only recent patterns (last hour)
            cutoff_time = current_time - 3600
            self.reuse_patterns[pattern_key] = [
                t for t in self.reuse_patterns[pattern_key] if t > cutoff_time
            ]

    async def predict_reuse_opportunity(self, user_id: str, task_id: str) -> float:
        """Predict likelihood of connection reuse.

        Args:
            user_id: User identifier
            task_id: Task identifier

        Returns:
            Reuse likelihood score (0.0 to 1.0)
        """
        async with self._lock:
            pattern_key = f"{user_id}:{task_id}"
            patterns = self.reuse_patterns.get(pattern_key, [])

            if len(patterns) < 2:
                return 0.0

            # Calculate reuse frequency
            time_span = max(patterns) - min(patterns)
            if time_span == 0:
                return 0.0

            frequency = len(patterns) / (time_span / 3600)  # Connections per hour

            # Normalize to 0.0-1.0 range
            return min(1.0, frequency / 10.0)  # Assume 10 connections/hour is maximum

    async def get_preferred_connection(
        self,
        user_id: str,
        task_id: str,
        available_connections: List[str],
    ) -> Optional[str]:
        """Get preferred connection for reuse.

        Args:
            user_id: User identifier
            task_id: Task identifier
            available_connections: List of available connection IDs

        Returns:
            Preferred connection ID or None
        """
        if not available_connections:
            return None

        # Find connection with highest reuse count
        best_connection = None
        best_score = -1

        for connection_id in available_connections:
            reuse_count = self.manager.connection_reuse_tracker.get(connection_id, 0)
            if reuse_count > best_score:
                best_score = reuse_count
                best_connection = connection_id

        return best_connection


# Global reuse strategy instance
reuse_strategy = ConnectionReuseStrategy(connection_pool_manager)
