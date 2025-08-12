from rest_framework import serializers

from .models import PreferenceTestResult
from .services import TasteTestService


class TasteTestAnswersSerializer(serializers.Serializer):
    """테스트 답변 제출용 시리얼라이저"""

    answers = serializers.DictField(
        child=serializers.ChoiceField(choices=["A", "B"]),
        help_text="질문별 답변 (예: {'Q1': 'A', 'Q2': 'B', 'Q3': 'A', 'Q4': 'B', 'Q5': 'A', 'Q6': 'B'})",
    )

    def validate_answers(self, value):
        """답변 유효성 검증"""
        # 기본 길이 검증 (6개 질문)
        if len(value) != 6:
            raise serializers.ValidationError(f"정확히 6개의 답변이 필요합니다. 현재: {len(value)}개")

        # 서비스 레이어의 상세 검증
        errors = TasteTestService.validate_answers(value)
        if errors:
            error_messages = []
            for field, messages in errors.items():
                error_messages.extend(messages)
            raise serializers.ValidationError(error_messages)
        return value

    def create(self, validated_data):
        """테스트 결과 생성 및 저장"""
        user = self.context["request"].user
        answers = validated_data["answers"]
        return TasteTestService.save_test_result(user, answers)


class PreferenceTestResultSerializer(serializers.ModelSerializer):
    """테스트 결과 조회용 시리얼라이저"""

    user_nickname = serializers.CharField(source="user.nickname", read_only=True)
    prefer_taste_display = serializers.CharField(source="get_prefer_taste_display", read_only=True)
    taste_description = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    type_info = serializers.SerializerMethodField()

    class Meta:
        model = PreferenceTestResult
        fields = [
            "id",
            "user_nickname",
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


class TasteTestResultSerializer(serializers.Serializer):
    """테스트 결과 응답용 시리얼라이저"""

    type = serializers.CharField(help_text="결정된 취향 유형 (한국어)")
    scores = serializers.DictField(child=serializers.IntegerField(), help_text="각 기본 유형별 점수")
    info = serializers.DictField(help_text="유형 상세 정보")
    saved = serializers.BooleanField(default=False, help_text="DB 저장 여부")


class TasteTypeInfoSerializer(serializers.Serializer):
    """취향 유형 정보 시리얼라이저"""

    name = serializers.CharField(help_text="유형명")
    enum = serializers.CharField(help_text="enum 값")
    description = serializers.CharField(help_text="유형 설명")
    characteristics = serializers.ListField(child=serializers.CharField(), help_text="특징 목록")
    image_url = serializers.CharField(help_text="이미지 URL")
