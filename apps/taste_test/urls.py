from django.urls import path

from . import views

app_name = "taste_profile"

urlpatterns = [
    # 맛 테스트 관련
    path("test/questions/", views.TasteTestQuestionsView.as_view(), name="test_questions"),
    path("test/submit/", views.TasteTestSubmitView.as_view(), name="test_submit"),
    # 프로필 조회
    path("profile/", views.UserTasteProfileView.as_view(), name="user_profile"),
    path("profile/<int:customer_id>/", views.UserTasteProfileView.as_view(), name="guest_profile"),
    # 맛 타입 목록
    path("types/", views.taste_types_list, name="taste_types"),
    # 통계 (관리자용)
    path("statistics/", views.TasteTestStatisticsView.as_view(), name="statistics"),
]
