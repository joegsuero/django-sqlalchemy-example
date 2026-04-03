"""
Seed script to create sample data for the demo.
Run with: python manage.py shell < blog/seed.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from blog.models import Author, Tag, Article

print("Creating sample data...")

# Create users and authors
user1, _ = User.objects.get_or_create(
    username='john_doe',
    defaults={'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe'}
)
user2, _ = User.objects.get_or_create(
    username='jane_smith',
    defaults={'email': 'jane@example.com', 'first_name': 'Jane', 'last_name': 'Smith'}
)

author1, _ = Author.objects.get_or_create(
    user=user1,
    defaults={'bio': 'Tech writer and Django enthusiast'}
)
author2, _ = Author.objects.get_or_create(
    user=user2,
    defaults={'bio': 'Data scientist and Python developer'}
)

# Create tags
tags_data = [
    {'name': 'Python', 'slug': 'python', 'description': 'Everything Python'},
    {'name': 'Django', 'slug': 'django', 'description': 'Django web framework'},
    {'name': 'SQLAlchemy', 'slug': 'sqlalchemy', 'description': 'SQLAlchemy ORM'},
    {'name': 'Database', 'slug': 'database', 'description': 'Database topics'},
    {'name': 'Tutorial', 'slug': 'tutorial', 'description': 'How-to guides'},
]

tags = []
for tag_data in tags_data:
    tag, _ = Tag.objects.get_or_create(slug=tag_data['slug'], defaults=tag_data)
    tags.append(tag)

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
        'author': author1,
        'tags': [tags[1], tags[4]],
    },
    {
        'title': 'Introduction to SQLAlchemy',
        'slug': 'intro-sqlalchemy',
        'body': '''SQLAlchemy is the most popular ORM for Python. It provides two distinct layers:

1. **SQLAlchemy Core**: Low-level SQL expression language
2. **SQLAlchemy ORM**: Object-relational mapper

Unlike Django's ORM which is designed for convenience, SQLAlchemy gives you more control over your queries and database interactions.''',
        'excerpt': 'An introduction to SQLAlchemy ORM for Python developers.',
        'status': 'published',
        'view_count': 200,
        'author': author2,
        'tags': [tags[2], tags[3]],
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
        'author': author1,
        'tags': [tags[0], tags[4]],
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
        'author': author2,
        'tags': [tags[1], tags[2], tags[3]],
    },
    {
        'title': 'Working with Database Migrations',
        'slug': 'database-migrations',
        'body': '''Database migrations are essential for managing schema changes over time.

Django's migration system:
- Auto-generates migrations from model changes
- Handles dependencies between migrations
- Supports Rollback capabilities

Best practices:
- Always test migrations locally first
- Keep migrations small and focused
- Review generated SQL before applying''',
        'excerpt': 'Learn how to manage database migrations effectively.',
        'status': 'published',
        'view_count': 120,
        'author': author1,
        'tags': [tags[3], tags[4]],
    },
]

for article_data in articles_data:
    tags_list = article_data.pop('tags', [])
    article, created = Article.objects.get_or_create(
        slug=article_data['slug'],
        defaults=article_data
    )
    if created:
        article.tags.set(tags_list)
        print(f"Created: {article.title}")
    else:
        print(f"Already exists: {article.title}")

# Set published_at for published articles
Article.objects.filter(status='published').update(
    published_at=timezone.now()
)

print(f"\nTotal articles: {Article.objects.count()}")
print(f"Total authors: {Author.objects.count()}")
print(f"Total tags: {Tag.objects.count()}")
print("\nSample data created successfully!")
