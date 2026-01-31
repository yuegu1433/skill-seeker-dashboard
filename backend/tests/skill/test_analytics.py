"""Tests for SkillAnalytics.

This module contains comprehensive unit tests for the SkillAnalytics
analytics and reporting functionality.
"""

import pytest
import asyncio
import statistics
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Dict, Any

from app.skill.analytics import (
    SkillAnalytics,
    Metric,
    AnalyticsReport,
    SkillUsageStats,
    QualityScore,
    DependencyGraph,
    MetricType,
    TimeRange,
    AggregationType,
)
from app.skill.manager import SkillManager
from app.skill.event_manager import SkillEventManager


@pytest.fixture
def skill_manager():
    """Create mock skill manager."""
    manager = Mock(spec=SkillManager)
    manager.get_skill = AsyncMock(return_value=Mock(
        id="test-skill",
        name="Test Skill",
        description="Test skill description",
        author="Test Author",
        content="def test():\n    print('test')",
        dependencies=["click", "pydantic"],
        version="1.0.0",
        category="testing",
    ))
    manager.list_skills = AsyncMock(return_value=Mock(
        items=[
            Mock(id="skill1", name="Skill 1"),
            Mock(id="skill2", name="Skill 2"),
            Mock(id="skill3", name="Skill 3"),
        ]
    ))
    return manager


@pytest.fixture
def event_manager():
    """Create mock event manager."""
    manager = Mock(spec=SkillEventManager)
    manager.publish_event = AsyncMock(return_value="event_id")
    return manager


@pytest.fixture
def analytics(skill_manager, event_manager):
    """Create SkillAnalytics instance for testing."""
    return SkillAnalytics(
        skill_manager=skill_manager,
        event_manager=event_manager,
    )


class TestMetric:
    """Test Metric dataclass."""

    def test_create_metric(self):
        """Test creating a metric."""
        metric = Metric(
            name="test.metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            tags={"env": "test"},
        )

        assert metric.name == "test.metric"
        assert metric.value == 42.0
        assert metric.metric_type == MetricType.COUNTER
        assert metric.tags == {"env": "test"}
        assert metric.timestamp is not None
        assert metric.metadata is None

    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        metric = Metric(
            name="test.metric",
            value=42.0,
            metric_type=MetricType.GAUGE,
        )

        data = metric.to_dict()

        assert "name" in data
        assert "value" in data
        assert "metric_type" in data
        assert "timestamp" in data
        assert data["metric_type"] == "gauge"
        assert isinstance(data["timestamp"], str)


class TestAnalyticsReport:
    """Test AnalyticsReport dataclass."""

    def test_create_report(self):
        """Test creating an analytics report."""
        report = AnalyticsReport(
            report_id="report123",
            title="Test Report",
            description="Test analytics report",
            time_range=TimeRange.LAST_WEEK,
        )

        assert report.report_id == "report123"
        assert report.title == "Test Report"
        assert report.description == "Test analytics report"
        assert report.time_range == TimeRange.LAST_WEEK
        assert report.generated_at is not None
        assert len(report.metrics) == 0
        assert len(report.insights) == 0
        assert len(report.recommendations) == 0

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = AnalyticsReport(
            report_id="report123",
            title="Test Report",
            description="Test",
        )

        data = report.to_dict()

        assert "report_id" in data
        assert "title" in data
        assert "generated_at" in data
        assert "time_range" in data
        assert data["time_range"] == "last_month"
        assert isinstance(data["generated_at"], str)


class TestSkillUsageStats:
    """Test SkillUsageStats dataclass."""

    def test_create_stats(self):
        """Test creating skill usage statistics."""
        stats = SkillUsageStats(
            skill_id="test-skill",
            total_executions=100,
            successful_executions=95,
            failed_executions=5,
        )

        assert stats.skill_id == "test-skill"
        assert stats.total_executions == 100
        assert stats.successful_executions == 95
        assert stats.failed_executions == 5
        assert stats.average_execution_time == 0.0
        assert stats.error_rate == 5.0

    def test_stats_to_dict(self):
        """Test converting stats to dictionary."""
        stats = SkillUsageStats(skill_id="test-skill")

        data = stats.to_dict()

        assert "skill_id" in data
        assert "total_executions" in data
        assert "error_rate" in data
        assert isinstance(data["total_executions"], int)


class TestQualityScore:
    """Test QualityScore dataclass."""

    def test_create_quality_score(self):
        """Test creating a quality score."""
        quality = QualityScore(
            skill_id="test-skill",
            overall_score=85.0,
            code_quality=90.0,
            documentation_score=80.0,
            test_coverage=75.0,
            performance_score=88.0,
            security_score=92.0,
            maintainability=85.0,
        )

        assert quality.skill_id == "test-skill"
        assert quality.overall_score == 85.0
        assert quality.code_quality == 90.0
        assert quality.documentation_score == 80.0
        assert quality.test_coverage == 75.0
        assert quality.performance_score == 88.0
        assert quality.security_score == 92.0
        assert quality.maintainability == 85.0
        assert quality.evaluated_at is not None

    def test_quality_score_to_dict(self):
        """Test converting quality score to dictionary."""
        quality = QualityScore(
            skill_id="test-skill",
            overall_score=85.0,
            code_quality=90.0,
            documentation_score=80.0,
            test_coverage=75.0,
            performance_score=88.0,
            security_score=92.0,
            maintainability=85.0,
        )

        data = quality.to_dict()

        assert "skill_id" in data
        assert "overall_score" in data
        assert "evaluated_at" in data
        assert isinstance(data["evaluated_at"], str)


class TestDependencyGraph:
    """Test DependencyGraph dataclass."""

    def test_create_graph(self):
        """Test creating a dependency graph."""
        graph = DependencyGraph()

        assert len(graph.nodes) == 0
        assert len(graph.edges) == 0
        assert len(graph.cycles) == 0

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = DependencyGraph()

        graph.add_node("skill1", name="Skill 1", version="1.0.0")

        assert "skill1" in graph.nodes
        assert graph.nodes["skill1"]["name"] == "Skill 1"
        assert graph.nodes["skill1"]["version"] == "1.0.0"

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = DependencyGraph()

        graph.add_edge("skill1", "skill2")

        assert ("skill1", "skill2") in graph.edges

    def test_detect_cycles(self):
        """Test cycle detection."""
        graph = DependencyGraph()

        # Add nodes
        graph.add_node("skill1")
        graph.add_node("skill2")
        graph.add_node("skill3")

        # Add edges forming a cycle: skill1 -> skill2 -> skill3 -> skill1
        graph.add_edge("skill1", "skill2")
        graph.add_edge("skill2", "skill3")
        graph.add_edge("skill3", "skill1")

        # Detect cycles
        cycles = graph.detect_cycles()

        assert len(cycles) > 0
        assert any("skill1" in cycle for cycle in cycles)

    def test_get_neighbors(self):
        """Test getting neighbors of a node."""
        graph = DependencyGraph()

        graph.add_node("skill1")
        graph.add_node("skill2")
        graph.add_node("skill3")

        graph.add_edge("skill1", "skill2")
        graph.add_edge("skill1", "skill3")

        neighbors = graph._get_neighbors("skill1")

        assert "skill2" in neighbors
        assert "skill3" in neighbors


class TestSkillAnalytics:
    """Test SkillAnalytics class."""

    @pytest.mark.asyncio
    async def test_track_execution_success(self, analytics):
        """Test tracking successful execution."""
        await analytics.track_execution(
            skill_id="test-skill",
            execution_time=1.5,
            success=True,
        )

        # Check stats
        assert "test-skill" in analytics.skill_stats
        stats = analytics.skill_stats["test-skill"]
        assert stats.total_executions == 1
        assert stats.successful_executions == 1
        assert stats.failed_executions == 0
        assert stats.average_execution_time == 1.5
        assert stats.error_rate == 0.0

        # Check event was published
        analytics.event_manager.publish_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_track_execution_failure(self, analytics):
        """Test tracking failed execution."""
        await analytics.track_execution(
            skill_id="test-skill",
            execution_time=2.0,
            success=False,
            error_message="Test error",
        )

        # Check stats
        stats = analytics.skill_stats["test-skill"]
        assert stats.total_executions == 1
        assert stats.failed_executions == 1
        assert stats.error_rate == 100.0
        assert len(stats.user_feedback) == 1
        assert stats.user_feedback[0]["type"] == "error"

    @pytest.mark.asyncio
    async def test_track_multiple_executions(self, analytics):
        """Test tracking multiple executions."""
        # Track multiple executions
        for i in range(5):
            await analytics.track_execution(
                skill_id="test-skill",
                execution_time=1.0 + i * 0.1,
                success=True,
            )

        # Check stats
        stats = analytics.skill_stats["test-skill"]
        assert stats.total_executions == 5
        assert stats.successful_executions == 5
        assert stats.average_execution_time == 1.2  # (1.0 + 1.1 + 1.2 + 1.3 + 1.4) / 5
        assert stats.min_execution_time == 1.0
        assert stats.max_execution_time == 1.4

    @pytest.mark.asyncio
    async def test_record_metric(self, analytics):
        """Test recording a metric."""
        await analytics.record_metric(
            name="test.metric",
            value=42.0,
            metric_type=MetricType.COUNTER,
            tags={"env": "test"},
        )

        # Check metric was recorded
        assert "test.metric" in analytics.metrics
        assert len(analytics.metrics["test.metric"]) == 1
        assert analytics.metrics["test.metric"][0].value == 42.0
        assert analytics.metrics["test.metric"][0].tags == {"env": "test"}

    @pytest.mark.asyncio
    async def test_record_multiple_metrics(self, analytics):
        """Test recording multiple metrics."""
        for i in range(3):
            await analytics.record_metric(
                name="test.metric",
                value=float(i),
                metric_type=MetricType.COUNTER,
            )

        # Check metrics
        assert len(analytics.metrics["test.metric"]) == 3

    @pytest.mark.asyncio
    async def test_calculate_quality_score(self, analytics, skill_manager):
        """Test calculating quality score."""
        quality = await analytics.calculate_quality_score("test-skill")

        assert quality is not None
        assert quality.skill_id == "test-skill"
        assert 0 <= quality.overall_score <= 100
        assert 0 <= quality.code_quality <= 100
        assert 0 <= quality.documentation_score <= 100
        assert 0 <= quality.test_coverage <= 100
        assert 0 <= quality.performance_score <= 100
        assert 0 <= quality.security_score <= 100
        assert 0 <= quality.maintainability <= 100

        # Check score was cached
        assert "test-skill" in analytics.quality_scores

    @pytest.mark.asyncio
    async def test_calculate_quality_score_nonexistent_skill(self, analytics, skill_manager):
        """Test calculating quality score for non-existent skill."""
        skill_manager.get_skill = AsyncMock(return_value=None)

        quality = await analytics.calculate_quality_score("nonexistent")

        assert quality is None

    @pytest.mark.asyncio
    async def test_analyze_code_quality(self, analytics, skill_manager):
        """Test code quality analysis."""
        # Create skill with good structure
        skill = Mock(
            name="Test Skill",
            description="Good description",
            author="Test Author",
            content="def test():\n    # Test function\n    try:\n        pass\n    except:\n        pass",
            dependencies=["click"],
        )

        score = await analytics._analyze_code_quality(skill)

        assert 0 <= score <= 100
        assert score >= 50  # Should have a good score

    @pytest.mark.asyncio
    async def test_analyze_documentation(self, analytics):
        """Test documentation analysis."""
        # Create skill with documentation
        skill = Mock(
            description="This is a test skill with a detailed description",
            readme="This is a README with detailed information",
            examples=["example1", "example2"],
        )

        score = await analytics._analyze_documentation(skill)

        assert 0 <= score <= 100
        assert score > 0

    @pytest.mark.asyncio
    async def test_analyze_performance(self, analytics):
        """Test performance analysis."""
        # Good performance stats
        good_stats = SkillUsageStats(
            skill_id="test",
            total_executions=100,
            successful_executions=100,
            failed_executions=0,
            average_execution_time=1.0,
            execution_history=[1.0] * 100,
        )

        score = await analytics._analyze_performance(good_stats)

        assert 0 <= score <= 100
        assert score > 80

        # Bad performance stats
        bad_stats = SkillUsageStats(
            skill_id="test",
            total_executions=100,
            successful_executions=80,
            failed_executions=20,
            average_execution_time=10.0,
            execution_history=[10.0] * 100,
        )

        score = await analytics._analyze_performance(bad_stats)

        assert score < 50

    @pytest.mark.asyncio
    async def test_analyze_security(self, analytics):
        """Test security analysis."""
        # Secure skill
        secure_skill = Mock(
            content="def safe_function():\n    return 'safe'",
            dependencies=["click"],
        )

        score = await analytics._analyze_security(secure_skill)

        assert 0 <= score <= 100
        assert score > 50

        # Insecure skill
        insecure_skill = Mock(
            content="eval(user_input)",
            dependencies=[],
        )

        score = await analytics._analyze_security(insecure_skill)

        assert score < 70

    @pytest.mark.asyncio
    async def test_analyze_maintainability(self, analytics):
        """Test maintainability analysis."""
        # Maintainable skill
        maintainable_skill = Mock(
            description="Good description",
            content="def func1():\n    pass\n\ndef func2():\n    pass",
        )

        score = await analytics._analyze_maintainability(maintainable_skill)

        assert 0 <= score <= 100

    @pytest.mark.asyncio
    async def test_build_dependency_graph(self, analytics):
        """Test building dependency graph."""
        graph = await analytics.build_dependency_graph(["skill1", "skill2"])

        assert isinstance(graph, DependencyGraph)
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_generate_usage_report(self, analytics):
        """Test generating usage report."""
        # Track some executions
        await analytics.track_execution("skill1", 1.0, True)
        await analytics.track_execution("skill1", 2.0, True)
        await analytics.track_execution("skill2", 3.0, False)

        # Generate report
        report = await analytics.generate_usage_report(
            skill_ids=["skill1", "skill2"],
            time_range=TimeRange.LAST_WEEK,
        )

        assert isinstance(report, AnalyticsReport)
        assert report.title == "Skill Usage Analytics"
        assert report.time_range == TimeRange.LAST_WEEK
        assert len(report.metrics) > 0
        assert "total_skills" in report.summary
        assert "total_executions" in report.summary

    @pytest.mark.asyncio
    async def test_get_skill_stats(self, analytics):
        """Test getting skill statistics."""
        # Track execution
        await analytics.track_execution("test-skill", 1.5, True)

        # Get stats
        stats = await analytics.get_skill_stats("test-skill")

        assert stats is not None
        assert stats.skill_id == "test-skill"
        assert stats.total_executions == 1

    @pytest.mark.asyncio
    async def test_get_skill_stats_nonexistent(self, analytics):
        """Test getting stats for non-existent skill."""
        stats = await analytics.get_skill_stats("nonexistent")

        assert stats is None

    @pytest.mark.asyncio
    async def test_get_quality_score(self, analytics, skill_manager):
        """Test getting quality score."""
        # Calculate quality score
        await analytics.calculate_quality_score("test-skill")

        # Get quality score
        quality = await analytics.get_quality_score("test-skill")

        assert quality is not None
        assert quality.skill_id == "test-skill"

    @pytest.mark.asyncio
    async def test_get_metrics(self, analytics):
        """Test getting metrics."""
        # Record metrics
        await analytics.record_metric("test.metric", 1.0, MetricType.COUNTER)
        await analytics.record_metric("test.metric", 2.0, MetricType.COUNTER)

        # Get metrics
        metrics = await analytics.get_metrics("test.metric")

        assert len(metrics) == 2
        assert all(m.name == "test.metric" for m in metrics)

    @pytest.mark.asyncio
    async def test_get_metrics_with_time_range(self, analytics):
        """Test getting metrics with time range filter."""
        # Record old metric
        old_metric = Metric("test.metric", 1.0, MetricType.COUNTER)
        old_metric.timestamp = datetime.now() - timedelta(days=35)
        analytics.metrics["test.metric"].append(old_metric)

        # Record recent metric
        await analytics.record_metric("test.metric", 2.0, MetricType.COUNTER)

        # Get metrics with time range
        metrics = await analytics.get_metrics(
            "test.metric",
            time_range=TimeRange.LAST_MONTH,
        )

        # Should only get recent metric
        assert len(metrics) == 1
        assert metrics[0].value == 2.0

    @pytest.mark.asyncio
    async def test_aggregate_metrics_sum(self, analytics):
        """Test aggregating metrics with SUM."""
        # Record metrics
        await analytics.record_metric("test.metric", 10.0, MetricType.COUNTER)
        await analytics.record_metric("test.metric", 20.0, MetricType.COUNTER)
        await analytics.record_metric("test.metric", 30.0, MetricType.COUNTER)

        # Aggregate
        result = await analytics.aggregate_metrics(
            "test.metric",
            AggregationType.SUM,
        )

        assert result == 60.0

    @pytest.mark.asyncio
    async def test_aggregate_metrics_average(self, analytics):
        """Test aggregating metrics with AVERAGE."""
        # Record metrics
        await analytics.record_metric("test.metric", 10.0, MetricType.GAUGE)
        await analytics.record_metric("test.metric", 20.0, MetricType.GAUGE)
        await analytics.record_metric("test.metric", 30.0, MetricType.GAUGE)

        # Aggregate
        result = await analytics.aggregate_metrics(
            "test.metric",
            AggregationType.AVERAGE,
        )

        assert result == 20.0

    @pytest.mark.asyncio
    async def test_aggregate_metrics_min_max(self, analytics):
        """Test aggregating metrics with MIN and MAX."""
        # Record metrics
        await analytics.record_metric("test.metric", 10.0, MetricType.GAUGE)
        await analytics.record_metric("test.metric", 30.0, MetricType.GAUGE)
        await analytics.record_metric("test.metric", 20.0, MetricType.GAUGE)

        # Aggregate
        min_result = await analytics.aggregate_metrics(
            "test.metric",
            AggregationType.MIN,
        )

        max_result = await analytics.aggregate_metrics(
            "test.metric",
            AggregationType.MAX,
        )

        assert min_result == 10.0
        assert max_result == 30.0

    @pytest.mark.asyncio
    async def test_aggregate_metrics_count(self, analytics):
        """Test aggregating metrics with COUNT."""
        # Record metrics
        for i in range(5):
            await analytics.record_metric("test.metric", 1.0, MetricType.COUNTER)

        # Aggregate
        result = await analytics.aggregate_metrics(
            "test.metric",
            AggregationType.COUNT,
        )

        assert result == 5

    @pytest.mark.asyncio
    async def test_aggregate_metrics_percentile(self, analytics):
        """Test aggregating metrics with PERCENTILE."""
        # Record metrics with different values
        for i in range(1, 11):
            await analytics.record_metric("test.metric", float(i), MetricType.GAUGE)

        # Aggregate (90th percentile)
        result = await analytics.aggregate_metrics(
            "test.metric",
            AggregationType.PERCENTILE,
            percentile=90.0,
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_export_analytics(self, analytics):
        """Test exporting analytics data."""
        # Add some data
        await analytics.track_execution("skill1", 1.0, True)
        await analytics.record_metric("test.metric", 42.0, MetricType.COUNTER)

        # Export
        exported = await analytics.export_analytics("json")

        assert exported is not None
        assert "exported_at" in exported
        assert "total_skills" in exported
        assert "skill_stats" in exported
        assert "metrics" in exported

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, analytics):
        """Test cleaning up old data."""
        # Add old metric
        old_metric = Metric("old.metric", 1.0, MetricType.COUNTER)
        old_metric.timestamp = datetime.now() - timedelta(days=40)
        analytics.metrics["old.metric"].append(old_metric)

        # Add recent metric
        await analytics.record_metric("old.metric", 2.0, MetricType.COUNTER)

        # Add skill with many executions
        stats = analytics.skill_stats["test-skill"] = SkillUsageStats(skill_id="test-skill")
        stats.execution_history = list(range(1500))

        # Cleanup
        await analytics.cleanup_old_data(days_old=30)

        # Check old metric was removed
        assert len(analytics.metrics["old.metric"]) == 1
        assert analytics.metrics["old.metric"][0].value == 2.0

        # Check execution history was trimmed
        assert len(stats.execution_history) <= 1000

    @pytest.mark.asyncio
    async def test_time_range_cutoffs(self, analytics):
        """Test time range cutoff calculations."""
        now = datetime.now()

        # Test LAST_HOUR
        cutoff = analytics._get_time_range_cutoff(TimeRange.LAST_HOUR)
        assert now - cutoff <= timedelta(hours=1)

        # Test LAST_DAY
        cutoff = analytics._get_time_range_cutoff(TimeRange.LAST_DAY)
        assert now - cutoff <= timedelta(days=1)

        # Test LAST_WEEK
        cutoff = analytics._get_time_range_cutoff(TimeRange.LAST_WEEK)
        assert now - cutoff <= timedelta(weeks=1)

        # Test LAST_MONTH
        cutoff = analytics._get_time_range_cutoff(TimeRange.LAST_MONTH)
        assert now - cutoff <= timedelta(days=30)

        # Test LAST_YEAR
        cutoff = analytics._get_time_range_cutoff(TimeRange.LAST_YEAR)
        assert now - cutoff <= timedelta(days=365)

    @pytest.mark.asyncio
    async def test_enums(self):
        """Test enum values."""
        # MetricType
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.TIMER.value == "timer"
        assert MetricType.RATE.value == "rate"

        # TimeRange
        assert TimeRange.LAST_HOUR.value == "last_hour"
        assert TimeRange.LAST_DAY.value == "last_day"
        assert TimeRange.LAST_WEEK.value == "last_week"
        assert TimeRange.LAST_MONTH.value == "last_month"
        assert TimeRange.LAST_YEAR.value == "last_year"
        assert TimeRange.CUSTOM.value == "custom"

        # AggregationType
        assert AggregationType.SUM.value == "sum"
        assert AggregationType.AVERAGE.value == "average"
        assert AggregationType.MIN.value == "min"
        assert AggregationType.MAX.value == "max"
        assert AggregationType.COUNT.value == "count"
        assert AggregationType.PERCENTILE.value == "percentile"
