from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    """
    피드백 생성, 조회, 수정, 삭제를 위한 API
    - 생성(POST): /api/feedbacks/
    - 내 피드백 목록(GET): /api/feedbacks/
    - 특정 피드백 조회(GET): /api/feedbacks/{id}/
    - 수정(PATCH): /api/feedbacks/{id}/
    - 삭제(DELETE): /api/feedbacks/{id}/
    """
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """자신이 작성한 피드백만 조회하도록 필터링"""
        return Feedback.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """피드백 생성 시, 현재 로그인된 사용자를 자동으로 할당"""
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        """시리얼라이저에 request 객체를 전달하여 권한 검사에 사용"""
        return {'request': self.request}