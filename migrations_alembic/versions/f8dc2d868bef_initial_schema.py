"""initial schema

Revision ID: f8dc2d868bef
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
import sqlalchemy as sa
from alembic import op

revision = 'f8dc2d868bef'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'blog_author',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(254), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'blog_tag',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), nullable=False, unique=True),
        sa.Column('slug', sa.String(50), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
    )

    op.create_table(
        'blog_article',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), nullable=False, unique=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('view_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('author_id', sa.Integer(), sa.ForeignKey('blog_author.id'), nullable=False),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'blog_article_tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('blog_article.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('blog_tag.id', ondelete='CASCADE'), nullable=False),
    )

    # Índices útiles para las queries más frecuentes
    op.create_index('ix_blog_article_status', 'blog_article', ['status'])
    op.create_index('ix_blog_article_author_id', 'blog_article', ['author_id'])
    op.create_index('ix_blog_article_published_at', 'blog_article', ['published_at'])


def downgrade() -> None:
    op.drop_index('ix_blog_article_published_at', table_name='blog_article')
    op.drop_index('ix_blog_article_author_id', table_name='blog_article')
    op.drop_index('ix_blog_article_status', table_name='blog_article')
    op.drop_table('blog_article_tags')
    op.drop_table('blog_article')
    op.drop_table('blog_tag')
    op.drop_table('blog_author')
