# apps/taste_test/models.py

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class TasteTest(models.Model):
    """맛 테스트 (ERD: taste_tests)"""

    title = models.CharField(max_length=255, help_text="테스트 제목")

    description = models.TextField(blank=True, help_text="테스트 설명")

    is_active = models.BooleanField(default=True, help_text="활성화 여부")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "맛 테스트"
        verbose_name_plural = "맛 테스트"

    def __str__(self):
        return self.title


class TasteQuestion(models.Model):
    """맛 테스트 질문 (ERD: taste_questions)"""

    test = models.ForeignKey(TasteTest, on_delete=models.CASCADE, related_name="questions")

    question_text = models.TextField(help_text="질문 내용")

    sequence = models.PositiveIntegerField(help_text="질문 순서")

    class Meta:
        verbose_name = "맛 테스트 질문"
        verbose_name_plural = "맛 테스트 질문"
        ordering = ["sequence"]

    def __str__(self):
        return f"Q{self.sequence}: {self.question_text[:50]}"


class TasteAnswer(models.Model):
    """맛 테스트 답변 선택지 (ERD: taste_answers)"""

    question = models.ForeignKey(TasteQuestion, on_delete=models.CASCADE, related_name="answers")

    answer_text = models.TextField(help_text="답변 내용")

    score_vector = models.JSONField(default=dict, help_text="맛 계수에 미치는 영향 (JSON 형태) - 예: {'달콤과일': 1}")

    class Meta:
        verbose_name = "맛 테스트 답변"
        verbose_name_plural = "맛 테스트 답변"

    def __str__(self):
        return f"{self.question.sequence}번 질문 답변: {self.answer_text[:30]}"


class TasteType(models.Model):
    """맛 타입 (ERD: taste_types)"""

    type_name = models.CharField(max_length=100, help_text="맛 타입명 (달콤과일, 상큼톡톡, 목적여운, 깔끔고소, 미식가)")

    type_description = models.TextField(help_text="타입 설명")

    type_image_url = models.URLField(blank=True, help_text="타입 이미지 URL")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "맛 타입"
        verbose_name_plural = "맛 타입"

    def __str__(self):
        return self.type_name


class UserProfile(models.Model):
    """사용자 프로필 (ERD: user_profiles) - 회원만"""

    # Customer 대신 User 직접 연결
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="taste_profile")

    initial_taste_type = models.ForeignKey(
        TasteType, on_delete=models.SET_NULL, null=True, blank=True, help_text="최초 입맛 테스트 결과"
    )

    taste_test_completed_at = models.DateTimeField(null=True, blank=True, help_text="테스트 완료 시간")

    # 테스트 결과 상세 정보 저장 (JSON)
    test_results = models.JSONField(default=dict, blank=True, help_text="테스트 상세 결과 (점수, 유형 수 등)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "사용자 프로필"
        verbose_name_plural = "사용자 프로필"

    def __str__(self):
        return f"{self.user.nickname} 프로필"

    @property
    def has_completed_test(self):
        """테스트 완료 여부"""
        return self.taste_test_completed_at is not None

    @property
    def test_result_type(self):
        """테스트 결과 타입명"""
        return self.initial_taste_type.type_name if self.initial_taste_type else None

    @property
    def all_scores(self):
        """모든 유형별 점수"""
        return self.test_results.get("type_scores", {})

    @property
    def type_count(self):
        """결정된 유형 개수"""
        return self.test_results.get("result_data", {}).get("type_count", 0)

    @property
    def characteristics(self):
        """유형 특성"""
        return self.test_results.get("result_data", {}).get("characteristics", [])

    @property
    def confidence_score(self):
        """신뢰도 점수"""
        return self.test_results.get("result_data", {}).get("confidence", 0.0)


class TasteTypeRecommendation(models.Model):
    """맛 타입별 추천 상품 (ERD: taste_type_recommendations)"""

    taste_type = models.ForeignKey(TasteType, on_delete=models.CASCADE, related_name="recommendations")

    # 임시로 product_id를 문자열로 저장 (나중에 Product 모델과 연결)
    product_id = models.CharField(max_length=36, help_text="추천 상품 ID (UUID)")

    recommendation_order = models.PositiveIntegerField(default=1, help_text="추천 순서")

    recommendation_reason = models.TextField(blank=True, help_text="추천 이유")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "맛 타입 추천"
        verbose_name_plural = "맛 타입 추천"
        unique_together = ("taste_type", "product_id")
        ordering = ["taste_type", "recommendation_order"]

    def __str__(self):
        return f"{self.taste_type.type_name} - {self.product_id} (순서: {self.recommendation_order})"
