# apps/products/views/drink.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
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

        **사용 목적:**
        - 관리자가 상품 생성 시 포함할 술을 선택하는 용도
        - 술 관리 및 조회

        **필터링 옵션:**
        - alcohol_type: 주종별 필터링 (MAKGEOLLI, YAKJU, CHEONGJU, SOJU, FRUIT_WINE)
        - brewery: 양조장별 필터링 (양조장 ID)

        **검색:**
        - 술 이름으로 검색
        - 양조장명으로 검색

        **정렬:**
        - name: 이름순 (a-z, z-a)
        - abv: 도수순 (낮은순, 높은순)  
        - created_at: 등록일순 (최신순, 오래된순)
        """,
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="검색어 (술 이름 또는 양조장명)"),
            OpenApiParameter(
                "alcohol_type",
                OpenApiTypes.STR,
                description="주종 (MAKGEOLLI, YAKJU, CHEONGJU, SOJU, FRUIT_WINE)",
                enum=["MAKGEOLLI", "YAKJU", "CHEONGJU", "SOJU", "FRUIT_WINE"],
            ),
            OpenApiParameter("brewery", OpenApiTypes.INT, description="양조장 ID"),
            OpenApiParameter(
                "ordering",
                OpenApiTypes.STR,
                description="정렬 (name, -name, abv, -abv, created_at, -created_at)",
                enum=["name", "-name", "abv", "-abv", "created_at", "-created_at"],
            ),
        ],
        examples=[
            OpenApiExample(
                "막걸리 검색",
                value="?alcohol_type=MAKGEOLLI&ordering=-created_at",
                description="막걸리만 최신순으로 조회",
            ),
            OpenApiExample(
                "양조장별 조회", value="?brewery=1&search=특별", description="특정 양조장의 '특별'이 포함된 술 검색"
            ),
            OpenApiExample("도수순 정렬", value="?ordering=abv", description="도수가 낮은 순서로 정렬"),
        ],
        tags=["관리자 - 술 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Drink.objects.select_related("brewery").order_by("-created_at")
