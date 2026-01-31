"""Create initial skill management tables

Revision ID: 001
Revises:
Create Date: 2026-02-01 00:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Create skill_categories table
    op.create_table('skill_categories',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.String(length=36), sa.ForeignKey('skill_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('icon', sa.String(length=100), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('skill_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_skill_categories_name'), 'skill_categories', ['name'], unique=False)
    op.create_index(op.f('idx_skill_categories_slug'), 'skill_categories', ['slug'], unique=True)
    op.create_index(op.f('idx_skill_categories_parent_id'), 'skill_categories', ['parent_id'], unique=False)
    op.create_index(op.f('idx_skill_categories_is_active'), 'skill_categories', ['is_active'], unique=False)
    op.create_index(op.f('idx_skill_categories_created_at'), 'skill_categories', ['created_at'], unique=False)

    # Create skill_tags table
    op.create_table('skill_tags',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=True),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_skill_tags_name'), 'skill_tags', ['name'], unique=False)
    op.create_index(op.f('idx_skill_tags_slug'), 'skill_tags', ['slug'], unique=True)
    op.create_index(op.f('idx_skill_tags_usage_count'), 'skill_tags', ['usage_count'], unique=False)
    op.create_index(op.f('idx_skill_tags_created_at'), 'skill_tags', ['created_at'], unique=False)

    # Create skills table
    op.create_table('skills',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category_id', sa.String(length=36), sa.ForeignKey('skill_categories.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, default='draft'),
        sa.Column('visibility', sa.String(length=20), nullable=False, default='public'),
        sa.Column('content_type', sa.String(length=50), nullable=False, default='yaml'),
        sa.Column('version', sa.String(length=50), nullable=False, default='1.0.0'),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('maintainer', sa.String(length=100), nullable=True),
        sa.Column('license', sa.String(length=50), nullable=True),
        sa.Column('homepage', sa.String(length=500), nullable=True),
        sa.Column('repository', sa.String(length=500), nullable=True),
        sa.Column('documentation', sa.String(length=500), nullable=True),
        sa.Column('keywords', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('python_requires', sa.String(length=50), nullable=True),
        sa.Column('dependencies', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('completeness', sa.Float(), nullable=False, default=0.0),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('view_count', sa.Integer(), nullable=False, default=0),
        sa.Column('like_count', sa.Integer(), nullable=False, default=0),
        sa.Column('rating', sa.Float(), nullable=False, default=0.0),
        sa.Column('rating_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deprecated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_skill_slug')
    )
    op.create_index(op.f('idx_skill_name'), 'skills', ['name'], unique=False)
    op.create_index(op.f('idx_skill_status'), 'skills', ['status'], unique=False)
    op.create_index(op.f('idx_skill_visibility'), 'skills', ['visibility'], unique=False)
    op.create_index(op.f('idx_skill_category_id'), 'skills', ['category_id'], unique=False)
    op.create_index(op.f('idx_skill_created_at'), 'skills', ['created_at'], unique=False)
    op.create_index(op.f('idx_skill_updated_at'), 'skills', ['updated_at'], unique=False)
    op.create_index(op.f('idx_skill_published_at'), 'skills', ['published_at'], unique=False)
    op.create_index(op.f('idx_skill_quality_score'), 'skills', ['quality_score'], unique=False)
    op.create_index(op.f('idx_skill_download_count'), 'skills', ['download_count'], unique=False)
    op.create_index(op.f('idx_skill_rating'), 'skills', ['rating'], unique=False)
    op.create_index(op.f('idx_skill_rating_count'), 'skills', ['rating_count'], unique=False)

    # Create skill_versions table
    op.create_table('skill_versions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('skill_id', sa.String(length=36), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=100), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_stable', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_prerelease', sa.Boolean(), nullable=False, default=False),
        sa.Column('download_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('skill_id', 'version', name='uq_skill_version')
    )
    op.create_index(op.f('idx_skill_versions_skill_id'), 'skill_versions', ['skill_id'], unique=False)
    op.create_index(op.f('idx_skill_versions_version'), 'skill_versions', ['version'], unique=False)
    op.create_index(op.f('idx_skill_versions_is_active'), 'skill_versions', ['is_active'], unique=False)
    op.create_index(op.f('idx_skill_versions_is_stable'), 'skill_versions', ['is_stable'], unique=False)
    op.create_index(op.f('idx_skill_versions_created_at'), 'skill_versions', ['created_at'], unique=False)

    # Create skill_tag_associations table (many-to-many)
    op.create_table('skill_tag_associations',
        sa.Column('skill_id', sa.String(length=36), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_id', sa.String(length=36), sa.ForeignKey('skill_tags.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('skill_id', 'tag_id')
    )
    op.create_index(op.f('idx_skill_tag_skill_id'), 'skill_tag_associations', ['skill_id'], unique=False)
    op.create_index(op.f('idx_skill_tag_tag_id'), 'skill_tag_associations', ['tag_id'], unique=False)

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_skills_category_id',
        'skills', 'skill_categories',
        ['category_id'], ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_skill_versions_skill_id',
        'skill_versions', 'skills',
        ['skill_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_skill_tag_associations_skill_id',
        'skill_tag_associations', 'skills',
        ['skill_id'], ['id'],
        ondelete='CASCADE'
    )

    op.create_foreign_key(
        'fk_skill_tag_associations_tag_id',
        'skill_tag_associations', 'skill_tags',
        ['tag_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop foreign keys
    op.drop_constraint('fk_skill_tag_associations_tag_id', 'skill_tag_associations', type_='foreignkey')
    op.drop_constraint('fk_skill_tag_associations_skill_id', 'skill_tag_associations', type_='foreignkey')
    op.drop_constraint('fk_skill_versions_skill_id', 'skill_versions', type_='foreignkey')
    op.drop_constraint('fk_skills_category_id', 'skills', type_='foreignkey')

    # Drop tables
    op.drop_table('skill_tag_associations')
    op.drop_table('skill_versions')
    op.drop_table('skills')
    op.drop_table('skill_tags')
    op.drop_table('skill_categories')
