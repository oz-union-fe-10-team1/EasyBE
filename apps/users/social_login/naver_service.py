# apps/users/social_login/naver_service.py
from typing import Any, Dict

import requests
from django.conf import settings


class NaverService:
    @staticmethod
    def get_access_token(authorization_code: str, state: str) -> Dict[str, Any]:
        """
        1단계: authorization code로 access token 요청
        """
        url = "https://nid.naver.com/oauth2.0/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.NAVER_CLIENT_ID,
            "client_secret": settings.NAVER_CLIENT_SECRET,
            "redirect_uri": settings.NAVER_REDIRECT_URI,
            "code": authorization_code,
            "state": state,
        }

        response = requests.post(url, data=data)

        if response.status_code != 200:
            raise Exception(f"네이버 토큰 요청 실패: {response.text}")

        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        2단계: access token으로 사용자 정보 요청
        """
        url = "https://openapi.naver.com/v1/nid/me"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"네이버 사용자 정보 요청 실패: {response.text}")

        return response.json()
