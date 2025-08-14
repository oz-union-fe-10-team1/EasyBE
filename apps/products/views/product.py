# apps/products/views/product.py

from decimal import Decimal
from typing import Optional, Type

from django.db.models import Case, DecimalField, F, Q, When
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.products.models import Drink, Product, ProductLike
from apps.products.serializers import (
    DrinkForPackageSerializer,
    IndividualProductCreateSerializer,
    PackageProductCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)

from .pagination import SearchPagination

# ============================================================================
# 기본 클래스들
# ============================================================================


class BaseProductListView(ListAPIView):
    """제품 목록 뷰 기본 클래스"""

    serializer_class = ProductListSerializer
    pagination_class: Optional[Type[SearchPagination]] = None

    def get_base_queryset(self):
        """기본 쿼리셋 - 최적화된 조회"""
        return (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images", "package__drinks__brewery")
        )

    def get_queryset(self):
        """각 뷰에서 오버라이드"""
        return self.get_base_queryset()


class BaseSectionView(BaseProductListView):
    """섹션 뷰 기본 클래스 - 제목과 함께 응답"""

    section_title = ""

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"title": self.section_title, "products": serializer.data})


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
        queryset = self.get_base_queryset().annotate(
            discount_rate=Case(
                When(
                    original_price__isnull=False,
                    discount__isnull=False,
                    original_price__gt=0,
                    then=F("discount") * 100.0 / F("original_price"),
                ),
                default=0.0,
                output_field=DecimalField(max_digits=5, decimal_places=1),
            )
        )

        queryset = self._apply_taste_filters(queryset)
        queryset = self._apply_category_filters(queryset)
        return queryset

    def _apply_taste_filters(self, queryset):
        """맛 프로필 슬라이더 필터링"""
        taste_params = {
            "sweetness": "drink__sweetness_level",
            "acidity": "drink__acidity_level",
            "body": "drink__body_level",
            "carbonation": "drink__carbonation_level",
            "bitterness": "drink__bitterness_level",
            "aroma": "drink__aroma_level",
        }

        for param, field in taste_params.items():
            value = self.request.query_params.get(param)
            if value:
                try:
                    target = Decimal(str(value))
                    queryset = queryset.filter(
                        **{f"{field}__gte": max(Decimal("0.0"), target - Decimal("0.5"))},
                        **{f"{field}__lte": min(Decimal("5.0"), target + Decimal("0.5"))},
                    )
                except (ValueError, TypeError):
                    continue
        return queryset

    def _apply_category_filters(self, queryset):
        """카테고리 체크박스 필터링"""
        filter_mapping = {
            "gift_suitable": "is_gift_suitable",
            "regional_specialty": "is_regional_specialty",
            "limited_edition": "is_limited_edition",
            "premium": "is_premium",
            "award_winning": "is_award_winning",
        }

        for param, field in filter_mapping.items():
            if self.request.query_params.get(param) == "true":
                queryset = queryset.filter(**{field: True})
        return queryset


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
        instance = self.get_object()

        # 조회수 증가
        Product.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        return (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images", "package__drinks__brewery")
        )


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
        try:
            product = Product.objects.get(pk=pk, status="ACTIVE")
        except Product.DoesNotExist:
            return Response({"error": "상품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        like, created = ProductLike.objects.get_or_create(user=request.user, product=product)

        if not created:
            like.delete()
            is_liked = False
        else:
            is_liked = True

        # 좋아요 수 업데이트
        like_count = ProductLike.objects.filter(product=product).count()
        Product.objects.filter(pk=product.pk).update(like_count=like_count)

        return Response({"is_liked": is_liked, "like_count": like_count})


# ============================================================================
# 메인페이지 섹션 뷰들
# ============================================================================


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
        return self.get_base_queryset().order_by("-view_count")[:8]


class FeaturedProductsView(BaseSectionView):
    """추천 패키지"""

    section_title = "추천 패키지"

    @extend_schema(
        summary="추천 패키지",
        description="프리미엄 제품 중 추천 패키지 4개를 반환합니다. (메인페이지용)",
        tags=["메인페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return self.get_base_queryset().filter(is_premium=True).order_by("-created_at")[:4]


class RecommendedProductsView(BaseSectionView):
    """추천 전통주"""

    section_title = "추천 전통주"

    @extend_schema(
        summary="추천 전통주",
        description="개별 술 상품 중 추천 전통주 4개를 반환합니다. (메인페이지용)",
        tags=["메인페이지"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Product.objects.filter(status="ACTIVE", drink__isnull=False)
            .select_related("drink__brewery")
            .prefetch_related("images")
            .order_by("-created_at")[:4]
        )


# ============================================================================
# 패키지페이지 섹션 뷰들
# ============================================================================


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
        return self.get_base_queryset().filter(is_award_winning=True).order_by("-order_count")[:4]


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
        return (
            self.get_base_queryset()
            .filter(package__drinks__alcohol_type="MAKGEOLLI")
            .distinct()
            .order_by("-created_at")[:4]
        )


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
        return self.get_base_queryset().filter(is_regional_specialty=True).order_by("-created_at")[:4]


# ============================================================================
# 관리자용 제품 관리 API
# ============================================================================


class IndividualProductCreateView(CreateAPIView):
    """개별 상품 생성 (관리자용)"""

    serializer_class = IndividualProductCreateSerializer
    permission_classes = [IsAuthenticated]

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
