# apps/products/serializers/drink.py

from rest_framework import serializers

from apps.products.models import Drink

from .brewery import BrewerySimpleSerializer


class DrinkListSerializer(serializers.ModelSerializer):
    """술 목록용 시리얼라이저"""

    brewery = BrewerySimpleSerializer(read_only=True)
    alcohol_type_display = serializers.CharField(source="get_alcohol_type_display", read_only=True)

    class Meta:
        model = Drink
        fields = ["id", "name", "brewery", "alcohol_type", "alcohol_type_display", "abv", "volume_ml", "created_at"]


class DrinkSerializer(serializers.ModelSerializer):
    """술 상세 시리얼라이저"""

    brewery = BrewerySimpleSerializer(read_only=True)
    alcohol_type_display = serializers.CharField(source="get_alcohol_type_display", read_only=True)
    taste_profile = serializers.SerializerMethodField()

    class Meta:
        model = Drink
        fields = [
            "id",
            "name",
            "brewery",
            "ingredients",
            "alcohol_type",
            "alcohol_type_display",
            "abv",
            "volume_ml",
            # 맛 프로필
            "sweetness_level",
            "acidity_level",
            "body_level",
            "carbonation_level",
            "bitterness_level",
            "aroma_level",
            "taste_profile",
            "created_at",
            "updated_at",
        ]

    def get_taste_profile(self, obj):
        """맛 프로필 벡터 형태로 반환"""
        return {
            "sweetness": float(obj.sweetness_level),
            "acidity": float(obj.acidity_level),
            "body": float(obj.body_level),
            "carbonation": float(obj.carbonation_level),
            "bitterness": float(obj.bitterness_level),
            "aroma": float(obj.aroma_level),
        }


class DrinkForPackageSerializer(serializers.ModelSerializer):
    """패키지 생성용 술 목록 시리얼라이저"""

    brewery = BrewerySimpleSerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()

    class Meta:
        model = Drink
        fields = ["id", "name", "brewery", "alcohol_type", "abv", "main_image", "price"]

    def get_main_image(self, obj):
        """술의 메인 이미지 URL 반환"""
        try:
            if hasattr(obj, "product") and obj.product:
                main_image = obj.product.images.filter(is_main=True).first()
                if main_image:
                    return main_image.image_url
        except:
            pass
        return None

    def get_price(self, obj):
        """술의 개별 상품 가격 반환"""
        try:
            if hasattr(obj, "product") and obj.product:
                return obj.product.price
        except:
            pass
        return None


class DrinkSimpleSerializer(serializers.ModelSerializer):
    """술 간단 정보 시리얼라이저 - 패키지에서 참조용"""

    brewery = BrewerySimpleSerializer(read_only=True)
    alcohol_type_display = serializers.CharField(source="get_alcohol_type_display", read_only=True)

    class Meta:
        model = Drink
        fields = ["id", "name", "brewery", "alcohol_type", "alcohol_type_display", "abv", "volume_ml"]


class DrinkCreationSerializer(serializers.ModelSerializer):
    """술 생성용 시리얼라이저 - 상품 생성 시 사용"""

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
        """양조장별 술 이름 중복 체크"""
        brewery_id = attrs.get("brewery_id")
        name = attrs.get("name")

        if brewery_id and name:
            if Drink.objects.filter(brewery_id=brewery_id, name=name).exists():
                raise serializers.ValidationError({"name": "해당 양조장에 같은 이름의 술이 이미 존재합니다."})

        return attrs

    def create(self, validated_data):
        """술 생성"""
        from apps.products.models import Brewery

        brewery_id = validated_data.pop("brewery_id")
        brewery = Brewery.objects.get(id=brewery_id)

        drink = Drink.objects.create(brewery=brewery, **validated_data)
        return drink
