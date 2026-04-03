"""
URL configuration for blog API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from blog.views import AuthorViewSet, TagViewSet, ArticleViewSet


router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'authors', AuthorViewSet, basename='author')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]
