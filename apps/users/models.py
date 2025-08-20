import datetime

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.users.utils.user_manager import UserManager
from config.settings import base


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "USER", "사용자"
        ADMIN = "ADMIN", "관리자"

    # 기본 정보
    nickname = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    # 성인 인증 관련
    is_adult = models.BooleanField(default=False, help_text="성인 인증 여부")
    adult_verified_at = models.DateTimeField(null=True, blank=True, help_text="성인 인증 완료 일시")

    # 알림 동의
    notification_agreed = models.BooleanField(default=True, help_text="알림 수신 동의")

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    recovery_deadline = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "nickname"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_adult"]),  # 성인 인증 여부로 필터링할 때 사용
            models.Index(fields=["created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.nickname} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_user(self):
        return self.role == self.Role.USER

    @property
    def is_staff(self):
        """Django admin 접근 권한"""
        return self.is_admin

    def make_admin(self):
        """사용자를 관리자로 승격"""
        self.role = self.Role.ADMIN
        self.save(update_fields=["role", "updated_at"])

    def make_user(self):
        """관리자를 일반 사용자로 강등"""
        self.role = self.Role.USER
        self.save(update_fields=["role", "updated_at"])

    def verify_adult(self):
        """성인 인증 처리"""
        from django.utils import timezone

        self.is_adult = True
        self.adult_verified_at = timezone.now()
        self.save(update_fields=["is_adult", "adult_verified_at", "updated_at"])

    def soft_delete(self):
        """회원 탈퇴 처리 (2주 뒤 완전 삭제 예정)"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.recovery_deadline = timezone.now() + datetime.timedelta(days=14)
        self.save(update_fields=["is_deleted", "deleted_at", "recovery_deadline"])

    def restore_account(self):
        """회원 복구 처리"""
        self.is_deleted = False
        self.deleted_at = None
        self.recovery_deadline = None
        self.save(update_fields=["is_deleted", "deleted_at", "recovery_deadline"])


class SocialAccount(models.Model):
    """사용자의 소셜 계정 정보"""

    class Provider(models.TextChoices):
        KAKAO = "KAKAO", "카카오"
        NAVER = "NAVER", "네이버"
        GOOGLE = "GOOGLE", "구글"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="social_accounts")
    provider = models.CharField(max_length=10, choices=Provider.choices)
    provider_id = models.CharField(max_length=255)
    provider_email = models.EmailField(null=True, blank=True)  # 각 소셜에서 제공하는 이메일

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_social_accounts"
        unique_together = ("provider", "provider_id")  # 유니크로 묶어서 동일한 소셜 계정 중복 방지
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["provider", "provider_id"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.provider}"


class PreferTasteProfile(models.Model):
    """사용자 취향 프로필 (진화하는 학습 시스템)"""

    user = models.OneToOneField(base.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taste_profile")

    # 맛 프로필 점수 (0.0 ~ 5.0)
    sweetness_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="단맛 선호도",
    )
    acidity_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="산미 선호도",
    )
    body_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="바디감 선호도",
    )
    carbonation_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="탄산감 선호도",
    )
    bitterness_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="쓴맛 선호도",
    )
    aroma_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=2.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="향 선호도",
    )

    # 메타데이터
    total_reviews_count = models.PositiveIntegerField(default=0, help_text="반영된 총 리뷰 수")

    # 재테스트 관련 필드들
    retake_count = models.PositiveIntegerField(default=0, help_text="재테스트 횟수")
    last_retake_at = models.DateTimeField(null=True, blank=True, help_text="마지막 재테스트 일시")
    last_retake_influence = models.DecimalField(
        max_digits=3, decimal_places=2, null=True, blank=True, help_text="마지막 재테스트 영향률"
    )
    retake_base_scores = models.JSONField(null=True, blank=True, help_text="재테스트 기준점 (점진적 적용용)")

    # 분석 관련
    analysis_description = models.TextField(blank=True, help_text="취향 분석 설명")
    analysis_updated_at = models.DateTimeField(null=True, blank=True, help_text="분석 마지막 업데이트 시간")

    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prefer_taste_profiles"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["last_updated"]),
            models.Index(fields=["last_retake_at"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} 취향 프로필"

    def initialize_from_test_result(self, test_result):
        """취향 테스트 결과로 초기값 설정"""
        from apps.taste_test.services import TasteTestData

        initial_scores = TasteTestData.TASTE_PROFILES.get(test_result.prefer_taste, {})
        for field, score in initial_scores.items():
            setattr(self, field, score)

        self.save()

    def update_from_review(self, feedback):
        """피드백을 바탕으로 취향 점수 업데이트 (진화하는 방식)"""
        from apps.users.utils.taste_analysis import TasteAnalysisService

        TasteAnalysisService.update_taste_profile_from_feedback(self, feedback)

    def handle_retake(self, new_test_result):
        """재테스트 처리 (기존 학습 보존하면서 새로운 성향 반영)"""
        from apps.users.utils.taste_analysis import TasteAnalysisService

        return TasteAnalysisService.handle_taste_test_retake(self, new_test_result)

    def get_taste_scores_dict(self):
        """맛 점수들을 딕셔너리로 반환 (API용)"""
        return {
            "sweetness_level": float(self.sweetness_level),
            "acidity_level": float(self.acidity_level),
            "body_level": float(self.body_level),
            "carbonation_level": float(self.carbonation_level),
            "bitterness_level": float(self.bitterness_level),
            "aroma_level": float(self.aroma_level),
        }

    def get_retake_history(self):
        """재테스트 이력 반환"""
        return {
            "retake_count": self.retake_count,
            "last_retake_at": self.last_retake_at,
            "last_influence_rate": (
                f"{int(float(self.last_retake_influence or 0) * 100)}%" if self.last_retake_influence else "0%"
            ),
            "has_pending_retake_scores": bool(self.retake_base_scores),
        }

    def needs_analysis_update(self):
        """분석 업데이트가 필요한지 확인"""
        if not self.analysis_description:
            return True

        if not self.analysis_updated_at:
            return True

        # 점수가 업데이트된 후 분석이 업데이트되지 않았다면
        if self.last_updated > self.analysis_updated_at:
            return True

        return False

    def update_analysis(self, description):
        """분석 설명 업데이트"""
        self.analysis_description = description
        self.analysis_updated_at = timezone.now()
        self.save(update_fields=["analysis_description", "analysis_updated_at"])

    def get_evolution_status(self):
        """취향 진화 상태 반환"""
        if self.total_reviews_count < 5:
            status = "초기 학습"
            description = "기본 취향을 바탕으로 학습 중"
        elif self.total_reviews_count < 20:
            status = "진화 중"
            description = "개인 취향이 형성되고 있음"
        else:
            status = "개인화 완료"
            description = "고유한 개인 취향 프로필"

        base_influence = max(0.1, 1.0 / (1 + self.total_reviews_count * 0.15))
        personal_influence = 1.0 - base_influence

        return {
            "status": status,
            "description": description,
            "base_influence_percent": int(base_influence * 100),
            "personal_influence_percent": int(personal_influence * 100),
            "reviews_count": self.total_reviews_count,
        }
