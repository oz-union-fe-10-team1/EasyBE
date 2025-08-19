# apps/users/views/user_view.py
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import UserSerializer, UserUpdateSerializer


class UserProfileView(APIView):
    """
    사용자 정보 조회/수정 API
    GET /api/v1/users/profile/ - 정보 조회
    PATCH /api/v1/users/profile/ - 닉네임 수정
    """

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """사용자 정보 조회"""
        user = request.user
        serializer = UserSerializer(user)

        return Response({"success": True, "user_info": serializer.data}, status=status.HTTP_200_OK)

    def patch(self, request: Request) -> Response:
        """닉네임 수정"""
        user = request.user
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()

        return Response(
            {"success": True, "message": "닉네임이 성공적으로 변경되었습니다.", "user_info": UserSerializer(user).data},
            status=status.HTTP_200_OK,
        )
