# apps/users/views/kakao_view.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.utils.jwt import JWTService
from apps.users.utils.social_auth import SocialAuthService

from ..serializers import KakaoLoginSerializer, UserSerializer
from ..social_login.kakao_service import KakaoService
from ..utils.cache_oauth_state import OAuthStateService


class KakaoLoginView(APIView):
    """
    카카오 소셜 로그인 API
    POST /api/v1/auth/login/kakao/
    """

    serializer_class = KakaoLoginSerializer

    def post(self, request):
        # 0. 요청 데이터 검증
        serializer = KakaoLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        authorization_code = serializer.validated_data["code"]

        try:
            # 1. 카카오에서 access token 획득
            token_data = KakaoService.get_access_token(authorization_code)
            access_token = token_data["access_token"]

            # 2. access token으로 카카오 사용자 정보 획득
            kakao_user_data = KakaoService.get_user_info(access_token)

            # 3. 카카오 데이터 파싱
            kakao_id = str(kakao_user_data["id"])
            email = kakao_user_data.get("kakao_account", {}).get("email")
            nickname = kakao_user_data.get("kakao_account", {}).get("profile", {}).get("nickname", "사용자")

            # 4. 사용자 인증 및 성인 인증 상태 확인
            user, auth_status = SocialAuthService.authenticate_social_user(
                provider="KAKAO", provider_id=kakao_id, user_info={"email": email, "nickname": nickname}
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
                temp_token = SocialAuthService.create_adult_verification_token(
                    provider="KAKAO", provider_id=kakao_id, nickname=nickname
                )

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
