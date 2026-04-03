"""
DRF Serializers for SQLAlchemy models.
"""
from rest_framework import serializers

from blog.models import Author, Tag, Article


class TagSerializer(serializers.Serializer):
    """Serializer for Tag model."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    slug = serializers.CharField(max_length=50)
    description = serializers.CharField(allow_blank=True, required=False)

    def create(self, validated_data: dict) -> Tag:
        from core.database import get_db_session
        session = get_db_session()
        try:
            tag = Tag(**validated_data)
            session.add(tag)
            session.commit()
            session.refresh(tag)
            return tag
        finally:
            session.close()

    def update(self, instance: Tag, validated_data: dict) -> Tag:
        from core.database import get_db_session
        session = get_db_session()
        try:
            for key, value in validated_data.items():
                setattr(instance, key, value)
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance
        finally:
            session.close()


class AuthorSerializer(serializers.Serializer):
    """Serializer for Author model."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(allow_blank=True, required=False)
    bio = serializers.CharField(allow_blank=True, required=False)
    avatar_url = serializers.URLField(allow_blank=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)

    def create(self, validated_data: dict) -> Author:
        from core.database import get_db_session
        session = get_db_session()
        try:
            author = Author(**validated_data)
            session.add(author)
            session.commit()
            session.refresh(author)
            return author
        finally:
            session.close()

    def update(self, instance: Author, validated_data: dict) -> Author:
        from core.database import get_db_session
        session = get_db_session()
        try:
            for key, value in validated_data.items():
                setattr(instance, key, value)
            session.add(instance)
            session.commit()
            session.refresh(instance)
            return instance
        finally:
            session.close()


class ArticleListSerializer(serializers.Serializer):
    """Serializer for Article list view."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=200)
    excerpt = serializers.CharField(allow_blank=True, allow_null=True)
    status = serializers.CharField(max_length=20)
    view_count = serializers.IntegerField(read_only=True)
    author_id = serializers.IntegerField()
    published_at = serializers.DateTimeField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)


class ArticleDetailSerializer(serializers.Serializer):
    """Serializer for Article detail view."""
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=200)
    body = serializers.CharField()
    excerpt = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    status = serializers.CharField(max_length=20)
    view_count = serializers.IntegerField(read_only=True)
    author_id = serializers.IntegerField()
    published_at = serializers.DateTimeField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = AuthorSerializer(read_only=True)

    def create(self, validated_data: dict) -> Article:
        from core.database import get_db_session
        from datetime import datetime
        
        session = get_db_session()
        
        try:
            if validated_data.get('status') == 'published' and not validated_data.get('published_at'):
                validated_data['published_at'] = datetime.utcnow()
            
            article = Article(**validated_data)
            session.add(article)
            session.commit()
            session.refresh(article)
            
            _ = article.author
            _ = list(article.tags)
            
            return article
        finally:
            session.close()

    def update(self, instance: Article, validated_data: dict) -> Article:
        from core.database import get_db_session
        from datetime import datetime
        
        session = get_db_session()
        
        try:
            if validated_data.get('status') == 'published' and not instance.published_at:
                validated_data['published_at'] = datetime.utcnow()
            
            for key, value in validated_data.items():
                setattr(instance, key, value)
            
            session.add(instance)
            session.commit()
            session.refresh(instance)
            
            _ = instance.author
            _ = list(instance.tags)
            
            return instance
        finally:
            session.close()


class ArticleCreateUpdateSerializer(serializers.Serializer):
    """Serializer for creating/updating articles."""
    title = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=200)
    body = serializers.CharField()
    excerpt = serializers.CharField(allow_blank=True, required=False)
    status = serializers.ChoiceField(choices=Article.STATUS_CHOICES, default='draft')
    author_id = serializers.IntegerField()
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=[]
    )
