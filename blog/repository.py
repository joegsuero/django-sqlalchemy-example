"""
blog/repository.py

Blog-specific repositories that extend the generic Repository base.
All complex query logic lives here, not in views.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session, joinedload, selectinload

from sa_core.repository import Repository
from blog.models import Article, Author, Tag, article_tags


class ArticleRepository(Repository[Article]):
    model = Article

    def published(
        self,
        session: Session,
        *,
        page: int = 1,
        page_size: int = 20,
        author_id: Optional[int] = None,
        tag_slug: Optional[str] = None,
    ) -> Tuple[List[Article], int]:
        """
        Paginated list of published articles.
        Eagerly loads author (JOIN) and tags (SELECT IN) to avoid N+1.
        """
        stmt = (
            select(Article)
            .where(Article.status == "published")
            .options(
                joinedload(Article.author),
                selectinload(Article.tags),
            )
            .order_by(Article.published_at.desc().nullslast())
        )

        count_stmt = (
            select(func.count(Article.id))
            .where(Article.status == "published")
        )

        if author_id:
            stmt = stmt.where(Article.author_id == author_id)
            count_stmt = count_stmt.where(Article.author_id == author_id)

        if tag_slug:
            stmt = (
                stmt
                .join(article_tags, Article.id == article_tags.c.article_id)
                .join(Tag, Tag.id == article_tags.c.tag_id)
                .where(Tag.slug == tag_slug)
            )
            count_stmt = (
                count_stmt
                .join(article_tags, Article.id == article_tags.c.article_id)
                .join(Tag, Tag.id == article_tags.c.tag_id)
                .where(Tag.slug == tag_slug)
            )

        offset = (page - 1) * page_size
        items = session.execute(
            stmt.limit(page_size).offset(offset)
        ).unique().scalars().all()

        total = session.execute(count_stmt).scalar_one()

        return items, total

    def get_with_relations(self, session: Session, pk: int) -> Optional[Article]:
        """Get a single article with author and tags pre-loaded."""
        return session.execute(
            select(Article)
            .where(Article.id == pk)
            .options(
                joinedload(Article.author),
                selectinload(Article.tags),
            )
        ).unique().scalar_one_or_none()

    def get_related(self, session: Session, article: Article, limit: int = 5) -> List[Article]:
        """
        Find articles sharing the most tags with the given article.
        Uses a COUNT + GROUP BY approach rather than Python-side filtering.
        """
        tag_ids = [tag.id for tag in article.tags]
        if not tag_ids:
            return []

        subq = (
            select(
                article_tags.c.article_id,
                func.count(article_tags.c.tag_id).label("match_count"),
            )
            .where(
                and_(
                    article_tags.c.tag_id.in_(tag_ids),
                    article_tags.c.article_id != article.id,
                )
            )
            .group_by(article_tags.c.article_id)
            .subquery()
        )

        stmt = (
            select(Article)
            .join(subq, Article.id == subq.c.article_id)
            .where(Article.status == "published")
            .options(joinedload(Article.author), selectinload(Article.tags))
            .order_by(subq.c.match_count.desc())
            .limit(limit)
        )

        return session.execute(stmt).unique().scalars().all()

    def search(self, session: Session, query: str, page: int = 1, page_size: int = 20):
        """Full-text search on title and body (LIKE-based, works on SQLite)."""
        like = f"%{query}%"
        stmt = (
            select(Article)
            .where(
                and_(
                    Article.status == "published",
                    Article.title.ilike(like) | Article.body.ilike(like),
                )
            )
            .options(joinedload(Article.author), selectinload(Article.tags))
            .order_by(Article.published_at.desc().nullslast())
        )
        count_stmt = select(func.count(Article.id)).where(
            Article.status == "published",
            Article.title.ilike(like) | Article.body.ilike(like),
        )
        offset = (page - 1) * page_size
        items = session.execute(stmt.limit(page_size).offset(offset)).unique().scalars().all()
        total = session.execute(count_stmt).scalar_one()
        return items, total

    def author_stats_report(self, session: Session) -> list:
        """
        Complex analytics query: per-author stats with window function ranking.
        Returns raw rows (not model instances).
        """
        stmt = (
            select(
                Author.id.label("author_id"),
                Author.name.label("author_name"),
                func.count(Article.id).label("total_articles"),
                func.sum(Article.view_count).label("total_views"),
                func.avg(Article.view_count).label("avg_views"),
                func.rank().over(
                    order_by=func.sum(Article.view_count).desc()
                ).label("rank_by_views"),
            )
            .join(Article, Article.author_id == Author.id)
            .where(Article.status == "published")
            .group_by(Author.id, Author.name)
            .order_by(func.sum(Article.view_count).desc())
        )
        return session.execute(stmt).all()

    def increment_views(self, session: Session, article_id: int) -> None:
        """Atomic view count increment using SQL UPDATE (no read-modify-write race)."""
        from sqlalchemy import update
        session.execute(
            update(Article)
            .where(Article.id == article_id)
            .values(view_count=Article.view_count + 1)
        )


class AuthorRepository(Repository[Author]):
    model = Author

    def with_article_count(self, session: Session) -> list:
        """Authors with their article count, ordered by most prolific."""
        stmt = (
            select(
                Author,
                func.count(Article.id).label("article_count"),
            )
            .outerjoin(Article, Article.author_id == Author.id)
            .group_by(Author.id)
            .order_by(func.count(Article.id).desc())
        )
        return session.execute(stmt).all()


class TagRepository(Repository[Tag]):
    model = Tag

    def popular_tags(self, session: Session, limit: int = 10) -> list:
        """Tags ordered by article count."""
        stmt = (
            select(
                Tag,
                func.count(article_tags.c.article_id).label("article_count"),
            )
            .join(article_tags, Tag.id == article_tags.c.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(article_tags.c.article_id).desc())
            .limit(limit)
        )
        return session.execute(stmt).all()
