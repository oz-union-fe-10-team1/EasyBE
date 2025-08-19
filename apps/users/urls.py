# apps/users/urls.py

from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views.adult_verification_view import CompleteAdultVerificationView
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
    UserDeleteView,
    UserProfileView,
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
    # 성인 인증
    path(
        "auth/adult-verification/complete", CompleteAdultVerificationView.as_view(), name="complete_adult_verification"
    ),
    # JWT 토큰 관련
    path("auth/token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    # 사용자 프로필 관리
    path("user/profile/", UserProfileView.as_view(), name="user_profile"),
    path("user/delete/", UserDeleteView.as_view(), name="user_delete"),  # 일관성 있게 수정
    # 사용자 취향 프로필
    path("user/taste-profile/", TasteProfileView.as_view(), name="taste_profile"),
    # 계정 복구
    path("restore/", SendRecoveryCodeAPIView.as_view(), name="save_recovery_code"),
    path("recovery/verify-email/", VerifyRecoveryCodeAPIView.as_view(), name="verify_email"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
