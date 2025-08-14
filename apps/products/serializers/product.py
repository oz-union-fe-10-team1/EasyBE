# apps/products/serializers/product.py

from typing import Any, Dict, Optional

from django.db import transaction
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.products.models import Drink, Package, PackageItem, Product, ProductImage
from apps.products.serializers.brewery import BrewerySimpleSerializer

# ============================================================================
# 기본 시리얼라이저들
# ============================================================================


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


# ============================================================================
# 관리자용 시리얼라이저들
# ============================================================================


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


class DrinkCreateSerializer(serializers.ModelSerializer):
    """술 생성용 시리얼라이저"""

    brewery_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Drink
        fields = [
            "name",
            "brewery_id",
            "ingredients",
            "alcohol_type",
            "abv",
            "volume_ml",
            "sweetness_level",
            "acidity_level",
            "body_level",
            "carbonation_level",
            "bitterness_level",
            "aroma_level",
        ]

    def validate_brewery_id(self, value):
        """양조장 존재 여부 확인"""
        from apps.products.models import Brewery

        if not Brewery.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("존재하지 않거나 비활성 상태인 양조장입니다.")
        return value

    def validate_name(self, value):
        """술 이름 유효성 검사"""
        if not value or not value.strip():
            raise serializers.ValidationError("술 이름은 필수입니다.")
        return value.strip()

    def validate(self, attrs):
        """전체 유효성 검사 - 중복 이름 체크"""
        brewery_id = attrs.get('brewery_id')
        name = attrs.get('name')

        # 같은 양조장에서 동일한 이름의 술이 있는지 확인
        if Drink.objects.filter(brewery_id=brewery_id, name=name).exists():
            raise serializers.ValidationError({
                "name": "같은 양조장에서 동일한 이름의 술이 이미 존재합니다."
            })

        return attrs

    def create(self, validated_data):
        """술 생성"""
        from apps.products.models import Brewery

        brewery_id = validated_data.pop("brewery_id")
        brewery = Brewery.objects.get(id=brewery_id)
        return Drink.objects.create(brewery=brewery, **validated_data)


class PackageCreateSerializer(serializers.ModelSerializer):
    """패키지 생성용 시리얼라이저"""

    drink_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        min_length=2,
        max_length=5,
        help_text="패키지에 포함할 술 ID 목록 (2~5개)",
    )

    class Meta:
        model = Package
        fields = ["name", "type", "drink_ids"]

    def validate_name(self, value):
        """패키지 이름 유효성 검사"""
        if not value or not value.strip():
            raise serializers.ValidationError("패키지 이름은 필수입니다.")
        return value.strip()

    def validate_drink_ids(self, value):
        """술 ID 목록 유효성 검사"""
        # 중복 체크
        if len(value) != len(set(value)):
            raise serializers.ValidationError("중복된 술은 선택할 수 없습니다.")

        # 존재하는 술인지 확인
        existing_drinks = Drink.objects.filter(id__in=value)
        if existing_drinks.count() != len(value):
            raise serializers.ValidationError("존재하지 않는 술이 포함되어 있습니다.")

        return value

    def create(self, validated_data):
        """패키지 생성"""
        drink_ids = validated_data.pop("drink_ids")
        package = Package.objects.create(**validated_data)

        # 패키지 아이템들 생성
        drinks = Drink.objects.filter(id__in=drink_ids)
        for drink in drinks:
            PackageItem.objects.create(package=package, drink=drink)

        return package


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


# ============================================================================
# 패키지 생성용 술 목록 시리얼라이저
# ============================================================================


class DrinkForPackageSerializer(serializers.ModelSerializer):
    """패키지 생성용 술 목록 시리얼라이저"""

    brewery = BrewerySimpleSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Drink
        fields = ["id", "name", "brewery", "alcohol_type", "abv", "main_image", "price"]

    @extend_schema_field(serializers.URLField(allow_null=True))
    def get_main_image(self, obj) -> Optional[str]:
        """술의 메인 이미지 URL 반환"""
        try:
            if hasattr(obj, "product") and obj.product:
                main_image = obj.product.images.filter(is_main=True).first()
                if main_image:
                    return main_image.image_url
        except:
            pass
        return None

    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_price(self, obj) -> Optional[int]:
        """술의 개별 상품 가격 반환"""
        try:
            if hasattr(obj, "product") and obj.product:
                return obj.product.price
        except:
            pass
        return None
