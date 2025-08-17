from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views.user_restore_code_view import (
    SendRecoveryCodeAPIView,
    VerifyRecoveryCodeAPIView,
)

from .views import (
    GoogleLoginView,
    KakaoLoginView,
    NaverLoginView,
    OAuthStateView,
    TasteProfileView,
)
from .views.logout_view import LogoutView

app_name = "users"

# v1 API 패턴
v1_patterns = [
    # OAuth 로그인 API
    path("auth/login/kakao", KakaoLoginView.as_view(), name="kakao_login"),
    path("auth/login/naver", NaverLoginView.as_view(), name="naver_login"),
    path("auth/login/google", GoogleLoginView.as_view(), name="google_login"),
    path("auth/state", OAuthStateView.as_view(), name="save_oauth_state"),
    # jwt token refresh
    path("auth/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    # logout
    path("auth/logout", LogoutView.as_view(), name="logout"),
    # 사용자 취향 프로필 조회 및 수정
    path("user/taste-profile/", TasteProfileView.as_view(), name="taste_profile"),
    path("restore/", SendRecoveryCodeAPIView.as_view(), name="save_recovery_code"),
    path("recovery/verify-email/", VerifyRecoveryCodeAPIView.as_view(), name="verify_email"),
]


urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
