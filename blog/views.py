"""
blog/views.py

DRF ViewSets para la API del blog.
La lógica de negocio vive en los repositories.
Los views conectan HTTP con las llamadas al repository.

Regla clave: serializar DENTRO del bloque `with get_session()`.
"""
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response

from sa_core.database import get_session
from sa_core.viewsets import SAViewSet
from blog.repository import ArticleRepository, AuthorRepository, TagRepository
from blog.serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleWriteSerializer,
    AuthorSerializer,
    TagSerializer,
)


class ArticleViewSet(SAViewSet):
    repository_class = ArticleRepository
    list_serializer = ArticleListSerializer
    detail_serializer = ArticleDetailSerializer
    write_serializer = ArticleWriteSerializer

    def list(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", self.page_size))
        author_id = request.query_params.get("author_id")
        tag_slug = request.query_params.get("tag")

        repo = self.get_repository()
        with get_session() as session:
            items, total = repo.published(
                session,
                page=page,
                page_size=page_size,
                author_id=int(author_id) if author_id else None,
                tag_slug=tag_slug,
            )
            # Serializar dentro de la sesión para evitar DetachedInstanceError
            data = self.list_serializer(items, many=True).data

        return Response({"count": total, "page": page, "page_size": page_size, "results": data})

    def retrieve(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            article = repo.get_with_relations(session, int(pk))
            if not article:
                raise NotFound()
            data = self.detail_serializer(article).data

        return Response(data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        q = request.query_params.get("q", "")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", self.page_size))

        repo = self.get_repository()
        with get_session() as session:
            items, total = repo.search(session, q, page=page, page_size=page_size)
            data = self.list_serializer(items, many=True).data

        return Response({"count": total, "results": data})

    @action(detail=True, methods=["get"])
    def related(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            article = repo.get_with_relations(session, int(pk))
            if not article:
                raise NotFound()
            related = repo.get_related(session, article)
            data = self.list_serializer(related, many=True).data

        return Response(data)

    @action(detail=True, methods=["post"])
    def increment_views(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            repo.get_or_404(session, int(pk))
            repo.increment_views(session, int(pk))

        return Response({"status": "ok"})

    @action(detail=False, methods=["get"])
    def report(self, request):
        repo = self.get_repository()
        with get_session() as session:
            rows = repo.author_stats_report(session)
            data = [
                {
                    "author_id": row.author_id,
                    "author_name": row.author_name,
                    "total_articles": row.total_articles,
                    "total_views": row.total_views,
                    "avg_views": float(row.avg_views or 0),
                    "rank_by_views": row.rank_by_views,
                }
                for row in rows
            ]

        return Response(data)

    def create(self, request):
        from rest_framework import status
        serializer = self.write_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            article = repo.create_article(session, dict(serializer.validated_data))
            session.flush()
            # Recargar con relaciones para serializar correctamente
            article = repo.get_with_relations(session, article.id)
            data = self.detail_serializer(article).data

        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        serializer = self.write_serializer(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            article = repo.get_or_404(session, int(pk))
            article = repo.update_article(session, article, dict(serializer.validated_data))
            article = repo.get_with_relations(session, article.id)
            data = self.detail_serializer(article).data

        return Response(data)

    def partial_update(self, request, pk=None):
        serializer = self.write_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            article = repo.get_or_404(session, int(pk))
            article = repo.update_article(session, article, dict(serializer.validated_data))
            article = repo.get_with_relations(session, article.id)
            data = self.detail_serializer(article).data

        return Response(data)


class AuthorViewSet(SAViewSet):
    repository_class = AuthorRepository
    list_serializer = AuthorSerializer
    detail_serializer = AuthorSerializer

    def list(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", self.page_size))
        repo = self.get_repository()
        with get_session() as session:
            items, total = repo.paginate(session, page=page, page_size=page_size)
            data = self.list_serializer(items, many=True).data
        return Response({"count": total, "page": page, "page_size": page_size, "results": data})

    def retrieve(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, int(pk))
            data = self.detail_serializer(instance).data
        return Response(data)


class TagViewSet(SAViewSet):
    repository_class = TagRepository
    list_serializer = TagSerializer
    detail_serializer = TagSerializer

    def list(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", self.page_size))
        repo = self.get_repository()
        with get_session() as session:
            items, total = repo.paginate(session, page=page, page_size=page_size)
            data = self.list_serializer(items, many=True).data
        return Response({"count": total, "page": page, "page_size": page_size, "results": data})

    def retrieve(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, int(pk))
            data = self.detail_serializer(instance).data
        return Response(data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        repo = self.get_repository()
        with get_session() as session:
            rows = repo.popular_tags(session, limit=10)
            data = [
                {**TagSerializer(row[0]).data, "article_count": row[1]}
                for row in rows
            ]
        return Response(data)
