"""
취향 테스트 상수 모듈
"""

from .taste_profiles import TASTE_PROFILES
from .taste_types import MIXED_TYPE_MAPPING, TYPE_INFO
from .test_data import ANSWER_MAPPING, QUESTIONS

__all__ = [
    "QUESTIONS",
    "ANSWER_MAPPING",
    "TYPE_INFO",
    "MIXED_TYPE_MAPPING",
    "TASTE_PROFILES",
]
