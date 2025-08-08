# apps/products/views/brewery.py

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

from apps.products.models import Brewery
from apps.products.serializers import BreweryListSerializer, BrewerySerializer


class StandardPagination(PageNumberPagination):
    """표준 페이지네이션"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


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
