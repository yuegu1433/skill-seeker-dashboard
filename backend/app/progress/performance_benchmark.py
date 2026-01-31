"""Performance benchmarking system for real-time progress tracking.

This module provides comprehensive performance testing including:
- API performance benchmarks
- WebSocket performance tests
- Database query benchmarks
- Memory usage tests
- Throughput measurements
"""

import asyncio
import time
import statistics
import logging
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil
import gc

logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of performance benchmarks."""
    API_LATENCY = "api_latency"
    API_THROUGHPUT = "api_throughput"
    WEBSOCKET_CONNECTIONS = "websocket_connections"
    WEBSOCKET_MESSAGES = "websocket_messages"
    DATABASE_QUERIES = "database_queries"
    MEMORY_USAGE = "memory_usage"
    CACHE_PERFORMANCE = "cache_performance"
    QUEUE_THROUGHPUT = "queue_throughput"


@dataclass
class BenchmarkResult:
    """Benchmark result data."""
    benchmark_type: BenchmarkType
    test_name: str
    duration_seconds: float
    operations_count: int
    operations_per_second: float
    latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    success_rate: float
    error_count: int
    memory_usage_mb: float
    cpu_usage_percent: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkConfig:
    """Benchmark configuration."""
    test_name: str
    duration_seconds: int
    concurrent_users: int
    warmup_seconds: int = 10
    cooldown_seconds: int = 5
    target_rps: Optional[float] = None
    max_errors: int = 100
    collect_detailed_metrics: bool = True


class PerformanceBenchmark:
    """Base class for performance benchmarks."""

    def __init__(self, config: BenchmarkConfig):
        """Initialize benchmark.

        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.results: List[BenchmarkResult] = []
        self._is_running = False

    async def run(self) -> BenchmarkResult:
        """Run the benchmark.

        Returns:
            Benchmark result
        """
        logger.info(f"Starting benchmark: {self.config.test_name}")

        # Start monitoring
        monitor_task = asyncio.create_task(self._monitor_resources())

        # Run benchmark
        result = await self._execute_benchmark()

        # Stop monitoring
        monitor_task.cancel()

        self.results.append(result)
        logger.info(f"Benchmark completed: {self.config.test_name}")

        return result

    async def _monitor_resources(self):
        """Monitor system resources during benchmark."""
        try:
            while True:
                # Collect resource metrics
                cpu_percent = psutil.cpu_percent()
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024

                # Log if high usage
                if cpu_percent > 80:
                    logger.warning(f"High CPU usage during benchmark: {cpu_percent:.1f}%")
                if memory_mb > 1024:
                    logger.warning(f"High memory usage during benchmark: {memory_mb:.1f} MB")

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            pass

    async def _execute_benchmark(self) -> BenchmarkResult:
        """Execute the actual benchmark.

        Returns:
            Benchmark result
        """
        raise NotImplementedError("Subclasses must implement _execute_benchmark")

    async def _measure_latency(self, func: Callable, *args, **kwargs) -> Tuple[float, Any]:
        """Measure function latency.

        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Tuple of (latency_ms, result)
        """
        start_time = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            latency_ms = (time.perf_counter() - start_time) * 1000
            return latency_ms, result
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            raise e


class APIBenchmark(PerformanceBenchmark):
    """API performance benchmark."""

    async def _execute_benchmark(self) -> BenchmarkResult:
        """Execute API benchmark.

        Returns:
            Benchmark result
        """
        # Placeholder API benchmark implementation
        # In a real implementation, this would make actual API calls

        latencies = []
        success_count = 0
        error_count = 0
        start_time = time.time()

        # Simulate API calls
        for _ in range(self.config.concurrent_users * 10):
            try:
                # Simulate API call
                await asyncio.sleep(0.01)  # Simulate network latency
                latency, _ = await self._measure_latency(self._simulate_api_call)
                latencies.append(latency)
                success_count += 1
            except Exception:
                error_count += 1

        end_time = time.time()
        duration = end_time - start_time

        return self._create_result(BenchmarkType.API_LATENCY, latencies, duration, success_count, error_count)

    async def _simulate_api_call(self):
        """Simulate an API call."""
        # Placeholder for actual API call
        await asyncio.sleep(0.001)


class WebSocketBenchmark(PerformanceBenchmark):
    """WebSocket performance benchmark."""

    async def _execute_benchmark(self) -> BenchmarkResult:
        """Execute WebSocket benchmark.

        Returns:
            Benchmark result
        """
        # Placeholder WebSocket benchmark
        # In a real implementation, this would test WebSocket connections

        latencies = []
        success_count = 0
        error_count = 0
        start_time = time.time()

        # Simulate WebSocket operations
        for _ in range(self.config.concurrent_users):
            try:
                # Simulate WebSocket connection
                await asyncio.sleep(0.1)
                latency, _ = await self._measure_latency(self._simulate_websocket_op)
                latencies.append(latency)
                success_count += 1
            except Exception:
                error_count += 1

        end_time = time.time()
        duration = end_time - start_time

        return self._create_result(BenchmarkType.WEBSOCKET_CONNECTIONS, latencies, duration, success_count, error_count)

    async def _simulate_websocket_op(self):
        """Simulate WebSocket operation."""
        # Placeholder for actual WebSocket operation
        await asyncio.sleep(0.001)


class DatabaseBenchmark(PerformanceBenchmark):
    """Database query performance benchmark."""

    async def _execute_benchmark(self) -> BenchmarkResult:
        """Execute database benchmark.

        Returns:
            Benchmark result
        """
        # Placeholder database benchmark
        # In a real implementation, this would test database queries

        latencies = []
        success_count = 0
        error_count = 0
        start_time = time.time()

        # Simulate database queries
        for _ in range(self.config.concurrent_users * 20):
            try:
                # Simulate database query
                await asyncio.sleep(0.005)
                latency, _ = await self._measure_latency(self._simulate_db_query)
                latencies.append(latency)
                success_count += 1
            except Exception:
                error_count += 1

        end_time = time.time()
        duration = end_time - start_time

        return self._create_result(BenchmarkType.DATABASE_QUERIES, latencies, duration, success_count, error_count)

    async def _simulate_db_query(self):
        """Simulate database query."""
        # Placeholder for actual database query
        await asyncio.sleep(0.001)


class CacheBenchmark(PerformanceBenchmark):
    """Cache performance benchmark."""

    async def _execute_benchmark(self) -> BenchmarkResult:
        """Execute cache benchmark.

        Returns:
            Benchmark result
        """
        # Placeholder cache benchmark
        # In a real implementation, this would test cache operations

        latencies = []
        success_count = 0
        error_count = 0
        start_time = time.time()

        # Simulate cache operations
        for _ in range(self.config.concurrent_users * 50):
            try:
                # Simulate cache operation
                await asyncio.sleep(0.0005)
                latency, _ = await self._measure_latency(self._simulate_cache_op)
                latencies.append(latency)
                success_count += 1
            except Exception:
                error_count += 1

        end_time = time.time()
        duration = end_time - start_time

        return self._create_result(BenchmarkType.CACHE_PERFORMANCE, latencies, duration, success_count, error_count)

    async def _simulate_cache_op(self):
        """Simulate cache operation."""
        # Placeholder for actual cache operation
        await asyncio.sleep(0.0001)


class BenchmarkSuite:
    """Suite of performance benchmarks."""

    def __init__(self):
        """Initialize benchmark suite."""
        self.benchmarks: List[PerformanceBenchmark] = []

    def add_benchmark(self, benchmark: PerformanceBenchmark):
        """Add benchmark to suite.

        Args:
            benchmark: Benchmark to add
        """
        self.benchmarks.append(benchmark)

    async def run_all(self) -> List[BenchmarkResult]:
        """Run all benchmarks.

        Returns:
            List of benchmark results
        """
        results = []

        for benchmark in self.benchmarks:
            try:
                result = await benchmark.run()
                results.append(result)
            except Exception as e:
                logger.error(f"Benchmark failed: {e}")

        return results

    async def run_load_test(
        self,
        config: BenchmarkConfig,
        test_duration: int = 60,
    ) -> Dict[str, Any]:
        """Run load test with specified configuration.

        Args:
            config: Benchmark configuration
            test_duration: Test duration in seconds

        Returns:
            Load test results
        """
        logger.info(f"Starting load test: {config.test_name}")

        # Initialize metrics
        metrics = {
            "start_time": time.time(),
            "end_time": None,
            "duration": test_duration,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0,
            "latencies": [],
            "errors": [],
            "rps_history": [],
        }

        start_time = time.time()
        end_time = start_time + test_duration

        # Run load test
        while time.time() < end_time:
            batch_start = time.time()

            # Run concurrent requests
            tasks = []
            for _ in range(config.concurrent_users):
                task = asyncio.create_task(self._simulate_request(metrics))
                tasks.append(task)

            await asyncio.gather(*tasks, return_exceptions=True)

            # Update metrics
            batch_duration = time.time() - batch_start
            metrics["rps_history"].append(config.concurrent_users / batch_duration)

            # Small delay between batches
            await asyncio.sleep(0.1)

        metrics["end_time"] = time.time()

        # Calculate statistics
        if metrics["latencies"]:
            metrics["avg_latency"] = statistics.mean(metrics["latencies"])
            metrics["p50_latency"] = statistics.median(metrics["latencies"])
            metrics["p95_latency"] = self._percentile(metrics["latencies"], 95)
            metrics["p99_latency"] = self._percentile(metrics["latencies"], 99)
            metrics["min_latency"] = min(metrics["latencies"])
            metrics["max_latency"] = max(metrics["latencies"])

        metrics["avg_rps"] = statistics.mean(metrics["rps_history"])
        metrics["success_rate"] = metrics["successful_requests"] / metrics["total_requests"]

        logger.info(f"Load test completed: {config.test_name}")
        return metrics

    async def _simulate_request(self, metrics: Dict[str, Any]):
        """Simulate a single request.

        Args:
            metrics: Metrics dictionary to update
        """
        try:
            request_start = time.time()
            metrics["total_requests"] += 1

            # Simulate request processing
            await asyncio.sleep(0.01)  # Simulate processing time

            latency = (time.time() - request_start) * 1000
            metrics["latencies"].append(latency)
            metrics["successful_requests"] += 1

        except Exception as e:
            metrics["failed_requests"] += 1
            metrics["errors"].append(str(e))

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data.

        Args:
            data: Data list
            percentile: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _create_result(
        self,
        benchmark_type: BenchmarkType,
        latencies: List[float],
        duration: float,
        success_count: int,
        error_count: int,
    ) -> BenchmarkResult:
        """Create benchmark result.

        Args:
            benchmark_type: Type of benchmark
            latencies: List of latencies in ms
            duration: Test duration in seconds
            success_count: Number of successful operations
            error_count: Number of failed operations

        Returns:
            Benchmark result
        """
        operations_count = success_count + error_count
        operations_per_second = operations_count / duration if duration > 0 else 0

        # Calculate statistics
        avg_latency = statistics.mean(latencies) if latencies else 0
        p50_latency = self._percentile(latencies, 50)
        p95_latency = self._percentile(latencies, 95)
        p99_latency = self._percentile(latencies, 99)
        min_latency = min(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0

        # Get system metrics
        memory_usage_mb = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_usage_percent = psutil.cpu_percent()

        # Calculate success rate
        success_rate = success_count / operations_count if operations_count > 0 else 0

        return BenchmarkResult(
            benchmark_type=benchmark_type,
            test_name=self.config.test_name,
            duration_seconds=duration,
            operations_count=operations_count,
            operations_per_second=operations_per_second,
            latency_ms=avg_latency,
            p50_latency_ms=p50_latency,
            p95_latency_ms=p95_latency,
            p99_latency_ms=p99_latency,
            min_latency_ms=min_latency,
            max_latency_ms=max_latency,
            success_rate=success_rate,
            error_count=error_count,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
        )


class BenchmarkReporter:
    """Generates reports from benchmark results."""

    @staticmethod
    def generate_report(results: List[BenchmarkResult]) -> str:
        """Generate benchmark report.

        Args:
            results: List of benchmark results

        Returns:
            Formatted report
        """
        report = ["# Performance Benchmark Report\n"]

        for result in results:
            report.append(f"## {result.test_name}\n")
            report.append(f"**Type:** {result.benchmark_type.value}\n")
            report.append(f"**Duration:** {result.duration_seconds:.2f}s\n")
            report.append(f"**Operations:** {result.operations_count}\n")
            report.append(f"**Operations/sec:** {result.operations_per_second:.2f}\n")
            report.append(f"**Avg Latency:** {result.latency_ms:.2f}ms\n")
            report.append(f"**P50 Latency:** {result.p50_latency_ms:.2f}ms\n")
            report.append(f"**P95 Latency:** {result.p95_latency_ms:.2f}ms\n")
            report.append(f"**P99 Latency:** {result.p99_latency_ms:.2f}ms\n")
            report.append(f"**Success Rate:** {result.success_rate:.2%}\n")
            report.append(f"**Memory Usage:** {result.memory_usage_mb:.2f}MB\n")
            report.append(f"**CPU Usage:** {result.cpu_usage_percent:.2f}%\n")
            report.append("\n")

        return "\n".join(report)

    @staticmethod
    def export_json(results: List[BenchmarkResult]) -> str:
        """Export results as JSON.

        Args:
            results: List of benchmark results

        Returns:
            JSON string
        """
        import json

        data = []
        for result in results:
            data.append({
                "benchmark_type": result.benchmark_type.value,
                "test_name": result.test_name,
                "duration_seconds": result.duration_seconds,
                "operations_count": result.operations_count,
                "operations_per_second": result.operations_per_second,
                "latency_ms": result.latency_ms,
                "p50_latency_ms": result.p50_latency_ms,
                "p95_latency_ms": result.p95_latency_ms,
                "p99_latency_ms": result.p99_latency_ms,
                "min_latency_ms": result.min_latency_ms,
                "max_latency_ms": result.max_latency_ms,
                "success_rate": result.success_rate,
                "error_count": result.error_count,
                "memory_usage_mb": result.memory_usage_mb,
                "cpu_usage_percent": result.cpu_usage_percent,
                "metadata": result.metadata,
            })

        return json.dumps(data, indent=2)
