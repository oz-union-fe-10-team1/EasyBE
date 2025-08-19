# apps/products/views/drink.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import ListAPIView

from apps.products.models import Drink
from apps.products.serializers import DrinkListSerializer

from .pagination import SearchPagination


class DrinkListView(ListAPIView):
    """술 목록 조회 (관리자용)"""

    serializer_class = DrinkListSerializer
    pagination_class = SearchPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["alcohol_type", "brewery"]
    search_fields = ["name", "brewery__name"]
    ordering_fields = ["name", "abv", "created_at"]
    ordering = ["-created_at"]

    @extend_schema(
        summary="술 목록 조회",
        description="""
        등록된 모든 술의 목록을 조회합니다. (관리자용)
        """,
        tags=["관리자 - 술 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Drink.objects.select_related("brewery").order_by("-created_at")
