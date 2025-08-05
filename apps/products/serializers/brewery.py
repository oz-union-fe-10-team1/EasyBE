# apps/products/serializers/brewery.py

from rest_framework import serializers

from apps.products.models import Brewery

from .metadata import RegionSerializer


class BrewerySerializer(serializers.ModelSerializer):
    """양조장 기본 Serializer"""

    region = RegionSerializer(read_only=True)

    class Meta:
        model = Brewery
        fields = [
            "id",
            "name",
            "region",
            "address",
            "phone",
            "email",
            "website",
            "founded_year",
            "description",
            "logo_image",
            "cover_image",
            "is_active",
            "created_at",
            "updated_at",
        ]


class BreweryDetailSerializer(serializers.ModelSerializer):
    """양조장 상세 Serializer (제품 목록 포함)"""

    region = RegionSerializer(read_only=True)
    products_count = serializers.SerializerMethodField()
    active_products_count = serializers.SerializerMethodField()

    class Meta:
        model = Brewery
        fields = [
            "id",
            "name",
            "region",
            "address",
            "phone",
            "email",
            "website",
            "founded_year",
            "description",
            "logo_image",
            "cover_image",
            "is_active",
            "created_at",
            "updated_at",
            "products_count",
            "active_products_count",
        ]

    def get_products_count(self, obj):
        """전체 제품 수"""
        return obj.products.count()

    def get_active_products_count(self, obj):
        """판매중인 제품 수"""
        return obj.products.filter(status="active").count()


class BreweryCreateSerializer(serializers.ModelSerializer):
    """양조장 생성용 Serializer"""

    class Meta:
        model = Brewery
        fields = [
            "name",
            "region",
            "address",
            "phone",
            "email",
            "website",
            "founded_year",
            "description",
            "logo_image",
            "cover_image",
        ]

    def validate_name(self, value):
        """양조장 이름 유효성 검사"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("양조장 이름은 2글자 이상이어야 합니다.")
        return value.strip()

    def validate_phone(self, value):
        """전화번호 유효성 검사"""
        if value and len(value.replace("-", "").replace(" ", "")) < 10:
            raise serializers.ValidationError("올바른 전화번호를 입력해주세요.")
        return value

    def validate_email(self, value):
        """이메일 중복 검사"""
        if value and Brewery.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 등록된 이메일입니다.")
        return value

    def validate_founded_year(self, value):
        """설립연도 유효성 검사"""
        if value and (value < 1900 or value > 2024):
            raise serializers.ValidationError("설립연도는 1900년~2024년 사이여야 합니다.")
        return value
