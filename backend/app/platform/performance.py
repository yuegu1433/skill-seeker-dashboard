"""Performance optimization for platform system.

This module provides performance optimization utilities and configurations
for the multi-platform system.
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import weakref

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Performance optimization strategies."""
    CACHING = "caching"
    CONCURRENCY = "concurrency"
    BATCHING = "batching"
    LAZY_LOADING = "lazy_loading"
    CONNECTION_POOLING = "connection_pooling"
    RESOURCE_POOLING = "resource_pooling"


@dataclass
class PerformanceMetrics:
    """Performance metrics tracking."""
    operation_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime
    metadata: Dict[str, Any]

    @property
    def is_slow(self) -> bool:
        """Check if operation is considered slow."""
        return self.execution_time > 5.0  # 5 seconds

    @property
    def is_memory_intensive(self) -> bool:
        """Check if operation is memory intensive."""
        return self.memory_usage > 100 * 1024 * 1024  # 100MB


class PerformanceOptimizer:
    """Performance optimization manager.

    Provides various performance optimization strategies including:
    - Caching for frequently accessed data
    - Connection pooling for API calls
    - Resource pooling for expensive operations
    - Lazy loading for large datasets
    - Batching for multiple operations
    """

    def __init__(self):
        """Initialize performance optimizer."""
        self.cache = {}
        self.connection_pools = {}
        self.resource_pools = {}
        self.metrics_history: List[PerformanceMetrics] = []
        self.optimization_strategies = {
            OptimizationStrategy.CACHING: self._optimize_with_caching,
            OptimizationStrategy.CONCURRENCY: self._optimize_with_concurrency,
            OptimizationStrategy.BATCHING: self._optimize_with_batching,
            OptimizationStrategy.LAZY_LOADING: self._optimize_with_lazy_loading,
            OptimizationStrategy.CONNECTION_POOLING: self._optimize_with_connection_pooling,
            OptimizationStrategy.RESOURCE_POOLING: self._optimize_with_resource_pooling
        }

        # Performance thresholds
        self.slow_operation_threshold = 5.0  # seconds
        self.memory_threshold = 100 * 1024 * 1024  # 100MB
        self.cache_ttl = 3600  # 1 hour
        self.max_cache_size = 1000

    async def optimize_operation(
        self,
        operation: Callable,
        operation_name: str,
        strategy: OptimizationStrategy,
        *args,
        **kwargs
    ) -> Any:
        """Optimize an operation using specified strategy.

        Args:
            operation: Async operation to optimize
            operation_name: Name of the operation
            strategy: Optimization strategy to use
            *args: Operation arguments
            **kwargs: Operation keyword arguments

        Returns:
            Operation result
        """
        # Record start time
        start_time = time.time()

        # Execute optimization
        optimizer_func = self.optimization_strategies.get(strategy)
        if optimizer_func:
            result = await optimizer_func(operation, operation_name, *args, **kwargs)
        else:
            result = await operation(*args, **kwargs)

        # Record metrics
        execution_time = time.time() - start_time
        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            memory_usage=0,  # Would be measured in real implementation
            cpu_usage=0,  # Would be measured in real implementation
            timestamp=datetime.utcnow(),
            metadata={
                "strategy": strategy.value,
                "args_count": len(args),
                "kwargs_count": len(kwargs)
            }
        )

        self.metrics_history.append(metrics)

        # Log slow operations
        if metrics.is_slow:
            logger.warning(
                f"Slow operation detected: {operation_name} "
                f"took {execution_time:.2f}s"
            )

        # Trim metrics history
        if len(self.metrics_history) > 10000:
            self.metrics_history = self.metrics_history[-5000:]

        return result

    async def _optimize_with_caching(
        self,
        operation: Callable,
        operation_name: str,
        cache_key: Optional[str] = None,
        ttl: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """Optimize with caching."""
        # Generate cache key
        if cache_key is None:
            cache_key = self._generate_cache_key(operation_name, args, kwargs)

        # Check cache
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if time.time() - entry["timestamp"] < (ttl or self.cache_ttl):
                logger.debug(f"Cache hit for {operation_name}")
                return entry["result"]

        # Execute operation
        result = await operation(*args, **kwargs)

        # Cache result
        self._cache_result(cache_key, result)

        return result

    async def _optimize_with_concurrency(
        self,
        operation: Callable,
        operation_name: str,
        max_concurrent: int = 10,
        *args,
        **kwargs
    ) -> Any:
        """Optimize with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_operation():
            async with semaphore:
                return await operation(*args, **kwargs)

        return await bounded_operation()

    async def _optimize_with_batching(
        self,
        operation: Callable,
        operation_name: str,
        batch_size: int = 100,
        *args,
        **kwargs
    ) -> Any:
        """Optimize with batching."""
        # This would batch multiple operations together
        # For now, just execute the operation
        return await operation(*args, **kwargs)

    async def _optimize_with_lazy_loading(
        self,
        operation: Callable,
        operation_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Optimize with lazy loading."""
        # This would defer expensive operations until needed
        # For now, just execute the operation
        return await operation(*args, **kwargs)

    async def _optimize_with_connection_pooling(
        self,
        operation: Callable,
        operation_name: str,
        pool_name: str,
        *args,
        **kwargs
    ) -> Any:
        """Optimize with connection pooling."""
        # Get or create connection pool
        if pool_name not in self.connection_pools:
            self.connection_pools[pool_name] = self._create_connection_pool(pool_name)

        # Use connection from pool
        connection = await self._get_connection(pool_name)

        try:
            return await operation(connection, *args, **kwargs)
        finally:
            await self._return_connection(pool_name, connection)

    async def _optimize_with_resource_pooling(
        self,
        operation: Callable,
        operation_name: str,
        resource_type: str,
        *args,
        **kwargs
    ) -> Any:
        """Optimize with resource pooling."""
        # Get or create resource pool
        if resource_type not in self.resource_pools:
            self.resource_pools[resource_type] = self._create_resource_pool(resource_type)

        # Get resource from pool
        resource = await self._get_resource(resource_type)

        try:
            return await operation(resource, *args, **kwargs)
        finally:
            await self._return_resource(resource_type, resource)

    def _generate_cache_key(
        self,
        operation_name: str,
        args: tuple,
        kwargs: dict
    ) -> str:
        """Generate cache key for operation."""
        import hashlib

        # Create hash from operation name, args, and kwargs
        key_data = {
            "operation": operation_name,
            "args": args,
            "kwargs": kwargs
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _cache_result(self, cache_key: str, result: Any) -> None:
        """Cache operation result."""
        # Clean up old cache if needed
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entries
            oldest_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k]["timestamp"]
            )[:100]
            for key in oldest_keys:
                del self.cache[key]

        # Add new entry
        self.cache[cache_key] = {
            "result": result,
            "timestamp": time.time()
        }

    def _create_connection_pool(self, pool_name: str) -> Dict[str, Any]:
        """Create a connection pool."""
        return {
            "connections": [],
            "available": [],
            "in_use": set(),
            "max_size": 10,
            "created_at": time.time()
        }

    async def _get_connection(self, pool_name: str):
        """Get connection from pool."""
        # Implementation would get actual connection
        return {"connection_id": f"{pool_name}_conn_1"}

    async def _return_connection(self, pool_name: str, connection: Dict[str, Any]) -> None:
        """Return connection to pool."""
        # Implementation would return actual connection
        pass

    def _create_resource_pool(self, resource_type: str) -> Dict[str, Any]:
        """Create a resource pool."""
        return {
            "resources": [],
            "available": [],
            "in_use": set(),
            "max_size": 5,
            "created_at": time.time()
        }

    async def _get_resource(self, resource_type: str):
        """Get resource from pool."""
        # Implementation would get actual resource
        return {"resource_id": f"{resource_type}_res_1"}

    async def _return_resource(self, resource_type: str, resource: Dict[str, Any]) -> None:
        """Return resource to pool."""
        # Implementation would return actual resource
        pass

    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.metrics_history:
            return {
                "total_operations": 0,
                "avg_execution_time": 0,
                "slow_operations": 0,
                "cache_hit_rate": 0
            }

        # Calculate statistics
        total_operations = len(self.metrics_history)
        avg_execution_time = sum(m.execution_time for m in self.metrics_history) / total_operations
        slow_operations = sum(1 for m in self.metrics_history if m.is_slow)
        cache_operations = sum(
            1 for m in self.metrics_history
            if m.metadata.get("strategy") == "caching"
        )

        return {
            "total_operations": total_operations,
            "avg_execution_time": avg_execution_time,
            "slow_operations": slow_operations,
            "slow_operation_rate": (slow_operations / total_operations * 100),
            "cache_operations": cache_operations,
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "memory_usage": sum(m.memory_usage for m in self.metrics_history),
            "most_slow_operations": self._get_most_slow_operations()
        }

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        # This would calculate based on actual cache statistics
        return 0.0

    def _get_most_slow_operations(self) -> List[str]:
        """Get list of most slow operations."""
        slow_ops = [
            m.operation_name for m in self.metrics_history
            if m.is_slow
        ]

        # Count occurrences
        from collections import Counter
        return [op for op, _ in Counter(slow_ops).most_common(10)]

    def clear_cache(self) -> None:
        """Clear optimization cache."""
        self.cache.clear()
        logger.info("Performance cache cleared")

    def cleanup_old_metrics(self, older_than_hours: int = 24) -> None:
        """Clean up old performance metrics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

        self.metrics_history = [
            m for m in self.metrics_history
            if m.timestamp > cutoff_time
        ]

        logger.info(f"Cleaned up metrics older than {older_than_hours} hours")


# Global performance optimizer instance
_performance_optimizer = None


def get_performance_optimizer() -> PerformanceOptimizer:
    """Get or create performance optimizer instance."""
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer()
    return _performance_optimizer


# Optimization decorators

def optimize_caching(ttl: Optional[int] = None):
    """Decorator to optimize function with caching."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            return await optimizer.optimize_operation(
                func,
                func.__name__,
                OptimizationStrategy.CACHING,
                ttl=ttl,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


def optimize_concurrency(max_concurrent: int = 10):
    """Decorator to optimize function with concurrency control."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            optimizer = get_performance_optimizer()
            return await optimizer.optimize_operation(
                func,
                func.__name__,
                OptimizationStrategy.CONCURRENCY,
                max_concurrent=max_concurrent,
                *args,
                **kwargs
            )
        return wrapper
    return decorator


def optimize_performance(
    strategy: OptimizationStrategy,
    **kwargs
):
    """Decorator to optimize function with specified strategy."""
    def decorator(func: Callable):
        async def wrapper(*args, **func_kwargs):
            optimizer = get_performance_optimizer()
            return await optimizer.optimize_operation(
                func,
                func.__name__,
                strategy,
                *args,
                **kwargs,
                **func_kwargs
            )
        return wrapper
    return decorator


# Performance configuration

PERFORMANCE_CONFIG = {
    "caching": {
        "enabled": True,
        "ttl": 3600,  # 1 hour
        "max_size": 1000
    },
    "concurrency": {
        "max_concurrent_operations": 10,
        "max_concurrent_api_calls": 20,
        "max_concurrent_deployments": 5
    },
    "batching": {
        "default_batch_size": 100,
        "max_batch_size": 1000
    },
    "lazy_loading": {
        "enabled": True,
        "threshold_size": 1024 * 1024  # 1MB
    },
    "connection_pooling": {
        "max_pool_size": 10,
        "pool_timeout": 30
    },
    "resource_pooling": {
        "max_pool_size": 5,
        "resource_timeout": 60
    }
}


async def configure_performance(config: Dict[str, Any]) -> None:
    """Configure performance optimizer with custom settings.

    Args:
        config: Performance configuration dictionary
    """
    optimizer = get_performance_optimizer()

    # Update cache configuration
    if "caching" in config:
        cache_config = config["caching"]
        optimizer.cache_ttl = cache_config.get("ttl", 3600)
        optimizer.max_cache_size = cache_config.get("max_size", 1000)

    logger.info("Performance optimizer configured")


if __name__ == "__main__":
    # Example usage
    async def example_operation(data: Dict[str, Any]) -> Dict[str, Any]:
        """Example async operation."""
        await asyncio.sleep(1)  # Simulate work
        return {"processed": True, "data": data}

    async def main():
        """Main example."""
        # Configure performance
        await configure_performance(PERFORMANCE_CONFIG)

        # Use optimizer
        optimizer = get_performance_optimizer()

        # Optimize operation with caching
        result = await optimizer.optimize_operation(
            example_operation,
            "example_operation",
            OptimizationStrategy.CACHING,
            data={"test": "value"}
        )

        print(f"Result: {result}")

        # Get statistics
        stats = optimizer.get_performance_statistics()
        print(f"Statistics: {json.dumps(stats, indent=2, default=str)}")

    # Run example
    asyncio.run(main())