"""
데이터 저장 및 조회 서비스
"""

from typing import Dict, Optional

from django.contrib.auth import get_user_model

from ..models import PreferenceTestResult
from ..utils import URLHelper
from .analyzer import TypeAnalyzer

User = get_user_model()


class TestResultStorage:
    """테스트 결과 저장 및 조회"""

    @staticmethod
    def save_test_result(user, answers: Dict[str, str]) -> PreferenceTestResult:
        """테스트 결과를 DB에 저장 (개선된 재테스트 지원)"""
        # 테스트 결과 처리
        test_result_data = TypeAnalyzer.process_complete_analysis(answers)
        korean_type = test_result_data["type"]

        # enum 값 가져오기
        enum_value = URLHelper.get_enum_by_korean_name(korean_type)
        if not enum_value or not hasattr(PreferenceTestResult.PreferTaste, enum_value):
            enum_value = "GOURMET"

        prefer_taste_enum = getattr(PreferenceTestResult.PreferTaste, enum_value)

        # 기존 테스트 결과 확인
        existing_result = PreferenceTestResult.objects.filter(user=user).first()
        is_new_test = existing_result is None

        # DB 저장 (재테스트면 업데이트, 신규면 생성)
        result, created = PreferenceTestResult.objects.update_or_create(
            user=user, defaults={"answers": answers, "prefer_taste": prefer_taste_enum}
        )

        # PreferTasteProfile 처리
        from .profile_handler import ProfileHandler

        profile_result = ProfileHandler.handle_taste_profile(user, result, is_new_test)

        # 결과에 프로필 처리 정보 추가
        result.profile_update_result = profile_result

        return result

    @staticmethod
    def get_user_result(user) -> Optional[PreferenceTestResult]:
        """사용자의 테스트 결과 조회"""
        try:
            return PreferenceTestResult.objects.get(user=user)
        except PreferenceTestResult.DoesNotExist:
            return None

    @staticmethod
    def has_test_result(user) -> bool:
        """사용자가 테스트를 완료했는지 확인"""
        return hasattr(user, "preference_test_result")
