"""WebSocket handler for platform operations.

This module provides WebSocketHandler class for handling WebSocket
connections and routing messages for platform operations.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .websocket_manager import WebSocketManager
from ..schemas.websocket_messages import (
    ConnectionRequest,
    MessageType,
)
from ..database import get_db_session


logger = logging.getLogger(__name__)

# Global WebSocket manager instance
_websocket_manager: Optional[WebSocketManager] = None


def get_websocket_manager(db: Session = None) -> WebSocketManager:
    """Get WebSocket manager instance.

    Args:
        db: Optional database session

    Returns:
        WebSocketManager instance
    """
    global _websocket_manager

    if _websocket_manager is None:
        _websocket_manager = WebSocketManager(db)
        # Start the manager
        asyncio.create_task(_websocket_manager.start())

    return _websocket_manager


async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db_session),
    user_id: Optional[str] = Query(None, description="User ID"),
    connection_type: str = Query("platform", description="Connection type"),
    platform_id: Optional[str] = Query(None, description="Platform ID"),
    skill_id: Optional[str] = Query(None, description="Skill ID"),
    subscriptions: str = Query("", description="Comma-separated subscriptions"),
):
    """WebSocket endpoint for platform operations.

    Args:
        websocket: WebSocket instance
        db: Database session
        user_id: Optional user ID
        connection_type: Connection type
        platform_id: Optional platform ID
        skill_id: Optional skill ID
        subscriptions: Comma-separated subscriptions
    """
    # Parse subscriptions
    subscription_list = [s.strip() for s in subscriptions.split(",") if s.strip()]

    # Create connection request
    connection_request = ConnectionRequest(
        user_id=user_id,
        connection_type=connection_type,
        subscriptions=subscription_list,
        platform_id=platform_id,
        skill_id=skill_id,
        metadata={
            'query_params': {
                'user_id': user_id,
                'connection_type': connection_type,
                'platform_id': platform_id,
                'skill_id': skill_id,
                'subscriptions': subscription_list,
            }
        },
    )

    # Get WebSocket manager
    ws_manager = get_websocket_manager(db)

    # Handle connection
    connection_id = await ws_manager.handle_connection(websocket, connection_request)

    if not connection_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        # Keep connection alive and handle messages
        while True:
            try:
                # Receive message with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0  # 30 second timeout
                )

                # Parse message
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from connection {connection_id}: {str(e)}")
                    await ws_manager.handle_message(
                        connection_id,
                        {
                            'error': 'invalid_json',
                            'message': 'Message must be valid JSON'
                        }
                    )
                    continue

                # Handle message
                await ws_manager.handle_message(connection_id, message_data)

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.send_json({
                        'type': 'ping',
                        'timestamp': '2024-01-01T00:00:00Z'
                    })
                except Exception:
                    # Connection is dead
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {str(e)}")
    finally:
        # Clean up connection
        await ws_manager.handle_disconnect(connection_id)


class WebSocketHandler:
    """Handler for WebSocket operations."""

    def __init__(self, db_session: Session):
        """Initialize WebSocketHandler.

        Args:
            db_session: Database session
        """
        self.db = db_session
        self.ws_manager = get_websocket_manager(db_session)

    # Platform-specific message handlers
    async def notify_platform_status_change(
        self,
        platform_id: str,
        old_status: bool,
        new_status: bool,
        user_id: Optional[str] = None
    ):
        """Notify about platform status change.

        Args:
            platform_id: Platform ID
            old_status: Previous status
            new_status: New status
            user_id: Optional user ID to notify
        """
        status_data = {
            'platform_id': platform_id,
            'old_status': old_status,
            'new_status': new_status,
            'changed_at': '2024-01-01T00:00:00Z',
        }

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'platform_status_change',
                    'title': 'Platform Status Changed',
                    'data': status_data,
                }
            )
        else:
            await self.ws_manager.send_platform_status_update(
                platform_id,
                status_data
            )

    async def notify_platform_health_change(
        self,
        platform_id: str,
        is_healthy: bool,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Notify about platform health change.

        Args:
            platform_id: Platform ID
            is_healthy: Health status
            error_message: Optional error message
            user_id: Optional user ID to notify
        """
        status_data = {
            'platform_id': platform_id,
            'is_healthy': is_healthy,
            'error_message': error_message,
            'checked_at': '2024-01-01T00:00:00Z',
        }

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'platform_health_change',
                    'title': 'Platform Health Alert',
                    'data': status_data,
                }
            )
        else:
            await self.ws_manager.send_platform_status_update(
                platform_id,
                status_data
            )

    # Deployment-specific message handlers
    async def notify_deployment_started(
        self,
        deployment_id: str,
        skill_id: str,
        platform_id: str,
        skill_name: str,
        platform_name: str,
        user_id: Optional[str] = None
    ):
        """Notify about deployment start.

        Args:
            deployment_id: Deployment ID
            skill_id: Skill ID
            platform_id: Platform ID
            skill_name: Skill name
            platform_name: Platform name
            user_id: Optional user ID to notify
        """
        update_data = {
            'deployment_id': deployment_id,
            'skill_id': skill_id,
            'platform_id': platform_id,
            'skill_name': skill_name,
            'platform_name': platform_name,
            'status': 'deploying',
            'progress': 0,
            'started_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_deployment_update(
            deployment_id,
            skill_id,
            platform_id,
            update_data
        )

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'deployment_started',
                    'title': 'Deployment Started',
                    'message': f'Deployment of {skill_name} to {platform_name} has started',
                    'data': update_data,
                }
            )

    async def notify_deployment_progress(
        self,
        deployment_id: str,
        skill_id: str,
        platform_id: str,
        progress: float,
        current_step: str,
        user_id: Optional[str] = None
    ):
        """Notify about deployment progress.

        Args:
            deployment_id: Deployment ID
            skill_id: Skill ID
            platform_id: Platform ID
            progress: Progress percentage
            current_step: Current step description
            user_id: Optional user ID to notify
        """
        update_data = {
            'deployment_id': deployment_id,
            'skill_id': skill_id,
            'platform_id': platform_id,
            'status': 'deploying',
            'progress': progress,
            'current_step': current_step,
            'updated_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_deployment_update(
            deployment_id,
            skill_id,
            platform_id,
            update_data
        )

    async def notify_deployment_completed(
        self,
        deployment_id: str,
        skill_id: str,
        platform_id: str,
        skill_name: str,
        platform_name: str,
        success: bool,
        error_message: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Notify about deployment completion.

        Args:
            deployment_id: Deployment ID
            skill_id: Skill ID
            platform_id: Platform ID
            skill_name: Skill name
            platform_name: Platform name
            success: Whether deployment was successful
            error_message: Optional error message
            user_id: Optional user ID to notify
        """
        update_data = {
            'deployment_id': deployment_id,
            'skill_id': skill_id,
            'platform_id': platform_id,
            'skill_name': skill_name,
            'platform_name': platform_name,
            'status': 'success' if success else 'failed',
            'success': success,
            'error_message': error_message,
            'completed_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_deployment_update(
            deployment_id,
            skill_id,
            platform_id,
            update_data
        )

        if user_id:
            notification_type = 'deployment_success' if success else 'deployment_failure'
            title = 'Deployment Successful' if success else 'Deployment Failed'
            message = (
                f'Deployment of {skill_name} to {platform_name} completed successfully'
                if success
                else f'Deployment of {skill_name} to {platform_name} failed: {error_message}'
            )

            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': notification_type,
                    'title': title,
                    'message': message,
                    'data': update_data,
                }
            )

    async def notify_deployment_retry(
        self,
        deployment_id: str,
        skill_id: str,
        platform_id: str,
        retry_count: int,
        max_retries: int,
        user_id: Optional[str] = None
    ):
        """Notify about deployment retry.

        Args:
            deployment_id: Deployment ID
            skill_id: Skill ID
            platform_id: Platform ID
            retry_count: Current retry count
            max_retries: Maximum retries
            user_id: Optional user ID to notify
        """
        update_data = {
            'deployment_id': deployment_id,
            'skill_id': skill_id,
            'platform_id': platform_id,
            'status': 'pending',
            'retry_count': retry_count,
            'max_retries': max_retries,
            'retry_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_deployment_update(
            deployment_id,
            skill_id,
            platform_id,
            update_data
        )

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'deployment_retry',
                    'title': 'Deployment Retry',
                    'message': f'Deployment retry attempt {retry_count}/{max_retries}',
                    'data': update_data,
                }
            )

    # Compatibility check message handlers
    async def notify_compatibility_check_started(
        self,
        check_id: str,
        skill_id: str,
        platforms: List[str],
        user_id: Optional[str] = None
    ):
        """Notify about compatibility check start.

        Args:
            check_id: Compatibility check ID
            skill_id: Skill ID
            platforms: List of platforms
            user_id: Optional user ID to notify
        """
        update_data = {
            'check_id': check_id,
            'skill_id': skill_id,
            'platforms': platforms,
            'status': 'running',
            'progress': 0,
            'started_at': '2024-01-01T00:00:00Z',
        }

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'compatibility_check_started',
                    'title': 'Compatibility Check Started',
                    'message': f'Compatibility check started for {len(platforms)} platforms',
                    'data': update_data,
                }
            )

    async def notify_compatibility_check_progress(
        self,
        check_id: str,
        skill_id: str,
        progress: float,
        current_platform: str,
        platforms_completed: List[str],
        platforms_remaining: List[str],
        user_id: Optional[str] = None
    ):
        """Notify about compatibility check progress.

        Args:
            check_id: Compatibility check ID
            skill_id: Skill ID
            progress: Progress percentage
            current_platform: Currently checking platform
            platforms_completed: Completed platforms
            platforms_remaining: Remaining platforms
            user_id: Optional user ID to notify
        """
        update_data = {
            'check_id': check_id,
            'skill_id': skill_id,
            'progress': progress,
            'current_platform': current_platform,
            'platforms_completed': platforms_completed,
            'platforms_remaining': platforms_remaining,
            'updated_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_compatibility_update(
            check_id,
            skill_id,
            update_data
        )

    async def notify_compatibility_check_completed(
        self,
        check_id: str,
        skill_id: str,
        overall_compatible: bool,
        compatibility_score: float,
        platforms_compatible: List[str],
        platforms_incompatible: List[str],
        total_issues: int,
        critical_issues: int,
        user_id: Optional[str] = None
    ):
        """Notify about compatibility check completion.

        Args:
            check_id: Compatibility check ID
            skill_id: Skill ID
            overall_compatible: Overall compatibility status
            compatibility_score: Compatibility score
            platforms_compatible: Compatible platforms
            platforms_incompatible: Incompatible platforms
            total_issues: Total issues found
            critical_issues: Critical issues count
            user_id: Optional user ID to notify
        """
        update_data = {
            'check_id': check_id,
            'skill_id': skill_id,
            'overall_compatible': overall_compatible,
            'compatibility_score': compatibility_score,
            'platforms_compatible': platforms_compatible,
            'platforms_incompatible': platforms_incompatible,
            'total_issues': total_issues,
            'critical_issues': critical_issues,
            'completed_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_compatibility_update(
            check_id,
            skill_id,
            update_data
        )

        if user_id:
            title = 'Compatibility Check Completed'
            if overall_compatible:
                message = f'Your skill is compatible with {len(platforms_compatible)} platforms'
            else:
                message = (
                    f'Your skill has compatibility issues with '
                    f'{len(platforms_incompatible)} platforms'
                )

            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'compatibility_check_completed',
                    'title': title,
                    'message': message,
                    'data': update_data,
                }
            )

    # Bulk operation message handlers
    async def notify_bulk_operation_started(
        self,
        operation_id: str,
        operation_type: str,
        total_items: int,
        user_id: Optional[str] = None
    ):
        """Notify about bulk operation start.

        Args:
            operation_id: Operation ID
            operation_type: Type of operation
            total_items: Total items to process
            user_id: Optional user ID to notify
        """
        update_data = {
            'operation_id': operation_id,
            'operation_type': operation_type,
            'total_items': total_items,
            'processed_items': 0,
            'successful_items': 0,
            'failed_items': 0,
            'progress_percentage': 0,
            'started_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_bulk_operation_update(
            operation_id,
            update_data
        )

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'bulk_operation_started',
                    'title': 'Bulk Operation Started',
                    'message': f'Processing {total_items} items',
                    'data': update_data,
                }
            )

    async def notify_bulk_operation_progress(
        self,
        operation_id: str,
        processed_items: int,
        successful_items: int,
        failed_items: int,
        progress_percentage: float,
        current_item: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Notify about bulk operation progress.

        Args:
            operation_id: Operation ID
            processed_items: Number of processed items
            successful_items: Number of successful items
            failed_items: Number of failed items
            progress_percentage: Progress percentage
            current_item: Currently processing item
            user_id: Optional user ID to notify
        """
        update_data = {
            'operation_id': operation_id,
            'processed_items': processed_items,
            'successful_items': successful_items,
            'failed_items': failed_items,
            'progress_percentage': progress_percentage,
            'current_item': current_item,
            'updated_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_bulk_operation_update(
            operation_id,
            update_data
        )

    async def notify_bulk_operation_completed(
        self,
        operation_id: str,
        total_items: int,
        successful_items: int,
        failed_items: int,
        user_id: Optional[str] = None
    ):
        """Notify about bulk operation completion.

        Args:
            operation_id: Operation ID
            total_items: Total items
            successful_items: Successful items
            failed_items: Failed items
            user_id: Optional user ID to notify
        """
        update_data = {
            'operation_id': operation_id,
            'total_items': total_items,
            'successful_items': successful_items,
            'failed_items': failed_items,
            'progress_percentage': 100,
            'completed_at': '2024-01-01T00:00:00Z',
        }

        await self.ws_manager.send_bulk_operation_update(
            operation_id,
            update_data
        )

        if user_id:
            await self.ws_manager.send_notification(
                user_id,
                {
                    'type': 'bulk_operation_completed',
                    'title': 'Bulk Operation Completed',
                    'message': f'Processed {total_items} items: {successful_items} successful, {failed_items} failed',
                    'data': update_data,
                }
            )

    # Utility methods
    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket handler statistics.

        Returns:
            Statistics dictionary
        """
        return self.ws_manager.get_statistics()

    async def broadcast_message(
        self,
        message: Dict[str, Any],
        user_id: Optional[str] = None,
        platform_id: Optional[str] = None,
        skill_id: Optional[str] = None
    ) -> int:
        """Broadcast message to connections.

        Args:
            message: Message to broadcast
            user_id: Optional user ID
            platform_id: Optional platform ID
            skill_id: Optional skill ID

        Returns:
            Number of messages sent
        """
        if user_id:
            return await self.ws_manager.connection_manager.send_user_message(
                message,
                user_id
            )
        elif platform_id:
            return await self.ws_manager.connection_manager.send_platform_message(
                message,
                platform_id
            )
        elif skill_id:
            return await self.ws_manager.connection_manager.send_skill_message(
                message,
                skill_id
            )
        else:
            return await self.ws_manager.connection_manager.broadcast_message(message)