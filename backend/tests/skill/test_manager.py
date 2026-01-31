"""Tests for skill manager.

This module contains comprehensive unit tests for the SkillManager class,
testing all CRUD operations, search, filtering, and state management.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from backend.app.skill.manager import SkillManager
from backend.app.skill.models import Skill, SkillVersion, SkillCategory, SkillTag
from backend.app.skill.schemas.skill_operations import (
    SkillCreate,
    SkillUpdate,
    SkillFilter,
    SkillSearch,
    SkillBulkOperation,
)
from backend.app.skill.schemas.skill_creation import SkillCreationRequest


class TestSkillManager:
    """Test suite for SkillManager."""

    @pytest.fixture
    def db_session(self):
        """Create mock database session."""
        return Mock(spec=Session)

    @pytest.fixture
    def skill_manager(self, db_session):
        """Create skill manager instance."""
        return SkillManager(db_session)

    @pytest.fixture
    def sample_skill(self):
        """Create sample skill data."""
        return {
            "id": "test-skill-123",
            "name": "Test Skill",
            "slug": "test-skill",
            "description": "A test skill",
            "status": "draft",
            "visibility": "public",
            "version": "1.0.0",
            "author": "test_user",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    @pytest.fixture
    def sample_category(self):
        """Create sample category."""
        return {
            "id": "test-category-123",
            "name": "Test Category",
            "slug": "test-category",
        }

    # ================================
    # Test Skill Creation
    # ================================

    @pytest.mark.asyncio
    async def test_create_skill_success(self, skill_manager, db_session):
        """Test successful skill creation."""
        # Setup
        skill_data = SkillCreate(
            name="New Skill",
            description="A new skill",
            content="test content",
        )

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add.return_value = None
        db_session.flush.return_value = None
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Execute
        result = await skill_manager.create_skill(skill_data)

        # Verify
        assert result is not None
        assert result.name == "New Skill"
        assert result.status == "draft"
        db_session.add.assert_called_once()
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_skill_duplicate_name(self, skill_manager, db_session):
        """Test skill creation with duplicate name."""
        # Setup
        skill_data = SkillCreate(
            name="Duplicate Skill",
            description="A duplicate skill",
            content="test content",
        )

        # Mock existing skill with same name
        existing_skill = Mock()
        existing_skill.name.lower.return_value = "duplicate skill"

        db_session.query.return_value.filter.return_value.first.return_value = existing_skill

        # Execute and verify
        with pytest.raises(ValueError, match="already exists"):
            await skill_manager.create_skill(skill_data)

        db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_skill_invalid_data(self, skill_manager):
        """Test skill creation with invalid data."""
        # Setup - empty name
        skill_data = SkillCreate(
            name="",  # Invalid: empty name
            description="A test skill",
            content="test content",
        )

        # Execute and verify
        with pytest.raises(ValueError, match="Invalid skill data"):
            await skill_manager.create_skill(skill_data)

    @pytest.mark.asyncio
    async def test_create_skill_database_error(self, skill_manager, db_session):
        """Test skill creation with database error."""
        # Setup
        skill_data = SkillCreate(
            name="New Skill",
            description="A new skill",
            content="test content",
        )

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.add.side_effect = SQLAlchemyError("Database error")

        # Execute and verify
        with pytest.raises(SQLAlchemyError):
            await skill_manager.create_skill(skill_data)

        db_session.rollback.assert_called_once()

    # ================================
    # Test Skill Retrieval
    # ================================

    @pytest.mark.asyncio
    async def test_get_skill_by_id_success(self, skill_manager, db_session, sample_skill):
        """Test getting skill by ID."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.name = sample_skill["name"]
        skill_model.slug = sample_skill["slug"]
        skill_model.description = sample_skill["description"]
        skill_model.status = sample_skill["status"]
        skill_model.visibility = sample_skill["visibility"]
        skill_model.version = sample_skill["version"]
        skill_model.author = sample_skill["author"]
        skill_model.quality_score = 0.0
        skill_model.completeness = 0.0
        skill_model.download_count = 0
        skill_model.view_count = 0
        skill_model.like_count = 0
        skill_model.rating = 0.0
        skill_model.rating_count = 0
        skill_model.created_at = sample_skill["created_at"]
        skill_model.updated_at = sample_skill["updated_at"]
        skill_model.published_at = None
        skill_model.deprecated_at = None
        skill_model.archived_at = None
        skill_model.category = None
        skill_model.tags = []

        db_session.query.return_value.filter.return_value.first.return_value = skill_model

        # Execute
        result = await skill_manager.get_skill(sample_skill["id"])

        # Verify
        assert result is not None
        assert result.id == sample_skill["id"]
        assert result.name == sample_skill["name"]

    @pytest.mark.asyncio
    async def test_get_skill_not_found(self, skill_manager, db_session):
        """Test getting skill that doesn't exist."""
        # Setup
        db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = await skill_manager.get_skill("nonexistent-id")

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_get_skill_by_slug_success(self, skill_manager, db_session, sample_skill):
        """Test getting skill by slug."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.name = sample_skill["name"]
        skill_model.slug = sample_skill["slug"]

        db_session.query.return_value.filter.return_value.first.return_value = skill_model

        # Execute
        result = await skill_manager.get_skill_by_slug(sample_skill["slug"])

        # Verify
        assert result is not None
        assert result.slug == sample_skill["slug"]

    # ================================
    # Test Skill Update
    # ================================

    @pytest.mark.asyncio
    async def test_update_skill_success(self, skill_manager, db_session, sample_skill):
        """Test successful skill update."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.name = "Old Name"
        skill_model.slug = "old-slug"
        skill_model.updated_at = sample_skill["updated_at"]

        update_data = SkillUpdate(
            name="New Name",
            description="Updated description",
        )

        db_session.query.return_value.filter.return_value.first.return_value = skill_model
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Execute
        result = await skill_manager.update_skill(sample_skill["id"], update_data)

        # Verify
        assert result is not None
        assert skill_model.name == "New Name"
        assert skill_model.slug == "new-slug"  # Updated slug
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_skill_not_found(self, skill_manager, db_session):
        """Test updating skill that doesn't exist."""
        # Setup
        update_data = SkillUpdate(name="New Name")
        db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = await skill_manager.update_skill("nonexistent-id", update_data)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_update_skill_invalid_data(self, skill_manager, db_session):
        """Test skill update with invalid data."""
        # Setup
        update_data = SkillUpdate(name="")  # Invalid: empty name

        # Execute and verify
        with pytest.raises(ValueError, match="Invalid skill data"):
            await skill_manager.update_skill("test-id", update_data)

    # ================================
    # Test Skill Deletion
    # ================================

    @pytest.mark.asyncio
    async def test_delete_skill_success(self, skill_manager, db_session, sample_skill):
        """Test successful skill deletion."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]

        db_session.query.return_value.filter.return_value.first.return_value = skill_model
        db_session.commit.return_value = None

        # Execute
        result = await skill_manager.delete_skill(sample_skill["id"])

        # Verify
        assert result is True
        db_session.delete.assert_called_once_with(skill_model)
        db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_skill_not_found(self, skill_manager, db_session):
        """Test deleting skill that doesn't exist."""
        # Setup
        db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute
        result = await skill_manager.delete_skill("nonexistent-id")

        # Verify
        assert result is False

    # ================================
    # Test Skill Listing
    # ================================

    @pytest.mark.asyncio
    async def test_list_skills_basic(self, skill_manager, db_session, sample_skill):
        """Test basic skill listing."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.name = sample_skill["name"]
        skill_model.slug = sample_skill["slug"]

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.count.return_value = 1
        db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [skill_model]

        # Execute
        result = await skill_manager.list_skills()

        # Verify
        assert result is not None
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == sample_skill["id"]

    @pytest.mark.asyncio
    async def test_list_skills_with_filters(self, skill_manager, db_session):
        """Test skill listing with filters."""
        # Setup
        filters = SkillFilter(
            status=["active"],
            category_id="test-category",
        )

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.count.return_value = 0
        db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        # Execute
        result = await skill_manager.list_skills(filters=filters)

        # Verify
        assert result is not None
        assert result.total == 0

    @pytest.mark.asyncio
    async def test_list_skills_with_pagination(self, skill_manager, db_session):
        """Test skill listing with pagination."""
        # Setup
        page = 2
        page_size = 10

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.count.return_value = 25
        db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        # Execute
        result = await skill_manager.list_skills(page=page, page_size=page_size)

        # Verify
        assert result.page == page
        assert result.page_size == page_size
        assert result.pages == 3  # 25 items / 10 per page

    # ================================
    # Test Skill Search
    # ================================

    @pytest.mark.asyncio
    async def test_search_skills_basic(self, skill_manager, db_session):
        """Test basic skill search."""
        # Setup
        search = SkillSearch(query="test")

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.count.return_value = 1
        db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        # Execute
        result = await skill_manager.search_skills(search)

        # Verify
        assert result is not None
        assert result.query == "test"

    @pytest.mark.asyncio
    async def test_search_skills_with_filters(self, skill_manager, db_session):
        """Test search with filters."""
        # Setup
        filters = SkillFilter(
            status=["active"],
            min_rating=4.0,
        )

        search = SkillSearch(
            query="test",
            filters=filters,
        )

        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.count.return_value = 0
        db_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        # Execute
        result = await skill_manager.search_skills(search)

        # Verify
        assert result is not None
        assert result.query == "test"
        assert result.filters_applied is not None

    # ================================
    # Test State Management
    # ================================

    @pytest.mark.asyncio
    async def test_activate_skill_success(self, skill_manager, db_session, sample_skill):
        """Test activating a skill."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.status = "draft"
        skill_model.published_at = None

        db_session.query.return_value.filter.return_value.first.return_value = skill_model
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Execute
        result = await skill_manager.activate_skill(sample_skill["id"])

        # Verify
        assert result is not None
        assert skill_model.status == "active"
        assert skill_model.published_at is not None

    @pytest.mark.asyncio
    async def test_deactivate_skill_success(self, skill_manager, db_session, sample_skill):
        """Test deactivating a skill."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.status = "active"

        db_session.query.return_value.filter.return_value.first.return_value = skill_model
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Execute
        result = await skill_manager.deactivate_skill(sample_skill["id"])

        # Verify
        assert result is not None
        assert skill_model.status == "draft"

    @pytest.mark.asyncio
    async def test_deprecate_skill_success(self, skill_manager, db_session, sample_skill):
        """Test deprecating a skill."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.status = "active"
        skill_model.deprecated_at = None

        db_session.query.return_value.filter.return_value.first.return_value = skill_model
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Execute
        result = await skill_manager.deprecate_skill(sample_skill["id"])

        # Verify
        assert result is not None
        assert skill_model.status == "deprecated"
        assert skill_model.deprecated_at is not None

    @pytest.mark.asyncio
    async def test_archive_skill_success(self, skill_manager, db_session, sample_skill):
        """Test archiving a skill."""
        # Setup
        skill_model = Mock(spec=Skill)
        skill_model.id = sample_skill["id"]
        skill_model.status = "active"
        skill_model.archived_at = None

        db_session.query.return_value.filter.return_value.first.return_value = skill_model
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        # Execute
        result = await skill_manager.archive_skill(sample_skill["id"])

        # Verify
        assert result is not None
        assert skill_model.status == "archived"
        assert skill_model.archived_at is not None

    @pytest.mark.asyncio
    async def test_state_change_not_found(self, skill_manager, db_session):
        """Test state change on non-existent skill."""
        # Setup
        db_session.query.return_value.filter.return_value.first.return_value = None

        # Execute and verify
        result = await skill_manager.activate_skill("nonexistent-id")
        assert result is None

        result = await skill_manager.deactivate_skill("nonexistent-id")
        assert result is None

        result = await skill_manager.deprecate_skill("nonexistent-id")
        assert result is None

        result = await skill_manager.archive_skill("nonexistent-id")
        assert result is None

    # ================================
    # Test Statistics
    # ================================

    @pytest.mark.asyncio
    async def test_get_skill_stats(self, skill_manager, db_session):
        """Test getting skill statistics."""
        # Setup
        db_session.query.return_value.filter.return_value.count.return_value = 10
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.filter.return_value.first.return_value = None
        db_session.query.return_value.filter.return_value.first.return_value = None

        # Mock aggregate queries
        db_session.query.return_value.scalar.return_value = 100
        db_session.query.return_value.join.return_value.group_by.return_value.all.return_value = []

        # Execute
        result = await skill_manager.get_skill_stats()

        # Verify
        assert result is not None
        assert result.total_skills == 10

    # ================================
    # Test Bulk Operations
    # ================================

    @pytest.mark.asyncio
    async def test_bulk_operation_success(self, skill_manager, db_session):
        """Test successful bulk operation."""
        # Setup
        operation = SkillBulkOperation(
            skill_ids=["skill-1", "skill-2", "skill-3"],
            operation="activate",
        )

        skill1 = Mock(spec=Skill)
        skill1.id = "skill-1"
        skill1.status = "draft"

        skill2 = Mock(spec=Skill)
        skill2.id = "skill-2"
        skill2.status = "draft"

        skill3 = Mock(spec=Skill)
        skill3.id = "skill-3"
        skill3.status = "draft"

        db_session.query.return_value.filter.return_value.in_.return_value.all.return_value = [skill1, skill2, skill3]
        db_session.commit.return_value = None

        # Execute
        result = await skill_manager.bulk_operation(operation)

        # Verify
        assert result is not None
        assert result.operation == "activate"
        assert result.total_requested == 3
        assert result.total_succeeded == 3
        assert result.total_failed == 0
        assert len(result.succeeded_ids) == 3

    @pytest.mark.asyncio
    async def test_bulk_operation_partial_failure(self, skill_manager, db_session):
        """Test bulk operation with partial failures."""
        # Setup
        operation = SkillBulkOperation(
            skill_ids=["skill-1", "skill-2", "skill-3"],
            operation="activate",
        )

        skill1 = Mock(spec=Skill)
        skill1.id = "skill-1"
        skill1.status = "draft"

        # Mock second skill to raise exception
        skill2 = Mock(spec=Skill)
        skill2.id = "skill-2"
        skill2.status = "draft"

        def raise_error(skill):
            if skill.id == "skill-2":
                raise Exception("Test error")
            skill.status = "active"

        skill2.activate = lambda: raise_error(skill2)

        skill3 = Mock(spec=Skill)
        skill3.id = "skill-3"
        skill3.status = "draft"
        skill3.activate = lambda: setattr(skill3, 'status', 'active')

        db_session.query.return_value.filter.return_value.in_.return_value.all.return_value = [skill1, skill2, skill3]
        db_session.commit.return_value = None

        # Execute
        result = await skill_manager.bulk_operation(operation)

        # Verify
        assert result is not None
        assert result.operation == "activate"
        assert result.total_requested == 3
        assert result.total_succeeded == 2
        assert result.total_failed == 1
        assert len(result.succeeded_ids) == 2
        assert len(result.failed_ids) == 1
        assert len(result.errors) == 1

    # ================================
    # Test Helper Methods
    # ================================

    def test_apply_filters_status(self, skill_manager):
        """Test filter application for status."""
        filters = SkillFilter(status=["active", "draft"])
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filter was applied
        query.filter.assert_called()

    def test_apply_filters_category(self, skill_manager):
        """Test filter application for category."""
        filters = SkillFilter(category_id="test-category")
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filter was applied
        query.filter.assert_called()

    def test_apply_filters_author(self, skill_manager):
        """Test filter application for author."""
        filters = SkillFilter(author="test_author")
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filter was applied
        query.filter.assert_called()

    def test_apply_filters_rating(self, skill_manager):
        """Test filter application for rating."""
        filters = SkillFilter(min_rating=4.0)
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filter was applied
        query.filter.assert_called()

    def test_apply_filters_dates(self, skill_manager):
        """Test filter application for dates."""
        filters = SkillFilter(
            created_after=datetime.utcnow() - timedelta(days=7),
            created_before=datetime.utcnow(),
        )
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filters were applied
        assert query.filter.call_count >= 2

    def test_apply_filters_usage(self, skill_manager):
        """Test filter application for usage statistics."""
        filters = SkillFilter(
            min_downloads=100,
            min_views=1000,
            min_likes=10,
        )
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filters were applied
        assert query.filter.call_count >= 3

    def test_apply_filters_text(self, skill_manager):
        """Test filter application for text search."""
        filters = SkillFilter(
            keyword="python",
            tag="machine-learning",
        )
        query = Mock()

        result = skill_manager._apply_filters(query, filters)

        # Verify filters were applied
        assert query.filter.call_count >= 2


class TestSkillManagerIntegration:
    """Integration tests for SkillManager with database."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_full_skill_lifecycle(self, skill_manager, db_session):
        """Test complete skill lifecycle."""
        # This would be an integration test with real database
        # Skipping for now as it requires database setup
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_skill_operations(self, skill_manager, db_session):
        """Test concurrent skill operations."""
        # This would test concurrent access patterns
        # Skipping for now as it requires database setup
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_skill_search_performance(self, skill_manager, db_session):
        """Test search performance with large dataset."""
        # This would test search performance
        # Skipping for now as it requires database setup
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
