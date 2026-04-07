# Django + SQLAlchemy Integration Demo

This project demonstrates a robust integration of SQLAlchemy 2.0 with Django using a hybrid approach: Django handles configuration and DRF, while SQLAlchemy manages models and data access through the Repository pattern.

## Key Features

- **SQLAlchemy 2.0** as the primary ORM with full typing support
- **Repository Pattern** for data access abstraction
- **Generic DRF ViewSets** with built-in SQLAlchemy support
- **Alembic** for database migrations
- **Session management** via context managers (`with get_session()`)

## Project Structure

```
django-sqlalchemy/
├── config/                   # Django configuration
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── sa_core/                  # Django app - SQLAlchemy infrastructure
│   ├── apps.py
│   ├── database.py           # Engine, sessions, context managers
│   ├── middleware.py         # Session middleware (opt-in)
│   ├── exceptions.py         # SQLAlchemy to DRF exception mapping
│   ├── repository.py         # Generic BaseRepository
│   ├── viewsets.py           # SAViewSet base for DRF
│   └── management/
│       └── commands/
│           └── migrate_sa.py # Django command for Alembic
├── blog/                     # Django app - Business logic
│   ├── models.py             # SQLAlchemy models
│   ├── repository.py         # Specific repositories
│   ├── serializers.py        # DRF Serializers
│   ├── views.py              # DRF ViewSets
│   ├── urls.py               # API routes
│   └── management/
│       └── commands/
│           └── seed_blog.py  # Test data command
└── migrations_alembic/       # Alembic migrations
    ├── env.py
    ├── script.py.mako
    └── versions/
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations (Alembic)
python manage.py migrate_sa upgrade head

# Create sample data
python manage.py seed_blog

# Start server
python manage.py runserver
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/articles/` | List articles (paginated) |
| POST | `/api/articles/` | Create article |
| GET | `/api/articles/{id}/` | View article detail |
| PUT | `/api/articles/{id}/` | Update article |
| PATCH | `/api/articles/{id}/` | Partial update |
| DELETE | `/api/articles/{id}/` | Delete article |
| GET | `/api/articles/search/?q=text` | Search articles |
| GET | `/api/articles/{id}/related/` | Related articles |
| POST | `/api/articles/{id}/increment_views/` | Increment views |
| GET | `/api/authors/` | List authors |
| GET | `/api/tags/` | List tags |
| GET | `/api/tags/popular/` | Most used tags |

### Available Filters

- `?author_id=1` - Filter by author
- `?tag=python` - Filter by tag slug
- `?page=2&page_size=10` - Custom pagination

## Patterns and Conventions

### 1. Repository Pattern

Repositories encapsulate query logic:

```python
from blog.repository import ArticleRepository
from sa_core.database import get_session

repo = ArticleRepository()
with get_session() as session:
    articles, total = repo.published(session, page=1, page_size=20)
    article = repo.get_with_relations(session, pk=1)
```

### 2. Session Management

**Key rule:** Always use the `get_session()` context manager:

```python
from sa_core.database import get_session

with get_session() as session:
    # Session operations
    # Automatic commit on successful exit
    # Automatic rollback on exception
```

### 3. Eager Loading

Avoid N+1 with loading strategies:

```python
from sqlalchemy.orm import joinedload, selectinload

stmt = (
    select(Article)
    .options(
        joinedload(Article.author),      # → select_related()
        selectinload(Article.tags),       # → prefetch_related()
    )
    .where(Article.status == "published")
)
```

**Note:** Use `.unique()` after `joinedload()` to deduplicate rows.

### 4. Serialization

**Always serialize inside the `with` block:**

```python
with get_session() as session:
    article = repo.get_with_relations(session, pk=1)
    data = ArticleDetailSerializer(article).data  # ✓ Inside the block
return Response(data)
```

## sa_core Architecture

### database.py
- `get_session()` - Session context manager
- `get_engine()` / `get_async_engine()` - Engine access
- Support for SQLite (sync/async) and PostgreSQL

### repository.py
- `Repository[T]` - Generic base class with CRUD
- `get()`, `get_or_404()`, `paginate()`, `create()`, `update()`, `delete()`

### viewsets.py
- `SAViewSet` - Base ViewSet for DRF
- Automatic serialization within session
- Ready-to-use CRUD methods

### middleware.py (opt-in)
Optional middleware for per-request session. **Not enabled by default.**

To enable, add to `MIDDLEWARE` in settings:
```python
MIDDLEWARE = [
    # ... other middlewares
    "sa_core.middleware.SQLAlchemySessionMiddleware",
]
```

## Migrations with Alembic

The project uses Alembic instead of `manage.py migrate` for the SQLAlchemy schema:

```bash
# Create new migration
python manage.py migrate_sa revision --autogenerate -m "description"

# Apply migrations
python manage.py migrate_sa upgrade head

# Rollback
python manage.py migrate_sa downgrade -1

# View history
python manage.py migrate_sa history
```

## License

MIT
