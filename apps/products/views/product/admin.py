# apps/products/views/product/admin.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import filters
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.products.models import Drink, Product
from apps.products.serializers.drink import DrinkForPackageSerializer
from apps.products.serializers.product.create import (
    IndividualProductCreateSerializer,
    PackageProductCreateSerializer,
)
from apps.products.serializers.product.detail import ProductDetailSerializer
from apps.products.serializers.product.list import ProductListSerializer

from ..pagination import SearchPagination

# ============================================================================
# 관리자용 제품 관리 API
# ============================================================================


class IndividualProductCreateView(CreateAPIView):
    """개별 상품 생성 (관리자용)"""

    serializer_class = IndividualProductCreateSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary="개별 상품 생성",
        description="""
        새로운 술과 개별 상품을 동시에 생성합니다. (관리자용)
        """,
        tags=["관리자 - 제품 관리"],
    )
    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class PackageProductCreateView(CreateAPIView):
    """패키지 상품 생성 (관리자용)"""

    serializer_class = PackageProductCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="패키지 상품 생성",
        description="""
        기존 술들을 선택해서 패키지와 상품을 생성합니다. (관리자용)
        """,
        tags=["관리자 - 제품 관리"],
    )
    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class DrinksForPackageView(ListAPIView):
    """패키지 생성용 술 목록 조회 (관리자용)"""

    serializer_class = DrinkForPackageSerializer
    pagination_class = SearchPagination
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="패키지 생성용 술 목록",
        description="""
        패키지에 포함할 수 있는 술들의 목록을 조회합니다. (관리자용)
        """,
        tags=["관리자 - 제품 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """상품이 있는 술들만 반환"""
        return (
            Drink.objects.filter(product__isnull=False, product__status="ACTIVE")
            .select_related("brewery")
            .prefetch_related("product__images")
            .order_by("name")
        )


class ProductManageView(RetrieveUpdateDestroyAPIView):
    """제품 관리 (관리자용)"""

    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    @extend_schema(
        summary="제품 관리 - 조회",
        description="""
        제품의 상세 정보를 조회합니다. (관리자용)
        모든 상태의 제품을 조회할 수 있습니다.
        """,
        tags=["관리자 - 제품 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(exclude=True)
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(summary="제품 정보 수정", description="제품 정보를 부분 수정합니다.", tags=["관리자 - 제품 관리"])
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="제품 삭제",
        description="""
        제품을 삭제합니다.
        """,
        tags=["관리자 - 제품 관리"],
    )
    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        """관리자는 모든 상태의 제품 조회 가능"""
        return Product.objects.select_related("drink__brewery", "package").prefetch_related(
            "images", "package__drinks__brewery"
        )

    def perform_destroy(self, instance):
        """제품 삭제 시 검증 로직"""
        if instance.drink:
            # 해당 술이 패키지에 포함되어 있는지 체크
            if instance.drink.packages.exists():
                package_names = list(instance.drink.packages.values_list("name", flat=True))
                from rest_framework.exceptions import ValidationError

                raise ValidationError(
                    f"이 술이 다음 패키지에 포함되어 있습니다: {', '.join(package_names)}. "
                    f"패키지 상품을 먼저 삭제해주세요."
                )

        # 패키지 상품이거나 패키지에 포함되지 않은 개별 상품만 삭제
        instance.delete()


class ProductManageListView(ListAPIView):
    """제품 목록 관리 (관리자용)"""

    serializer_class = ProductListSerializer
    pagination_class = SearchPagination
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["drink__name", "package__name", "description"]
    ordering_fields = ["price", "created_at", "view_count", "status"]
    ordering = ["-created_at"]

    @extend_schema(
        summary="제품 목록 관리",
        description="""
        모든 제품의 목록을 조회합니다. (관리자용)
        """,
        tags=["관리자 - 제품 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """관리자는 모든 상태의 제품 조회 가능"""
        queryset = Product.objects.select_related("drink__brewery", "package").prefetch_related("images")

        # 상태 필터링
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset
