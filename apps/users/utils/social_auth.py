# apps/users/utils/social_auth.py

import random
from typing import Any, Dict, Optional, Tuple

from django.db import transaction

from apps.users.models import SocialAccount, User


class SocialAuthService:
    @staticmethod
    @transaction.atomic
    def authenticate_social_user(
        provider: str, provider_id: str, user_info: Dict[str, Any]
    ) -> Tuple[Optional[User], str]:
        """
        소셜 로그인 인증 + 성인 인증 확인
        """
        email = user_info.get("email")
        nickname = user_info.get("nickname")

        # 1. 기존 소셜 계정 확인
        try:
            social_account = SocialAccount.objects.get(provider=provider, provider_id=provider_id)
            user = social_account.user

            # 성인 인증 여부 확인
            if user.is_adult:
                return user, "existing_verified"
            else:
                return user, "existing_need_adult_verification"

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

            if existing_user.is_adult:
                return existing_user, "linked_verified"
            else:
                return existing_user, "linked_need_adult_verification"

        # 3-2. 새 사용자 - 무조건 성인 인증 필요
        return None, "new_user_need_adult_verification"

    @staticmethod
    @transaction.atomic
    def complete_adult_verification(provider: str, provider_id: str, user_info: Dict[str, Any]) -> User:
        """
        성인 인증 완료 후 계정 생성/업데이트
        """
        email = user_info.get("email")
        nickname = user_info.get("nickname")

        # 1. 기존 소셜 계정이 있는지 확인
        try:
            social_account = SocialAccount.objects.get(provider=provider, provider_id=provider_id)
            user = social_account.user

            # 성인 인증 완료 처리 (이미 구현된 메서드 사용)
            user.verify_adult()

            return user

        except SocialAccount.DoesNotExist:
            pass

        # 2. 동일 이메일 기존 사용자 확인
        existing_user = None
        if email:
            existing_user = User.objects.get_by_email(email)

        if existing_user:
            # 기존 사용자에 소셜 계정 연결 + 성인 인증
            social_account = SocialAccount.objects.create(
                user=existing_user, provider=provider, provider_id=provider_id, provider_email=email
            )
            existing_user.verify_adult()

            return existing_user

        # 3. 새 사용자 생성
        unique_nickname = SocialAuthService.generate_unique_nickname(nickname)

        user = User.objects.create_user(nickname=unique_nickname, email=email)

        # 성인 인증 완료 처리
        user.verify_adult()

        SocialAccount.objects.create(user=user, provider=provider, provider_id=provider_id, provider_email=email)

        return user

    @staticmethod
    def create_adult_verification_token(provider: str, provider_id: str, nickname: str = "") -> str:
        """성인 인증용 임시 토큰 생성"""
        from core.utils.temp_token import TempTokenManager

        return TempTokenManager.create_adult_verification_token(
            social_id=provider_id, provider=provider, nickname=nickname
        )

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
