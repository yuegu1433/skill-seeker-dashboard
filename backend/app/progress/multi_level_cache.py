"""Multi-level caching system for real-time progress tracking.

This module provides a multi-level caching system including:
- L1: In-memory cache
- L2: Redis cache
- Cache warming and preloading
- Cache invalidation and eviction
- Performance monitoring
"""

import asyncio
import json
import time
import logging
from typing import Any, Dict, List, Optional, Callable, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict, defaultdict
from threading import Lock
import hashlib
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class CacheLevel(Enum):
    """Cache levels."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"


class EvictionPolicy(Enum):
    """Cache eviction policies."""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"


@dataclass
class CacheEntry:
    """Cache entry structure."""
    key: str
    value: Any
    level: CacheLevel
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    ttl: Optional[float] = None
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheConfig:
    """Cache configuration."""
    cache_name: str
    level: CacheLevel
    max_size: int = 1000
    ttl: float = 3600.0
    eviction_policy: EvictionPolicy = EvictionPolicy.LRU
    compression_enabled: bool = False
    serialization_format: str = "json"
    stats_enabled: bool = True


class MemoryCache:
    """L1 in-memory cache with LRU eviction."""

    def __init__(self, config: CacheConfig):
        """Initialize memory cache.

        Args:
            config: Cache configuration
        """
        self.config = config
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "inserts": 0,
            "deletes": 0,
        }

    def _calculate_size(self, value: Any) -> int:
        """Calculate approximate size of value in bytes.

        Args:
            value: Value to size

        Returns:
            Size in bytes
        """
        try:
            return len(json.dumps(value, default=str).encode("utf-8"))
        except Exception:
            return 100  # Default size

    def _should_evict(self) -> bool:
        """Check if cache should evict entries.

        Returns:
            True if eviction is needed
        """
        return len(self._cache) >= self.config.max_size

    def _evict_entry(self):
        """Evict an entry based on eviction policy."""
        if not self._cache:
            return

        if self.config.eviction_policy == EvictionPolicy.LRU:
            # Remove least recently used
            self._cache.popitem(last=False)

        elif self.config.eviction_policy == EvictionPolicy.FIFO:
            # Remove first inserted
            self._cache.popitem(last=False)

        elif self.config.eviction_policy == EvictionPolicy.LFU:
            # Remove least frequently used
            min_access = min(entry.access_count for entry in self._cache.values())
            lfu_keys = [k for k, v in self._cache.items() if v.access_count == min_access]
            if lfu_keys:
                self._cache.pop(lfu_keys[0])

        self._stats["evictions"] += 1

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry:
                # Check TTL
                if entry.ttl and time.time() - entry.created_at > entry.ttl:
                    del self._cache[key]
                    self._stats["misses"] += 1
                    return None

                # Update access statistics
                entry.last_accessed = time.time()
                entry.access_count += 1

                # Move to end (most recently used)
                self._cache.move_to_end(key)

                self._stats["hits"] += 1
                return entry.value

            self._stats["misses"] += 1
            return None

    def put(self, key: str, value: Any, ttl: Optional[float] = None):
        """Put value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self._lock:
            # Calculate size
            size_bytes = self._calculate_size(value)

            # Evict if necessary
            if key not in self._cache and self._should_evict():
                self._evict_entry()

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                level=CacheLevel.L1_MEMORY,
                ttl=ttl or self.config.ttl,
                size_bytes=size_bytes,
            )

            self._cache[key] = entry
            self._stats["inserts"] += 1

    def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                **self._stats,
                "hit_rate": hit_rate,
                "current_size": len(self._cache),
                "max_size": self.config.max_size,
                "utilization": len(self._cache) / self.config.max_size,
            }


class RedisCache:
    """L2 Redis cache."""

    def __init__(self, config: CacheConfig, redis_url: str = "redis://localhost:6379"):
        """Initialize Redis cache.

        Args:
            config: Cache configuration
            redis_url: Redis connection URL
        """
        self.config = config
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "inserts": 0,
            "deletes": 0,
        }

    async def initialize(self):
        """Initialize Redis connection."""
        try:
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=10,
                socket_timeout=10,
                retry_on_timeout=True,
            )

            await self.redis.ping()
            logger.info(f"Redis cache initialized: {self.config.cache_name}")

        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            raise

    async def _serialize(self, value: Any) -> str:
        """Serialize value for Redis storage.

        Args:
            value: Value to serialize

        Returns:
            Serialized string
        """
        try:
            return json.dumps(value, default=str)
        except Exception:
            return str(value)

    async def _deserialize(self, data: str) -> Any:
        """Deserialize value from Redis.

        Args:
            data: Serialized data

        Returns:
            Deserialized value
        """
        try:
            return json.loads(data)
        except Exception:
            return data

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis:
            await self.initialize()

        try:
            data = await self.redis.get(f"{self.config.cache_name}:{key}")

            if data:
                value = await self._deserialize(data)
                self._stats["hits"] += 1
                return value

            self._stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            self._stats["misses"] += 1
            return None

    async def put(self, key: str, value: Any, ttl: Optional[float] = None):
        """Put value in Redis cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self.redis:
            await self.initialize()

        try:
            data = await self._serialize(value)
            ttl_seconds = ttl or self.config.ttl

            await self.redis.setex(
                f"{self.config.cache_name}:{key}",
                int(ttl_seconds),
                data
            )

            self._stats["inserts"] += 1

        except Exception as e:
            logger.error(f"Redis cache put error: {e}")

    async def delete(self, key: str) -> bool:
        """Delete value from Redis cache.

        Args:
            key: Cache key

        Returns:
            True if key existed and was deleted
        """
        if not self.redis:
            await self.initialize()

        try:
            result = await self.redis.delete(f"{self.config.cache_name}:{key}")
            if result:
                self._stats["deletes"] += 1
            return bool(result)

        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            return False

    async def clear(self):
        """Clear all cache entries."""
        if not self.redis:
            await self.initialize()

        try:
            await self.redis.delete(f"{self.config.cache_name}:*")
            logger.info(f"Cleared Redis cache: {self.config.cache_name}")

        except Exception as e:
            logger.error(f"Redis cache clear error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics.

        Returns:
            Cache statistics
        """
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self._stats,
            "hit_rate": hit_rate,
        }


class MultiLevelCache:
    """Multi-level cache with L1 (memory) and L2 (Redis)."""

    def __init__(
        self,
        name: str,
        l1_config: CacheConfig,
        l2_config: Optional[CacheConfig] = None,
        redis_url: str = "redis://localhost:6379",
        enable_warming: bool = True,
    ):
        """Initialize multi-level cache.

        Args:
            name: Cache name
            l1_config: L1 (memory) cache configuration
            l2_config: L2 (Redis) cache configuration
            redis_url: Redis connection URL
            enable_warming: Enable cache warming
        """
        self.name = name
        self.l1_config = l1_config
        self.l2_config = l2_config or CacheConfig(
            cache_name=f"{name}_l2",
            level=CacheLevel.L2_REDIS,
            max_size=10000,
        )
        self.redis_url = redis_url
        self.enable_warming = enable_warming

        # Initialize caches
        self.l1_cache = MemoryCache(l1_config)
        self.l2_cache = RedisCache(self.l2_config, redis_url)

        # Statistics
        self._stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "l1_to_l2_promotions": 0,
            "l2_to_l1_demotions": 0,
        }

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._warming_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the multi-level cache."""
        await self.l2_cache.initialize()

        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        if self.enable_warming:
            self._warming_task = asyncio.create_task(self._warming_loop())

        logger.info(f"Multi-level cache started: {self.name}")

    async def stop(self):
        """Stop the multi-level cache."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self._warming_task:
            self._warming_task.cancel()
            try:
                await self._warming_task
            except asyncio.CancelledError:
                pass

        logger.info(f"Multi-level cache stopped: {self.name}")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (L1 -> L2 fallback).

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try L1 cache first
        value = self.l1_cache.get(key)

        if value is not None:
            self._stats["l1_hits"] += 1
            return value

        self._stats["l1_misses"] += 1

        # Try L2 cache
        value = await self.l2_cache.get(key)

        if value is not None:
            self._stats["l2_hits"] += 1

            # Promote to L1 cache
            self.l1_cache.put(key, value)
            self._stats["l1_to_l2_promotions"] += 1

            return value

        self._stats["l2_misses"] += 1
        return None

    async def put(self, key: str, value: Any, ttl: Optional[float] = None):
        """Put value in both L1 and L2 caches.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        # Put in L1 cache
        self.l1_cache.put(key, value, ttl)

        # Put in L2 cache
        await self.l2_cache.put(key, value, ttl)

    async def delete(self, key: str) -> bool:
        """Delete value from both caches.

        Args:
            key: Cache key

        Returns:
            True if key existed in either cache
        """
        l1_deleted = self.l1_cache.delete(key)
        l2_deleted = await self.l2_cache.delete(key)

        return l1_deleted or l2_deleted

    async def clear(self):
        """Clear all cache entries."""
        self.l1_cache.clear()
        await self.l2_cache.clear()

    async def warm_cache(self, keys: List[str], fetch_func: Callable[[str], Any]):
        """Warm cache with frequently accessed keys.

        Args:
            keys: List of keys to warm
            fetch_func: Function to fetch value for key
        """
        for key in keys:
            try:
                # Check if already cached
                value = await self.get(key)
                if value is not None:
                    continue

                # Fetch and cache
                value = await fetch_func(key)
                if value is not None:
                    await self.put(key, value)

            except Exception as e:
                logger.error(f"Error warming cache for key {key}: {e}")

    async def _cleanup_loop(self):
        """Background cleanup loop for expired entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Clear L1 cache
                self.l1_cache.clear()

                # L2 cleanup is handled by Redis TTL

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup loop: {e}")

    async def _warming_loop(self):
        """Background warming loop."""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes

                # Warm cache with hot keys (this would be implemented based on actual usage)
                # For now, just log
                logger.debug(f"Cache warming cycle completed: {self.name}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache warming loop: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get multi-level cache statistics.

        Returns:
            Cache statistics
        """
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()

        total_requests = self._stats["l1_hits"] + self._stats["l1_misses"]
        overall_hit_rate = self._stats["l1_hits"] / total_requests if total_requests > 0 else 0

        return {
            "name": self.name,
            "l1_stats": l1_stats,
            "l2_stats": l2_stats,
            "multi_level_stats": self._stats,
            "overall_hit_rate": overall_hit_rate,
            "cache_hit_breakdown": {
                "l1_hit_rate": l1_stats["hit_rate"],
                "l2_hit_rate": l2_stats["hit_rate"],
                "promotion_rate": self._stats["l1_to_l2_promotions"] / total_requests if total_requests > 0 else 0,
            },
        }


class CacheManager:
    """Manager for multiple cache instances."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize cache manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.caches: Dict[str, MultiLevelCache] = {}

    def create_cache(
        self,
        name: str,
        l1_size: int = 1000,
        l2_size: int = 10000,
        ttl: float = 3600.0,
    ) -> MultiLevelCache:
        """Create a new multi-level cache.

        Args:
            name: Cache name
            l1_size: L1 cache size
            l2_size: L2 cache size
            ttl: Default TTL

        Returns:
            MultiLevelCache instance
        """
        l1_config = CacheConfig(
            cache_name=f"{name}_l1",
            level=CacheLevel.L1_MEMORY,
            max_size=l1_size,
            ttl=ttl,
        )

        l2_config = CacheConfig(
            cache_name=f"{name}_l2",
            level=CacheLevel.L2_REDIS,
            max_size=l2_size,
            ttl=ttl,
        )

        cache = MultiLevelCache(
            name=name,
            l1_config=l1_config,
            l2_config=l2_config,
            redis_url=self.redis_url,
        )

        self.caches[name] = cache
        return cache

    def get_cache(self, name: str) -> Optional[MultiLevelCache]:
        """Get cache by name.

        Args:
            name: Cache name

        Returns:
            MultiLevelCache instance or None
        """
        return self.caches.get(name)

    async def start_all(self):
        """Start all caches."""
        for cache in self.caches.values():
            await cache.start()

        logger.info(f"Started {len(self.caches)} caches")

    async def stop_all(self):
        """Stop all caches."""
        for cache in self.caches.values():
            await cache.stop()

        logger.info("Stopped all caches")

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches.

        Returns:
            Statistics for all caches
        """
        return {
            name: cache.get_stats()
            for name, cache in self.caches.items()
        }


# Global cache manager
cache_manager = CacheManager()
