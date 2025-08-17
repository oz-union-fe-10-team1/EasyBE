"""
취향 유형 분석 서비스
"""

from typing import Dict

from ..constants import MIXED_TYPE_MAPPING, TASTE_PROFILES, TYPE_INFO
from .calculator import ScoreCalculator


class TypeAnalyzer:
    """취향 유형 분석 및 결정"""

    @staticmethod
    def determine_type(scores: Dict[str, int]) -> str:
        """점수를 바탕으로 최종 유형 결정"""
        max_score, top_types = ScoreCalculator.get_max_score_types(scores)

        # 단일 유형 (3점 이상)
        if max_score >= 3 and len(top_types) == 1:
            return top_types[0]

        # 2개 유형 동점 - 혼합 유형
        if max_score == 2 and len(top_types) == 2:
            combination = frozenset(top_types)
            return MIXED_TYPE_MAPPING.get(combination, "미식가유형")

        # 기타 경우
        return "미식가유형"

    @staticmethod
    def get_type_info(korean_name: str) -> Dict:
        """한국어 유형명으로 유형 정보 반환"""
        from ..utils import URLHelper

        type_info = TYPE_INFO.get(korean_name, TYPE_INFO["미식가유형"]).copy()
        # 절대 URL로 변환
        type_info["image_url"] = URLHelper.get_image_url_by_enum(str(type_info["enum"]))
        return type_info

    @staticmethod
    def get_type_info_by_enum(enum_value: str) -> Dict:
        """enum 값으로 유형 정보 반환"""
        from ..utils import URLHelper

        for type_info in TYPE_INFO.values():
            if type_info["enum"] == enum_value:
                result = type_info.copy()
                result["image_url"] = URLHelper.get_image_url_by_enum(enum_value)
                return result

        result = TYPE_INFO["미식가유형"].copy()
        result["image_url"] = URLHelper.get_image_url_by_enum("GOURMET")
        return result

    @staticmethod
    def get_taste_type_base_scores(enum_value: str) -> Dict[str, float]:
        """enum 값으로 기본 맛 점수 반환"""
        return TASTE_PROFILES.get(enum_value, TASTE_PROFILES["GOURMET"])

    @staticmethod
    def process_complete_analysis(answers: Dict[str, str]) -> Dict:
        """테스트 전체 분석 처리"""
        scores = ScoreCalculator.calculate_scores(answers)
        determined_type = TypeAnalyzer.determine_type(scores)
        type_info = TypeAnalyzer.get_type_info(determined_type)

        return {
            "type": determined_type,
            "scores": scores,
            "info": type_info,
        }
