# apps/products/views/product.py

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.products.models import Product
from apps.products.serializers import (
    ProductCreateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ProductUpdateSerializer,
)

from ..utils.filters import ProductFilter
from ..utils.permissions import IsAdminOrReadOnly


class ProductViewSet(viewsets.ModelViewSet):
    """
    제품 CRUD ViewSet

    list: 제품 목록 조회 (필터링, 검색, 정렬 지원)
    retrieve: 제품 상세 조회
    create: 제품 생성 (관리자만)
    update: 제품 수정 (관리자만)
    destroy: 제품 삭제 (관리자만)
    """

    queryset = (
        Product.objects.select_related("brewery", "alcohol_type", "region", "category")
        .prefetch_related("images", "taste_tags", "producttastetag_set__taste_tag")
        .all()
    )

    # 권한: 조회는 모든 사용자, 생성/수정/삭제는 관리자만
    permission_classes = [IsAdminOrReadOnly]

    # 필터링, 검색, 정렬
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ["name", "description", "flavor_notes", "brewery__name"]
    ordering_fields = [
        "price",
        "alcohol_content",
        "created_at",
        "order_count",
        "average_rating",
        "view_count",
        "like_count",
    ]
    ordering = ["-created_at"]  # 기본 정렬: 최신순

    def get_serializer_class(self):
        """액션에 따른 Serializer 선택"""
        if self.action == "list":
            return ProductListSerializer
        elif self.action == "create":
            return ProductCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return ProductUpdateSerializer
        else:  # retrieve
            return ProductDetailSerializer

    def get_queryset(self):
        """쿼리셋 최적화 및 필터링"""
        queryset = self.queryset

        # 관리자가 아닌 경우 활성 상태 제품만 조회
        if not self.request.user.is_staff:
            queryset = queryset.filter(status="active")

        return queryset

    def perform_create(self, serializer):
        """제품 생성 시 추가 로직"""
        # 기본값 설정
        product = serializer.save()

        # 생성 로그 (향후 확장 가능)
        # logger.info(f"Product created: {product.name} by {self.request.user}")

    def perform_update(self, serializer):
        """제품 수정 시 추가 로직"""
        product = serializer.save()

        # 수정 로그 (향후 확장 가능)
        # logger.info(f"Product updated: {product.name} by {self.request.user}")

    def retrieve(self, request, *args, **kwargs):
        """제품 상세 조회 (조회수 증가)"""
        instance = self.get_object()

        # 조회수 증가 (관리자 제외)
        if not request.user.is_staff:
            instance.increment_view_count()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """인기 제품 목록"""
        popular_products = self.get_queryset().filter(status="active").order_by("-order_count", "-view_count")[:20]

        serializer = ProductListSerializer(popular_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """추천 제품 목록"""
        featured_products = self.get_queryset().filter(status="active", is_featured=True).order_by("-created_at")[:10]

        serializer = ProductListSerializer(featured_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def new(self, request):
        """신제품 목록"""
        new_products = self.get_queryset().filter(status="active").order_by("-created_at")[:20]

        serializer = ProductListSerializer(new_products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        """제품 찜하기/찜 해제"""
        if not request.user.is_authenticated:
            return Response({"error": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        product = self.get_object()

        # 찜하기/해제 로직은 향후 구현
        # ProductLike 모델 활용

        return Response(
            {
                "message": "찜하기 기능은 향후 구현 예정입니다.",
                "product_id": str(product.id),
                "user_id": request.user.id,
            }
        )

    @action(detail=True, methods=["get"])
    def similar(self, request, pk=None):
        """유사 제품 추천"""
        product = self.get_object()

        # 간단한 유사 제품 로직 (맛 프로필 기반)
        similar_products = (
            Product.objects.filter(alcohol_type=product.alcohol_type, status="active")
            .exclude(id=product.id)
            .order_by("?")[:5]
        )  # 임시로 랜덤 5개

        serializer = ProductListSerializer(similar_products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def filter_options(self, request):
        """필터링 옵션 정보 제공"""
        from django.db import models

        queryset = self.get_queryset().filter(status="active")

        filter_options = {
            "price_range": {
                "min": queryset.aggregate(min_price=models.Min("price"))["min_price"] or 0,
                "max": queryset.aggregate(max_price=models.Max("price"))["max_price"] or 0,
            },
            "alcohol_content_range": {
                "min": queryset.aggregate(min_alcohol=models.Min("alcohol_content"))["min_alcohol"] or 0,
                "max": queryset.aggregate(max_alcohol=models.Max("alcohol_content"))["max_alcohol"] or 0,
            },
            "taste_ranges": {
                "sweetness": {"min": 0.0, "max": 5.0},
                "sourness": {"min": 0.0, "max": 5.0},
                "bitterness": {"min": 0.0, "max": 5.0},
                "umami": {"min": 0.0, "max": 5.0},
                "alcohol_strength": {"min": 0.0, "max": 5.0},
                "body": {"min": 0.0, "max": 5.0},
            },
            "regions": list(
                queryset.values_list("region__name", flat=True).distinct().exclude(region__name__isnull=True)
            ),
            "alcohol_types": list(queryset.values_list("alcohol_type__name", flat=True).distinct()),
            "categories": list(
                queryset.values_list("category__name", flat=True).distinct().exclude(category__name__isnull=True)
            ),
            "breweries": list(queryset.values_list("brewery__name", flat=True).distinct()),
        }

        return Response(filter_options)
