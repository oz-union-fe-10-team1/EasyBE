# apps/feedback/urls.py
from django.urls import include, path

from apps.feedback.views import FeedbackViewSet

app_name = "feedback"

v1_patterns = [
    # 피드백 기본 CRUD
    path("feedbacks/", FeedbackViewSet.as_view({"get": "list", "post": "create"}), name="feedbacks-list"),
    path(
        "feedbacks/<int:pk>/",
        FeedbackViewSet.as_view(
            {
                "get": "retrieve",  # 조회 시 자동으로 조회수 증가
                "put": "update",
                "patch": "partial_update",  # 이미지 삭제도 여기서 처리
                "delete": "destroy",
            }
        ),
        name="feedbacks-detail",
    ),
    # 메인페이지용 피드백 조회
    path("feedbacks/recent/", FeedbackViewSet.as_view({"get": "recent_reviews"}), name="feedbacks-recent"),
    path("feedbacks/popular/", FeedbackViewSet.as_view({"get": "popular_reviews"}), name="feedbacks-popular"),
    path(
        "feedbacks/personalized/",
        FeedbackViewSet.as_view({"get": "personalized_reviews"}),
        name="feedbacks-personalized",
    ),
    # 사용자별 피드백
    path("user/feedbacks/", FeedbackViewSet.as_view({"get": "my_reviews"}), name="feedbacks-my"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
