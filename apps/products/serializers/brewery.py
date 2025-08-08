# apps/products/serializers/brewery.py

from rest_framework import serializers

from apps.products.models import Brewery


class BreweryListSerializer(serializers.ModelSerializer):
    """양조장 목록용 시리얼라이저 - 간단한 정보만"""

    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Brewery
        fields = ["id", "name", "region", "image_url", "product_count"]

    def get_product_count(self, obj):
        """양조장의 상품 수 계산"""
        from apps.products.models import Product

        return Product.objects.filter(drink__brewery=obj, status="ACTIVE").count()


class BrewerySerializer(serializers.ModelSerializer):
    """양조장 상세 시리얼라이저"""

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

    def get_drink_count(self, obj):
        """양조장의 술 개수"""
        return obj.drinks.count()

    def get_product_count(self, obj):
        """양조장의 활성 상품 수"""
        from apps.products.models import Product

        return Product.objects.filter(drink__brewery=obj, status="ACTIVE").count()


class BrewerySimpleSerializer(serializers.ModelSerializer):
    """양조장 간단 정보 시리얼라이저 - 다른 모델에서 참조용"""

    class Meta:
        model = Brewery
        fields = ["id", "name", "region"]
