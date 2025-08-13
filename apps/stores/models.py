from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Store(models.Model):
    """매장 정보"""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "정상 운영"
        TEMPORARY_CLOSED = "TEMPORARY_CLOSED", "임시 휴업"
        PERMANENTLY_CLOSED = "PERMANENTLY_CLOSED", "폐점"
        MAINTENANCE = "MAINTENANCE", "정비 중"

    name = models.CharField(max_length=100, help_text="매장명")
    address = models.TextField(help_text="매장 주소")

    # 위치 정보 (GPS 좌표)
    latitude = models.DecimalField(
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text="위도",
    )
    longitude = models.DecimalField(
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text="경도",
    )

    # 연락처
    contact = models.CharField(max_length=20, null=True, blank=True, help_text="연락처")

    # 운영 시간 관련
    opening_days = models.CharField(max_length=255, null=True, blank=True, help_text="운영 요일 (예: 월-일)")
    opening_hours = models.JSONField(
        null=True, blank=True, help_text="요일별 운영시간 (예: {'monday': '09:00-18:00', 'tuesday': '09:00-18:00'})")
    closed_days = models.JSONField(
        null=True,
        blank=True,
        help_text="휴무일 정보 (예: ['2024-01-01', '2024-12-25'] 또는 {'regular': ['sunday'], 'special': ['2024-01-01']})",
    )

    # 매장 특성
    has_tasting = models.BooleanField(default=True, help_text="시음 가능 여부")
    has_parking = models.BooleanField(default=False, help_text="주차 가능 여부")

    # 매장 이미지
    image = models.URLField(max_length=255, null=True, blank=True, help_text="매장 대표 이미지")

    # 매장 상태
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, help_text="매장 운영 상태")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["status"]),
            models.Index(fields=["latitude", "longitude"]),  # 위치 기반 검색용
            models.Index(fields=["has_tasting"]),
            models.Index(fields=["has_parking"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    @property
    def is_open(self):
        """현재 운영 중인지 확인"""
        return self.status == self.Status.ACTIVE

    def close_temporarily(self, reason=None):
        """임시 휴업 처리"""
        self.status = self.Status.TEMPORARY_CLOSED
        self.save(update_fields=["status", "updated_at"])

    def reopen(self):
        """재개장 처리"""
        self.status = self.Status.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def close_permanently(self):
        """폐점 처리"""
        self.status = self.Status.PERMANENTLY_CLOSED
        self.save(update_fields=["status", "updated_at"])


class StoreLike(models.Model):
    """매장 좋아요"""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="liked_stores")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "store_likes"
        unique_together = ("user", "store")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["store"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.store.name}"