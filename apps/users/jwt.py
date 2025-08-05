# apps/users/jwt_service.py
from typing import Dict

from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class JWTService:
    @staticmethod
    def create_tokens_for_user(user: User) -> Dict[str, str]:
        """사용자를 위한 JWT 토큰 생성"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }
