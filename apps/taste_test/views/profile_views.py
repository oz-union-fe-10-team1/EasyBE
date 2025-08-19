"""
사용자 프로필 관련 뷰 - 단계별 처리 과정 명시
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.controller_support import ControllerService


class UserProfileView(APIView):
    """사용자 프로필 조회"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자의 입맛 테스트 조회",
        description="로그인한 사용자의 기본 정보와 테스트 완료 여부를 조회합니다. 테스트 완료시 기본 결과 정보 포함.",
        tags=["마이페이지"],
    )
    def get(self, request):
        """사용자 프로필 조회"""
        # 1. 서비스에서 사용자 프로필 데이터 조회
        profile_data = ControllerService.get_user_profile_data(request.user)

        # 2. 응답 반환
        return Response(profile_data, status=status.HTTP_200_OK)
