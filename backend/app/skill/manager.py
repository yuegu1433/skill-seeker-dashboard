"""Skill manager.

This module provides the core SkillManager class for managing skills
with CRUD operations, search, filtering, and state management.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from .models import Skill, SkillVersion, SkillCategory, SkillTag, SkillTagAssociation
from .schemas.skill_operations import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListItem,
    SkillFilter,
    SkillSearch,
    SkillSearchResult,
    SkillStats,
    SkillBulkOperation,
    SkillBulkResult,
)
from .schemas.skill_creation import SkillCreationRequest
from .utils.validators import SkillValidator, BusinessRuleValidator
from .utils.formatters import SkillFormatter, SkillDisplayFormatter

logger = logging.getLogger(__name__)


class SkillManager:
    """Core skill management class.

    Provides unified interface for skill CRUD operations,
    search, filtering, and state management.
    """

    def __init__(self, db_session: Session):
        """Initialize skill manager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.validator = SkillValidator()
        self.formatter = SkillFormatter()
        self.display_formatter = SkillDisplayFormatter()

    # ================================
    # Skill CRUD Operations
    # ================================

    async def create_skill(self, skill_data: Union[SkillCreate, SkillCreationRequest]) -> SkillResponse:
        """Create a new skill.

        Args:
            skill_data: Skill creation data

        Returns:
            Created skill response

        Raises:
            ValueError: If skill data is invalid
            SQLAlchemyError: If database operation fails
        """
        try:
            # Validate skill data
            is_valid, errors = self.validator.validate_skill_data(skill_data.dict())
            if not is_valid:
                raise ValueError(f"Invalid skill data: {', '.join(errors)}")

            # Check uniqueness
            slug = self.formatter.format_skill_slug(skill_data.name)
            existing_skills = self.db.query(Skill).filter(
                or_(
                    func.lower(Skill.name) == skill_data.name.lower(),
                    Skill.slug == slug
                )
            ).all()

            if existing_skills:
                for skill in existing_skills:
                    if skill.name.lower() == skill_data.name.lower():
                        raise ValueError(f"Skill with name '{skill_data.name}' already exists")
                    if skill.slug == slug:
                        raise ValueError(f"Skill with slug '{slug}' already exists")

            # Create skill
            skill = Skill(
                name=skill_data.name,
                slug=slug,
                description=skill_data.description,
                category_id=skill_data.category_id,
                status=skill_data.status,
                visibility=skill_data.visibility,
                content_type=skill_data.content_type,
                version=skill_data.version,
                author=skill_data.author,
                maintainer=skill_data.maintainer,
                license=skill_data.license,
                homepage=skill_data.homepage,
                repository=skill_data.repository,
                documentation=skill_data.documentation,
                keywords=skill_data.keywords,
                python_requires=skill_data.python_requires,
                dependencies=skill_data.dependencies,
                config=skill_data.config,
            )

            # Add to database
            self.db.add(skill)
            self.db.flush()  # Get skill ID without committing

            # Create initial version if content is provided
            if hasattr(skill_data, 'content') and skill_data.content:
                version = SkillVersion(
                    skill_id=skill.id,
                    version=skill_data.version,
                    content=skill_data.content,
                    content_format=getattr(skill_data, 'content_format', 'yaml'),
                    is_active=True,
                    is_latest=True,
                )
                self.db.add(version)
                self.db.flush()

            # Add tags if provided
            if hasattr(skill_data, 'tags') and skill_data.tags:
                await self._add_tags_to_skill(skill, skill_data.tags)

            # Commit transaction
            self.db.commit()
            self.db.refresh(skill)

            logger.info(f"Created skill: {skill.id} ({skill.name})")
            return self._to_skill_response(skill)

        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating skill: {e}")
            raise
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating skill: {e}")
            raise

    async def get_skill(self, skill_id: str) -> Optional[SkillResponse]:
        """Get skill by ID.

        Args:
            skill_id: Skill ID

        Returns:
            Skill response or None if not found
        """
        try:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return None

            return self._to_skill_response(skill)

        except SQLAlchemyError as e:
            logger.error(f"Database error getting skill {skill_id}: {e}")
            raise

    async def get_skill_by_slug(self, slug: str) -> Optional[SkillResponse]:
        """Get skill by slug.

        Args:
            slug: Skill slug

        Returns:
            Skill response or None if not found
        """
        try:
            skill = self.db.query(Skill).filter(Skill.slug == slug).first()
            if not skill:
                return None

            return self._to_skill_response(skill)

        except SQLAlchemyError as e:
            logger.error(f"Database error getting skill by slug {slug}: {e}")
            raise

    async def update_skill(self, skill_id: str, skill_data: SkillUpdate) -> Optional[SkillResponse]:
        """Update an existing skill.

        Args:
            skill_id: Skill ID
            skill_data: Skill update data

        Returns:
            Updated skill response or None if not found

        Raises:
            ValueError: If skill data is invalid
        """
        try:
            # Get existing skill
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return None

            # Validate update data
            update_dict = skill_data.dict(exclude_unset=True)
            if update_dict:
                is_valid, errors = self.validator.validate_skill_data(update_dict)
                if not is_valid:
                    raise ValueError(f"Invalid skill data: {', '.join(errors)}")

            # Update fields
            for field, value in update_dict.items():
                if hasattr(skill, field):
                    setattr(skill, field, value)

            # Update slug if name changed
            if 'name' in update_dict:
                skill.slug = self.formatter.format_skill_slug(skill.name)

            # Update timestamps
            skill.updated_at = datetime.utcnow()

            # Commit transaction
            self.db.commit()
            self.db.refresh(skill)

            logger.info(f"Updated skill: {skill.id} ({skill.name})")
            return self._to_skill_response(skill)

        except ValueError:
            raise
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error updating skill {skill_id}: {e}")
            raise

    async def delete_skill(self, skill_id: str) -> bool:
        """Delete a skill.

        Args:
            skill_id: Skill ID

        Returns:
            True if deleted, False if not found

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return False

            # Delete skill (cascades to versions and associations)
            self.db.delete(skill)
            self.db.commit()

            logger.info(f"Deleted skill: {skill_id}")
            return True

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deleting skill {skill_id}: {e}")
            raise

    async def list_skills(
        self,
        filters: Optional[SkillFilter] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> SkillSearchResult:
        """List skills with filtering and pagination.

        Args:
            filters: Skill filters
            page: Page number (1-based)
            page_size: Items per page
            sort_by: Sort field
            sort_order: Sort order ("asc" or "desc")

        Returns:
            Search result with items and pagination info
        """
        try:
            # Build query
            query = self.db.query(Skill)

            # Apply filters
            if filters:
                query = self._apply_filters(query, filters)

            # Get total count
            total = query.count()

            # Apply sorting
            sort_field = getattr(Skill, sort_by, Skill.updated_at)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))

            # Apply pagination
            offset = (page - 1) * page_size
            skills = query.offset(offset).limit(page_size).all()

            # Convert to response format
            items = [self._to_skill_list_item(skill) for skill in skills]

            # Calculate pagination
            pages = (total + page_size - 1) // page_size

            return SkillSearchResult(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                pages=pages,
                has_next=page < pages,
                has_prev=page > 1,
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error listing skills: {e}")
            raise

    async def search_skills(self, search: SkillSearch) -> SkillSearchResult:
        """Search skills with advanced options.

        Args:
            search: Search parameters

        Returns:
            Search result
        """
        try:
            # Build base query
            query = self.db.query(Skill)

            # Apply text search
            if search.query:
                search_term = f"%{search.query.lower()}%"
                query = query.filter(
                    or_(
                        func.lower(Skill.name).like(search_term),
                        func.lower(Skill.description).like(search_term),
                        Skill.keywords.contains([search.query.lower()]),
                    )
                )

            # Apply filters
            if search.filters:
                query = self._apply_filters(query, search.filters)

            # Get total count
            total = query.count()

            # Apply sorting
            sort_field = getattr(Skill, search.sort_by, Skill.updated_at)
            if search.sort_order.lower() == "desc":
                query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(asc(sort_field))

            # Apply pagination
            offset = (search.page - 1) * search.page_size
            skills = query.offset(offset).limit(search.page_size).all()

            # Convert to response format
            items = [self._to_skill_list_item(skill) for skill in skills]

            # Calculate pagination
            pages = (total + search.page_size - 1) // search.page_size

            return SkillSearchResult(
                items=items,
                total=total,
                page=search.page,
                page_size=search.page_size,
                pages=pages,
                has_next=search.page < pages,
                has_prev=search.page > 1,
                query=search.query,
                filters_applied=search.filters.dict() if search.filters else None,
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error searching skills: {e}")
            raise

    # ================================
    # State Management
    # ================================

    async def activate_skill(self, skill_id: str) -> Optional[SkillResponse]:
        """Activate a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Updated skill response or None if not found
        """
        try:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return None

            skill.activate()
            skill.updated_at = datetime.utcnow()

            if not skill.published_at:
                skill.published_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(skill)

            logger.info(f"Activated skill: {skill_id}")
            return self._to_skill_response(skill)

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error activating skill {skill_id}: {e}")
            raise

    async def deactivate_skill(self, skill_id: str) -> Optional[SkillResponse]:
        """Deactivate a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Updated skill response or None if not found
        """
        try:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return None

            skill.deactivate()
            skill.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(skill)

            logger.info(f"Deactivated skill: {skill_id}")
            return self._to_skill_response(skill)

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deactivating skill {skill_id}: {e}")
            raise

    async def deprecate_skill(self, skill_id: str) -> Optional[SkillResponse]:
        """Mark a skill as deprecated.

        Args:
            skill_id: Skill ID

        Returns:
            Updated skill response or None if not found
        """
        try:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return None

            skill.deprecate()
            skill.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(skill)

            logger.info(f"Deprecated skill: {skill_id}")
            return self._to_skill_response(skill)

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error deprecating skill {skill_id}: {e}")
            raise

    async def archive_skill(self, skill_id: str) -> Optional[SkillResponse]:
        """Archive a skill.

        Args:
            skill_id: Skill ID

        Returns:
            Updated skill response or None if not found
        """
        try:
            skill = self.db.query(Skill).filter(Skill.id == skill_id).first()
            if not skill:
                return None

            skill.archive()
            skill.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(skill)

            logger.info(f"Archived skill: {skill_id}")
            return self._to_skill_response(skill)

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error archiving skill {skill_id}: {e}")
            raise

    # ================================
    # Statistics
    # ================================

    async def get_skill_stats(self) -> SkillStats:
        """Get skill statistics.

        Returns:
            Skill statistics
        """
        try:
            # Get basic counts
            total_skills = self.db.query(Skill).count()
            active_skills = self.db.query(Skill).filter(Skill.status == "active").count()
            draft_skills = self.db.query(Skill).filter(Skill.status == "draft").count()
            deprecated_skills = self.db.query(Skill).filter(Skill.status == "deprecated").count()
            archived_skills = self.db.query(Skill).filter(Skill.status == "archived").count()

            # Get usage statistics
            total_downloads = self.db.query(func.sum(Skill.download_count)).scalar() or 0
            total_views = self.db.query(func.sum(Skill.view_count)).scalar() or 0
            total_likes = self.db.query(func.sum(Skill.like_count)).scalar() or 0

            # Get rating statistics
            avg_rating = self.db.query(func.avg(Skill.rating)).scalar() or 0.0
            total_ratings = self.db.query(func.sum(Skill.rating_count)).scalar() or 0

            # Get quality statistics
            avg_quality_score = self.db.query(func.avg(Skill.quality_score)).scalar() or 0.0
            avg_completeness = self.db.query(func.avg(Skill.completeness)).scalar() or 0.0

            # Get category distribution
            categories = self.db.query(
                SkillCategory.name,
                func.count(Skill.id).label('count')
            ).outerjoin(Skill).group_by(SkillCategory.id).all()

            category_dist = [{"name": cat[0], "count": cat[1]} for cat in categories if cat[0]]

            # Get top tags
            tags = self.db.query(
                SkillTag.name,
                func.count(Skill.id).label('count')
            ).join(SkillTagAssociation).join(Skill).group_by(SkillTag.id).order_by(desc('count')).limit(10).all()

            tag_dist = [{"name": tag[0], "count": tag[1]} for tag in tags if tag[0]]

            # Get content type distribution
            content_types = self.db.query(
                Skill.content_type,
                func.count(Skill.id).label('count')
            ).group_by(Skill.content_type).all()

            type_dist = [{"type": ct[0], "count": ct[1]} for ct in content_types if ct[0]]

            return SkillStats(
                total_skills=total_skills,
                active_skills=active_skills,
                draft_skills=draft_skills,
                deprecated_skills=deprecated_skills,
                archived_skills=archived_skills,
                total_downloads=total_downloads,
                total_views=total_views,
                total_likes=total_likes,
                avg_rating=round(avg_rating, 2),
                total_ratings=total_ratings,
                avg_quality_score=round(avg_quality_score, 2),
                avg_completeness=round(avg_completeness, 2),
                categories=category_dist,
                top_tags=tag_dist,
                content_types=type_dist,
            )

        except SQLAlchemyError as e:
            logger.error(f"Database error getting skill stats: {e}")
            raise

    # ================================
    # Bulk Operations
    # ================================

    async def bulk_operation(self, operation: SkillBulkOperation) -> SkillBulkResult:
        """Perform bulk operation on skills.

        Args:
            operation: Bulk operation parameters

        Returns:
            Bulk operation result
        """
        try:
            skills = self.db.query(Skill).filter(Skill.id.in_(operation.skill_ids)).all()

            succeeded_ids = []
            failed_ids = []
            errors = []

            for skill in skills:
                try:
                    await self._perform_single_operation(skill, operation)
                    succeeded_ids.append(skill.id)
                except Exception as e:
                    failed_ids.append(skill.id)
                    errors.append({
                        "skill_id": skill.id,
                        "error": str(e),
                    })

            # Commit successful operations
            if succeeded_ids:
                self.db.commit()

            result = SkillBulkResult(
                operation=operation.operation,
                total_requested=len(operation.skill_ids),
                total_succeeded=len(succeeded_ids),
                total_failed=len(failed_ids),
                succeeded_ids=succeeded_ids,
                failed_ids=failed_ids,
                errors=errors,
                processed_at=datetime.utcnow(),
            )

            logger.info(f"Bulk operation '{operation.operation}' completed: "
                       f"{len(succeeded_ids)} succeeded, {len(failed_ids)} failed")

            return result

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error in bulk operation: {e}")
            raise

    # ================================
    # Helper Methods
    # ================================

    def _apply_filters(self, query, filters: SkillFilter):
        """Apply filters to query.

        Args:
            query: SQLAlchemy query
            filters: Filter parameters

        Returns:
            Filtered query
        """
        # Status filter
        if filters.status:
            query = query.filter(Skill.status.in_(filters.status))

        # Visibility filter
        if filters.visibility:
            query = query.filter(Skill.visibility.in_(filters.visibility))

        # Category filter
        if filters.category_id:
            query = query.filter(Skill.category_id == filters.category_id)

        # Author filter
        if filters.author:
            query = query.filter(func.lower(Skill.author) == filters.author.lower())

        # Maintainer filter
        if filters.maintainer:
            query = query.filter(func.lower(Skill.maintainer) == filters.maintainer.lower())

        # Content type filter
        if filters.content_type:
            query = query.filter(Skill.content_type == filters.content_type)

        # Quality filters
        if filters.min_quality_score:
            query = query.filter(Skill.quality_score >= filters.min_quality_score)

        if filters.min_rating:
            query = query.filter(Skill.rating >= filters.min_rating)

        # Date filters
        if filters.created_after:
            query = query.filter(Skill.created_at >= filters.created_after)

        if filters.created_before:
            query = query.filter(Skill.created_at <= filters.created_before)

        if filters.updated_after:
            query = query.filter(Skill.updated_at >= filters.updated_after)

        if filters.updated_before:
            query = query.filter(Skill.updated_at <= filters.updated_before)

        if filters.published_after:
            query = query.filter(Skill.published_at >= filters.published_after)

        if filters.published_before:
            query = query.filter(Skill.published_at <= filters.published_before)

        # Usage filters
        if filters.min_downloads:
            query = query.filter(Skill.download_count >= filters.min_downloads)

        if filters.min_views:
            query = query.filter(Skill.view_count >= filters.min_views)

        if filters.min_likes:
            query = query.filter(Skill.like_count >= filters.min_likes)

        # Keyword filter
        if filters.keyword:
            query = query.filter(Skill.keywords.contains([filters.keyword.lower()]))

        # Tag filter
        if filters.tag:
            query = query.join(SkillTagAssociation).join(SkillTag).filter(
                func.lower(SkillTag.name) == filters.tag.lower()
            )

        return query

    async def _add_tags_to_skill(self, skill: Skill, tags: List[str]):
        """Add tags to a skill.

        Args:
            skill: Skill instance
            tags: List of tag names
        """
        for tag_name in tags:
            # Get or create tag
            tag = self.db.query(SkillTag).filter(
                func.lower(SkillTag.name) == tag_name.lower()
            ).first()

            if not tag:
                tag = SkillTag(name=tag_name)
                self.db.add(tag)
                self.db.flush()

            # Add association
            if tag not in skill.tags:
                skill.tags.append(tag)
                tag.increment_usage()

    async def _perform_single_operation(self, skill: Skill, operation: SkillBulkOperation):
        """Perform a single bulk operation on a skill.

        Args:
            skill: Skill instance
            operation: Operation parameters
        """
        if operation.operation == "activate":
            skill.activate()
        elif operation.operation == "deactivate":
            skill.deactivate()
        elif operation.operation == "deprecate":
            skill.deprecate()
        elif operation.operation == "archive":
            skill.archive()
        elif operation.operation == "update_status" and operation.parameters:
            status = operation.parameters.get("status")
            if status:
                skill.status = status

        skill.updated_at = datetime.utcnow()

    def _to_skill_response(self, skill: Skill) -> SkillResponse:
        """Convert skill model to response.

        Args:
            skill: Skill model instance

        Returns:
            Skill response
        """
        return SkillResponse(
            id=skill.id,
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            status=skill.status,
            visibility=skill.visibility,
            version=skill.version,
            author=skill.author,
            maintainer=skill.maintainer,
            license=skill.license,
            homepage=skill.homepage,
            repository=skill.repository,
            documentation=skill.documentation,
            keywords=skill.keywords,
            python_requires=skill.python_requires,
            dependencies=skill.dependencies,
            quality_score=skill.quality_score,
            completeness=skill.completeness,
            download_count=skill.download_count,
            view_count=skill.view_count,
            like_count=skill.like_count,
            rating=skill.rating,
            rating_count=skill.rating_count,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
            published_at=skill.published_at,
            deprecated_at=skill.deprecated_at,
            archived_at=skill.archived_at,
            category=(
                {"id": skill.category.id, "name": skill.category.name}
                if skill.category
                else None
            ),
            tags=[
                {"id": tag.id, "name": tag.name, "color": tag.color}
                for tag in skill.tags
            ] if skill.tags else None,
        )

    def _to_skill_list_item(self, skill: Skill) -> SkillListItem:
        """Convert skill model to list item.

        Args:
            skill: Skill model instance

        Returns:
            Skill list item
        """
        return SkillListItem(
            id=skill.id,
            name=skill.name,
            slug=skill.slug,
            description=skill.description,
            status=skill.status,
            visibility=skill.visibility,
            version=skill.version,
            author=skill.author,
            rating=skill.rating,
            rating_count=skill.rating_count,
            download_count=skill.download_count,
            view_count=skill.view_count,
            like_count=skill.like_count,
            quality_score=skill.quality_score,
            created_at=skill.created_at,
            updated_at=skill.updated_at,
            published_at=skill.published_at,
            category_name=skill.category.name if skill.category else None,
            tags=[tag.name for tag in skill.tags] if skill.tags else None,
        )
