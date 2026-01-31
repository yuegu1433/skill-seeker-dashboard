"""Performance configuration for progress tracking system.

This module provides optimized configuration settings for various
deployment scenarios based on performance testing results.
"""

from dataclasses import dataclass
from typing import Dict, Any
from enum import Enum


class DeploymentEnvironment(Enum):
    """Deployment environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LoadProfile(Enum):
    """System load profiles."""
    LOW = "low"        # < 100 concurrent connections
    MEDIUM = "medium"  # 100-500 concurrent connections
    HIGH = "high"      # 500-1000 concurrent connections
    EXTREME = "extreme"  # > 1000 concurrent connections


@dataclass
class WebSocketConfig:
    """WebSocket performance configuration."""
    max_connections: int
    heartbeat_interval: float
    connection_timeout: float
    max_message_size: int
    enable_compression: bool
    buffer_size: int


@dataclass
class ConnectionPoolConfig:
    """Connection pool performance configuration."""
    max_connections: int
    max_connections_per_user: int
    max_connections_per_task: int
    min_idle_connections: int
    max_idle_connections: int
    connection_timeout: float
    heartbeat_interval: float
    cleanup_interval: float
    max_message_queue_size: int
    memory_limit_mb: float
    cpu_threshold: float
    enable_auto_scaling: bool
    scale_up_threshold: float
    scale_down_threshold: float
    health_check_interval: float


@dataclass
class CacheConfig:
    """Cache performance configuration."""
    max_size: int
    max_memory_mb: float
    strategy: str  # LRU, LFU, FIFO, TTL
    default_ttl: float
    enable_compression: bool
    compression_threshold: int
    enable_persistence: bool
    persistence_path: str


@dataclass
class MessageQueueConfig:
    """Message queue performance configuration."""
    redis_url: str
    max_size: int
    batch_size: int
    max_workers: int
    enable_persistence: bool
    persistence_interval: float
    enable_compression: bool
    compression_threshold: int
    max_retries: int
    retry_delay: float


@dataclass
class DatabaseConfig:
    """Database performance configuration."""
    pool_size: int
    max_overflow: int
    pool_timeout: float
    pool_recycle: int
    enable_query_cache: bool
    query_cache_size: int
    enable_connection_pooling: bool
    connection_pool_max_size: int
    connection_pool_min_size: int


@dataclass
class PerformanceThresholds:
    """Performance monitoring thresholds."""
    cpu_percent_warning: float
    cpu_percent_critical: float
    memory_mb_warning: float
    memory_mb_critical: float
    latency_ms_warning: float
    latency_ms_critical: float
    error_rate_warning: float
    error_rate_critical: float
    connections_warning: int
    connections_critical: int
    queue_size_warning: int
    queue_size_critical: int


@dataclass
class PerformanceConfig:
    """Complete performance configuration."""
    environment: DeploymentEnvironment
    load_profile: LoadProfile
    websocket: WebSocketConfig
    connection_pool: ConnectionPoolConfig
    cache: CacheConfig
    message_queue: MessageQueueConfig
    database: DatabaseConfig
    thresholds: PerformanceThresholds

    @classmethod
    def for_environment(
        cls,
        environment: DeploymentEnvironment,
        load_profile: LoadProfile,
    ) -> "PerformanceConfig":
        """Create configuration for specific environment and load.

        Args:
            environment: Deployment environment
            load_profile: Expected load level

        Returns:
            PerformanceConfig instance
        """
        config_map = {
            (DeploymentEnvironment.DEVELOPMENT, LoadProfile.LOW): cls._dev_low,
            (DeploymentEnvironment.DEVELOPMENT, LoadProfile.MEDIUM): cls._dev_medium,
            (DeploymentEnvironment.TESTING, LoadProfile.LOW): cls._test_low,
            (DeploymentEnvironment.TESTING, LoadProfile.MEDIUM): cls._test_medium,
            (DeploymentEnvironment.PRODUCTION, LoadProfile.LOW): cls._prod_low,
            (DeploymentEnvironment.PRODUCTION, LoadProfile.MEDIUM): cls._prod_medium,
            (DeploymentEnvironment.PRODUCTION, LoadProfile.HIGH): cls._prod_high,
            (DeploymentEnvironment.PRODUCTION, LoadProfile.EXTREME): cls._prod_extreme,
        }

        return config_map.get(
            (environment, load_profile),
            cls._prod_medium()
        )

    @classmethod
    def _dev_low(cls) -> "PerformanceConfig":
        """Development environment, low load."""
        return cls(
            environment=DeploymentEnvironment.DEVELOPMENT,
            load_profile=LoadProfile.LOW,
            websocket=WebSocketConfig(
                max_connections=50,
                heartbeat_interval=60.0,
                connection_timeout=300.0,
                max_message_size=1024 * 1024,
                enable_compression=False,
                buffer_size=8192,
            ),
            connection_pool=ConnectionPoolConfig(
                max_connections=50,
                max_connections_per_user=5,
                max_connections_per_task=3,
                min_idle_connections=5,
                max_idle_connections=20,
                connection_timeout=300.0,
                heartbeat_interval=60.0,
                cleanup_interval=120.0,
                max_message_queue_size=500,
                memory_limit_mb=256.0,
                cpu_threshold=70.0,
                enable_auto_scaling=False,
                scale_up_threshold=0.8,
                scale_down_threshold=0.3,
                health_check_interval=30.0,
            ),
            cache=CacheConfig(
                max_size=100,
                max_memory_mb=64.0,
                strategy="LRU",
                default_ttl=300.0,
                enable_compression=False,
                compression_threshold=1024,
                enable_persistence=False,
                persistence_path="",
            ),
            message_queue=MessageQueueConfig(
                redis_url="redis://localhost:6379/0",
                max_size=1000,
                batch_size=10,
                max_workers=2,
                enable_persistence=False,
                persistence_interval=60.0,
                enable_compression=False,
                compression_threshold=1024,
                max_retries=3,
                retry_delay=1.0,
            ),
            database=DatabaseConfig(
                pool_size=5,
                max_overflow=10,
                pool_timeout=30.0,
                pool_recycle=3600,
                enable_query_cache=False,
                query_cache_size=100,
                enable_connection_pooling=True,
                connection_pool_max_size=10,
                connection_pool_min_size=1,
            ),
            thresholds=PerformanceThresholds(
                cpu_percent_warning=60.0,
                cpu_percent_critical=80.0,
                memory_mb_warning=200.0,
                memory_mb_critical=400.0,
                latency_ms_warning=50.0,
                latency_ms_critical=100.0,
                error_rate_warning=0.01,
                error_rate_critical=0.05,
                connections_warning=40,
                connections_critical=45,
                queue_size_warning=800,
                queue_size_critical=950,
            ),
        )

    @classmethod
    def _dev_medium(cls) -> "PerformanceConfig":
        """Development environment, medium load."""
        config = cls._dev_low()
        config.websocket.max_connections = 100
        config.connection_pool.max_connections = 100
        config.cache.max_size = 500
        config.cache.max_memory_mb = 128.0
        config.message_queue.max_size = 5000
        config.message_queue.batch_size = 50
        return config

    @classmethod
    def _test_low(cls) -> "PerformanceConfig":
        """Testing environment, low load."""
        return cls(
            environment=DeploymentEnvironment.TESTING,
            load_profile=LoadProfile.LOW,
            websocket=WebSocketConfig(
                max_connections=100,
                heartbeat_interval=30.0,
                connection_timeout=300.0,
                max_message_size=1024 * 1024,
                enable_compression=True,
                buffer_size=8192,
            ),
            connection_pool=ConnectionPoolConfig(
                max_connections=100,
                max_connections_per_user=10,
                max_connections_per_task=5,
                min_idle_connections=10,
                max_idle_connections=30,
                connection_timeout=300.0,
                heartbeat_interval=30.0,
                cleanup_interval=60.0,
                max_message_queue_size=1000,
                memory_limit_mb=512.0,
                cpu_threshold=70.0,
                enable_auto_scaling=True,
                scale_up_threshold=0.7,
                scale_down_threshold=0.3,
                health_check_interval=15.0,
            ),
            cache=CacheConfig(
                max_size=500,
                max_memory_mb=128.0,
                strategy="LRU",
                default_ttl=600.0,
                enable_compression=True,
                compression_threshold=512,
                enable_persistence=False,
                persistence_path="",
            ),
            message_queue=MessageQueueConfig(
                redis_url="redis://localhost:6379/1",
                max_size=5000,
                batch_size=50,
                max_workers=4,
                enable_persistence=True,
                persistence_interval=30.0,
                enable_compression=True,
                compression_threshold=512,
                max_retries=3,
                retry_delay=1.0,
            ),
            database=DatabaseConfig(
                pool_size=10,
                max_overflow=20,
                pool_timeout=30.0,
                pool_recycle=3600,
                enable_query_cache=True,
                query_cache_size=200,
                enable_connection_pooling=True,
                connection_pool_max_size=20,
                connection_pool_min_size=5,
            ),
            thresholds=PerformanceThresholds(
                cpu_percent_warning=65.0,
                cpu_percent_critical=85.0,
                memory_mb_warning=400.0,
                memory_mb_critical=600.0,
                latency_ms_warning=50.0,
                latency_ms_critical=100.0,
                error_rate_warning=0.01,
                error_rate_critical=0.05,
                connections_warning=80,
                connections_critical=95,
                queue_size_warning=4000,
                queue_size_critical=4800,
            ),
        )

    @classmethod
    def _test_medium(cls) -> "PerformanceConfig":
        """Testing environment, medium load."""
        config = cls._test_low()
        config.websocket.max_connections = 300
        config.connection_pool.max_connections = 300
        config.cache.max_size = 1000
        config.cache.max_memory_mb = 256.0
        config.message_queue.max_size = 10000
        config.message_queue.batch_size = 100
        return config

    @classmethod
    def _prod_low(cls) -> "PerformanceConfig":
        """Production environment, low load."""
        return cls(
            environment=DeploymentEnvironment.PRODUCTION,
            load_profile=LoadProfile.LOW,
            websocket=WebSocketConfig(
                max_connections=300,
                heartbeat_interval=30.0,
                connection_timeout=300.0,
                max_message_size=4 * 1024 * 1024,
                enable_compression=True,
                buffer_size=16384,
            ),
            connection_pool=ConnectionPoolConfig(
                max_connections=300,
                max_connections_per_user=20,
                max_connections_per_task=10,
                min_idle_connections=30,
                max_idle_connections=100,
                connection_timeout=300.0,
                heartbeat_interval=30.0,
                cleanup_interval=60.0,
                max_message_queue_size=2000,
                memory_limit_mb=1024.0,
                cpu_threshold=75.0,
                enable_auto_scaling=True,
                scale_up_threshold=0.7,
                scale_down_threshold=0.3,
                health_check_interval=10.0,
            ),
            cache=CacheConfig(
                max_size=1000,
                max_memory_mb=512.0,
                strategy="LRU",
                default_ttl=3600.0,
                enable_compression=True,
                compression_threshold=1024,
                enable_persistence=True,
                persistence_path="/var/lib/progress/cache",
            ),
            message_queue=MessageQueueConfig(
                redis_url="redis://localhost:6379/2",
                max_size=10000,
                batch_size=100,
                max_workers=8,
                enable_persistence=True,
                persistence_interval=30.0,
                enable_compression=True,
                compression_threshold=1024,
                max_retries=5,
                retry_delay=2.0,
            ),
            database=DatabaseConfig(
                pool_size=20,
                max_overflow=40,
                pool_timeout=30.0,
                pool_recycle=3600,
                enable_query_cache=True,
                query_cache_size=500,
                enable_connection_pooling=True,
                connection_pool_max_size=50,
                connection_pool_min_size=10,
            ),
            thresholds=PerformanceThresholds(
                cpu_percent_warning=70.0,
                cpu_percent_critical=85.0,
                memory_mb_warning=800.0,
                memory_mb_critical=1200.0,
                latency_ms_warning=50.0,
                latency_ms_critical=100.0,
                error_rate_warning=0.005,
                error_rate_critical=0.02,
                connections_warning=250,
                connections_critical=290,
                queue_size_warning=8000,
                queue_size_critical=9500,
            ),
        )

    @classmethod
    def _prod_medium(cls) -> "PerformanceConfig":
        """Production environment, medium load."""
        config = cls._prod_low()
        config.websocket.max_connections = 500
        config.connection_pool.max_connections = 500
        config.cache.max_size = 5000
        config.cache.max_memory_mb = 1024.0
        config.message_queue.max_size = 50000
        config.message_queue.batch_size = 200
        config.database.pool_size = 30
        config.database.max_overflow = 60
        config.thresholds.connections_warning = 400
        config.thresholds.connections_critical = 480
        return config

    @classmethod
    def _prod_high(cls) -> "PerformanceConfig":
        """Production environment, high load."""
        config = cls._prod_medium()
        config.websocket.max_connections = 800
        config.connection_pool.max_connections = 800
        config.cache.max_size = 10000
        config.cache.max_memory_mb = 2048.0
        config.message_queue.max_size = 100000
        config.message_queue.batch_size = 500
        config.message_queue.max_workers = 16
        config.database.pool_size = 50
        config.database.max_overflow = 100
        config.thresholds.connections_warning = 700
        config.thresholds.connections_critical = 780
        config.thresholds.queue_size_warning = 80000
        config.thresholds.queue_size_critical = 95000
        return config

    @classmethod
    def _prod_extreme(cls) -> "PerformanceConfig":
        """Production environment, extreme load."""
        config = cls._prod_high()
        config.websocket.max_connections = 1500
        config.connection_pool.max_connections = 1500
        config.connection_pool.min_idle_connections = 100
        config.connection_pool.max_idle_connections = 500
        config.cache.max_size = 20000
        config.cache.max_memory_mb = 4096.0
        config.message_queue.max_size = 200000
        config.message_queue.batch_size = 1000
        config.message_queue.max_workers = 32
        config.database.pool_size = 100
        config.database.max_overflow = 200
        config.thresholds.connections_warning = 1200
        config.thresholds.connections_critical = 1450
        config.thresholds.queue_size_warning = 150000
        config.thresholds.queue_size_critical = 190000
        return config

    def get_optimization_tips(self) -> Dict[str, Any]:
        """Get performance optimization tips for this configuration.

        Returns:
            Dictionary of optimization tips
        """
        tips = {
            "websocket": [],
            "connection_pool": [],
            "cache": [],
            "message_queue": [],
            "database": [],
            "general": [],
        }

        # WebSocket tips
        if self.websocket.enable_compression:
            tips["websocket"].append(
                "Compression enabled for large messages (>8KB)"
            )
        else:
            tips["websocket"].append(
                "Consider enabling compression for better bandwidth utilization"
            )

        if self.websocket.max_connections > 500:
            tips["websocket"].append(
                "High connection limit - ensure adequate system resources"
            )

        # Connection pool tips
        if self.connection_pool.enable_auto_scaling:
            tips["connection_pool"].append(
                "Auto-scaling enabled - monitor scaling events"
            )

        if self.connection_pool.max_connections > 1000:
            tips["connection_pool"].append(
                "Extreme connection load - consider load balancing"
            )

        # Cache tips
        if self.cache.enable_persistence:
            tips["cache"].append(
                "Cache persistence enabled - ensure adequate disk space"
            )

        if self.cache.max_memory_mb > 1024:
            tips["cache"].append(
                "Large cache size - monitor memory usage"
            )

        # Message queue tips
        if self.message_queue.batch_size > 500:
            tips["message_queue"].append(
                "Large batch size - may increase latency but improves throughput"
            )

        if self.message_queue.max_workers > 16:
            tips["message_queue"].append(
                "High worker count - ensure CPU resources are adequate"
            )

        # Database tips
        if self.database.pool_size > 50:
            tips["database"].append(
                "Large connection pool - ensure database can handle load"
            )

        if self.database.enable_query_cache:
            tips["database"].append(
                "Query caching enabled - monitor cache hit rates"
            )

        # General tips
        tips["general"].append(
            f"Optimized for {self.load_profile.value} load in {self.environment.value} environment"
        )

        if self.load_profile in [LoadProfile.HIGH, LoadProfile.EXTREME]:
            tips["general"].append(
                "High load configuration - ensure robust monitoring and alerting"
            )
            tips["general"].append(
                "Consider horizontal scaling for additional capacity"
            )

        return tips

    def apply_optimizations(self) -> Dict[str, Any]:
        """Apply performance optimizations to system.

        Returns:
            Dictionary of applied optimizations
        """
        optimizations = {
            "websocket": {
                "max_connections": self.websocket.max_connections,
                "heartbeat_interval": self.websocket.heartbeat_interval,
                "enable_compression": self.websocket.enable_compression,
            },
            "connection_pool": {
                "max_connections": self.connection_pool.max_connections,
                "auto_scaling": self.connection_pool.enable_auto_scaling,
                "cleanup_interval": self.connection_pool.cleanup_interval,
            },
            "cache": {
                "max_size": self.cache.max_size,
                "max_memory_mb": self.cache.max_memory_mb,
                "strategy": self.cache.strategy,
            },
            "message_queue": {
                "max_size": self.message_queue.max_size,
                "batch_size": self.message_queue.batch_size,
                "max_workers": self.message_queue.max_workers,
            },
            "database": {
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow,
                "query_cache": self.database.enable_query_cache,
            },
        }

        return optimizations


# Predefined configurations for common scenarios
DEVELOPMENT_LOW = PerformanceConfig.for_environment(
    DeploymentEnvironment.DEVELOPMENT,
    LoadProfile.LOW
)

TESTING_MEDIUM = PerformanceConfig.for_environment(
    DeploymentEnvironment.TESTING,
    LoadProfile.MEDIUM
)

PRODUCTION_HIGH = PerformanceConfig.for_environment(
    DeploymentEnvironment.PRODUCTION,
    LoadProfile.HIGH
)

PRODUCTION_EXTREME = PerformanceConfig.for_environment(
    DeploymentEnvironment.PRODUCTION,
    LoadProfile.EXTREME
)
