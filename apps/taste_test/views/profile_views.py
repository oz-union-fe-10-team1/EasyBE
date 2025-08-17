"""
사용자 프로필 관련 뷰
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services import TasteTestService


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
        has_test = hasattr(request.user, "preference_test_result")

        data = {"user": request.user.nickname, "has_test": has_test}

        if has_test:
            test_result = request.user.preference_test_result
            data.update(
                {
                    "id": test_result.id,
                    "prefer_taste": test_result.prefer_taste,
                    "prefer_taste_display": test_result.get_prefer_taste_display(),
                    "taste_description": test_result.get_taste_description(),
                    "image_url": TasteTestService.get_image_url_by_enum(test_result.prefer_taste),
                    "created_at": test_result.created_at,
                }
            )

        return Response(data, status=status.HTTP_200_OK)