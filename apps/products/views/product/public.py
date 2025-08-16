# apps/products/views/product/public.py

from typing import Optional, Type

from django.db.models import Case, DecimalField, F, Q, When
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters, status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Product, ProductLike
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

        **검색 기능:**
        - 제품명, 양조장명, 설명으로 검색 가능

        **맛 프로필 필터 (0.0~5.0):**
        - sweetness: 단맛
        - acidity: 신맛  
        - body: 바디감
        - carbonation: 탄산감
        - bitterness: 쓴맛
        - aroma: 풍미

        **카테고리 필터:**
        - gift_suitable: 선물용 적합
        - regional_specialty: 지역 특산주
        - limited_edition: 리미티드 에디션
        - premium: 프리미엄
        """,
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="검색어"),
            OpenApiParameter(
                "ordering", OpenApiTypes.STR, description="정렬 (-created_at, price, -price, view_count, -view_count)"
            ),
            OpenApiParameter("sweetness", OpenApiTypes.FLOAT, description="단맛 (0.0~5.0)"),
            OpenApiParameter("acidity", OpenApiTypes.FLOAT, description="신맛 (0.0~5.0)"),
            OpenApiParameter("body", OpenApiTypes.FLOAT, description="바디감 (0.0~5.0)"),
            OpenApiParameter("carbonation", OpenApiTypes.FLOAT, description="탄산감 (0.0~5.0)"),
            OpenApiParameter("bitterness", OpenApiTypes.FLOAT, description="쓴맛 (0.0~5.0)"),
            OpenApiParameter("aroma", OpenApiTypes.FLOAT, description="풍미 (0.0~5.0)"),
            OpenApiParameter("gift_suitable", OpenApiTypes.BOOL, description="선물용 적합"),
            OpenApiParameter("regional_specialty", OpenApiTypes.BOOL, description="지역 특산주"),
            OpenApiParameter("limited_edition", OpenApiTypes.BOOL, description="리미티드 에디션"),
            OpenApiParameter("premium", OpenApiTypes.BOOL, description="프리미엄"),
        ],
        examples=[
            OpenApiExample(
                "기본 검색", value="?search=막걸리&ordering=-created_at", description="막걸리 검색 후 최신순 정렬"
            ),
            OpenApiExample(
                "맛 프로필 필터",
                value="?sweetness=3.0&acidity=2.5&premium=true",
                description="단맛 3.0, 신맛 2.5인 프리미엄 제품",
            ),
        ],
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
        조회 시 자동으로 조회수가 1 증가합니다.

        **응답 정보:**
        - 제품 기본 정보 (이름, 가격, 설명 등)
        - 개별 술 정보 (양조장, 맛 프로필 등) 또는 패키지 정보
        - 이미지 목록
        - 통계 (조회수, 좋아요 수 등)
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

        **동작:**
        - 좋아요가 없으면 추가
        - 좋아요가 있으면 제거

        **응답:**
        - is_liked: 현재 좋아요 상태
        - like_count: 총 좋아요 수
        """,
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "is_liked": {"type": "boolean", "description": "좋아요 상태"},
                    "like_count": {"type": "integer", "description": "총 좋아요 수"},
                },
            },
            404: {"description": "제품을 찾을 수 없음"},
        },
        tags=["제품"],
    )
    def post(self, request, pk):
        is_liked, like_count = LikeService.toggle_product_like(user=request.user, product_id=pk)

        return Response({"is_liked": is_liked, "like_count": like_count}, status=status.HTTP_200_OK)
