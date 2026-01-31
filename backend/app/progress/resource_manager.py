"""Resource management for real-time progress tracking.

This module provides comprehensive resource management including connection pooling,
resource monitoring, performance optimization, and auto-scaling capabilities.
"""

import asyncio
import logging
import time
import psutil
import gc
from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock
import weakref

from .websocket import websocket_manager, ConnectionPool
from .progress_manager import progress_manager
from .log_manager import log_manager
from .notification_manager import notification_manager
from .visualization_manager import visualization_manager

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of managed resources."""
    WEBSOCKET_CONNECTION = "websocket_connection"
    DATABASE_SESSION = "database_session"
    MEMORY_CACHE = "memory_cache"
    FILE_HANDLE = "file_handle"
    NETWORK_CONNECTION = "network_connection"


class ResourceStatus(Enum):
    """Resource status states."""
    ACTIVE = "active"
    IDLE = "idle"
    EXHAUSTED = "exhausted"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class ResourceMetrics:
    """Metrics for a resource."""
    resource_type: ResourceType
    total_allocated: int = 0
    total_released: int = 0
    current_active: int = 0
    peak_usage: int = 0
    average_lifetime: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SystemMetrics:
    """System-level resource metrics."""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    memory_used_mb: float = 0.0
    memory_available_mb: float = 0.0
    disk_percent: float = 0.0
    network_connections: int = 0
    active_threads: int = 0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ResourcePool:
    """Generic resource pool with lifecycle management."""

    def __init__(
        self,
        resource_type: ResourceType,
        max_size: int = 100,
        min_size: int = 10,
        acquire_timeout: float = 30.0,
        idle_timeout: float = 300.0,
    ):
        """Initialize resource pool.

        Args:
            resource_type: Type of resources in this pool
            max_size: Maximum number of resources
            min_size: Minimum number of resources to maintain
            acquire_timeout: Timeout for acquiring resources
            idle_timeout: Idle timeout before releasing resources
        """
        self.resource_type = resource_type
        self.max_size = max_size
        self.min_size = min_size
        self.acquire_timeout = acquire_timeout
        self.idle_timeout = idle_timeout

        self._resources: deque = deque()
        self._acquired: Dict[str, Any] = {}
        self._metrics = ResourceMetrics(resource_type=resource_type)
        self._lock = Lock()
        self._closed = False

    def acquire(self, timeout: Optional[float] = None) -> Any:
        """Acquire a resource from the pool.

        Args:
            timeout: Acquisition timeout (uses default if None)

        Returns:
            Acquired resource

        Raises:
            TimeoutError: If acquisition times out
            RuntimeError: If pool is closed
        """
        if self._closed:
            raise RuntimeError("Resource pool is closed")

        timeout = timeout or self.acquire_timeout
        start_time = time.time()

        with self._lock:
            # Try to get an existing resource
            while self._resources and time.time() - start_time < timeout:
                resource = self._resources.popleft()
                if self._is_resource_valid(resource):
                    self._acquired[id(resource)] = resource
                    self._metrics.current_active += 1
                    self._metrics.peak_usage = max(
                        self._metrics.peak_usage,
                        self._metrics.current_active,
                    )
                    self._metrics.updated_at = datetime.utcnow()
                    return resource

            # Create new resource if under max
            if len(self._acquired) < self.max_size:
                resource = self._create_resource()
                self._acquired[id(resource)] = resource
                self._metrics.current_active += 1
                self._metrics.peak_usage = max(
                    self._metrics.peak_usage,
                    self._metrics.current_active,
                )
                self._metrics.total_allocated += 1
                self._metrics.updated_at = datetime.utcnow()
                return resource

        raise TimeoutError(f"Failed to acquire {self.resource_type.value} within timeout")

    def release(self, resource: Any):
        """Release a resource back to the pool.

        Args:
            resource: Resource to release
        """
        if self._closed:
            return

        resource_id = id(resource)

        with self._lock:
            if resource_id in self._acquired:
                del self._acquired[resource_id]
                self._metrics.current_active -= 1

                # Return to pool if valid and not exceeding max idle
                if self._is_resource_valid(resource) and len(self._resources) < self.max_size:
                    self._resources.append(resource)
                else:
                    self._close_resource(resource)
                    self._metrics.total_released += 1

                self._metrics.updated_at = datetime.utcnow()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics.

        Returns:
            Dictionary containing statistics
        """
        with self._lock:
            return {
                "resource_type": self.resource_type.value,
                "max_size": self.max_size,
                "min_size": self.min_size,
                "current_pool_size": len(self._resources),
                "current_active": len(self._acquired),
                "total_allocated": self._metrics.total_allocated,
                "total_released": self._metrics.total_released,
                "peak_usage": self._metrics.peak_usage,
                "utilization": (
                    len(self._acquired) / self.max_size * 100
                    if self.max_size > 0 else 0
                ),
            }

    def _create_resource(self) -> Any:
        """Create a new resource (override in subclasses)."""
        # Placeholder - override in subclasses
        return {}

    def _is_resource_valid(self, resource: Any) -> bool:
        """Check if a resource is still valid (override in subclasses)."""
        # Placeholder - override in subclasses
        return True

    def _close_resource(self, resource: Any):
        """Close/cleanup a resource (override in subclasses)."""
        # Placeholder - override in subclasses
        pass

    def close(self):
        """Close the resource pool."""
        if self._closed:
            return

        self._closed = True

        with self._lock:
            # Close all resources
            while self._resources:
                resource = self._resources.popleft()
                self._close_resource(resource)

            # Close all acquired resources
            for resource in self._acquired.values():
                self._close_resource(resource)

            self._acquired.clear()

        logger.info(f"Closed resource pool: {self.resource_type.value}")


class DatabaseSessionPool(ResourcePool):
    """Resource pool for database sessions."""

    def __init__(self, **kwargs):
        """Initialize database session pool."""
        super().__init__(ResourceType.DATABASE_SESSION, **kwargs)

    def _create_resource(self):
        """Create a database session (placeholder)."""
        # In a real implementation, create actual database session
        return {"session_id": f"db_session_{int(time.time())}", "created_at": time.time()}

    def _is_resource_valid(self, resource: Dict[str, Any]) -> bool:
        """Check if database session is valid."""
        # Check session age
        age = time.time() - resource.get("created_at", 0)
        return age < self.idle_timeout

    def _close_resource(self, resource: Dict[str, Any]):
        """Close database session."""
        # In a real implementation, close actual session
        logger.debug(f"Closing database session: {resource['session_id']}")


class MemoryCachePool(ResourcePool):
    """Resource pool for memory cache entries."""

    def __init__(self, max_memory_mb: int = 100, **kwargs):
        """Initialize memory cache pool.

        Args:
            max_memory_mb: Maximum memory in MB
        """
        super().__init__(ResourceType.MEMORY_CACHE, **kwargs)
        self.max_memory_mb = max_memory_mb
        self.current_memory_mb = 0
        self._cache: Dict[str, Any] = {}

    def acquire(self, key: str, value: Any, size_bytes: int):
        """Acquire cache entry.

        Args:
            key: Cache key
            value: Cache value
            size_bytes: Size in bytes

        Returns:
            True if cached successfully
        """
        if self._closed:
            return False

        # Check memory limit
        if self.current_memory_mb + size_bytes / (1024 * 1024) > self.max_memory_mb:
            # Try to evict oldest entries
            self._evict_cache()

        # Try to add to cache
        with self._lock:
            if len(self._cache) < self.max_size:
                self._cache[key] = {
                    "value": value,
                    "size_bytes": size_bytes,
                    "created_at": time.time(),
                }
                self.current_memory_mb += size_bytes / (1024 * 1024)
                self._metrics.total_allocated += 1
                return True

        return False

    def release(self, key: str):
        """Release cache entry.

        Args:
            key: Cache key to release
        """
        if self._closed or key not in self._cache:
            return

        with self._lock:
            entry = self._cache.pop(key)
            self.current_memory_mb -= entry["size_bytes"] / (1024 * 1024)
            self._metrics.total_released += 1

    def _evict_cache(self):
        """Evict oldest cache entries."""
        with self._lock:
            # Sort by creation time
            sorted_keys = sorted(
                self._cache.keys(),
                key=lambda k: self._cache[k]["created_at"],
            )

            # Evict 25% of entries
            evict_count = max(1, len(sorted_keys) // 4)
            for key in sorted_keys[:evict_count]:
                entry = self._cache.pop(key)
                self.current_memory_mb -= entry["size_bytes"] / (1024 * 1024)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            stats = super().get_stats()
            stats.update({
                "current_memory_mb": self.current_memory_mb,
                "max_memory_mb": self.max_memory_mb,
                "memory_utilization": (
                    self.current_memory_mb / self.max_memory_mb * 100
                    if self.max_memory_mb > 0 else 0
                ),
                "cache_entries": len(self._cache),
            })
            return stats


class ResourceManager:
    """Central resource management system."""

    def __init__(self):
        """Initialize resource manager."""
        self.pools: Dict[ResourceType, ResourcePool] = {}
        self.system_metrics_history: deque = deque(maxlen=1000)
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_running = False

        # Register default pools
        self._register_default_pools()

    def _register_default_pools(self):
        """Register default resource pools."""
        self.register_pool(DatabaseSessionPool(max_size=50, min_size=5))
        self.register_pool(MemoryCachePool(max_size=1000, max_memory_mb=200))

    def register_pool(self, pool: ResourcePool):
        """Register a resource pool.

        Args:
            pool: ResourcePool instance
        """
        self.pools[pool.resource_type] = pool
        logger.info(f"Registered resource pool: {pool.resource_type.value}")

    def get_pool(self, resource_type: ResourceType) -> Optional[ResourcePool]:
        """Get resource pool by type.

        Args:
            resource_type: Resource type

        Returns:
            ResourcePool instance or None
        """
        return self.pools.get(resource_type)

    async def start_monitoring(self, interval: float = 60.0):
        """Start resource monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        if self._is_running:
            return

        self._is_running = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )

        logger.info("Resource monitoring started")

    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if not self._is_running:
            return

        self._is_running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Resource monitoring stopped")

    async def _monitoring_loop(self, interval: float):
        """Main monitoring loop.

        Args:
            interval: Monitoring interval
        """
        while self._is_running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self.system_metrics_history.append(metrics)

                # Check resource health
                await self._check_resource_health()

                # Auto-scale if needed
                await self._auto_scale_pools()

                # Trigger garbage collection if memory is high
                await self._check_memory_pressure()

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect system-level metrics.

        Returns:
            SystemMetrics instance
        """
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Network connections
            network_connections = len(psutil.net_connections())

            # Active threads
            active_threads = psutil.process().num_threads()

            # GC statistics
            gc_stats = gc.get_stats()
            gc_collections = {i: stat["collections"] for i, stat in enumerate(gc_stats)}

            return SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_percent=disk.percent,
                network_connections=network_connections,
                active_threads=active_threads,
                gc_collections=gc_collections,
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics()

    async def _check_resource_health(self):
        """Check health of all resource pools."""
        for resource_type, pool in self.pools.items():
            try:
                stats = pool.get_stats()
                utilization = stats.get("utilization", 0)

                # Check for high utilization
                if utilization > 90:
                    logger.warning(
                        f"High resource utilization for {resource_type.value}: {utilization:.1f}%"
                    )

                # Check for errors
                if hasattr(pool._metrics, "error_count") and pool._metrics.error_count > 0:
                    logger.warning(
                        f"Resource pool {resource_type.value} has {pool._metrics.error_count} errors"
                    )

            except Exception as e:
                logger.error(f"Error checking pool health for {resource_type.value}: {e}")

    async def _auto_scale_pools(self):
        """Automatically scale resource pools based on load."""
        if not self.system_metrics_history:
            return

        latest_metrics = self.system_metrics_history[-1]

        # Scale based on CPU usage
        if latest_metrics.cpu_percent > 80:
            # Scale up pools
            await self._scale_up_pools()
        elif latest_metrics.cpu_percent < 30:
            # Scale down pools
            await self._scale_down_pools()

    async def _scale_up_pools(self):
        """Scale up resource pools."""
        for resource_type, pool in self.pools.items():
            try:
                if pool.max_size < 1000:  # Don't scale infinitely
                    old_max = pool.max_size
                    pool.max_size = min(pool.max_size * 2, 1000)
                    logger.info(
                        f"Scaled up {resource_type.value} pool: {old_max} -> {pool.max_size}"
                    )
            except Exception as e:
                logger.error(f"Error scaling up pool {resource_type.value}: {e}")

    async def _scale_down_pools(self):
        """Scale down resource pools."""
        for resource_type, pool in self.pools.items():
            try:
                if pool.max_size > 10:  # Don't scale below minimum
                    old_max = pool.max_size
                    pool.max_size = max(pool.max_size // 2, 10)
                    logger.info(
                        f"Scaled down {resource_type.value} pool: {old_max} -> {pool.max_size}"
                    )
            except Exception as e:
                logger.error(f"Error scaling down pool {resource_type.value}: {e}")

    async def _check_memory_pressure(self):
        """Check for memory pressure and trigger GC."""
        if not self.system_metrics_history:
            return

        latest_metrics = self.system_metrics_history[-1]

        if latest_metrics.memory_percent > 85:
            # Trigger garbage collection
            collected = gc.collect()
            logger.info(f"Triggered garbage collection: collected {collected} objects")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics.

        Returns:
            Dictionary containing all resource statistics
        """
        # Get pool statistics
        pool_stats = {}
        for resource_type, pool in self.pools.items():
            pool_stats[resource_type.value] = pool.get_stats()

        # Get system metrics
        latest_metrics = self.system_metrics_history[-1] if self.system_metrics_history else None

        # Calculate averages over last hour
        if len(self.system_metrics_history) > 0:
            recent_metrics = list(self.system_metrics_history)[-60:]
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = avg_memory = 0

        return {
            "pools": pool_stats,
            "system": {
                "latest": latest_metrics.__dict__ if latest_metrics else {},
                "averages": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory,
                },
                "history_size": len(self.system_metrics_history),
            },
            "monitoring": {
                "is_running": self._is_running,
                "total_pools": len(self.pools),
            },
        }

    def optimize_resources(self):
        """Optimize resource usage."""
        # Close unused pools
        for resource_type, pool in self.pools.items():
            stats = pool.get_stats()
            if stats["current_active"] == 0 and stats["current_pool_size"] > pool.min_size:
                # Release excess resources
                excess = stats["current_pool_size"] - pool.min_size
                logger.info(f"Releasing {excess} excess resources from {resource_type.value} pool")

        # Force garbage collection
        collected = gc.collect()
        logger.info(f"Resource optimization: collected {collected} objects")

    def close_all_pools(self):
        """Close all resource pools."""
        for pool in self.pools.values():
            pool.close()

        self.pools.clear()

        logger.info("All resource pools closed")


# Global resource manager instance
resource_manager = ResourceManager()


# Convenience functions
async def get_resource(resource_type: ResourceType, **kwargs) -> Any:
    """Get a resource from the pool.

    Args:
        resource_type: Type of resource
        **kwargs: Additional arguments for resource acquisition

    Returns:
        Acquired resource
    """
    pool = resource_manager.get_pool(resource_type)
    if not pool:
        raise ValueError(f"No pool registered for resource type: {resource_type.value}")

    return pool.acquire(**kwargs)


def release_resource(resource_type: ResourceType, resource: Any):
    """Release a resource back to the pool.

    Args:
        resource_type: Type of resource
        resource: Resource to release
    """
    pool = resource_manager.get_pool(resource_type)
    if pool:
        pool.release(resource)


async def start_resource_monitoring():
    """Start resource monitoring."""
    await resource_manager.start_monitoring()


async def stop_resource_monitoring():
    """Stop resource monitoring."""
    await resource_manager.stop_monitoring()


def get_resource_stats() -> Dict[str, Any]:
    """Get resource statistics."""
    return resource_manager.get_comprehensive_stats()


def optimize_resource_usage():
    """Optimize resource usage."""
    resource_manager.optimize_resources()
