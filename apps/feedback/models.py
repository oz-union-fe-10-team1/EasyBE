from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.orders.models import OrderItem


class Feedback(models.Model):
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="feedback")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")

    # 맛 점수
    sweetness = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    acidity = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    body = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    # 평가
    confidence = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    overall_rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])

    # 후기 내용
    photo_url = models.URLField(max_length=2048, null=True, blank=True)
    comment = models.TextField(blank=True, verbose_name="한 줄 평")
    detailed_comment = models.TextField(blank=True, verbose_name="상세 후기")

    # JSON으로 맛 태그 저장
    selected_tags = models.JSONField(null=True, blank=True, verbose_name="선택된 맛 태그")

    # 메타데이터
    view_count = models.PositiveIntegerField(default=0, verbose_name="조회수")
    days_after_purchase = models.IntegerField(null=True, blank=True, verbose_name="구매 후 경과일")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "피드백"
        verbose_name_plural = "피드백 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.nickname}'s feedback for {self.order_item.product.name}"
