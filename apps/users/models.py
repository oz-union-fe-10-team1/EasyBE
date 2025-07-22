from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.users.user_manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Provider(models.TextChoices):
        KAKAO = "KAKAO", "카카오"
        NAVER = "NAVER", "네이버"
        GOOGLE = "GOOGLE", "구글"

    class Role(models.TextChoices):
        USER = "USER", "사용자"
        ADMIN = "ADMIN", "관리자"

    # 소셜 로그인에서 가져올 정보
    nickname = models.CharField(max_length=20, unique=True, default="temp_user")  # 기본값 추가
    email = models.EmailField(blank=True, null=True)

    # 소셜 로그인
    provider = models.CharField(max_length=10, choices=Provider.choices, default=Provider.KAKAO)  # 기본값 추가
    provider_id = models.CharField(max_length=255, default="temp_id")  # 기본값 추가

    # 권한 및 상태
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "nickname"
    REQUIRED_FIELDS = ["provider", "provider_id"]

    class Meta:
        db_table = "users"
        unique_together = ("provider", "provider_id")
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["provider", "provider_id"]),
            models.Index(fields=["role"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.nickname} - {self.provider}"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_user(self):
        return self.role == self.Role.USER

    def make_admin(self):
        self.role = self.Role.ADMIN
        self.save(update_fields=["role", "updated_at"])

    def make_user(self):
        self.role = self.Role.USER
        self.save(update_fields=["role", "updated_at"])
