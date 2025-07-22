from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, nickname, provider, provider_id, **extra_fields):
        """
        소셜 로그인 사용자 생성
        - 소셜 플랫폼에서 받은 정보로 자동 생성
        """
        if not nickname:
            raise ValueError("닉네임은 필수입니다.")

        if not provider or not provider_id:
            raise ValueError("Provider와 Provider ID는 필수입니다.")

        # 기본 역할을 USER로 설정
        extra_fields.setdefault("role", "USER")

        # 이메일이 있다면 정규화
        email = extra_fields.get("email")
        if email:
            extra_fields["email"] = self.normalize_email(email)

        # 소셜 로그인에서 받은 정보 처리
        user = self.model(nickname=nickname, provider=provider, provider_id=provider_id, **extra_fields)
        user.set_unusable_password()  # 소셜 로그인이므로 패스워드 불필요
        user.save(using=self._db)
        return user

    def get_or_create_social_user(self, provider, provider_id, defaults=None):
        """
        소셜 로그인 시 사용자 조회 또는 생성
        - OAuth 콜백에서 사용할 헬퍼 메소드
        """
        try:
            user = self.get(provider=provider, provider_id=provider_id)
            return user, False
        except self.model.DoesNotExist:
            if defaults:
                return self.create_user(provider=provider, provider_id=provider_id, **defaults), True
            else:
                raise ValueError("새 사용자 생성을 위한 기본값이 필요합니다.")
