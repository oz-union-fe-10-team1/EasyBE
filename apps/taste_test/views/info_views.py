"""
정보 조회 관련 뷰 - 단계별 처리 과정 명시
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..services.controller_support import ControllerService


class TasteTypesView(APIView):
    """취향 유형 목록 조회"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="취향 유형 목록",
        description="9가지 취향 유형의 상세 정보를 조회합니다",
        responses={
            200: {
                "description": "유형 목록",
                "example": {
                    "types": [
                        {
                            "name": "달콤과일파",
                            "enum": "SWEET_FRUIT",
                            "description": "당신은 부드럽고 달콤한 맛에서 행복을 느끼는군요!",
                            "characteristics": ["달콤함", "과일향", "로맨틱", "부드러움"],
                            "image_url": "http://localhost:8000/images/types/sweet_fruit.png",
                        }
                    ],
                    "total": 9,
                },
            }
        },
        tags=["정보"],
    )
    def get(self, request):
        """취향 유형 목록 조회"""
        # 1. 서비스에서 취향 유형 데이터 조회 (이미지 URL 포함 처리)
        taste_types_data = ControllerService.get_taste_types_data()

        # 2. 응답 반환
        return Response(taste_types_data, status=status.HTTP_200_OK)