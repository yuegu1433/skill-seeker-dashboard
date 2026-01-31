"""Statistics chart component.

This module provides StatisticsChartComponent for displaying
statistical data with various chart types.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from .base import BaseChartComponent, AnimationType

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Chart type options."""
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    RADAR = "radar"
    SCATTER = "scatter"


class StatisticsChartComponent(BaseChartComponent):
    """Statistics chart component for data visualization."""

    def __init__(
        self,
        component_id: str,
        chart_type: ChartType = ChartType.BAR,
        show_legend: bool = True,
        show_grid: bool = True,
        show_tooltip: bool = True,
        stacked: bool = False,
        color_scheme: str = "default",
        **kwargs,
    ):
        """Initialize statistics chart component.

        Args:
            component_id: Component identifier
            chart_type: Type of chart
            show_legend: Whether to show legend
            show_grid: Whether to show grid
            show_tooltip: Whether to show tooltips
            stacked: Whether to stack bars/areas
            color_scheme: Color scheme name
            **kwargs: Additional base component arguments
        """
        super().__init__(component_id, **kwargs)
        self.chart_type = chart_type
        self.show_legend = show_legend
        self.show_grid = show_grid
        self.show_tooltip = show_tooltip
        self.stacked = stacked
        self.color_scheme = color_scheme
        self.labels: List[str] = []
        self.datasets: List[Dict[str, Any]] = []

    async def render(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Render statistics chart.

        Args:
            data: Chart data with labels and values

        Returns:
            Rendered chart configuration
        """
        # Parse data into labels and datasets
        self._parse_chart_data(data)

        config = self.get_config()
        config.update({
            "type": "statistics_chart",
            "chart_type": self.chart_type.value,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self._get_chart_options(),
            "style": self._get_chart_style(),
            "animation": self._get_animation_config(),
        })

        self._rendered_at = datetime.utcnow()
        self._is_initialized = True

        logger.debug(f"Rendered statistics chart {self.component_id}")
        return config

    async def update(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update chart with new data.

        Args:
            new_data: New chart data

        Returns:
            Updated chart configuration
        """
        # Store old data for transition
        old_labels = self.labels.copy()
        old_datasets = [d.copy() for d in self.datasets]

        # Render with new data
        config = await self.render(new_data)

        # Add transition metadata
        config["transition"] = {
            "type": "data_update",
            "old_labels": old_labels,
            "old_datasets": old_datasets,
            "duration": self.animation_duration,
        }

        return config

    def _parse_chart_data(self, data: List[Dict[str, Any]]):
        """Parse raw data into chart labels and datasets.

        Args:
            data: Raw chart data
        """
        if not data:
            return

        # Extract labels from first data item
        first_item = data[0]
        self.labels = [key for key in first_item.keys() if key not in ["label", "id", "category"]]

        # Parse datasets
        self.datasets = []
        for item in data:
            dataset = {
                "label": item.get("label", f"Dataset {len(self.datasets) + 1}"),
                "data": [item.get(label, 0) for label in self.labels],
                "backgroundColor": self._get_dataset_colors(len(self.datasets)),
                "borderColor": self._get_dataset_colors(len(self.datasets), alpha=1.0),
                "borderWidth": 2,
                "fill": self.chart_type == ChartType.AREA,
            }

            # Add category for pie/doughnut charts
            if self.chart_type in [ChartType.PIE, ChartType.DOUGHNUT]:
                dataset["category"] = item.get("category", dataset["label"])

            self.datasets.append(dataset)

    def _get_dataset_colors(self, index: int, alpha: float = 0.6) -> List[str]:
        """Get colors for a dataset.

        Args:
            index: Dataset index
            alpha: Color alpha value

        Returns:
            List of color strings
        """
        color_palettes = {
            "default": [
                f"rgba(59, 130, 246, {alpha})",    # Blue
                f"rgba(16, 185, 129, {alpha})",    # Green
                f"rgba(245, 158, 11, {alpha})",    # Yellow
                f"rgba(239, 68, 68, {alpha})",     # Red
                f"rgba(139, 92, 246, {alpha})",    # Purple
                f"rgba(236, 72, 153, {alpha})",    # Pink
            ],
            "blue": [
                f"rgba(29, 78, 216, {alpha})",
                f"rgba(59, 130, 246, {alpha})",
                f"rgba(96, 165, 250, {alpha})",
                f"rgba(147, 197, 253, {alpha})",
            ],
            "green": [
                f"rgba(5, 150, 105, {alpha})",
                f"rgba(16, 185, 129, {alpha})",
                f"rgba(52, 211, 153, {alpha})",
                f"rgba(110, 231, 183, {alpha})",
            ],
            "warm": [
                f"rgba(220, 38, 38, {alpha})",
                f"rgba(245, 158, 11, {alpha})",
                f"rgba(34, 197, 94, {alpha})",
                f"rgba(59, 130, 246, {alpha})",
            ],
        }

        palette = color_palettes.get(self.color_scheme, color_palettes["default"])
        return [palette[index % len(palette)]]

    def _get_chart_options(self) -> Dict[str, Any]:
        """Get chart configuration options.

        Returns:
            Chart options dictionary
        """
        options = {
            "responsive": self.responsive,
            "maintainAspectRatio": False,
            "legend": {
                "display": self.show_legend,
                "position": "top",
            },
            "tooltip": {
                "enabled": self.show_tooltip,
                "mode": "index",
                "intersect": False,
            },
            "animation": {
                "duration": self.animation_duration,
                "easing": "easeInOutQuart",
            },
        }

        # Add grid options for non-pie charts
        if self.chart_type not in [ChartType.PIE, ChartType.DOUGHNUT]:
            options["scales"] = {
                "x": {
                    "display": True,
                    "grid": {
                        "display": self.show_grid,
                    },
                },
                "y": {
                    "display": True,
                    "beginAtZero": True,
                    "grid": {
                        "display": self.show_grid,
                    },
                    "stacked": self.stacked,
                },
            }

        return options

    def _get_chart_style(self) -> Dict[str, Any]:
        """Get chart style configuration.

        Returns:
            Style configuration dictionary
        """
        return {
            "background_color": "#ffffff",
            "border_color": "#e5e7eb",
            "text_color": "#374151",
            "grid_color": "#f3f4f6",
            "font_family": "system-ui, sans-serif",
            "font_size": "12px",
        }

    def _get_animation_config(self) -> Dict[str, Any]:
        """Get animation configuration.

        Returns:
            Animation configuration
        """
        if self.animation == AnimationType.NONE:
            return {"enabled": False}

        animations = {
            AnimationType.FADE: {
                "type": "fadeIn",
                "from": {"opacity": 0},
                "to": {"opacity": 1},
                "duration": self.animation_duration,
            },
            AnimationType.SLIDE: {
                "type": "slideInUp",
                "from": {"y": 50, "opacity": 0},
                "to": {"y": 0, "opacity": 1},
                "duration": self.animation_duration,
            },
            AnimationType.SCALE: {
                "type": "scaleIn",
                "from": {"scale": 0.8, "opacity": 0},
                "to": {"scale": 1, "opacity": 1},
                "duration": self.animation_duration,
            },
            AnimationType.BOUNCE: {
                "type": "bounceIn",
                "duration": self.animation_duration,
            },
        }

        return animations.get(self.animation, {"enabled": False})

    def add_dataset(
        self,
        label: str,
        data: List[float],
        color: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Add a new dataset.

        Args:
            label: Dataset label
            data: Dataset values
            color: Custom color (optional)
            **kwargs: Additional dataset properties

        Returns:
            Dataset index
        """
        dataset = {
            "label": label,
            "data": data,
            "backgroundColor": color or self._get_dataset_colors(len(self.datasets))[0],
            "borderColor": color or self._get_dataset_colors(len(self.datasets), alpha=1.0)[0],
            "borderWidth": 2,
            "fill": self.chart_type == ChartType.AREA,
            **kwargs,
        }

        self.datasets.append(dataset)
        logger.debug(f"Added dataset: {label}")
        return str(len(self.datasets) - 1)

    def remove_dataset(self, index: int) -> bool:
        """Remove a dataset by index.

        Args:
            index: Dataset index

        Returns:
            True if removed successfully
        """
        if 0 <= index < len(self.datasets):
            del self.datasets[index]
            logger.debug(f"Removed dataset at index {index}")
            return True

        return False

    def update_dataset(self, index: int, **kwargs) -> bool:
        """Update a dataset.

        Args:
            index: Dataset index
            **kwargs: Fields to update

        Returns:
            True if updated successfully
        """
        if 0 <= index < len(self.datasets):
            self.datasets[index].update(kwargs)
            logger.debug(f"Updated dataset at index {index}")
            return True

        return False

    def set_labels(self, labels: List[str]):
        """Set chart labels.

        Args:
            labels: List of label names
        """
        self.labels = labels

    def get_labels(self) -> List[str]:
        """Get chart labels.

        Returns:
            List of labels
        """
        return self.labels

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate statistics from chart data.

        Returns:
            Statistics dictionary
        """
        if not self.datasets:
            return {"datasets": 0}

        stats = {
            "datasets": len(self.datasets),
            "labels": len(self.labels),
            "total_data_points": sum(len(d["data"]) for d in self.datasets),
        }

        # Calculate statistics for each dataset
        dataset_stats = []
        for i, dataset in enumerate(self.datasets):
            data = dataset["data"]
            if data:
                dataset_stats.append({
                    "index": i,
                    "label": dataset["label"],
                    "min": min(data),
                    "max": max(data),
                    "sum": sum(data),
                    "avg": sum(data) / len(data),
                    "count": len(data),
                })

        stats["dataset_statistics"] = dataset_stats
        return stats

    def export_chartjs_config(self) -> Dict[str, Any]:
        """Export chart as Chart.js configuration.

        Returns:
            Chart.js configuration dictionary
        """
        return {
            "type": self.chart_type.value,
            "data": {
                "labels": self.labels,
                "datasets": self.datasets,
            },
            "options": self._get_chart_options(),
        }

    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate chart data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        if not super().validate_data(data):
            return False

        if not data:
            return True

        # Check if all items have the same structure
        first_keys = set(data[0].keys())
        for item in data[1:]:
            if set(item.keys()) != first_keys:
                return False

        return True
