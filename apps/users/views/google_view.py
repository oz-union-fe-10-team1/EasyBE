# apps/users/views/google_view.py
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.utils.jwt import JWTService
from apps.users.utils.social_auth import SocialAuthService

from ..serializers import GoogleLoginSerializer, UserSerializer
from ..social_login.google_service import GoogleService
from ..utils.cache_oauth_state import OAuthStateService


class GoogleLoginView(APIView):
    """
    구글 소셜 로그인 API
    POST /api/v1/auth/login/google/
    """

    serializer_class = GoogleLoginSerializer

    def post(self, request: Request) -> Response:
        # 0. 요청 데이터 검증
        serializer = GoogleLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        authorization_code = serializer.validated_data["code"]
        # state = serializer.validated_data["state"]

        try:
            # 1. State 검증 및 소비
            # if not OAuthStateService.verify_and_consume_state(state):
            #     return Response({"error": "Invalid or expired state"}, status=status.HTTP_400_BAD_REQUEST)

            # 2. 구글에서 access token 획득
            token_data = GoogleService.get_access_token(authorization_code)
            access_token = token_data["access_token"]

            # 3. access token으로 구글 사용자 정보 획득
            google_user_data = GoogleService.get_user_info(access_token)

            # 4. 구글 데이터 파싱
            google_id = str(google_user_data["id"])
            email = google_user_data.get("email")
            name = google_user_data.get("name", "사용자")

            # 5. 사용자 생성/조회 및 계정 통합
            user, auth_type = SocialAuthService.authenticate_social_user(
                provider="GOOGLE", provider_id=google_id, user_info={"email": email, "nickname": name}
            )

            # 6. JWT 토큰 생성
            tokens = JWTService.create_tokens_for_user(user)

            # 7. 응답 데이터 구성
            response_data = {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "user": UserSerializer(user).data,
                "auth_type": auth_type,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"로그인 처리 중 오류가 발생했습니다: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )
