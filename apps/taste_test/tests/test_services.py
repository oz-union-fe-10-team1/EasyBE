# tests/test_services.py
"""
TasteTestService 테스트
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..services import TasteTestService, TASTE_QUESTIONS, ANSWER_SCORE_MAPPING
from ..models import TasteTestResult

User = get_user_model()


class TasteTestServiceTest(TestCase):
    """TasteTestService 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com"
        )

    def test_get_questions(self):
        """질문 목록 반환 테스트"""
        questions = TasteTestService.get_questions()

        self.assertEqual(len(questions), 6)
        self.assertEqual(questions[0]["id"], "Q1")
        self.assertIn("question", questions[0])
        self.assertIn("options", questions[0])
        self.assertEqual(len(questions[0]["options"]), 2)
        self.assertIn("A", questions[0]["options"])
        self.assertIn("B", questions[0]["options"])

    def test_calculate_scores_basic(self):
        """기본 점수 계산 테스트"""
        answers = {
            "Q1": "A",  # 달콤과일파 +1
            "Q2": "B",  # 달콤과일파 +1
            "Q3": "A",  # 상큼톡톡파 +1
            "Q4": "A",  # 묵직여운파 +1
            "Q5": "A",  # 깔끔고소파 +1
            "Q6": "A"  # 달콤과일파 +1
        }

        scores = TasteTestService.calculate_scores(answers)

        expected = {
            "달콤과일파": 3,
            "상큼톡톡파": 1,
            "묵직여운파": 1,
            "깔끔고소파": 1
        }

        self.assertEqual(scores, expected)

    def test_calculate_scores_empty(self):
        """빈 답변 점수 계산 테스트"""
        scores = TasteTestService.calculate_scores({})

        expected = {
            "달콤과일파": 0,
            "상큼톡톡파": 0,
            "묵직여운파": 0,
            "깔끔고소파": 0
        }

        self.assertEqual(scores, expected)

    def test_calculate_scores_invalid_answers(self):
        """잘못된 답변 무시 테스트"""
        answers = {
            "Q1": "A",  # 달콤과일파 +1 (유효)
            "Q2": "X",  # 무효한 선택지 (무시)
            "Q7": "A",  # 존재하지 않는 질문 (무시)
        }

        scores = TasteTestService.calculate_scores(answers)

        expected = {
            "달콤과일파": 1,
            "상큼톡톡파": 0,
            "묵직여운파": 0,
            "깔끔고소파": 0
        }

        self.assertEqual(scores, expected)

    def test_determine_type_single_high_score(self):
        """3점 이상 단일 유형 테스트"""
        scores = {
            "달콤과일파": 4,
            "상큼톡톡파": 1,
            "묵직여운파": 1,
            "깔끔고소파": 0
        }

        result_type = TasteTestService.determine_type(scores)
        self.assertEqual(result_type, "달콤과일파")

    def test_determine_type_mixed_two_types(self):
        """2점 동점 혼합 유형 테스트"""
        test_cases = [
            ({"달콤과일파": 2, "상큼톡톡파": 2, "묵직여운파": 1, "깔끔고소파": 1}, "상큼깔끔파"),
            ({"달콤과일파": 2, "상큼톡톡파": 1, "묵직여운파": 2, "깔끔고소파": 1}, "묵직달콤파"),
            ({"달콤과일파": 2, "상큼톡톡파": 1, "묵직여운파": 1, "깔끔고소파": 2}, "달콤고소파"),
            ({"달콤과일파": 1, "상큼톡톡파": 2, "묵직여운파": 2, "깔끔고소파": 1}, "향긋단정파"),
            ({"달콤과일파": 1, "상큼톡톡파": 2, "묵직여운파": 1, "깔끔고소파": 2}, "상큼깔끔파"),
            ({"달콤과일파": 1, "상큼톡톡파": 1, "묵직여운파": 2, "깔끔고소파": 2}, "향긋단정파"),
        ]

        for scores, expected_type in test_cases:
            with self.subTest(scores=scores):
                result = TasteTestService.determine_type(scores)
                self.assertEqual(result, expected_type)

    def test_determine_type_gourmet_balanced(self):
        """균형잡힌 미식가 유형 테스트"""
        test_cases = [
            # 2:2:2 균형
            {"달콤과일파": 2, "상큼톡톡파": 2, "묵직여운파": 2, "깔끔고소파": 0},
            # 1:1:1:1 균형
            {"달콤과일파": 1, "상큼톡톡파": 1, "묵직여운파": 1, "깔끔고소파": 1},
            # 전체 0점
            {"달콤과일파": 0, "상큼톡톡파": 0, "묵직여운파": 0, "깔끔고소파": 0},
        ]

        for scores in test_cases:
            with self.subTest(scores=scores):
                result = TasteTestService.determine_type(scores)
                self.assertEqual(result, "미식가유형")

    def test_get_type_info(self):
        """유형 정보 반환 테스트"""
        info = TasteTestService.get_type_info("달콤과일파")

        self.assertIn("name", info)
        self.assertIn("description", info)
        self.assertIn("characteristics", info)
        self.assertEqual(info["name"], "달콤과일파")
        self.assertIsInstance(info["characteristics"], list)
        self.assertGreater(len(info["description"]), 0)

    def test_get_type_info_invalid(self):
        """존재하지 않는 유형 테스트"""
        info = TasteTestService.get_type_info("존재하지않는유형")
        self.assertEqual(info["name"], "미식가유형")

    def test_process_taste_test_integration(self):
        """전체 프로세스 통합 테스트"""
        answers = {
            "Q1": "A",  # 달콤과일파
            "Q2": "B",  # 달콤과일파
            "Q3": "A",  # 상큼톡톡파
            "Q4": "B",  # 상큼톡톡파
            "Q5": "A",  # 깔끔고소파
            "Q6": "A"  # 달콤과일파
        }

        result = TasteTestService.process_taste_test(answers)

        self.assertIn("type", result)
        self.assertIn("scores", result)
        self.assertIn("info", result)

        # 달콤과일파 3점으로 단일 유형이어야 함
        self.assertEqual(result["type"], "달콤과일파")
        self.assertEqual(result["scores"]["달콤과일파"], 3)
        self.assertEqual(result["info"]["name"], "달콤과일파")

    def test_validate_answers_valid(self):
        """유효한 답변 검증 테스트"""
        valid_answers = {
            "Q1": "A",
            "Q2": "B",
            "Q3": "A",
            "Q4": "B",
            "Q5": "A",
            "Q6": "B"
        }

        errors = TasteTestService.validate_answers(valid_answers)
        self.assertEqual(errors, {})

    def test_validate_answers_missing_questions(self):
        """누락된 질문 검증 테스트"""
        incomplete_answers = {
            "Q1": "A",
            "Q2": "B"
            # Q3, Q4, Q5, Q6 누락
        }

        errors = TasteTestService.validate_answers(incomplete_answers)
        self.assertIn("missing_questions", errors)
        self.assertIn("Q3", errors["missing_questions"][0])

    def test_validate_answers_extra_questions(self):
        """추가 질문 검증 테스트"""
        answers_with_extra = {
            "Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B",
            "Q7": "A"  # 존재하지 않는 질문
        }

        errors = TasteTestService.validate_answers(answers_with_extra)
        self.assertIn("extra_questions", errors)
        self.assertIn("Q7", errors["extra_questions"][0])

    def test_validate_answers_invalid_choices(self):
        """잘못된 선택지 검증 테스트"""
        invalid_answers = {
            "Q1": "C",  # A, B만 유효
            "Q2": "B",
            "Q3": "A",
            "Q4": "B",
            "Q5": "X",  # A, B만 유효
            "Q6": "B"
        }

        errors = TasteTestService.validate_answers(invalid_answers)
        self.assertIn("Q1", errors)
        self.assertIn("Q5", errors)
        self.assertIn("A, B", errors["Q1"][0])

    def test_save_test_result_new_user(self):
        """새 사용자 테스트 결과 저장"""
        answers = {
            "Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"
        }

        result = TasteTestService.save_test_result(self.user, answers)

        self.assertIsInstance(result, TasteTestResult)
        self.assertEqual(result.user, self.user)
        self.assertEqual(result.answers, answers)
        self.assertEqual(result.taste_type, TasteTestResult.TasteType.SWEET_FRUIT)
        self.assertIsInstance(result.scores, dict)

    def test_save_test_result_update_existing(self):
        """기존 사용자 테스트 결과 업데이트"""
        # 첫 번째 테스트
        first_answers = {
            "Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"
        }
        first_result = TasteTestService.save_test_result(self.user, first_answers)
        first_id = first_result.id

        # 두 번째 테스트 (업데이트)
        second_answers = {
            "Q1": "B", "Q2": "A", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"
        }
        second_result = TasteTestService.save_test_result(self.user, second_answers)

        # 같은 객체가 업데이트되어야 함
        self.assertEqual(first_id, second_result.id)
        self.assertEqual(second_result.answers, second_answers)

        # DB에 하나의 결과만 있어야 함
        self.assertEqual(TasteTestResult.objects.filter(user=self.user).count(), 1)


class TasteTestServiceScenarioTest(TestCase):
    """실제 사용 시나리오 테스트"""

    def test_scenario_sweet_lover(self):
        """달콤한 맛을 좋아하는 사용자 시나리오"""
        answers = {
            "Q1": "A",  # 은은한 향기 (달콤과일파)
            "Q2": "B",  # 달콤한 여운 (달콤과일파)
            "Q5": "B",  # 과일향기 (달콤과일파)
            "Q6": "A",  # 강렬한 술 (달콤과일파)
            "Q3": "A",  # 실패없는 맛 (상큼톡톡파)
            "Q4": "B"  # 가벼운 목넘김 (상큼톡톡파)
        }

        result = TasteTestService.process_taste_test(answers)
        self.assertEqual(result["type"], "달콤과일파")  # 4점으로 단일 유형

    def test_scenario_balanced_user(self):
        """균형잡힌 사용자 시나리오"""
        answers = {
            "Q1": "A",  # 달콤과일파 +1
            "Q2": "A",  # 상큼톡톡파 +1
            "Q3": "A",  # 상큼톡톡파 +1 (총 2점)
            "Q4": "A",  # 묵직여운파 +1
            "Q5": "A",  # 깔끔고소파 +1
            "Q6": "B"  # 묵직여운파 +1 (총 2점)
        }

        result = TasteTestService.process_taste_test(answers)
        # 상큼톡톡파(2) + 묵직여운파(2) = 향긋단정파
        self.assertEqual(result["type"], "향긋단정파")

    def test_scenario_mixed_sweet_clean(self):
        """달콤고소파 혼합 유형 시나리오"""
        answers = {
            "Q1": "A",  # 달콤과일파 +1
            "Q2": "B",  # 달콤과일파 +1 (총 2점)
            "Q3": "B",  # 깔끔고소파 +1
            "Q4": "B",  # 상큼톡톡파 +1
            "Q5": "A",  # 깔끔고소파 +1 (총 2점)
            "Q6": "B"  # 묵직여운파 +1
        }

        result = TasteTestService.process_taste_test(answers)
        # 달콤과일파(2) + 깔끔고소파(2) = 달콤고소파
        self.assertEqual(result["type"], "달콤고소파")

    def test_scenario_gourmet_type(self):
        """미식가 유형 시나리오"""
        answers = {
            "Q1": "A",  # 달콤과일파 +1
            "Q2": "A",  # 상큼톡톡파 +1
            "Q3": "B",  # 깔끔고소파 +1
            "Q4": "A",  # 묵직여운파 +1
            "Q5": "B",  # 달콤과일파 +1 (총 2점)
            "Q6": "B"  # 묵직여운파 +1 (총 2점)
        }

        result = TasteTestService.process_taste_test(answers)
        # 달콤과일파(2), 묵직여운파(2), 상큼톡톡파(1), 깔끔고소파(1)
        # 2점 동점이지만 달콤과일파+묵직여운파 = 묵직달콤파
        self.assertEqual(result["type"], "묵직달콤파")


class TasteTestServicePerformanceTest(TestCase):
    """성능 테스트"""

    def test_large_scale_processing(self):
        """대량 처리 성능 테스트"""
        import time

        test_cases = []
        for i in range(100):
            answers = {
                "Q1": "A" if i % 2 == 0 else "B",
                "Q2": "A" if i % 3 == 0 else "B",
                "Q3": "A" if i % 5 == 0 else "B",
                "Q4": "A" if i % 7 == 0 else "B",
                "Q5": "A" if i % 11 == 0 else "B",
                "Q6": "A" if i % 13 == 0 else "B",
            }
            test_cases.append(answers)

        start_time = time.time()

        for answers in test_cases:
            result = TasteTestService.process_taste_test(answers)
            self.assertIn("type", result)

        end_time = time.time()
        execution_time = end_time - start_time

        # 100개 처리가 0.1초 이내에 완료되어야 함
        self.assertLess(execution_time, 0.1, f"100개 계산에 {execution_time:.3f}초 소요")


class TasteTestServiceEdgeCaseTest(TestCase):
    """엣지 케이스 테스트"""

    def test_all_same_answer(self):
        """모든 답변이 같은 경우"""
        all_a_answers = {f"Q{i}": "A" for i in range(1, 7)}
        all_b_answers = {f"Q{i}": "B" for i in range(1, 7)}

        result_a = TasteTestService.process_taste_test(all_a_answers)
        result_b = TasteTestService.process_taste_test(all_b_answers)

        # 결과가 미식가유형이 아닌 특정 유형이어야 함
        self.assertNotEqual(result_a["type"], "미식가유형")
        self.assertNotEqual(result_b["type"], "미식가유형")

    def test_partial_answers(self):
        """일부 답변만 있는 경우"""
        partial_answers = {"Q1": "A", "Q3": "B"}

        result = TasteTestService.process_taste_test(partial_answers)

        # 처리는 되어야 하지만 점수가 낮을 것
        self.assertIn("type", result)
        total_score = sum(result["scores"].values())
        self.assertEqual(total_score, 2)

    def test_case_sensitivity(self):
        """대소문자 처리 테스트"""
        # 소문자 답변은 무시되어야 함
        mixed_case_answers = {
            "Q1": "a",  # 소문자 (무시)
            "Q2": "A",  # 대문자 (유효)
            "Q3": "B",  # 대문자 (유효)
            "q4": "A",  # 소문자 질문 ID (무시)
            "Q5": "B",  # 대문자 (유효)
            "Q6": "b"  # 소문자 (무시)
        }

        scores = TasteTestService.calculate_scores(mixed_case_answers)
        total_score = sum(scores.values())
        self.assertEqual(total_score, 3)  # Q2, Q3, Q5만 계산됨


if __name__ == "__main__":
    # pytest로 실행할 수 있도록
    pytest.main([__file__])