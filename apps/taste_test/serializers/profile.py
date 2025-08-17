"""
프로필 관련 시리얼라이저
"""

from rest_framework import serializers

from ..models import PreferenceTestResult
from ..services import TasteTestService


class PreferenceTestResultSerializer(serializers.ModelSerializer):
    """테스트 결과 조회용 시리얼라이저"""

    prefer_taste_display = serializers.CharField(source="get_prefer_taste_display", read_only=True)
    taste_description = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    type_info = serializers.SerializerMethodField()

    class Meta:
        model = PreferenceTestResult
        fields = [
            "id",
            "answers",
            "prefer_taste",
            "prefer_taste_display",
            "taste_description",
            "image_url",
            "type_info",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_taste_description(self, obj):
        """취향 설명 반환"""
        return obj.get_taste_description()

    def get_image_url(self, obj):
        """이미지 URL 반환"""
        return TasteTestService.get_image_url_by_enum(obj.prefer_taste)

    def get_type_info(self, obj):
        """전체 타입 정보 반환"""
        korean_name = obj.get_prefer_taste_display()
        return TasteTestService.get_type_info(korean_name)


class PreferenceTestResultProfileSerializer(serializers.ModelSerializer):
    """프로필용 테스트 결과 시리얼라이저 (답변 제외)"""

    user_nickname = serializers.CharField(source="user.nickname", read_only=True)
    prefer_taste_display = serializers.CharField(source="get_prefer_taste_display", read_only=True)
    taste_description = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PreferenceTestResult
        fields = [
            "id",
            "user_nickname",
            "prefer_taste",
            "prefer_taste_display",
            "taste_description",
            "image_url",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_taste_description(self, obj):
        """취향 설명 반환"""
        return obj.get_taste_description()

    def get_image_url(self, obj):
        """이미지 URL 반환"""
        return TasteTestService.get_image_url_by_enum(obj.prefer_taste)
