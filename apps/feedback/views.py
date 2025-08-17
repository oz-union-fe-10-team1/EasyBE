# apps/feedback/views.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Feedback
from .serializers import FeedbackSerializer


@extend_schema_view(
    list=extend_schema(summary="피드백 목록 조회", tags=["피드백"]),
    create=extend_schema(summary="피드백 작성", tags=["피드백"]),
    retrieve=extend_schema(summary="피드백 상세 조회", tags=["피드백"]),
    update=extend_schema(summary="피드백 수정", tags=["피드백"]),
    partial_update=extend_schema(summary="피드백 부분 수정", tags=["피드백"]),
    destroy=extend_schema(summary="피드백 삭제", tags=["피드백"]),
)
class FeedbackViewSet(viewsets.ModelViewSet):
    """피드백 ViewSet"""

    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["rating", "user"]
    ordering_fields = ["created_at", "rating", "view_count"]
    ordering = ["-created_at"]

    def get_permissions(self):
        """액션별 권한 설정"""
        if self.action in ["retrieve", "recent_reviews", "popular_reviews", "personalized_reviews"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """리뷰 생성 시 사용자 자동 설정"""
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """리뷰 상세 조회 시 조회수 증가"""
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="실시간 후기", description="최근 높은 평점 피드백 4개", tags=["후기페이지"])
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def recent_reviews(self, request):
        """실시간 후기"""
        queryset = Feedback.objects.recent().high_rated()[:4]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="인기 후기", description="조회수 높은 피드백 8개", tags=["후기페이지"])
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def popular_reviews(self, request):
        """인기 후기"""
        queryset = Feedback.objects.popular()[:8]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="개인화 추천 후기", description="사용자 취향 기반 추천 피드백 8개", tags=["후기페이지"])
    @action(detail=False, methods=["get"])
    def personalized_reviews(self, request):
        """나와 비슷한 취향의 후기"""
        queryset = Feedback.objects.personalized_for_user(request.user)[:8]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="내 후기 목록", description="본인이 작성한 피드백 목록", tags=["마이페이지"])
    @action(detail=False, methods=["get"])
    def my_reviews(self, request):
        """내가 작성한 리뷰들"""
        queryset = Feedback.objects.filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
