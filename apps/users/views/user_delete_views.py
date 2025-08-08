from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.users.models import User
class UserDeleteAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id):
        user = User.objects.get(id=user_id) # login 구현시 request.user 로 변경 예정
        if user.is_deleted:
            return Response({"detail": "이미 탈퇴 처리된 계정입니다."}, status=status.HTTP_400_BAD_REQUEST)

        user.soft_delete()
        return  Response({"detail": "회원 탈퇴가 완료되었습니다. 14일 이내에 복구 가능합니다."}, status=status.HTTP_200_OK)