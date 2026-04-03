"""
core/viewsets.py

Generic DRF ViewSet that integrates with SQLAlchemy sessions and the
Repository pattern. Subclasses declare their repository and serializer;
standard CRUD is handled automatically.
"""
from __future__ import annotations

from typing import Type

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from core.database import get_session
from core.repository import Repository


class SAViewSet(ViewSet):
    """
    Base ViewSet that wires DRF actions to a SQLAlchemy Repository.

    Subclass and set:
        repository_class  = MyModelRepository
        list_serializer   = MyModelListSerializer
        detail_serializer = MyModelDetailSerializer  (defaults to list_serializer)
        write_serializer  = MyModelWriteSerializer   (defaults to detail_serializer)
        page_size         = 20  (default)

    Then override individual actions for custom behavior.
    """

    repository_class: Type[Repository] = None
    list_serializer = None
    detail_serializer = None
    write_serializer = None
    page_size: int = 20

    def get_repository(self) -> Repository:
        assert self.repository_class, (
            f"{self.__class__.__name__} must define `repository_class`."
        )
        return self.repository_class()

    def get_list_serializer(self):
        assert self.list_serializer, (
            f"{self.__class__.__name__} must define `list_serializer`."
        )
        return self.list_serializer

    def get_detail_serializer(self):
        return self.detail_serializer or self.get_list_serializer()

    def get_write_serializer(self):
        return self.write_serializer or self.get_detail_serializer()

    # ═══════════════════════════════════════════════════════════════════════════
    # Default CRUD actions
    # ═══════════════════════════════════════════════════════════════════════════

    def list(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", self.page_size))

        repo = self.get_repository()
        with get_session() as session:
            items, total = repo.paginate(session, page=page, page_size=page_size)

        serializer_class = self.get_list_serializer()
        return Response(
            {
                "count": total,
                "page": page,
                "page_size": page_size,
                "results": serializer_class(items, many=True).data,
            }
        )

    def retrieve(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)

        serializer_class = self.get_detail_serializer()
        return Response(serializer_class(instance).data)

    def create(self, request):
        write_serializer_class = self.get_write_serializer()
        serializer = write_serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            instance = repo.create(session, **serializer.validated_data)
            session.commit()
            session.refresh(instance)

        detail_serializer_class = self.get_detail_serializer()
        return Response(
            detail_serializer_class(instance).data,
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, pk=None):
        write_serializer_class = self.get_write_serializer()
        serializer = write_serializer_class(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            instance = repo.update(session, instance, **serializer.validated_data)
            session.commit()
            session.refresh(instance)

        detail_serializer_class = self.get_detail_serializer()
        return Response(detail_serializer_class(instance).data)

    def partial_update(self, request, pk=None):
        write_serializer_class = self.get_write_serializer()
        serializer = write_serializer_class(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            instance = repo.update(session, instance, **serializer.validated_data)
            session.commit()
            session.refresh(instance)

        detail_serializer_class = self.get_detail_serializer()
        return Response(detail_serializer_class(instance).data)

    def destroy(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            repo.delete(session, instance)
            session.commit()

        return Response(status=status.HTTP_204_NO_CONTENT)
