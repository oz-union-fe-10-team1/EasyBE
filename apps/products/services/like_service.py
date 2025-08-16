# apps/products/services/like_service.py

from typing import Tuple

from django.contrib.auth import get_user_model
from django.db.models import F
from django.shortcuts import get_object_or_404

from apps.products.models import Product, ProductLike

User = get_user_model()


class LikeService:
    """상품 좋아요 관련 비즈니스 로직"""

    @staticmethod
    def toggle_product_like(user, product_id: str) -> Tuple[bool, int]:
        """
        상품 좋아요 토글

        Args:
            user: 사용자 객체
            product_id: 상품 ID

        Returns:
            Tuple[bool, int]: (좋아요 상태, 총 좋아요 수)

        Raises:
            Http404: 상품이 존재하지 않거나 비활성 상태일 때
        """
        # 상품 존재 확인
        product = get_object_or_404(Product, pk=product_id, status="ACTIVE")

        # 좋아요 토글
        like, created = ProductLike.objects.get_or_create(user=user, product=product)

        if not created:
            # 이미 좋아요가 있으면 삭제
            like.delete()
            is_liked = False
        else:
            # 새로 좋아요 추가
            is_liked = True

        # 좋아요 수 업데이트 및 반환
        like_count = LikeService.update_product_like_count(product_id)

        return is_liked, like_count

    @staticmethod
    def update_product_like_count(product_id: str) -> int:
        """
        상품의 좋아요 수 업데이트

        Args:
            product_id: 상품 ID

        Returns:
            int: 업데이트된 좋아요 수
        """
        like_count = ProductLike.objects.filter(product_id=product_id).count()

        Product.objects.filter(pk=product_id).update(like_count=like_count)

        return like_count

    @staticmethod
    def get_user_liked_products(user):
        """
        사용자가 좋아요한 상품 목록 조회

        Args:
            user: 사용자 객체

        Returns:
            QuerySet: 좋아요한 상품들
        """
        return (
            Product.objects.filter(likes__user=user, status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images")
        )

    @staticmethod
    def check_user_liked_product(user, product_id: str) -> bool:
        """
        사용자가 특정 상품을 좋아요했는지 확인

        Args:
            user: 사용자 객체
            product_id: 상품 ID

        Returns:
            bool: 좋아요 여부
        """
        if not hasattr(user, "is_authenticated") or not user.is_authenticated:
            return False

        return ProductLike.objects.filter(user=user, product_id=product_id).exists()
