from django.urls import path

from .views import KakaoLoginView, NaverLoginView, GoogleLoginView

urlpatterns = [
    path("login/kakao/", KakaoLoginView.as_view(), name="kakao_login"),
    path("login/naver/", NaverLoginView.as_view(), name="naver_login"),
    path("login/google/", GoogleLoginView.as_view(), name="google_login"),
]
