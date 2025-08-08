# apps/products/views/package.py

from decimal import Decimal

from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

from apps.products.models import Package, Product
from apps.products.serializers import PackageSerializer, ProductListSerializer


class StandardPagination(PageNumberPagination):
    """표준 페이지네이션"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class PackageListView(ListAPIView):
    """패키지 목록 API - GET /api/v1/packages/ (UI 패키지페이지용)"""

    serializer_class = ProductListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        """패키지 상품들을 Product 테이블에서 필터링"""
        # Product 테이블에서 패키지 상품만 조회
        queryset = (
            Product.objects.filter(status="ACTIVE", package__isnull=False)  # 패키지 상품만
            .select_related("package")
            .prefetch_related("package__drinks__brewery", "images")
            .order_by("-created_at")
        )

        return self._apply_filters(queryset)

    def _apply_filters(self, queryset):
        """Product 기반 필터링 (UI 패키지 카테고리용)"""
        # 기존 Package 타입 필터링
        package_type = self.request.query_params.get("type")
        if package_type and package_type in ["CURATED", "MY_CUSTOM"]:
            queryset = queryset.filter(package__type=package_type)

        # Product 필드 기반 카테고리 필터링 (UI 카테고리용)
        if self.request.query_params.get("is_premium"):
            queryset = queryset.filter(is_premium=True)  # 추천 패키지

        if self.request.query_params.get("is_award_winning"):
            queryset = queryset.filter(is_award_winning=True)  # 주류 대상 수상 5종

        if self.request.query_params.get("is_regional_specialty"):
            queryset = queryset.filter(is_regional_specialty=True)  # 지역 특산주

        # 막걸리 패키지 - 포함된 술이 모두 막걸리인 패키지
        if self.request.query_params.get("category") == "makgeolli":
            # 막걸리가 아닌 다른 술이 포함된 패키지는 제외
            queryset = (
                queryset.exclude(package__drinks__alcohol_type__in=["YAKJU", "CHEONGJU", "SOJU", "FRUIT_WINE"])
                .filter(package__drinks__alcohol_type="MAKGEOLLI")
                .distinct()
            )

        return queryset


class PackageDetailView(RetrieveAPIView):
    """패키지 상세 API - GET /api/v1/packages/{id}/"""

    serializer_class = PackageSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Package.objects.prefetch_related("drinks__brewery")
