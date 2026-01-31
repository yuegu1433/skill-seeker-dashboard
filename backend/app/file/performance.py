"""File Management Performance Optimization.

This module provides performance optimization configurations, caching strategies,
query optimization, and performance monitoring for the file management system.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import pickle
import redis
from functools import wraps

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache strategy enumeration."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


@dataclass
class PerformanceConfig:
    """Performance configuration."""

    # Caching settings
    enable_caching: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.LRU
    cache_ttl: int = 3600  # 1 hour
    cache_max_size: int = 10000
    cache_compression: bool = True

    # Database optimization
    enable_query_optimization: bool = True
    connection_pool_size: int = 20
    connection_pool_max_overflow: int = 30
    query_timeout: int = 30

    # File operation optimization
    enable_async_io: bool = True
    max_concurrent_operations: int = 100
    chunk_size: int = 64 * 1024  # 64KB
    buffer_size: int = 1024 * 1024  # 1MB

    # Batch operation optimization
    batch_size: int = 100
    enable_parallel_processing: bool = True
    max_worker_threads: int = 10

    # Preview optimization
    enable_preview_caching: bool = True
    preview_cache_ttl: int = 86400  # 24 hours
    thumbnail_size: int = 200
    max_preview_size: int = 10 * 1024 * 1024  # 10MB

    # Memory optimization
    max_memory_usage: int = 1024 * 1024 * 1024  # 1GB
    garbage_collection_threshold: int = 100
    enable_memory_monitoring: bool = True

    # Network optimization
    enable_compression: bool = True
    compression_level: int = 6
    enable_http2: bool = True
    connection_keepalive: bool = True

    # Monitoring
    enable_performance_monitoring: bool = True
    slow_query_threshold: float = 1.0  # seconds
    enable_metrics_collection: bool = True
    metrics_retention_days: int = 30


class PerformanceMonitor:
    """Performance monitoring and metrics collection."""

    def __init__(self, config: PerformanceConfig):
        """Initialize performance monitor."""
        self.config = config
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self.slow_operations: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()

    def record_metric(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a performance metric.

        Args:
            name: Metric name
            value: Metric value
            labels: Optional labels
        """
        if not self.config.enable_metrics_collection:
            return

        if name not in self.metrics:
            self.metrics[name] = []

        metric = {
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
            "labels": labels or {},
        }

        self.metrics[name].append(metric)

        # Check for slow operations
        if value > self.config.slow_query_threshold:
            self.slow_operations.append({
                "name": name,
                "duration": value,
                "timestamp": metric["timestamp"],
                "labels": labels,
            })

    def get_metric_summary(self, name: str) -> Optional[Dict[str, Any]]:
        """Get metric summary statistics.

        Args:
            name: Metric name

        Returns:
            Metric summary or None
        """
        if name not in self.metrics:
            return None

        values = [m["value"] for m in self.metrics[name]]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1] if values else None,
        }

    def get_slow_operations(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get slow operations within time window.

        Args:
            hours: Hours to look back

        Returns:
            List of slow operations
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            op for op in self.slow_operations
            if datetime.fromisoformat(op["timestamp"]) > cutoff
        ]

    def clear_metrics(self, name: Optional[str] = None):
        """Clear metrics.

        Args:
            name: Optional specific metric name
        """
        if name:
            self.metrics.pop(name, None)
        else:
            self.metrics.clear()
        self.slow_operations.clear()


class QueryOptimizer:
    """Database query optimization."""

    def __init__(self):
        """Initialize query optimizer."""
        self.query_cache: Dict[str, Any] = {}
        self.query_stats: Dict[str, Dict[str, Any]] = {}

    def optimize_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Optimize a database query.

        Args:
            query: SQL query
            params: Query parameters

        Returns:
            Optimized query
        """
        # Add LIMIT if missing for SELECT queries
        if query.strip().upper().startswith("SELECT") and "LIMIT" not in query.upper():
            query = f"{query.rstrip(';')} LIMIT 1000"

        # Add indexes hints for large tables
        if "FROM files" in query.upper() and "WHERE" in query.upper():
            query = query.replace("FROM files", "FROM files WITH (INDEX(idx_files_created_at))")

        # Optimize JOIN operations
        if "JOIN" in query.upper():
            query = query.replace("JOIN", "INNER JOIN") if "LEFT JOIN" not in query.upper() else query

        return query

    def cache_query_result(self, query: str, result: Any, ttl: int = 300):
        """Cache query result.

        Args:
            query: Query string
            result: Query result
            ttl: Time to live in seconds
        """
        cache_key = hashlib.md5(f"{query}:{str(params)}".encode()).hexdigest()
        self.query_cache[cache_key] = {
            "result": result,
            "timestamp": time.time(),
            "ttl": ttl,
        }

    def get_cached_result(self, query: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get cached query result.

        Args:
            query: Query string
            params: Query parameters

        Returns:
            Cached result or None
        """
        cache_key = hashlib.md5(f"{query}:{str(params)}".encode()).hexdigest()

        if cache_key in self.query_cache:
            cached = self.query_cache[cache_key]
            if time.time() - cached["timestamp"] < cached["ttl"]:
                return cached["result"]
            else:
                del self.query_cache[cache_key]

        return None

    def get_query_stats(self, query: str) -> Dict[str, Any]:
        """Get query execution statistics.

        Args:
            query: Query string

        Returns:
            Query statistics
        """
        return self.query_stats.get(query, {
            "execution_count": 0,
            "total_time": 0.0,
            "avg_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
        })


class CacheManager:
    """High-performance cache manager."""

    def __init__(self, config: PerformanceConfig):
        """Initialize cache manager."""
        self.config = config
        self.cache: Dict[str, Any] = {}
        self.access_times: Dict[str, float] = {}
        self.access_counts: Dict[str, int] = {}
        self.redis_client = None

        # Try to initialize Redis if available
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            self.redis_client.ping()
        except Exception:
            logger.warning("Redis not available, using in-memory cache")
            self.redis_client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    self._update_access_info(key)
                    return pickle.loads(cached.encode('latin-1')) if isinstance(cached, str) else cached
            except Exception as e:
                logger.error(f"Redis get error: {e}")

        # Fallback to in-memory cache
        if key in self.cache:
            self._update_access_info(key)
            return self.cache[key]

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time to live
        """
        ttl = ttl or self.config.cache_ttl

        if self.redis_client:
            try:
                serialized = pickle.dumps(value)
                if self.config.cache_compression:
                    import zlib
                    serialized = zlib.compress(serialized)

                self.redis_client.setex(key, ttl, serialized)
            except Exception as e:
                logger.error(f"Redis set error: {e}")

        # Fallback to in-memory cache
        self.cache[key] = value
        self._update_access_info(key)

        # Evict if cache is full
        if len(self.cache) > self.config.cache_max_size:
            self._evict_lru()

    def delete(self, key: str):
        """Delete value from cache.

        Args:
            key: Cache key
        """
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.error(f"Redis delete error: {e}")

        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.access_counts.pop(key, None)

    def clear(self):
        """Clear all cached values."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"Redis clear error: {e}")

        self.cache.clear()
        self.access_times.clear()
        self.access_counts.clear()

    def _update_access_info(self, key: str):
        """Update access information for LRU/LFU.

        Args:
            key: Cache key
        """
        self.access_times[key] = time.time()
        self.access_counts[key] = self.access_counts.get(key, 0) + 1

    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.access_times:
            return

        # Remove item with oldest access time
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self.delete(lru_key)


# Global performance components
performance_config = PerformanceConfig()
performance_monitor = PerformanceMonitor(performance_config)
query_optimizer = QueryOptimizer()
cache_manager = CacheManager(performance_config)


def performance_monitor_decorator(func: Callable) -> Callable:
    """Decorator to monitor function performance.

    Args:
        func: Function to monitor

    Returns:
        Wrapped function
    """
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time

            performance_monitor.record_metric(
                name=f"{func.__name__}_duration",
                value=duration,
                labels={"status": "success"},
            )

            return result
        except Exception as e:
            duration = time.time() - start_time

            performance_monitor.record_metric(
                name=f"{func.__name__}_duration",
                value=duration,
                labels={"status": "error"},
            )

            performance_monitor.record_metric(
                name=f"{func.__name__}_errors",
                value=1.0,
                labels={"error_type": type(e).__name__},
            )

            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            performance_monitor.record_metric(
                name=f"{func.__name__}_duration",
                value=duration,
                labels={"status": "success"},
            )

            return result
        except Exception as e:
            duration = time.time() - start_time

            performance_monitor.record_metric(
                name=f"{func.__name__}_duration",
                value=duration,
                labels={"status": "error"},
            )

            performance_monitor.record_metric(
                name=f"{func.__name__}_errors",
                value=1.0,
                labels={"error_type": type(e).__name__},
            )

            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def cache_result(ttl: Optional[int] = None):
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)

            return result

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


class FileOperationOptimizer:
    """Optimized file operations."""

    @staticmethod
    @performance_monitor_decorator
    async def optimized_file_read(file_path: str, buffer_size: int = 8192) -> bytes:
        """Optimized file reading with buffering.

        Args:
            file_path: File path
            buffer_size: Buffer size

        Returns:
            File content
        """
        try:
            import aiofiles

            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()

            return content
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    @staticmethod
    @performance_monitor_decorator
    async def optimized_file_write(file_path: str, content: bytes, buffer_size: int = 8192) -> bool:
        """Optimized file writing with buffering.

        Args:
            file_path: File path
            content: File content
            buffer_size: Buffer size

        Returns:
            Success status
        """
        try:
            import aiofiles
            import os

            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            return False

    @staticmethod
    @performance_monitor_decorator
    async def parallel_file_operations(
        operations: List[Dict[str, Any]],
        max_concurrency: int = 10,
    ) -> List[Dict[str, Any]]:
        """Execute file operations in parallel.

        Args:
            operations: List of operations
            max_concurrency: Maximum concurrent operations

        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_operation(op: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                operation_type = op.get("type")
                if operation_type == "read":
                    content = await FileOperationOptimizer.optimized_file_read(
                        op["file_path"],
                        op.get("buffer_size", 8192),
                    )
                    return {"success": True, "content": content, "file_path": op["file_path"]}
                elif operation_type == "write":
                    success = await FileOperationOptimizer.optimized_file_write(
                        op["file_path"],
                        op["content"],
                        op.get("buffer_size", 8192),
                    )
                    return {"success": success, "file_path": op["file_path"]}
                else:
                    return {"success": False, "error": "Unknown operation type"}

        results = await asyncio.gather(*[execute_operation(op) for op in operations])
        return results


class DatabaseOptimizer:
    """Database performance optimization."""

    @staticmethod
    def get_optimized_file_query(filters: Optional[Dict[str, Any]] = None) -> str:
        """Get optimized file query.

        Args:
            filters: Query filters

        Returns:
            Optimized SQL query
        """
        base_query = """
            SELECT f.id, f.filename, f.size, f.content_type, f.created_at, f.updated_at
            FROM files f
        """

        conditions = []
        params = {}

        if filters:
            if "folder_id" in filters:
                conditions.append("f.folder_id = :folder_id")
                params["folder_id"] = filters["folder_id"]

            if "file_type" in filters:
                conditions.append("f.content_type = :file_type")
                params["file_type"] = filters["file_type"]

            if "created_after" in filters:
                conditions.append("f.created_at > :created_after")
                params["created_after"] = filters["created_after"]

        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)

        # Add ordering for better performance
        base_query += " ORDER BY f.created_at DESC"

        # Add limit for pagination
        if "limit" in filters:
            base_query += " LIMIT :limit"
            params["limit"] = filters["limit"]

        if "offset" in filters:
            base_query += " OFFSET :offset"
            params["offset"] = filters["offset"]

        return query_optimizer.optimize_query(base_query, params), params

    @staticmethod
    @performance_monitor_decorator
    @cache_result(ttl=300)
    async def get_file_stats() -> Dict[str, Any]:
        """Get file statistics with caching.

        Returns:
            File statistics
        """
        # This would execute actual database queries
        # For now, return mock statistics
        return {
            "total_files": 10000,
            "total_size": 1024 * 1024 * 1024 * 10,  # 10GB
            "file_types": {
                "text/plain": 5000,
                "image/jpeg": 3000,
                "application/pdf": 2000,
            },
            "avg_file_size": 1024 * 1024,  # 1MB
        }


class MemoryOptimizer:
    """Memory usage optimization."""

    @staticmethod
    def optimize_memory_usage():
        """Optimize memory usage."""
        import gc

        # Force garbage collection
        gc.collect()

        # Set lower memory thresholds
        gc.set_threshold(700, 10, 10)

    @staticmethod
    def get_memory_usage() -> Dict[str, Any]:
        """Get current memory usage statistics.

        Returns:
            Memory usage information
        """
        import psutil
        import sys

        process = psutil.Process()

        return {
            "rss": process.memory_info().rss,  # Resident Set Size
            "vms": process.memory_info().vms,  # Virtual Memory Size
            "percent": process.memory_percent(),
            "available": psutil.virtual_memory().available,
            "total": psutil.virtual_memory().total,
            "python_allocated": sys.getsizeof([]),  # Approximation
        }


# Performance optimization utilities
async def optimize_system_performance():
    """Optimize overall system performance."""
    logger.info("Starting system performance optimization")

    # Optimize memory usage
    MemoryOptimizer.optimize_memory_usage()

    # Clear old metrics
    performance_monitor.clear_metrics()

    # Optimize cache
    cache_manager.clear()

    # Reset query statistics
    query_optimizer.query_stats.clear()

    logger.info("System performance optimization completed")


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report.

    Returns:
        Performance report
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime": (datetime.utcnow() - performance_monitor.start_time).total_seconds(),
        "cache_stats": {
            "cache_size": len(cache_manager.cache),
            "cache_hits": len([k for k in cache_manager.access_counts]),
        },
        "query_stats": {
            "cached_queries": len(query_optimizer.query_cache),
            "total_queries": sum(
                stats.get("execution_count", 0)
                for stats in query_optimizer.query_stats.values()
            ),
        },
        "slow_operations": performance_monitor.get_slow_operations(),
        "memory_usage": MemoryOptimizer.get_memory_usage(),
        "metric_summaries": {
            name: performance_monitor.get_metric_summary(name)
            for name in performance_monitor.metrics.keys()
        },
    }

    return report


# Export performance components
__all__ = [
    "PerformanceConfig",
    "PerformanceMonitor",
    "QueryOptimizer",
    "CacheManager",
    "FileOperationOptimizer",
    "DatabaseOptimizer",
    "MemoryOptimizer",
    "performance_monitor_decorator",
    "cache_result",
    "optimize_system_performance",
    "get_performance_report",
    "performance_config",
    "performance_monitor",
    "query_optimizer",
    "cache_manager",
]
