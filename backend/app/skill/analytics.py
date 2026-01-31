"""Skill Analytics Manager.

This module provides comprehensive analytics and reporting capabilities
for skill management, including usage statistics, performance metrics,
trend analysis, and quality assessments.
"""

import asyncio
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, Counter
import logging

from .event_manager import SkillEventManager, EventType
from .manager import SkillManager

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    RATE = "rate"


class TimeRange(Enum):
    """Time range enumeration."""
    LAST_HOUR = "last_hour"
    LAST_DAY = "last_day"
    LAST_WEEK = "last_week"
    LAST_MONTH = "last_month"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"


class AggregationType(Enum):
    """Aggregation type enumeration."""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"


@dataclass
class Metric:
    """Represents a metric data point."""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class AnalyticsReport:
    """Represents an analytics report."""

    report_id: str
    title: str
    description: str
    generated_at: datetime = field(default_factory=datetime.now)
    time_range: TimeRange = TimeRange.LAST_MONTH
    metrics: List[Metric] = field(default_factory=list)
    insights: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["generated_at"] = self.generated_at.isoformat()
        data["time_range"] = self.time_range.value
        data["metrics"] = [m.to_dict() for m in self.metrics]
        return data


@dataclass
class SkillUsageStats:
    """Represents skill usage statistics."""

    skill_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0
    min_execution_time: float = 0.0
    max_execution_time: float = 0.0
    error_rate: float = 0.0
    last_executed: Optional[datetime] = None
    execution_history: List[float] = field(default_factory=list)
    user_feedback: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        if self.last_executed:
            data["last_executed"] = self.last_executed.isoformat()
        return data


@dataclass
class QualityScore:
    """Represents a skill quality score."""

    skill_id: str
    overall_score: float
    code_quality: float
    documentation_score: float
    test_coverage: float
    performance_score: float
    security_score: float
    maintainability: float
    breakdown: Dict[str, float] = field(default_factory=dict)
    evaluated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["evaluated_at"] = self.evaluated_at.isoformat()
        return data


@dataclass
class DependencyGraph:
    """Represents a dependency graph."""

    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[Tuple[str, str]] = field(default_factory=list)  # (source, target)
    cycles: List[List[str]] = field(default_factory=list)

    def add_node(self, node_id: str, **kwargs):
        """Add a node to the graph."""
        self.nodes[node_id] = kwargs

    def add_edge(self, source: str, target: str):
        """Add an edge to the graph."""
        self.edges.append((source, target))

    def detect_cycles(self):
        """Detect cycles in the dependency graph."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            # Visit all neighbors
            for neighbor in self._get_neighbors(node):
                dfs(neighbor, path)

            rec_stack.remove(node)
            path.pop()

        for node in self.nodes:
            if node not in visited:
                dfs(node, [])

        self.cycles = cycles
        return cycles

    def _get_neighbors(self, node: str) -> List[str]:
        """Get neighbors of a node."""
        return [target for source, target in self.edges if source == node]


class SkillAnalytics:
    """Manages skill analytics and reporting."""

    def __init__(
        self,
        skill_manager: SkillManager,
        event_manager: SkillEventManager,
    ):
        """Initialize analytics manager.

        Args:
            skill_manager: Skill manager instance
            event_manager: Event manager instance
        """
        self.skill_manager = skill_manager
        self.event_manager = event_manager

        # Metrics storage
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.skill_stats: Dict[str, SkillUsageStats] = {}
        self.quality_scores: Dict[str, QualityScore] = {}

        # Analytics cache
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}

        # Lock for concurrent access
        self._lock = asyncio.Lock()

    async def track_execution(
        self,
        skill_id: str,
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track skill execution.

        Args:
            skill_id: Skill identifier
            execution_time: Execution time in seconds
            success: Whether execution was successful
            error_message: Error message if failed
            metadata: Additional metadata
        """
        async with self._lock:
            # Initialize stats if not exists
            if skill_id not in self.skill_stats:
                self.skill_stats[skill_id] = SkillUsageStats(skill_id=skill_id)

            stats = self.skill_stats[skill_id]

            # Update stats
            stats.total_executions += 1
            stats.execution_history.append(execution_time)

            if success:
                stats.successful_executions += 1
            else:
                stats.failed_executions += 1
                if error_message:
                    stats.user_feedback.append({
                        "type": "error",
                        "message": error_message,
                        "timestamp": datetime.now().isoformat(),
                    })

            # Update timing stats
            if len(stats.execution_history) > 0:
                stats.average_execution_time = statistics.mean(stats.execution_history)
                stats.min_execution_time = min(stats.execution_history)
                stats.max_execution_time = max(stats.execution_history)

            # Calculate error rate
            if stats.total_executions > 0:
                stats.error_rate = (stats.failed_executions / stats.total_executions) * 100

            stats.last_executed = datetime.now()

            # Record metric
            await self.record_metric(
                name="skill.execution.time",
                value=execution_time,
                metric_type=MetricType.TIMER,
                tags={
                    "skill_id": skill_id,
                    "status": "success" if success else "failure",
                },
                metadata=metadata,
            )

            # Record success/failure metrics
            await self.record_metric(
                name="skill.execution.count",
                value=1,
                metric_type=MetricType.COUNTER,
                tags={
                    "skill_id": skill_id,
                    "result": "success" if success else "failure",
                },
            )

            # Publish event
            await self.event_manager.publish_event(
                EventType.SKILL_EXECUTED,
                skill_id=skill_id,
                execution_time=execution_time,
                success=success,
                error_message=error_message,
            )

    async def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Record a metric.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            tags: Metric tags
            metadata: Additional metadata
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            tags=tags or {},
            metadata=metadata,
        )

        self.metrics[name].append(metric)

        # Keep only recent metrics (last 30 days)
        cutoff_time = datetime.now() - timedelta(days=30)
        self.metrics[name] = [
            m for m in self.metrics[name]
            if m.timestamp > cutoff_time
        ]

    async def calculate_quality_score(
        self,
        skill_id: str,
    ) -> Optional[QualityScore]:
        """Calculate quality score for a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            QualityScore instance or None
        """
        try:
            # Get skill data
            skill = await self.skill_manager.get_skill(skill_id)
            if not skill:
                return None

            # Get usage stats
            stats = self.skill_stats.get(skill_id)

            # Calculate component scores
            code_quality = await self._analyze_code_quality(skill)
            documentation_score = await self._analyze_documentation(skill)
            test_coverage = await self._analyze_test_coverage(skill)
            performance_score = await self._analyze_performance(stats)
            security_score = await self._analyze_security(skill)
            maintainability = await self._analyze_maintainability(skill)

            # Calculate overall score (weighted average)
            overall_score = (
                code_quality * 0.25 +
                documentation_score * 0.15 +
                test_coverage * 0.15 +
                performance_score * 0.20 +
                security_score * 0.15 +
                maintainability * 0.10
            )

            # Create quality score
            quality = QualityScore(
                skill_id=skill_id,
                overall_score=overall_score,
                code_quality=code_quality,
                documentation_score=documentation_score,
                test_coverage=test_coverage,
                performance_score=performance_score,
                security_score=security_score,
                maintainability=maintainability,
                breakdown={
                    "code_quality": code_quality,
                    "documentation": documentation_score,
                    "test_coverage": test_coverage,
                    "performance": performance_score,
                    "security": security_score,
                    "maintainability": maintainability,
                },
            )

            # Cache score
            self.quality_scores[skill_id] = quality

            return quality

        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return None

    async def _analyze_code_quality(self, skill: Any) -> float:
        """Analyze code quality.

        Args:
            skill: Skill data

        Returns:
            Quality score (0-100)
        """
        score = 50.0  # Base score

        # Check for required fields
        if hasattr(skill, "name") and skill.name:
            score += 10

        if hasattr(skill, "description") and skill.description:
            score += 10

        if hasattr(skill, "author") and skill.author:
            score += 5

        if hasattr(skill, "dependencies"):
            score += 5

        # Check content quality (simplified)
        content = getattr(skill, "content", "")
        if content:
            # Simple heuristics
            lines = content.split("\n")
            non_empty_lines = [l for l in lines if l.strip()]

            # Code structure
            if len(non_empty_lines) > 10:
                score += 5

            # Comments
            comment_lines = [l for l in lines if l.strip().startswith("#")]
            if len(comment_lines) > 0:
                score += 5

            # Error handling
            if "try:" in content or "except" in content:
                score += 5

        return min(100.0, score)

    async def _analyze_documentation(self, skill: Any) -> float:
        """Analyze documentation quality.

        Args:
            skill: Skill data

        Returns:
            Documentation score (0-100)
        """
        score = 0.0

        # Check description
        if hasattr(skill, "description") and skill.description:
            score += 30
            if len(skill.description) > 100:
                score += 10

        # Check README
        if hasattr(skill, "readme") and skill.readme:
            score += 40
            if len(skill.readme) > 500:
                score += 10

        # Check examples
        if hasattr(skill, "examples") and skill.examples:
            score += 10

        return min(100.0, score)

    async def _analyze_test_coverage(self, skill: Any) -> float:
        """Analyze test coverage.

        Args:
            skill: Skill data

        Returns:
            Test coverage score (0-100)
        """
        # This is a simplified analysis
        # In a real system, you would parse actual test files

        score = 0.0

        # Check for test-related fields
        if hasattr(skill, "test_config") and skill.test_config:
            score += 50

        if hasattr(skill, "test_files") and skill.test_files:
            score += 30

        # Check for testing keywords in content
        content = getattr(skill, "content", "")
        if "test" in content.lower() or "pytest" in content.lower():
            score += 20

        return min(100.0, score)

    async def _analyze_performance(self, stats: Optional[SkillUsageStats]) -> float:
        """Analyze performance.

        Args:
            stats: Skill usage statistics

        Returns:
            Performance score (0-100)
        """
        if not stats or stats.total_executions == 0:
            return 50.0  # Default score

        score = 100.0

        # Execution time penalty
        if stats.average_execution_time > 5.0:
            score -= 20
        elif stats.average_execution_time > 2.0:
            score -= 10

        # Error rate penalty
        if stats.error_rate > 10:
            score -= 30
        elif stats.error_rate > 5:
            score -= 15
        elif stats.error_rate > 1:
            score -= 5

        return max(0.0, score)

    async def _analyze_security(self, skill: Any) -> float:
        """Analyze security aspects.

        Args:
            skill: Skill data

        Returns:
            Security score (0-100)
        """
        score = 70.0  # Base score

        content = getattr(skill, "content", "")

        # Check for security issues
        security_keywords = ["eval(", "exec(", "subprocess", "os.system"]
        for keyword in security_keywords:
            if keyword in content:
                score -= 20

        # Check dependencies for security
        dependencies = getattr(skill, "dependencies", [])
        if dependencies:
            # Check for known vulnerable packages (simplified)
            vulnerable_packages = ["django<3.0", "flask<2.0"]
            for dep in dependencies:
                if any(vuln in str(dep) for vuln in vulnerable_packages):
                    score -= 15

        return max(0.0, min(100.0, score))

    async def _analyze_maintainability(self, skill: Any) -> float:
        """Analyze maintainability.

        Args:
            skill: Skill data

        Returns:
            Maintainability score (0-100)
        """
        score = 60.0  # Base score

        content = getattr(skill, "content", "")
        if not content:
            return score

        # Code complexity (simplified)
        lines = content.split("\n")
        non_empty_lines = [l for l in lines if l.strip()]

        if len(non_empty_lines) > 100:
            score -= 10
        elif len(non_empty_lines) > 50:
            score -= 5

        # Function/class count
        if "def " in content:
            func_count = content.count("def ")
            if func_count > 20:
                score -= 10
            elif func_count > 10:
                score -= 5

        # Documentation
        if hasattr(skill, "description") and skill.description:
            score += 10

        return max(0.0, min(100.0, score))

    async def build_dependency_graph(
        self,
        skill_ids: Optional[List[str]] = None,
    ) -> DependencyGraph:
        """Build dependency graph.

        Args:
            skill_ids: List of skill IDs to include

        Returns:
            DependencyGraph instance
        """
        graph = DependencyGraph()

        # Get all skills if not specified
        if skill_ids is None:
            search_result = await self.skill_manager.list_skills(page_size=1000)
            skill_ids = [skill.id for skill in search_result.items]

        # Build nodes
        for skill_id in skill_ids:
            skill = await self.skill_manager.get_skill(skill_id)
            if skill:
                graph.add_node(
                    skill_id,
                    name=getattr(skill, "name", skill_id),
                    version=getattr(skill, "version", "unknown"),
                    category=getattr(skill, "category", "unknown"),
                )

                # Add dependencies
                dependencies = getattr(skill, "dependencies", [])
                for dep in dependencies:
                    dep_id = str(dep) if isinstance(dep, str) else dep.get("name", str(dep))
                    graph.add_edge(skill_id, dep_id)

        # Detect cycles
        graph.detect_cycles()

        return graph

    async def generate_usage_report(
        self,
        skill_ids: Optional[List[str]] = None,
        time_range: TimeRange = TimeRange.LAST_MONTH,
    ) -> AnalyticsReport:
        """Generate usage analytics report.

        Args:
            skill_ids: List of skill IDs to include
            time_range: Time range for report

        Returns:
            AnalyticsReport instance
        """
        report_id = f"usage_report_{datetime.now().timestamp()}"

        # Filter skills
        if skill_ids is None:
            search_result = await self.skill_manager.list_skills(page_size=1000)
            skill_ids = [skill.id for skill in search_result.items]

        # Collect metrics
        metrics = []
        for skill_id in skill_ids:
            stats = self.skill_stats.get(skill_id)
            if stats:
                # Execution count metric
                metrics.append(Metric(
                    name="skill.execution.count",
                    value=stats.total_executions,
                    metric_type=MetricType.COUNTER,
                    tags={"skill_id": skill_id},
                ))

                # Error rate metric
                metrics.append(Metric(
                    name="skill.error.rate",
                    value=stats.error_rate,
                    metric_type=MetricType.GAUGE,
                    tags={"skill_id": skill_id},
                ))

                # Average execution time metric
                metrics.append(Metric(
                    name="skill.execution.time.avg",
                    value=stats.average_execution_time,
                    metric_type=MetricType.GAUGE,
                    tags={"skill_id": skill_id},
                ))

        # Generate insights
        insights = await self._generate_usage_insights(skill_ids)

        # Generate recommendations
        recommendations = await self._generate_usage_recommendations(skill_ids)

        # Create summary
        summary = {
            "total_skills": len(skill_ids),
            "active_skills": len([s for s in skill_ids if s in self.skill_stats]),
            "total_executions": sum(
                self.skill_stats.get(sid, SkillUsageStats(skill_id=sid)).total_executions
                for sid in skill_ids
            ),
            "average_error_rate": statistics.mean([
                self.skill_stats.get(sid, SkillUsageStats(skill_id=sid)).error_rate
                for sid in skill_ids
            ]) if skill_ids else 0,
        }

        return AnalyticsReport(
            report_id=report_id,
            title="Skill Usage Analytics",
            description="Usage statistics and performance metrics",
            time_range=time_range,
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            summary=summary,
        )

    async def _generate_usage_insights(
        self,
        skill_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Generate usage insights.

        Args:
            skill_ids: List of skill IDs

        Returns:
            List of insights
        """
        insights = []

        # Most popular skills
        skill_executions = [
            (sid, self.skill_stats.get(sid, SkillUsageStats(skill_id=sid)).total_executions)
            for sid in skill_ids
        ]
        skill_executions.sort(key=lambda x: x[1], reverse=True)

        if skill_executions:
            top_skill = skill_executions[0]
            insights.append({
                "type": "most_popular",
                "message": f"Most executed skill: {top_skill[0]} ({top_skill[1]} executions)",
                "value": top_skill[1],
            })

        # Skills with high error rates
        high_error_skills = [
            (sid, stats.error_rate)
            for sid, stats in self.skill_stats.items()
            if sid in skill_ids and stats.error_rate > 10
        ]

        if high_error_skills:
            insights.append({
                "type": "high_error_rate",
                "message": f"{len(high_error_skills)} skills have error rates > 10%",
                "count": len(high_error_skills),
            })

        # Performance insights
        execution_times = [
            stats.average_execution_time
            for sid, stats in self.skill_stats.items()
            if sid in skill_ids and stats.total_executions > 0
        ]

        if execution_times:
            avg_time = statistics.mean(execution_times)
            max_time = max(execution_times)

            insights.append({
                "type": "performance",
                "message": f"Average execution time: {avg_time:.2f}s, Max: {max_time:.2f}s",
                "average": avg_time,
                "maximum": max_time,
            })

        return insights

    async def _generate_usage_recommendations(
        self,
        skill_ids: List[str],
    ) -> List[str]:
        """Generate usage recommendations.

        Args:
            skill_ids: List of skill IDs

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for unused skills
        unused_skills = [
            sid for sid in skill_ids
            if sid not in self.skill_stats or
            self.skill_stats[sid].total_executions == 0
        ]

        if len(unused_skills) > len(skill_ids) * 0.3:
            recommendations.append(
                f"Consider reviewing or archiving {len(unused_skills)} unused skills"
            )

        # Check for high error rate skills
        high_error_skills = [
            sid for sid, stats in self.skill_stats.items()
            if sid in skill_ids and stats.error_rate > 10
        ]

        if high_error_skills:
            recommendations.append(
                f"Improve error handling for {len(high_error_skills)} high-error-rate skills"
            )

        # Check for slow skills
        slow_skills = [
            sid for sid, stats in self.skill_stats.items()
            if sid in skill_ids and stats.average_execution_time > 5.0
        ]

        if slow_skills:
            recommendations.append(
                f"Optimize performance for {len(slow_skills)} slow-executing skills"
            )

        return recommendations

    async def get_skill_stats(
        self,
        skill_id: str,
    ) -> Optional[SkillUsageStats]:
        """Get skill statistics.

        Args:
            skill_id: Skill identifier

        Returns:
            SkillUsageStats instance or None
        """
        return self.skill_stats.get(skill_id)

    async def get_quality_score(
        self,
        skill_id: str,
    ) -> Optional[QualityScore]:
        """Get skill quality score.

        Args:
            skill_id: Skill identifier

        Returns:
            QualityScore instance or None
        """
        return self.quality_scores.get(skill_id)

    async def get_metrics(
        self,
        metric_name: str,
        time_range: Optional[TimeRange] = None,
    ) -> List[Metric]:
        """Get metrics by name.

        Args:
            metric_name: Metric name
            time_range: Time range filter

        Returns:
            List of Metric instances
        """
        metrics = self.metrics.get(metric_name, [])

        if time_range:
            cutoff_time = self._get_time_range_cutoff(time_range)
            metrics = [m for m in metrics if m.timestamp > cutoff_time]

        return metrics

    def _get_time_range_cutoff(self, time_range: TimeRange) -> datetime:
        """Get cutoff time for time range.

        Args:
            time_range: Time range

        Returns:
            Cutoff datetime
        """
        now = datetime.now()

        if time_range == TimeRange.LAST_HOUR:
            return now - timedelta(hours=1)
        elif time_range == TimeRange.LAST_DAY:
            return now - timedelta(days=1)
        elif time_range == TimeRange.LAST_WEEK:
            return now - timedelta(weeks=1)
        elif time_range == TimeRange.LAST_MONTH:
            return now - timedelta(days=30)
        elif time_range == TimeRange.LAST_YEAR:
            return now - timedelta(days=365)
        else:
            return now - timedelta(days=30)

    async def aggregate_metrics(
        self,
        metric_name: str,
        aggregation: AggregationType,
        time_range: TimeRange = TimeRange.LAST_MONTH,
        percentile: Optional[float] = None,
    ) -> Optional[float]:
        """Aggregate metrics.

        Args:
            metric_name: Metric name
            aggregation: Aggregation type
            time_range: Time range
            percentile: Percentile value (for PERCENTILE aggregation)

        Returns:
            Aggregated value or None
        """
        metrics = await self.get_metrics(metric_name, time_range)

        if not metrics:
            return None

        values = [m.value for m in metrics]

        if aggregation == AggregationType.SUM:
            return sum(values)
        elif aggregation == AggregationType.AVERAGE:
            return statistics.mean(values)
        elif aggregation == AggregationType.MIN:
            return min(values)
        elif aggregation == AggregationType.MAX:
            return max(values)
        elif aggregation == AggregationType.COUNT:
            return len(values)
        elif aggregation == AggregationType.PERCENTILE:
            if percentile is not None:
                return statistics.quantiles(values, n=100)[int(percentile) - 1]
            else:
                return statistics.median(values)

        return None

    async def export_analytics(
        self,
        format_type: str = "json",
    ) -> Optional[str]:
        """Export analytics data.

        Args:
            format_type: Export format

        Returns:
            Exported data or None
        """
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_skills": len(self.skill_stats),
            "total_metrics": sum(len(metrics) for metrics in self.metrics.values()),
            "skill_stats": {
                skill_id: stats.to_dict()
                for skill_id, stats in self.skill_stats.items()
            },
            "quality_scores": {
                skill_id: score.to_dict()
                for skill_id, score in self.quality_scores.items()
            },
            "metrics": {
                name: [metric.to_dict() for metric in metric_list]
                for name, metric_list in self.metrics.items()
            },
        }

        if format_type == "json":
            import json
            return json.dumps(export_data, indent=2, default=str)

        return str(export_data)

    async def cleanup_old_data(self, days_old: int = 30):
        """Cleanup old analytics data.

        Args:
            days_old: Remove data older than this many days
        """
        cutoff_time = datetime.now() - timedelta(days=days_old)

        # Clean metrics
        for metric_name in self.metrics:
            self.metrics[metric_name] = [
                m for m in self.metrics[metric_name]
                if m.timestamp > cutoff_time
            ]

        # Clean skill stats (keep only recent executions)
        for skill_id, stats in self.skill_stats.items():
            # Keep only last 1000 executions
            if len(stats.execution_history) > 1000:
                stats.execution_history = stats.execution_history[-1000:]

        logger.info(f"Cleaned up analytics data older than {days_old} days")
