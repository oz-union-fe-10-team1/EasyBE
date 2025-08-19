# urls.py
from django.urls import include, path

from . import views

app_name = "taste_test"

v1_patterns = [
    path("taste_test/questions/", views.TasteTestQuestionsView.as_view(), name="questions"),
    path("taste_test/submit/", views.TasteTestSubmitView.as_view(), name="submit"),
    path("user/taste_test/profile", views.UserProfileView.as_view(), name="profile"),
    path("taste_test/retake/", views.TasteTestRetakeView.as_view(), name="retake"),
    path("taste_test/types/", views.TasteTypesView.as_view(), name="types"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
