"""
취향 테스트 통합 서비스 (하위 호환성 지원)
"""

from typing import Dict, List

from ..constants import QUESTIONS
from ..utils import URLHelper
from ..validators import AnswerValidator
from .analyzer import TypeAnalyzer
from .calculator import ScoreCalculator
from .profile_handler import ProfileHandler
from .storage import TestResultStorage


class TasteTestService:
    """취향 테스트 통합 서비스 클래스 (기존 인터페이스 유지)"""

    # === 질문 관련 메서드 ===
    @staticmethod
    def get_questions() -> List[Dict]:
        """질문 목록 반환"""
        return QUESTIONS

    # === 계산 관련 메서드 ===
    @staticmethod
    def calculate_scores(answers: Dict[str, str]) -> Dict[str, int]:
        """답변을 기반으로 각 유형별 점수 계산"""
        return ScoreCalculator.calculate_scores(answers)

    @staticmethod
    def determine_type(scores: Dict[str, int]) -> str:
        """점수를 바탕으로 최종 유형 결정"""
        return TypeAnalyzer.determine_type(scores)

    # === 정보 조회 메서드 ===
    @staticmethod
    def get_type_info(korean_name: str) -> Dict:
        """한국어 유형명으로 유형 정보 반환"""
        return TypeAnalyzer.get_type_info(korean_name)

    @staticmethod
    def get_type_info_by_enum(enum_value: str) -> Dict:
        """enum 값으로 유형 정보 반환"""
        return TypeAnalyzer.get_type_info_by_enum(enum_value)

    @staticmethod
    def get_image_url_by_enum(enum_value: str) -> str:
        """enum 값으로 이미지 URL 반환"""
        return URLHelper.get_image_url_by_enum(enum_value)

    @staticmethod
    def get_taste_type_base_scores(enum_value: str) -> Dict[str, float]:
        """enum 값으로 기본 맛 점수 반환"""
        return TypeAnalyzer.get_taste_type_base_scores(enum_value)

    # === 통합 처리 메서드 ===
    @staticmethod
    def process_taste_test(answers: Dict[str, str]) -> Dict:
        """테스트 전체 처리"""
        return TypeAnalyzer.process_complete_analysis(answers)

    # === 저장 관련 메서드 ===
    @staticmethod
    def save_test_result(user, answers: Dict[str, str]):
        """테스트 결과를 DB에 저장"""
        return TestResultStorage.save_test_result(user, answers)

    # === 재테스트 관련 메서드 ===
    @staticmethod
    def get_retake_preview(user, answers: Dict[str, str]) -> Dict:
        """재테스트 시 변화 미리보기"""
        return ProfileHandler.get_retake_preview(user, answers)

    # === 검증 관련 메서드 ===
    @staticmethod
    def validate_answers(answers: Dict[str, str]) -> Dict[str, List[str]]:
        """답변 유효성 검증"""
        return AnswerValidator.validate_answers(answers)


# === 하위 호환성을 위한 함수들 ===
def get_questions() -> List[Dict]:
    """하위 호환성: 질문 목록 반환"""
    return TasteTestService.get_questions()


def process_taste_test(answers: Dict[str, str]) -> Dict:
    """하위 호환성: 테스트 전체 처리"""
    return TasteTestService.process_taste_test(answers)
