# apps/taste_test/serializers.py

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .exceptions import TasteTestError
from .models import TasteAnswer, TasteQuestion, TasteTest, TasteType, UserProfile
from .services import TasteAnalyzer  # services.py에서 import

User = get_user_model()
logger = logging.getLogger(__name__)


class TasteAnswerSerializer(serializers.ModelSerializer):
    """맛 테스트 답변 시리얼라이저"""

    class Meta:
        model = TasteAnswer
        fields = ["id", "answer_text"]


class TasteQuestionSerializer(serializers.ModelSerializer):
    """맛 테스트 질문 시리얼라이저"""

    answers = TasteAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = TasteQuestion
        fields = ["id", "question_text", "sequence", "answers"]


class TasteTestSerializer(serializers.ModelSerializer):
    """맛 테스트 시리얼라이저"""

    questions = TasteQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = TasteTest
        fields = ["id", "title", "description", "questions"]


class TasteTestQuestionsListSerializer(serializers.Serializer):
    """질문 목록 응답 시리얼라이저"""

    def to_representation(self, instance):
        """커스텀 응답 구조"""
        test = instance.get("test")
        if not test:
            raise serializers.ValidationError("테스트 정보가 없습니다.")

        questions = test.questions.filter(test__is_active=True).order_by("sequence")

        return {
            "test": {"id": test.id, "title": test.title, "description": test.description},
            "questions": TasteQuestionSerializer(questions, many=True).data,
            "total_questions": questions.count(),
            "instructions": "각 질문에 답변을 선택해주세요.",
            "estimated_time": "약 3-5분",
        }


class TasteTestSubmitSerializer(serializers.Serializer):
    """맛 테스트 제출 시리얼라이저 - 회원만"""

    test_id = serializers.IntegerField(help_text="테스트 ID")
    answers = serializers.ListField(
        child=serializers.DictField(),
        help_text="답변 목록 [{'question_id': 1, 'answer_id': 2}, ...]",
        min_length=6,  # 6개 질문 모두 필수
        max_length=6,
    )

    def validate_test_id(self, value):
        """테스트 ID 유효성 검사"""
        try:
            test = TasteTest.objects.get(id=value, is_active=True)
            self.test = test  # 나중에 사용하기 위해 저장
            return value
        except TasteTest.DoesNotExist:
            raise serializers.ValidationError("유효하지 않거나 비활성화된 테스트입니다.")

    def validate_answers(self, value):
        """답변 유효성 검사"""
        if len(value) != 6:
            raise serializers.ValidationError("6개의 모든 질문에 대한 답변이 필요합니다.")

        # 답변 구조 검사
        required_fields = {"question_id", "answer_id"}
        for i, answer in enumerate(value):
            if not isinstance(answer, dict):
                raise serializers.ValidationError(f"답변 {i + 1}이 올바른 형식이 아닙니다.")

            missing_fields = required_fields - set(answer.keys())
            if missing_fields:
                raise serializers.ValidationError(f"답변 {i + 1}에 필수 필드가 누락되었습니다: {missing_fields}")

            # 타입 검사
            try:
                answer["question_id"] = int(answer["question_id"])
                answer["answer_id"] = int(answer["answer_id"])
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"답변 {i + 1}의 ID 값이 올바르지 않습니다.")

        # 중복 질문 검사
        question_ids = [answer["question_id"] for answer in value]
        if len(question_ids) != len(set(question_ids)):
            raise serializers.ValidationError("중복된 질문에 대한 답변이 있습니다.")

        # 1~6번 질문이 모두 있는지 확인
        if set(question_ids) != {1, 2, 3, 4, 5, 6}:
            raise serializers.ValidationError("1번부터 6번까지 모든 질문에 답변해야 합니다.")

        # 질문과 답변 존재 여부 검사
        self._validate_questions_and_answers(value)

        return value

    def _validate_questions_and_answers(self, answers):
        """질문과 답변의 존재 여부 및 관계 검사"""
        for answer in answers:
            question_id = answer["question_id"]
            answer_id = answer["answer_id"]

            try:
                question = TasteQuestion.objects.get(
                    id=question_id,
                    test_id=self.test.id if hasattr(self, "test") else None,
                    sequence=question_id,  # sequence와 question_id가 일치해야 함
                )
                TasteAnswer.objects.get(id=answer_id, question=question)
            except TasteQuestion.DoesNotExist:
                raise serializers.ValidationError(f"질문 ID {question_id}가 이 테스트에 존재하지 않습니다.")
            except TasteAnswer.DoesNotExist:
                raise serializers.ValidationError(f"답변 ID {answer_id}가 질문 ID {question_id}에 존재하지 않습니다.")

    def validate(self, attrs):
        """전체 데이터 검증"""
        request = self.context.get("request")
        if not request:
            raise serializers.ValidationError("요청 컨텍스트가 필요합니다.")

        # 인증 필수 (회원만)
        if not request.user.is_authenticated:
            raise serializers.ValidationError("회원만 테스트를 진행할 수 있습니다.")

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """테스트 결과 생성 및 점수 계산 - services.py 사용"""
        try:
            request = self.context["request"]
            test_id = validated_data["test_id"]
            answers = validated_data["answers"]

            # 이미 테스트를 완료한 사용자인지 확인
            if hasattr(request.user, "taste_profile") and request.user.taste_profile.taste_test_completed_at:
                logger.info(f"User {request.user.id}가 테스트를 재실행합니다.")

            # services.py의 TasteAnalyzer 사용
            analyzer = TasteAnalyzer(request.user, test_id, answers)
            result = analyzer.analyze_and_save()

            logger.info(
                f"맛 테스트 완료 - User: {request.user.id}, Type: {result.profile.initial_taste_type.type_name}"
            )
            return result

        except Exception as e:
            logger.error(f"맛 테스트 처리 중 오류: {str(e)}")
            raise TasteTestError(f"테스트 처리 중 오류가 발생했습니다: {str(e)}")


class TasteTypeSerializer(serializers.ModelSerializer):
    """맛 타입 시리얼라이저"""

    characteristics = serializers.SerializerMethodField()

    class Meta:
        model = TasteType
        fields = ["id", "type_name", "type_description", "type_image_url", "characteristics", "created_at"]

    def get_characteristics(self, obj):
        """특성 정보 추가"""
        from .services import TasteScoreCalculator

        return TasteScoreCalculator._get_type_characteristics(obj.type_name)


class TasteResultSerializer(serializers.Serializer):
    """테스트 결과 응답 시리얼라이저"""

    taste_type_id = serializers.IntegerField(read_only=True, allow_null=True)
    taste_type_name = serializers.CharField(read_only=True, allow_null=True)
    description = serializers.CharField(read_only=True)
    type_count = serializers.IntegerField(read_only=True, help_text="결정된 유형 개수")
    all_scores = serializers.DictField(read_only=True, help_text="모든 유형별 점수")
    characteristics = serializers.ListField(read_only=True)
    image_url = serializers.URLField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    confidence = serializers.FloatField(read_only=True, help_text="신뢰도 점수")

    # 추천 상품 (선택사항)
    recommended_products = serializers.ListField(required=False, read_only=True)

    def to_representation(self, instance):
        """결과 데이터 구조화"""
        if not hasattr(instance, "profile"):
            raise serializers.ValidationError("프로필 정보가 없습니다.")

        profile = instance.profile
        taste_type = profile.initial_taste_type

        return {
            "taste_type_id": taste_type.id if taste_type else None,
            "taste_type_name": taste_type.type_name if taste_type else None,
            "description": taste_type.type_description if taste_type else None,
            "image_url": taste_type.type_image_url if taste_type else None,
            "created_at": profile.taste_test_completed_at,
            "type_count": getattr(instance, "type_count", 1),
            "all_scores": getattr(instance, "all_scores", {}),
            "characteristics": getattr(instance, "characteristics", []),
            "confidence": getattr(instance, "confidence", 0.0),
            "recommended_products": getattr(instance, "recommended_products", []),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """사용자 프로필 시리얼라이저"""

    taste_type_id = serializers.IntegerField(source="initial_taste_type.id", read_only=True, allow_null=True)
    taste_type_name = serializers.CharField(source="initial_taste_type.type_name", read_only=True, allow_null=True)
    taste_type_description = serializers.CharField(
        source="initial_taste_type.type_description", read_only=True, allow_null=True
    )
    taste_type_image_url = serializers.URLField(
        source="initial_taste_type.type_image_url", read_only=True, allow_null=True
    )

    # 추가 정보들
    type_count = serializers.ReadOnlyField()
    all_scores = serializers.ReadOnlyField()
    characteristics = serializers.ReadOnlyField()

    # 알고리즘 상태 (향후 확장용)
    algorithm_status = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "has_completed_test",
            "taste_test_completed_at",
            "taste_type_id",
            "taste_type_name",
            "taste_type_description",
            "taste_type_image_url",
            "type_count",
            "all_scores",
            "characteristics",
            "algorithm_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_algorithm_status(self, obj):
        """알고리즘 상태 정보 (향후 피드백 기능 추가 시 사용)"""
        return {
            "has_algorithm": False,  # 아직 피드백 기반 학습 미구현
            "feedback_count": 0,
            "confidence_score": 0.0,
            "last_learning_at": None,
        }
