# apps/products/views/package.py

from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from apps.products.models import Package, Product
from apps.products.serializers import PackageSerializer, ProductListSerializer

from .pagination import StandardPagination


class PackageListView(ListAPIView):
    """패키지 목록 API - GET /api/v1/packages/ (UI 패키지페이지용)"""

    serializer_class = ProductListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        """패키지 상품들을 Product 테이블에서 필터링"""
        queryset = (
            Product.objects.filter(status="ACTIVE", package__isnull=False)
            .select_related("package")
            .prefetch_related("package__drinks__brewery", "images")
            .order_by("-created_at")
        )

        return self._apply_filters(queryset)

    def _apply_filters(self, queryset):
        """Product 기반 필터링 (UI 패키지 카테고리용)"""
        # 패키지 타입 필터링
        package_type = self.request.query_params.get("type")
        if package_type and package_type in ["CURATED", "MY_CUSTOM"]:
            queryset = queryset.filter(package__type=package_type)

        # Product 필드 기반 카테고리 필터링
        if self.request.query_params.get("is_premium"):
            queryset = queryset.filter(is_premium=True)

        if self.request.query_params.get("is_award_winning"):
            queryset = queryset.filter(is_award_winning=True)

        if self.request.query_params.get("is_regional_specialty"):
            queryset = queryset.filter(is_regional_specialty=True)

        # 막걸리 패키지 - 포함된 술이 모두 막걸리인 패키지
        if self.request.query_params.get("category") == "makgeolli":
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


class PackageCreateView(CreateAPIView):
    """패키지 생성 API - POST /api/v1/packages/ (어드민용)"""

    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]


class PackageManageView(RetrieveUpdateDestroyAPIView):
    """패키지 관리 API - GET/PUT/PATCH/DELETE /api/v1/packages/{id}/manage/ (어드민용)"""

    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Package.objects.prefetch_related("drinks__brewery")

    def perform_destroy(self, instance):
        # 연관된 상품이 있으면 삭제 불가
        if hasattr(instance, "product") and instance.product:
            from rest_framework.exceptions import ValidationError

            raise ValidationError("연관된 상품이 있어 삭제할 수 없습니다.")
        instance.delete()
