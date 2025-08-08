# apps/products/serializers/product.py
from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from apps.products.models import Product, ProductImage

from .drink import DrinkCreationSerializer, DrinkSerializer
from .package import (
    PackageCreationSerializer,
    PackageItemCreationSerializer,
    PackageListSerializer,
)


class ProductImageSerializer(serializers.ModelSerializer):
    """상품 이미지 시리얼라이저"""

    class Meta:
        model = ProductImage
        fields = ["image_url", "is_main", "created_at"]


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
            "is_regional_specialty",  # 추가
            "is_limited_edition",  # 추가
            "is_premium",
            "is_award_winning",
            "view_count",
            "like_count",
            "status",
            "created_at",
        ]

    def get_name(self, obj):
        return obj.name

    def get_product_type(self, obj):
        return obj.product_type

    def get_main_image_url(self, obj):
        """메인 이미지 URL 반환"""
        main_image = obj.images.filter(is_main=True).first()
        return main_image.image_url if main_image else None

    def get_brewery_name(self, obj):
        """양조장명 반환"""
        if obj.drink:
            return obj.drink.brewery.name
        return None

    def get_alcohol_type(self, obj):
        """주종 반환"""
        if obj.drink:
            return obj.drink.alcohol_type
        return None

    def get_discount_rate(self, obj):
        """할인율 반환"""
        return obj.get_discount_rate()

    def get_final_price(self, obj):
        """최종 가격 반환"""
        return obj.get_final_price()

    def get_is_on_sale(self, obj):
        """할인 중 여부 반환"""
        return obj.is_on_sale()


class ProductDetailSerializer(serializers.ModelSerializer):
    """상품 상세 시리얼라이저"""

    name = serializers.SerializerMethodField()
    product_type = serializers.SerializerMethodField()
    drink = DrinkSerializer(read_only=True)
    package = PackageListSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)

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

    def get_name(self, obj):
        return obj.name

    def get_product_type(self, obj):
        return obj.product_type

    def get_discount_rate(self, obj):
        return obj.get_discount_rate()

    def get_final_price(self, obj):
        return obj.get_final_price()

    def get_is_on_sale(self, obj):
        return obj.is_on_sale()


class ProductImageCreationSerializer(serializers.ModelSerializer):
    """상품 이미지 생성용 시리얼라이저"""

    class Meta:
        model = ProductImage
        fields = ["image_url", "is_main"]

    def validate(self, attrs):
        """이미지 유효성 검사"""
        if not attrs.get("image_url"):
            raise serializers.ValidationError({"image_url": "이미지 URL은 필수입니다."})
        return attrs


class ProductInfoSerializer(serializers.Serializer):
    """상품 정보 입력용 시리얼라이저"""

    price = serializers.IntegerField(min_value=0)
    original_price = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    discount = serializers.IntegerField(min_value=0, required=False, allow_null=True)
    description = serializers.CharField()
    description_image_url = serializers.URLField()

    # 상품 특성
    is_gift_suitable = serializers.BooleanField(default=False)
    is_award_winning = serializers.BooleanField(default=False)
    is_regional_specialty = serializers.BooleanField(default=False)
    is_limited_edition = serializers.BooleanField(default=False)
    is_premium = serializers.BooleanField(default=False)
    is_organic = serializers.BooleanField(default=False)

    def validate(self, attrs):
        """할인 정보 유효성 검사"""
        original_price = attrs.get("original_price")
        discount = attrs.get("discount")

        # 할인이 있다면 정가도 있어야 함
        if discount and not original_price:
            raise serializers.ValidationError({"original_price": "할인이 있을 경우 정가는 필수입니다."})

        # 할인금액이 정가보다 클 수 없음
        if original_price and discount and discount > original_price:
            raise serializers.ValidationError({"discount": "할인금액이 정가보다 클 수 없습니다."})

        return attrs


class IndividualProductCreationSerializer(serializers.Serializer):
    """개별 상품 생성용 시리얼라이저"""

    drink_info = DrinkCreationSerializer()
    product_info = ProductInfoSerializer()
    images = ProductImageCreationSerializer(many=True)

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

    @transaction.atomic
    def create(self, validated_data):
        """개별 상품 생성 (트랜잭션)"""
        drink_data = validated_data["drink_info"]
        product_data = validated_data["product_info"]
        images_data = validated_data["images"]

        # 1. 술 생성
        drink_serializer = DrinkCreationSerializer(data=drink_data)
        drink_serializer.is_valid(raise_exception=True)
        drink = drink_serializer.save()

        # 2. 상품 생성
        product = Product.objects.create(drink=drink, **product_data)

        # 3. 이미지들 생성
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)

        return product

    def to_representation(self, instance):
        """응답 시리얼라이저"""
        return ProductDetailSerializer(instance).data


class PackageProductCreationSerializer(serializers.Serializer):
    """패키지 상품 생성용 시리얼라이저"""

    package_info = PackageCreationSerializer()
    drink_ids = serializers.ListField(child=serializers.IntegerField(), min_length=2, max_length=5)
    product_info = ProductInfoSerializer()
    images = ProductImageCreationSerializer(many=True)

    def validate_drink_ids(self, value):
        """술 ID 목록 유효성 검사"""
        from apps.products.models import Drink

        # 중복 체크
        if len(value) != len(set(value)):
            raise serializers.ValidationError("중복된 술은 선택할 수 없습니다.")

        # 존재하는 술인지 확인
        existing_drinks = Drink.objects.filter(id__in=value)
        if existing_drinks.count() != len(value):
            raise serializers.ValidationError("존재하지 않는 술이 포함되어 있습니다.")

        return value

    def validate_images(self, value):
        """이미지 유효성 검사"""
        if not value:
            raise serializers.ValidationError("최소 1개의 이미지는 필요합니다.")

        # 메인 이미지 체크
        main_images = [img for img in value if img.get("is_main")]
        if len(main_images) != 1:
            raise serializers.ValidationError("메인 이미지는 정확히 1개여야 합니다.")

        return value

    @transaction.atomic
    def create(self, validated_data):
        """패키지 상품 생성 (트랜잭션)"""
        from apps.products.models import Drink, PackageItem

        package_data = validated_data["package_info"]
        drink_ids = validated_data["drink_ids"]
        product_data = validated_data["product_info"]
        images_data = validated_data["images"]

        # 1. 패키지 생성
        package_serializer = PackageCreationSerializer(data=package_data)
        package_serializer.is_valid(raise_exception=True)
        package = package_serializer.save()

        # 2. 패키지 아이템들 생성
        drinks = Drink.objects.filter(id__in=drink_ids)
        for drink in drinks:
            PackageItem.objects.create(package=package, drink=drink)

        # 3. 상품 생성
        product = Product.objects.create(package=package, **product_data)

        # 4. 이미지들 생성
        for image_data in images_data:
            ProductImage.objects.create(product=product, **image_data)

        return product

    def to_representation(self, instance):
        """응답 시리얼라이저"""
        return ProductDetailSerializer(instance).data


class ProductFilterSerializer(serializers.Serializer):
    """상품 필터링용 시리얼라이저 (UI 기반)"""

    # 체크박스 필터들 (UI 상세 검색)
    is_gift_suitable = serializers.BooleanField(required=False)
    is_regional_specialty = serializers.BooleanField(required=False)
    is_award_winning = serializers.BooleanField(required=False)
    is_limited_edition = serializers.BooleanField(required=False)

    # 맛 프로필 슬라이더들 (0.0 ~ 5.0)
    sweetness_level = serializers.DecimalField(
        max_digits=3, decimal_places=1, min_value=Decimal("0.0"), max_value=Decimal("5.0"), required=False
    )
    acidity_level = serializers.DecimalField(
        max_digits=3, decimal_places=1, min_value=Decimal("0.0"), max_value=Decimal("5.0"), required=False
    )
    bitterness_level = serializers.DecimalField(
        max_digits=3, decimal_places=1, min_value=Decimal("0.0"), max_value=Decimal("5.0"), required=False
    )
    body_level = serializers.DecimalField(
        max_digits=3, decimal_places=1, min_value=Decimal("0.0"), max_value=Decimal("5.0"), required=False
    )
    carbonation_level = serializers.DecimalField(
        max_digits=3, decimal_places=1, min_value=Decimal("0.0"), max_value=Decimal("5.0"), required=False
    )
    aroma_level = serializers.DecimalField(
        max_digits=3, decimal_places=1, min_value=Decimal("0.0"), max_value=Decimal("5.0"), required=False
    )

    # 검색
    search = serializers.CharField(max_length=100, required=False)

    # 정렬
    ordering = serializers.ChoiceField(
        choices=[
            "price",
            "-price",
            "created_at",
            "-created_at",
            "view_count",
            "-view_count",
            "like_count",
            "-like_count",
        ],
        required=False,
        default="-created_at",
    )


class ProductLikeSerializer(serializers.Serializer):
    """상품 좋아요 응답용 시리얼라이저"""

    is_liked = serializers.BooleanField()
    like_count = serializers.IntegerField()
