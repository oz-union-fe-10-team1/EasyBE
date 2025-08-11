# apps/products/serializers/package.py

from rest_framework import serializers

from apps.products.models import Drink, Package, PackageItem

from .drink import DrinkSimpleSerializer


class PackageSerializer(serializers.ModelSerializer):
    """패키지 통합 시리얼라이저 - 생성/수정/상세"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drinks = DrinkSimpleSerializer(many=True, read_only=True)
    drink_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        min_length=2,
        max_length=5,
        help_text="패키지에 포함할 술 ID 목록 (2~5개)",
    )
    drink_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "type",
            "type_display",
            "drinks",
            "drink_ids",
            "drink_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_drink_count(self, obj):
        """패키지에 포함된 술 개수"""
        return obj.drinks.count()

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

    def validate(self, attrs):
        """패키지 이름 중복 체크"""
        name = attrs.get("name")
        if name:
            # 수정 시에는 자기 자신 제외
            queryset = Package.objects.filter(name=name)
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError({"name": "같은 이름의 패키지가 이미 존재합니다."})
        return attrs

    def create(self, validated_data):
        """패키지 생성"""
        drink_ids = validated_data.pop("drink_ids")
        package = Package.objects.create(**validated_data)

        # 패키지 아이템들 생성
        drinks = Drink.objects.filter(id__in=drink_ids)
        for drink in drinks:
            PackageItem.objects.create(package=package, drink=drink)

        return package

    def update(self, instance, validated_data):
        """패키지 수정"""
        drink_ids = validated_data.pop("drink_ids", None)

        # 기본 필드 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 패키지 아이템 업데이트
        if drink_ids is not None:
            # 기존 아이템들 삭제
            PackageItem.objects.filter(package=instance).delete()

            # 새 아이템들 생성
            drinks = Drink.objects.filter(id__in=drink_ids)
            for drink in drinks:
                PackageItem.objects.create(package=instance, drink=drink)

        return instance


class PackageListSerializer(serializers.ModelSerializer):
    """패키지 목록용 시리얼라이저 (사용하지 않음 - Product 기반으로 대체)"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drink_count = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = ["id", "name", "type", "type_display", "drink_count", "created_at"]

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
