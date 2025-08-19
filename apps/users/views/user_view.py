# apps/users/views/user_view.py
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import User
from ..serializers import UserSerializer, UserUpdateSerializer


@extend_schema_view(
    get=extend_schema(
        tags=["마이페이지"],
        summary="사용자 정보 조회",
        description="현재 로그인한 사용자의 프로필 정보를 조회합니다.",
        responses={
            200: UserSerializer,
        },
    ),
    patch=extend_schema(
        tags=["마이페이지"],
        summary="사용자 정보 수정",
        description="사용자의 닉네임, 알림 설정을 수정하거나 랜덤 닉네임을 생성할 수 있습니다.",
        request=UserUpdateSerializer,
        responses={
            200: UserSerializer,
        },
    ),
)
class UserProfileView(APIView):
    """
    사용자 정보 조회/수정 API
    GET /api/v1/users/profile/ - 정보 조회
    PATCH /api/v1/users/profile/ - 사용자 정보 수정
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """사용자 정보 조회"""
        user = request.user
        serializer = UserSerializer(user)

        return Response({"success": True, "user_info": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        """사용자 정보 수정"""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            {"success": True, "message": "프로필이 성공적으로 변경되었습니다.", "user_info": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    tags=["마이페이지"],
    summary="회원 탈퇴",
    description="현재 로그인한 사용자의 계정을 탈퇴 처리합니다. 14일 이내 복구 가능합니다.",
    responses={200: {"description": "탈퇴 성공"}, 400: {"description": "이미 탈퇴된 계정"}},
)
class UserDeleteView(APIView):
    """회원 탈퇴 API"""

    permission_classes = [IsAuthenticated]

    def delete(self, request: Request) -> Response:
        """회원 탈퇴"""
        user = request.user

        # 이미 탈퇴된 계정인지 확인
        if user.is_deleted:
            return Response(
                {"success": False, "message": "이미 탈퇴 처리된 계정입니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        # 탈퇴 처리
        user.soft_delete()

        return Response(
            {"success": True, "message": "회원 탈퇴가 완료되었습니다. 14일 이내에 복구 가능합니다."},
            status=status.HTTP_200_OK,
        )
