from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.users.user_manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        USER = "USER", "사용자"
        ADMIN = "ADMIN", "관리자"

    # 기본 정보만 유지
    nickname = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)  # 주 이메일
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
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
