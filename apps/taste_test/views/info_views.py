"""
정보 조회 관련 뷰
"""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ..constants import TYPE_INFO
from ..services import TasteTestService


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
        # 절대 URL로 변환하여 반환
        types_data = []
        for type_info in TYPE_INFO.values():
            type_info_copy = type_info.copy()
            type_info_copy["image_url"] = TasteTestService.get_image_url_by_enum(type_info["enum"])
            types_data.append(type_info_copy)

        return Response({"types": types_data, "total": len(types_data)}, status=status.HTTP_200_OK)