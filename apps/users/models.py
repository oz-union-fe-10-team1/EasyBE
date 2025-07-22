from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.users.user_manager import UserManager

# Create your models here.

class User(AbstractBaseUser, PermissionsMixin):
    class Provider(models.TextChoices):
        KAKAO = "KAKAO", "카카오"
        NAVER = "NAVER", "네이버"
        GOOGLE = "GOOGLE", "구글"

    class Role(models.TextChoices):
        USER = "USER", "사용자"
        ADMIN = "ADMIN", "관리자"

    # 소셜 로그인에서 가져올 정보
    nickname = models.CharField(max_length=20, unique=True) # 소셜에서 제공 시 저장
    email = models.EmailField(blank=True, null=True)  # 소셜에서 제공 시 저장

    # 소셜 로그인
    provider = models.CharField(max_length=10, choices=Provider.choices)
    provider_id = models.CharField(max_length=255)

    # 권한 및 상태
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER) #관리자는 장고 쉘을 이용해서 변경

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'nickname'  # Django 인증에서 사용할 필드
    REQUIRED_FIELDS = ['provider', 'provider_id']  # createsuperuser에서 요구할 필드들

    class Meta:
        db_table = "users"
        unique_together = ("provider", "provider_id")  # 유니크로 묶어서 동일한 소셜 계정 중복 방지
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['provider', 'provider_id']),
            models.Index(fields=['role']),
            models.Index(fields=['created_at']),
            models.Index(fields=['-created_at']),  # 최신순 정렬용
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
        self.save(update_fields=['role', 'updated_at'])

    def make_user(self):
        self.role = self.Role.USER
        self.save(update_fields=['role', 'updated_at'])