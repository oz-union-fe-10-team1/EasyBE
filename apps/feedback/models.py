from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.orders.models import OrderItem


class Feedback(models.Model):
    # 어떤 주문 상품에 대한 피드백인지 명확히 연결 (1:1 관계)
    order_item = models.OneToOneField(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="feedback",
        verbose_name="주문 상품",
    )
    # 피드백 작성자 (주문 상품에서 자동으로 가져옴)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        verbose_name="작성자",
    )

    # 점수 필드
    sweetness = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="단맛 점수")
    acidity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="산미 점수")
    body = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="바디감 점수")
    confidence = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], verbose_name="입맛 신뢰도 (%)")
    overall_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="전체 평점")

    # 선택 사항 필드
    photo_url = models.URLField(max_length=2048, null=True, blank=True, verbose_name="시음 사진 URL")
    comment = models.TextField(blank=True, verbose_name="시음 한 줄 평")
    detailed_comment = models.TextField(blank=True, verbose_name="상세 후기")
    taste_tags = models.CharField(max_length=255, blank=True, verbose_name="맛 태그", help_text="쉼표로 구분된 문자열 (예: 단맛,과일향)")

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "피드백"
        verbose_name_plural = "피드백 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.nickname}'s feedback for {self.order_item.product.name}"