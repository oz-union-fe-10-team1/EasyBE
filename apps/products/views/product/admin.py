# apps/products/views/product/admin.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters
from rest_framework.exceptions import ValidationError
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

        **동작:**
        1. 새로운 술 정보를 받아서 Drink 생성
        2. 생성된 술로 개별 Product 생성
        3. 상품 이미지들 생성

        **필요한 정보:**
        - drink_info: 새로 생성할 술의 모든 정보
        - 상품 기본 정보 (가격, 설명, 특성 등)
        - 이미지 목록 (메인 이미지 1개 필수)
        """,
        examples=[
            OpenApiExample(
                "개별 상품 생성 요청",
                value={
                    "drink_info": {
                        "name": "신제품 막걸리",
                        "brewery_id": 1,
                        "ingredients": "쌀, 누룩, 정제수",
                        "alcohol_type": "MAKGEOLLI",
                        "abv": 6.0,
                        "volume_ml": 750,
                        "sweetness_level": 3.0,
                        "acidity_level": 2.5,
                        "body_level": 2.0,
                        "carbonation_level": 1.5,
                        "bitterness_level": 1.0,
                        "aroma_level": 4.0,
                    },
                    "price": 25000,
                    "original_price": 30000,
                    "discount": 5000,
                    "description": "깔끔하고 부드러운 맛의 프리미엄 막걸리",
                    "description_image_url": "https://example.com/desc.jpg",
                    "is_gift_suitable": True,
                    "is_premium": True,
                    "is_regional_specialty": False,
                    "images": [
                        {"image_url": "https://example.com/main.jpg", "is_main": True},
                        {"image_url": "https://example.com/sub1.jpg", "is_main": False},
                        {"image_url": "https://example.com/sub2.jpg", "is_main": False},
                    ],
                },
            )
        ],
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

        **동작:**
        1. 기존 술들의 ID를 받아서 Package 생성
        2. 생성된 패키지로 Product 생성
        3. 상품 이미지들 생성

        **필요한 정보:**
        - package_info: 패키지명과 포함할 술들의 ID
        - 상품 기본 정보 (가격, 설명, 특성 등)
        - 이미지 목록 (메인 이미지 1개 필수)

        **주의사항:**
        - drink_ids는 2~5개 사이여야 함
        - 중복된 술 ID는 불가
        """,
        examples=[
            OpenApiExample(
                "패키지 상품 생성 요청",
                value={
                    "package_info": {"name": "전통주 프리미엄 세트", "type": "CURATED", "drink_ids": [1, 3, 5]},
                    "price": 80000,
                    "original_price": 95000,
                    "discount": 15000,
                    "description": "엄선된 전통주 3종을 담은 프리미엄 세트",
                    "description_image_url": "https://example.com/package-desc.jpg",
                    "is_gift_suitable": True,
                    "is_premium": True,
                    "is_award_winning": True,
                    "images": [
                        {"image_url": "https://example.com/package-main.jpg", "is_main": True},
                        {"image_url": "https://example.com/package-detail.jpg", "is_main": False},
                    ],
                },
            )
        ],
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

        **조건:**
        - 이미 상품화된 술들만 표시
        - 활성 상태인 상품들만

        **응답 정보:**
        - 술 기본 정보 (이름, 양조장, 주종, 도수)
        - 해당 술의 개별 상품 가격
        - 메인 이미지
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

        **삭제 규칙:**
        - 개별 상품: 해당 술이 패키지에 포함되어 있으면 삭제 불가
        - 패키지 상품: 바로 삭제 가능
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

        **일반 사용자용 검색과의 차이점:**
        - 모든 상태의 제품 조회 가능 (ACTIVE, INACTIVE, OUT_OF_STOCK)
        - 맛 프로필 필터링 없음
        - 관리 목적의 단순한 목록
        """,
        parameters=[
            OpenApiParameter("search", OpenApiTypes.STR, description="검색어"),
            OpenApiParameter("ordering", OpenApiTypes.STR, description="정렬 (-created_at, price, -price, status)"),
            OpenApiParameter("status", OpenApiTypes.STR, description="상태 필터 (ACTIVE, INACTIVE, OUT_OF_STOCK)"),
        ],
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
