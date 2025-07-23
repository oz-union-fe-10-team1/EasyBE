# apps/users/social_login/kakao_service.py
from typing import Any, Dict

import requests
from django.conf import settings


class KakaoService:
    @staticmethod
    def get_access_token(authorization_code: str) -> Dict[str, Any]:
        """
        1단계: authorization code로 access token 요청
        """
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.KAKAO_CLIENT_ID,
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
            "code": authorization_code,
        }

        response = requests.post(url, data=data)

        if response.status_code != 200:
            raise Exception(f"카카오 토큰 요청 실패: {response.text}")

        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        2단계: access token으로 사용자 정보 요청
        """
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }

        response = requests.post(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"카카오 사용자 정보 요청 실패: {response.text}")

        return response.json()
