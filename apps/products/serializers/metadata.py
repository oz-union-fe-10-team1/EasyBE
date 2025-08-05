# apps/products/serializers/metadata.py

from rest_framework import serializers

from apps.products.models import AlcoholType, ProductCategory, Region, TasteTag


class RegionSerializer(serializers.ModelSerializer):
    """지역 Serializer"""

    class Meta:
        model = Region
        fields = ["id", "name", "code", "description", "created_at"]


class AlcoholTypeSerializer(serializers.ModelSerializer):
    """주종 Serializer"""

    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = AlcoholType
        fields = ["id", "name", "category", "category_display", "description", "created_at"]


class TasteTagSerializer(serializers.ModelSerializer):
    """맛 태그 Serializer"""

    category_display = serializers.CharField(source="get_category_display", read_only=True)

    class Meta:
        model = TasteTag
        fields = ["id", "name", "category", "category_display", "description", "color_code", "created_at"]


class ProductCategorySerializer(serializers.ModelSerializer):
    """제품 카테고리 Serializer"""

    parent_name = serializers.CharField(source="parent.name", read_only=True)
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "parent",
            "parent_name",
            "full_name",
            "image",
            "sort_order",
            "is_active",
            "created_at",
        ]

    def get_full_name(self, obj):
        """계층 구조 포함한 전체 이름"""
        return str(obj)  # __str__ 메서드 활용


class ProductCategoryTreeSerializer(serializers.ModelSerializer):
    """계층 구조 카테고리 Serializer"""

    children = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ["id", "name", "slug", "description", "image", "sort_order", "is_active", "children"]

    def get_children(self, obj):
        """자식 카테고리들"""
        children = ProductCategory.objects.filter(parent=obj, is_active=True).order_by("sort_order")
        return ProductCategoryTreeSerializer(children, many=True).data
