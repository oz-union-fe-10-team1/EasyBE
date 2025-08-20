# apps/feedback/views.py

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Feedback
from .serializers import FeedbackListSerializer, FeedbackSerializer


@extend_schema_view(
    list=extend_schema(summary="피드백 목록 조회", tags=["피드백"]),
    create=extend_schema(summary="피드백 작성 (이미지 포함)", tags=["피드백"]),
    retrieve=extend_schema(summary="피드백 상세 조회", tags=["피드백"]),
    update=extend_schema(summary="피드백 수정 (이미지 교체 가능)", tags=["피드백"]),
    partial_update=extend_schema(summary="피드백 부분 수정", tags=["피드백"]),
    destroy=extend_schema(summary="피드백 삭제 (이미지 포함)", tags=["피드백"]),
)
class FeedbackViewSet(viewsets.ModelViewSet):
    """피드백 ViewSet - 이미지 업로드 지원"""

    queryset = Feedback.objects.select_related(
        "user", "order_item", "order_item__product", "order_item__order", "order_item__order__user"
    ).all()
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["rating", "user"]
    ordering_fields = ["created_at", "rating", "view_count"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        """액션별 시리얼라이저 선택"""
        if self.action == "list":
            return FeedbackListSerializer
        return FeedbackSerializer

    def get_permissions(self):
        """액션별 권한 설정"""
        if self.action in ["retrieve", "recent_reviews", "popular_reviews", "personalized_reviews"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """피드백 생성 시 사용자 정보 및 검증"""
        order_item = serializer.validated_data.get("order_item")

        if not order_item:
            raise ValueError("order_item은 필수 필드입니다.")

        # 해당 주문이 현재 사용자의 것인지 확인
        if order_item.order.user != self.request.user:
            raise PermissionError("본인의 주문에 대해서만 피드백을 작성할 수 있습니다.")

        # 이미 피드백이 존재하는지 확인
        if hasattr(order_item, "feedback"):
            raise ValueError("이미 해당 상품에 대한 피드백이 존재합니다.")

        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """피드백 생성 (이미지 포함) - 에러 처리"""
        try:
            return super().create(request, *args, **kwargs)
        except PermissionError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        """피드백 수정 (이미지 교체/삭제 포함) - 권한 검증"""
        instance = self.get_object()

        # 본인의 피드백만 수정 가능
        if instance.user != request.user:
            return Response({"error": "본인의 피드백만 수정할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        # 이미지 삭제 요청 처리 (image: null로 전송)
        if "image" in request.data and request.data["image"] is None:
            if instance.image_url:
                instance.delete_image()
            # image 필드를 데이터에서 제거 (시리얼라이저 검증 오류 방지)
            request.data.pop("image", None)

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """피드백 삭제 (이미지도 함께 삭제) - 권한 검증"""
        instance = self.get_object()

        # 본인의 피드백만 삭제 가능
        if instance.user != request.user:
            return Response({"error": "본인의 피드백만 삭제할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        return super().destroy(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """피드백 상세 조회 시 조회수 자동 증가"""
        instance = self.get_object()
        instance.increment_view_count()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(summary="실시간 후기", description="최근 높은 평점 피드백 4개", tags=["후기페이지"])
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def recent_reviews(self, request):
        """실시간 후기"""
        queryset = (
            Feedback.objects.select_related("user", "order_item__product")
            .recent()
            .high_rated()
            .order_by("-created_at")[:4]
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="인기 후기", description="조회수 높은 피드백 8개", tags=["후기페이지"])
    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def popular_reviews(self, request):
        """인기 후기"""
        queryset = Feedback.objects.select_related("user", "order_item__product").popular()[:8]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="개인화 추천 후기", description="사용자 취향 기반 추천 피드백 8개", tags=["후기페이지"])
    @action(detail=False, methods=["get"])
    def personalized_reviews(self, request):
        """나와 비슷한 취향의 후기"""
        queryset = Feedback.objects.select_related("user", "order_item__product").personalized_for_user(request.user)[
            :8
        ]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(summary="내 후기 목록", description="본인이 작성한 피드백 목록", tags=["마이페이지"])
    @action(detail=False, methods=["get"])
    def my_reviews(self, request):
        """내가 작성한 리뷰들"""
        queryset = Feedback.objects.select_related("order_item__product").filter(user=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
