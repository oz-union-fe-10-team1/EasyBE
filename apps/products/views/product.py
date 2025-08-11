# apps/products/views/product.py
from decimal import Decimal

from django.db.models import Case, DecimalField, F, Q, When
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
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
    ProductFilterSerializer,
    ProductLikeSerializer,
    ProductListSerializer,
)

from .pagination import MainPagePagination, SearchPagination, StandardPagination


class ProductListView(ListAPIView):
    """상품 목록 조회 API - GET /api/v1/products/ (UI 검색페이지용)"""

    serializer_class = ProductListSerializer
    pagination_class = SearchPagination  # 16개씩
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["drink__name", "package__name", "description"]
    ordering_fields = ["price", "created_at", "view_count", "like_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """필터링된 상품 목록 반환"""
        queryset = (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images")
        )

        # 할인율 계산 필드 추가
        queryset = queryset.annotate(
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

        return self._apply_filters(queryset)

    def _apply_filters(self, queryset):
        """커스텀 필터 적용 (UI 기반)"""
        filter_serializer = ProductFilterSerializer(data=self.request.query_params)
        if not filter_serializer.is_valid():
            return queryset

        filters_data = filter_serializer.validated_data

        # 체크박스 필터들
        checkbox_filters = {
            "is_gift_suitable": "is_gift_suitable",
            "is_regional_specialty": "is_regional_specialty",
            "is_award_winning": "is_award_winning",
            "is_limited_edition": "is_limited_edition",
        }

        for param, field in checkbox_filters.items():
            if filters_data.get(param):
                queryset = queryset.filter(**{field: True})

        # 맛 프로필 슬라이더 필터들 (±1 범위)
        taste_filters = [
            "sweetness_level",
            "acidity_level",
            "bitterness_level",
            "body_level",
            "carbonation_level",
            "aroma_level",
        ]

        for taste_filter in taste_filters:
            if filters_data.get(taste_filter) is not None:
                target = filters_data[taste_filter]
                queryset = queryset.filter(
                    **{f"drink__{taste_filter}__gte": max(Decimal("0.0"), target - Decimal("1.0"))},
                    **{f"drink__{taste_filter}__lte": min(Decimal("5.0"), target + Decimal("1.0"))},
                )

        # 정렬
        ordering = filters_data.get("ordering", "-created_at")
        queryset = queryset.order_by(ordering)

        return queryset


class ProductDetailView(RetrieveAPIView):
    """상품 상세 조회 API - GET /api/v1/products/{id}/ (UI 상품상세페이지용)"""

    serializer_class = ProductDetailSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images", "package__drinks__brewery")
        )

    def retrieve(self, request, *args, **kwargs):
        """상품 상세 조회 시 조회수 증가"""
        instance = self.get_object()

        # 조회수 증가
        Product.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class IndividualProductCreateView(CreateAPIView):
    """개별 상품 생성 API - POST /api/v1/products/individual/ (어드민용)"""

    serializer_class = IndividualProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """개별 상품 생성"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            product = serializer.save()
            return Response(serializer.to_representation(product), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"상품 생성 중 오류가 발생했습니다: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PackageProductCreateView(CreateAPIView):
    """패키지 상품 생성 API - POST /api/v1/products/package/ (어드민용)"""

    serializer_class = PackageProductCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        """패키지 상품 생성"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            product = serializer.save()
            return Response(serializer.to_representation(product), status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"패키지 생성 중 오류가 발생했습니다: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DrinksForPackageView(ListAPIView):
    """패키지 생성용 술 목록 API - GET /api/v1/drinks/for-package/ (어드민용)"""

    serializer_class = DrinkForPackageSerializer
    pagination_class = StandardPagination  # 20개씩

    def get_queryset(self):
        """상품이 있는 술들만 반환"""
        return (
            Drink.objects.filter(product__isnull=False, product__status="ACTIVE")
            .select_related("brewery")
            .prefetch_related("product__images")
            .order_by("name")
        )


class ProductLikeToggleView(APIView):
    """상품 좋아요 토글 API - POST /api/v1/products/{id}/like/ (UI용)"""

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """좋아요 토글"""
        try:
            product = Product.objects.get(pk=pk, status="ACTIVE")
        except Product.DoesNotExist:
            return Response({"error": "상품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        like, created = ProductLike.objects.get_or_create(user=request.user, product=product)

        if not created:
            # 이미 좋아요가 있으면 제거
            like.delete()
            is_liked = False
        else:
            is_liked = True

        # 좋아요 수 업데이트
        like_count = ProductLike.objects.filter(product=product).count()
        Product.objects.filter(pk=product.pk).update(like_count=like_count)

        serializer = ProductLikeSerializer({"is_liked": is_liked, "like_count": like_count})
        return Response(serializer.data)


class ProductDeleteView(DestroyAPIView):
    """상품 삭제 API - DELETE /api/v1/products/{id}/ (어드민용)"""

    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        return Product.objects.all()

    def perform_destroy(self, instance):
        from rest_framework.exceptions import ValidationError

        if instance.drink:  # 개별 상품인 경우
            # 해당 술이 패키지에 포함되어 있는지 체크
            if instance.drink.packages.exists():
                package_names = list(instance.drink.packages.values_list("name", flat=True))
                raise ValidationError(
                    f"이 술이 다음 패키지에 포함되어 있습니다: {', '.join(package_names)}. "
                    f"패키지 상품을 먼저 삭제해주세요."
                )

        # 패키지 상품이거나 패키지에 포함되지 않은 개별 상품만 삭제
        instance.delete()


class PopularProductsView(ListAPIView):
    """인기 상품 API - GET /api/v1/products/popular/ (UI 메인페이지용)"""

    serializer_class = ProductListSerializer
    pagination_class = MainPagePagination  # 8개씩

    def get_queryset(self):
        """조회수 기준 인기 상품"""
        return (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images")
            .order_by("-view_count")[:20]
        )


class FeaturedProductsView(ListAPIView):
    """추천 상품 API - GET /api/v1/products/featured/ (UI 메인페이지용)"""

    serializer_class = ProductListSerializer
    pagination_class = MainPagePagination  # 8개씩

    def get_queryset(self):
        """프리미엄 상품들을 추천 상품으로"""
        return (
            Product.objects.filter(status="ACTIVE", is_premium=True)
            .select_related("drink__brewery", "package")
            .prefetch_related("images")
            .order_by("-created_at")[:20]
        )
