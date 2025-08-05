from datetime import datetime, timedelta

from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Feedback
from .serializers import FeedbackSerializer


class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """자신이 작성한 피드백만 조회하도록 필터링"""
        return Feedback.objects.filter(user=self.request.user).select_related(
            "order_item__product", "order_item__order"
        )

    def perform_create(self, serializer):
        """피드백 생성 시, Serializer의 create 메소드에 필요한 데이터를 전달"""
        serializer.save(user=self.request.user)

    def get_serializer_context(self):
        return {"request": self.request}

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # 조회수 1 증가
        instance.view_count = F("view_count") + 1
        instance.save(update_fields=["view_count"])
        instance.refresh_from_db()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="realtime")
    def realtime(self, request):
        """최신순으로 후기 목록을 반환"""
        queryset = Feedback.objects.order_by("-created_at")[:10]  # 최신 10개
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="monthly-best")
    def monthly_best(self, request):
        """최근 한 달간 가장 인기있는(조회수 높은) 피드백 목록을 반환"""
        one_month_ago = datetime.now() - timedelta(days=30)
        queryset = Feedback.objects.filter(created_at__gte=one_month_ago).order_by("-view_count")[:10]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny], url_path="all")
    def all_feedbacks(self, request):
        """인증 없이 모든 피드백 목록을 최신순으로 조회"""
        queryset = Feedback.objects.all().order_by("-created_at")
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
