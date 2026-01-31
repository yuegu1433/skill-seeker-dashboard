"""Enhanced resource manager with advanced monitoring and optimization.

This module provides enhanced resource management including:
- Resource leak detection
- Advanced monitoring
- Resource optimization
- Performance tuning
- Alert system
"""

import asyncio
import logging
import time
import psutil
import gc
from typing import Dict, List, Optional, Set, Callable, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock
from enum import Enum
import weakref
import traceback

from .resource_manager import (
    ResourceManager,
    ResourceType,
    ResourceStatus,
    ResourcePool,
    ResourceMetrics as BaseResourceMetrics,
)

logger = logging.getLogger(__name__)


class ResourceLeakLevel(Enum):
    """Resource leak severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ResourceLeak:
    """Resource leak information."""
    resource_type: ResourceType
    resource_id: str
    leak_level: ResourceLeakLevel
    first_detected: float
    last_detected: float
    leak_count: int
    stack_trace: str


@dataclass
class EnhancedResourceMetrics(BaseResourceMetrics):
    """Enhanced resource metrics with additional information."""
    leak_count: int = 0
    leak_level: Optional[ResourceLeakLevel] = None
    memory_fragmentation: float = 0.0
    gc_collections: Dict[int, int] = field(default_factory=dict)
    connection_quality: float = 100.0
    performance_score: float = 100.0
    last_optimization: Optional[float] = None


class ResourceLeakDetector:
    """Detects and tracks resource leaks."""

    def __init__(self, max_history: int = 1000):
        """Initialize resource leak detector.

        Args:
            max_history: Maximum history size
        """
        self.max_history = max_history
        self.resource_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.active_resources: Dict[str, Dict[str, Any]] = {}
        self.leaks: List[ResourceLeak] = []
        self._lock = Lock()

    def track_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a resource for leak detection.

        Args:
            resource_id: Resource identifier
            resource_type: Type of resource
            metadata: Additional metadata
        """
        with self._lock:
            now = time.time()
            resource_info = {
                "resource_id": resource_id,
                "resource_type": resource_type,
                "created_at": now,
                "last_seen": now,
                "metadata": metadata or {},
                "access_count": 0,
            }

            self.active_resources[resource_id] = resource_info
            self.resource_history[resource_type.value].append(now)

            logger.debug(f"Tracking resource: {resource_id} (type: {resource_type.value})")

    def update_resource_access(self, resource_id: str):
        """Update resource access time.

        Args:
            resource_id: Resource identifier
        """
        with self._lock:
            if resource_id in self.active_resources:
                self.active_resources[resource_id]["last_seen"] = time.time()
                self.active_resources[resource_id]["access_count"] += 1

    def release_resource(self, resource_id: str):
        """Release a tracked resource.

        Args:
            resource_id: Resource identifier
        """
        with self._lock:
            if resource_id in self.active_resources:
                del self.active_resources[resource_id]
                logger.debug(f"Released resource: {resource_id}")

    def detect_leaks(
        self,
        timeout: float = 300.0,
        min_leak_count: int = 10,
    ) -> List[ResourceLeak]:
        """Detect resource leaks.

        Args:
            timeout: Resource timeout in seconds
            min_leak_count: Minimum leak count for detection

        Returns:
            List of detected leaks
        """
        with self._lock:
            now = time.time()
            potential_leaks = []

            for resource_id, resource_info in self.active_resources.items():
                age = now - resource_info["created_at"]
                last_seen = now - resource_info["last_seen"]

                # Check for stale resources
                if age > timeout and last_seen > timeout:
                    leak_level = ResourceLeakLevel.ERROR
                    if age > timeout * 2:
                        leak_level = ResourceLeakLevel.CRITICAL
                    elif age > timeout * 1.5:
                        leak_level = ResourceLeakLevel.WARNING

                    # Find or create leak
                    existing_leak = next(
                        (l for l in self.leaks if l.resource_id == resource_id),
                        None
                    )

                    if existing_leak:
                        existing_leak.last_detected = now
                        existing_leak.leak_count += 1
                    else:
                        leak = ResourceLeak(
                            resource_type=resource_info["resource_type"],
                            resource_id=resource_id,
                            leak_level=leak_level,
                            first_detected=now,
                            last_detected=now,
                            leak_count=1,
                            stack_trace=traceback.format_stack(),
                        )
                        self.leaks.append(leak)

                    potential_leaks.append(resource_id)

            # Clean old leaks
            self.leaks = [
                leak for leak in self.leaks
                if now - leak.last_detected < 3600  # Remove leaks older than 1 hour
            ]

            return self.leaks

    def get_leak_report(self) -> Dict[str, Any]:
        """Generate leak report.

        Returns:
            Leak report
        """
        with self._lock:
            now = time.time()
            leak_counts = defaultdict(int)
            leak_by_level = defaultdict(int)

            for leak in self.leaks:
                leak_counts[leak.resource_type.value] += 1
                leak_by_level[leak.leak_level.value] += 1

            return {
                "total_leaks": len(self.leaks),
                "leak_by_type": dict(leak_counts),
                "leak_by_level": dict(leak_by_level),
                "active_resources": len(self.active_resources),
                "oldest_leak_age": max(
                    (now - leak.first_detected for leak in self.leaks),
                    default=0
                ),
                "recent_leaks": [
                    {
                        "resource_id": leak.resource_id,
                        "resource_type": leak.resource_type.value,
                        "leak_level": leak.leak_level.value,
                        "leak_count": leak.leak_count,
                        "first_detected": leak.first_detected,
                        "last_detected": leak.last_detected,
                    }
                    for leak in self.leaks[-10:]  # Last 10 leaks
                ],
            }


class ResourceAlertSystem:
    """System for alerting on resource issues."""

    def __init__(self):
        """Initialize alert system."""
        self.alert_callbacks: List[Callable[[str, Dict[str, Any]], None]] = []
        self.alert_history: deque = deque(maxlen=1000)
        self._lock = Lock()

    def add_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add alert callback.

        Args:
            callback: Alert callback function
        """
        with self._lock:
            self.alert_callbacks.append(callback)

    async def send_alert(self, alert_type: str, details: Dict[str, Any]):
        """Send alert.

        Args:
            alert_type: Type of alert
            details: Alert details
        """
        alert = {
            "type": alert_type,
            "details": details,
            "timestamp": time.time(),
        }

        with self._lock:
            self.alert_history.append(alert)

        # Call callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, details)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

        logger.warning(f"Alert sent: {alert_type} - {details}")


class ResourceOptimizer:
    """Optimizes resource usage."""

    def __init__(self):
        """Initialize resource optimizer."""
        self.optimization_history: deque = deque(maxlen=100)
        self._lock = Lock()

    async def optimize_memory(self) -> Dict[str, Any]:
        """Optimize memory usage.

        Returns:
            Optimization results
        """
        start_time = time.time()
        results = {
            "gc_collections_before": dict(zip(range(3), gc.get_count())),
            "memory_before_mb": psutil.Process().memory_info().rss / 1024 / 1024,
        }

        # Force garbage collection
        collected = gc.collect()
        results["gc_collections_after"] = dict(zip(range(3), gc.get_count()))
        results["memory_after_mb"] = psutil.Process().memory_info().rss / 1024 / 1024
        results["memory_freed_mb"] = results["memory_before_mb"] - results["memory_after_mb"]
        results["objects_collected"] = collected
        results["optimization_time"] = time.time() - start_time

        with self._lock:
            self.optimization_history.append(results)

        logger.info(f"Memory optimization: {results['memory_freed_mb']:.2f} MB freed")

        return results

    async def optimize_connections(self) -> Dict[str, Any]:
        """Optimize connection usage.

        Returns:
            Optimization results
        """
        # This would implement connection optimization logic
        # For now, just return a placeholder
        return {
            "optimized_connections": 0,
            "optimization_time": time.time(),
        }

    async def optimize_database(self) -> Dict[str, Any]:
        """Optimize database connections.

        Returns:
            Optimization results
        """
        # This would implement database optimization logic
        # For now, just return a placeholder
        return {
            "optimized_queries": 0,
            "optimization_time": time.time(),
        }


class EnhancedResourceManager:
    """Enhanced resource manager with advanced features."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize enhanced resource manager.

        Args:
            config: Configuration options
        """
        config = config or {}
        self.config = config

        # Initialize components
        self.leak_detector = ResourceLeakDetector()
        self.alert_system = ResourceAlertSystem()
        self.optimizer = ResourceOptimizer()

        # Tracking
        self.resource_timestamps: Dict[str, float] = {}
        self._lock = Lock()

        # Performance monitoring
        self.performance_history: deque = deque(maxlen=1000)
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start_monitoring(self, interval: float = 30.0):
        """Start resource monitoring.

        Args:
            interval: Monitoring interval in seconds
        """
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(interval)
        )
        logger.info("Resource monitoring started")

    async def stop_monitoring(self):
        """Stop resource monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource monitoring stopped")

    async def _monitoring_loop(self, interval: float):
        """Background monitoring loop.

        Args:
            interval: Monitoring interval
        """
        while True:
            try:
                await asyncio.sleep(interval)

                # Detect leaks
                leaks = self.leak_detector.detect_leaks()
                if leaks:
                    await self._handle_leaks(leaks)

                # Optimize resources
                await self._optimize_resources()

                # Update performance metrics
                await self._update_performance_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")

    async def _handle_leaks(self, leaks: List[ResourceLeak]):
        """Handle detected resource leaks.

        Args:
            leaks: List of detected leaks
        """
        for leak in leaks:
            alert_details = {
                "resource_id": leak.resource_id,
                "resource_type": leak.resource_type.value,
                "leak_level": leak.leak_level.value,
                "leak_count": leak.leak_count,
                "age": time.time() - leak.first_detected,
            }

            await self.alert_system.send_alert("resource_leak", alert_details)

    async def _optimize_resources(self):
        """Optimize resource usage."""
        try:
            # Memory optimization
            memory_results = await self.optimizer.optimize_memory()

            # Connection optimization
            connection_results = await self.optimizer.optimize_connections()

            # Database optimization
            database_results = await self.optimizer.optimize_database()

            # Check if optimization was significant
            if memory_results["memory_freed_mb"] > 10:  # More than 10 MB freed
                await self.alert_system.send_alert(
                    "significant_optimization",
                    {
                        "type": "memory",
                        "memory_freed_mb": memory_results["memory_freed_mb"],
                        "objects_collected": memory_results["objects_collected"],
                    }
                )

        except Exception as e:
            logger.error(f"Error optimizing resources: {e}")

    async def _update_performance_metrics(self):
        """Update performance metrics."""
        now = time.time()
        process = psutil.Process()

        metrics = {
            "timestamp": now,
            "cpu_percent": psutil.cpu_percent(),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "thread_count": process.num_threads(),
            "fd_count": process.num_fds() if hasattr(process, "num_fds") else 0,
            "active_resources": len(self.leak_detector.active_resources),
            "detected_leaks": len(self.leak_detector.leaks),
            "gc_collections": dict(zip(range(3), gc.get_count())),
        }

        with self._lock:
            self.performance_history.append(metrics)

    async def track_resource(
        self,
        resource_id: str,
        resource_type: ResourceType,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a resource.

        Args:
            resource_id: Resource identifier
            resource_type: Type of resource
            metadata: Additional metadata
        """
        self.leak_detector.track_resource(resource_id, resource_type, metadata)
        self.resource_timestamps[resource_id] = time.time()

    async def release_resource(self, resource_id: str):
        """Release a tracked resource.

        Args:
            resource_id: Resource identifier
        """
        self.leak_detector.release_resource(resource_id)
        self.resource_timestamps.pop(resource_id, None)

    def get_enhanced_metrics(self) -> EnhancedResourceMetrics:
        """Get enhanced resource metrics.

        Returns:
            Enhanced resource metrics
        """
        process = psutil.Process()
        memory_info = process.memory_info()

        # Calculate memory fragmentation
        gc_stats = gc.get_stats()
        total_collections = sum(stat["collections"] for stat in gc_stats)

        # Calculate performance score
        performance_score = 100.0
        with self._lock:
            if self.performance_history:
                recent_metrics = list(self.performance_history)[-10:]
                avg_cpu = sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics)
                avg_memory = sum(m["memory_percent"] for m in recent_metrics) / len(recent_metrics)

                # Simple performance score calculation
                performance_score = max(
                    0,
                    100 - (avg_cpu * 0.5 + avg_memory * 0.5)
                )

        return EnhancedResourceMetrics(
            resource_type=ResourceType.WEBSOCKET_CONNECTION,
            status=ResourceStatus.ACTIVE,
            usage_percent=memory_info.rss / 1024 / 1024 / 1024 * 100,  # Convert to percentage
            active_count=len(self.leak_detector.active_resources),
            idle_count=len(self.leak_detector.leaks),
            leak_count=len(self.leak_detector.leaks),
            memory_fragmentation=total_collections % 1000,  # Simple fragmentation metric
            gc_collections=dict(zip(range(3), gc.get_count())),
            connection_quality=performance_score,
            performance_score=performance_score,
            last_optimization=time.time(),
        )

    def get_leak_report(self) -> Dict[str, Any]:
        """Get resource leak report.

        Returns:
            Leak report
        """
        return self.leak_detector.get_leak_report()

    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report.

        Returns:
            Performance report
        """
        with self._lock:
            if not self.performance_history:
                return {}

            recent_metrics = list(self.performance_history)[-60:]  # Last 60 measurements

            return {
                "average_cpu_percent": sum(m["cpu_percent"] for m in recent_metrics) / len(recent_metrics),
                "average_memory_mb": sum(m["memory_mb"] for m in recent_metrics) / len(recent_metrics),
                "average_thread_count": sum(m["thread_count"] for m in recent_metrics) / len(recent_metrics),
                "peak_memory_mb": max(m["memory_mb"] for m in recent_metrics),
                "active_resources": recent_metrics[-1]["active_resources"],
                "detected_leaks": recent_metrics[-1]["detected_leaks"],
                "gc_collections": recent_metrics[-1]["gc_collections"],
                "measurement_count": len(recent_metrics),
            }
