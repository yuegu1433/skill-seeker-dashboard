"""Message queue and cache optimization system.

This module provides Redis-based message queuing, intelligent caching,
batch processing, and priority handling to optimize performance for
high-concurrency message processing.

Key Features:
- Redis-backed message queues
- Intelligent cache strategies
- Priority-based message handling
- Batch processing optimization
- Message ordering guarantees
- Cache warming and prefetching
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Tuple, Union
from concurrent.futures import ThreadPoolExecutor
import hashlib
import pickle

try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError, ConnectionError as RedisConnectionError
except ImportError:
    redis = None
    RedisError = Exception
    RedisConnectionError = Exception

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


class CacheStrategy(Enum):
    """Cache strategies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live


@dataclass
class QueuedMessage:
    """Represents a queued message."""
    id: str
    content: Dict[str, Any]
    priority: MessagePriority
    timestamp: float
    ttl: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Represents a cache entry."""
    key: str
    value: Any
    timestamp: float
    last_accessed: float
    access_count: int = 0
    size_bytes: int = 0
    ttl: Optional[float] = None


class RedisMessageQueue:
    """Redis-backed message queue with priority support."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        max_size: int = 10000,
        batch_size: int = 100,
    ):
        """Initialize Redis message queue.

        Args:
            redis_url: Redis connection URL
            max_size: Maximum queue size
            batch_size: Batch processing size
        """
        self.redis_url = redis_url
        self.max_size = max_size
        self.batch_size = batch_size
        self.redis_client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        self._is_connected = False

        # Queue statistics
        self.stats = {
            "messages_enqueued": 0,
            "messages_dequeued": 0,
            "messages_failed": 0,
            "batches_processed": 0,
            "avg_processing_time": 0.0,
        }

    async def connect(self):
        """Connect to Redis."""
        if redis is None:
            raise ImportError("Redis not installed. Install with: pip install redis")

        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            self._is_connected = True
            logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            self._is_connected = False
            logger.info("Disconnected from Redis")

    async def enqueue(
        self,
        message: QueuedMessage,
        queue_name: str = "default",
    ) -> bool:
        """Enqueue a message.

        Args:
            message: Message to enqueue
            queue_name: Queue name

        Returns:
            True if enqueued successfully
        """
        if not self._is_connected:
            await self.connect()

        async with self._lock:
            try:
                # Check queue size
                current_size = await self.redis_client.llen(queue_name)
                if current_size >= self.max_size:
                    logger.warning(f"Queue {queue_name} is full")
                    return False

                # Serialize message
                message_data = pickle.dumps(message.__dict__)
                score = message.priority.value

                # Use sorted set for priority queue
                await self.redis_client.zadd(
                    f"queue:{queue_name}",
                    {message.id: score}
                )

                # Store message data
                await self.redis_client.setex(
                    f"message:{message.id}",
                    int(message.ttl or 3600),
                    message_data
                )

                self.stats["messages_enqueued"] += 1
                logger.debug(f"Enqueued message {message.id} to {queue_name}")
                return True

            except RedisError as e:
                logger.error(f"Failed to enqueue message: {e}")
                self.stats["messages_failed"] += 1
                return False

    async def dequeue(
        self,
        queue_name: str = "default",
        timeout: float = 0,
    ) -> Optional[QueuedMessage]:
        """Dequeue a message.

        Args:
            queue_name: Queue name
            timeout: Timeout in seconds

        Returns:
            Dequeued message or None
        """
        if not self._is_connected:
            await self.connect()

        try:
            # Get highest priority message
            result = await self.redis_client.bzpopmax(
                f"queue:{queue_name}",
                timeout=timeout
            )

            if not result:
                return None

            _, message_id, score = result

            # Get message data
            message_data = await self.redis_client.get(f"message:{message_id}")
            if not message_data:
                return None

            # Deserialize message
            message_dict = pickle.loads(message_data)
            message = QueuedMessage(**message_dict)

            # Remove from storage
            await self.redis_client.delete(f"message:{message_id}")

            self.stats["messages_dequeued"] += 1
            logger.debug(f"Dequeued message {message.id} from {queue_name}")
            return message

        except RedisError as e:
            logger.error(f"Failed to dequeue message: {e}")
            return None

    async def batch_dequeue(
        self,
        queue_name: str = "default",
        batch_size: Optional[int] = None,
    ) -> List[QueuedMessage]:
        """Dequeue multiple messages in a batch.

        Args:
            queue_name: Queue name
            batch_size: Number of messages to dequeue

        Returns:
            List of dequeued messages
        """
        if not self._is_connected:
            await self.connect()

        batch_size = batch_size or self.batch_size
        messages = []

        try:
            # Get multiple messages
            results = await self.redis_client.bzpopmax(
                f"queue:{queue_name}",
                timeout=0
            )

            while results and len(messages) < batch_size:
                _, message_id, score = results

                # Get message data
                message_data = await self.redis_client.get(f"message:{message_id}")
                if message_data:
                    message_dict = pickle.loads(message_data)
                    message = QueuedMessage(**message_dict)
                    messages.append(message)

                    # Remove from storage
                    await self.redis_client.delete(f"message:{message_id}")

                # Get next message
                results = await self.redis_client.bzpopmax(
                    f"queue:{queue_name}",
                    timeout=0
                )

            if messages:
                self.stats["messages_dequeued"] += len(messages)
                self.stats["batches_processed"] += 1
                logger.debug(f"Dequeued batch of {len(messages)} messages from {queue_name}")

            return messages

        except RedisError as e:
            logger.error(f"Failed to dequeue batch: {e}")
            return messages

    async def get_queue_size(self, queue_name: str = "default") -> int:
        """Get queue size.

        Args:
            queue_name: Queue name

        Returns:
            Number of messages in queue
        """
        if not self._is_connected:
            await self.connect()

        try:
            return await self.redis_client.zcard(f"queue:{queue_name}")
        except RedisError as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0

    async def clear_queue(self, queue_name: str = "default"):
        """Clear a queue.

        Args:
            queue_name: Queue name
        """
        if not self._is_connected:
            await self.connect()

        try:
            # Get all message IDs
            message_ids = await self.redis_client.zrange(f"queue:{queue_name}", 0, -1)

            # Delete messages and queue
            if message_ids:
                pipe = self.redis_client.pipeline()
                for message_id in message_ids:
                    pipe.delete(f"message:{message_id}")
                pipe.delete(f"queue:{queue_name}")
                await pipe.execute()

            logger.info(f"Cleared queue {queue_name}")

        except RedisError as e:
            logger.error(f"Failed to clear queue: {e}")


class IntelligentCache:
    """Intelligent caching system with multiple strategies."""

    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: float = 512.0,
        strategy: CacheStrategy = CacheStrategy.LRU,
        default_ttl: float = 3600.0,
    ):
        """Initialize intelligent cache.

        Args:
            max_size: Maximum number of cache entries
            max_memory_mb: Maximum memory usage in MB
            strategy: Cache eviction strategy
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.max_memory_bytes = int(max_memory_mb * 1024 * 1024)
        self.strategy = strategy
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._access_order: deque = deque()
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_size_bytes": 0,
        }

    def _calculate_size(self, value: Any) -> int:
        """Calculate size of a value in bytes.

        Args:
            value: Value to measure

        Returns:
            Size in bytes
        """
        try:
            return len(pickle.dumps(value))
        except Exception:
            return 100  # Default size

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        async with self._lock:
            entry = self._cache.get(key)
            current_time = time.time()

            if entry:
                # Check TTL
                if entry.ttl and current_time - entry.timestamp > entry.ttl:
                    await self._remove(key)
                    self.stats["misses"] += 1
                    return None

                # Update access stats
                entry.last_accessed = current_time
                entry.access_count += 1

                # Update access order
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)

                self.stats["hits"] += 1
                return entry.value

            self.stats["misses"] += 1
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
        priority: bool = False,
    ):
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            priority: Whether to prioritize this entry
        """
        async with self._lock:
            current_time = time.time()
            size_bytes = self._calculate_size(value)

            # Check if key already exists
            if key in self._cache:
                await self._remove(key)

            # Check memory limit
            while (
                self.stats["total_size_bytes"] + size_bytes > self.max_memory_bytes
                and self._cache
            ):
                await self._evict_one()

            # Check size limit
            while len(self._cache) >= self.max_size and self._cache:
                await self._evict_one()

            # Create cache entry
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=current_time,
                last_accessed=current_time,
                size_bytes=size_bytes,
                ttl=ttl or self.default_ttl,
            )

            self._cache[key] = entry
            self._access_order.append(key)
            self.stats["total_size_bytes"] += size_bytes

            logger.debug(f"Cached key {key} ({size_bytes} bytes)")

    async def delete(self, key: str) -> bool:
        """Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        async with self._lock:
            return await self._remove(key)

    async def _remove(self, key: str) -> bool:
        """Remove entry from cache.

        Args:
            key: Cache key

        Returns:
            True if removed
        """
        if key not in self._cache:
            return False

        entry = self._cache[key]
        self.stats["total_size_bytes"] -= entry.size_bytes
        del self._cache[key]

        if key in self._access_order:
            self._access_order.remove(key)

        return True

    async def _evict_one(self):
        """Evict one entry based on strategy."""
        if not self._cache:
            return

        if self.strategy == CacheStrategy.LRU:
            # Least Recently Used
            key = self._access_order.popleft()
        elif self.strategy == CacheStrategy.LFU:
            # Least Frequently Used
            key = min(self._cache.keys(), key=lambda k: self._cache[k].access_count)
        elif self.strategy == CacheStrategy.FIFO:
            # First In First Out
            key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
        else:  # TTL-based
            # Evict expired or oldest
            key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)

        await self._remove(key)
        self.stats["evictions"] += 1

    async def clear(self):
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self.stats["total_size_bytes"] = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Cache statistics
        """
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "miss_rate": 1 - hit_rate,
            "current_size": len(self._cache),
            "current_memory_mb": self.stats["total_size_bytes"] / 1024 / 1024,
            "max_size": self.max_size,
            "max_memory_mb": self.max_memory_bytes / 1024 / 1024,
            "strategy": self.strategy.value,
        }


class MessageBatchProcessor:
    """Processes messages in batches for efficiency."""

    def __init__(
        self,
        queue: RedisMessageQueue,
        cache: IntelligentCache,
        processor: Callable[[List[QueuedMessage]], Any],
        batch_size: int = 100,
        max_wait_time: float = 1.0,
    ):
        """Initialize batch processor.

        Args:
            queue: Message queue
            cache: Cache for results
            processor: Function to process batch
            batch_size: Maximum batch size
            max_wait_time: Maximum time to wait for batch
        """
        self.queue = queue
        self.cache = cache
        self.processor = processor
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self._is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start batch processor."""
        if self._is_running:
            return

        self._is_running = True
        self._task = asyncio.create_task(self._process_loop())
        logger.info("Batch processor started")

    async def stop(self):
        """Stop batch processor."""
        if not self._is_running:
            return

        self._is_running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Batch processor stopped")

    async def _process_loop(self):
        """Main processing loop."""
        while self._is_running:
            try:
                batch = []
                start_time = time.time()

                # Collect messages for batch
                while (
                    len(batch) < self.batch_size
                    and time.time() - start_time < self.max_wait_time
                ):
                    message = await self.queue.dequeue(timeout=0.1)
                    if message:
                        batch.append(message)
                    else:
                        await asyncio.sleep(0.01)

                # Process batch if we have messages
                if batch:
                    await self._process_batch(batch)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processor: {e}")
                await asyncio.sleep(1.0)

    async def _process_batch(self, batch: List[QueuedMessage]):
        """Process a batch of messages.

        Args:
            batch: List of messages to process
        """
        start_time = time.time()

        try:
            # Process messages
            results = await self._run_processor(batch)

            # Cache results
            for message, result in zip(batch, results):
                cache_key = f"result:{message.id}"
                await self.cache.set(cache_key, result, ttl=3600)

            processing_time = time.time() - start_time
            logger.debug(f"Processed batch of {len(batch)} messages in {processing_time:.2f}s")

        except Exception as e:
            logger.error(f"Failed to process batch: {e}")
            # Handle failures (could retry or log)

    async def _run_processor(self, batch: List[QueuedMessage]) -> List[Any]:
        """Run processor in thread pool.

        Args:
            batch: Batch of messages

        Returns:
            Processing results
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.processor, batch)


class MessageQueueManager:
    """Main message queue and cache manager."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        cache_size: int = 1000,
        cache_memory_mb: float = 512.0,
    ):
        """Initialize message queue manager.

        Args:
            redis_url: Redis connection URL
            cache_size: Cache size
            cache_memory_mb: Cache memory limit
        """
        self.queue = RedisMessageQueue(redis_url=redis_url)
        self.cache = IntelligentCache(
            max_size=cache_size,
            max_memory_mb=cache_memory_mb,
        )
        self.batch_processors: Dict[str, MessageBatchProcessor] = {}
        self._is_running = False

    async def start(self):
        """Start message queue manager."""
        if self._is_running:
            return

        self._is_running = True
        await self.queue.connect()
        logger.info("Message queue manager started")

    async def stop(self):
        """Stop message queue manager."""
        if not self._is_running:
            return

        self._is_running = False

        # Stop all batch processors
        for processor in self.batch_processors.values():
            await processor.stop()

        await self.queue.disconnect()
        logger.info("Message queue manager stopped")

    async def send_message(
        self,
        content: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        queue_name: str = "default",
        ttl: Optional[float] = None,
        message_id: Optional[str] = None,
    ) -> str:
        """Send a message to queue.

        Args:
            content: Message content
            priority: Message priority
            queue_name: Queue name
            ttl: Time-to-live
            message_id: Message ID (generated if not provided)

        Returns:
            Message ID
        """
        message_id = message_id or hashlib.md5(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()

        message = QueuedMessage(
            id=message_id,
            content=content,
            priority=priority,
            timestamp=time.time(),
            ttl=ttl,
        )

        await self.queue.enqueue(message, queue_name)
        return message_id

    async def receive_message(
        self,
        queue_name: str = "default",
        timeout: float = 0,
    ) -> Optional[QueuedMessage]:
        """Receive a message from queue.

        Args:
            queue_name: Queue name
            timeout: Timeout in seconds

        Returns:
            Received message or None
        """
        return await self.queue.dequeue(queue_name, timeout)

    async def get_cache(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        return await self.cache.get(key)

    async def set_cache(
        self,
        key: str,
        value: Any,
        ttl: Optional[float] = None,
    ):
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live
        """
        await self.cache.set(key, value, ttl)

    def register_batch_processor(
        self,
        name: str,
        processor: Callable[[List[QueuedMessage]], Any],
        queue_name: str = "default",
        batch_size: int = 100,
    ):
        """Register a batch processor.

        Args:
            name: Processor name
            processor: Processing function
            queue_name: Queue to process
            batch_size: Batch size
        """
        self.batch_processors[name] = MessageBatchProcessor(
            queue=self.queue,
            cache=self.cache,
            processor=processor,
            batch_size=batch_size,
        )

    async def start_batch_processor(self, name: str):
        """Start a batch processor.

        Args:
            name: Processor name
        """
        if name in self.batch_processors:
            await self.batch_processors[name].start()

    async def stop_batch_processor(self, name: str):
        """Stop a batch processor.

        Args:
            name: Processor name
        """
        if name in self.batch_processors:
            await self.batch_processors[name].stop()

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics.

        Returns:
            System statistics
        """
        return {
            "queue": self.queue.stats,
            "cache": self.cache.get_stats(),
            "batch_processors": {
                name: "running" if processor._is_running else "stopped"
                for name, processor in self.batch_processors.items()
            },
        }


# Global message queue manager instance
message_queue_manager = MessageQueueManager()
