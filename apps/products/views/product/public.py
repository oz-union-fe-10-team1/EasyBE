# apps/products/views/product/public.py

from typing import Optional, Type

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.serializers.product.detail import ProductDetailSerializer
from apps.products.serializers.product.list import ProductListSerializer

from ...services import ProductService, SearchService
from ...services.like_service import LikeService
from ..pagination import SearchPagination

# ============================================================================
# 기본 클래스들
# ============================================================================


class BaseProductListView(ListAPIView):
    """제품 목록 뷰 기본 클래스"""

    serializer_class = ProductListSerializer
    pagination_class: Optional[Type[SearchPagination]] = None

    def get_base_queryset(self):
        """기본 쿼리셋 - Service에서 가져오기"""
        return ProductService.get_product_list_queryset()

    def get_queryset(self):
        """각 뷰에서 오버라이드"""
        return self.get_base_queryset()


# ============================================================================
# 일반 사용자용 API (UI용)
# ============================================================================


class ProductSearchView(BaseProductListView):
    """제품 검색 및 필터링"""

    pagination_class = SearchPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["drink__name", "package__name", "description"]
    ordering_fields = ["price", "created_at", "view_count", "like_count"]
    ordering = ["-created_at"]

    @extend_schema(
        summary="제품 검색",
        description="""
        제품을 검색하고 다양한 필터를 적용할 수 있습니다.
        """,
        tags=["제품"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return SearchService.get_search_queryset(self.request.query_params)


class ProductDetailView(RetrieveAPIView):
    """제품 상세 조회"""

    serializer_class = ProductDetailSerializer
    lookup_field = "pk"

    @extend_schema(
        summary="제품 상세 조회",
        description="""
        제품의 상세 정보를 조회합니다.
        """,
        tags=["제품"],
    )
    def get(self, request, *args, **kwargs):

        product_id = kwargs.get("pk")
        product = ProductService.get_product_detail(product_id)

        serializer = self.get_serializer(product)
        return Response(serializer.data)


class ProductLikeToggleView(APIView):
    """제품 좋아요 토글"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="제품 좋아요 토글",
        description="""
        제품의 좋아요를 토글합니다.
        """,
        tags=["제품"],
    )
    def post(self, request, pk):
        is_liked, like_count = LikeService.toggle_product_like(user=request.user, product_id=pk)

        return Response({"is_liked": is_liked, "like_count": like_count}, status=status.HTTP_200_OK)
