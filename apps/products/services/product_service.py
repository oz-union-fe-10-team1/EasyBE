# apps/products/services/product_service.py

from typing import Optional

from django.db.models import F
from django.shortcuts import get_object_or_404

from apps.products.models import Product


class ProductService:
    """상품 관련 비즈니스 로직"""

    @staticmethod
    def get_product_detail(product_id: str) -> Product:
        """
        상품 상세 조회 (조회수 증가 포함)

        Args:
            product_id: 상품 ID

        Returns:
            Product: 조회수가 증가된 상품 객체

        Raises:
            Http404: 상품이 존재하지 않거나 비활성 상태일 때
        """
        # 상품 존재 여부 확인
        product = get_object_or_404(
            Product.objects.select_related("drink__brewery", "package").prefetch_related(
                "images", "package__drinks__brewery"
            ),
            pk=product_id,
            status="ACTIVE",
        )

        # 조회수 증가
        ProductService.increment_view_count(product_id)

        # 업데이트된 상품 객체 반환
        product.refresh_from_db()
        return product

    @staticmethod
    def increment_view_count(product_id: str) -> None:
        """
        상품 조회수 증가

        Args:
            product_id: 상품 ID
        """
        Product.objects.filter(pk=product_id).update(view_count=F("view_count") + 1)

    @staticmethod
    def get_product_list_queryset():
        """
        상품 목록 조회용 최적화된 쿼리셋 반환

        Returns:
            QuerySet: 최적화된 상품 쿼리셋
        """
        return (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images", "package__drinks__brewery")
        )

    @staticmethod
    def get_package_products_by_alcohol_type(alcohol_type: str, limit: int = 4):
        """
        특정 주종이 포함된 패키지 상품만 조회

        Args:
            alcohol_type: 주종 (MAKGEOLLI, YAKJU, etc.)
            limit: 반환할 상품 수

        Returns:
            QuerySet: 해당 주종이 포함된 패키지 상품들
        """
        return (
            Product.objects.filter(
                status="ACTIVE", package__isnull=False, package__drinks__alcohol_type=alcohol_type  # 패키지 상품만
            )
            .select_related("package")
            .prefetch_related("images", "package__drinks__brewery")
            .distinct()
            .order_by("-created_at")[:limit]
        )

    @staticmethod
    def get_section_products(section_type: str, limit: int = 8):
        """
        섹션별 상품 목록 조회

        Args:
            section_type: 섹션 타입 ('popular', 'featured', 'recommended', etc.)
            limit: 반환할 상품 수

        Returns:
            QuerySet: 섹션에 맞는 상품 목록
        """
        base_queryset = ProductService.get_product_list_queryset()

        if section_type == "popular":
            return base_queryset.order_by("-view_count")[:limit]

        elif section_type == "featured":
            # 패키지페이지용: 프리미엄 패키지만
            return base_queryset.filter(is_premium=True, package__isnull=False).order_by("-created_at")[  # 패키지만
                :limit
            ]

        elif section_type == "recommended":
            return base_queryset.filter(drink__isnull=False).order_by("-created_at")[:limit]

        elif section_type == "monthly":
            return base_queryset.filter(drink__isnull=False).order_by("-view_count")[:3]

        elif section_type == "award_winning":
            # 패키지페이지용: 수상작 패키지만
            return base_queryset.filter(is_award_winning=True, package__isnull=False).order_by(  # 패키지만
                "-order_count"
            )[:limit]

        elif section_type == "makgeolli":
            # 패키지페이지 전용: 막걸리 패키지만
            return ProductService.get_package_products_by_alcohol_type("MAKGEOLLI", limit)

        elif section_type == "regional":
            # 패키지페이지용: 지역특산주 패키지만
            return base_queryset.filter(is_regional_specialty=True, package__isnull=False).order_by(  # 패키지만
                "-created_at"
            )[:limit]

        else:
            return base_queryset.none()

    @staticmethod
    def get_product_for_management(product_id: str) -> Product:
        """
        관리자용 상품 조회 (모든 상태 포함)

        Args:
            product_id: 상품 ID

        Returns:
            Product: 상품 객체
        """
        return get_object_or_404(
            Product.objects.select_related("drink__brewery", "package").prefetch_related(
                "images", "package__drinks__brewery"
            ),
            pk=product_id,
        )
