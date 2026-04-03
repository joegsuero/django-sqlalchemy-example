"""
SQLAlchemy ORM models for the blog application.
Uses separate metadata to avoid conflicts with other apps.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Table, MetaData
)
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship,
    Session
)


# Create app-specific metadata (avoid sharing with other apps)
metadata = MetaData()


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models in blog app."""
    metadata = metadata


# Association table for many-to-many relationship
article_tags = Table(
    'blog_article_tags',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('article_id', Integer, ForeignKey('blog_article.id', ondelete='CASCADE')),
    Column('tag_id', Integer, ForeignKey('blog_tag.id', ondelete='CASCADE')),
)


class Author(Base):
    """Author model - represents blog authors."""
    __tablename__ = 'blog_author'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(254), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    articles: Mapped[List['Article']] = relationship(
        'Article',
        back_populates='author',
        cascade='all, delete-orphan',
    )


class Tag(Base):
    """Tag model for categorizing articles."""
    __tablename__ = 'blog_tag'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    articles: Mapped[List['Article']] = relationship(
        'Article',
        secondary=article_tags,
        back_populates='tags',
    )


class Article(Base):
    """Article model - the main content model."""
    __tablename__ = 'blog_article'

    STATUS_CHOICES = ['draft', 'published', 'archived']

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey('blog_author.id'), nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author: Mapped['Author'] = relationship('Author', back_populates='articles')
    tags: Mapped[List['Tag']] = relationship(
        'Tag',
        secondary=article_tags,
        back_populates='articles',
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title}', status='{self.status}')>"


def create_tables(engine) -> None:
    """Create all tables in the database."""
    metadata.create_all(engine)


def drop_tables(engine) -> None:
    """Drop all tables in the database."""
    metadata.drop_all(engine)
