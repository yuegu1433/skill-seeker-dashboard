"""Skill Version Manager.

This module provides comprehensive version control for skill files,
including versioning, branching, tagging, and rollback capabilities.
"""

import asyncio
import difflib
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging

from .utils import SkillValidator, SkillFormatter
from .event_manager import SkillEventManager, EventType
from .manager import SkillManager

logger = logging.getLogger(__name__)


class VersionStatus(Enum):
    """Version status enumeration."""
    DRAFT = "draft"
    DEVELOPMENT = "development"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class CompareType(Enum):
    """Comparison type enumeration."""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side_by_side"
    INLINE = "inline"


class MergeStrategy(Enum):
    """Merge strategy enumeration."""
    MERGE = "merge"
    REPLACE = "replace"
    KEEP_BOTH = "keep_both"


@dataclass
class VersionTag:
    """Represents a version tag."""

    name: str
    version: str
    message: str
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class VersionCommit:
    """Represents a version commit."""

    commit_id: str
    version: str
    skill_id: str
    message: str
    author: str
    timestamp: datetime = field(default_factory=datetime.now)
    parent_commit: Optional[str] = None
    changes: Dict[str, Any] = field(default_factory=dict)
    file_hash: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class VersionBranch:
    """Represents a version branch."""

    name: str
    version: str
    skill_id: str
    base_branch: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class VersionComparison:
    """Represents a version comparison result."""

    from_version: str
    to_version: str
    compare_type: CompareType
    differences: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        return data


@dataclass
class MergeConflict:
    """Represents a merge conflict."""

    file_path: str
    conflict_type: str  # "content", "metadata", "dependency"
    from_content: str
    to_content: str
    merged_content: Optional[str] = None
    resolution_strategy: Optional[MergeStrategy] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class SkillVersionManager:
    """Manages skill versions, branches, tags, and version control operations."""

    def __init__(
        self,
        skill_manager: SkillManager,
        event_manager: SkillEventManager,
        workspace_path: Path,
    ):
        """Initialize version manager.

        Args:
            skill_manager: Skill manager instance
            event_manager: Event manager instance
            workspace_path: Workspace directory path
        """
        self.skill_manager = skill_manager
        self.event_manager = event_manager
        self.workspace_path = workspace_path

        # Version storage
        self.versions: Dict[str, Dict[str, VersionCommit]] = {}
        self.tags: Dict[str, List[VersionTag]] = {}
        self.branches: Dict[str, List[VersionBranch]] = {}

        # Version cache
        self.version_cache: Dict[str, Dict[str, Any]] = {}

        # Lock for concurrent access
        self._lock = asyncio.Lock()

    async def create_version(
        self,
        skill_id: str,
        version: str,
        message: str,
        author: str,
        file_path: str,
        status: VersionStatus = VersionStatus.DEVELOPMENT,
        parent_version: Optional[str] = None,
    ) -> Optional[VersionCommit]:
        """Create a new version.

        Args:
            skill_id: Skill identifier
            version: Version string (e.g., "1.0.0")
            message: Commit message
            author: Author name
            file_path: Path to skill file
            status: Version status
            parent_version: Parent version (for branching)

        Returns:
            VersionCommit instance or None
        """
        async with self._lock:
            try:
                # Read file content
                full_path = self.workspace_path / file_path
                if not full_path.exists():
                    logger.error(f"File not found: {full_path}")
                    return None

                content = full_path.read_text(encoding="utf-8")

                # Calculate file hash
                file_hash = hashlib.sha256(content.encode()).hexdigest()

                # Generate commit ID
                commit_id = self._generate_commit_id(skill_id, version, file_hash)

                # Create commit
                commit = VersionCommit(
                    commit_id=commit_id,
                    version=version,
                    skill_id=skill_id,
                    message=message,
                    author=author,
                    parent_commit=parent_version,
                    file_hash=file_hash,
                    changes={
                        "file_path": file_path,
                        "status": status.value,
                        "content_size": len(content),
                        "lines_count": len(content.splitlines()),
                    },
                )

                # Store commit
                if skill_id not in self.versions:
                    self.versions[skill_id] = {}

                self.versions[skill_id][version] = commit

                # Cache version
                await self._cache_version(skill_id, version, content)

                # Publish event
                await self.event_manager.publish_event(
                    EventType.VERSION_CREATED,
                    skill_id=skill_id,
                    version=version,
                    commit_id=commit_id,
                    author=author,
                )

                logger.info(f"Created version {version} for skill {skill_id}")
                return commit

            except Exception as e:
                logger.error(f"Error creating version: {e}")
                return None

    async def tag_version(
        self,
        skill_id: str,
        version: str,
        tag_name: str,
        message: str,
        created_by: Optional[str] = None,
    ) -> Optional[VersionTag]:
        """Create a tag for a version.

        Args:
            skill_id: Skill identifier
            version: Version to tag
            tag_name: Tag name
            message: Tag message
            created_by: Tag creator

        Returns:
            VersionTag instance or None
        """
        # Check if version exists
        if skill_id not in self.versions or version not in self.versions[skill_id]:
            logger.error(f"Version {version} not found for skill {skill_id}")
            return None

        # Create tag
        tag = VersionTag(
            name=tag_name,
            version=version,
            message=message,
            created_by=created_by,
        )

        # Store tag
        if skill_id not in self.tags:
            self.tags[skill_id] = []

        self.tags[skill_id].append(tag)

        # Publish event
        await self.event_manager.publish_event(
            EventType.VERSION_TAGGED,
            skill_id=skill_id,
            version=version,
            tag_name=tag_name,
            created_by=created_by,
        )

        logger.info(f"Created tag {tag_name} for version {version}")
        return tag

    async def create_branch(
        self,
        skill_id: str,
        version: str,
        branch_name: str,
        created_by: Optional[str] = None,
        base_branch: Optional[str] = None,
    ) -> Optional[VersionBranch]:
        """Create a new branch from a version.

        Args:
            skill_id: Skill identifier
            version: Version to branch from
            branch_name: Branch name
            created_by: Branch creator
            base_branch: Base branch name

        Returns:
            VersionBranch instance or None
        """
        # Check if version exists
        if skill_id not in self.versions or version not in self.versions[skill_id]:
            logger.error(f"Version {version} not found for skill {skill_id}")
            return None

        # Create branch
        branch = VersionBranch(
            name=branch_name,
            version=version,
            skill_id=skill_id,
            base_branch=base_branch,
            created_by=created_by,
        )

        # Store branch
        if skill_id not in self.branches:
            self.branches[skill_id] = []

        self.branches[skill_id].append(branch)

        # Publish event
        await self.event_manager.publish_event(
            EventType.BRANCH_CREATED,
            skill_id=skill_id,
            branch_name=branch_name,
            base_version=version,
            created_by=created_by,
        )

        logger.info(f"Created branch {branch_name} from version {version}")
        return branch

    async def compare_versions(
        self,
        skill_id: str,
        from_version: str,
        to_version: str,
        compare_type: CompareType = CompareType.UNIFIED,
    ) -> Optional[VersionComparison]:
        """Compare two versions.

        Args:
            skill_id: Skill identifier
            from_version: Source version
            to_version: Target version
            compare_type: Type of comparison

        Returns:
            VersionComparison instance or None
        """
        try:
            # Get version content
            from_content = await self._get_version_content(skill_id, from_version)
            to_content = await self._get_version_content(skill_id, to_version)

            if from_content is None or to_content is None:
                logger.error("Could not retrieve version content")
                return None

            # Perform comparison
            differences = []
            summary = {
                "added_lines": 0,
                "deleted_lines": 0,
                "modified_lines": 0,
            }

            if compare_type == CompareType.UNIFIED:
                diff = difflib.unified_diff(
                    from_content.splitlines(keepends=True),
                    to_content.splitlines(keepends=True),
                    fromfile=f"v{from_version}",
                    tofile=f"v{to_version}",
                    lineterm="",
                )

                differences = [{"type": "diff", "content": "\n".join(diff)}]

                # Calculate summary
                for line in diff:
                    if line.startswith("+") and not line.startswith("+++"):
                        summary["added_lines"] += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        summary["deleted_lines"] += 1

            # Create comparison
            comparison = VersionComparison(
                from_version=from_version,
                to_version=to_version,
                compare_type=compare_type,
                differences=differences,
                summary=summary,
            )

            # Publish event
            await self.event_manager.publish_event(
                EventType.VERSION_COMPARED,
                skill_id=skill_id,
                from_version=from_version,
                to_version=to_version,
                compare_type=compare_type.value,
            )

            return comparison

        except Exception as e:
            logger.error(f"Error comparing versions: {e}")
            return None

    async def rollback_version(
        self,
        skill_id: str,
        target_version: str,
        author: str,
        reason: str,
    ) -> bool:
        """Rollback to a previous version.

        Args:
            skill_id: Skill identifier
            target_version: Version to rollback to
            author: Rollback author
            reason: Rollback reason

        Returns:
            True if rollback was successful
        """
        async with self._lock:
            try:
                # Get target version content
                content = await self._get_version_content(skill_id, target_version)
                if content is None:
                    logger.error(f"Could not find version {target_version}")
                    return False

                # Create new version for rollback
                rollback_version = f"{target_version}-rollback-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

                # Get skill file path
                skill = await self.skill_manager.get_skill(skill_id)
                if not skill:
                    logger.error(f"Skill not found: {skill_id}")
                    return False

                file_path = f"{skill_id}.yaml"

                # Create rollback version
                commit = await self.create_version(
                    skill_id=skill_id,
                    version=rollback_version,
                    message=f"Rollback to {target_version}: {reason}",
                    author=author,
                    file_path=file_path,
                    status=VersionStatus.STABLE,
                    parent_version=target_version,
                )

                if commit is None:
                    return False

                # Write rolled back content
                full_path = self.workspace_path / file_path
                full_path.write_text(content, encoding="utf-8")

                # Publish event
                await self.event_manager.publish_event(
                    EventType.VERSION_ROLLED_BACK,
                    skill_id=skill_id,
                    target_version=target_version,
                    rollback_version=rollback_version,
                    author=author,
                    reason=reason,
                )

                logger.info(f"Rolled back skill {skill_id} to version {target_version}")
                return True

            except Exception as e:
                logger.error(f"Error during rollback: {e}")
                return False

    async def merge_branches(
        self,
        skill_id: str,
        source_branch: str,
        target_branch: str,
        author: str,
        strategy: MergeStrategy = MergeStrategy.MERGE,
    ) -> Tuple[bool, List[MergeConflict]]:
        """Merge branches.

        Args:
            skill_id: Skill identifier
            source_branch: Source branch name
            target_branch: Target branch name
            author: Merge author
            strategy: Merge strategy

        Returns:
            Tuple of (success, conflicts)
        """
        async with self._lock:
            conflicts = []

            try:
                # Get branch versions
                source_version = await self._get_branch_version(skill_id, source_branch)
                target_version = await self._get_branch_version(skill_id, target_branch)

                if not source_version or not target_version:
                    logger.error("Could not find branch versions")
                    return False, conflicts

                # Get content from both branches
                source_content = await self._get_version_content(
                    skill_id,
                    source_version.version,
                )
                target_content = await self._get_version_content(
                    skill_id,
                    target_version.version,
                )

                if source_content is None or target_content is None:
                    return False, conflicts

                # Merge content
                if strategy == MergeStrategy.REPLACE:
                    merged_content = source_content
                elif strategy == MergeStrategy.KEEP_BOTH:
                    # Keep both versions (could add timestamp markers)
                    merged_content = f"# Source: {source_branch}\n{source_content}\n\n# Target: {target_branch}\n{target_content}"
                else:  # MERGE
                    merged_content = await self._merge_content(
                        source_content,
                        target_content,
                        conflicts,
                    )

                # Write merged content
                skill = await self.skill_manager.get_skill(skill_id)
                if not skill:
                    return False, conflicts

                file_path = f"{skill_id}.yaml"
                full_path = self.workspace_path / file_path
                full_path.write_text(merged_content, encoding="utf-8")

                # Create merge commit
                merge_version = f"merge-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

                await self.create_version(
                    skill_id=skill_id,
                    version=merge_version,
                    message=f"Merge {source_branch} into {target_branch}",
                    author=author,
                    file_path=file_path,
                    status=VersionStatus.DEVELOPMENT,
                    parent_version=target_version.version,
                )

                # Publish event
                await self.event_manager.publish_event(
                    EventType.BRANCH_MERGED,
                    skill_id=skill_id,
                    source_branch=source_branch,
                    target_branch=target_branch,
                    strategy=strategy.value,
                    author=author,
                    conflicts_count=len(conflicts),
                )

                logger.info(f"Merged {source_branch} into {target_branch}")
                return len(conflicts) == 0, conflicts

            except Exception as e:
                logger.error(f"Error during merge: {e}")
                return False, conflicts

    async def get_version_history(
        self,
        skill_id: str,
        limit: Optional[int] = None,
    ) -> List[VersionCommit]:
        """Get version history for a skill.

        Args:
            skill_id: Skill identifier
            limit: Maximum number of versions to return

        Returns:
            List of VersionCommit instances
        """
        if skill_id not in self.versions:
            return []

        versions = list(self.versions[skill_id].values())

        # Sort by timestamp (newest first)
        versions.sort(key=lambda v: v.timestamp, reverse=True)

        if limit:
            versions = versions[:limit]

        return versions

    async def get_version_tags(
        self,
        skill_id: str,
    ) -> List[VersionTag]:
        """Get tags for a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            List of VersionTag instances
        """
        return self.tags.get(skill_id, [])

    async def get_version_branches(
        self,
        skill_id: str,
    ) -> List[VersionBranch]:
        """Get branches for a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            List of VersionBranch instances
        """
        return self.branches.get(skill_id, [])

    async def get_version_statistics(
        self,
        skill_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get version statistics for a skill.

        Args:
            skill_id: Skill identifier

        Returns:
            Statistics dictionary or None
        """
        if skill_id not in self.versions:
            return None

        versions = list(self.versions[skill_id].values())
        tags = self.tags.get(skill_id, [])
        branches = self.branches.get(skill_id, [])

        # Calculate statistics
        total_versions = len(versions)
        total_tags = len(tags)
        total_branches = len(branches)

        # Version status distribution
        status_counts = {}
        for version in versions:
            status = version.changes.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Author statistics
        author_counts = {}
        for version in versions:
            author = version.author
            author_counts[author] = author_counts.get(author, 0) + 1

        # Recent activity (last 30 days)
        cutoff_date = datetime.now().timestamp() - (30 * 24 * 3600)
        recent_versions = [
            v for v in versions
            if v.timestamp.timestamp() > cutoff_date
        ]

        return {
            "skill_id": skill_id,
            "total_versions": total_versions,
            "total_tags": total_tags,
            "total_branches": total_branches,
            "status_distribution": status_counts,
            "author_statistics": author_counts,
            "recent_versions_count": len(recent_versions),
            "latest_version": versions[0].version if versions else None,
            "oldest_version": versions[-1].version if versions else None,
        }

    async def export_version(
        self,
        skill_id: str,
        version: str,
        format_type: str = "json",
    ) -> Optional[str]:
        """Export version in specified format.

        Args:
            skill_id: Skill identifier
            version: Version to export
            format_type: Export format (json, yaml, etc.)

        Returns:
            Exported content or None
        """
        if skill_id not in self.versions or version not in self.versions[skill_id]:
            return None

        commit = self.versions[skill_id][version]
        content = await self._get_version_content(skill_id, version)

        if content is None:
            return None

        export_data = {
            "version": version,
            "commit": commit.to_dict(),
            "content": content,
        }

        if format_type == "json":
            return json.dumps(export_data, indent=2, default=str)
        elif format_type == "yaml":
            # Simple YAML export
            result = f"# Version: {version}\n"
            result += f"# Commit: {commit.commit_id}\n"
            result += f"# Author: {commit.author}\n"
            result += f"# Date: {commit.timestamp.isoformat()}\n\n"
            result += content
            return result
        else:
            return content

    async def cleanup_old_versions(
        self,
        skill_id: str,
        keep_count: int = 50,
    ) -> int:
        """Clean up old versions, keeping only the most recent ones.

        Args:
            skill_id: Skill identifier
            keep_count: Number of versions to keep

        Returns:
            Number of versions cleaned up
        """
        async with self._lock:
            if skill_id not in self.versions:
                return 0

            versions = list(self.versions[skill_id].values())
            versions.sort(key=lambda v: v.timestamp, reverse=True)

            cleaned_count = 0
            if len(versions) > keep_count:
                versions_to_delete = versions[keep_count:]

                for version in versions_to_delete:
                    del self.versions[skill_id][version.version]
                    cleaned_count += 1

                logger.info(f"Cleaned up {cleaned_count} old versions for skill {skill_id}")

            return cleaned_count

    def _generate_commit_id(
        self,
        skill_id: str,
        version: str,
        file_hash: str,
    ) -> str:
        """Generate unique commit ID.

        Args:
            skill_id: Skill identifier
            version: Version string
            file_hash: File hash

        Returns:
            Unique commit ID
        """
        data = f"{skill_id}:{version}:{file_hash}:{datetime.now().timestamp()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    async def _cache_version(
        self,
        skill_id: str,
        version: str,
        content: str,
    ):
        """Cache version content.

        Args:
            skill_id: Skill identifier
            version: Version string
            content: File content
        """
        if skill_id not in self.version_cache:
            self.version_cache[skill_id] = {}

        self.version_cache[skill_id][version] = content

    async def _get_version_content(
        self,
        skill_id: str,
        version: str,
    ) -> Optional[str]:
        """Get version content from cache or storage.

        Args:
            skill_id: Skill identifier
            version: Version string

        Returns:
            Content string or None
        """
        # Try cache first
        if skill_id in self.version_cache and version in self.version_cache[skill_id]:
            return self.version_cache[skill_id][version]

        # Try to read from file system
        if skill_id in self.versions and version in self.versions[skill_id]:
            commit = self.versions[skill_id][version]
            file_path = commit.changes.get("file_path", f"{skill_id}.yaml")

            full_path = self.workspace_path / file_path
            if full_path.exists():
                content = full_path.read_text(encoding="utf-8")
                await self._cache_version(skill_id, version, content)
                return content

        return None

    async def _get_branch_version(
        self,
        skill_id: str,
        branch_name: str,
    ) -> Optional[VersionBranch]:
        """Get branch information.

        Args:
            skill_id: Skill identifier
            branch_name: Branch name

        Returns:
            VersionBranch instance or None
        """
        if skill_id not in self.branches:
            return None

        for branch in self.branches[skill_id]:
            if branch.name == branch_name and branch.is_active:
                return branch

        return None

    async def _merge_content(
        self,
        source_content: str,
        target_content: str,
        conflicts: List[MergeConflict],
    ) -> str:
        """Merge two content versions.

        Args:
            source_content: Source content
            target_content: Target content
            conflicts: List to store conflicts

        Returns:
            Merged content
        """
        # Simple merge strategy - this is a basic implementation
        # In a real system, you would use a more sophisticated merge algorithm

        source_lines = source_content.splitlines()
        target_lines = target_content.splitlines()

        merged_lines = []
        i, j = 0, 0

        while i < len(source_lines) or j < len(target_lines):
            if i >= len(source_lines):
                merged_lines.append(target_lines[j])
                j += 1
            elif j >= len(target_lines):
                merged_lines.append(source_lines[i])
                i += 1
            elif source_lines[i] == target_lines[j]:
                merged_lines.append(source_lines[i])
                i += 1
                j += 1
            else:
                # Conflict detected
                conflict = MergeConflict(
                    file_path="skill.yaml",
                    conflict_type="content",
                    from_content=source_lines[i],
                    to_content=target_lines[j],
                    merged_content=None,
                )
                conflicts.append(conflict)

                # For now, keep source version
                merged_lines.append(source_lines[i])
                i += 1

        return "\n".join(merged_lines)
