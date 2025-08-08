# apps/products/serializers/package.py

from rest_framework import serializers

from apps.products.models import Package, PackageItem, Product

from .drink import DrinkSimpleSerializer


class PackageListSerializer(serializers.ModelSerializer):
    """패키지 목록용 시리얼라이저 (Package 기반 - 사용하지 않음)"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drink_count = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ["id", "name", "type", "type_display", "drink_count", "created_at"]

    def get_drink_count(self, obj):
        """패키지에 포함된 술 개수"""
        return obj.drinks.count()


class PackageSerializer(serializers.ModelSerializer):
    """패키지 상세용 시리얼라이저"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drinks = DrinkSimpleSerializer(many=True, read_only=True)
    drink_count = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ["id", "name", "type", "type_display", "drinks", "drink_count", "created_at", "updated_at"]

    def get_drink_count(self, obj):
        """패키지에 포함된 술 개수"""
        return obj.drinks.count()


class PackageSimpleSerializer(serializers.ModelSerializer):
    """패키지 간단 정보 시리얼라이저 - 상품에서 참조용"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drink_count = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ["id", "name", "type", "type_display", "drink_count"]

    def get_drink_count(self, obj):
        return obj.drinks.count()


class PackageCreationSerializer(serializers.ModelSerializer):
    """패키지 생성용 시리얼라이저"""

    class Meta:
        model = Package
        fields = ["name", "type"]

    def validate_name(self, value):
        """패키지 이름 유효성 검사"""
        if not value or not value.strip():
            raise serializers.ValidationError("패키지 이름은 필수입니다.")
        return value.strip()

    def validate(self, attrs):
        """패키지 이름 중복 체크"""
        name = attrs.get("name")
        if name and Package.objects.filter(name=name).exists():
            raise serializers.ValidationError({"name": "같은 이름의 패키지가 이미 존재합니다."})
        return attrs


class PackageItemCreationSerializer(serializers.Serializer):
    """패키지 아이템 생성용 시리얼라이저"""

    drink_ids = serializers.ListField(
        child=serializers.IntegerField(), min_length=2, max_length=5, help_text="패키지에 포함할 술 ID 목록 (2~5개)"
    )

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

    def create_package_items(self, package, drink_ids):
        """패키지 아이템들 생성"""
        from apps.products.models import Drink

        drinks = Drink.objects.filter(id__in=drink_ids)
        package_items = []

        for drink in drinks:
            package_item = PackageItem.objects.create(package=package, drink=drink)
            package_items.append(package_item)

        return package_items
