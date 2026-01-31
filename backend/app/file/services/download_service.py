"""File Download Service.

This module provides comprehensive file download capabilities including download
processing, streaming transmission, rate limiting, and resumable downloads.
"""

import asyncio
import logging
import hashlib
import time
from typing import Dict, List, Optional, Tuple, Any, BinaryIO, Callable, AsyncGenerator
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, field
import json
import io

from sqlalchemy.ext.asyncio import AsyncSession

# Import managers and schemas
from app.file.manager import FileManager
from app.file.models.file import File
from app.file.schemas.file_operations import FileResponse

logger = logging.getLogger(__name__)


class DownloadStatus(str, Enum):
    """Download status enumeration."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadChunk:
    """Download chunk information."""

    chunk_id: str
    start_byte: int
    end_byte: int
    size: int
    data: Optional[bytes] = None
    downloaded_at: Optional[datetime] = None
    verified: bool = False
    hash: Optional[str] = None


@dataclass
class DownloadProgress:
    """Download progress information."""

    download_id: str
    status: DownloadStatus
    total_size: int
    downloaded_size: int
    chunk_size: int
    total_chunks: int
    downloaded_chunks: int
    verified_chunks: int
    progress_percentage: float
    download_speed: float  # bytes per second
    estimated_time_remaining: float  # seconds
    start_time: datetime
    last_update: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "download_id": self.download_id,
            "status": self.status.value,
            "total_size": self.total_size,
            "downloaded_size": self.downloaded_size,
            "chunk_size": self.chunk_size,
            "total_chunks": self.total_chunks,
            "downloaded_chunks": self.downloaded_chunks,
            "verified_chunks": self.verified_chunks,
            "progress_percentage": round(self.progress_percentage, 2),
            "download_speed": round(self.download_speed, 2),
            "estimated_time_remaining": round(self.estimated_time_remaining, 2),
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat(),
        }


@dataclass
class DownloadSession:
    """Download session information."""

    session_id: str
    file_id: str
    filename: str
    total_size: int
    chunk_size: int
    total_chunks: int
    status: DownloadStatus
    chunks: List[DownloadChunk] = field(default_factory=list)
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    download_speed_limit: Optional[float] = None  # bytes per second

    def update_progress(self):
        """Update download progress."""
        self.updated_at = datetime.utcnow()


@dataclass
class DownloadResult:
    """Download result information."""

    success: bool
    file_data: Optional[bytes] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: int = 0
    download_duration: float = 0.0
    chunks_downloaded: int = 0
    verification_status: str = "not_verified"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class RateLimiter:
    """Rate limiter for download speed control."""

    def __init__(self, max_rate: Optional[float] = None):
        """Initialize rate limiter.

        Args:
            max_rate: Maximum download rate in bytes per second
        """
        self.max_rate = max_rate  # bytes per second
        self.tokens = max_rate if max_rate else float('inf')
        self.last_update = time.time()

    async def acquire(self, amount: int) -> bool:
        """Acquire tokens for downloading data.

        Args:
            amount: Amount of data to download in bytes

        Returns:
            True if tokens acquired successfully
        """
        if self.max_rate is None or self.max_rate == float('inf'):
            return True

        now = time.time()
        elapsed = now - self.last_update

        # Add tokens based on elapsed time
        self.tokens += elapsed * self.max_rate
        self.last_update = now

        # Cap tokens at max_rate
        self.tokens = min(self.tokens, self.max_rate)

        # Check if enough tokens available
        if self.tokens >= amount:
            self.tokens -= amount
            return True

        return False

    async def wait_for_tokens(self, amount: int) -> bool:
        """Wait for tokens to become available.

        Args:
            amount: Amount of data to download in bytes

        Returns:
            True if tokens acquired
        """
        if self.max_rate is None or self.max_rate == float('inf'):
            return True

        if self.tokens >= amount:
            self.tokens -= amount
            return True

        # Calculate wait time
        wait_time = (amount - self.tokens) / self.max_rate
        await asyncio.sleep(wait_time)

        # Reset tokens
        self.tokens = 0
        self.last_update = time.time()

        return True


class DownloadService:
    """File download service."""

    def __init__(
        self,
        db_session: AsyncSession,
        default_chunk_size: int = 1024 * 1024,  # 1 MB
        max_concurrent_downloads: int = 10,
        default_rate_limit: Optional[float] = None,  # bytes per second
    ):
        """Initialize download service.

        Args:
            db_session: Database session
            default_chunk_size: Default chunk size in bytes
            max_concurrent_downloads: Maximum concurrent downloads
            default_rate_limit: Default rate limit in bytes per second
        """
        self.db = db_session
        self.file_manager = FileManager(db_session)

        self.default_chunk_size = default_chunk_size
        self.max_concurrent_downloads = max_concurrent_downloads
        self.default_rate_limit = default_rate_limit

        # Active download sessions
        self.download_sessions: Dict[str, DownloadSession] = {}

        # Download statistics
        self.download_stats = {
            "total_downloads": 0,
            "completed_downloads": 0,
            "failed_downloads": 0,
            "total_bytes_downloaded": 0,
            "average_download_speed": 0.0,
        }

    async def create_download_session(
        self,
        file_id: str,
        chunk_size: Optional[int] = None,
        rate_limit: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DownloadSession:
        """Create a new download session.

        Args:
            file_id: File ID to download
            chunk_size: Chunk size in bytes (optional)
            rate_limit: Download rate limit in bytes per second (optional)
            metadata: Additional metadata

        Returns:
            DownloadSession instance
        """
        # Get file information
        file_response = await self.file_manager.get_file(UUID(file_id), "system")
        if not file_response:
            raise ValueError(f"File not found: {file_id}")

        # Determine chunk size
        if chunk_size is None:
            chunk_size = self.default_chunk_size

        # Calculate total chunks
        total_chunks = (file_response.size + chunk_size - 1) // chunk_size

        # Create session
        session = DownloadSession(
            session_id=str(uuid4()),
            file_id=file_id,
            filename=file_response.name,
            total_size=file_response.size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            status=DownloadStatus.PENDING,
            file_hash=None,  # Will be calculated during download
            download_speed_limit=rate_limit or self.default_rate_limit,
            metadata=metadata or {},
        )

        # Store session
        self.download_sessions[session.session_id] = session

        # Update stats
        self.download_stats["total_downloads"] += 1

        logger.info(f"Created download session {session.session_id} for file {file_id}")
        return session

    async def download_file(
        self,
        session_id: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> DownloadResult:
        """Download a complete file.

        Args:
            session_id: Download session ID
            progress_callback: Progress callback function

        Returns:
            DownloadResult instance
        """
        session = self._get_session(session_id)
        if not session:
            return DownloadResult(success=False, error_message="Download session not found")

        try:
            session.status = DownloadStatus.DOWNLOADING
            session.update_progress()

            # Get file information
            file_response = await self.file_manager.get_file(UUID(session.file_id), "system")
            if not file_response:
                session.status = DownloadStatus.FAILED
                return DownloadResult(success=False, error_message="File not found")

            # Simulate file download (in real implementation, this would stream from storage)
            file_data = b"0" * session.total_size  # Mock file data

            # Calculate file hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            session.file_hash = file_hash

            # Mark chunks as downloaded
            for i in range(session.total_chunks):
                start_byte = i * session.chunk_size
                end_byte = min(start_byte + session.chunk_size, session.total_size)
                chunk_data = file_data[start_byte:end_byte]

                chunk = DownloadChunk(
                    chunk_id=str(uuid4()),
                    start_byte=start_byte,
                    end_byte=end_byte,
                    size=len(chunk_data),
                    data=chunk_data,
                    downloaded_at=datetime.utcnow(),
                    verified=True,
                    hash=hashlib.sha256(chunk_data).hexdigest(),
                )
                session.chunks.append(chunk)

            # Simulate download progress
            await self._simulate_download_progress(session, progress_callback)

            # Mark as completed
            session.status = DownloadStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.update_progress()

            # Update stats
            self.download_stats["completed_downloads"] += 1
            self.download_stats["total_bytes_downloaded"] += session.total_size

            # Calculate average download speed
            if session.completed_at:
                duration = (session.completed_at - session.created_at).total_seconds()
                if duration > 0:
                    self.download_stats["average_download_speed"] = (
                        (self.download_stats["average_download_speed"] + (session.total_size / duration)) / 2
                    )

            logger.info(f"Completed file download for session {session_id}")
            return DownloadResult(
                success=True,
                file_data=file_data,
                file_path=file_response.path,
                file_hash=file_hash,
                file_size=session.total_size,
                download_duration=duration if session.completed_at else 0.0,
                chunks_downloaded=len(session.chunks),
                verification_status="completed",
            )

        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            session.status = DownloadStatus.FAILED
            self.download_stats["failed_downloads"] += 1
            return DownloadResult(success=False, error_message=str(e))

    async def download_chunk(
        self,
        session_id: str,
        chunk_index: int,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> DownloadResult:
        """Download a single chunk.

        Args:
            session_id: Download session ID
            chunk_index: Chunk index (0-based)
            rate_limiter: Optional rate limiter

        Returns:
            DownloadResult instance
        """
        session = self._get_session(session_id)
        if not session:
            return DownloadResult(success=False, error_message="Download session not found")

        try:
            # Validate chunk index
            if chunk_index < 0 or chunk_index >= session.total_chunks:
                return DownloadResult(success=False, error_message="Invalid chunk index")

            # Get file information
            file_response = await self.file_manager.get_file(UUID(session.file_id), "system")
            if not file_response:
                return DownloadResult(success=False, error_message="File not found")

            # Calculate chunk boundaries
            start_byte = chunk_index * session.chunk_size
            end_byte = min(start_byte + session.chunk_size, session.total_size)
            expected_size = end_byte - start_byte

            # Check if chunk already downloaded
            existing_chunk = next(
                (c for c in session.chunks if c.chunk_index == chunk_index), None
            )
            if existing_chunk and existing_chunk.data:
                return DownloadResult(
                    success=True,
                    file_data=existing_chunk.data,
                    file_size=expected_size,
                )

            # Simulate chunk download (in real implementation, this would stream from storage)
            chunk_data = b"0" * expected_size  # Mock chunk data

            # Apply rate limiting if provided
            if rate_limiter:
                await rate_limiter.wait_for_tokens(len(chunk_data))

            # Create download chunk
            chunk = DownloadChunk(
                chunk_id=str(uuid4()),
                start_byte=start_byte,
                end_byte=end_byte,
                size=len(chunk_data),
                data=chunk_data,
                downloaded_at=datetime.utcnow(),
                verified=True,
                hash=hashlib.sha256(chunk_data).hexdigest(),
            )

            # Remove existing chunk if exists
            session.chunks = [c for c in session.chunks if c.chunk_index != chunk_index]
            session.chunks.append(chunk)

            # Sort chunks by index
            session.chunks.sort(key=lambda x: x.start_byte)

            session.update_progress()

            logger.debug(f"Downloaded chunk {chunk_index} for session {session_id}")
            return DownloadResult(
                success=True,
                file_data=chunk_data,
                file_size=expected_size,
            )

        except Exception as e:
            logger.error(f"Error downloading chunk: {str(e)}")
            return DownloadResult(success=False, error_message=str(e))

    async def assemble_downloaded_chunks(
        self,
        session_id: str,
        progress_callback: Optional[Callable[[DownloadProgress], None]] = None,
    ) -> DownloadResult:
        """Assemble downloaded chunks into a complete file.

        Args:
            session_id: Download session ID
            progress_callback: Progress callback function

        Returns:
            DownloadResult instance
        """
        session = self._get_session(session_id)
        if not session:
            return DownloadResult(success=False, error_message="Download session not found")

        try:
            # Verify all chunks are downloaded
            if len(session.chunks) != session.total_chunks:
                return DownloadResult(
                    success=False,
                    error_message=f"Missing chunks: expected {session.total_chunks}, got {len(session.chunks)}",
                )

            # Check for gaps in chunks
            expected_indices = set(range(session.total_chunks))
            actual_indices = {chunk.start_byte // session.chunk_size for chunk in session.chunks}
            missing_indices = expected_indices - actual_indices

            if missing_indices:
                return DownloadResult(
                    success=False,
                    error_message=f"Missing chunk indices: {missing_indices}",
                )

            # Verify chunk order and sizes
            for i, chunk in enumerate(session.chunks):
                expected_start = i * session.chunk_size
                expected_end = min(expected_start + session.chunk_size, session.total_size)
                expected_size = expected_end - expected_start

                if chunk.start_byte != expected_start:
                    return DownloadResult(
                        success=False,
                        error_message=f"Chunk {i} start byte mismatch",
                    )

                if chunk.size != expected_size:
                    return DownloadResult(
                        success=False,
                        error_message=f"Chunk {i} size mismatch: expected {expected_size}, got {chunk.size}",
                    )

            # Assemble file data
            file_data = b"".join(chunk.data for chunk in session.chunks)

            if len(file_data) != session.total_size:
                return DownloadResult(
                    success=False,
                    error_message=f"Assembled file size mismatch: expected {session.total_size}, got {len(file_data)}",
                )

            # Verify file hash
            calculated_hash = hashlib.sha256(file_data).hexdigest()
            if session.file_hash and calculated_hash != session.file_hash:
                return DownloadResult(
                    success=False,
                    error_message="File hash mismatch",
                )

            session.file_hash = calculated_hash

            # Simulate final download progress
            await self._simulate_download_progress(session, progress_callback)

            # Mark as completed
            session.status = DownloadStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.update_progress()

            # Update stats
            self.download_stats["completed_downloads"] += 1
            self.download_stats["total_bytes_downloaded"] += session.total_size

            logger.info(f"Assembled downloaded chunks for session {session_id}")
            return DownloadResult(
                success=True,
                file_data=file_data,
                file_hash=calculated_hash,
                file_size=session.total_size,
                download_duration=(session.completed_at - session.created_at).total_seconds(),
                chunks_downloaded=len(session.chunks),
                verification_status="completed",
            )

        except Exception as e:
            logger.error(f"Error assembling downloaded chunks: {str(e)}")
            session.status = DownloadStatus.FAILED
            self.download_stats["failed_downloads"] += 1
            return DownloadResult(success=False, error_message=str(e))

    async def stream_file(
        self,
        session_id: str,
        chunk_callback: Optional[Callable[[bytes], None]] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Stream file content in chunks.

        Args:
            session_id: Download session ID
            chunk_callback: Callback for each chunk
            rate_limiter: Optional rate limiter

        Yields:
            File content as bytes
        """
        session = self._get_session(session_id)
        if not session:
            return

        try:
            session.status = DownloadStatus.DOWNLOADING
            session.update_progress()

            # Get file information
            file_response = await self.file_manager.get_file(UUID(session.file_id), "system")
            if not file_response:
                return

            # Stream file in chunks
            for i in range(session.total_chunks):
                start_byte = i * session.chunk_size
                end_byte = min(start_byte + session.chunk_size, session.total_size)

                # Simulate chunk download
                chunk_data = b"0" * (end_byte - start_byte)  # Mock chunk data

                # Apply rate limiting if provided
                if rate_limiter:
                    await rate_limiter.wait_for_tokens(len(chunk_data))

                # Update progress
                session.update_progress()
                downloaded_size = sum(c.size for c in session.chunks)
                progress_percentage = (downloaded_size / session.total_size) * 100 if session.total_size > 0 else 0

                if chunk_callback:
                    await asyncio.get_event_loop().run_in_executor(
                        None, chunk_callback, chunk_data
                    )

                yield chunk_data

            session.status = DownloadStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.update_progress()

        except Exception as e:
            logger.error(f"Error streaming file: {str(e)}")
            session.status = DownloadStatus.FAILED
            yield b""  # Return empty bytes on error

    async def pause_download(self, session_id: str) -> bool:
        """Pause a download session.

        Args:
            session_id: Download session ID

        Returns:
            True if paused successfully
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if session.status not in [DownloadStatus.DOWNLOADING, DownloadStatus.PENDING]:
            return False

        session.status = DownloadStatus.PAUSED
        session.update_progress()

        logger.info(f"Paused download session {session_id}")
        return True

    async def resume_download(self, session_id: str) -> bool:
        """Resume a paused download session.

        Args:
            session_id: Download session ID

        Returns:
            True if resumed successfully
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if session.status != DownloadStatus.PAUSED:
            return False

        session.status = DownloadStatus.PENDING
        session.update_progress()

        logger.info(f"Resumed download session {session_id}")
        return True

    async def cancel_download(self, session_id: str) -> bool:
        """Cancel a download session.

        Args:
            session_id: Download session ID

        Returns:
            True if cancelled successfully
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if session.status == DownloadStatus.COMPLETED:
            return False

        session.status = DownloadStatus.CANCELLED
        session.update_progress()

        # Clean up session
        if session_id in self.download_sessions:
            del self.download_sessions[session_id]

        logger.info(f"Cancelled download session {session_id}")
        return True

    def get_download_session(self, session_id: str) -> Optional[DownloadSession]:
        """Get download session information.

        Args:
            session_id: Download session ID

        Returns:
            DownloadSession instance or None
        """
        return self._get_session(session_id)

    def get_download_progress(self, session_id: str) -> Optional[DownloadProgress]:
        """Get download progress.

        Args:
            session_id: Download session ID

        Returns:
            DownloadProgress instance or None
        """
        session = self._get_session(session_id)
        if not session:
            return None

        # Calculate progress
        downloaded_size = sum(chunk.size for chunk in session.chunks)
        downloaded_chunks = len(session.chunks)
        verified_chunks = sum(1 for chunk in session.chunks if chunk.verified)

        progress_percentage = (downloaded_size / session.total_size) * 100 if session.total_size > 0 else 0

        # Calculate download speed
        download_speed = 0.0
        estimated_time_remaining = 0.0

        if session.status == DownloadStatus.DOWNLOADING:
            elapsed_time = (datetime.utcnow() - session.created_at).total_seconds()
            if elapsed_time > 0:
                download_speed = downloaded_size / elapsed_time
                if download_speed > 0:
                    remaining_size = session.total_size - downloaded_size
                    estimated_time_remaining = remaining_size / download_speed

        return DownloadProgress(
            download_id=session.session_id,
            status=session.status,
            total_size=session.total_size,
            downloaded_size=downloaded_size,
            chunk_size=session.chunk_size,
            total_chunks=session.total_chunks,
            downloaded_chunks=downloaded_chunks,
            verified_chunks=verified_chunks,
            progress_percentage=progress_percentage,
            download_speed=download_speed,
            estimated_time_remaining=estimated_time_remaining,
            start_time=session.created_at,
            last_update=session.updated_at,
        )

    def list_download_sessions(
        self,
        status: Optional[DownloadStatus] = None,
        limit: int = 100,
    ) -> List[DownloadSession]:
        """List download sessions.

        Args:
            status: Filter by status
            limit: Maximum number of sessions to return

        Returns:
            List of download sessions
        """
        sessions = list(self.download_sessions.values())

        # Apply filter
        if status:
            sessions = [s for s in sessions if s.status == status]

        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit
        return sessions[:limit]

    def get_download_statistics(self) -> Dict[str, Any]:
        """Get download statistics.

        Returns:
            Dictionary with download statistics
        """
        active_sessions = len([s for s in self.download_sessions.values() if s.status == DownloadStatus.DOWNLOADING])
        paused_sessions = len([s for s in self.download_sessions.values() if s.status == DownloadStatus.PAUSED])

        return {
            **self.download_stats,
            "active_sessions": active_sessions,
            "paused_sessions": paused_sessions,
            "total_sessions": len(self.download_sessions),
        }

    def cleanup_completed_sessions(self, older_than_hours: int = 24) -> int:
        """Clean up completed download sessions.

        Args:
            older_than_hours: Remove sessions older than this many hours

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        sessions_to_remove = []

        for session_id, session in self.download_sessions.items():
            if session.status in [DownloadStatus.COMPLETED, DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
                if session.updated_at < cutoff_time:
                    sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.download_sessions[session_id]

        logger.info(f"Cleaned up {len(sessions_to_remove)} completed download sessions")
        return len(sessions_to_remove)

    # Private methods

    def _get_session(self, session_id: str) -> Optional[DownloadSession]:
        """Get download session by ID."""
        return self.download_sessions.get(session_id)

    async def _simulate_download_progress(
        self,
        session: DownloadSession,
        progress_callback: Optional[Callable[[DownloadProgress], None]],
    ):
        """Simulate download progress.

        Args:
            session: Download session
            progress_callback: Progress callback
        """
        # In a real implementation, this would update progress during streaming
        # For mock, we'll just call the callback if provided
        if progress_callback:
            progress = self.get_download_progress(session.session_id)
            if progress:
                await asyncio.get_event_loop().run_in_executor(None, progress_callback, progress)
