"""
core/repository.py

Generic repository base class that provides typed CRUD operations
for any SQLAlchemy model. Extend it per-model to add custom queries.
"""
from __future__ import annotations

from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import Session, DeclarativeBase

ModelT = TypeVar("ModelT", bound=DeclarativeBase)


class Repository(Generic[ModelT]):
    """
    Generic CRUD repository for any SQLAlchemy model.

    Usage:
        class ArticleRepository(Repository[Article]):
            model = Article

            def published(self, session: Session) -> List[Article]:
                return self.filter(session, status="published")

        # In a view or service:
        repo = ArticleRepository()
        articles = repo.published(session)
        article = repo.get_or_404(session, 42)
    """

    model: Type[ModelT]

    # ═══════════════════════════════════════════════════════════════════════════
    # READ
    # ═══════════════════════════════════════════════════════════════════════════

    def get(self, session: Session, pk: Any) -> Optional[ModelT]:
        """Get by primary key. Returns None if not found."""
        return session.get(self.model, pk)

    def get_or_404(self, session: Session, pk: Any) -> ModelT:
        """Get by primary key. Raises NoResultFound if not found."""
        from sqlalchemy.exc import NoResultFound
        instance = session.get(self.model, pk)
        if instance is None:
            raise NoResultFound(f"{self.model.__name__} with pk={pk} not found.")
        return instance

    def all(self, session: Session) -> List[ModelT]:
        """Return all rows."""
        return session.execute(select(self.model)).scalars().all()

    def filter(self, session: Session, **kwargs) -> List[ModelT]:
        """
        Simple equality filter. For complex queries, use select() directly
        or add named methods to the subclass.

        Example: repo.filter(session, status="published", author_id=3)
        """
        stmt = select(self.model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        return session.execute(stmt).scalars().all()

    def first(self, session: Session, **kwargs) -> Optional[ModelT]:
        """Like filter() but returns only the first result."""
        stmt = select(self.model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        return session.execute(stmt.limit(1)).scalar_one_or_none()

    def count(self, session: Session, **kwargs) -> int:
        """Count rows matching optional equality filters."""
        stmt = select(func.count()).select_from(self.model)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        return session.execute(stmt).scalar_one()

    def exists(self, session: Session, **kwargs) -> bool:
        """Return True if any row matches the given filters."""
        return self.count(session, **kwargs) > 0

    def paginate(
        self,
        session: Session,
        page: int = 1,
        page_size: int = 20,
        *,
        order_by=None,
        **filters,
    ) -> tuple[List[ModelT], int]:
        """
        Paginate results. Returns (items, total_count).

        Example:
            articles, total = repo.paginate(session, page=2, page_size=10,
                                            status="published")
        """
        stmt = select(self.model)
        count_stmt = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            condition = getattr(self.model, key) == value
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)

        if order_by is not None:
            stmt = stmt.order_by(order_by)

        offset = (page - 1) * page_size
        stmt = stmt.limit(page_size).offset(offset)

        items = session.execute(stmt).scalars().all()
        total = session.execute(count_stmt).scalar_one()

        return items, total

    # ═══════════════════════════════════════════════════════════════════════════
    # WRITE
    # ═══════════════════════════════════════════════════════════════════════════

    def create(self, session: Session, **kwargs) -> ModelT:
        """Create and flush a new instance (does not commit)."""
        instance = self.model(**kwargs)
        session.add(instance)
        session.flush()
        return instance

    def create_many(self, session: Session, data: List[dict]) -> List[ModelT]:
        """Bulk create instances."""
        instances = [self.model(**d) for d in data]
        session.add_all(instances)
        session.flush()
        return instances

    def update(self, session: Session, instance: ModelT, **kwargs) -> ModelT:
        """Update an existing instance and flush."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        session.add(instance)
        session.flush()
        return instance

    def bulk_update(self, session: Session, filters: dict, values: dict) -> int:
        """
        Bulk update matching rows without loading them into memory.
        Returns the number of rows updated.

        Example:
            repo.bulk_update(session, filters={"status": "draft"}, values={"status": "archived"})
        """
        stmt = update(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        stmt = stmt.values(**values)
        result = session.execute(stmt)
        session.flush()
        return result.rowcount

    def delete(self, session: Session, instance: ModelT) -> None:
        """Delete an instance."""
        session.delete(instance)
        session.flush()

    def bulk_delete(self, session: Session, **filters) -> int:
        """
        Bulk delete matching rows without loading them.
        Returns the number of rows deleted.
        """
        stmt = delete(self.model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(self.model, key) == value)
        result = session.execute(stmt)
        session.flush()
        return result.rowcount
