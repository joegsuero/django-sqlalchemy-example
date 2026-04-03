# Django + SQLAlchemy Integration Demo

This project demonstrates how to integrate SQLAlchemy with Django, using both ORMs in the same project following the "hybrid approach" described in the blog post.

## Project Structure

```
django-sqlalchemy/
├── config/          # Project configuration
│   ├── settings.py             # Django settings
│   ├── urls.py                 # URL routing
│   ├── db.py                   # SQLAlchemy engine & session setup
│   ├── async_db.py             # Async SQLAlchemy setup
│   ├── middleware.py           # SQLAlchemy session middleware
│   ├── sa_base.py              # BaseModel with Django-style helpers
│   └── sa_query.py             # QueryBuilder with Django-like API
├── blog/                       # Blog application
│   ├── models.py               # Django ORM models
│   ├── sa_models.py           # SQLAlchemy models (mirrors Django)
│   ├── services.py            # Hybrid service layer
│   ├── views.py               # Django views
│   └── urls.py                # URL patterns
```

## Features

### 1. Dual ORM Support
- **Django ORM**: For standard CRUD operations
- **SQLAlchemy ORM**: For complex queries and analytics

### 2. Hybrid Service Layer (`blog/services.py`)
- `get_article_django()` - Simple retrieval with Django
- `get_article_sqlalchemy()` - Same with SQLAlchemy
- `get_author_performance_report_sqlalchemy()` - Window functions
- `get_articles_raw_sql()` - Raw SQL demonstration

### 3. QueryBuilder (`config/sa_query.py`)
Django-like chainable interface for SQLAlchemy:
```python
articles = (
    QueryBuilder(SAArticle, session)
    .filter(published=True)
    .order_by('-created_at')
    .limit(20)
    .all()
)
```

### 4. BaseModel Helpers (`config/sa_base.py`)
Django-style methods for SQLAlchemy models:
```python
article = SAArticle.get(session, 42)
articles = SAArticle.filter(session, published=True)
new_article = SAArticle.create(session, title='Hello', published=True)
```

### 5. Async Support (`config/async_db.py`)
Async SQLAlchemy for use with Django async views.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create sample data
python manage.py shell < blog/seed.py

# Run server
python manage.py runserver
```

## Available URLs

| URL | Description |
|-----|-------------|
| `/` | Article list (Django ORM) |
| `/sqlalchemy/` | Article list (SQLAlchemy) |
| `/querybuilder/` | Article list (QueryBuilder) |
| `/article/<id>/` | Article detail (Django) |
| `/article-sa/<id>/` | Article detail (SQLAlchemy) |
| `/search/?q=query` | Search (SQLAlchemy) |
| `/report/` | Author performance (SQLAlchemy) |
| `/tags/` | Popular tags (SQLAlchemy) |
| `/compare/` | Compare Django vs SQLAlchemy |

## Key Concepts

### Session Management
SQLAlchemy sessions need explicit lifecycle management:
```python
# Option 1: Context manager
with get_session() as session:
    articles = session.execute(select(SAArticle)).scalars().all()

# Option 2: Middleware (automatic per-request)
def my_view(request):
    articles = request.sa_session.execute(select(SAArticle)).scalars().all()
```

### Eager Loading
SQLAlchemy's loading strategies vs Django:
- `joinedload()` → `select_related()`
- `selectinload()` → `prefetch_related()`
- Note: SQLAlchemy requires `.unique()` after joinedload to deduplicate rows

## License

MIT
