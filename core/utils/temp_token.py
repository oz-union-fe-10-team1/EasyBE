# core/utils/temp_token.py
from datetime import datetime, timedelta

import jwt
from django.conf import settings


class TempTokenManager:
    @staticmethod
    def create_adult_verification_token(social_id: str, provider: str, nickname: str = "") -> str:
        payload = {
            "social_id": social_id,
            "provider": provider,
            "nickname": nickname,
            "token_type": "adult_verification",
            "exp": datetime.utcnow() + timedelta(minutes=10),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    @staticmethod
    def verify_adult_verification_token(token: str):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

            if payload.get("token_type") != "adult_verification":
                return {"valid": False, "error": "잘못된 토큰 타입"}

            return {
                "valid": True,
                "social_id": payload["social_id"],
                "provider": payload["provider"],
                "nickname": payload.get("nickname", ""),
            }

        except jwt.ExpiredSignatureError:
            return {"valid": False, "error": "만료된 토큰"}
        except jwt.InvalidTokenError:
            return {"valid": False, "error": "유효하지 않은 토큰"}
