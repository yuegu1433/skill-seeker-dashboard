"""Tests for visualization system.

This module contains comprehensive tests for VisualizationManager and chart components,
including chart generation, data aggregation, real-time updates, and component functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from uuid import uuid4

# Import components to test
from backend.app.progress.visualization_manager import (
    VisualizationManager,
    ChartType,
    MetricAggregation,
    ChartTemplate,
    RealTimeUpdate,
)
from backend.app.progress.charts.base import BaseChartComponent, AnimationType, ResponsiveBreakpoint
from backend.app.progress.charts.progress_bar import ProgressBarComponent
from backend.app.progress.charts.timeline import TimelineComponent, TimelineItem, TimelineOrientation
from backend.app.progress.charts.statistics_chart import StatisticsChartComponent, ChartType as StatsChartType
from backend.app.progress.charts.heatmap import HeatmapComponent
from backend.app.progress.charts.gauge import GaugeComponent


class TestBaseChartComponent:
    """Test BaseChartComponent functionality."""

    @pytest.fixture
    def base_component(self):
        """Create base component instance."""
        class TestComponent(BaseChartComponent):
            async def render(self, data):
                return {"type": "test", "data": data}

            async def update(self, new_data):
                return await self.render(new_data)

        return TestComponent("test-component")

    def test_component_initialization(self, base_component):
        """Test component initialization."""
        assert base_component.component_id == "test-component"
        assert base_component.width == 400
        assert base_component.height == 300
        assert base_component.responsive is True
        assert base_component.animation == AnimationType.FADE
        assert base_component.animation_duration == 1000
        assert base_component.theme == "default"
        assert base_component.data == []
        assert base_component.metadata == {}
        assert base_component.event_handlers == {}
        assert base_component._is_initialized is False

    def test_set_get_data(self, base_component):
        """Test setting and getting data."""
        test_data = [{"value": 1}, {"value": 2}]
        base_component.set_data(test_data)
        assert base_component.get_data() == test_data

    def test_set_get_metadata(self, base_component):
        """Test setting and getting metadata."""
        test_metadata = {"key": "value"}
        base_component.set_metadata(test_metadata)
        assert base_component.get_metadata() == test_metadata

    def test_event_handlers(self, base_component):
        """Test event handler management."""
        async def test_handler(event_data):
            pass

        base_component.add_event_handler("click", test_handler)
        assert "click" in base_component.event_handlers

        base_component.remove_event_handler("click")
        assert "click" not in base_component.event_handlers

    def test_get_config(self, base_component):
        """Test getting component configuration."""
        config = base_component.get_config()
        assert config["component_id"] == "test-component"
        assert config["width"] == 400
        assert config["height"] == 300
        assert config["responsive"] is True
        assert config["animation"] == "fade"
        assert config["animation_duration"] == 1000
        assert config["theme"] == "default"

    @pytest.mark.asyncio
    async def test_handle_event(self, base_component):
        """Test event handling."""
        async def test_handler(event_data):
            assert event_data == "test_data"

        base_component.add_event_handler("test_event", test_handler)
        await base_component.handle_event("test_event", "test_data")

    def test_responsive_config(self, base_component):
        """Test responsive configuration."""
        # Mobile breakpoint
        base_component.apply_responsive_config(ResponsiveBreakpoint.MOBILE)
        assert base_component.width <= 320
        assert base_component.height <= 240

        # Reset
        base_component.width = 400
        base_component.height = 300

        # Desktop breakpoint (should keep original)
        base_component.apply_responsive_config(ResponsiveBreakpoint.DESKTOP)
        assert base_component.width == 400
        assert base_component.height == 300

    def test_validate_data(self, base_component):
        """Test data validation."""
        # Valid data
        valid_data = [{"value": 1}, {"value": 2}]
        assert base_component.validate_data(valid_data) is True

        # Empty data
        assert base_component.validate_data([]) is True

        # Invalid data
        assert base_component.validate_data("not a list") is False

    def test_format_tooltip(self, base_component):
        """Test tooltip formatting."""
        data_point = {"label": "Test", "value": 100, "id": "123"}
        tooltip = base_component.format_tooltip(data_point)
        assert "label: Test" in tooltip
        assert "value: 100" in tooltip
        assert "id" not in tooltip

    def test_calculate_statistics(self, base_component):
        """Test statistics calculation."""
        base_component.set_data([
            {"value": 10},
            {"value": 20},
            {"value": 30},
        ])
        stats = base_component.calculate_statistics()
        assert stats["count"] == 3
        assert stats["min"] == 10
        assert stats["max"] == 30
        assert stats["sum"] == 60
        assert stats["avg"] == 20

    def test_export_data_json(self, base_component):
        """Test data export to JSON."""
        base_component.set_data([{"value": 1}])
        exported = base_component.export_data("json")
        data = json.loads(exported)
        assert data["component_id"] == "test-component"
        assert data["type"] == "TestComponent"
        assert data["data"] == [{"value": 1}]


class TestProgressBarComponent:
    """Test ProgressBarComponent functionality."""

    @pytest.fixture
    def progress_bar(self):
        """Create progress bar component."""
        return ProgressBarComponent(
            "test-progress",
            show_percentage=True,
            show_label=True,
            striped=False,
            animated=True,
            color_scheme="blue",
        )

    @pytest.mark.asyncio
    async def test_render_progress_bar(self, progress_bar):
        """Test rendering progress bar."""
        data = [{"progress": 75, "label": "Test Progress"}]
        config = await progress_bar.render(data)

        assert config["type"] == "progress_bar"
        assert config["progress"] == 75
        assert config["label"] == "Test Progress"
        assert config["show_percentage"] is True
        assert config["show_label"] is True
        assert config["striped"] is False
        assert config["animated"] is True
        assert config["color_scheme"] == "blue"

    @pytest.mark.asyncio
    async def test_update_progress_bar(self, progress_bar):
        """Test updating progress bar."""
        # Initial render
        data = [{"progress": 50, "label": "Initial"}]
        config = await progress_bar.render(data)
        assert config["progress"] == 50

        # Update
        new_data = [{"progress": 75, "label": "Updated"}]
        config = await progress_bar.update(new_data)
        assert config["progress"] == 75
        assert config["transition"]["from"] == 50
        assert config["transition"]["to"] == 75

    def test_progress_bar_validation(self, progress_bar):
        """Test progress bar data validation."""
        # Valid data
        assert progress_bar.validate_data([{"progress": 50}]) is True
        assert progress_bar.validate_data([{"progress": 0}]) is True
        assert progress_bar.validate_data([{"progress": 100}]) is True

        # Invalid data
        assert progress_bar.validate_data([{"progress": -10}]) is False
        assert progress_bar.validate_data([{"progress": 150}]) is False
        assert progress_bar.validate_data([{"progress": "invalid"}]) is False
        assert progress_bar.validate_data([{}]) is False

    def test_progress_bar_methods(self, progress_bar):
        """Test progress bar utility methods."""
        progress_bar.set_progress(75, "Test")
        assert progress_bar.get_progress() == 75
        assert progress_bar.label == "Test"
        assert not progress_bar.is_complete()
        assert progress_bar.get_remaining() == 25

        progress_bar.increment_progress(30)
        assert progress_bar.get_progress() == 100
        assert progress_bar.is_complete()
        assert progress_bar.get_remaining() == 0

    def test_get_bar_style(self, progress_bar):
        """Test getting bar style."""
        style = progress_bar._get_bar_style()
        assert "background_color" in style
        assert "text_color" in style
        assert "height" in style
        assert "border_radius" in style
        assert "font_size" in style

    def test_export_html(self, progress_bar):
        """Test HTML export."""
        progress_bar.set_progress(75, "Test Progress")
        html = progress_bar.export_html()
        assert "progress-bar-container" in html
        assert "Test Progress" in html
        assert "75" in html


class TestTimelineComponent:
    """Test TimelineComponent functionality."""

    @pytest.fixture
    def timeline(self):
        """Create timeline component."""
        return TimelineComponent(
            "test-timeline",
            orientation=TimelineOrientation.HORIZONTAL,
            show_connector=True,
            show_date=True,
            collapsible=False,
            color_scheme="blue",
        )

    @pytest.mark.asyncio
    async def test_render_timeline(self, timeline):
        """Test rendering timeline."""
        data = [
            {
                "id": "item1",
                "title": "Event 1",
                "description": "Description 1",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "completed",
            },
            {
                "id": "item2",
                "title": "Event 2",
                "description": "Description 2",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "active",
            },
        ]
        config = await timeline.render(data)

        assert config["type"] == "timeline"
        assert config["orientation"] == "horizontal"
        assert config["show_connector"] is True
        assert config["show_date"] is True
        assert len(config["items"]) == 2

    def test_add_remove_items(self, timeline):
        """Test adding and removing timeline items."""
        # Add item
        item_id = timeline.add_item(
            "Test Event",
            "Test Description",
            datetime.utcnow(),
            "active",
        )
        assert item_id in [item.id for item in timeline.items]

        # Get item
        item = timeline.get_item(item_id)
        assert item is not None
        assert item.title == "Test Event"

        # Update item
        updated = timeline.update_item(item_id, title="Updated Event")
        assert updated is True
        assert timeline.get_item(item_id).title == "Updated Event"

        # Remove item
        removed = timeline.remove_item(item_id)
        assert removed is True
        assert timeline.get_item(item_id) is None

    def test_timeline_status_methods(self, timeline):
        """Test timeline status management."""
        item_id = timeline.add_item("Test", "Description", datetime.utcnow(), "default")

        # Mark complete
        assert timeline.mark_item_complete(item_id) is True
        assert timeline.get_item(item_id).status == "completed"

        # Mark active
        assert timeline.mark_item_active(item_id) is True
        assert timeline.get_item(item_id).status == "active"

    def test_timeline_statistics(self, timeline):
        """Test timeline statistics."""
        timeline.add_item("1", "d", datetime.utcnow(), "completed")
        timeline.add_item("2", "d", datetime.utcnow(), "completed")
        timeline.add_item("3", "d", datetime.utcnow(), "active")
        timeline.add_item("4", "d", datetime.utcnow(), "error")

        stats = timeline.get_statistics()
        assert stats["total_items"] == 4
        assert stats["completed_items"] == 2
        assert stats["active_items"] == 1
        assert stats["error_items"] == 1
        assert stats["completion_rate"] == 50.0


class TestStatisticsChartComponent:
    """Test StatisticsChartComponent functionality."""

    @pytest.fixture
    def stats_chart(self):
        """Create statistics chart component."""
        return StatisticsChartComponent(
            "test-stats",
            chart_type=StatsChartType.BAR,
            show_legend=True,
            show_grid=True,
            show_tooltip=True,
            stacked=False,
            color_scheme="default",
        )

    @pytest.mark.asyncio
    async def test_render_stats_chart(self, stats_chart):
        """Test rendering statistics chart."""
        data = [
            {"label": "Dataset 1", "value1": 10, "value2": 20},
            {"label": "Dataset 2", "value1": 15, "value2": 25},
        ]
        config = await stats_chart.render(data)

        assert config["type"] == "statistics_chart"
        assert config["chart_type"] == "bar"
        assert config["labels"] == ["value1", "value2"]
        assert len(config["datasets"]) == 2
        assert config["show_legend"] is True
        assert config["show_grid"] is True

    def test_add_remove_datasets(self, stats_chart):
        """Test adding and removing datasets."""
        # Add dataset
        dataset_index = stats_chart.add_dataset("Test Dataset", [10, 20, 30])
        assert dataset_index == "0"
        assert len(stats_chart.datasets) == 1

        # Update dataset
        updated = stats_chart.update_dataset(0, label="Updated Dataset")
        assert updated is True
        assert stats_chart.datasets[0]["label"] == "Updated Dataset"

        # Remove dataset
        removed = stats_chart.remove_dataset(0)
        assert removed is True
        assert len(stats_chart.datasets) == 0

    def test_set_labels(self, stats_chart):
        """Test setting labels."""
        labels = ["Label1", "Label2", "Label3"]
        stats_chart.set_labels(labels)
        assert stats_chart.get_labels() == labels

    def test_calculate_statistics(self, stats_chart):
        """Test statistics calculation."""
        stats_chart.add_dataset("Dataset 1", [10, 20, 30])
        stats_chart.add_dataset("Dataset 2", [15, 25, 35])
        stats_chart.set_labels(["A", "B", "C"])

        stats = stats_chart.calculate_statistics()
        assert stats["datasets"] == 2
        assert stats["labels"] == 3
        assert stats["total_data_points"] == 6
        assert len(stats["dataset_statistics"]) == 2

    def test_export_chartjs_config(self, stats_chart):
        """Test Chart.js configuration export."""
        stats_chart.add_dataset("Test", [1, 2, 3])
        stats_chart.set_labels(["A", "B", "C"])

        config = stats_chart.export_chartjs_config()
        assert config["type"] == "bar"
        assert len(config["data"]["labels"]) == 3
        assert len(config["data"]["datasets"]) == 1


class TestHeatmapComponent:
    """Test HeatmapComponent functionality."""

    @pytest.fixture
    def heatmap(self):
        """Create heatmap component."""
        return HeatmapComponent(
            "test-heatmap",
            cell_size=20,
            color_scheme="viridis",
            show_tooltip=True,
            show_legend=True,
        )

    @pytest.mark.asyncio
    async def test_render_heatmap(self, heatmap):
        """Test rendering heatmap."""
        data = [
            {"x": 0, "y": 0, "value": 50, "label": "Cell 1"},
            {"x": 1, "y": 1, "value": 75, "label": "Cell 2"},
        ]
        config = await heatmap.render(data)

        assert config["type"] == "heatmap"
        assert config["cell_size"] == 20
        assert config["color_scheme"] == "viridis"
        assert len(config["cells"]) == 2
        assert config["show_tooltip"] is True
        assert config["show_legend"] is True

    def test_add_remove_cells(self, heatmap):
        """Test adding and removing heatmap cells."""
        # Add cell
        heatmap.add_cell(0, 0, 50, "Test Cell")
        cell = heatmap.get_cell(0, 0)
        assert cell is not None
        assert cell["value"] == 50
        assert cell["label"] == "Test Cell"

        # Update cell
        updated = heatmap.update_cell(0, 0, 75)
        assert updated is True
        assert heatmap.get_cell(0, 0)["value"] == 75

        # Remove cell
        removed = heatmap.remove_cell(0, 0)
        assert removed is True
        assert heatmap.get_cell(0, 0) is None

    def test_generate_activity_heatmap(self, heatmap):
        """Test generating activity heatmap."""
        start_date = datetime.utcnow()
        heatmap_data = heatmap.generate_activity_heatmap(start_date, days=7)

        assert len(heatmap_data) == 7
        for cell in heatmap_data:
            assert "x" in cell
            assert "y" in cell
            assert "value" in cell
            assert 0 <= cell["value"] <= 100

    def test_calculate_statistics(self, heatmap):
        """Test heatmap statistics."""
        heatmap.add_cell(0, 0, 10)
        heatmap.add_cell(1, 1, 20)
        heatmap.add_cell(2, 2, 30)

        stats = heatmap.calculate_statistics()
        assert stats["cells"] == 3
        assert stats["min_value"] == 10
        assert stats["max_value"] == 30
        assert stats["avg_value"] == 20
        assert stats["total_value"] == 60


class TestGaugeComponent:
    """Test GaugeComponent functionality."""

    @pytest.fixture
    def gauge(self):
        """Create gauge component."""
        return GaugeComponent(
            "test-gauge",
            min_value=0,
            max_value=100,
            unit="%",
            show_min_max=True,
            show_value=True,
            color_scheme="default",
            gauge_type="semicircle",
        )

    @pytest.mark.asyncio
    async def test_render_gauge(self, gauge):
        """Test rendering gauge."""
        data = [{"value": 75, "label": "Progress"}]
        config = await gauge.render(data)

        assert config["type"] == "gauge"
        assert config["value"] == 75
        assert config["label"] == "Progress"
        assert config["min_value"] == 0
        assert config["max_value"] == 100
        assert config["unit"] == "%"
        assert config["show_min_max"] is True
        assert config["show_value"] is True

    def test_gauge_value_methods(self, gauge):
        """Test gauge value manipulation."""
        gauge.set_value(75, "Test")
        assert gauge.get_value() == 75
        assert gauge.get_percentage() == 75
        assert not gauge.is_at_max()
        assert not gauge.is_at_min()
        assert gauge.get_remaining() == 25

        gauge.increment(30)
        assert gauge.get_value() == 100
        assert gauge.is_at_max()
        assert gauge.get_remaining() == 0

        gauge.decrement(50)
        assert gauge.get_value() == 50
        assert not gauge.is_at_max()
        assert not gauge.is_at_min()

    def test_get_color(self, gauge):
        """Test getting gauge color."""
        gauge.set_value(25)
        color = gauge.get_color()
        assert color == "#ef4444"  # Red for low values

        gauge.set_value(65)
        color = gauge.get_color()
        assert color == "#f59e0b"  # Yellow for medium values

        gauge.set_value(90)
        color = gauge.get_color()
        assert color == "#10b981"  # Green for high values

    def test_export_html(self, gauge):
        """Test HTML export."""
        gauge.set_value(75, "Test Gauge")
        html = gauge.export_html()
        assert "gauge-container" in html
        assert "Test Gauge" in html
        assert "75%" in html


class TestVisualizationManager:
    """Test VisualizationManager functionality."""

    @pytest.fixture
    def viz_manager(self):
        """Create visualization manager instance."""
        return VisualizationManager()

    @pytest.mark.asyncio
    async def test_create_progress_chart(self, viz_manager):
        """Test creating progress chart."""
        task_ids = ["task1", "task2", "task3"]
        chart = await viz_manager.create_progress_chart(
            task_ids=task_ids,
            time_range="7d",
            group_by="status",
            aggregation=MetricAggregation.AVG,
        )

        assert chart.chart_type == ChartType.LINE
        assert chart.title == "Task Progress Over Time"
        assert len(chart.data) > 0
        assert chart.metadata["task_ids"] == task_ids

    @pytest.mark.asyncio
    async def test_create_status_distribution_chart(self, viz_manager):
        """Test creating status distribution chart."""
        chart = await viz_manager.create_status_distribution_chart(
            user_id="user123",
            task_type="computation",
        )

        assert chart.chart_type == ChartType.PIE
        assert chart.title == "Task Status Distribution"
        assert len(chart.data) > 0
        assert all("status" in item for item in chart.data)
        assert all("count" in item for item in chart.data)

    @pytest.mark.asyncio
    async def test_create_performance_metrics_chart(self, viz_manager):
        """Test creating performance metrics chart."""
        task_ids = ["task1", "task2"]
        chart = await viz_manager.create_performance_metrics_chart(
            task_ids=task_ids,
            time_range="7d",
        )

        assert chart.chart_type == ChartType.GAUGE
        assert chart.title == "Performance Metrics"
        assert len(chart.data) > 0

    @pytest.mark.asyncio
    async def test_create_activity_heatmap(self, viz_manager):
        """Test creating activity heatmap."""
        chart = await viz_manager.create_activity_heatmap(
            user_id="user123",
            days=30,
        )

        assert chart.chart_type == ChartType.HEATMAP
        assert chart.title == "Activity Heatmap"
        assert len(chart.data) == 30
        assert all("date" in item for item in chart.data)
        assert all("count" in item for item in chart.data)

    @pytest.mark.asyncio
    async def test_create_dashboard(self, viz_manager):
        """Test creating dashboard."""
        dashboard_id = "test-dashboard"
        widgets = [
            {
                "widget_id": "widget1",
                "title": "Progress Chart",
                "chart_type": "line",
                "query": {
                    "task_ids": ["task1"],
                    "time_range": "7d",
                },
                "position": {"x": 0, "y": 0},
                "size": {"width": 6, "height": 4},
            },
        ]

        dashboard = await viz_manager.create_dashboard(
            dashboard_id=dashboard_id,
            title="Test Dashboard",
            widgets=widgets,
        )

        assert dashboard["dashboard_id"] == dashboard_id
        assert dashboard["title"] == "Test Dashboard"
        assert len(dashboard["widgets"]) == 1

    @pytest.mark.asyncio
    async def test_custom_chart_creation(self, viz_manager):
        """Test creating custom charts with templates."""
        # Create custom chart using template
        data = [{"time": "2024-01-01", "value": 50}]
        chart = await viz_manager.create_custom_chart(
            template_id="progress_timeline",
            data=data,
            title="Custom Progress Chart",
            custom_config={"color": "#ff0000"},
        )

        assert chart.chart_type == ChartType.LINE
        assert chart.title == "Custom Progress Chart"
        assert chart.metadata["template_id"] == "progress_timeline"
        assert chart.metadata["config"]["color"] == "#ff0000"

    def test_chart_templates(self, viz_manager):
        """Test chart template management."""
        # List templates
        templates = viz_manager.list_chart_templates()
        assert len(templates) > 0

        # Get template
        template = viz_manager.get_chart_template("progress_timeline")
        assert template is not None
        assert template.template_id == "progress_timeline"

        # Add custom template
        custom_template = viz_manager.add_chart_template(
            template_id="custom_template",
            name="Custom Template",
            chart_type=ChartType.BAR,
            config={"custom": "config"},
            description="Custom template description",
        )

        assert custom_template.template_id == "custom_template"
        assert custom_template.name == "Custom Template"

    @pytest.mark.asyncio
    async def test_real_time_subscriptions(self, viz_manager):
        """Test real-time update subscriptions."""
        # Add subscription
        subscription_id = await viz_manager.add_real_time_subscription(
            connection_id="conn123",
            visualization_query={"chart_type": "line"},
            update_interval=5.0,
        )

        assert subscription_id in viz_manager.real_time_updates
        assert viz_manager._stats["total_real_time_subscriptions"] == 1

        # Remove subscription
        await viz_manager.remove_real_time_subscription(subscription_id)
        assert subscription_id not in viz_manager.real_time_updates

    @pytest.mark.asyncio
    async def test_animated_chart(self, viz_manager):
        """Test creating animated charts."""
        base_data = [{"time": "2024-01-01", "value": 50}]
        animation_config = {
            "type": "fade",
            "duration": 1500,
            "easing": "ease-in-out",
            "title": "Animated Chart",
        }

        chart = await viz_manager.create_animated_chart(
            base_data=base_data,
            animation_config=animation_config,
        )

        assert chart.metadata["animation"]["enabled"] is True
        assert chart.metadata["animation"]["type"] == "fade"
        assert chart.metadata["animation"]["duration"] == 1000

    def test_export_dashboard(self, viz_manager):
        """Test dashboard export."""
        # Create dashboard
        asyncio.run(viz_manager.create_dashboard(
            dashboard_id="export-test",
            title="Export Test",
            widgets=[],
        ))

        # Export as JSON
        exported = asyncio.run(viz_manager.export_dashboard("export-test", "json"))
        data = json.loads(exported)
        assert data["dashboard_id"] == "export-test"
        assert data["exported_at"] is not None

    def test_statistics(self, viz_manager):
        """Test visualization manager statistics."""
        stats = viz_manager.get_stats()
        assert "total_visualizations_created" in stats
        assert "total_dashboards_created" in stats
        assert "total_data_points_rendered" in stats
        assert "total_templates_created" in stats
        assert "total_templates" in stats
        assert "active_subscriptions" in stats


# Test data fixtures
@pytest.fixture
def sample_progress_data():
    """Create sample progress data."""
    return [
        {"progress": 25, "label": "Phase 1"},
        {"progress": 50, "label": "Phase 2"},
        {"progress": 75, "label": "Phase 3"},
        {"progress": 100, "label": "Completed"},
    ]


@pytest.fixture
def sample_timeline_data():
    """Create sample timeline data."""
    now = datetime.utcnow()
    return [
        {
            "id": "1",
            "title": "Started",
            "description": "Task started",
            "timestamp": now.isoformat(),
            "status": "completed",
        },
        {
            "id": "2",
            "title": "In Progress",
            "description": "Task in progress",
            "timestamp": (now + timedelta(hours=1)).isoformat(),
            "status": "active",
        },
        {
            "id": "3",
            "title": "Completed",
            "description": "Task completed",
            "timestamp": (now + timedelta(hours=2)).isoformat(),
            "status": "default",
        },
    ]


@pytest.fixture
def sample_stats_data():
    """Create sample statistics data."""
    return [
        {"label": "Dataset 1", "value1": 10, "value2": 20, "value3": 30},
        {"label": "Dataset 2", "value1": 15, "value2": 25, "value3": 35},
        {"label": "Dataset 3", "value1": 20, "value2": 30, "value3": 40},
    ]


@pytest.fixture
def sample_heatmap_data():
    """Create sample heatmap data."""
    return [
        {"x": 0, "y": 0, "value": 25, "label": "Cell (0,0)"},
        {"x": 1, "y": 0, "value": 50, "label": "Cell (1,0)"},
        {"x": 0, "y": 1, "value": 75, "label": "Cell (0,1)"},
        {"x": 1, "y": 1, "value": 100, "label": "Cell (1,1)"},
    ]


@pytest.fixture
def sample_gauge_data():
    """Create sample gauge data."""
    return [{"value": 85, "label": "CPU Usage"}]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
