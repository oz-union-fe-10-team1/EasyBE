# urls.py
from django.urls import path

from . import views

app_name = "taste_test"

urlpatterns = [
    path("questions/", views.TasteTestQuestionsView.as_view(), name="questions"),
    path("submit/", views.TasteTestSubmitView.as_view(), name="submit"),
    path("profile/", views.UserProfileView.as_view(), name="profile"),
    path("retake/", views.TasteTestRetakeView.as_view(), name="retake"),
    path("types/", views.TasteTypesView.as_view(), name="types"),
]
