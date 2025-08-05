# apps/products/serializers/product.py

from decimal import Decimal

from rest_framework import serializers

from apps.products.models import Product, ProductTasteTag, TasteTag

from .brewery import BrewerySerializer
from .metadata import AlcoholTypeSerializer, ProductCategorySerializer, RegionSerializer


class ProductTasteTagSerializer(serializers.ModelSerializer):
    """제품-맛태그 중간 테이블 Serializer"""

    class Meta:
        model = ProductTasteTag
        fields = ["taste_tag", "intensity"]

    def to_representation(self, instance):
        """응답 시 맛태그 정보도 포함"""
        data = super().to_representation(instance)
        data["taste_tag_name"] = instance.taste_tag.name
        data["taste_tag_category"] = instance.taste_tag.get_category_display()
        data["color_code"] = instance.taste_tag.color_code
        return data


class ProductListSerializer(serializers.ModelSerializer):
    """제품 목록용 Serializer (간소화된 필드)"""

    brewery = BrewerySerializer(read_only=True)
    alcohol_type = AlcoholTypeSerializer(read_only=True)
    region = RegionSerializer(read_only=True)

    # Property 필드들
    is_available = serializers.ReadOnlyField()
    discount_rate = serializers.ReadOnlyField()
    main_image_url = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "brewery",
            "alcohol_type",
            "region",
            "price",
            "original_price",
            "discount_rate",
            "alcohol_content",
            "volume_ml",
            "main_image_url",
            "is_available",
            # 맛 프로필 (완전한 필드들)
            "sweetness_level",
            "acidity_level",
            "body_level",
            "carbonation_level",
            "bitterness_level",
            "aroma_level",  # 추가
            "flavor_notes",
            "short_description",
            "is_gift_suitable",
            "is_award_winning",
            "is_regional_specialty",
            "view_count",
            "order_count",
            "like_count",
            "average_rating",
            "status",
            "is_featured",
            "created_at",
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    """제품 상세용 Serializer (모든 필드)"""

    brewery = BrewerySerializer(read_only=True)
    alcohol_type = AlcoholTypeSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    category = ProductCategorySerializer(read_only=True)

    # Property 필드들
    is_available = serializers.ReadOnlyField()
    discount_rate = serializers.ReadOnlyField()
    main_image_url = serializers.ReadOnlyField()
    taste_profile_vector = serializers.ReadOnlyField()

    # 맛 태그 관계
    taste_tags_detail = ProductTasteTagSerializer(source="producttastetag_set", many=True, read_only=True)

    class Meta:
        model = Product
        fields = "__all__"

    def to_representation(self, instance):
        """응답 데이터 후처리"""
        data = super().to_representation(instance)

        # 가격을 문자열로 변환 (프론트엔드 호환성)
        if data.get("price"):
            data["price"] = str(data["price"])
        if data.get("original_price"):
            data["original_price"] = str(data["original_price"])

        return data


class ProductCreateSerializer(serializers.ModelSerializer):
    """제품 생성용 Serializer"""

    # 맛 태그 관계 처리를 위한 필드
    taste_tags = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="맛 태그 배열: [{'taste_tag': 1, 'intensity': 2.5}]",
    )

    class Meta:
        model = Product
        fields = [
            # 기본 정보
            "name",
            "brewery",
            "alcohol_type",
            "region",
            "category",
            # 상품 상세
            "description",
            "ingredients",
            "alcohol_content",
            "volume_ml",
            # 가격 정보
            "price",
            "original_price",
            # 재고 관리
            "stock_quantity",
            "min_stock_alert",
            # 맛 프로필
            "sweetness_level",
            "acidity_level",
            "body_level",
            "carbonation_level",
            "bitterness_level",
            "aroma_level",
            # 제품 특성
            "is_gift_suitable",
            "is_award_winning",
            "is_regional_specialty",
            "is_limited_edition",
            "is_premium",
            "is_organic",
            # UI 표시용
            "flavor_notes",
            "short_description",
            "package_name",
            # 상태 관리
            "status",
            "is_featured",
            "launch_date",
            # SEO
            "meta_title",
            "meta_description",
            # 맛 태그
            "taste_tags",
        ]

        # 필수 필드 명시
        extra_kwargs = {
            "alcohol_type": {"required": True},
            "name": {"required": True},
            "brewery": {"required": True},
            "description": {"required": True},
            "ingredients": {"required": True},
            "alcohol_content": {"required": True},
            "volume_ml": {"required": True},
            "price": {"required": True},
        }

    def validate_price(self, value):
        """가격 유효성 검사"""
        if value < 0:
            raise serializers.ValidationError("가격은 0 이상이어야 합니다.")
        return value

    def validate_original_price(self, value):
        """정가 유효성 검사"""
        if value is not None and value < 0:
            raise serializers.ValidationError("정가는 0 이상이어야 합니다.")
        return value

    def validate_alcohol_content(self, value):
        """알코올 도수 유효성 검사"""
        if not 0.0 <= value <= 100.0:
            raise serializers.ValidationError("알코올 도수는 0.0~100.0 사이여야 합니다.")
        return value

    def validate_volume_ml(self, value):
        """용량 유효성 검사"""
        if value <= 0:
            raise serializers.ValidationError("용량은 0보다 커야 합니다.")
        return value

    def validate_stock_quantity(self, value):
        """재고 수량 유효성 검사"""
        if value < 0:
            raise serializers.ValidationError("재고 수량은 0 이상이어야 합니다.")
        return value

    def validate_taste_profile(self, attrs):
        """맛 프로필 필드 통합 유효성 검사"""
        taste_fields = {
            "sweetness_level": "단맛",
            "acidity_level": "산미",
            "body_level": "바디감",
            "carbonation_level": "탄산감",
            "bitterness_level": "쓴맛:누룩맛",
            "aroma_level": "향",
        }

        errors = {}

        for field_name, field_display in taste_fields.items():
            value = attrs.get(field_name)

            # 값이 제공된 경우에만 검증
            if value is not None:
                if not isinstance(value, (int, float)):
                    errors[field_name] = f"{field_display} 지수는 숫자여야 합니다."
                elif not 0.0 <= value <= 5.0:
                    errors[field_name] = f"{field_display} 지수는 0.0~5.0 사이여야 합니다."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def validate(self, attrs):
        """전체 데이터 유효성 검사"""
        # 정가와 판매가 비교
        attrs = self.validate_taste_profile(attrs)

        original_price = attrs.get("original_price")
        price = attrs.get("price")

        if original_price and price and original_price < price:
            raise serializers.ValidationError({"original_price": "정가는 판매가보다 크거나 같아야 합니다."})

        return attrs

    def create(self, validated_data):
        """제품 생성"""
        # 맛 태그 데이터 분리
        taste_tags_data = validated_data.pop("taste_tags", [])

        # 제품 생성
        product = Product.objects.create(**validated_data)

        # 맛 태그 관계 생성
        for taste_tag_data in taste_tags_data:
            taste_tag_id = taste_tag_data.get("taste_tag")
            intensity = taste_tag_data.get("intensity", 1.0)

            try:
                taste_tag = TasteTag.objects.get(id=taste_tag_id)
                ProductTasteTag.objects.create(product=product, taste_tag=taste_tag, intensity=intensity)
            except TasteTag.DoesNotExist:
                # 존재하지 않는 맛 태그는 무시 (또는 에러 발생)
                continue

        return product

    def to_representation(self, instance):
        """생성 후 응답은 DetailSerializer 형식으로"""
        return ProductDetailSerializer(instance, context=self.context).data


class ProductUpdateSerializer(serializers.ModelSerializer):
    """제품 수정용 Serializer"""

    # 맛 태그 관계 처리
    taste_tags = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Product
        fields = [
            "name",
            "description",
            "ingredients",
            "alcohol_content",
            "volume_ml",
            "price",
            "original_price",
            "stock_quantity",
            "min_stock_alert",
            "sweetness_level",
            "acidity_level",
            "bitterness_level",
            "carbonation_level",
            "body_level",
            "aroma_level",
            "is_gift_suitable",
            "is_award_winning",
            "is_regional_specialty",
            "is_limited_edition",
            "is_premium",
            "is_organic",
            "flavor_notes",
            "short_description",
            "package_name",
            "status",
            "is_featured",
            "launch_date",
            "meta_title",
            "meta_description",
            "taste_tags",
        ]

    # ProductCreateSerializer의 모든 validate 메서드 동일하게 적용
    validate_price = ProductCreateSerializer.validate_price
    validate_original_price = ProductCreateSerializer.validate_original_price
    validate_alcohol_content = ProductCreateSerializer.validate_alcohol_content
    validate_volume_ml = ProductCreateSerializer.validate_volume_ml
    validate_stock_quantity = ProductCreateSerializer.validate_stock_quantity
    validate_taste_profile = ProductCreateSerializer.validate_taste_profile
    validate = ProductCreateSerializer.validate

    def update(self, instance, validated_data):
        """제품 수정"""
        # 맛 태그 데이터 분리
        taste_tags_data = validated_data.pop("taste_tags", None)

        # 기본 필드 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 맛 태그 관계 업데이트
        if taste_tags_data is not None:
            # 기존 맛 태그 관계 삭제
            instance.producttastetag_set.all().delete()

            # 새로운 맛 태그 관계 생성
            for taste_tag_data in taste_tags_data:
                taste_tag_id = taste_tag_data.get("taste_tag")
                intensity = taste_tag_data.get("intensity", 1.0)

                try:
                    taste_tag = TasteTag.objects.get(id=taste_tag_id)
                    ProductTasteTag.objects.create(product=instance, taste_tag=taste_tag, intensity=intensity)
                except TasteTag.DoesNotExist:
                    continue

        return instance

    def to_representation(self, instance):
        """수정 후 응답은 DetailSerializer 형식으로"""
        return ProductDetailSerializer(instance, context=self.context).data
