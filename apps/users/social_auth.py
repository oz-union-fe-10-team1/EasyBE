# apps/users/services.py
import random
from typing import Any, Dict, Tuple

from django.db import transaction

from .models import SocialAccount, User


class SocialAuthService:
    @staticmethod
    @transaction.atomic
    def authenticate_social_user(provider: str, provider_id: str, user_info: Dict[str, Any]) -> Tuple[User, str]:
        """
        소셜 로그인 인증 + 계정 통합 처리
        """
        email = user_info.get("email")
        nickname = user_info.get("nickname")

        # 1. 기존 소셜 계정 확인
        try:
            social_account = SocialAccount.objects.get(provider=provider, provider_id=provider_id)
            return social_account.user, "existing_social"
        except SocialAccount.DoesNotExist:
            pass

        # 2. 동일한 이메일의 기존 사용자 확인
        existing_user = None
        if email:
            existing_user = User.objects.get_by_email(email)

        # 3-1. 기존 사용자가 있다면 새 소셜 계정 연결
        if existing_user:
            social_account = SocialAccount.objects.create(
                user=existing_user, provider=provider, provider_id=provider_id, provider_email=email
            )
            return existing_user, "linked_to_existing"

        # 3-2. 새 사용자 + 소셜 계정 생성
        unique_nickname = SocialAuthService.generate_unique_nickname(nickname)

        user = User.objects.create_user(nickname=unique_nickname, email=email)

        social_account = SocialAccount.objects.create(
            user=user, provider=provider, provider_id=provider_id, provider_email=email
        )

        return user, "new_user"

    @staticmethod
    def generate_unique_nickname(base_nickname):
        """유니크한 닉네임 생성"""
        if not base_nickname:
            base_nickname = "사용자"

        # 원본 닉네임이 사용 가능한지 확인
        if not User.objects.filter(nickname=base_nickname).exists():
            return base_nickname

        # 숫자를 붙여서 유니크한 닉네임 생성
        for i in range(1, 1000):
            candidate = f"{base_nickname}{i}"
            if not User.objects.filter(nickname=candidate).exists():
                return candidate

        # 최후의 수단 (랜덤 숫자)
        return f"{base_nickname}{random.randint(1000, 9999)}"

    @staticmethod
    def link_social_account(user, provider, provider_id, provider_email=None):
        """
        기존 사용자에게 소셜 계정 연결
        """
        # 이미 연결된 소셜 계정인지 확인
        if SocialAccount.objects.filter(provider=provider, provider_id=provider_id).exists():
            raise ValueError("이미 다른 계정에 연결된 소셜 계정입니다.")

        social_account = SocialAccount.objects.create(
            user=user, provider=provider, provider_id=provider_id, provider_email=provider_email
        )

        return social_account
