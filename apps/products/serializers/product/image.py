# apps/products/serializers/product/image.py

from rest_framework import serializers
from apps.products.models import ProductImage


class ProductImageSerializer(serializers.ModelSerializer):
    """상품 이미지 시리얼라이저"""

    class Meta:
        model = ProductImage
        fields = ["image_url", "is_main", "created_at"]


class ProductImageCreateSerializer(serializers.ModelSerializer):
    """상품 이미지 생성용 시리얼라이저"""

    class Meta:
        model = ProductImage
        fields = ["image_url", "is_main"]

    def validate_image_url(self, value):
        """이미지 URL 유효성 검사"""
        if not value or not value.strip():
            raise serializers.ValidationError("이미지 URL은 필수입니다.")
        return value.strip()