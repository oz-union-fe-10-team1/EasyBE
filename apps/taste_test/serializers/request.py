"""
요청 관련 시리얼라이저
"""

from drf_spectacular.utils import OpenApiExample, extend_schema_serializer
from rest_framework import serializers

from ..services import TasteTestService


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "테스트 답변 예시",
            value={"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}},
            description="6개 질문에 대한 A 또는 B 답변",
        )
    ]
)
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