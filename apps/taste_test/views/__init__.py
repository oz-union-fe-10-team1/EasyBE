"""
뷰 모듈
"""

from .test_views import TasteTestQuestionsView, TasteTestSubmitView, TasteTestRetakeView
from .profile_views import UserProfileView
from .info_views import TasteTypesView

__all__ = [
    # 테스트 관련 뷰
    "TasteTestQuestionsView",
    "TasteTestSubmitView",
    "TasteTestRetakeView",

    # 프로필 관련 뷰
    "UserProfileView",

    # 정보 조회 뷰
    "TasteTypesView",
]