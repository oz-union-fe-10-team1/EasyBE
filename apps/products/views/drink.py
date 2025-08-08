# apps/products/views/drink.py

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

from apps.products.models import Drink
from apps.products.serializers import DrinkListSerializer, DrinkSerializer


class StandardPagination(PageNumberPagination):
    """표준 페이지네이션"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


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
