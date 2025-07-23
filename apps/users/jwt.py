# apps/users/jwt_service.py
from rest_framework_simplejwt.tokens import RefreshToken


class JWTService:
    @staticmethod
    def create_tokens_for_user(user):
        """사용자를 위한 JWT 토큰 생성"""
        refresh = RefreshToken.for_user(user)
        return {
            "refresh_token": str(refresh),
            "access_token": str(refresh.access_token),
        }
