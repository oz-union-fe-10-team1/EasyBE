"""
서비스 모듈
"""

# 하위 호환성을 위한 상수들
from ..constants import ANSWER_MAPPING, QUESTIONS, TASTE_PROFILES, TYPE_INFO
from ..constants.taste_types import MIXED_TYPE_MAPPING
from ..utils import URLHelper
from .analyzer import TypeAnalyzer
from .base import TasteTestService, get_questions, process_taste_test
from .calculator import ScoreCalculator
from .controller_support import ControllerService
from .profile_handler import ProfileHandler
from .storage import TestResultStorage

# 기존 테스트에서 사용하던 상수들 (하위 호환성)
TASTE_QUESTIONS = QUESTIONS
ANSWER_SCORE_MAPPING = ANSWER_MAPPING
TASTE_TYPES = TYPE_INFO
TASTE_TYPE_IMAGES = {
    str(type_info["enum"]): URLHelper.get_image_url_by_enum(str(type_info["enum"])) for type_info in TYPE_INFO.values()
}


# TasteTestData 클래스 하위 호환성 (외부에서 사용하는 경우)
class TasteTestData:
    """하위 호환성을 위한 TasteTestData 클래스"""

    QUESTIONS = QUESTIONS
    ANSWER_MAPPING = ANSWER_MAPPING
    TYPE_INFO = TYPE_INFO
    TASTE_PROFILES = TASTE_PROFILES
    MIXED_TYPE_MAPPING = MIXED_TYPE_MAPPING

    @classmethod
    def get_enum_by_korean_name(cls, korean_name: str):
        """한국어 이름으로 enum 값 조회"""
        return URLHelper.get_enum_by_korean_name(korean_name)

    @classmethod
    def get_image_url_by_enum(cls, enum_value: str) -> str:
        """enum 값으로 이미지 URL 조회"""
        return URLHelper.get_image_url_by_enum(enum_value)


__all__ = [
    # 통합 서비스 (하위 호환성)
    "TasteTestService",
    "get_questions",
    "process_taste_test",
    # 개별 서비스 클래스
    "ScoreCalculator",
    "TypeAnalyzer",
    "TestResultStorage",
    "ProfileHandler",
    # 컨트롤러 지원 서비스
    "ControllerService",
    # 하위 호환성 상수들
    "TASTE_QUESTIONS",
    "ANSWER_SCORE_MAPPING",
    "TASTE_TYPES",
    "TASTE_TYPE_IMAGES",
    # 하위 호환성 클래스
    "TasteTestData",
]
