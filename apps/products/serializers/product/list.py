from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from typing import Optional

from apps.products.models import Product

class ProductListSerializer(serializers.ModelSerializer):
    """상품 목록용 시리얼라이저"""

    name = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    brewery_name = serializers.SerializerMethodField()
    alcohol_type = serializers.SerializerMethodField()

    # 할인 관련 계산 필드
    discount_rate = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_type",
            "price",
            "original_price",
            "discount",
            "discount_rate",
            "final_price",
            "is_on_sale",
            "main_image_url",
            "brewery_name",
            "alcohol_type",
            "is_gift_suitable",
            "is_regional_specialty",
            "is_limited_edition",
            "is_premium",
            "is_award_winning",
            "view_count",
            "like_count",
            "status",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj) -> str:
        return obj.name

    @extend_schema_field(serializers.CharField)
    def get_product_type(self, obj) -> str:
        return obj.product_type

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_main_image_url(self, obj) -> Optional[str]:
        """메인 이미지 URL 반환"""
        main_image = obj.images.filter(is_main=True).first()
        return main_image.image_url if main_image else None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_brewery_name(self, obj) -> Optional[str]:
        """양조장명 반환"""
        if obj.drink:
            return obj.drink.brewery.name
        return None

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_alcohol_type(self, obj) -> Optional[str]:
        """주종 반환"""
        if obj.drink:
            return obj.drink.alcohol_type
        return None

    @extend_schema_field(serializers.FloatField)
    def get_discount_rate(self, obj) -> float:
        """할인율 반환"""
        return obj.get_discount_rate()

    @extend_schema_field(serializers.IntegerField)
    def get_final_price(self, obj) -> int:
        """최종 가격 반환"""
        return obj.get_final_price()

    @extend_schema_field(serializers.BooleanField)
    def get_is_on_sale(self, obj) -> bool:
        """할인 중 여부 반환"""
        return obj.is_on_sale()