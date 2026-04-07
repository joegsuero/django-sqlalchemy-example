"""
sa_core/viewsets.py

ViewSet base genérico que integra sesiones SQLAlchemy con el patrón Repository.
Regla: serializar DENTRO del bloque `with get_session()`.
"""
from __future__ import annotations

from typing import Type

from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from sa_core.database import get_session
from sa_core.repository import Repository


class SAViewSet(ViewSet):
    repository_class: Type[Repository] = None
    list_serializer = None
    detail_serializer = None
    write_serializer = None
    page_size: int = 20

    def get_repository(self) -> Repository:
        assert self.repository_class, (
            f"{self.__class__.__name__} debe definir `repository_class`."
        )
        return self.repository_class()

    def get_list_serializer(self):
        assert self.list_serializer, (
            f"{self.__class__.__name__} debe definir `list_serializer`."
        )
        return self.list_serializer

    def get_detail_serializer(self):
        return self.detail_serializer or self.get_list_serializer()

    def get_write_serializer(self):
        return self.write_serializer or self.get_detail_serializer()

    def list(self, request):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", self.page_size))
        repo = self.get_repository()
        with get_session() as session:
            items, total = repo.paginate(session, page=page, page_size=page_size)
            data = self.get_list_serializer()(items, many=True).data
        return Response({"count": total, "page": page, "page_size": page_size, "results": data})

    def retrieve(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            data = self.get_detail_serializer()(instance).data
        return Response(data)

    def create(self, request):
        write_cls = self.get_write_serializer()
        serializer = write_cls(data=request.data)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            instance = repo.create(session, **serializer.validated_data)
            # get_session() hace commit al salir; refresh aquí dentro, antes del cierre
            session.flush()
            session.refresh(instance)
            data = self.get_detail_serializer()(instance).data

        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None):
        write_cls = self.get_write_serializer()
        serializer = write_cls(data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            instance = repo.update(session, instance, **serializer.validated_data)
            session.flush()
            session.refresh(instance)
            data = self.get_detail_serializer()(instance).data

        return Response(data)

    def partial_update(self, request, pk=None):
        write_cls = self.get_write_serializer()
        serializer = write_cls(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            instance = repo.update(session, instance, **serializer.validated_data)
            session.flush()
            session.refresh(instance)
            data = self.get_detail_serializer()(instance).data

        return Response(data)

    def destroy(self, request, pk=None):
        repo = self.get_repository()
        with get_session() as session:
            instance = repo.get_or_404(session, pk)
            repo.delete(session, instance)

        return Response(status=status.HTTP_204_NO_CONTENT)
