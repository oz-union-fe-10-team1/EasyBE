from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Feedback(models.Model):
    """상품 피드백/리뷰"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feedbacks")
    order_item = models.OneToOneField(
        "orders.OrderItem", on_delete=models.CASCADE, related_name="feedback", help_text="피드백을 작성한 주문 아이템"
    )

    # 평점 및 신뢰도
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], help_text="평점 (1-5점)"
    )
    confidence = models.PositiveIntegerField(
        default=50,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="신뢰도 (0-100%) - 사용자가 자신의 입맛 정확도를 설정",
    )

    # 텍스트 피드백
    comment = models.TextField(null=True, blank=True, help_text="상세 피드백 내용")

    # TODO: 이미지 피드백 (나중에 추가 가능) 태그, 구매인증등 검토 필요 피드백 커멘트 쪽도 한줄평 등 두가지가 필요할 수 있음.
    # 맛/느낌 태그들
    selected_tags = models.JSONField(
        null=True, blank=True, help_text="선택한 맛/느낌 태그들 (예: ['달콤해요', '목넘김이 좋아요', '향이 좋아요'])"
    )

    # 구매 인증
    verified_purchase = models.BooleanField(default=True, help_text="구매 인증 여부")

    # 조회 관련
    view_count = models.PositiveIntegerField(default=0, help_text="피드백 조회수")
    last_viewed_at = models.DateTimeField(null=True, blank=True, help_text="마지막 조회 일시")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "feedbacks"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["rating"]),
            models.Index(fields=["order_item"]),
            models.Index(fields=["rating", "created_at"]),
            models.Index(fields=["user", "rating"]),
            models.Index(fields=["created_at", "view_count"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.order_item.product.name} ({self.rating}점)"

    @property
    def product(self):
        """피드백 대상 상품"""
        return self.order_item.product

    @property
    def drink(self):
        """피드백 대상 술 (개별 상품인 경우만)"""
        return self.order_item.product.drink if self.order_item.product.drink else None

    def increment_view_count(self):
        """조회수 증가"""
        from django.utils import timezone

        self.view_count += 1
        self.last_viewed_at = timezone.now()
        self.save(update_fields=["view_count", "last_viewed_at"])

    def get_helpful_score(self):
        """도움이 된 점수 (나중에 추가 가능)"""
        # 추후 FeedbackHelpful 모델과 연계
        return 0

    def is_high_confidence(self):
        """높은 신뢰도 피드백인지 확인 (80% 이상)"""
        return self.confidence >= 80

    def get_display_tags(self):
        """태그들을 문자열로 반환"""
        if self.selected_tags:
            return ", ".join(self.selected_tags)
        return ""

    def save(self, *args, **kwargs):
        # 피드백 작성 시 상품의 리뷰 수 업데이트
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # 상품의 review_count 증가
            product = self.order_item.product
            product.review_count += 1
            product.save(update_fields=["review_count"])

            # 사용자의 취향 프로필 업데이트 (개별 술 상품인 경우만)
            if self.drink and hasattr(self.user, "taste_profile"):
                self.user.taste_profile.update_from_review(self, self.drink)

    def delete(self, *args, **kwargs):
        # 피드백 삭제 시 상품의 리뷰 수 감소
        product = self.order_item.product
        product.review_count -= 1
        product.save(update_fields=["review_count"])

        super().delete(*args, **kwargs)
