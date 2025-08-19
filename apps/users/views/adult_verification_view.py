# apps/users/views/adult_verification_view.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.serializers import UserSerializer
from apps.users.utils.social_auth import SocialAuthService
from core.utils.temp_token import TempTokenManager


class CompleteAdultVerificationView(APIView):
    """성인 인증 완료 처리"""

    def post(self, request):
        # 1. 요청 데이터 검증
        temp_token = request.data.get("temp_token")
        if not temp_token:
            return Response({"error": "임시 토큰이 필요합니다."}, status=400)

        # 2. 토큰 검증
        token_data = TempTokenManager.verify_adult_verification_token(temp_token)
        if not token_data["valid"]:
            return Response({"error": token_data["error"]}, status=400)

        # 3. 성인 인증 완료 처리
        user = SocialAuthService.complete_adult_verification(
            provider=token_data["provider"],
            provider_id=token_data["social_id"],
            user_info={"nickname": token_data["nickname"]},
        )

        # 4. JWT 토큰 발급
        refresh = RefreshToken.for_user(user)

        # 5. 응답 반환
        return Response(
            {
                "success": True,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user_info": UserSerializer(user).data,
            }
        )
