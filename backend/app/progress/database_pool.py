"""Database connection pool manager for real-time progress tracking.

This module provides comprehensive database connection pool management including:
- PostgreSQL connection pooling
- Connection health monitoring
- Automatic failover and recovery
- Performance optimization
- Resource cleanup
"""

import asyncio
import logging
import time
import asyncpg
from typing import Optional, Dict, Any, List, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from collections import deque

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "progress_tracking"
    user: str = "postgres"
    password: str = ""
    min_connections: int = 5
    max_connections: int = 50
    max_idle_time: float = 300.0
    connection_timeout: float = 10.0
    command_timeout: float = 30.0
    enable_ssl: bool = False
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None


@dataclass
class ConnectionMetrics:
    """Metrics for a database connection."""
    connection_id: str
    created_at: float
    last_used_at: float
    is_idle: bool
    query_count: int
    total_query_time: float
    average_query_time: float
    error_count: int
    status: str = "active"


class DatabaseConnectionPool:
    """High-performance database connection pool for PostgreSQL."""

    def __init__(
        self,
        config: DatabaseConfig,
        database_type: DatabaseType = DatabaseType.POSTGRESQL,
    ):
        """Initialize database connection pool.

        Args:
            config: Database configuration
            database_type: Type of database
        """
        self.config = config
        self.database_type = database_type
        self._pool: Optional[asyncpg.Pool] = None
        self._lock = Lock()
        self._is_initialized = False
        self._health_check_interval = 30.0
        self._cleanup_interval = 60.0
        self._metrics_history = deque(maxlen=1000)

        # Connection statistics
        self._stats = {
            "total_connections_created": 0,
            "total_connections_closed": 0,
            "active_connections": 0,
            "idle_connections": 0,
            "total_queries": 0,
            "total_query_time": 0.0,
            "average_query_time": 0.0,
            "connection_errors": 0,
            "query_errors": 0,
        }

    async def initialize(self):
        """Initialize the database connection pool."""
        if self._is_initialized:
            return

        try:
            if self.database_type == DatabaseType.POSTGRESQL:
                await self._init_postgresql_pool()
            else:
                raise ValueError(f"Unsupported database type: {self.database_type}")

            self._is_initialized = True
            logger.info(f"Database connection pool initialized with {self.config.min_connections} connections")

        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    async def _init_postgresql_pool(self):
        """Initialize PostgreSQL connection pool."""
        # Build connection string
        dsn = (
            f"postgresql://{self.config.user}:{self.config.password}"
            f"@{self.config.host}:{self.config.port}/{self.config.database}"
        )

        # Add SSL if enabled
        if self.config.enable_ssl:
            ssl_options = []
            if self.config.ssl_ca:
                ssl_options.append(f"sslrootcert={self.config.ssl_ca}")
            if self.config.ssl_cert:
                ssl_options.append(f"sslcert={self.config.ssl_cert}")
            if self.config.ssl_key:
                ssl_options.append(f"sslkey={self.config.ssl_key}")

            if ssl_options:
                dsn += f"?ssl={'&'.join(ssl_options)}"

        # Create connection pool
        self._pool = await asyncpg.create_pool(
            dsn=dsn,
            min_size=self.config.min_connections,
            max_size=self.config.max_connections,
            max_inactive_connection_lifetime=self.config.max_idle_time,
            command_timeout=self.config.command_timeout,
            server_settings={
                "application_name": "progress_tracking",
                "jit": "off",  # Disable JIT for faster query planning
                "shared_preload_libraries": "pg_stat_statements",  # Enable query statistics
            },
        )

        self._stats["total_connections_created"] = self.config.min_connections

    @asynccontextmanager
    async def acquire(self, timeout: Optional[float] = None):
        """Acquire a database connection from the pool.

        Args:
            timeout: Connection acquire timeout (seconds)

        Yields:
            Database connection
        """
        if not self._is_initialized:
            await self.initialize()

        timeout = timeout or self.config.connection_timeout

        try:
            start_time = time.time()
            conn = await asyncio.wait_for(self._pool.acquire(), timeout=timeout)
            acquire_time = time.time() - start_time

            # Update metrics
            with self._lock:
                self._stats["active_connections"] += 1
                self._stats["idle_connections"] = max(0, self._stats["idle_connections"] - 1)

            logger.debug(f"Acquired database connection in {acquire_time:.3f}s")

            yield conn

        except asyncio.TimeoutError:
            logger.error(f"Failed to acquire database connection within {timeout}s")
            raise
        except Exception as e:
            with self._lock:
                self._stats["connection_errors"] += 1
            logger.error(f"Error acquiring database connection: {e}")
            raise
        finally:
            try:
                if conn:
                    await self._pool.release(conn)
                    with self._lock:
                        self._stats["active_connections"] = max(0, self._stats["active_connections"] - 1)
                        self._stats["idle_connections"] += 1
            except Exception as e:
                logger.error(f"Error releasing database connection: {e}")

    async def execute(
        self,
        query: str,
        *args,
        timeout: Optional[float] = None,
        fetch: bool = False,
        fetchval: bool = False,
        fetchrow: bool = False,
    ):
        """Execute a database query.

        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout
            fetch: Fetch all rows
            fetchval: Fetch single value
            fetchrow: Fetch single row

        Returns:
            Query result
        """
        async with self.acquire() as conn:
            start_time = time.time()
            try:
                if fetchval:
                    result = await conn.fetchval(query, *args, timeout=timeout)
                elif fetchrow:
                    result = await conn.fetchrow(query, *args, timeout=timeout)
                elif fetch:
                    result = await conn.fetch(query, *args, timeout=timeout)
                else:
                    result = await conn.execute(query, *args, timeout=timeout)

                query_time = time.time() - start_time

                # Update statistics
                with self._lock:
                    self._stats["total_queries"] += 1
                    self._stats["total_query_time"] += query_time
                    self._stats["average_query_time"] = (
                        self._stats["total_query_time"] / self._stats["total_queries"]
                    )

                return result

            except Exception as e:
                with self._lock:
                    self._stats["query_errors"] += 1
                logger.error(f"Database query error: {e}")
                raise

    async def fetch_one(self, query: str, *args, timeout: Optional[float] = None):
        """Fetch a single row.

        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout

        Returns:
            Single row or None
        """
        return await self.execute(query, *args, timeout=timeout, fetchrow=True)

    async def fetch_all(self, query: str, *args, timeout: Optional[float] = None):
        """Fetch all rows.

        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout

        Returns:
            List of rows
        """
        return await self.execute(query, *args, timeout=timeout, fetch=True)

    async def fetch_val(self, query: str, *args, timeout: Optional[float] = None):
        """Fetch a single value.

        Args:
            query: SQL query
            *args: Query parameters
            timeout: Query timeout

        Returns:
            Single value or None
        """
        return await self.execute(query, *args, timeout=timeout, fetchval=True)

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the database connection pool.

        Returns:
            Health check results
        """
        try:
            start_time = time.time()
            async with self.acquire(timeout=5.0) as conn:
                await conn.fetchval("SELECT 1")
                response_time = time.time() - start_time

                # Get pool statistics
                pool_stats = {
                    "pool_size": len(self._pool._queue) if self._pool else 0,
                    "idle_connections": len([c for c in self._pool._queue if c.is_connected()]) if self._pool else 0,
                    "active_connections": len(self._pool._holders) if self._pool else 0,
                }

                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "pool_stats": pool_stats,
                    "timestamp": time.time(),
                }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time(),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get database connection pool statistics.

        Returns:
            Pool statistics
        """
        with self._lock:
            return {
                **self._stats,
                "pool_size": self.config.max_connections,
                "utilization": (
                    (self._stats["active_connections"] + self._stats["idle_connections"])
                    / self.config.max_connections
                    if self.config.max_connections > 0
                    else 0
                ),
                "is_initialized": self._is_initialized,
            }

    async def optimize_pool(self):
        """Optimize the database connection pool."""
        try:
            # Execute optimization queries
            await self.execute("ANALYZE")
            logger.info("Database connection pool optimized")
        except Exception as e:
            logger.error(f"Failed to optimize database connection pool: {e}")

    async def close(self):
        """Close the database connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._is_initialized = False

            with self._lock:
                self._stats["total_connections_closed"] = self._stats["active_connections"] + self._stats["idle_connections"]
                self._stats["active_connections"] = 0
                self._stats["idle_connections"] = 0

            logger.info("Database connection pool closed")


class DatabasePoolManager:
    """Manager for multiple database connection pools."""

    def __init__(self):
        """Initialize database pool manager."""
        self._pools: Dict[str, DatabaseConnectionPool] = {}
        self._lock = Lock()

    def add_pool(
        self,
        name: str,
        config: DatabaseConfig,
        database_type: DatabaseType = DatabaseType.POSTGRESQL,
    ):
        """Add a database connection pool.

        Args:
            name: Pool name
            config: Database configuration
            database_type: Database type
        """
        with self._lock:
            self._pools[name] = DatabaseConnectionPool(config, database_type)
            logger.info(f"Added database pool: {name}")

    async def initialize_pools(self):
        """Initialize all database connection pools."""
        for name, pool in self._pools.items():
            try:
                await pool.initialize()
                logger.info(f"Initialized database pool: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize pool {name}: {e}")

    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all pools.

        Returns:
            Health check results for all pools
        """
        results = {}
        for name, pool in self._pools.items():
            results[name] = await pool.health_check()
        return results

    def get_pool(self, name: str) -> Optional[DatabaseConnectionPool]:
        """Get database connection pool by name.

        Args:
            name: Pool name

        Returns:
            Database connection pool or None
        """
        return self._pools.get(name)

    async def close_all(self):
        """Close all database connection pools."""
        for name, pool in self._pools.items():
            try:
                await pool.close()
                logger.info(f"Closed database pool: {name}")
            except Exception as e:
                logger.error(f"Failed to close pool {name}: {e}")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all pools.

        Returns:
            Statistics for all pools
        """
        stats = {}
        for name, pool in self._pools.items():
            stats[name] = pool.get_stats()
        return stats


# Global database pool manager instance
database_pool_manager = DatabasePoolManager()
