# apps/products/views/brewery.py

from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated

from apps.products.models import Brewery
from apps.products.serializers import BreweryListSerializer, BrewerySerializer

from .pagination import SearchPagination


class BreweryListView(ListAPIView):
    """양조장 목록 조회"""

    serializer_class = BreweryListSerializer
    pagination_class = SearchPagination

    @extend_schema(
        summary="양조장 목록 조회",
        description="""
        활성화된 모든 양조장의 목록을 조회합니다. (관리자용)

        **사용 목적:**
        - 관리자가 술 등록 시 양조장을 선택하는 용도
        - 양조장 관리 및 조회

        **응답 정보:**
        - 기본 정보: ID, 이름, 지역, 이미지
        - 통계: 해당 양조장의 활성 상품 수

        **정렬:** 양조장명 가나다순
        """,
        examples=[
            OpenApiExample(
                "응답 예시",
                value={
                    "count": 15,
                    "results": [
                        {
                            "id": 1,
                            "name": "국순당",
                            "region": "경기도",
                            "image_url": "https://example.com/image.jpg",
                            "product_count": 8,
                        }
                    ],
                },
            )
        ],
        tags=["관리자 - 양조장 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        return Brewery.objects.filter(is_active=True).order_by("name")


class BreweryDetailView(RetrieveAPIView):
    """양조장 상세 조회"""

    serializer_class = BrewerySerializer
    lookup_field = "pk"

    @extend_schema(
        summary="양조장 상세 조회",
        description="""
        특정 양조장의 상세 정보를 조회합니다. (관리자용)

        **응답 정보:**
        - 기본 정보: 이름, 지역, 주소, 연락처, 설명
        - 이미지 정보
        - 활성 상태
        - 통계: 술 개수, 활성 상품 수
        - 등록일
        """,
        examples=[
            OpenApiExample(
                "응답 예시",
                value={
                    "id": 1,
                    "name": "국순당",
                    "region": "경기도",
                    "address": "경기도 성남시...",
                    "phone": "031-123-4567",
                    "description": "전통주 전문 양조장...",
                    "image_url": "https://example.com/image.jpg",
                    "is_active": True,
                    "drink_count": 12,
                    "product_count": 8,
                    "created_at": "2024-01-01T00:00:00Z",
                },
            )
        ],
        tags=["관리자 - 양조장 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_queryset(self):
        return Brewery.objects.filter(is_active=True)


class BreweryCreateView(CreateAPIView):
    """양조장 생성"""

    serializer_class = BrewerySerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="양조장 생성",
        description="""
        새로운 양조장을 등록합니다. (관리자용)

        **필수 항목:**
        - name: 양조장명

        **선택 항목:**
        - region: 지역
        - address: 주소  
        - phone: 연락처
        - description: 설명
        - image_url: 이미지 URL

        **기본값:**
        - is_active: true (활성 상태)
        """,
        examples=[
            OpenApiExample(
                "요청 예시",
                value={
                    "name": "새로운 양조장",
                    "region": "충청북도",
                    "address": "충청북도 청주시...",
                    "phone": "043-123-4567",
                    "description": "전통 막걸리 전문 양조장",
                    "image_url": "https://example.com/new-brewery.jpg",
                },
            )
        ],
        tags=["관리자 - 양조장 관리"],
    )
    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save()


class BreweryManageView(RetrieveUpdateDestroyAPIView):
    """양조장 관리 (조회/수정/삭제)"""

    serializer_class = BrewerySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"

    @extend_schema(
        summary="양조장 관리 - 조회",
        description="""
        양조장의 상세 정보를 조회합니다. (관리자용)
        비활성 양조장도 조회할 수 있습니다.
        """,
        tags=["관리자 - 양조장 관리"],
    )
    def get(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(exclude=True)  # PUT은 PATCH와 동일하므로 문서에서 제외
    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="양조장 정보 수정",
        description="양조장 정보를 부분 수정합니다.",
        examples=[
            OpenApiExample(
                "수정 요청 예시",
                value={"name": "수정된 양조장명", "region": "전라남도", "description": "업데이트된 설명"},
            )
        ],
        tags=["관리자 - 양조장 관리"],
    )
    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="양조장 삭제 (비활성화)",
        description="""
        양조장을 비활성화합니다. (소프트 삭제)

        **동작:**
        - 실제 삭제하지 않고 is_active를 false로 변경
        - 기존 데이터는 보존됩니다
        """,
        tags=["관리자 - 양조장 관리"],
    )
    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_queryset(self):
        return Brewery.objects.all()  # 관리자는 비활성 양조장도 조회 가능

    def perform_destroy(self, instance):
        # 실제 삭제 대신 소프트 삭제
        instance.is_active = False
        instance.save()
