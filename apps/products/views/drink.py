# apps/products/views/drink.py

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from apps.products.models import Drink
from apps.products.serializers import DrinkListSerializer, DrinkSerializer

from .pagination import StandardPagination


class DrinkListView(ListAPIView):
    """술 목록 API - GET /api/v1/drinks/"""

    serializer_class = DrinkListSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["alcohol_type", "brewery"]
    search_fields = ["name", "brewery__name"]
    ordering_fields = ["name", "abv", "created_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Drink.objects.select_related("brewery").order_by("-created_at")


class DrinkDetailView(RetrieveAPIView):
    """술 상세 API - GET /api/v1/drinks/{id}/"""

    serializer_class = DrinkSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Drink.objects.select_related("brewery")


class DrinkCreateView(CreateAPIView):
    """술 생성 API - POST /api/v1/drinks/ (어드민용)"""

    serializer_class = DrinkSerializer
    permission_classes = [IsAuthenticated]


class DrinkManageView(RetrieveUpdateDestroyAPIView):
    """술 관리 API - GET/PUT/PATCH/DELETE /api/v1/drinks/{id}/manage/ (어드민용)"""

    serializer_class = DrinkSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Drink.objects.select_related("brewery")

    def perform_destroy(self, instance):
        # 연관된 상품이 있으면 삭제 불가
        if hasattr(instance, "product") and instance.product:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("연관된 상품이 있어 삭제할 수 없습니다.")
        instance.delete()
