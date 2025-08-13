from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

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
    """사용자 취향 프로필 (리뷰 기반 단순 평균)"""

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

    def update_from_review(self, drink):
        """리뷰를 바탕으로 취향 점수 업데이트 (단순 평균)"""
        from decimal import Decimal

        count = self.total_reviews_count

        # 단순 평균 계산
        self.sweetness_level = (self.sweetness_level * count + drink.sweetness_level) / (count + 1)
        self.acidity_level = (self.acidity_level * count + drink.acidity_level) / (count + 1)
        self.body_level = (self.body_level * count + drink.body_level) / (count + 1)
        self.carbonation_level = (self.carbonation_level * count + drink.carbonation_level) / (count + 1)
        self.bitterness_level = (self.bitterness_level * count + drink.bitterness_level) / (count + 1)
        self.aroma_level = (self.aroma_level * count + drink.aroma_level) / (count + 1)

        self.total_reviews_count += 1
        self.save()

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
        from django.utils import timezone

        self.analysis_description = description
        self.analysis_updated_at = timezone.now()
        self.save(update_fields=["analysis_description", "analysis_updated_at"])
