"""
blog/serializers.py

Serializers are data-shape contracts only.
They do NOT open sessions or talk to the database.
"""
from rest_framework import serializers


class TagSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=50)
    slug = serializers.CharField(max_length=50)
    description = serializers.CharField(allow_blank=True, required=False, allow_null=True)


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField(allow_blank=True, required=False, allow_null=True)
    bio = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    avatar_url = serializers.URLField(allow_blank=True, required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class ArticleListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=200)
    excerpt = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    status = serializers.CharField(max_length=20)
    view_count = serializers.IntegerField(read_only=True)
    published_at = serializers.DateTimeField(allow_null=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)


class ArticleDetailSerializer(ArticleListSerializer):
    body = serializers.CharField()
    updated_at = serializers.DateTimeField(read_only=True)


class ArticleWriteSerializer(serializers.Serializer):
    """Used for POST/PUT/PATCH. Validates incoming data only."""
    title = serializers.CharField(max_length=200)
    slug = serializers.CharField(max_length=200)
    body = serializers.CharField()
    excerpt = serializers.CharField(allow_blank=True, required=False, allow_null=True)
    status = serializers.ChoiceField(choices=["draft", "published", "archived"], default="draft")
    author_id = serializers.IntegerField()
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
    )
