"""
서비스 모듈
"""

from .base import TasteTestService, get_questions, process_taste_test
from .calculator import ScoreCalculator
from .analyzer import TypeAnalyzer
from .storage import TestResultStorage
from .profile_handler import ProfileHandler

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
]