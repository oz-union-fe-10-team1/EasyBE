from datetime import date

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, nickname, provider, provider_id, **extra_fields):
        """
                소셜 로그인 사용자 생성
                - 소셜 플랫폼에서 받은 정보로 자동 생성
        """
        if not nickname:
            raise ValueError('닉네임은 필수입니다.')

        if not provider or not provider_id:
            raise ValueError('Provider와 Provider ID는 필수입니다.')

        # 소셜 로그인에서 받은 정보 처리
        user = self.model(
            nickname=nickname,
            provider=provider,
            provider_id=provider_id,
            **extra_fields
        )
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname, **extra_fields):
        """
                관리자 계정 생성 (소셜 로그인 없이)
        """
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('provider', 'ADMIN')
        extra_fields.setdefault('provider_id', f'admin_{nickname}')
        extra_fields.setdefault('name', nickname)

        if not extra_fields.get('is_admin'):
            raise ValueError('Superuser는 is_admin=True여야 합니다.')

        return self.create_user(**extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Provider(models.TextChoices):
        KAKAO = "KAKAO", "카카오"
        NAVER = "NAVER", "네이버"
        GOOGLE = "GOOGLE", "구글"
        ADMIN = "ADMIN", "관리자"  # 관리자 계정용

    class Gender(models.TextChoices):
        MALE = "MALE", "남성"
        FEMALE = "FEMALE", "여성"

    # 소셜 로그인에서 가져올 정보
    name = models.CharField(max_length=30) # 소셜에서 제공 시 저장
    nickname = models.CharField(max_length=10, unique=True) # 소셜에서 제공 시 저장
    email = models.EmailField(blank=True, null=True)  # 소셜에서 제공 시 저장

    # 필수 정보 (추후 마이페이지 등 에서 입력)
    phone_number = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=6, choices=Gender.choices, default=Gender.MALE)
    birthday = models.DateField(default=date(2000, 1, 1))

    # 소셜 로그인
    provider = models.CharField(max_length=10, choices=Provider.choices)
    provider_id = models.CharField(max_length=255)

    # 권한 및 상태
    is_admin = models.BooleanField(default=False)  # 관리자 여부
    is_active = models.BooleanField(default=True)
    is_adult_verified = models.BooleanField(default=False) # 성인 여부

    # 플랫폼 특화
    taste_test_completed = models.BooleanField(default=False)
    is_marketing_agreed = models.BooleanField(default=False)

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    class Meta:
        db_table = "users"
        unique_together = ("provider", "provider_id")  # 유니크로 묶어서 동일한 소셜 계정 중복 방지

        def __str__(self) -> str:
            return f"{self.nickname} - {self.provider}"

        def has_completed_profile(self):
            """프로필 완성 여부 확인"""
            return all([self.nickname, self.phone_number])

        @property
        def is_staff(self):
            """Django admin 접근 권한"""
            return self.is_admin