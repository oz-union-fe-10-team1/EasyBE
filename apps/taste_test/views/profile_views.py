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
        summary="사용자 프로필",
        description="로그인한 사용자의 기본 정보와 테스트 완료 여부를 조회합니다. 테스트 완료시 기본 결과 정보 포함.",
        responses={
            200: {
                "description": "사용자 프로필",
                "example": {
                    "user": "사용자닉네임",
                    "has_test": True,
                    "id": 1,
                    "prefer_taste": "SWEET_FRUIT",
                    "prefer_taste_display": "달콤과일파",
                    "taste_description": "당신은 부드럽고 달콤한 맛에서 행복을 느끼는군요!",
                    "image_url": "http://localhost:8000/images/types/sweet_fruit.png",
                    "created_at": "2024-01-01T00:00:00Z",
                },
            }
        },
        tags=["사용자"],
    )
    def get(self, request):
        """사용자 프로필 조회"""
        # 1. 서비스에서 사용자 프로필 데이터 조회
        profile_data = ControllerService.get_user_profile_data(request.user)

        # 2. 응답 반환
        return Response(profile_data, status=status.HTTP_200_OK)
