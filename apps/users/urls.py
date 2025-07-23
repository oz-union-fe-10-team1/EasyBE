from django.urls import path

from .views import KakaoLoginView, NaverLoginView

urlpatterns = [
    path("login/kakao/", KakaoLoginView.as_view(), name="kakao_login"),
    path("login/naver/", NaverLoginView.as_view(), name="naver_login"),
]
