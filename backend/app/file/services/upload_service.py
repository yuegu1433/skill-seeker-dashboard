"""File Upload Service.

This module provides comprehensive file upload capabilities including upload
processing, validation, chunked upload, and resumable uploads.
"""

import asyncio
import logging
import hashlib
import os
from typing import Dict, List, Optional, Tuple, Any, BinaryIO, Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from enum import Enum
from dataclasses import dataclass, field
import json
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession

# Import managers and schemas
from app.file.manager import FileManager
from app.file.models.file import File
from app.file.schemas.file_operations import FileCreate

logger = logging.getLogger(__name__)


class UploadStatus(str, Enum):
    """Upload status enumeration."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFYING = "verifying"


class UploadMode(str, Enum):
    """Upload mode enumeration."""
    NORMAL = "normal"
    CHUNKED = "chunked"
    RESUMABLE = "resumable"


@dataclass
class UploadChunk:
    """Upload chunk information."""

    chunk_id: str
    chunk_index: int
    start_byte: int
    end_byte: int
    size: int
    data: bytes
    hash: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    verified: bool = False


@dataclass
class UploadProgress:
    """Upload progress information."""

    upload_id: str
    status: UploadStatus
    total_size: int
    uploaded_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: int
    verified_chunks: int
    progress_percentage: float
    upload_speed: float  # bytes per second
    estimated_time_remaining: float  # seconds
    start_time: datetime
    last_update: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "upload_id": self.upload_id,
            "status": self.status.value,
            "total_size": self.total_size,
            "uploaded_size": self.uploaded_size,
            "chunk_size": self.chunk_size,
            "total_chunks": self.total_chunks,
            "uploaded_chunks": self.uploaded_chunks,
            "verified_chunks": self.verified_chunks,
            "progress_percentage": round(self.progress_percentage, 2),
            "upload_speed": round(self.upload_speed, 2),
            "estimated_time_remaining": round(self.estimated_time_remaining, 2),
            "start_time": self.start_time.isoformat(),
            "last_update": self.last_update.isoformat(),
        }


@dataclass
class UploadSession:
    """Upload session information."""

    session_id: str
    file_id: str
    filename: str
    total_size: int
    chunk_size: int
    total_chunks: int
    upload_mode: UploadMode
    status: UploadStatus
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[UploadChunk] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    def update_progress(self):
        """Update upload progress."""
        self.updated_at = datetime.utcnow()


@dataclass
class UploadResult:
    """Upload result information."""

    success: bool
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_hash: Optional[str] = None
    file_size: int = 0
    upload_duration: float = 0.0
    chunks_uploaded: int = 0
    verification_status: str = "not_verified"
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UploadValidator:
    """Upload file validator."""

    # Maximum file sizes (in bytes)
    MAX_FILE_SIZE = 10 * 1024 * 1024 * 1024  # 10 GB
    MAX_CHUNK_SIZE = 10 * 1024 * 1024  # 10 MB

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        # Documents
        '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt',
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg',
        # Videos
        '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv',
        # Audio
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma',
        # Archives
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',
        # Code
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb',
        '.go', '.rs', '.swift', '.kt', '.scala', '.pl', '.sh', '.sql',
        '.html', '.css', '.xml', '.json', '.yaml', '.yml', '.md', '.tex',
        # Data
        '.csv', '.xls', '.xlsx', '.xml', '.json',
    }

    # Forbidden file extensions
    FORBIDDEN_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.ps1', '.app', '.deb', '.pkg', '.dmg', '.msi', '.apk',
    }

    @classmethod
    def validate_file_size(cls, file_size: int, max_size: Optional[int] = None) -> Tuple[bool, str]:
        """Validate file size.

        Args:
            file_size: File size in bytes
            max_size: Maximum allowed size (optional)

        Returns:
            Tuple of (is_valid, error_message)
        """
        max_allowed = max_size or cls.MAX_FILE_SIZE

        if file_size <= 0:
            return False, "File size must be greater than 0"

        if file_size > max_allowed:
            return False, f"File size exceeds maximum allowed size of {max_allowed} bytes"

        return True, ""

    @classmethod
    def validate_filename(cls, filename: str) -> Tuple[bool, str]:
        """Validate filename.

        Args:
            filename: File name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not filename or not filename.strip():
            return False, "Filename cannot be empty"

        if len(filename) > 255:
            return False, "Filename cannot exceed 255 characters"

        # Check for dangerous characters
        dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        for char in dangerous_chars:
            if char in filename:
                return False, f"Filename contains forbidden character: {char}"

        return True, ""

    @classmethod
    def validate_file_extension(cls, filename: str) -> Tuple[bool, str]:
        """Validate file extension.

        Args:
            filename: File name

        Returns:
            Tuple of (is_valid, error_message)
        """
        import os

        _, ext = os.path.splitext(filename.lower())

        if not ext:
            return False, "File must have an extension"

        if ext in cls.FORBIDDEN_EXTENSIONS:
            return False, f"File extension {ext} is not allowed"

        return True, ""

    @classmethod
    def validate_chunk_size(cls, chunk_size: int, total_size: int) -> Tuple[bool, str]:
        """Validate chunk size.

        Args:
            chunk_size: Chunk size in bytes
            total_size: Total file size

        Returns:
            Tuple of (is_valid, error_message)
        """
        if chunk_size <= 0:
            return False, "Chunk size must be greater than 0"

        if chunk_size > cls.MAX_CHUNK_SIZE:
            return False, f"Chunk size cannot exceed {cls.MAX_CHUNK_SIZE} bytes"

        if chunk_size > total_size:
            return False, "Chunk size cannot be larger than total file size"

        return True, ""

    @classmethod
    def calculate_file_hash(cls, file_data: bytes) -> str:
        """Calculate file hash.

        Args:
            file_data: File content as bytes

        Returns:
            SHA256 hash string
        """
        return hashlib.sha256(file_data).hexdigest()


class UploadService:
    """File upload service."""

    def __init__(
        self,
        db_session: AsyncSession,
        max_file_size: int = 10 * 1024 * 1024 * 1024,  # 10 GB
        default_chunk_size: int = 5 * 1024 * 1024,  # 5 MB
        max_concurrent_uploads: int = 10,
        storage_path: Optional[str] = None,
    ):
        """Initialize upload service.

        Args:
            db_session: Database session
            max_file_size: Maximum file size in bytes
            default_chunk_size: Default chunk size in bytes
            max_concurrent_uploads: Maximum concurrent uploads
            storage_path: Storage path for temporary files
        """
        self.db = db_session
        self.file_manager = FileManager(db_session)
        self.validator = UploadValidator()

        self.max_file_size = max_file_size
        self.default_chunk_size = default_chunk_size
        self.max_concurrent_uploads = max_concurrent_uploads
        self.storage_path = storage_path or tempfile.gettempdir()

        # Active upload sessions
        self.upload_sessions: Dict[str, UploadSession] = {}

        # Upload statistics
        self.upload_stats = {
            "total_uploads": 0,
            "completed_uploads": 0,
            "failed_uploads": 0,
            "total_bytes_uploaded": 0,
            "average_upload_speed": 0.0,
        }

    async def create_upload_session(
        self,
        filename: str,
        file_size: int,
        upload_mode: UploadMode = UploadMode.NORMAL,
        chunk_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UploadSession:
        """Create a new upload session.

        Args:
            filename: File name
            file_size: File size in bytes
            upload_mode: Upload mode
            chunk_size: Chunk size (optional)
            metadata: Additional metadata

        Returns:
            UploadSession instance
        """
        # Validate filename
        is_valid, error = self.validator.validate_filename(filename)
        if not is_valid:
            raise ValueError(error)

        # Validate file extension
        is_valid, error = self.validator.validate_file_extension(filename)
        if not is_valid:
            raise ValueError(error)

        # Validate file size
        is_valid, error = self.validator.validate_file_size(file_size, self.max_file_size)
        if not is_valid:
            raise ValueError(error)

        # Determine chunk size
        if chunk_size is None:
            chunk_size = self.default_chunk_size

        # Validate chunk size
        is_valid, error = self.validator.validate_chunk_size(chunk_size, file_size)
        if not is_valid:
            raise ValueError(error)

        # Calculate total chunks
        total_chunks = (file_size + chunk_size - 1) // chunk_size

        # Create session
        session = UploadSession(
            session_id=str(uuid4()),
            file_id=str(uuid4()),
            filename=filename,
            total_size=file_size,
            chunk_size=chunk_size,
            total_chunks=total_chunks,
            upload_mode=upload_mode,
            status=UploadStatus.PENDING,
            metadata=metadata or {},
        )

        # Store session
        self.upload_sessions[session.session_id] = session

        # Update stats
        self.upload_stats["total_uploads"] += 1

        logger.info(f"Created upload session {session.session_id} for {filename}")
        return session

    async def upload_file(
        self,
        session_id: str,
        file_data: bytes,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None,
    ) -> UploadResult:
        """Upload a complete file.

        Args:
            session_id: Upload session ID
            file_data: File content as bytes
            progress_callback: Progress callback function

        Returns:
            UploadResult instance
        """
        session = self._get_session(session_id)
        if not session:
            return UploadResult(success=False, error_message="Upload session not found")

        try:
            session.status = UploadStatus.UPLOADING
            session.update_progress()

            # Validate file data
            if len(file_data) != session.total_size:
                return UploadResult(
                    success=False,
                    error_message=f"File size mismatch: expected {session.total_size}, got {len(file_data)}",
                )

            # Calculate file hash
            file_hash = self.validator.calculate_file_hash(file_data)
            session.file_hash = file_hash

            # Simulate upload progress
            await self._simulate_upload_progress(session, progress_callback)

            # Create file in database
            file_create = FileCreate(
                name=session.filename,
                path=f"/uploads/{session.filename}",
                size=session.total_size,
                mime_type=self._get_mime_type(session.filename),
                metadata=session.metadata,
            )

            file_response = await self.file_manager.create_file(file_create, "system")

            if not file_response:
                session.status = UploadStatus.FAILED
                return UploadResult(success=False, error_message="Failed to create file")

            # Mark as completed
            session.status = UploadStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.update_progress()

            # Update stats
            self.upload_stats["completed_uploads"] += 1
            self.upload_stats["total_bytes_uploaded"] += session.total_size

            # Calculate average upload speed
            if session.completed_at:
                duration = (session.completed_at - session.created_at).total_seconds()
                if duration > 0:
                    self.upload_stats["average_upload_speed"] = (
                        (self.upload_stats["average_upload_speed"] + (session.total_size / duration)) / 2
                    )

            logger.info(f"Completed file upload for session {session_id}")
            return UploadResult(
                success=True,
                file_id=file_response.id,
                file_path=file_response.path,
                file_hash=file_hash,
                file_size=session.total_size,
                upload_duration=duration if session.completed_at else 0.0,
                chunks_uploaded=1,
                verification_status="completed",
            )

        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            session.status = UploadStatus.FAILED
            self.upload_stats["failed_uploads"] += 1
            return UploadResult(success=False, error_message=str(e))

    async def upload_chunk(
        self,
        session_id: str,
        chunk_index: int,
        chunk_data: bytes,
        chunk_hash: Optional[str] = None,
    ) -> UploadResult:
        """Upload a single chunk.

        Args:
            session_id: Upload session ID
            chunk_index: Chunk index (0-based)
            chunk_data: Chunk content as bytes
            chunk_hash: Chunk hash (optional)

        Returns:
            UploadResult instance
        """
        session = self._get_session(session_id)
        if not session:
            return UploadResult(success=False, error_message="Upload session not found")

        try:
            # Validate chunk index
            if chunk_index < 0 or chunk_index >= session.total_chunks:
                return UploadResult(success=False, error_message="Invalid chunk index")

            # Calculate expected chunk size
            start_byte = chunk_index * session.chunk_size
            end_byte = min(start_byte + session.chunk_size, session.total_size)
            expected_size = end_byte - start_byte

            # Validate chunk size
            if len(chunk_data) != expected_size:
                return UploadResult(
                    success=False,
                    error_message=f"Chunk size mismatch: expected {expected_size}, got {len(chunk_data)}",
                )

            # Create upload chunk
            chunk = UploadChunk(
                chunk_id=str(uuid4()),
                chunk_index=chunk_index,
                start_byte=start_byte,
                end_byte=end_byte,
                size=len(chunk_data),
                data=chunk_data,
                hash=chunk_hash or hashlib.sha256(chunk_data).hexdigest(),
                uploaded_at=datetime.utcnow(),
                verified=True,  # Assume verified in mock
            )

            # Add chunk to session
            # Remove existing chunk if exists
            session.chunks = [c for c in session.chunks if c.chunk_index != chunk_index]
            session.chunks.append(chunk)

            # Sort chunks by index
            session.chunks.sort(key=lambda x: x.chunk_index)

            session.update_progress()

            logger.debug(f"Uploaded chunk {chunk_index} for session {session_id}")
            return UploadResult(success=True)

        except Exception as e:
            logger.error(f"Error uploading chunk: {str(e)}")
            return UploadResult(success=False, error_message=str(e))

    async def complete_chunked_upload(
        self,
        session_id: str,
        progress_callback: Optional[Callable[[UploadProgress], None]] = None,
    ) -> UploadResult:
        """Complete a chunked upload.

        Args:
            session_id: Upload session ID
            progress_callback: Progress callback function

        Returns:
            UploadResult instance
        """
        session = self._get_session(session_id)
        if not session:
            return UploadResult(success=False, error_message="Upload session not found")

        try:
            session.status = UploadStatus.VERIFYING
            session.update_progress()

            # Verify all chunks are uploaded
            if len(session.chunks) != session.total_chunks:
                return UploadResult(
                    success=False,
                    error_message=f"Missing chunks: expected {session.total_chunks}, got {len(session.chunks)}",
                )

            # Check for gaps in chunks
            expected_indices = set(range(session.total_chunks))
            actual_indices = {chunk.chunk_index for chunk in session.chunks}
            missing_indices = expected_indices - actual_indices

            if missing_indices:
                return UploadResult(
                    success=False,
                    error_message=f"Missing chunk indices: {missing_indices}",
                )

            # Verify chunk order and sizes
            for i, chunk in enumerate(session.chunks):
                if chunk.chunk_index != i:
                    return UploadResult(
                        success=False,
                        error_message=f"Chunk index mismatch at position {i}",
                    )

                expected_start = i * session.chunk_size
                expected_end = min(expected_start + session.chunk_size, session.total_size)
                expected_size = expected_end - expected_start

                if chunk.size != expected_size:
                    return UploadResult(
                        success=False,
                        error_message=f"Chunk {i} size mismatch: expected {expected_size}, got {chunk.size}",
                    )

            # Assemble file data
            file_data = b"".join(chunk.data for chunk in session.chunks)

            if len(file_data) != session.total_size:
                return UploadResult(
                    success=False,
                    error_message=f"Assembled file size mismatch: expected {session.total_size}, got {len(file_data)}",
                )

            # Verify file hash
            calculated_hash = self.validator.calculate_file_hash(file_data)
            if session.file_hash and calculated_hash != session.file_hash:
                return UploadResult(
                    success=False,
                    error_message="File hash mismatch",
                )

            session.file_hash = calculated_hash

            # Simulate final upload progress
            await self._simulate_upload_progress(session, progress_callback)

            # Create file in database
            file_create = FileCreate(
                name=session.filename,
                path=f"/uploads/{session.filename}",
                size=session.total_size,
                mime_type=self._get_mime_type(session.filename),
                metadata=session.metadata,
            )

            file_response = await self.file_manager.create_file(file_create, "system")

            if not file_response:
                session.status = UploadStatus.FAILED
                return UploadResult(success=False, error_message="Failed to create file")

            # Mark as completed
            session.status = UploadStatus.COMPLETED
            session.completed_at = datetime.utcnow()
            session.update_progress()

            # Update stats
            self.upload_stats["completed_uploads"] += 1
            self.upload_stats["total_bytes_uploaded"] += session.total_size

            logger.info(f"Completed chunked upload for session {session_id}")
            return UploadResult(
                success=True,
                file_id=file_response.id,
                file_path=file_response.path,
                file_hash=calculated_hash,
                file_size=session.total_size,
                upload_duration=(session.completed_at - session.created_at).total_seconds(),
                chunks_uploaded=len(session.chunks),
                verification_status="completed",
            )

        except Exception as e:
            logger.error(f"Error completing chunked upload: {str(e)}")
            session.status = UploadStatus.FAILED
            self.upload_stats["failed_uploads"] += 1
            return UploadResult(success=False, error_message=str(e))

    async def pause_upload(self, session_id: str) -> bool:
        """Pause an upload session.

        Args:
            session_id: Upload session ID

        Returns:
            True if paused successfully
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if session.status not in [UploadStatus.UPLOADING, UploadStatus.PENDING]:
            return False

        session.status = UploadStatus.PAUSED
        session.update_progress()

        logger.info(f"Paused upload session {session_id}")
        return True

    async def resume_upload(self, session_id: str) -> bool:
        """Resume a paused upload session.

        Args:
            session_id: Upload session ID

        Returns:
            True if resumed successfully
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if session.status != UploadStatus.PAUSED:
            return False

        session.status = UploadStatus.PENDING
        session.update_progress()

        logger.info(f"Resumed upload session {session_id}")
        return True

    async def cancel_upload(self, session_id: str) -> bool:
        """Cancel an upload session.

        Args:
            session_id: Upload session ID

        Returns:
            True if cancelled successfully
        """
        session = self._get_session(session_id)
        if not session:
            return False

        if session.status == UploadStatus.COMPLETED:
            return False

        session.status = UploadStatus.CANCELLED
        session.update_progress()

        # Clean up session
        if session_id in self.upload_sessions:
            del self.upload_sessions[session_id]

        logger.info(f"Cancelled upload session {session_id}")
        return True

    def get_upload_session(self, session_id: str) -> Optional[UploadSession]:
        """Get upload session information.

        Args:
            session_id: Upload session ID

        Returns:
            UploadSession instance or None
        """
        return self._get_session(session_id)

    def get_upload_progress(self, session_id: str) -> Optional[UploadProgress]:
        """Get upload progress.

        Args:
            session_id: Upload session ID

        Returns:
            UploadProgress instance or None
        """
        session = self._get_session(session_id)
        if not session:
            return None

        # Calculate progress
        uploaded_size = sum(chunk.size for chunk in session.chunks)
        uploaded_chunks = len(session.chunks)
        verified_chunks = sum(1 for chunk in session.chunks if chunk.verified)

        progress_percentage = (uploaded_size / session.total_size) * 100 if session.total_size > 0 else 0

        # Calculate upload speed
        upload_speed = 0.0
        estimated_time_remaining = 0.0

        if session.status == UploadStatus.UPLOADING:
            elapsed_time = (datetime.utcnow() - session.created_at).total_seconds()
            if elapsed_time > 0:
                upload_speed = uploaded_size / elapsed_time
                if upload_speed > 0:
                    remaining_size = session.total_size - uploaded_size
                    estimated_time_remaining = remaining_size / upload_speed

        return UploadProgress(
            upload_id=session.session_id,
            status=session.status,
            total_size=session.total_size,
            uploaded_size=uploaded_size,
            chunk_size=session.chunk_size,
            total_chunks=session.total_chunks,
            uploaded_chunks=uploaded_chunks,
            verified_chunks=verified_chunks,
            progress_percentage=progress_percentage,
            upload_speed=upload_speed,
            estimated_time_remaining=estimated_time_remaining,
            start_time=session.created_at,
            last_update=session.updated_at,
        )

    def list_upload_sessions(
        self,
        status: Optional[UploadStatus] = None,
        limit: int = 100,
    ) -> List[UploadSession]:
        """List upload sessions.

        Args:
            status: Filter by status
            limit: Maximum number of sessions to return

        Returns:
            List of upload sessions
        """
        sessions = list(self.upload_sessions.values())

        # Apply filter
        if status:
            sessions = [s for s in sessions if s.status == status]

        # Sort by creation time (newest first)
        sessions.sort(key=lambda x: x.created_at, reverse=True)

        # Apply limit
        return sessions[:limit]

    def get_upload_statistics(self) -> Dict[str, Any]:
        """Get upload statistics.

        Returns:
            Dictionary with upload statistics
        """
        active_sessions = len([s for s in self.upload_sessions.values() if s.status == UploadStatus.UPLOADING])
        paused_sessions = len([s for s in self.upload_sessions.values() if s.status == UploadStatus.PAUSED])

        return {
            **self.upload_stats,
            "active_sessions": active_sessions,
            "paused_sessions": paused_sessions,
            "total_sessions": len(self.upload_sessions),
        }

    def cleanup_completed_sessions(self, older_than_hours: int = 24) -> int:
        """Clean up completed upload sessions.

        Args:
            older_than_hours: Remove sessions older than this many hours

        Returns:
            Number of sessions cleaned up
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        sessions_to_remove = []

        for session_id, session in self.upload_sessions.items():
            if session.status in [UploadStatus.COMPLETED, UploadStatus.FAILED, UploadStatus.CANCELLED]:
                if session.updated_at < cutoff_time:
                    sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            del self.upload_sessions[session_id]

        logger.info(f"Cleaned up {len(sessions_to_remove)} completed upload sessions")
        return len(sessions_to_remove)

    # Private methods

    def _get_session(self, session_id: str) -> Optional[UploadSession]:
        """Get upload session by ID."""
        return self.upload_sessions.get(session_id)

    async def _simulate_upload_progress(
        self,
        session: UploadSession,
        progress_callback: Optional[Callable[[UploadProgress], None]],
    ):
        """Simulate upload progress.

        Args:
            session: Upload session
            progress_callback: Progress callback
        """
        # In a real implementation, this would stream data and update progress
        # For mock, we'll just call the callback if provided
        if progress_callback:
            progress = self.get_upload_progress(session.session_id)
            if progress:
                await asyncio.get_event_loop().run_in_executor(None, progress_callback, progress)

    def _get_mime_type(self, filename: str) -> str:
        """Get MIME type for filename.

        Args:
            filename: File name

        Returns:
            MIME type string
        """
        import mimetypes

        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
