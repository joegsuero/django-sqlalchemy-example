"""
Management command to create tables and seed database.
"""
from django.core.management.base import BaseCommand

from core.database import engine
from blog.models import Author, Tag, Article, create_tables
from datetime import datetime


class Command(BaseCommand):
    help = 'Create tables and seed database with sample data'

    def handle(self, *args, **options):
        self.stdout.write('Creating tables...')
        create_tables(engine)
        self.stdout.write(self.style.SUCCESS('Tables created successfully'))
        
        self.stdout.write('Creating sample data...')
        self.create_sample_data()
        self.stdout.write(self.style.SUCCESS('Sample data created successfully'))

    def create_sample_data(self):
        from core.database import get_session
        
        with get_session() as session:
            # Create authors (standalone, no Django user dependency)
            author1 = Author(
                name='John Doe',
                email='john@example.com',
                bio='Tech writer and Django enthusiast'
            )
            author2 = Author(
                name='Jane Smith',
                email='jane@example.com',
                bio='Data scientist and Python developer'
            )
            author3 = Author(
                name='Bob Wilson',
                email='bob@example.com',
                bio='Full-stack developer and open source contributor'
            )
            
            session.add_all([author1, author2, author3])
            session.flush()
            
            # Create tags
            tags_data = [
                {'name': 'Python', 'slug': 'python', 'description': 'Everything Python'},
                {'name': 'Django', 'slug': 'django', 'description': 'Django web framework'},
                {'name': 'SQLAlchemy', 'slug': 'sqlalchemy', 'description': 'SQLAlchemy ORM'},
                {'name': 'Database', 'slug': 'database', 'description': 'Database topics'},
                {'name': 'Tutorial', 'slug': 'tutorial', 'description': 'How-to guides'},
                {'name': 'API', 'slug': 'api', 'description': 'API development'},
                {'name': 'REST', 'slug': 'rest', 'description': 'RESTful services'},
            ]
            
            tags = []
            for tag_data in tags_data:
                tag = Tag(**tag_data)
                session.add(tag)
                tags.append(tag)
            
            session.flush()
            
            # Create articles
            articles_data = [
                {
                    'title': 'Getting Started with Django',
                    'slug': 'getting-started-django',
                    'body': '''Django is a powerful web framework that makes it easy to build web applications quickly.

In this tutorial, we'll cover:
1. Setting up Django
2. Creating your first app
3. Working with models
4. Creating views and templates

Django follows the "batteries included" philosophy, providing everything you need to build web applications.''',
                    'excerpt': 'Learn how to get started with Django web framework.',
                    'status': 'published',
                    'view_count': 150,
                    'author_id': author1.id,
                    'published_at': datetime.utcnow(),
                },
                {
                    'title': 'Introduction to SQLAlchemy',
                    'slug': 'intro-sqlalchemy',
                    'body': '''SQLAlchemy is the most popular ORM for Python. It provides two distinct layers:

1. **SQLAlchemy Core**: Low-level SQL expression language
2. **SQLAlchemy ORM**: Object-relational mapper

Unlike Django's ORM which is designed for convenience, SQLAlchemy gives you more control over your queries and database interactions.

This guide covers the basics of SQLAlchemy ORM including:
- Defining models
- Creating sessions
- Basic CRUD operations
- Relationships''',
                    'excerpt': 'An introduction to SQLAlchemy ORM for Python developers.',
                    'status': 'published',
                    'view_count': 200,
                    'author_id': author2.id,
                    'published_at': datetime.utcnow(),
                },
                {
                    'title': 'Python Best Practices',
                    'slug': 'python-best-practices',
                    'body': '''Here are some essential best practices for writing clean Python code:

- Use meaningful variable names
- Write docstrings for functions and classes
- Follow PEP 8 style guide
- Use type hints
- Write tests before implementing features

Python emphasizes code readability and simplicity, making it an excellent choice for beginners and experts alike.''',
                    'excerpt': 'Essential best practices for writing clean Python code.',
                    'status': 'published',
                    'view_count': 180,
                    'author_id': author1.id,
                    'published_at': datetime.utcnow(),
                },
                {
                    'title': 'Django vs SQLAlchemy: A Comparison',
                    'slug': 'django-vs-sqlalchemy',
                    'body': '''Both Django ORM and SQLAlchemy are excellent tools, but they serve different purposes.

**Django ORM** is great for:
- Rapid development
- Standard CRUD operations
- Built-in admin interface
- Auto migrations

**SQLAlchemy** excels at:
- Complex queries
- Window functions
- Multiple database support
- Fine-grained control

Many teams use both in the same project - the "hybrid approach".''',
                    'excerpt': 'Comparing Django ORM and SQLAlchemy for Python developers.',
                    'status': 'published',
                    'view_count': 250,
                    'author_id': author2.id,
                    'published_at': datetime.utcnow(),
                },
                {
                    'title': 'Building REST APIs with DRF',
                    'slug': 'building-rest-apis-drf',
                    'body': '''Django Rest Framework (DRF) makes building APIs simple and straightforward.

In this tutorial, we'll explore:
- Setting up DRF
- Creating serializers
- Building viewsets
- URL routing
- Authentication

DRF provides a powerful, flexible toolkit for building Web APIs.''',
                    'excerpt': 'Learn how to build REST APIs with Django Rest Framework.',
                    'status': 'published',
                    'view_count': 320,
                    'author_id': author3.id,
                    'published_at': datetime.utcnow(),
                },
                {
                    'title': 'Database Migrations Best Practices',
                    'slug': 'database-migrations',
                    'body': '''Database migrations are essential for managing schema changes over time.

Best practices:
- Always test migrations locally first
- Keep migrations small and focused
- Review generated SQL before applying
- Use meaningful migration names

This guide covers both Django migrations and SQLAlchemy/Alembic.''',
                    'excerpt': 'Learn how to manage database migrations effectively.',
                    'status': 'published',
                    'view_count': 120,
                    'author_id': author1.id,
                    'published_at': datetime.utcnow(),
                },
                {
                    'title': 'Async Python with FastAPI',
                    'slug': 'async-python-fastapi',
                    'body': '''FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+.

Key features:
- Fast performance (on par with Node.js and Go)
- Automatic docs (Swagger UI)
- Easy validation with Pydantic
- Async/await support

This tutorial shows how to build async APIs with FastAPI.''',
                    'excerpt': 'Introduction to building async APIs with FastAPI.',
                    'status': 'draft',
                    'view_count': 50,
                    'author_id': author3.id,
                    'published_at': None,
                },
            ]
            
            articles = []
            for article_data in articles_data:
                article = Article(**article_data)
                session.add(article)
                articles.append(article)
            
            session.flush()
            
            # Assign tags to articles
            articles[0].tags = [tags[1], tags[4], tags[5]]  # Django, Tutorial, API
            articles[1].tags = [tags[2], tags[3], tags[4]]   # SQLAlchemy, Database, Tutorial
            articles[2].tags = [tags[0], tags[4]]             # Python, Tutorial
            articles[3].tags = [tags[1], tags[2], tags[3], tags[4]]  # Django, SQLAlchemy, Database, Tutorial
            articles[4].tags = [tags[1], tags[5], tags[6], tags[4]]  # Django, API, REST, Tutorial
            articles[5].tags = [tags[3], tags[4]]             # Database, Tutorial
            articles[6].tags = [tags[0], tags[5]]            # Python, API
            
            session.commit()
            
            self.stdout.write(f"Created 3 authors")
            self.stdout.write(f"Created {len(tags)} tags")
            self.stdout.write(f"Created {len(articles)} articles")
