# tests/test_validators.py
"""
Validators 테스트 - 새로운 모듈 구조
"""

from django.test import TestCase

from ..validators import AnswerValidator


class AnswerValidatorTest(TestCase):
    """AnswerValidator 테스트"""

    def test_validate_answers_valid_input(self):
        """유효한 답변 검증 테스트"""
        valid_answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}

        errors = AnswerValidator.validate_answers(valid_answers)

        self.assertEqual(len(errors), 0)

    def test_validate_answers_missing_questions(self):
        """누락된 질문 검증 테스트"""
        incomplete_answers = {"Q1": "A", "Q3": "B"}

        errors = AnswerValidator.validate_answers(incomplete_answers)

        self.assertIn("missing_questions", errors)
        self.assertIn("Q2", errors["missing_questions"][0])
        self.assertIn("Q4", errors["missing_questions"][0])
        self.assertIn("Q5", errors["missing_questions"][0])
        self.assertIn("Q6", errors["missing_questions"][0])

    def test_validate_answers_extra_questions(self):
        """추가 질문 검증 테스트"""
        extra_answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B", "Q7": "A", "Q99": "B"}

        errors = AnswerValidator.validate_answers(extra_answers)

        self.assertIn("extra_questions", errors)
        self.assertIn("Q7", errors["extra_questions"][0])
        self.assertIn("Q99", errors["extra_questions"][0])

    def test_validate_answers_invalid_choices(self):
        """잘못된 선택지 검증 테스트"""
        invalid_answers = {"Q1": "C", "Q2": "A", "Q3": "X", "Q4": "B", "Q5": "A", "Q6": "B"}

        errors = AnswerValidator.validate_answers(invalid_answers)

        self.assertIn("Q1", errors)
        self.assertIn("Q3", errors)
        self.assertIn("A, B", errors["Q1"][0])
        self.assertIn("A, B", errors["Q3"][0])

    def test_validate_answers_empty_input(self):
        """빈 답변 검증 테스트"""
        empty_answers = {}

        errors = AnswerValidator.validate_answers(empty_answers)

        self.assertIn("missing_questions", errors)
        # 모든 질문이 누락되어야 함
        for i in range(1, 7):
            self.assertIn(f"Q{i}", errors["missing_questions"][0])

    def test_validate_answer_count_valid(self):
        """답변 개수 검증 테스트 - 유효"""
        valid_answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}

        is_valid = AnswerValidator.validate_answer_count(valid_answers)

        self.assertTrue(is_valid)

    def test_validate_answer_count_invalid(self):
        """답변 개수 검증 테스트 - 무효"""
        too_few_answers = {"Q1": "A", "Q2": "B"}
        too_many_answers = {f"Q{i}": "A" for i in range(1, 10)}

        self.assertFalse(AnswerValidator.validate_answer_count(too_few_answers))
        self.assertFalse(AnswerValidator.validate_answer_count(too_many_answers))

    def test_validate_answer_format_valid(self):
        """답변 형식 검증 테스트 - 유효"""
        valid_answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}

        is_valid = AnswerValidator.validate_answer_format(valid_answers)

        self.assertTrue(is_valid)

    def test_validate_answer_format_invalid(self):
        """답변 형식 검증 테스트 - 무효"""
        invalid_format_answers = {"Q1": "C", "Q2": "B", "Q3": "X", "Q4": "B", "Q5": "A", "Q6": "B"}

        is_valid = AnswerValidator.validate_answer_format(invalid_format_answers)

        self.assertFalse(is_valid)

    def test_validate_answers_case_sensitivity(self):
        """대소문자 구분 검증 테스트"""
        case_sensitive_answers = {"Q1": "a", "Q2": "B", "Q3": "A", "Q4": "b", "Q5": "A", "Q6": "B"}

        errors = AnswerValidator.validate_answers(case_sensitive_answers)

        # 소문자는 유효하지 않은 선택지로 처리되어야 함
        self.assertIn("Q1", errors)
        self.assertIn("Q4", errors)

    def test_validate_answers_mixed_errors(self):
        """여러 종류의 에러가 함께 있는 경우"""
        mixed_error_answers = {"Q1": "C", "Q3": "A", "Q7": "B"}

        errors = AnswerValidator.validate_answers(mixed_error_answers)

        # 누락된 질문
        self.assertIn("missing_questions", errors)
        # 추가 질문
        self.assertIn("extra_questions", errors)
        # 잘못된 선택지
        self.assertIn("Q1", errors)

        # 각 에러 타입이 올바르게 감지되는지 확인
        self.assertIn("Q2", errors["missing_questions"][0])
        self.assertIn("Q7", errors["extra_questions"][0])
        self.assertIn("A, B", errors["Q1"][0])


class AnswerValidatorIntegrationTest(TestCase):
    """AnswerValidator 통합 테스트"""

    def test_validator_with_real_test_data(self):
        """실제 테스트 데이터와의 통합 테스트"""
        # 실제로 테스트에서 사용할 법한 데이터들
        test_cases = [
            # 달콤과일파 패턴
            {"Q1": "A", "Q2": "B", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"},
            # 상큼톡톡파 패턴
            {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "A", "Q5": "A", "Q6": "B"},
            # 묵직여운파 패턴
            {"Q1": "B", "Q2": "A", "Q3": "B", "Q4": "B", "Q5": "B", "Q6": "B"},
            # 깔끔고소파 패턴
            {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"},
        ]

        for i, answers in enumerate(test_cases):
            with self.subTest(case=i):
                errors = AnswerValidator.validate_answers(answers)
                self.assertEqual(len(errors), 0, f"Case {i} should be valid")

    def test_validator_edge_cases(self):
        """엣지 케이스 테스트"""
        edge_cases = [
            # 빈 문자열 답변
            {"Q1": "", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            # None 값
            {"Q1": None, "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            # 숫자 값
            {"Q1": "1", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            # 공백 문자
            {"Q1": " A ", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
        ]

        for i, answers in enumerate(edge_cases):
            with self.subTest(case=i):
                # 이러한 케이스들은 모두 에러를 발생시켜야 함
                errors = AnswerValidator.validate_answers(answers)
                self.assertGreater(len(errors), 0, f"Edge case {i} should produce errors")

    def test_validator_performance(self):
        """검증 성능 테스트"""
        import time

        valid_answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}

        start_time = time.time()

        # 1000번 검증 실행
        for _ in range(1000):
            AnswerValidator.validate_answers(valid_answers)

        end_time = time.time()
        execution_time = end_time - start_time

        # 1000번 검증이 0.1초 이내에 완료되어야 함
        self.assertLess(execution_time, 0.1, f"1000번 검증에 {execution_time:.3f}초 소요")

    def test_error_message_quality(self):
        """에러 메시지 품질 테스트"""
        # 누락된 질문에 대한 명확한 메시지
        incomplete_answers = {"Q1": "A"}
        errors = AnswerValidator.validate_answers(incomplete_answers)

        missing_msg = errors["missing_questions"][0]
        self.assertIn("다음 질문에 답변해주세요", missing_msg)
        self.assertIn("Q2, Q3, Q4, Q5, Q6", missing_msg)

        # 잘못된 선택지에 대한 명확한 메시지
        invalid_answers = {"Q1": "X", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}
        errors = AnswerValidator.validate_answers(invalid_answers)

        invalid_msg = errors["Q1"][0]
        self.assertIn("유효한 선택지는", invalid_msg)
        self.assertIn("A, B", invalid_msg)
