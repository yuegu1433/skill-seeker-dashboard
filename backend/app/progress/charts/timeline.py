"""Timeline chart component.

This module provides TimelineComponent for displaying chronological
events and milestones with interactive features.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

from .base import BaseChartComponent, AnimationType

logger = logging.getLogger(__name__)


class TimelineOrientation(Enum):
    """Timeline orientation options."""
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


class TimelineItem:
    """Represents a timeline item."""

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        timestamp: datetime,
        status: str = "default",
        icon: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize timeline item.

        Args:
            id: Item identifier
            title: Item title
            description: Item description
            timestamp: Item timestamp
            status: Item status (default, completed, active, error)
            icon: Optional icon name
            metadata: Additional metadata
        """
        self.id = id
        self.title = title
        self.description = description
        self.timestamp = timestamp
        self.status = status
        self.icon = icon
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "icon": self.icon,
            "metadata": self.metadata,
        }


class TimelineComponent(BaseChartComponent):
    """Timeline component for displaying chronological events."""

    def __init__(
        self,
        component_id: str,
        orientation: TimelineOrientation = TimelineOrientation.HORIZONTAL,
        show_connector: bool = True,
        show_date: bool = True,
        collapsible: bool = False,
        color_scheme: str = "blue",
        **kwargs,
    ):
        """Initialize timeline component.

        Args:
            component_id: Component identifier
            orientation: Timeline orientation
            show_connector: Whether to show connector line
            show_date: Whether to show dates
            collapsible: Whether items are collapsible
            color_scheme: Color scheme name
            **kwargs: Additional base component arguments
        """
        super().__init__(component_id, **kwargs)
        self.orientation = orientation
        self.show_connector = show_connector
        self.show_date = show_date
        self.collapsible = collapsible
        self.color_scheme = color_scheme
        self.items: List[TimelineItem] = []

    async def render(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Render timeline component.

        Args:
            data: Timeline data with events

        Returns:
            Rendered timeline configuration
        """
        # Convert data to TimelineItem objects
        self.items = self._parse_items(data)

        # Sort items by timestamp
        self.items.sort(key=lambda item: item.timestamp)

        config = self.get_config()
        config.update({
            "type": "timeline",
            "orientation": self.orientation.value,
            "show_connector": self.show_connector,
            "show_date": self.show_date,
            "collapsible": self.collapsible,
            "color_scheme": self.color_scheme,
            "items": [item.to_dict() for item in self.items],
            "style": self._get_timeline_style(),
            "animation": self._get_animation_config(),
        })

        self._rendered_at = datetime.utcnow()
        self._is_initialized = True

        logger.debug(f"Rendered timeline {self.component_id} with {len(self.items)} items")
        return config

    async def update(self, new_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update timeline with new data.

        Args:
            new_data: New timeline data

        Returns:
            Updated timeline configuration
        """
        # Store old items for transition animation
        old_items = self.items.copy()

        # Render with new data
        config = await self.render(new_data)

        # Add transition metadata
        config["transition"] = {
            "type": "item_update",
            "old_count": len(old_items),
            "new_count": len(self.items),
            "duration": self.animation_duration,
        }

        return config

    def _parse_items(self, data: List[Dict[str, Any]]) -> List[TimelineItem]:
        """Parse data into TimelineItem objects.

        Args:
            data: Raw timeline data

        Returns:
            List of TimelineItem objects
        """
        items = []

        for item_data in data:
            # Parse timestamp
            timestamp_str = item_data.get("timestamp")
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            elif isinstance(timestamp_str, datetime):
                timestamp = timestamp_str
            else:
                timestamp = datetime.utcnow()

            # Create TimelineItem
            item = TimelineItem(
                id=item_data.get("id", f"item-{len(items)}"),
                title=item_data.get("title", "Untitled"),
                description=item_data.get("description", ""),
                timestamp=timestamp,
                status=item_data.get("status", "default"),
                icon=item_data.get("icon"),
                metadata=item_data.get("metadata", {}),
            )

            items.append(item)

        return items

    def _get_timeline_style(self) -> Dict[str, Any]:
        """Get timeline style configuration.

        Returns:
            Style configuration dictionary
        """
        color_schemes = {
            "blue": {
                "primary": "#3b82f6",
                "secondary": "#93c5fd",
                "completed": "#10b981",
                "active": "#f59e0b",
                "error": "#ef4444",
            },
            "green": {
                "primary": "#10b981",
                "secondary": "#6ee7b7",
                "completed": "#059669",
                "active": "#fbbf24",
                "error": "#dc2626",
            },
            "purple": {
                "primary": "#8b5cf6",
                "secondary": "#c4b5fd",
                "completed": "#7c3aed",
                "active": "#f59e0b",
                "error": "#ef4444",
            },
        }

        colors = color_schemes.get(self.color_scheme, color_schemes["blue"])

        return {
            "colors": colors,
            "connector_width": "2px",
            "dot_size": "16px",
            "font_size": "14px",
            "line_style": "solid",
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
                "type": "fadeInUp",
                "stagger": 100,
                "duration": self.animation_duration,
            },
            AnimationType.SLIDE: {
                "type": "slideInUp",
                "stagger": 100,
                "duration": self.animation_duration,
            },
            AnimationType.SCALE: {
                "type": "scaleIn",
                "stagger": 50,
                "duration": self.animation_duration,
            },
        }

        return animations.get(self.animation, {"enabled": False})

    def add_item(
        self,
        title: str,
        description: str,
        timestamp: datetime,
        status: str = "default",
        icon: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a new timeline item.

        Args:
            title: Item title
            description: Item description
            timestamp: Item timestamp
            status: Item status
            icon: Optional icon
            metadata: Additional metadata

        Returns:
            Created item ID
        """
        item_id = f"item-{len(self.items)}"
        item = TimelineItem(
            id=item_id,
            title=title,
            description=description,
            timestamp=timestamp,
            status=status,
            icon=icon,
            metadata=metadata,
        )

        self.items.append(item)
        logger.debug(f"Added timeline item {item_id}")
        return item_id

    def remove_item(self, item_id: str) -> bool:
        """Remove a timeline item.

        Args:
            item_id: Item ID to remove

        Returns:
            True if removed successfully
        """
        for i, item in enumerate(self.items):
            if item.id == item_id:
                del self.items[i]
                logger.debug(f"Removed timeline item {item_id}")
                return True

        return False

    def update_item(
        self,
        item_id: str,
        **kwargs,
    ) -> bool:
        """Update a timeline item.

        Args:
            item_id: Item ID to update
            **kwargs: Fields to update

        Returns:
            True if updated successfully
        """
        for item in self.items:
            if item.id == item_id:
                for field, value in kwargs.items():
                    if hasattr(item, field):
                        setattr(item, field, value)

                logger.debug(f"Updated timeline item {item_id}")
                return True

        return False

    def get_item(self, item_id: str) -> Optional[TimelineItem]:
        """Get timeline item by ID.

        Args:
            item_id: Item ID

        Returns:
            TimelineItem or None if not found
        """
        for item in self.items:
            if item.id == item_id:
                return item

        return None

    def get_active_item(self) -> Optional[TimelineItem]:
        """Get currently active timeline item.

        Returns:
            Active TimelineItem or None
        """
        for item in self.items:
            if item.status == "active":
                return item

        return None

    def get_completed_items(self) -> List[TimelineItem]:
        """Get completed timeline items.

        Returns:
            List of completed TimelineItem objects
        """
        return [item for item in self.items if item.status == "completed"]

    def mark_item_complete(self, item_id: str) -> bool:
        """Mark an item as completed.

        Args:
            item_id: Item ID

        Returns:
            True if marked successfully
        """
        return self.update_item(item_id, status="completed")

    def mark_item_active(self, item_id: str) -> bool:
        """Mark an item as active.

        Args:
            item_id: Item ID

        Returns:
            True if marked successfully
        """
        return self.update_item(item_id, status="active")

    def get_statistics(self) -> Dict[str, Any]:
        """Get timeline statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self.items)
        completed = len(self.get_completed_items())
        active = len([item for item in self.items if item.status == "active"])
        errors = len([item for item in self.items if item.status == "error"])

        completion_rate = (completed / total * 100) if total > 0 else 0

        return {
            "total_items": total,
            "completed_items": completed,
            "active_items": active,
            "error_items": errors,
            "completion_rate": completion_rate,
            "pending_items": total - completed - active - errors,
        }

    def validate_data(self, data: List[Dict[str, Any]]) -> bool:
        """Validate timeline data.

        Args:
            data: Data to validate

        Returns:
            True if data is valid
        """
        if not super().validate_data(data):
            return False

        for item_data in data:
            # Check required fields
            if "title" not in item_data or "timestamp" not in item_data:
                return False

            # Check timestamp format
            try:
                if isinstance(item_data["timestamp"], str):
                    datetime.fromisoformat(item_data["timestamp"].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                return False

        return True
