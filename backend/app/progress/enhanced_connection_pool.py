"""Enhanced connection pool with advanced optimizations.

This module provides enhanced connection pooling with:
- Connection warming
- Adaptive scaling
- Load balancing
- Performance optimization
- Memory management
"""

import asyncio
import logging
import time
import gc
import weakref
from typing import Dict, List, Optional, Set, Callable, Any
from collections import deque, defaultdict
from dataclasses import dataclass, field
from threading import Lock
import psutil

from .connection_pool import (
    ConnectionPoolConfig,
    ResourceMonitor,
    ResourceMetrics,
    PoolStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class ConnectionMetrics:
    """Metrics for individual connections."""
    connection_id: str
    created_at: float
    last_used_at: float
    request_count: int
    total_response_time: float
    average_response_time: float
    error_count: int
    is_active: bool
    memory_usage_mb: float


@dataclass
class PerformanceThresholds:
    """Performance threshold configuration."""
    cpu_threshold: float = 80.0
    memory_threshold: float = 85.0
    connection_utilization_threshold: float = 0.9
    response_time_threshold: float = 100.0
    error_rate_threshold: float = 0.05


class ConnectionWarmingManager:
    """Manages connection warming for optimal performance."""

    def __init__(self, pool_size: int = 50):
        """Initialize connection warming manager.

        Args:
            pool_size: Number of warm connections to maintain
        """
        self.pool_size = pool_size
        self.warmed_connections: deque = deque(maxlen=pool_size)
        self._lock = Lock()

    def add_warmed_connection(self, connection_id: str):
        """Add a connection to the warmed pool.

        Args:
            connection_id: Connection ID to warm
        """
        with self._lock:
            if connection_id not in self.warmed_connections:
                self.warmed_connections.append(connection_id)
                logger.debug(f"Added warmed connection: {connection_id}")

    def get_warmed_connection(self) -> Optional[str]:
        """Get a warmed connection for reuse.

        Returns:
            Warmed connection ID or None
        """
        with self._lock:
            if self.warmed_connections:
                connection_id = self.warmed_connections.popleft()
                logger.debug(f"Reusing warmed connection: {connection_id}")
                return connection_id
        return None


class AdaptiveScaler:
    """Automatically scales connection pool based on load."""

    def __init__(self, config: ConnectionPoolConfig):
        """Initialize adaptive scaler.

        Args:
            config: Connection pool configuration
        """
        self.config = config
        self._scale_history = deque(maxlen=100)
        self._last_scale_time = time.time()
        self._lock = Lock()

    def should_scale_up(
        self,
        metrics: ResourceMetrics,
        thresholds: PerformanceThresholds,
    ) -> bool:
        """Determine if pool should scale up.

        Args:
            metrics: Current resource metrics
            thresholds: Performance thresholds

        Returns:
            True if should scale up
        """
        now = time.time()
        if now - self._last_scale_time < 60:  # Minimum 60 seconds between scales
            return False

        # Check if load is high
        utilization = metrics.active_connections / self.config.max_connections

        if (
            metrics.cpu_percent > thresholds.cpu_threshold
            or metrics.memory_percent > thresholds.memory_threshold
            or utilization > thresholds.connection_utilization_threshold
        ):
            with self._lock:
                self._scale_history.append(("scale_up", now))
                self._last_scale_time = now
            logger.info(f"Scaling up: CPU={metrics.cpu_percent:.1f}%, Memory={metrics.memory_percent:.1f}%, Util={utilization:.2f}")
            return True

        return False

    def should_scale_down(
        self,
        metrics: ResourceMetrics,
        thresholds: PerformanceThresholds,
    ) -> bool:
        """Determine if pool should scale down.

        Args:
            metrics: Current resource metrics
            thresholds: Performance thresholds

        Returns:
            True if should scale down
        """
        now = time.time()
        if now - self._last_scale_time < 120:  # Minimum 120 seconds between scale down
            return False

        # Check if load is low
        utilization = metrics.active_connections / self.config.max_connections

        if (
            metrics.cpu_percent < thresholds.cpu_threshold * 0.5
            and metrics.memory_percent < thresholds.memory_threshold * 0.5
            and utilization < thresholds.connection_utilization_threshold * 0.3
        ):
            with self._lock:
                self._scale_history.append(("scale_down", now))
                self._last_scale_time = now
            logger.info(f"Scaling down: CPU={metrics.cpu_percent:.1f}%, Memory={metrics.memory_percent:.1f}%, Util={utilization:.2f}")
            return True

        return False


class LoadBalancer:
    """Distributes connections across multiple pools."""

    def __init__(self, algorithm: str = "round_robin"):
        """Initialize load balancer.

        Args:
            algorithm: Load balancing algorithm
        """
        self.algorithm = algorithm
        self._pool_weights: Dict[str, float] = {}
        self._pool_round_robin_index = 0
        self._pool_connections_count: Dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def add_pool(self, pool_name: str, weight: float = 1.0):
        """Add a pool to load balancer.

        Args:
            pool_name: Pool name
            weight: Pool weight (higher = more connections)
        """
        with self._lock:
            self._pool_weights[pool_name] = weight
            logger.debug(f"Added pool to load balancer: {pool_name} (weight={weight})")

    def get_pool(self) -> Optional[str]:
        """Get optimal pool based on algorithm.

        Returns:
            Pool name or None
        """
        with self._lock:
            if not self._pool_weights:
                return None

            if self.algorithm == "round_robin":
                pool_names = list(self._pool_weights.keys())
                pool_name = pool_names[self._pool_round_robin_index % len(pool_names)]
                self._pool_round_robin_index += 1
                return pool_name

            elif self.algorithm == "least_connections":
                return min(
                    self._pool_weights.keys(),
                    key=lambda x: self._pool_connections_count[x]
                )

            elif self.algorithm == "weighted":
                # Simple weighted random selection
                import random
                return random.choices(
                    list(self._pool_weights.keys()),
                    weights=list(self._pool_weights.values())
                )[0]

            else:
                logger.warning(f"Unknown load balancing algorithm: {self.algorithm}")
                return list(self._pool_weights.keys())[0]

    def increment_connection_count(self, pool_name: str):
        """Increment connection count for pool.

        Args:
            pool_name: Pool name
        """
        with self._lock:
            self._pool_connections_count[pool_name] += 1

    def decrement_connection_count(self, pool_name: str):
        """Decrement connection count for pool.

        Args:
            pool_name: Pool name
        """
        with self._lock:
            self._pool_connections_count[pool_name] = max(0, self._pool_connections_count[pool_name] - 1)


class MemoryOptimizer:
    """Optimizes memory usage for connection pools."""

    def __init__(self, gc_threshold: int = 1000):
        """Initialize memory optimizer.

        Args:
            gc_threshold: Garbage collection threshold
        """
        self.gc_threshold = gc_threshold
        self._allocation_count = 0
        self._lock = Lock()

    def track_allocation(self):
        """Track memory allocation."""
        with self._lock:
            self._allocation_count += 1
            if self._allocation_count % self.gc_threshold == 0:
                self.trigger_gc()

    def trigger_gc(self):
        """Trigger garbage collection."""
        collected = gc.collect()
        logger.debug(f"Garbage collection triggered: {collected} objects collected")

    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory statistics.

        Returns:
            Memory statistics
        """
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "r memory_info.rssss_mb": / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "gc_count": sum(gc.get_count()),
        }


class EnhancedConnectionPoolManager:
    """Enhanced connection pool manager with advanced features."""

    def __init__(
        self,
        config: ConnectionPoolConfig,
        warm_connections: bool = True,
        adaptive_scaling: bool = True,
        load_balancing: bool = False,
    ):
        """Initialize enhanced connection pool manager.

        Args:
            config: Connection pool configuration
            warm_connections: Enable connection warming
            adaptive_scaling: Enable adaptive scaling
            load_balancing: Enable load balancing
        """
        self.config = config
        self.warm_connections = warm_connections
        self.adaptive_scaling = adaptive_scaling
        self.load_balancing = load_balancing

        # Initialize components
        self.resource_monitor = ResourceMonitor(config)
        self.warming_manager = ConnectionWarmingManager() if warm_connections else None
        self.adaptive_scaler = AdaptiveScaler(config) if adaptive_scaling else None
        self.load_balancer = LoadBalancer() if load_balancing else None
        self.memory_optimizer = MemoryOptimizer()

        # Connection tracking
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._connection_metrics: Dict[str, ConnectionMetrics] = {}
        self._lock = Lock()

        # Performance tracking
        self._performance_history = deque(maxlen=1000)
        self._thresholds = PerformanceThresholds()

        # Background tasks
        self._optimization_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the enhanced connection pool manager."""
        logger.info("Starting enhanced connection pool manager")

        # Start background tasks
        if self.adaptive_scaling:
            self._optimization_task = asyncio.create_task(self._optimization_loop())

        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("Enhanced connection pool manager started")

    async def stop(self):
        """Stop the enhanced connection pool manager."""
        logger.info("Stopping enhanced connection pool manager")

        # Cancel background tasks
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Cleanup all connections
        await self._cleanup_all_connections()

        logger.info("Enhanced connection pool manager stopped")

    async def _optimization_loop(self):
        """Background optimization loop."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)

                # Get current metrics
                metrics = self.resource_monitor.get_current_metrics()

                # Check if we should scale up
                if self.adaptive_scaler and self.adaptive_scaler.should_scale_up(metrics, self._thresholds):
                    await self._scale_up()

                # Check if we should scale down
                elif self.adaptive_scaler and self.adaptive_scaler.should_scale_down(metrics, self._thresholds):
                    await self._scale_down()

                # Memory optimization
                self.memory_optimizer.trigger_gc()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")

    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval)

                # Cleanup idle connections
                await self._cleanup_idle_connections()

                # Update performance metrics
                await self._update_performance_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    async def _scale_up(self):
        """Scale up connection pool."""
        old_max = self.config.max_connections
        self.config.max_connections = min(
            int(self.config.max_connections * 1.2),
            int(self.config.max_connections * 1.5)
        )

        logger.info(f"Scaled up connection pool: {old_max} -> {self.config.max_connections}")

    async def _scale_down(self):
        """Scale down connection pool."""
        old_max = self.config.max_connections
        self.config.max_connections = max(
            int(self.config.max_connections * 0.8),
            self.config.min_idle_connections
        )

        logger.info(f"Scaled down connection pool: {old_max} -> {self.config.max_connections}")

    async def _cleanup_idle_connections(self):
        """Cleanup idle connections."""
        now = time.time()
        idle_connections = []

        with self._lock:
            for connection_id, conn_data in self._connections.items():
                if now - conn_data["last_used"] > self.config.connection_timeout:
                    idle_connections.append(connection_id)

        for connection_id in idle_connections:
            await self._close_connection(connection_id)

        if idle_connections:
            logger.info(f"Cleaned up {len(idle_connections)} idle connections")

    async def _update_performance_metrics(self):
        """Update performance metrics."""
        now = time.time()
        with self._lock:
            active_connections = sum(1 for c in self._connections.values() if c["is_active"])

            metrics = {
                "timestamp": now,
                "active_connections": active_connections,
                "total_connections": len(self._connections),
                "cpu_percent": self.resource_monitor.get_current_metrics().cpu_percent,
                "memory_mb": self.resource_monitor.get_current_metrics().memory_mb,
            }

            self._performance_history.append(metrics)

    async def _cleanup_all_connections(self):
        """Cleanup all connections."""
        with self._lock:
            connection_ids = list(self._connections.keys())

        for connection_id in connection_ids:
            await self._close_connection(connection_id)

    async def _close_connection(self, connection_id: str):
        """Close a connection.

        Args:
            connection_id: Connection ID to close
        """
        with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
                if connection_id in self._connection_metrics:
                    del self._connection_metrics[connection_id]

                logger.debug(f"Closed connection: {connection_id}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics.

        Returns:
            Performance statistics
        """
        with self._lock:
            recent_metrics = list(self._performance_history)[-10:]  # Last 10 measurements

            if not recent_metrics:
                return {}

            avg_active = sum(m["active_connections"] for m in recent_metrics) / len(recent_metrics)
            avg_cpu = sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m["memory_mb"] for m in recent_metrics) / len(recent_metrics)

            return {
                "average_active_connections": avg_active,
                "average_cpu_percent": avg_cpu,
                "average_memory_mb": avg_memory,
                "total_connections": len(self._connections),
                "utilization": avg_active / self.config.max_connections if self.config.max_connections > 0 else 0,
                "memory_stats": self.memory_optimizer.get_memory_stats(),
            }
