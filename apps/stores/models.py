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

    # 연락처
    contact = models.CharField(max_length=20, null=True, blank=True, help_text="연락처")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stores"
        indexes = [
            models.Index(fields=["name"]),
        ]
