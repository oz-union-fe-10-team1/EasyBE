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
    path("questions", TasteTestQuestionsView.as_view(), name="questions"),
    path("submit", TasteTestSubmitView.as_view(), name="submit"),
    path("profile", UserProfileView.as_view(), name="profile"),
    path("retake", TasteTestRetakeView.as_view(), name="retake"),
    path("types", TasteTypesView.as_view(), name="types"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
