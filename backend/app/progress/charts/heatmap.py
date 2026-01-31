"""Heatmap chart component.

This module provides HeatmapComponent for displaying
activity patterns and density visualizations.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from .base import BaseChartComponent, AnimationType

logger = logging.getLogger(__name__)


class HeatmapComponent(BaseChartComponent):
    """Heatmap component for displaying activity patterns."""

    def __init__(
        self,
        component_id: str,
        cell_size: int = 20,
        color_scheme: str = "viridis",
        show_tooltip: bool = True,
        show_legend: bool = True,
        **kwargs,
    ):
        """Initialize heatmap component.

        Args:
            component_id: Component identifier
            cell_size: Size of each cell in pixels
            color_scheme: Color scheme name
            show_tooltip: Whether to show tooltips
            show_legend: Whether to show color legend
            **kwargs: Additional base component arguments
        """
        super().__init__(component_id, **kwargs)
        self.cell_size = cell_size
        self.color_scheme = color_scheme
        self.show_tooltip = show_tooltip
        self.show_legend = show_legend
        self.cells: List[Dict[str, Any]] = []

    async def render(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Render heatmap component.

        Args:
            data: Heatmap data with coordinates and values

        Returns:
            Rendered heatmap configuration
        """
        # Parse data into cells
        self.cells = self._parse_heatmap_data(data)

        config = self.get_config()
        config.update({
            "type": "heatmap",
            "cells": self.cells,
            "cell_size": self.cell_size,
            "color_scheme": self.color_scheme,
            "show_tooltip": self.show_tooltip,
            "show_legend": self.show_legend,
            "color_scale": self._get_color_scale(),
            "animation": self._get_animation_config(),
        })

        self._rendered_at = datetime.utcnow()
        self._is_initialized = True

        logger.debug(f"Rendered heatmap {self.component_id} with {len(self.cells)} cells")
        return config

    async def update(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update heatmap with new data.

        Args:
            new_data: New heatmap data

        Returns:
            Updated heatmap configuration
        """
        # Store old cells for transition
        old_cells = self.cells.copy()

        # Render with new data
        config = await self.render(new_data)

        # Add transition metadata
        config["transition"] = {
            "type": "heatmap_update",
            "old_cells": old_cells,
            "duration": self.animation_duration,
        }

        return config

    def _parse_heatmap_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse raw data into heatmap cells.

        Args:
            data: Raw heatmap data

        Returns:
            List of cell dictionaries
        """
        cells = []

        for item in data:
            cell = {
                "x": item.get("x", 0),
                "y": item.get("y", 0),
                "value": float(item.get("value", 0)),
                "label": item.get("label", ""),
                "timestamp": self._parse_timestamp(item.get("timestamp")),
            }

            # Calculate color based on value and color scheme
            cell["color"] = self._get_cell_color(cell["value"])

            cells.append(cell)

        return cells

    def _parse_timestamp(self, timestamp: Any) -> Optional[str]:
        """Parse timestamp to ISO string.

        Args:
            timestamp: Timestamp to parse

        Returns:
            ISO formatted timestamp string
        """
        if isinstance(timestamp, datetime):
            return timestamp.isoformat()
        elif isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00')).isoformat()
            except ValueError:
                return timestamp
        else:
            return None

    def _get_cell_color(self, value: float) -> str:
        """Get color for a cell based on value.

        Args:
            value: Cell value

        Returns:
            Color string
        """
        # Normalize value to 0-1 range (assuming max value is 100)
        normalized = max(0, min(1, value / 100.0))

        color_schemes = {
            "viridis": [
                (0.0, "#440154"),
                (0.25, "#3b528b"),
                (0.5, "#21918c"),
                (0.75, "#5ec962"),
                (1.0, "#fde725"),
            ],
            "plasma": [
                (0.0, "#0d0887"),
                (0.25, "#6a00a8"),
                (0.5, "#b12a90"),
                (0.75, "#e16462"),
                (1.0, "#fca636"),
            ],
            "blues": [
                (0.0, "#f7fbff"),
                (0.25, "#deebf7"),
                (0.5, "#9ecae1"),
                (0.75, "#3182bd"),
                (1.0, "#08519c"),
            ],
            "reds": [
                (0.0, "#fff5f0"),
                (0.25, "#fee0d2"),
                (0.5, "#fc9272"),
                (0.75, "#de2d26"),
                (1.0, "#a50f15"),
            ],
            "greens": [
                (0.0, "#f7fcf5"),
                (0.25, "#c7e9c0"),
                (0.5, "#74c476"),
                (0.75, "#238b45"),
                (1.0, "#00441b"),
            ],
        }

        scheme = color_schemes.get(self.color_scheme, color_schemes["viridis"])

        # Find appropriate color based on normalized value
        for i in range(len(scheme) - 1):
            threshold, color = scheme[i]
            next_threshold, next_color = scheme[i + 1]

            if threshold <= normalized <= next_threshold:
                # Interpolate between colors
                return self._interpolate_color(color, next_color, (normalized - threshold) / (next_threshold - threshold))

        return scheme[-1][1]  # Return last color

    def _interpolate_color(self, color1: str, color2: str, factor: float) -> str:
        """Interpolate between two colors.

        Args:
            color1: First color
            color2: Second color
            factor: Interpolation factor (0-1)

        Returns:
            Interpolated color
        """
        # Parse hex colors
        def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)

        interpolated = tuple(int(rgb1[i] + factor * (rgb2[i] - rgb1[i])) for i in range(3))
        return rgb_to_hex(interpolated)

    def _get_color_scale(self) -> Dict[str, Any]:
        """Get color scale configuration.

        Returns:
            Color scale configuration
        """
        return {
            "scheme": self.color_scheme,
            "min": 0,
            "max": 100,
            "legend": {
                "display": self.show_legend,
                "position": "bottom",
            },
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
                "stagger": 10,
                "duration": self.animation_duration,
            },
            AnimationType.SCALE: {
                "type": "scaleIn",
                "stagger": 10,
                "duration": self.animation_duration,
            },
        }

        return animations.get(self.animation, {"enabled": False})

    def add_cell(
        self,
        x: int,
        y: int,
        value: float,
        label: str = "",
        timestamp: Optional[datetime] = None,
    ):
        """Add a new heatmap cell.

        Args:
            x: X coordinate
            y: Y coordinate
            value: Cell value
            label: Cell label
            timestamp: Cell timestamp
        """
        cell = {
            "x": x,
            "y": y,
            "value": value,
            "label": label,
            "timestamp": timestamp.isoformat() if timestamp else None,
            "color": self._get_cell_color(value),
        }

        self.cells.append(cell)
        logger.debug(f"Added heatmap cell at ({x}, {y}) with value {value}")

    def remove_cell(self, x: int, y: int) -> bool:
        """Remove a heatmap cell.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if removed successfully
        """
        for i, cell in enumerate(self.cells):
            if cell["x"] == x and cell["y"] == y:
                del self.cells[i]
                logger.debug(f"Removed heatmap cell at ({x}, {y})")
                return True

        return False

    def update_cell(self, x: int, y: int, value: float) -> bool:
        """Update a heatmap cell value.

        Args:
            x: X coordinate
            y: Y coordinate
            value: New value

        Returns:
            True if updated successfully
        """
        for cell in self.cells:
            if cell["x"] == x and cell["y"] == y:
                cell["value"] = value
                cell["color"] = self._get_cell_color(value)
                logger.debug(f"Updated heatmap cell at ({x}, {y}) to value {value}")
                return True

        return False

    def get_cell(self, x: int, y: int) -> Optional[Dict[str, Any]]:
        """Get heatmap cell by coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Cell dictionary or None if not found
        """
        for cell in self.cells:
            if cell["x"] == x and cell["y"] == y:
                return cell

        return None

    def generate_activity_heatmap(
        self,
        start_date: datetime,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Generate activity heatmap data.

        Args:
            start_date: Start date
            days: Number of days

        Returns:
            Generated heatmap data
        """
        heatmap_data = []

        for day in range(days):
            date = start_date + timedelta(days=day)
            # Generate random activity value for demo
            import random
            value = random.randint(0, 100)

            heatmap_data.append({
                "x": day,
                "y": date.weekday(),  # Day of week
                "value": value,
                "label": date.strftime("%Y-%m-%d"),
                "timestamp": date.isoformat(),
            })

        return heatmap_data

    def calculate_statistics(self) -> Dict[str, Any]:
        """Calculate heatmap statistics.

        Returns:
            Statistics dictionary
        """
        if not self.cells:
            return {"cells": 0}

        values = [cell["value"] for cell in self.cells]

        return {
            "cells": len(self.cells),
            "min_value": min(values),
            "max_value": max(values),
            "avg_value": sum(values) / len(values),
            "total_value": sum(values),
            "density": len(self.cells) / (max(cell["x"] for cell in self.cells) + 1) / (max(cell["y"] for cell in self.cells) + 1),
        }

    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate heatmap data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        if not super().validate_data(data):
            return False

        for item in data:
            # Check required fields
            if "x" not in item or "y" not in item or "value" not in item:
                return False

            # Check data types
            try:
                x = int(item["x"])
                y = int(item["y"])
                value = float(item["value"])
                return x >= 0 and y >= 0 and value >= 0
            except (ValueError, TypeError):
                return False

        return True
