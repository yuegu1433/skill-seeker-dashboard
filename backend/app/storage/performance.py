"""Performance optimization module for MinIO storage system.

This module provides performance monitoring, optimization configurations,
and tuning utilities for the MinIO storage system.
"""

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import statistics

from .client import MinIOClient
from .cache import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for storage operations."""

    operation_type: str
    duration: float
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None
    data_size: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationConfig:
    """Configuration for performance optimization."""

    # Connection pooling
    max_connections: int = 100
    connection_timeout: int = 30
    read_timeout: int = 60
    pool_size: int = 10

    # Upload optimization
    chunk_size: int = 10 * 1024 * 1024  # 10MB
    max_concurrent_uploads: int = 5
    multipart_threshold: int = 100 * 1024 * 1024  # 100MB

    # Cache optimization
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 10000
    enable_compression: bool = True

    # Database optimization
    query_cache_size: int = 1000
    connection_pool_size: int = 20

    # Monitoring
    metrics_retention_hours: int = 24
    enable_detailed_metrics: bool = True


class PerformanceMonitor:
    """Monitor for storage system performance."""

    def __init__(self, config: OptimizationConfig):
        """Initialize performance monitor.

        Args:
            config: Optimization configuration
        """
        self.config = config
        self.metrics: deque = deque(maxlen=config.metrics_retention_hours * 3600)
        self.operation_stats: Dict[str, List[float]] = defaultdict(list)
        self.lock = threading.Lock()

    def record_operation(
        self,
        operation_type: str,
        duration: float,
        success: bool,
        error_message: Optional[str] = None,
        data_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record operation performance metrics.

        Args:
            operation_type: Type of operation
            duration: Operation duration in seconds
            success: Whether operation was successful
            error_message: Error message if failed
            data_size: Size of data processed in bytes
            metadata: Additional metadata
        """
        metric = PerformanceMetrics(
            operation_type=operation_type,
            duration=duration,
            timestamp=datetime.utcnow(),
            success=success,
            error_message=error_message,
            data_size=data_size,
            metadata=metadata or {},
        )

        with self.lock:
            self.metrics.append(metric)
            self.operation_stats[operation_type].append(duration)

    def get_operation_stats(self, operation_type: str) -> Dict[str, float]:
        """Get statistics for an operation type.

        Args:
            operation_type: Type of operation

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            durations = self.operation_stats.get(operation_type, [])

            if not durations:
                return {
                    "count": 0,
                    "avg_duration": 0.0,
                    "min_duration": 0.0,
                    "max_duration": 0.0,
                    "p95_duration": 0.0,
                    "success_rate": 0.0,
                }

            # Calculate statistics
            success_count = sum(
                1 for m in self.metrics
                if m.operation_type == operation_type and m.success
            )
            total_count = len([m for m in self.metrics if m.operation_type == operation_type])

            return {
                "count": len(durations),
                "avg_duration": statistics.mean(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "p95_duration": self._percentile(durations, 95),
                "success_rate": (success_count / total_count * 100) if total_count > 0 else 0.0,
            }

    def get_throughput_stats(self, hours: int = 1) -> Dict[str, float]:
        """Get throughput statistics.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with throughput metrics
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics
            if m.timestamp >= cutoff and m.success and m.data_size
        ]

        if not recent_metrics:
            return {
                "total_operations": 0,
                "total_data_mb": 0.0,
                "avg_throughput_mbps": 0.0,
                "operations_per_second": 0.0,
            }

        total_data = sum(m.data_size for m in recent_metrics)
        total_duration = sum(m.duration for m in recent_metrics)
        total_operations = len(recent_metrics)

        return {
            "total_operations": total_operations,
            "total_data_mb": total_data / (1024 * 1024),
            "avg_throughput_mbps": (total_data / (1024 * 1024)) / total_duration if total_duration > 0 else 0.0,
            "operations_per_second": total_operations / (hours * 3600),
        }

    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data.

        Args:
            data: List of values
            percentile: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report.

        Returns:
            Performance report dictionary
        """
        with self.lock:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "config": {
                    "chunk_size_mb": self.config.chunk_size / (1024 * 1024),
                    "max_concurrent_uploads": self.config.max_concurrent_uploads,
                    "cache_ttl_seconds": self.config.cache_ttl,
                    "enable_compression": self.config.enable_compression,
                },
                "operation_stats": {},
                "throughput": self.get_throughput_stats(),
                "recommendations": self._generate_recommendations(),
            }

            # Add stats for each operation type
            for op_type in self.operation_stats.keys():
                report["operation_stats"][op_type] = self.get_operation_stats(op_type)

            return report

    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Analyze operation stats
        for op_type, durations in self.operation_stats.items():
            if not durations:
                continue

            avg_duration = statistics.mean(durations)
            p95_duration = self._percentile(durations, 95)

            # Check for slow operations
            if avg_duration > 5.0:
                recommendations.append(
                    f"Operation '{op_type}' has high average duration "
                    f"({avg_duration:.2f}s). Consider optimizing."
                )

            # Check for performance degradation
            if p95_duration > avg_duration * 2:
                recommendations.append(
                    f"Operation '{op_type}' shows high variability "
                    f"(P95: {p95_duration:.2f}s vs avg: {avg_duration:.2f}s)."
                )

        # Check throughput
        throughput = self.get_throughput_stats()
        if throughput["avg_throughput_mbps"] < 10:
            recommendations.append(
                "Low average throughput detected. "
                "Consider increasing chunk size or enabling compression."
            )

        # Check success rates
        for op_type in self.operation_stats.keys():
            stats = self.get_operation_stats(op_type)
            if stats["success_rate"] < 95:
                recommendations.append(
                    f"Operation '{op_type}' has low success rate "
                    f"({stats['success_rate']:.1f}%). Check error logs."
                )

        return recommendations


class ConnectionPoolOptimizer:
    """Optimizer for connection pool settings."""

    @staticmethod
    def get_optimal_pool_size(
        expected_concurrent_operations: int,
        average_operation_duration: float,
    ) -> int:
        """Calculate optimal connection pool size.

        Args:
            expected_concurrent_operations: Expected concurrent operations
            average_operation_duration: Average operation duration in seconds

        Returns:
            Optimal pool size
        """
        # Formula: (concurrent_operations * average_duration) / operation_time
        # Assuming each operation takes ~1 second
        optimal_size = int(expected_concurrent_operations * average_operation_duration)
        return max(10, min(100, optimal_size))  # Clamp between 10 and 100

    @staticmethod
    def optimize_timeouts(
        network_latency_ms: int,
        expected_operation_duration_ms: int,
    ) -> Tuple[int, int]:
        """Calculate optimal timeout settings.

        Args:
            network_latency_ms: Network latency in milliseconds
            expected_operation_duration_ms: Expected operation duration in milliseconds

        Returns:
            Tuple of (connection_timeout, read_timeout) in seconds
        """
        connection_timeout = max(5, (network_latency_ms * 2) / 1000)
        read_timeout = max(
            30,
            (expected_operation_duration_ms * 3) / 1000 + connection_timeout
        )
        return int(connection_timeout), int(read_timeout)


class CacheOptimizer:
    """Optimizer for cache performance."""

    def __init__(self, cache_manager: CacheManager):
        """Initialize cache optimizer.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager

    def calculate_optimal_ttl(
        self,
        access_pattern: str,
        data_volatility: str,
    ) -> int:
        """Calculate optimal cache TTL.

        Args:
            access_pattern: Access pattern (frequent, moderate, rare)
            data_volatility: Data volatility (stable, moderate, volatile)

        Returns:
            Optimal TTL in seconds
        """
        base_ttl = 3600  # 1 hour base

        # Adjust based on access pattern
        if access_pattern == "frequent":
            base_ttl *= 2
        elif access_pattern == "rare":
            base_ttl //= 2

        # Adjust based on volatility
        if data_volatility == "volatile":
            base_ttl //= 4
        elif data_volatility == "stable":
            base_ttl *= 2

        return base_ttl

    def optimize_cache_strategy(
        self,
        cache_hit_rate: float,
        avg_access_frequency: float,
    ) -> Dict[str, Any]:
        """Provide cache optimization strategy.

        Args:
            cache_hit_rate: Current cache hit rate (0-1)
            avg_access_frequency: Average access frequency per hour

        Returns:
            Optimization strategy dictionary
        """
        strategy = {
            "current_hit_rate": cache_hit_rate,
            "recommendations": [],
            "config_changes": {},
        }

        # Analyze hit rate
        if cache_hit_rate < 0.5:
            strategy["recommendations"].append(
                "Low cache hit rate. Consider increasing cache size or TTL."
            )
            strategy["config_changes"]["cache_size"] = "increase"
        elif cache_hit_rate > 0.9:
            strategy["recommendations"].append(
                "High cache hit rate. Consider reducing cache size to save memory."
            )
            strategy["config_changes"]["cache_size"] = "decrease"

        # Analyze access frequency
        if avg_access_frequency > 100:
            strategy["recommendations"].append(
                "High access frequency. Consider enabling compression."
            )
            strategy["config_changes"]["compression"] = "enable"

        return strategy


class UploadOptimizer:
    """Optimizer for file upload performance."""

    @staticmethod
    def calculate_optimal_chunk_size(
        file_size: int,
        network_bandwidth_mbps: float,
        latency_ms: int,
    ) -> int:
        """Calculate optimal chunk size for uploads.

        Args:
            file_size: File size in bytes
            network_bandwidth_mbps: Network bandwidth in Mbps
            latency_ms: Network latency in milliseconds

        Returns:
            Optimal chunk size in bytes
        """
        # Calculate based on bandwidth-delay product
        bandwidth_bytes_per_sec = (network_bandwidth_mbps * 1024 * 1024) / 8
        optimal_chunk_size = int(bandwidth_bytes_per_sec * (latency_ms / 1000) * 4)

        # Clamp to reasonable bounds
        min_chunk = 1024 * 1024  # 1MB
        max_chunk = 100 * 1024 * 1024  # 100MB

        # For small files, use smaller chunks
        if file_size < 10 * 1024 * 1024:
            max_chunk = 5 * 1024 * 1024

        return max(min_chunk, min(optimal_chunk_size, max_chunk))

    @staticmethod
    def get_concurrent_upload_count(
        available_bandwidth_mbps: float,
        avg_file_size_mb: float,
        network_latency_ms: int,
    ) -> int:
        """Calculate optimal concurrent upload count.

        Args:
            available_bandwidth_mbps: Available bandwidth in Mbps
            avg_file_size_mb: Average file size in MB
            network_latency_ms: Network latency in milliseconds

        Returns:
            Optimal concurrent upload count
        """
        # Calculate how many files can be uploaded concurrently
        # while keeping bandwidth utilization reasonable

        files_per_second = (available_bandwidth_mbps * 1024) / (avg_file_size_mb * 8)
        optimal_concurrent = int(files_per_second * (network_latency_ms / 1000))

        return max(1, min(10, optimal_concurrent))


class DatabaseOptimizer:
    """Optimizer for database performance."""

    @staticmethod
    def get_query_optimization_hints(
        operation_type: str,
        expected_result_size: int,
    ) -> List[str]:
        """Get database query optimization hints.

        Args:
            operation_type: Type of database operation
            expected_result_size: Expected result size

        Returns:
            List of optimization hints
        """
        hints = []

        if operation_type == "list_files":
            hints.append("Use pagination for large result sets")
            hints.append("Add index on (skill_id, file_path)")
            if expected_result_size > 1000:
                hints.append("Consider caching frequently accessed file lists")

        elif operation_type == "get_file":
            hints.append("Use primary key lookup for single file retrieval")
            hints.append("Add index on object_name for direct lookups")

        elif operation_type == "search_files":
            hints.append("Use full-text search indexes")
            hints.append("Limit search results with LIMIT clause")
            hints.append("Consider denormalization for frequently searched fields")

        return hints

    @staticmethod
    def optimize_connection_pool(
        expected_connections: int,
        avg_query_duration_ms: int,
    ) -> Dict[str, int]:
        """Optimize database connection pool settings.

        Args:
            expected_connections: Expected number of concurrent connections
            avg_query_duration_ms: Average query duration in milliseconds

        Returns:
            Dictionary with pool configuration
        """
        # Calculate pool size based on query duration and expected load
        pool_size = max(
            10,
            int(expected_connections * (avg_query_duration_ms / 1000))
        )

        return {
            "pool_size": min(pool_size, 100),
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 3600,  # Recycle connections every hour
        }


class PerformanceProfiler:
    """Performance profiler for storage operations."""

    def __init__(self, monitor: PerformanceMonitor):
        """Initialize performance profiler.

        Args:
            monitor: Performance monitor instance
        """
        self.monitor = monitor
        self.active_profiles: Dict[str, Dict[str, Any]] = {}

    def start_profile(self, operation_id: str, operation_type: str, **kwargs):
        """Start profiling an operation.

        Args:
            operation_id: Unique operation identifier
            operation_type: Type of operation
            **kwargs: Additional metadata
        """
        self.active_profiles[operation_id] = {
            "operation_type": operation_type,
            "start_time": time.time(),
            "metadata": kwargs,
        }

    def end_profile(
        self,
        operation_id: str,
        success: bool,
        error_message: Optional[str] = None,
        data_size: Optional[int] = None,
    ):
        """End profiling an operation.

        Args:
            operation_id: Operation identifier
            success: Whether operation was successful
            error_message: Error message if failed
            data_size: Size of data processed
        """
        if operation_id not in self.active_profiles:
            logger.warning(f"Profile {operation_id} not found")
            return

        profile = self.active_profiles[operation_id]
        duration = time.time() - profile["start_time"]

        self.monitor.record_operation(
            operation_type=profile["operation_type"],
            duration=duration,
            success=success,
            error_message=error_message,
            data_size=data_size,
            metadata=profile["metadata"],
        )

        del self.active_profiles[operation_id]

    def get_active_profiles(self) -> List[Dict[str, Any]]:
        """Get all active operation profiles.

        Returns:
            List of active profiles
        """
        current_time = time.time()
        return [
            {
                "operation_id": op_id,
                "operation_type": profile["operation_type"],
                "duration": current_time - profile["start_time"],
                "metadata": profile["metadata"],
            }
            for op_id, profile in self.active_profiles.items()
        ]


class OptimizationManager:
    """Manager for all performance optimizations."""

    def __init__(self, config: OptimizationConfig):
        """Initialize optimization manager.

        Args:
            config: Optimization configuration
        """
        self.config = config
        self.monitor = PerformanceMonitor(config)
        self.profiler = PerformanceProfiler(self.monitor)
        self.cache_optimizer = None  # Will be set when cache manager is available

    def set_cache_manager(self, cache_manager: CacheManager):
        """Set cache manager for optimization.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_optimizer = CacheOptimizer(cache_manager)

    def apply_optimizations(
        self,
        minio_client: Optional[MinIOClient] = None,
    ) -> Dict[str, Any]:
        """Apply performance optimizations.

        Args:
            minio_client: MinIO client instance (optional)

        Returns:
            Dictionary with applied optimizations
        """
        optimizations = {
            "connection_pool": self._optimize_connection_pool(),
            "cache_settings": self._optimize_cache(),
            "upload_settings": self._optimize_uploads(),
            "database_settings": self._optimize_database(),
        }

        # Apply to MinIO client if provided
        if minio_client:
            self._apply_minio_optimizations(minio_client)

        return optimizations

    def _optimize_connection_pool(self) -> Dict[str, Any]:
        """Optimize connection pool settings.

        Returns:
            Dictionary with connection pool optimizations
        """
        optimizer = ConnectionPoolOptimizer()
        pool_size = optimizer.get_optimal_pool_size(
            expected_concurrent_operations=50,
            average_operation_duration=2.0,
        )

        conn_timeout, read_timeout = optimizer.optimize_timeouts(
            network_latency_ms=50,
            expected_operation_duration_ms=5000,
        )

        return {
            "pool_size": pool_size,
            "connection_timeout": conn_timeout,
            "read_timeout": read_timeout,
        }

    def _optimize_cache(self) -> Dict[str, Any]:
        """Optimize cache settings.

        Returns:
            Dictionary with cache optimizations
        """
        if not self.cache_optimizer:
            return {}

        return {
            "optimal_ttl_frequent": self.cache_optimizer.calculate_optimal_ttl(
                access_pattern="frequent",
                data_volatility="stable",
            ),
            "optimal_ttl_rare": self.cache_optimizer.calculate_optimal_ttl(
                access_pattern="rare",
                data_volatility="volatile",
            ),
            "compression_enabled": self.config.enable_compression,
        }

    def _optimize_uploads(self) -> Dict[str, Any]:
        """Optimize upload settings.

        Returns:
            Dictionary with upload optimizations
        """
        upload_optimizer = UploadOptimizer()

        chunk_size = upload_optimizer.calculate_optimal_chunk_size(
            file_size=50 * 1024 * 1024,  # 50MB
            network_bandwidth_mbps=100,
            latency_ms=50,
        )

        concurrent_uploads = upload_optimizer.get_concurrent_upload_count(
            available_bandwidth_mbps=100,
            avg_file_size_mb=50,
            network_latency_ms=50,
        )

        return {
            "chunk_size": chunk_size,
            "concurrent_uploads": concurrent_uploads,
            "multipart_threshold": self.config.multipart_threshold,
        }

    def _optimize_database(self) -> Dict[str, Any]:
        """Optimize database settings.

        Returns:
            Dictionary with database optimizations
        """
        optimizer = DatabaseOptimizer()
        pool_config = optimizer.optimize_connection_pool(
            expected_connections=20,
            avg_query_duration_ms=100,
        )

        return {
            "connection_pool": pool_config,
            "query_hints": {
                "list_files": optimizer.get_query_optimization_hints(
                    operation_type="list_files",
                    expected_result_size=100,
                ),
                "get_file": optimizer.get_query_optimization_hints(
                    operation_type="get_file",
                    expected_result_size=1,
                ),
            },
        }

    def _apply_minio_optimizations(self, client: MinIOClient):
        """Apply optimizations to MinIO client.

        Args:
            client: MinIO client instance
        """
        # This would apply optimizations to the actual client
        # Implementation depends on the specific MinIO client library
        pass

    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report.

        Returns:
            Complete optimization report
        """
        return {
            "performance_report": self.monitor.get_performance_report(),
            "optimizations_applied": self.apply_optimizations(),
            "active_profiles": self.profiler.get_active_profiles(),
            "recommendations": self._generate_optimization_recommendations(),
        }

    def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations.

        Returns:
            List of recommendations
        """
        recommendations = []

        # Get performance report
        report = self.monitor.get_performance_report()

        # Add performance-based recommendations
        recommendations.extend(report["recommendations"])

        # Add configuration recommendations
        recommendations.append(
            f"Consider using chunk size of "
            f"{self.config.chunk_size / (1024 * 1024):.1f}MB for optimal performance"
        )

        recommendations.append(
            f"Set max concurrent uploads to {self.config.max_concurrent_uploads}"
            " for optimal throughput"
        )

        if self.config.enable_compression:
            recommendations.append(
                "Compression is enabled. Monitor CPU usage to ensure optimal performance."
            )

        return recommendations


def create_optimization_config(**kwargs) -> OptimizationConfig:
    """Create optimization configuration with custom parameters.

    Args:
        **kwargs: Custom configuration parameters

    Returns:
        OptimizationConfig instance
    """
    return OptimizationConfig(**kwargs)


def get_default_optimization_config() -> OptimizationConfig:
    """Get default optimization configuration.

    Returns:
        Default OptimizationConfig instance
    """
    return OptimizationConfig()


def optimize_storage_system(
    config: Optional[OptimizationConfig] = None,
) -> OptimizationManager:
    """Create optimized storage system configuration.

    Args:
        config: Custom optimization configuration

    Returns:
        Configured OptimizationManager instance
    """
    if config is None:
        config = get_default_optimization_config()

    return OptimizationManager(config)
