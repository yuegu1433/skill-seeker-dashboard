"""Cache invalidation and update mechanisms.

This module provides cache invalidation strategies including:
- Pattern-based invalidation
- Dependency tracking
- Time-based invalidation
- Manual invalidation
- Cascading invalidation
"""

import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Set, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
from threading import Lock
import json

from .multi_level_cache import MultiLevelCache, CacheManager

logger = logging.getLogger(__name__)


class InvalidationStrategy(Enum):
    """Cache invalidation strategies."""
    IMMEDIATE = "immediate"
    DELAYED = "delayed"
    BATCHED = "batched"
    DEPENDENCY_BASED = "dependency_based"


@dataclass
class InvalidationRule:
    """Cache invalidation rule."""
    pattern: str
    strategy: InvalidationStrategy
    delay_seconds: float = 0.0
    batch_size: int = 100
    dependencies: Set[str] = field(default_factory=set)
    callback: Optional[Callable[[str], None]] = None


@dataclass
class CacheDependency:
    """Cache dependency tracking."""
    cache_key: str
    dependencies: Set[str]
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    access_count: int = 0


class CacheDependencyTracker:
    """Tracks dependencies between cache keys."""

    def __init__(self, max_history: int = 10000):
        """Initialize dependency tracker.

        Args:
            max_history: Maximum history size
        """
        self.max_history = max_history
        self.dependencies: Dict[str, CacheDependency] = {}
        self.reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._lock = Lock()

    def add_dependency(self, cache_key: str, depends_on: str):
        """Add dependency between cache keys.

        Args:
            cache_key: Dependent key
            depends_on: Key that cache_key depends on
        """
        with self._lock:
            if cache_key not in self.dependencies:
                self.dependencies[cache_key] = CacheDependency(
                    cache_key=cache_key,
                    dependencies=set(),
                )

            self.dependencies[cache_key].dependencies.add(depends_on)
            self.reverse_dependencies[depends_on].add(cache_key)

            logger.debug(f"Added dependency: {cache_key} -> {depends_on}")

    def remove_dependency(self, cache_key: str, depends_on: str):
        """Remove dependency between cache keys.

        Args:
            cache_key: Dependent key
            depends_on: Key that cache_key depends on
        """
        with self._lock:
            if cache_key in self.dependencies:
                self.dependencies[cache_key].dependencies.discard(depends_on)
                self.reverse_dependencies[depends_on].discard(cache_key)

            logger.debug(f"Removed dependency: {cache_key} -> {depends_on}")

    def update_access(self, cache_key: str):
        """Update access statistics for cache key.

        Args:
            cache_key: Cache key
        """
        with self._lock:
            if cache_key in self.dependencies:
                self.dependencies[cache_key].access_count += 1
                self.dependencies[cache_key].last_updated = time.time()

    def get_dependents(self, cache_key: str) -> Set[str]:
        """Get keys that depend on the given key.

        Args:
            cache_key: Cache key

        Returns:
            Set of dependent keys
        """
        with self._lock:
            return self.reverse_dependencies.get(cache_key, set()).copy()

    def get_dependencies(self, cache_key: str) -> Set[str]:
        """Get keys that the given key depends on.

        Args:
            cache_key: Cache key

        Returns:
            Set of dependency keys
        """
        with self._lock:
            return self.dependencies.get(cache_key, CacheDependency(cache_key, set())).dependencies.copy()

    def invalidate_key(self, cache_key: str):
        """Invalidate a cache key and its dependents.

        Args:
            cache_key: Cache key to invalidate
        """
        with self._lock:
            # Get dependents
            dependents = self.get_dependents(cache_key)

            # Add all to invalidation set
            invalidation_set = {cache_key}
            invalidation_set.update(dependents)

            logger.debug(f"Invalidating {len(invalidation_set)} keys: {invalidation_set}")

            return invalidation_set

    def get_dependency_graph(self) -> Dict[str, Set[str]]:
        """Get the entire dependency graph.

        Returns:
            Dictionary mapping keys to their dependencies
        """
        with self._lock:
            return {
                key: dep.dependencies.copy()
                for key, dep in self.dependencies.items()
            }


class CacheInvalidator:
    """Manages cache invalidation strategies."""

    def __init__(self, cache_manager: CacheManager):
        """Initialize cache invalidator.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager
        self.dependency_tracker = CacheDependencyTracker()
        self.invalidation_rules: List[InvalidationRule] = []
        self.invalidation_history: deque = deque(maxlen=1000)
        self._lock = Lock()

    def add_rule(self, rule: InvalidationRule):
        """Add an invalidation rule.

        Args:
            rule: Invalidation rule
        """
        with self._lock:
            self.invalidation_rules.append(rule)
            logger.info(f"Added invalidation rule: {rule.pattern} ({rule.strategy.value})")

    async def invalidate(
        self,
        cache_name: str,
        key_pattern: str,
        strategy: InvalidationStrategy = InvalidationStrategy.IMMEDIATE,
        delay_seconds: float = 0.0,
    ):
        """Invalidate cache entries matching pattern.

        Args:
            cache_name: Cache name
            key_pattern: Pattern to match keys
            strategy: Invalidation strategy
            delay_seconds: Delay before invalidation
        """
        cache = self.cache_manager.get_cache(cache_name)
        if not cache:
            logger.warning(f"Cache not found: {cache_name}")
            return

        # Use dependency-based invalidation if requested
        if strategy == InvalidationStrategy.DEPENDENCY_BASED:
            await self._invalidate_dependency_based(cache, key_pattern)
        else:
            await self._invalidate_direct(cache, key_pattern, strategy, delay_seconds)

        # Record in history
        with self._lock:
            self.invalidation_history.append({
                "cache_name": cache_name,
                "pattern": key_pattern,
                "strategy": strategy.value,
                "timestamp": time.time(),
                "delay_seconds": delay_seconds,
            })

    async def _invalidate_dependency_based(self, cache: MultiLevelCache, pattern: str):
        """Invalidate using dependency tracking.

        Args:
            cache: Cache instance
            pattern: Key pattern
        """
        # This would implement pattern matching for dependencies
        # For now, just log
        logger.debug(f"Dependency-based invalidation for pattern: {pattern}")

        # Get all keys matching pattern
        matching_keys = await self._get_matching_keys(cache, pattern)

        # Invalidate each key and its dependents
        for key in matching_keys:
            invalidation_set = self.dependency_tracker.invalidate_key(key)

            # Invalidate all keys in the set
            for invalid_key in invalidation_set:
                await cache.delete(invalid_key)

    async def _invalidate_direct(
        self,
        cache: MultiLevelCache,
        pattern: str,
        strategy: InvalidationStrategy,
        delay_seconds: float,
    ):
        """Invalidate using direct strategy.

        Args:
            cache: Cache instance
            pattern: Key pattern
            strategy: Invalidation strategy
            delay_seconds: Delay before invalidation
        """
        if strategy == InvalidationStrategy.IMMEDIATE:
            await self._invalidate_immediate(cache, pattern)

        elif strategy == InvalidationStrategy.DELAYED:
            await self._invalidate_delayed(cache, pattern, delay_seconds)

        elif strategy == InvalidationStrategy.BATCHED:
            await self._invalidate_batched(cache, pattern)

    async def _invalidate_immediate(self, cache: MultiLevelCache, pattern: str):
        """Immediately invalidate matching keys.

        Args:
            cache: Cache instance
            pattern: Key pattern
        """
        matching_keys = await self._get_matching_keys(cache, pattern)

        for key in matching_keys:
            await cache.delete(key)

        logger.info(f"Immediately invalidated {len(matching_keys)} keys matching pattern: {pattern}")

    async def _invalidate_delayed(self, cache: MultiLevelCache, pattern: str, delay_seconds: float):
        """Delayed invalidation with sleep.

        Args:
            cache: Cache instance
            pattern: Key pattern
            delay_seconds: Delay before invalidation
        """
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)

        matching_keys = await self._get_matching_keys(cache, pattern)

        for key in matching_keys:
            await cache.delete(key)

        logger.info(f"Delayed invalidated {len(matching_keys)} keys matching pattern: {pattern} (delay: {delay_seconds}s)")

    async def _invalidate_batched(self, cache: MultiLevelCache, pattern: str):
        """Batched invalidation for better performance.

        Args:
            cache: Cache instance
            pattern: Key pattern
        """
        matching_keys = await self._get_matching_keys(cache, pattern)

        # Invalidate in batches
        batch_size = 100
        for i in range(0, len(matching_keys), batch_size):
            batch = matching_keys[i:i + batch_size]

            for key in batch:
                await cache.delete(key)

            # Small delay between batches
            await asyncio.sleep(0.001)

        logger.info(f"Batched invalidated {len(matching_keys)} keys matching pattern: {pattern}")

    async def _get_matching_keys(self, cache: MultiLevelCache, pattern: str) -> List[str]:
        """Get keys matching pattern.

        Args:
            cache: Cache instance
            pattern: Key pattern

        Returns:
            List of matching keys
        """
        # This would implement pattern matching
        # For now, return empty list as placeholders
        # In a real implementation, you would track all cached keys
        return []

    async def cascade_invalidate(self, cache_name: str, start_key: str):
        """Cascade invalidation starting from a key.

        Args:
            cache_name: Cache name
            start_key: Starting key for cascade
        """
        cache = self.cache_manager.get_cache(cache_name)
        if not cache:
            return

        # Get invalidation set from dependency tracker
        invalidation_set = self.dependency_tracker.invalidate_key(start_key)

        # Invalidate all keys in the set
        for key in invalidation_set:
            await cache.delete(key)

        logger.info(f"Cascade invalidated {len(invalidation_set)} keys starting from: {start_key}")

    async def time_based_invalidation(self, cache_name: str, max_age_seconds: float):
        """Invalidate entries older than max age.

        Args:
            cache_name: Cache name
            max_age_seconds: Maximum age in seconds
        """
        cache = self.cache_manager.get_cache(cache_name)
        if not cache:
            return

        # This would track entry ages
        # For now, just log
        logger.info(f"Time-based invalidation for cache {cache_name}: max age {max_age_seconds}s")

    async def manual_invalidate(self, cache_name: str, keys: List[str]):
        """Manually invalidate specific keys.

        Args:
            cache_name: Cache name
            keys: List of keys to invalidate
        """
        cache = self.cache_manager.get_cache(cache_name)
        if not cache:
            return

        invalidated = 0
        for key in keys:
            if await cache.delete(key):
                invalidated += 1

        logger.info(f"Manually invalidated {invalidated}/{len(keys)} keys in cache {cache_name}")

    def get_invalidation_stats(self) -> Dict[str, Any]:
        """Get invalidation statistics.

        Returns:
            Invalidation statistics
        """
        with self._lock:
            recent_invalidations = list(self.invalidation_history)[-100:]

            return {
                "total_invalidations": len(self.invalidation_history),
                "recent_invalidations": len(recent_invalidations),
                "active_rules": len(self.invalidation_rules),
                "dependency_graph_size": len(self.dependency_tracker.dependencies),
                "recent_patterns": [
                    inv["pattern"] for inv in recent_invalidations[-10:]
                ],
            }


class CacheWarmingManager:
    """Manages cache warming and preloading."""

    def __init__(self, cache_manager: CacheManager):
        """Initialize cache warming manager.

        Args:
            cache_manager: Cache manager instance
        """
        self.cache_manager = cache_manager
        self.warming_tasks: Dict[str, asyncio.Task] = {}
        self._lock = Lock()

    async def warm_cache(
        self,
        cache_name: str,
        keys: List[str],
        fetch_func: Callable[[str], Any],
        batch_size: int = 10,
    ):
        """Warm cache with specified keys.

        Args:
            cache_name: Cache name
            keys: Keys to warm
            fetch_func: Function to fetch value for key
            batch_size: Batch size for warming
        """
        cache = self.cache_manager.get_cache(cache_name)
        if not cache:
            return

        # Start warming task
        task = asyncio.create_task(
            self._warm_cache_task(cache, keys, fetch_func, batch_size)
        )

        with self._lock:
            self.warming_tasks[cache_name] = task

        logger.info(f"Started warming cache {cache_name} with {len(keys)} keys")

    async def _warm_cache_task(
        self,
        cache: MultiLevelCache,
        keys: List[str],
        fetch_func: Callable[[str], Any],
        batch_size: int,
    ):
        """Background warming task.

        Args:
            cache: Cache instance
            keys: Keys to warm
            fetch_func: Fetch function
            batch_size: Batch size
        """
        try:
            warmed = 0
            errors = 0

            # Process keys in batches
            for i in range(0, len(keys), batch_size):
                batch = keys[i:i + batch_size]

                # Process batch
                for key in batch:
                    try:
                        # Check if already cached
                        value = await cache.get(key)
                        if value is None:
                            # Fetch and cache
                            value = await fetch_func(key)
                            if value is not None:
                                await cache.put(key, value)
                                warmed += 1

                    except Exception as e:
                        logger.error(f"Error warming key {key}: {e}")
                        errors += 1

                # Small delay between batches
                await asyncio.sleep(0.001)

            logger.info(f"Cache warming completed: {warmed} warmed, {errors} errors")

        except Exception as e:
            logger.error(f"Cache warming task error: {e}")

    def stop_warming(self, cache_name: str):
        """Stop warming task for cache.

        Args:
            cache_name: Cache name
        """
        with self._lock:
            if cache_name in self.warming_tasks:
                self.warming_tasks[cache_name].cancel()
                del self.warming_tasks[cache_name]

                logger.info(f"Stopped warming task for cache: {cache_name}")

    def get_warming_stats(self) -> Dict[str, Any]:
        """Get warming statistics.

        Returns:
            Warming statistics
        """
        with self._lock:
            return {
                "active_warming_tasks": len(self.warming_tasks),
                "warming_cache_names": list(self.warming_tasks.keys()),
            }
