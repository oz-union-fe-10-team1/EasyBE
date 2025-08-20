from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from apps.products.services import ProductService

from .public import BaseProductListView

# ============================================================================
# 기본 클래스들
# ============================================================================


class BaseSectionView(BaseProductListView):
    """섹션 뷰 기본 클래스 - 제목과 함께 응답"""

    section_title = ""

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"title": self.section_title, "products": serializer.data})


# ============================================================================
# 메인페이지 섹션 뷰들
# ============================================================================


class MonthlyFeaturedDrinksView(BaseSectionView):
    """이달의 전통주 (TOP 3)"""

    section_title = "이달의 전통주"

    @extend_schema(
        summary="이달의 전통주",
        description="조회수 기준 이달의 추천 전통주 TOP 3를 반환합니다. (메인페이지용)",
        tags=["메인페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("monthly", limit=3)


class PopularProductsView(BaseSectionView):
    """인기 패키지"""

    section_title = "인기 패키지"

    @extend_schema(
        summary="인기 패키지",
        description="조회수 기준 인기 패키지 8개를 반환합니다. (메인페이지용)",
        tags=["메인페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("popular", limit=8)


class RecommendedProductsView(BaseSectionView):
    """추천 전통주"""

    section_title = "추천 전통주"

    @extend_schema(
        summary="추천 전통주",
        description="개별 술 상품 중 추천 전통주 8개를 반환합니다. (메인페이지용)",
        tags=["메인페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("recommended", limit=8)


# ============================================================================
# 패키지페이지 섹션 뷰들
# ============================================================================


class FeaturedProductsView(BaseSectionView):
    """추천 패키지"""

    section_title = "추천 패키지"

    @extend_schema(
        summary="추천 패키지",
        description="프리미엄 제품 중 추천 패키지 4개를 반환합니다. (패키지페이지용)",
        tags=["패키지페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("featured", limit=4)


class AwardWinningProductsView(BaseSectionView):
    """수상작 패키지"""

    section_title = "주류 대상 수상 5종 패키지"

    @extend_schema(
        summary="수상작 패키지",
        description="주류 대상 수상작 패키지 4개를 반환합니다. (패키지페이지용)",
        tags=["패키지페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("award_winning", limit=4)


class MakgeolliProductsView(BaseSectionView):
    """막걸리 패키지"""

    section_title = "막걸리 패키지"

    @extend_schema(
        summary="막걸리 패키지",
        description="막걸리만 포함된 패키지 4개를 반환합니다. (패키지페이지용)",
        tags=["패키지페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("makgeolli", limit=4)


class RegionalProductsView(BaseSectionView):
    """지역 특산주 패키지"""

    section_title = "지역 특산주 패키지"

    @extend_schema(
        summary="지역 특산주 패키지",
        description="지역 특산주 패키지 4개를 반환합니다. (패키지페이지용)",
        tags=["패키지페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return ProductService.get_section_products("regional", limit=4)
