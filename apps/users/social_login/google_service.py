# apps/users/social_login/google_service.py
from typing import Any, Dict

import requests
from django.conf import settings


class GoogleService:
    @staticmethod
    def get_access_token(authorization_code: str) -> Dict[str, Any]:
        """
        1단계: authorization code로 access token 요청
        """
        url = "https://oauth2.googleapis.com/token"
        # TODO : authorization_code 받을 때 인코딩 된 '/'(%2F) 디코딩해서 구글에 보내줘야함
        data = {
            "grant_type": "authorization_code",
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "code": authorization_code,
        }

        response = requests.post(url, data=data)

        if response.status_code != 200:
            raise Exception(f"구글 토큰 요청 실패: {response.text}")

        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        2단계: access token으로 사용자 정보 요청
        """
        url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"구글 사용자 정보 요청 실패: {response.text}")

        return response.json()
