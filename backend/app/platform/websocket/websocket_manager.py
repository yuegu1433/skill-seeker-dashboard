"""WebSocket manager for real-time platform communications.

This module provides WebSocketManager class for handling real-time
communication related to platform operations, deployments, and compatibility checks.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Union
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from ..schemas.websocket_messages import (
    WebSocketMessage,
    MessageType,
    MessagePriority,
    ConnectionRequest,
    ConnectionResponse,
    HeartbeatMessage,
    ErrorMessage,
)
from ..utils.validators import validate_pagination_params


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        """Initialize ConnectionManager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> set of connection_ids
        self.platform_connections: Dict[str, Set[str]] = {}  # platform_id -> set of connection_ids
        self.skill_connections: Dict[str, Set[str]] = {}  # skill_id -> set of connection_ids

    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """Accept WebSocket connection.

        Args:
            websocket: WebSocket instance
            connection_id: Unique connection ID
            metadata: Connection metadata

        Returns:
            True if connected successfully
        """
        try:
            await websocket.accept()
            self.active_connections[connection_id] = websocket
            self.connection_metadata[connection_id] = {
                **metadata,
                'connected_at': datetime.utcnow(),
                'last_heartbeat': datetime.utcnow(),
                'message_count': 0,
            }

            # Track connections by user
            user_id = metadata.get('user_id')
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)

            # Track connections by platform
            platform_id = metadata.get('platform_id')
            if platform_id:
                if platform_id not in self.platform_connections:
                    self.platform_connections[platform_id] = set()
                self.platform_connections[platform_id].add(connection_id)

            # Track connections by skill
            skill_id = metadata.get('skill_id')
            if skill_id:
                if skill_id not in self.skill_connections:
                    self.skill_connections[skill_id] = set()
                self.skill_connections[skill_id].add(connection_id)

            logger.info(f"WebSocket connected: {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection {connection_id}: {str(e)}")
            return False

    def disconnect(self, connection_id: str):
        """Remove WebSocket connection.

        Args:
            connection_id: Connection ID to remove
        """
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        if connection_id in self.connection_metadata:
            metadata = self.connection_metadata[connection_id]

            # Remove from user connections
            user_id = metadata.get('user_id')
            if user_id and user_id in self.user_connections:
                self.user_connections[user_id].discard(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]

            # Remove from platform connections
            platform_id = metadata.get('platform_id')
            if platform_id and platform_id in self.platform_connections:
                self.platform_connections[platform_id].discard(connection_id)
                if not self.platform_connections[platform_id]:
                    del self.platform_connections[platform_id]

            # Remove from skill connections
            skill_id = metadata.get('skill_id')
            if skill_id and skill_id in self.skill_connections:
                self.skill_connections[skill_id].discard(connection_id)
                if not self.skill_connections[skill_id]:
                    del self.skill_connections[skill_id]

            del self.connection_metadata[connection_id]

        logger.info(f"WebSocket disconnected: {connection_id}")

    async def send_personal_message(
        self,
        message: Dict[str, Any],
        connection_id: str
    ) -> bool:
        """Send message to specific connection.

        Args:
            message: Message to send
            connection_id: Target connection ID

        Returns:
            True if sent successfully
        """
        if connection_id not in self.active_connections:
            return False

        try:
            websocket = self.active_connections[connection_id]
            await websocket.send_json(message)

            # Update message count
            if connection_id in self.connection_metadata:
                self.connection_metadata[connection_id]['message_count'] += 1

            return True

        except Exception as e:
            logger.error(f"Failed to send message to {connection_id}: {str(e)}")
            self.disconnect(connection_id)
            return False

    async def send_user_message(
        self,
        message: Dict[str, Any],
        user_id: str
    ) -> int:
        """Send message to all connections for a user.

        Args:
            message: Message to send
            user_id: Target user ID

        Returns:
            Number of messages sent
        """
        if user_id not in self.user_connections:
            return 0

        sent_count = 0
        connection_ids = list(self.user_connections[user_id])  # Create copy to avoid modification during iteration

        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1

        return sent_count

    async def send_platform_message(
        self,
        message: Dict[str, Any],
        platform_id: str
    ) -> int:
        """Send message to all connections for a platform.

        Args:
            message: Message to send
            platform_id: Target platform ID

        Returns:
            Number of messages sent
        """
        if platform_id not in self.platform_connections:
            return 0

        sent_count = 0
        connection_ids = list(self.platform_connections[platform_id])

        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1

        return sent_count

    async def send_skill_message(
        self,
        message: Dict[str, Any],
        skill_id: str
    ) -> int:
        """Send message to all connections for a skill.

        Args:
            message: Message to send
            skill_id: Target skill ID

        Returns:
            Number of messages sent
        """
        if skill_id not in self.skill_connections:
            return 0

        sent_count = 0
        connection_ids = list(self.skill_connections[skill_id])

        for connection_id in connection_ids:
            if await self.send_personal_message(message, connection_id):
                sent_count += 1

        return sent_count

    async def broadcast_message(
        self,
        message: Dict[str, Any],
        exclude_connection_ids: Optional[Set[str]] = None
    ) -> int:
        """Broadcast message to all active connections.

        Args:
            message: Message to broadcast
            exclude_connection_ids: Connection IDs to exclude

        Returns:
            Number of messages sent
        """
        exclude_connection_ids = exclude_connection_ids or set()
        sent_count = 0
        connection_ids = list(self.active_connections.keys())

        for connection_id in connection_ids:
            if connection_id not in exclude_connection_ids:
                if await self.send_personal_message(message, connection_id):
                    sent_count += 1

        return sent_count

    def get_connection_count(self) -> int:
        """Get total number of active connections.

        Returns:
            Number of active connections
        """
        return len(self.active_connections)

    def get_user_connection_count(self, user_id: str) -> int:
        """Get number of connections for a user.

        Args:
            user_id: User ID

        Returns:
            Number of connections
        """
        return len(self.user_connections.get(user_id, set()))

    def get_platform_connection_count(self, platform_id: str) -> int:
        """Get number of connections for a platform.

        Args:
            platform_id: Platform ID

        Returns:
            Number of connections
        """
        return len(self.platform_connections.get(platform_id, set()))

    def get_skill_connection_count(self, skill_id: str) -> int:
        """Get number of connections for a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Number of connections
        """
        return len(self.skill_connections.get(skill_id, set()))

    def get_connection_metadata(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a connection.

        Args:
            connection_id: Connection ID

        Returns:
            Connection metadata or None
        """
        return self.connection_metadata.get(connection_id)


class WebSocketManager:
    """Manager for WebSocket operations.

    Handles WebSocket connections, message routing, and real-time
    communication for platform operations.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """Initialize WebSocketManager.

        Args:
            db_session: Optional database session
        """
        self.db = db_session
        self.connection_manager = ConnectionManager()
        self.heartbeat_interval = 30  # seconds
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._tasks: List[asyncio.Task] = []

    async def start(self):
        """Start WebSocket manager."""
        if self.running:
            return

        self.running = True
        self._tasks = [
            asyncio.create_task(self._message_processor()),
            asyncio.create_task(self._heartbeat_checker()),
        ]

        logger.info("WebSocket manager started")

    async def stop(self):
        """Stop WebSocket manager."""
        self.running = False

        # Cancel all tasks
        for task in self._tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Disconnect all connections
        connection_ids = list(self.connection_manager.active_connections.keys())
        for connection_id in connection_ids:
            self.connection_manager.disconnect(connection_id)

        logger.info("WebSocket manager stopped")

    async def handle_connection(
        self,
        websocket: WebSocket,
        connection_request: ConnectionRequest
    ) -> Optional[str]:
        """Handle new WebSocket connection.

        Args:
            websocket: WebSocket instance
            connection_request: Connection request data

        Returns:
            Connection ID if successful, None otherwise
        """
        connection_id = str(uuid4())

        metadata = {
            'connection_id': connection_id,
            'user_id': connection_request.user_id,
            'connection_type': connection_request.connection_type,
            'platform_id': connection_request.platform_id,
            'skill_id': connection_request.skill_id,
            'subscriptions': connection_request.subscriptions,
            'metadata': connection_request.metadata,
        }

        success = await self.connection_manager.connect(websocket, connection_id, metadata)
        if not success:
            return None

        # Send connection response
        response = ConnectionResponse(
            connection_id=connection_id,
            status='connected',
            server_info={
                'server': 'platform-websocket',
                'version': '1.0',
                'timestamp': datetime.utcnow().isoformat(),
            },
            subscribed_topics=connection_request.subscriptions,
            heartbeat_interval=self.heartbeat_interval,
            rate_limits={
                'messages_per_minute': 60,
                'messages_per_hour': 1000,
            },
        )

        await self.connection_manager.send_personal_message(
            response.dict(),
            connection_id
        )

        return connection_id

    async def handle_disconnect(self, connection_id: str):
        """Handle WebSocket disconnection.

        Args:
            connection_id: Connection ID
        """
        self.connection_manager.disconnect(connection_id)

    async def handle_message(
        self,
        connection_id: str,
        message: Dict[str, Any]
    ) -> bool:
        """Handle incoming WebSocket message.

        Args:
            connection_id: Connection ID
            message: Received message

        Returns:
            True if message was processed successfully
        """
        try:
            # Validate message
            ws_message = WebSocketMessage(**message)

            # Update heartbeat
            metadata = self.connection_manager.get_connection_metadata(connection_id)
            if metadata:
                metadata['last_heartbeat'] = datetime.utcnow()

            # Add to message queue for processing
            await self.message_queue.put({
                'connection_id': connection_id,
                'message': ws_message,
                'metadata': metadata,
            })

            return True

        except Exception as e:
            logger.error(f"Failed to handle message from {connection_id}: {str(e)}")

            # Send error message
            error_msg = ErrorMessage(
                error_code='INVALID_MESSAGE',
                error_message=f'Invalid message format: {str(e)}',
                error_type='validation',
                severity='high',
                details={'original_message': message},
            )

            await self.connection_manager.send_personal_message(
                error_msg.dict(),
                connection_id
            )

            return False

    async def send_platform_status_update(
        self,
        platform_id: str,
        status_data: Dict[str, Any]
    ) -> int:
        """Send platform status update.

        Args:
            platform_id: Platform ID
            status_data: Status data

        Returns:
            Number of messages sent
        """
        message = WebSocketMessage(
            message_id=str(uuid4()),
            message_type=MessageType.PLATFORM_STATUS_UPDATE,
            timestamp=datetime.utcnow(),
            priority=MessagePriority.NORMAL,
            source='platform-manager',
            data={
                'platform_id': platform_id,
                'status': status_data,
            },
        )

        return await self.connection_manager.send_platform_message(
            message.dict(),
            platform_id
        )

    async def send_deployment_update(
        self,
        deployment_id: str,
        skill_id: str,
        platform_id: str,
        update_data: Dict[str, Any]
    ) -> int:
        """Send deployment status update.

        Args:
            deployment_id: Deployment ID
            skill_id: Skill ID
            platform_id: Platform ID
            update_data: Update data

        Returns:
            Number of messages sent
        """
        message = WebSocketMessage(
            message_id=str(uuid4()),
            message_type=MessageType.DEPLOYMENT_STATUS_UPDATE,
            timestamp=datetime.utcnow(),
            priority=MessagePriority.HIGH,
            source='deployment-manager',
            data={
                'deployment_id': deployment_id,
                'skill_id': skill_id,
                'platform_id': platform_id,
                'update': update_data,
            },
        )

        # Send to both platform and skill connections
        sent_count = 0

        # Send to platform connections
        sent_count += await self.connection_manager.send_platform_message(
            message.dict(),
            platform_id
        )

        # Send to skill connections
        sent_count += await self.connection_manager.send_skill_message(
            message.dict(),
            skill_id
        )

        return sent_count

    async def send_compatibility_update(
        self,
        check_id: str,
        skill_id: str,
        update_data: Dict[str, Any]
    ) -> int:
        """Send compatibility check update.

        Args:
            check_id: Compatibility check ID
            skill_id: Skill ID
            update_data: Update data

        Returns:
            Number of messages sent
        """
        message = WebSocketMessage(
            message_id=str(uuid4()),
            message_type=MessageType.COMPATIBILITY_CHECK_COMPLETED,
            timestamp=datetime.utcnow(),
            priority=MessagePriority.NORMAL,
            source='compatibility-manager',
            data={
                'check_id': check_id,
                'skill_id': skill_id,
                'result': update_data,
            },
        )

        return await self.connection_manager.send_skill_message(
            message.dict(),
            skill_id
        )

    async def send_notification(
        self,
        user_id: Optional[str],
        notification_data: Dict[str, Any]
    ) -> int:
        """Send notification to user.

        Args:
            user_id: Optional user ID
            notification_data: Notification data

        Returns:
            Number of messages sent
        """
        message = WebSocketMessage(
            message_id=str(uuid4()),
            message_type=MessageType.NOTIFICATION_SENT,
            timestamp=datetime.utcnow(),
            priority=MessagePriority.NORMAL,
            source='notification-manager',
            data=notification_data,
        )

        if user_id:
            return await self.connection_manager.send_user_message(
                message.dict(),
                user_id
            )
        else:
            # Broadcast to all connections
            return await self.connection_manager.broadcast_message(message.dict())

    async def send_bulk_operation_update(
        self,
        operation_id: str,
        update_data: Dict[str, Any]
    ) -> int:
        """Send bulk operation update.

        Args:
            operation_id: Operation ID
            update_data: Update data

        Returns:
            Number of messages sent
        """
        message = WebSocketMessage(
            message_id=str(uuid4()),
            message_type=MessageType.BULK_OPERATION_UPDATE,
            timestamp=datetime.utcnow(),
            priority=MessagePriority.NORMAL,
            source='bulk-operation-manager',
            data={
                'operation_id': operation_id,
                'update': update_data,
            },
        )

        # Broadcast to all connections
        return await self.connection_manager.broadcast_message(message.dict())

    async def _message_processor(self):
        """Process incoming messages from queue."""
        while self.running:
            try:
                # Get message from queue with timeout
                item = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                connection_id = item['connection_id']
                message = item['message']
                metadata = item['metadata']

                # Process message based on type
                await self._process_message(connection_id, message, metadata)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in message processor: {str(e)}")

    async def _process_message(
        self,
        connection_id: str,
        message: WebSocketMessage,
        metadata: Dict[str, Any]
    ):
        """Process individual message.

        Args:
            connection_id: Connection ID
            message: WebSocket message
            metadata: Connection metadata
        """
        try:
            if message.message_type == MessageType.HEARTBEAT:
                # Respond to heartbeat
                response = HeartbeatMessage(
                    connection_id=connection_id,
                    server_time=datetime.utcnow(),
                    client_time=message.timestamp,
                )

                await self.connection_manager.send_personal_message(
                    response.dict(),
                    connection_id
                )

            elif message.message_type == MessageType.ACKNOWLEDGMENT:
                # Handle acknowledgment (for delivery confirmation)
                pass

            else:
                # Log unhandled message type
                logger.debug(
                    f"Received unhandled message type: {message.message_type} "
                    f"from connection: {connection_id}"
                )

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")

    async def _heartbeat_checker(self):
        """Check heartbeat for all connections."""
        while self.running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                # Check all connections
                expired_connections = []
                current_time = datetime.utcnow()

                for connection_id, metadata in self.connection_manager.connection_metadata.items():
                    last_heartbeat = metadata.get('last_heartbeat')
                    if last_heartbeat:
                        time_diff = (current_time - last_heartbeat).total_seconds()
                        if time_diff > self.heartbeat_interval * 3:
                            # Connection heartbeat expired
                            expired_connections.append(connection_id)

                # Disconnect expired connections
                for connection_id in expired_connections:
                    logger.warning(f"Disconnecting expired connection: {connection_id}")
                    self.connection_manager.disconnect(connection_id)

            except Exception as e:
                logger.error(f"Error in heartbeat checker: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics.

        Returns:
            Statistics dictionary
        """
        return {
            'total_connections': self.connection_manager.get_connection_count(),
            'user_connections': len(self.connection_manager.user_connections),
            'platform_connections': len(self.connection_manager.platform_connections),
            'skill_connections': len(self.connection_manager.skill_connections),
            'queue_size': self.message_queue.qsize(),
            'running': self.running,
        }