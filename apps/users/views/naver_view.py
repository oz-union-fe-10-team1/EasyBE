# apps/users/views/naver_view.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.utils.jwt import JWTService
from apps.users.utils.social_auth import SocialAuthService

from ..serializers import NaverLoginSerializer, UserSerializer
from ..social_login.naver_service import NaverService
from ..utils.cache_oauth_state import OAuthStateService


class NaverLoginView(APIView):
    """
    네이버 소셜 로그인 API
    POST /api/v1/auth/login/naver/
    """

    serializer_class = NaverLoginSerializer

    def post(self, request):
        # 0. 요청 데이터 검증
        serializer = NaverLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        authorization_code = serializer.validated_data["code"]
        state = serializer.validated_data["state"]

        try:
            # 1. 네이버에서 access token 획득
            token_data = NaverService.get_access_token(authorization_code, state)
            access_token = token_data["access_token"]

            # 2. access token으로 네이버 사용자 정보 획득
            naver_user_data = NaverService.get_user_info(access_token)

            # 3. 네이버 데이터 파싱
            if naver_user_data.get("resultcode") != "00":
                raise Exception(f"네이버 사용자 정보 조회 실패: {naver_user_data.get('message')}")

            response_data = naver_user_data.get("response", {})
            naver_id = response_data.get("id")
            email = response_data.get("email")

            if not naver_id:
                raise Exception("네이버 ID를 가져올 수 없습니다.")

            # 4. 사용자 인증 및 성인 인증 상태 확인
            user, auth_status = SocialAuthService.authenticate_social_user(
                provider="NAVER", provider_id=naver_id, user_info={"email": email}
            )

            # 5. 성인 인증 여부에 따른 분기 처리
            if auth_status in ["existing_verified", "linked_verified"]:
                # 성인 인증 완료 → 바로 로그인
                tokens = JWTService.create_tokens_for_user(user)

                return Response(
                    {
                        "success": True,
                        "access": tokens["access_token"],
                        "refresh": tokens["refresh_token"],
                        "user_info": UserSerializer(user).data,
                        "auth_type": auth_status,
                    },
                    status=status.HTTP_200_OK,
                )

            else:
                # 성인 인증 필요 → 임시 토큰 발급
                temp_token = SocialAuthService.create_adult_verification_token(provider="NAVER", provider_id=naver_id)

                return Response(
                    {
                        "success": True,
                        "status": "adult_verification_required",
                        "temp_token": temp_token,
                        "message": "성인 인증이 필요합니다.",
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"error": f"로그인 처리 중 오류가 발생했습니다: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST
            )
