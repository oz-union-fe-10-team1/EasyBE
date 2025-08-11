from typing import TYPE_CHECKING, Any, Optional

from django.contrib.auth.models import BaseUserManager

if TYPE_CHECKING:
    from apps.users.models import SocialAccount, User


class UserManager(BaseUserManager["User"]):
    def create_user(self, nickname: str, email: Optional[str] = None, **extra_fields: Any):
        """
        기본 사용자 생성 (소셜 계정 정보는 별도 처리)
        """
        if not nickname:
            raise ValueError("닉네임은 필수입니다.")

        # 기본 역할을 USER로 설정
        extra_fields.setdefault("role", "USER")

        # 이메일이 있다면 정규화
        if email:
            extra_fields["email"] = self.normalize_email(email)

        user_fields = {"nickname": nickname, "email": email, "role": extra_fields.get("role", "USER")}

        # 소셜 로그인에서 받은 정보 처리
        user = self.model(**user_fields)
        user.set_unusable_password()  # 소셜 로그인이므로 패스워드 불필요
        user.save(using=self._db)
        return user

    def create_superuser(self, nickname: str, email: Optional[str] = None, **extra_fields: Any):
        """
        슈퍼유저 생성 (Django admin용)
        """
        user = self.create_user(nickname=nickname, email=email, role="ADMIN")

        # PermissionsMixin 필드들은 User 인스턴스 생성 후 설정
        user.is_superuser = True
        user.save(update_fields=["is_superuser"])

        return user

    def get_by_social_account(self, provider: str, provider_id: str):
        """
        소셜 계정으로 사용자 조회
        """
        from .models import SocialAccount  # 순환 임포트 방지

        try:
            social_account = SocialAccount.objects.get(provider=provider, provider_id=provider_id)
            return social_account.user
        except SocialAccount.DoesNotExist:
            return None

    def get_by_email(self, email: str):
        """
        이메일로 사용자 조회
        """
        try:
            return self.get(email=email)
        except self.model.DoesNotExist:
            return None
