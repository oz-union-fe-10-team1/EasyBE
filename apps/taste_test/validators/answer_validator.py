"""
답변 유효성 검증 모듈
"""

from typing import Dict, List

from ..constants import ANSWER_MAPPING, QUESTIONS


class AnswerValidator:
    """테스트 답변 유효성 검증"""

    @staticmethod
    def validate_answers(answers: Dict[str, str]) -> Dict[str, List[str]]:
        """답변 유효성 검증"""
        errors: Dict[str, List[str]] = {}

        # 타입 안전하게 question id 추출
        required_questions = {str(q["id"]) for q in QUESTIONS}
        provided_questions = {str(k) for k in answers.keys()}

        # 누락/추가 질문 확인
        missing = required_questions - provided_questions
        if missing:
            missing_sorted = sorted(missing)
            errors["missing_questions"] = [f"다음 질문에 답변해주세요: {', '.join(missing_sorted)}"]

        extra = provided_questions - required_questions
        if extra:
            extra_sorted = sorted(extra)
            errors["extra_questions"] = [f"존재하지 않는 질문입니다: {', '.join(extra_sorted)}"]

        # 각 답변 유효성 확인
        for question_id, answer in answers.items():
            if question_id in ANSWER_MAPPING:
                valid_choices = list(ANSWER_MAPPING[question_id].keys())
                if answer not in valid_choices:
                    errors[question_id] = [f"유효한 선택지는 {', '.join(valid_choices)}입니다."]

        return errors

    @staticmethod
    def validate_answer_count(answers: Dict[str, str]) -> bool:
        """답변 개수 유효성 검증 (6개 질문)"""
        return len(answers) == len(QUESTIONS)

    @staticmethod
    def validate_answer_format(answers: Dict[str, str]) -> bool:
        """답변 형식 유효성 검증 (A 또는 B)"""
        valid_choices = {"A", "B"}
        return all(answer in valid_choices for answer in answers.values())
