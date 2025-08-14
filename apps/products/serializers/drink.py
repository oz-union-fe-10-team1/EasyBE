# apps/products/serializers/drink.py

from rest_framework import serializers

from apps.products.models import Drink

from .brewery import BrewerySimpleSerializer


class DrinkListSerializer(serializers.ModelSerializer):
    """술 목록용 시리얼라이저 (관리자용 - 선택 목록)"""

    brewery = BrewerySimpleSerializer(read_only=True)
    alcohol_type_display = serializers.CharField(source="get_alcohol_type_display", read_only=True)

    class Meta:
        model = Drink
        fields = ["id", "name", "brewery", "alcohol_type", "alcohol_type_display", "abv", "volume_ml", "created_at"]
