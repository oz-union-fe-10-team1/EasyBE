from typing import Any, Dict, Optional

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.products.models import Product
from .image import ProductImageSerializer

class ProductDetailSerializer(serializers.ModelSerializer):
    """상품 상세 시리얼라이저"""

    name = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()

    # 관련 객체들 - 인라인화된 정보
    drink = serializers.SerializerMethodField()
    package = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)

    # 할인 정보
    discount_rate = serializers.SerializerMethodField()
    final_price = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "product_type",
            "drink",
            "package",
            "price",
            "original_price",
            "discount",
            "discount_rate",
            "final_price",
            "is_on_sale",
            "description",
            "description_image_url",
            "is_gift_suitable",
            "is_award_winning",
            "is_regional_specialty",
            "is_limited_edition",
            "is_premium",
            "is_organic",
            "view_count",
            "order_count",
            "like_count",
            "review_count",
            "status",
            "images",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_name(self, obj) -> str:
        return obj.name

    @extend_schema_field(serializers.CharField)
    def get_product_type(self, obj) -> str:
        return obj.product_type

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_drink(self, obj) -> Optional[Dict[str, Any]]:
        """개별 술 정보 - 인라인화"""
        if not obj.drink:
            return None

        drink = obj.drink
        return {
            "id": drink.id,
            "name": drink.name,
            "brewery": {
                "id": drink.brewery.id,
                "name": drink.brewery.name,
                "region": drink.brewery.region,
            },
            "ingredients": drink.ingredients,
            "alcohol_type": drink.alcohol_type,
            "alcohol_type_display": drink.get_alcohol_type_display(),
            "abv": float(drink.abv),
            "volume_ml": drink.volume_ml,
            "taste_profile": {
                "sweetness": float(drink.sweetness_level),
                "acidity": float(drink.acidity_level),
                "body": float(drink.body_level),
                "carbonation": float(drink.carbonation_level),
                "bitterness": float(drink.bitterness_level),
                "aroma": float(drink.aroma_level),
            },
            "created_at": drink.created_at,
            "updated_at": drink.updated_at,
        }

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_package(self, obj) -> Optional[Dict[str, Any]]:
        """패키지 정보 - 인라인화"""
        if not obj.package:
            return None

        package = obj.package
        drinks_data = []

        for drink in package.drinks.all():
            drinks_data.append(
                {
                    "id": drink.id,
                    "name": drink.name,
                    "brewery": {
                        "id": drink.brewery.id,
                        "name": drink.brewery.name,
                        "region": drink.brewery.region,
                    },
                    "alcohol_type": drink.alcohol_type,
                    "alcohol_type_display": drink.get_alcohol_type_display(),
                    "abv": float(drink.abv),
                    "volume_ml": drink.volume_ml,
                }
            )

        return {
            "id": package.id,
            "name": package.name,
            "type": package.type,
            "type_display": package.get_type_display(),
            "drinks": drinks_data,
            "drink_count": package.drinks.count(),
            "created_at": package.created_at,
            "updated_at": package.updated_at,
        }

    @extend_schema_field(serializers.FloatField)
    def get_discount_rate(self, obj) -> float:
        return obj.get_discount_rate()

    @extend_schema_field(serializers.IntegerField)
    def get_final_price(self, obj) -> int:
        return obj.get_final_price()

    @extend_schema_field(serializers.BooleanField)
    def get_is_on_sale(self, obj) -> bool:
        return obj.is_on_sale()