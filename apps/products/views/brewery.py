# apps/products/views/brewery.py

from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from apps.products.models import Brewery
from apps.products.serializers import BreweryListSerializer, BrewerySerializer

from .pagination import StandardPagination


class BreweryListView(ListAPIView):
    """양조장 목록 API - GET /api/v1/breweries/"""

    serializer_class = BreweryListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Brewery.objects.filter(is_active=True).order_by("name")


class BreweryDetailView(RetrieveAPIView):
    """양조장 상세 API - GET /api/v1/breweries/{id}/"""

    serializer_class = BrewerySerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Brewery.objects.filter(is_active=True)


class BreweryCreateView(CreateAPIView):
    """양조장 생성 API - POST /api/v1/breweries/ (어드민용)"""

    serializer_class = BrewerySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()


class BreweryManageView(RetrieveUpdateDestroyAPIView):
    """양조장 관리 API - GET/PUT/PATCH/DELETE /api/v1/breweries/{id}/manage/ (어드민용)"""

    serializer_class = BrewerySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Brewery.objects.all()  # 어드민은 비활성 양조장도 조회 가능

    def perform_destroy(self, instance):
        # 실제 삭제 대신 비활성화
        instance.is_active = False
        instance.save()
