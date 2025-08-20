from django.db import transaction
from rest_framework import serializers

from apps.products.models import Product, ProductImage

from ..drink import DrinkCreateSerializer
from ..package import PackageCreateSerializer
from .detail import ProductDetailSerializer

# 다른 시리얼라이저들 import
from .image import ProductImageCreateSerializer


class ProductBaseCreateSerializer(serializers.Serializer):
    """상품 생성 기본 시리얼라이저"""

    # 가격 정보
    price = serializers.IntegerField(min_value=0)
    original_price = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    discount = serializers.IntegerField(min_value=0, required=False, allow_null=True)

    # 상품 설명
    description = serializers.CharField()
    description_image_url = serializers.URLField()

    # 상품 특성
    is_gift_suitable = serializers.BooleanField(default=False)
    is_award_winning = serializers.BooleanField(default=False)
    is_regional_specialty = serializers.BooleanField(default=False)
    is_limited_edition = serializers.BooleanField(default=False)
    is_premium = serializers.BooleanField(default=False)
    is_organic = serializers.BooleanField(default=False)

    # 이미지
    images = ProductImageCreateSerializer(many=True)

    def validate(self, attrs):
        """공통 유효성 검사"""
        original_price = attrs.get("original_price")
        discount = attrs.get("discount")

        # 할인이 있다면 정가도 있어야 함
        if discount and not original_price:
            raise serializers.ValidationError({"original_price": "할인이 있을 경우 정가는 필수입니다."})

        # 할인금액이 정가보다 클 수 없음
        if original_price and discount and discount > original_price:
            raise serializers.ValidationError({"discount": "할인금액이 정가보다 클 수 없습니다."})

        return attrs

    def validate_images(self, value):
        """이미지 유효성 검사"""
        if not value:
            raise serializers.ValidationError("최소 1개의 이미지는 필요합니다.")

        # 메인 이미지 체크
        main_images = [img for img in value if img.get("is_main")]
        if len(main_images) != 1:
            raise serializers.ValidationError("메인 이미지는 정확히 1개여야 합니다.")

        if len(value) > 5:
            raise serializers.ValidationError("이미지는 최대 5개까지 업로드 가능합니다.")

        return value

    def create_product_images(self, product, images_data):
        """상품 이미지들 생성"""
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)


class IndividualProductCreateSerializer(ProductBaseCreateSerializer):
    """개별 상품 생성용 시리얼라이저"""

    drink_info = DrinkCreateSerializer()

    @transaction.atomic
    def create(self, validated_data):
        """개별 상품 생성 (트랜잭션)"""
        drink_data = validated_data.pop("drink_info")
        images_data = validated_data.pop("images")

        # 1. 술 생성
        drink_serializer = DrinkCreateSerializer(data=drink_data)
        drink_serializer.is_valid(raise_exception=True)
        drink = drink_serializer.save()

        # 2. 상품 생성
        product = Product.objects.create(drink=drink, **validated_data)

        # 3. 이미지들 생성
        self.create_product_images(product, images_data)

        return product

    def to_representation(self, instance):
        """응답 시리얼라이저"""
        return ProductDetailSerializer(instance).data


class PackageProductCreateSerializer(ProductBaseCreateSerializer):
    """패키지 상품 생성용 시리얼라이저"""

    package_info = PackageCreateSerializer()

    @transaction.atomic
    def create(self, validated_data):
        """패키지 상품 생성 (트랜잭션)"""
        package_data = validated_data.pop("package_info")
        images_data = validated_data.pop("images")

        # 1. 패키지 생성
        package_serializer = PackageCreateSerializer(data=package_data)
        package_serializer.is_valid(raise_exception=True)
        package = package_serializer.save()

        # 2. 상품 생성
        product = Product.objects.create(package=package, **validated_data)

        # 3. 이미지들 생성
        self.create_product_images(product, images_data)

        return product

    def to_representation(self, instance):
        """응답 시리얼라이저"""
        return ProductDetailSerializer(instance).data
