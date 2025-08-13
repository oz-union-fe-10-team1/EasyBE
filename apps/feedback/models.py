# apps/feedback/models.py

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

# 태그 선택지 정의
TASTE_TAG_CHOICES = [
    ("과일향", "과일향"),
    ("달콤한", "달콤한"),
    ("산뜻한", "산뜻한"),
    ("청량한", "청량한"),
    ("고소한", "고소한"),
    ("부드러운", "부드러운"),
    ("톡쏘는", "톡쏘는"),
    ("달링한", "달링한"),
    ("독치한", "독치한"),
    ("드라이", "드라이"),
    ("시무한", "시무한"),
    ("누룩향", "누룩향"),
]


class FeedbackQuerySet(models.QuerySet):
    """피드백 QuerySet"""

    def high_rated(self):
        """높은 평점 리뷰들 (4점 이상)"""
        return self.filter(rating__gte=4)

    def with_taste_profile(self):
        """취향 평가가 있는 리뷰들"""
        return self.filter(
            models.Q(sweetness__isnull=False) | models.Q(acidity__isnull=False) | models.Q(body__isnull=False)
        )

    def recent(self, days=7):
        """최근 N일 내 리뷰들"""
        from datetime import timedelta

        from django.utils import timezone

        since = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=since)

    def popular(self):
        """인기 리뷰들 (조회수 기준)"""
        return self.order_by("-view_count", "-created_at")

    def personalized_for_user(self, user):
        """사용자 취향과 비슷한 리뷰들"""
        if hasattr(user, "taste_profile"):
            # TODO: 취향 프로필 기반 필터링 로직
            return self.high_rated().order_by("-created_at")
        return self.high_rated().order_by("-created_at")


class FeedbackManager(models.Manager):
    """피드백 Manager"""

    def get_queryset(self):
        return FeedbackQuerySet(self.model, using=self._db)

    def high_rated(self):
        return self.get_queryset().high_rated()

    def with_taste_profile(self):
        return self.get_queryset().with_taste_profile()

    def recent(self, days=7):
        return self.get_queryset().recent(days)

    def popular(self):
        return self.get_queryset().popular()

    def personalized_for_user(self, user):
        return self.get_queryset().personalized_for_user(user)


class Feedback(models.Model):
    """상품 피드백/리뷰"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    order_item = models.OneToOneField(
        "orders.OrderItem", on_delete=models.CASCADE, related_name="feedback", help_text="피드백을 작성한 주문 아이템"
    )

    # 종합 평점 (별점 1-5)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="종합 평점 (1-5점)"
    )

    # 세부 취향 평가 (0.0-5.0)
    sweetness = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
        help_text="단맛 평가 (0.0-5.0)",
    )
    acidity = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
        help_text="산미 평가 (0.0-5.0)",
    )
    body = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
        help_text="바디감 평가 (0.0-5.0)",
    )
    carbonation = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
        help_text="탄산감 평가 (0.0-5.0)",
    )
    bitterness = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
        help_text="쓴맛 평가 (0.0-5.0)",
    )
    aroma = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
        help_text="풍미 평가 (0.0-5.0)",
    )

    # 신뢰도
    confidence = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="신뢰도 (0-100%) - 사용자가 자신의 입맛 정확도를 설정",
    )

    # 텍스트 피드백
    comment = models.TextField(null=True, blank=True, help_text="상세 피드백 내용")

    # 맛/느낌 태그들
    selected_tags = models.JSONField(
        null=True, blank=True, help_text="선택한 맛/느낌 태그들 (예: ['과일향', '달콤한', '부드러운'])"
    )

    # 조회 관련
    view_count = models.PositiveIntegerField(default=0, help_text="피드백 조회수")
    last_viewed_at = models.DateTimeField(null=True, blank=True, help_text="마지막 조회 일시")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Manager 설정
    objects = FeedbackManager()

    class Meta:
        db_table = "feedbacks"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["order_item"]),
            models.Index(fields=["rating", "created_at"]),
            models.Index(fields=["sweetness", "acidity", "body"]),
            models.Index(fields=["carbonation", "bitterness", "aroma"]),
            models.Index(fields=["view_count"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.order_item.product.name} ({self.rating}점)"

    @property
    def product(self):
        """피드백 대상 상품"""
        return self.order_item.product

    @property
    def masked_username(self):
        """사용자명 마스킹 처리 (abc**** 형태)"""
        username = self.user.nickname or self.user.username
        if len(username) <= 3:
            return username[0] + "*" * (len(username) - 1)
        return username[:3] + "*" * (len(username) - 3)

    def increment_view_count(self):
        """조회수 증가"""
        from django.utils import timezone

        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=["view_count", "last_viewed_at"])

    def clean(self):
        """태그 검증"""
        if self.selected_tags:
            valid_tags = [choice[0] for choice in TASTE_TAG_CHOICES]
            invalid_tags = [tag for tag in self.selected_tags if tag not in valid_tags]
            if invalid_tags:
                from django.core.exceptions import ValidationError

                raise ValidationError(f"허용되지 않은 태그: {invalid_tags}")

    def save(self, *args, **kwargs):
        """피드백 저장 시 상품 통계 업데이트"""
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # 상품의 review_count 증가
            product = self.order_item.product
            product.review_count += 1
            product.save(update_fields=["review_count"])

    def delete(self, *args, **kwargs):
        """피드백 삭제 시 상품의 리뷰 수 감소"""
        product = self.order_item.product
        product.review_count -= 1
        product.save(update_fields=["review_count"])

        super().delete(*args, **kwargs)
