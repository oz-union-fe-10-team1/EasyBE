from django.core.cache import cache
from django.core.mail import send_mail
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.users.utils.Base62 import generate_base62_code
from config.settings.base import EMAIL_HOST_USER


class SendRecoveryCodeAPIView(APIView):
    # 이메일로 인증코드 전송 (Redis 저장)
    @extend_schema(summary="회원탈퇴 복구 이메일 인증 코드 발송", description="회원탈퇴 복구 이메일 인증 코드 발송")
    def post(self, request):
        # email = "parkseokmin0724@gmail.com"  # 임시 테스트
        email = request.data.get("email")
        if not email:
            return Response({"detail": "이메일을 입력해주세요."}, status=status.HTTP_400_BAD_REQUEST)

        code = generate_base62_code()
        # {key:value} >> {"seokmin0724@gmail.com":"v41kl5"}
        # Redis에 저장 (5분 TTL)
        cache_key = email
        cache.set(cache_key, code, timeout=300)  # 300초 = 5분

        # 이메일 발송
        send_mail(
            subject="[서비스명] 계정 복구 인증코드",
            message=f"인증코드: {code}\n5분 안에 입력해주세요.",
            from_email=EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        return Response({"detail": "인증코드를 이메일로 전송했습니다."}, status=status.HTTP_200_OK)


class VerifyRecoveryCodeAPIView(APIView):
    @extend_schema(summary="인증코드 검증 및 계정 복구", description="인증코드 검증 및 계정 복구")
    # 인증코드 검증 및 계정 복구
    def post(self, request):
        """
        ex) 예시
        email = "parkseokmin0724@gmail.com"
        code = "yuHqtW"
        """
        email = request.data.get("email")
        code = request.data.get("code")

        cache_key = email
        stored_code = cache.get(cache_key)

        if not stored_code:
            return Response({"detail": "인증코드가 만료되었거나 없습니다."}, status=status.HTTP_400_BAD_REQUEST)

        if stored_code != code:
            return Response({"detail": "잘못된 인증코드입니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 인증 성공 → 코드 삭제
        cache.delete(cache_key)

        try:
            user = User.objects.get(email=email)
            # user.is_active = True # is_deleted,deleted_at,recovery_deadline 추가 필요
            user.restore_account()
        except User.DoesNotExist:
            return Response({"detail": "해당 이메일의 탈퇴 계정을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "계정이 성공적으로 복구되었습니다."}, status=status.HTTP_200_OK)
