# apps/taste_test/urls.py

from django.urls import include, path

from apps.taste_test.views import (
    TasteTestQuestionsView,
    TasteTestRetakeView,
    TasteTestSubmitView,
    TasteTypesView,
    UserProfileView,
)

app_name = "taste_test"

# v1 API 패턴
v1_patterns = [
    path("taste_test/questions", TasteTestQuestionsView.as_view(), name="questions"),
    path("taste_test/submit", TasteTestSubmitView.as_view(), name="submit"),
    path("taste_test/profile", UserProfileView.as_view(), name="profile"),
    path("taste_test/retake", TasteTestRetakeView.as_view(), name="retake"),
    path("taste_test/types", TasteTypesView.as_view(), name="types"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
