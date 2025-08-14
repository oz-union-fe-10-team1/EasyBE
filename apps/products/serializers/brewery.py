# apps/products/serializers/brewery.py

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.products.models import Brewery, Product


class BrewerySimpleSerializer(serializers.ModelSerializer):
    """양조장 간단 정보 시리얼라이저 - 다른 모델에서 참조용"""

    class Meta:
        model = Brewery
        fields = ["id", "name", "region"]


class BreweryListSerializer(serializers.ModelSerializer):
    """양조장 목록용 시리얼라이저 (관리자용)"""

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brewery
        fields = ["id", "name", "region", "image_url", "product_count"]

    @extend_schema_field(serializers.IntegerField)
    def get_product_count(self, obj) -> int:
        """양조장의 활성 상품 수 계산"""
        return Product.objects.filter(drink__brewery=obj, status="ACTIVE").count()


class BrewerySerializer(serializers.ModelSerializer):
    """양조장 통합 시리얼라이저 - 생성/수정/상세 (관리자용)"""

    drink_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brewery
        fields = [
            "id",
            "name",
            "region",
            "address",
            "phone",
            "description",
            "image_url",
            "is_active",
            "drink_count",
            "product_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    @extend_schema_field(serializers.IntegerField)
    def get_product_count(self, obj) -> int:
        """양조장의 활성 상품 수 계산"""
        return Product.objects.filter(drink__brewery=obj, status="ACTIVE").count()

    @extend_schema_field(serializers.IntegerField)
    def get_drink_count(self, obj) -> int:
        """양조장의 술 개수"""
        return obj.drinks.count()
