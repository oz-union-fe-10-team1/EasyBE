from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.users.user_manager import UserManager
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
    """사용자 취향 프로필 (리뷰 기반 이동평균)"""

    user = models.OneToOneField(base.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="taste_profile")

    # 맛 프로필 점수 (0.0 ~ 5.0) - Drink 모델과 동일한 구조
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

    # 이동평균 계산을 위한 메타데이터
    total_reviews_count = models.PositiveIntegerField(default=0, help_text="반영된 총 리뷰 수")
    is_initialized = models.BooleanField(default=False, help_text="취향 테스트로 초기화 완료 여부")

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
        """취향 테스트 결과로 초기값 설정 (한 번만 가능)"""
        if self.is_initialized:
            raise ValueError("취향 프로필은 이미 초기화되었습니다. 다시 설정할 수 없습니다.")

        # 취향 유형별 초기 점수 매핑
        taste_mapping = {
            "SWEET_FRUIT": {
                "sweetness_level": 4.5,
                "acidity_level": 3.5,
                "body_level": 2.0,
                "carbonation_level": 2.0,
                "bitterness_level": 1.0,
                "aroma_level": 4.0,
            },
            "FRESH_FIZZY": {
                "sweetness_level": 2.0,
                "acidity_level": 4.5,
                "body_level": 2.0,
                "carbonation_level": 4.5,
                "bitterness_level": 1.5,
                "aroma_level": 3.0,
            },
            "HEAVY_LINGERING": {
                "sweetness_level": 2.5,
                "acidity_level": 2.0,
                "body_level": 4.5,
                "carbonation_level": 1.0,
                "bitterness_level": 3.5,
                "aroma_level": 4.0,
            },
            "CLEAN_SAVORY": {
                "sweetness_level": 1.5,
                "acidity_level": 2.0,
                "body_level": 3.0,
                "carbonation_level": 2.5,
                "bitterness_level": 2.0,
                "aroma_level": 2.5,
            },
            "FRAGRANT_NEAT": {
                "sweetness_level": 2.0,
                "acidity_level": 2.5,
                "body_level": 2.5,
                "carbonation_level": 2.0,
                "bitterness_level": 1.5,
                "aroma_level": 4.5,
            },
            "FRESH_CLEAN": {
                "sweetness_level": 2.0,
                "acidity_level": 4.0,
                "body_level": 2.0,
                "carbonation_level": 3.0,
                "bitterness_level": 1.5,
                "aroma_level": 3.0,
            },
            "HEAVY_SWEET": {
                "sweetness_level": 4.5,
                "acidity_level": 2.0,
                "body_level": 4.0,
                "carbonation_level": 1.5,
                "bitterness_level": 2.0,
                "aroma_level": 3.5,
            },
            "SWEET_SAVORY": {
                "sweetness_level": 4.0,
                "acidity_level": 2.0,
                "body_level": 3.5,
                "carbonation_level": 2.0,
                "bitterness_level": 2.5,
                "aroma_level": 3.0,
            },
            "GOURMET": {
                "sweetness_level": 3.0,
                "acidity_level": 3.0,
                "body_level": 3.5,
                "carbonation_level": 2.5,
                "bitterness_level": 3.0,
                "aroma_level": 4.0,
            },
        }

        initial_scores = taste_mapping.get(test_result.prefer_taste, {})
        for field, score in initial_scores.items():
            setattr(self, field, score)

        self.is_initialized = True
        self.save()

    def update_from_review(self, review, drink):
        """리뷰를 바탕으로 취향 점수 업데이트 (가중 이동평균)"""
        from decimal import Decimal

        # 리뷰 평점에 따른 가중치 (5점 만점 기준)
        # 평점이 높을수록 해당 술의 맛 프로필을 더 선호한다고 판단
        rating_weight = Decimal(str(review.rating)) / Decimal("5.0")

        # 최근성 가중치 (최근 리뷰일수록 높은 가중치)
        recency_weight = Decimal("1.0")  # 추후 구현 가능

        # 최종 가중치
        final_weight = rating_weight * recency_weight

        # 현재 점수와 새로운 점수의 가중 평균
        # 기존 가중치는 리뷰 수에 비례, 새로운 가중치는 final_weight
        current_weight = Decimal(str(self.total_reviews_count))
        total_weight = current_weight + final_weight

        if total_weight > 0:
            # 각 맛 지표별로 업데이트
            self.sweetness_level = (
                self.sweetness_level * current_weight + drink.sweetness_level * final_weight
            ) / total_weight
            self.acidity_level = (
                self.acidity_level * current_weight + drink.acidity_level * final_weight
            ) / total_weight
            self.body_level = (self.body_level * current_weight + drink.body_level * final_weight) / total_weight
            self.carbonation_level = (
                self.carbonation_level * current_weight + drink.carbonation_level * final_weight
            ) / total_weight
            self.bitterness_level = (
                self.bitterness_level * current_weight + drink.bitterness_level * final_weight
            ) / total_weight
            self.aroma_level = (self.aroma_level * current_weight + drink.aroma_level * final_weight) / total_weight

        self.total_reviews_count += 1
        self.save()

    def get_taste_similarity(self, drink):
        """특정 술과의 취향 유사도 계산 (0.0 ~ 1.0)"""
        import math
        from decimal import Decimal

        # 각 맛 지표별 차이 계산
        differences = [
            abs(self.sweetness_level - drink.sweetness_level),
            abs(self.acidity_level - drink.acidity_level),
            abs(self.body_level - drink.body_level),
            abs(self.carbonation_level - drink.carbonation_level),
            abs(self.bitterness_level - drink.bitterness_level),
            abs(self.aroma_level - drink.aroma_level),
        ]

        # 유클리드 거리 계산
        distance = math.sqrt(sum(float(d) ** 2 for d in differences))

        # 최대 가능 거리 (모든 지표가 최대 차이날 때)
        max_distance = math.sqrt(6 * (5.0**2))

        # 유사도 (거리가 클수록 유사도 낮음)
        similarity = 1.0 - (distance / max_distance)
        return max(0.0, min(1.0, similarity))

    # def get_recommended_drinks(self, limit=10):
    #     """취향에 맞는 술 추천 (나중에 구현)"""
    #     pass
