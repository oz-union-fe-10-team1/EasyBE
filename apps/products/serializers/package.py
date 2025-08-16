
from rest_framework import serializers
from apps.products.models import Package, Drink, PackageItem


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