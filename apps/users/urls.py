from django.urls import path

from apps.users.views.user_delete_views import UserDeleteAPIView

from .views import GoogleLoginView, KakaoLoginView, NaverLoginView, OAuthStateView

urlpatterns = [
    path("login/kakao/", KakaoLoginView.as_view(), name="kakao_login"),
    path("login/naver/", NaverLoginView.as_view(), name="naver_login"),
    path("login/google/", GoogleLoginView.as_view(), name="google_login"),
    path("state", OAuthStateView.as_view(), name="save_oauth_state"),
    path("<int:user_id>/delete/", UserDeleteAPIView.as_view(), name="delete_view"),  # login 구현시 파라미터 삭제 예정
]
