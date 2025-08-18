# apps/feedback/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.feedback.views import FeedbackViewSet

app_name = "feedback"

# ViewSet을 위한 라우터 설정
router = DefaultRouter()
router.register(r"feedbacks", FeedbackViewSet, basename="feedback")

# v1 API 패턴
v1_patterns = [
    # 피드백 기본 CRUD (이미지 업로드 지원)
    path("feedbacks", FeedbackViewSet.as_view({"get": "list", "post": "create"}), name="feedbacks-list"),
    path(
        "feedbacks/<int:pk>",
        FeedbackViewSet.as_view({"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}),
        name="feedbacks-detail",
    ),
    # 피드백 관리 (어드민용)
    path(
        "feedbacks/<int:pk>/manage",
        FeedbackViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="feedbacks-manage",
    ),
    # 메인페이지용 피드백 조회 APIs
    path("feedbacks/recent", FeedbackViewSet.as_view({"get": "recent_reviews"}), name="feedbacks-recent"),
    path("feedbacks/popular", FeedbackViewSet.as_view({"get": "popular_reviews"}), name="feedbacks-popular"),
    path(
        "feedbacks/personalized",
        FeedbackViewSet.as_view({"get": "personalized_reviews"}),
        name="feedbacks-personalized",
    ),
    # 사용자별 피드백
    path("feedbacks/my", FeedbackViewSet.as_view({"get": "my_reviews"}), name="feedbacks-my"),
    # 피드백 액션들 (이미지 관련)
    path(
        "feedbacks/<int:pk>/increment_view",
        FeedbackViewSet.as_view({"post": "increment_view"}),
        name="feedbacks-increment-view",
    ),
    path(
        "feedbacks/<int:pk>/delete_image",
        FeedbackViewSet.as_view({"delete": "delete_image"}),
        name="feedbacks-delete-image",
    ),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
