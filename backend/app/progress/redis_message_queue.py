"""Redis-based message queue for real-time progress tracking.

This module provides Redis message queue implementation including:
- Multi-queue management
- Message persistence
- Retry mechanisms
- Dead letter queues
- Performance monitoring
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

logger = logging.getLogger(__name__)


class MessagePriority(Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class MessageStatus(Enum):
    """Message processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    DEAD_LETTER = "dead_letter"


@dataclass
class Message:
    """Message structure."""
    id: str
    queue: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.PENDING
    created_at: float = field(default_factory=time.time)
    processed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    ttl: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QueueConfig:
    """Message queue configuration."""
    queue_name: str
    max_size: int = 10000
    message_ttl: float = 3600.0  # 1 hour
    retry_delay: float = 60.0  # 1 minute
    max_retries: int = 3
    dead_letter_enabled: bool = True
    compression_enabled: bool = False
    batch_size: int = 100


class RedisMessageQueue:
    """Redis-based message queue with advanced features."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_config: Optional[QueueConfig] = None,
    ):
        """Initialize Redis message queue.

        Args:
            redis_url: Redis connection URL
            default_config: Default queue configuration
        """
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.default_config = default_config or QueueConfig("default")
        self.queue_configs: Dict[str, QueueConfig] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "messages_published": 0,
            "messages_consumed": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "queues_created": 0,
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

            # Test connection
            await self.redis.ping()
            logger.info("Redis message queue initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    async def create_queue(self, config: QueueConfig):
        """Create a new message queue.

        Args:
            config: Queue configuration
        """
        async with self._lock:
            self.queue_configs[config.queue_name] = config
            self._stats["queues_created"] += 1

            logger.info(f"Created message queue: {config.queue_name}")

    async def publish(
        self,
        queue: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        message_id: Optional[str] = None,
        ttl: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Publish a message to the queue.

        Args:
            queue: Queue name
            payload: Message payload
            priority: Message priority
            message_id: Optional message ID
            ttl: Time to live in seconds
            metadata: Additional metadata

        Returns:
            Message ID
        """
        if not self.redis:
            await self.initialize()

        config = self.queue_configs.get(queue, self.default_config)
        message_id = message_id or f"{queue}:{int(time.time() * 1000000)}"

        message = Message(
            id=message_id,
            queue=queue,
            payload=payload,
            priority=priority,
            ttl=ttl or config.message_ttl,
            metadata=metadata or {},
        )

        try:
            # Serialize message
            message_data = {
                "id": message.id,
                "queue": message.queue,
                "payload": message.payload,
                "priority": message.priority.value,
                "status": message.status.value,
                "created_at": message.created_at,
                "retry_count": message.retry_count,
                "max_retries": message.max_retries,
                "ttl": message.ttl,
                "metadata": message.metadata,
            }

            # Store in Redis
            message_key = f"msg:{queue}:{message_id}"

            # Set TTL if specified
            if message.ttl:
                await self.redis.setex(message_key, int(message.ttl), json.dumps(message_data))

                # Add to sorted set with score as expiration time
                await self.redis.zadd(
                    f"queue:{queue}:pending",
                    {message_id: time.time() + message.ttl}
                )
            else:
                await self.redis.set(message_key, json.dumps(message_data))
                await self.redis.zadd(f"queue:{queue}:pending", {message_id: time.time()})

            # Add to priority queue
            priority_score = self._get_priority_score(priority)
            await self.redis.zadd(
                f"queue:{queue}:priority",
                {message_id: priority_score}
            )

            self._stats["messages_published"] += 1

            logger.debug(f"Published message to queue {queue}: {message_id}")

            return message_id

        except Exception as e:
            logger.error(f"Failed to publish message to queue {queue}: {e}")
            raise

    async def consume(
        self,
        queue: str,
        batch_size: int = 10,
        timeout: float = 10.0,
    ) -> List[Message]:
        """Consume messages from the queue.

        Args:
            queue: Queue name
            batch_size: Number of messages to consume
            timeout: Timeout in seconds

        Returns:
            List of messages
        """
        if not self.redis:
            await self.initialize()

        config = self.queue_configs.get(queue, self.default_config)
        batch_size = min(batch_size, config.batch_size)

        try:
            # Get message IDs from priority queue
            now = time.time()
            message_ids = await self.redis.zrangebyscore(
                f"queue:{queue}:priority",
                -float("inf"),
                now,
                start=0,
                num=batch_size
            )

            if not message_ids:
                await asyncio.sleep(timeout)
                return []

            messages = []
            pipeline = self.redis.pipeline()

            for message_id in message_ids:
                # Mark as processing
                pipeline.zrem(f"queue:{queue}:priority", message_id)
                pipeline.zadd(f"queue:{queue}:processing", {message_id: now})

            results = await pipeline.execute()

            # Retrieve message data
            for message_id in message_ids:
                message_key = f"msg:{queue}:{message_id}"
                message_data = await self.redis.get(message_key)

                if message_data:
                    data = json.loads(message_data)
                    message = Message(
                        id=data["id"],
                        queue=data["queue"],
                        payload=data["payload"],
                        priority=MessagePriority(data["priority"]),
                        status=MessageStatus(data["status"]),
                        created_at=data["created_at"],
                        retry_count=data["retry_count"],
                        max_retries=data["max_retries"],
                        ttl=data.get("ttl"),
                        metadata=data.get("metadata", {}),
                    )
                    messages.append(message)
                    self._stats["messages_consumed"] += 1

            logger.debug(f"Consumed {len(messages)} messages from queue {queue}")

            return messages

        except Exception as e:
            logger.error(f"Failed to consume messages from queue {queue}: {e}")
            raise

    async def acknowledge(self, queue: str, message_id: str, success: bool = True):
        """Acknowledge message processing.

        Args:
            queue: Queue name
            message_id: Message ID
            success: Whether processing was successful
        """
        if not self.redis:
            await self.initialize()

        try:
            message_key = f"msg:{queue}:{message_id}"

            if success:
                # Mark as completed
                await self.redis.zrem(f"queue:{queue}:processing", message_id)
                await self.redis.delete(message_key)

                # Update message status if exists
                message_data = await self.redis.get(message_key)
                if message_data:
                    data = json.loads(message_data)
                    data["status"] = MessageStatus.COMPLETED.value
                    data["processed_at"] = time.time()
                    await self.redis.setex(message_key, 300, json.dumps(data))  # Keep for 5 minutes

                logger.debug(f"Acknowledged message {message_id} from queue {queue}")

            else:
                # Handle failure
                await self.handle_message_failure(queue, message_id)

        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")

    async def handle_message_failure(self, queue: str, message_id: str):
        """Handle message processing failure.

        Args:
            queue: Queue name
            message_id: Message ID
        """
        if not self.redis:
            await self.initialize()

        config = self.queue_configs.get(queue, self.default_config)

        try:
            message_key = f"msg:{queue}:{message_id}"
            message_data = await self.redis.get(message_key)

            if not message_data:
                return

            data = json.loads(message_data)
            data["retry_count"] += 1

            if data["retry_count"] >= data["max_retries"]:
                # Max retries reached, move to dead letter queue
                data["status"] = MessageStatus.DEAD_LETTER.value
                await self.redis.zrem(f"queue:{queue}:processing", message_id)
                await self.redis.zadd(f"queue:{queue}:dead_letter", {message_id: time.time()})
                self._stats["messages_failed"] += 1

                logger.warning(f"Message {message_id} moved to dead letter queue")
            else:
                # Retry with delay
                data["status"] = MessageStatus.RETRY.value
                retry_delay = config.retry_delay * (2 ** data["retry_count"])  # Exponential backoff
                await self.redis.zrem(f"queue:{queue}:processing", message_id)
                await self.redis.zadd(
                    f"queue:{queue}:priority",
                    {message_id: time.time() + retry_delay}
                )
                self._stats["messages_retried"] += 1

                logger.info(f"Message {message_id} scheduled for retry in {retry_delay}s")

            # Update message data
            await self.redis.setex(message_key, int(config.message_ttl), json.dumps(data))

        except Exception as e:
            logger.error(f"Failed to handle message failure {message_id}: {e}")

    async def get_queue_stats(self, queue: str) -> Dict[str, Any]:
        """Get queue statistics.

        Args:
            queue: Queue name

        Returns:
            Queue statistics
        """
        if not self.redis:
            await self.initialize()

        try:
            stats = {
                "pending": await self.redis.zcard(f"queue:{queue}:pending"),
                "processing": await self.redis.zcard(f"queue:{queue}:processing"),
                "dead_letter": await self.redis.zcard(f"queue:{queue}:dead_letter"),
            }

            # Get oldest pending message
            oldest = await self.redis.zrange(f"queue:{queue}:pending", 0, 0, withscores=True)
            if oldest:
                stats["oldest_pending_age"] = time.time() - oldest[0][1]
            else:
                stats["oldest_pending_age"] = 0

            return stats

        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue}: {e}")
            raise

    async def cleanup_expired_messages(self, queue: str):
        """Clean up expired messages from queue.

        Args:
            queue: Queue name
        """
        if not self.redis:
            await self.initialize()

        try:
            now = time.time()

            # Remove expired messages
            expired_ids = await self.redis.zrangebyscore(
                f"queue:{queue}:pending",
                0,
                now
            )

            if expired_ids:
                pipeline = self.redis.pipeline()
                for message_id in expired_ids:
                    pipeline.delete(f"msg:{queue}:{message_id}")
                    pipeline.zrem(f"queue:{queue}:pending", message_id)

                await pipeline.execute()

                logger.info(f"Cleaned up {len(expired_ids)} expired messages from queue {queue}")

        except Exception as e:
            logger.error(f"Failed to cleanup expired messages from queue {queue}: {e}")

    async def get_overall_stats(self) -> Dict[str, Any]:
        """Get overall queue statistics.

        Returns:
            Overall statistics
        """
        with self._lock:
            return {
                **self._stats,
                "active_queues": len(self.queue_configs),
                "queue_configs": {
                    name: {
                        "max_size": config.max_size,
                        "message_ttl": config.message_ttl,
                        "max_retries": config.max_retries,
                    }
                    for name, config in self.queue_configs.items()
                },
            }

    def _get_priority_score(self, priority: MessagePriority) -> float:
        """Get priority score for message.

        Args:
            priority: Message priority

        Returns:
            Priority score (lower = higher priority)
        """
        priority_scores = {
            MessagePriority.CRITICAL: -1000,
            MessagePriority.HIGH: -500,
            MessagePriority.NORMAL: 0,
            MessagePriority.LOW: 500,
        }
        return priority_scores.get(priority, 0)

    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis message queue closed")


class MessageQueueManager:
    """Manager for multiple message queues."""

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize message queue manager.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self.queues: Dict[str, RedisMessageQueue] = {}

    async def create_queue(self, name: str, config: QueueConfig) -> RedisMessageQueue:
        """Create a new message queue.

        Args:
            name: Queue name
            config: Queue configuration

        Returns:
            RedisMessageQueue instance
        """
        queue = RedisMessageQueue(self.redis_url, config)
        await queue.initialize()
        await queue.create_queue(config)
        self.queues[name] = queue

        logger.info(f"Created message queue manager for {name}")
        return queue

    def get_queue(self, name: str) -> Optional[RedisMessageQueue]:
        """Get queue by name.

        Args:
            name: Queue name

        Returns:
            RedisMessageQueue instance or None
        """
        return self.queues.get(name)

    async def close_all(self):
        """Close all queues."""
        for queue in self.queues.values():
            await queue.close()

        logger.info("Closed all message queues")


# Global message queue manager
message_queue_manager = MessageQueueManager()
