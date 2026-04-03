"""
DRF Viewsets for blog API.
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action

from blog.models import Author, Tag, Article, article_tags
from blog.serializers import (
    AuthorSerializer,
    TagSerializer,
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateUpdateSerializer,
)


class AuthorViewSet(viewsets.ViewSet):
    """ViewSet for Author CRUD operations."""

    def list(self, request):
        from core.database import get_session
        with get_session() as session:
            authors = session.query(Author).all()
            serializer = AuthorSerializer(authors, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = AuthorSerializer(data=request.data)
        if serializer.is_valid():
            author = serializer.save()
            return Response(AuthorSerializer(author).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        from core.database import get_session
        with get_session() as session:
            author = session.query(Author).filter(Author.id == pk).first()
            if not author:
                return Response({'error': 'Author not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AuthorSerializer(author).data)


class TagViewSet(viewsets.ViewSet):
    """ViewSet for Tag CRUD operations."""

    def list(self, request):
        from core.database import get_session
        with get_session() as session:
            tags = session.query(Tag).all()
            serializer = TagSerializer(tags, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = TagSerializer(data=request.data)
        if serializer.is_valid():
            tag = serializer.save()
            return Response(TagSerializer(tag).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, pk=None):
        from core.database import get_session
        with get_session() as session:
            tag = session.query(Tag).filter(Tag.id == pk).first()
            if not tag:
                return Response({'error': 'Tag not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(TagSerializer(tag).data)


class ArticleViewSet(viewsets.ViewSet):
    """ViewSet for Article CRUD operations."""

    def list(self, request):
        from core.database import get_session
        from sqlalchemy import select
        
        status_filter = request.query_params.get('status', 'published')
        author_id = request.query_params.get('author_id')
        tag_id = request.query_params.get('tag_id')
        
        with get_session() as session:
            stmt = select(Article)
            
            if status_filter:
                stmt = stmt.where(Article.status == status_filter)
            
            if author_id:
                stmt = stmt.where(Article.author_id == int(author_id))
            
            if tag_id:
                from blog.models import article_tags
                stmt = stmt.join(article_tags).where(article_tags.c.tag_id == int(tag_id))
            
            stmt = stmt.order_by(Article.published_at.desc().nullslast(), Article.created_at.desc())
            
            result = session.execute(stmt)
            articles = result.scalars().all()
            
            # Load relationships
            for article in articles:
                _ = article.author
                _ = list(article.tags)
        
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)

    def create(self, request):
        from core.database import get_session
        from datetime import datetime
        
        with get_session() as session:
            validated_data = request.data.copy()
            
            tag_ids = validated_data.pop('tag_ids', [])
            
            if validated_data.get('status') == 'published':
                validated_data['published_at'] = datetime.utcnow()
            
            article = Article(**validated_data)
            session.add(article)
            session.flush()
            
            if tag_ids:
                from blog.models import Tag
                tags = session.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                article.tags = tags
            
            session.commit()
            session.refresh(article)
            
            _ = article.author
            _ = list(article.tags)
        
        return Response(
            ArticleDetailSerializer(article).data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, pk=None):
        from core.database import get_session
        
        with get_session() as session:
            article = session.query(Article).filter(Article.id == pk).first()
            if not article:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
            _ = article.author
            _ = list(article.tags)
        
        return Response(ArticleDetailSerializer(article).data)

    def update(self, request, pk=None):
        from core.database import get_session
        from datetime import datetime
        
        with get_session() as session:
            article = session.query(Article).filter(Article.id == pk).first()
            if not article:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
            validated_data = request.data.copy()
            tag_ids = validated_data.pop('tag_ids', None)
            
            if validated_data.get('status') == 'published' and not article.published_at:
                validated_data['published_at'] = datetime.utcnow()
            
            for key, value in validated_data.items():
                setattr(article, key, value)
            
            if tag_ids is not None:
                from blog.models import Tag
                tags = session.query(Tag).filter(Tag.id.in_(tag_ids)).all()
                article.tags = tags
            
            session.add(article)
            session.commit()
            session.refresh(article)
            
            _ = article.author
            _ = list(article.tags)
        
        return Response(ArticleDetailSerializer(article).data)

    def destroy(self, request, pk=None):
        from core.database import get_session
        
        with get_session() as session:
            article = session.query(Article).filter(Article.id == pk).first()
            if not article:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
            session.delete(article)
            session.commit()
        
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """Get related articles based on tags."""
        from core.database import get_session
        from sqlalchemy import select, func
        
        with get_session() as session:
            # Get current article
            article = session.query(Article).filter(Article.id == pk).first()
            if not article:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get tag IDs
            tag_ids = [tag.id for tag in article.tags]
            
            if not tag_ids:
                return Response([])
            
            # Find related articles (same tags, excluding current)
            stmt = (
                select(Article, func.count(article_tags.c.tag_id).label('match_count'))
                .select_from(Article)
                .join(article_tags, Article.id == article_tags.c.article_id)
                .where(
                    article_tags.c.tag_id.in_(tag_ids),
                    Article.id != pk,
                    Article.status == 'published'
                )
                .group_by(Article.id)
                .order_by(func.count(article_tags.c.tag_id).desc())
                .limit(5)
            )
            
            result = session.execute(stmt)
            related_articles = [row[0] for row in result.fetchall()]
            
            # Load relationships
            for art in related_articles:
                _ = art.author
                _ = list(art.tags)
        
        serializer = ArticleListSerializer(related_articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment article view count."""
        from core.database import get_session
        
        with get_session() as session:
            article = session.query(Article).filter(Article.id == pk).first()
            if not article:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            
            article.view_count += 1
            session.commit()
        
        return Response({'view_count': article.view_count})
