"""
점수 계산 서비스
"""

from typing import Dict

from ..constants import ANSWER_MAPPING


class ScoreCalculator:
    """테스트 답변 기반 점수 계산"""

    @staticmethod
    def calculate_scores(answers: Dict[str, str]) -> Dict[str, int]:
        """답변을 기반으로 각 유형별 점수 계산"""
        scores = {"달콤과일파": 0, "상큼톡톡파": 0, "묵직여운파": 0, "깔끔고소파": 0}

        for question_id, answer in answers.items():
            if question_id in ANSWER_MAPPING:
                taste_type = ANSWER_MAPPING[question_id].get(answer)
                if taste_type in scores:
                    scores[taste_type] += 1

        return scores

    @staticmethod
    def get_max_score_types(scores: Dict[str, int]) -> tuple[int, list[str]]:
        """최고 점수와 해당하는 유형들 반환"""
        max_score = max(scores.values())
        top_types = [type_name for type_name, score in scores.items() if score == max_score]
        return max_score, top_types

    @staticmethod
    def is_dominant_type(scores: Dict[str, int], threshold: int = 3) -> bool:
        """단일 우세 유형인지 확인 (기본 임계값: 3점)"""
        max_score, top_types = ScoreCalculator.get_max_score_types(scores)
        return max_score >= threshold and len(top_types) == 1
