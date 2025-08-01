# apps/taste_test/tests/test_taste_logic.py

from django.test import TestCase

from apps.taste_test.models import TasteAnswer, TasteQuestion, TasteTest, TasteType
from apps.taste_test.services import TasteScoreCalculator
from apps.users.models import User


class TasteTestLogicTests(TestCase):
    """실제 6문항 테스트 로직 검증 - TDD 방식"""

    def setUp(self):
        """실제 6개 질문 테스트 데이터 준비"""
        self.test = TasteTest.objects.create(
            title="나만의 전통주 취향 찾기",
            description="몇 가지 질문을 통해 당신에게 맞는 전통주 유형을 찾아보세요!",
            is_active=True,
        )

        # 실제 6개 질문 생성
        self.setup_real_questions()

    def setup_real_questions(self):
        """실제 테스트 문항 설정"""

        # Q1: 카페에 가면 주로 시키는 메뉴는?
        self.q1 = TasteQuestion.objects.create(
            test=self.test, question_text="카페에 가면 주로 시키는 메뉴는?", sequence=1
        )
        self.q1_a = TasteAnswer.objects.create(
            question=self.q1, answer_text="달콤한 바닐라 라떼나 과일 에이드", score_vector={"달콤과일": 1}
        )
        self.q1_b = TasteAnswer.objects.create(
            question=self.q1, answer_text="깔끔한 아메리카노나 고소한 곡물 라떼", score_vector={"깔끔고소": 1}
        )

        # Q2: 둘 중 더 좋아하는 과일 스타일은?
        self.q2 = TasteQuestion.objects.create(
            test=self.test, question_text="둘 중 더 좋아하는 과일 스타일은?", sequence=2
        )
        self.q2_a = TasteAnswer.objects.create(
            question=self.q2, answer_text="침이 고이는 레몬,유자,자몽", score_vector={"상큼톡톡": 1}
        )
        self.q2_b = TasteAnswer.objects.create(
            question=self.q2, answer_text="잘 익은 달콤한 수박,복숭아", score_vector={"달콤과일": 1}
        )

        # Q3: 디저트를 딱 하나만 고른다면?
        self.q3 = TasteQuestion.objects.create(test=self.test, question_text="디저트를 딱 하나만 고른다면?", sequence=3)
        self.q3_a = TasteAnswer.objects.create(
            question=self.q3,
            answer_text="입안이 상쾌해지는 과일 소르베나 요거트 아이스크림",
            score_vector={"상큼톡톡": 1},
        )
        self.q3_b = TasteAnswer.objects.create(
            question=self.q3,
            answer_text="커피나 위스키가 생각나는 진한 치즈케이크나 티라미수",
            score_vector={"목적여운": 1},
        )

        # Q4: 평소 즐겨 마시는 음료는?
        self.q4 = TasteQuestion.objects.create(test=self.test, question_text="평소 즐겨 마시는 음료는?", sequence=4)
        self.q4_a = TasteAnswer.objects.create(
            question=self.q4, answer_text="톡 쏘는 탄산수나 상큼한 콤부차", score_vector={"상큼톡톡": 1}
        )
        self.q4_b = TasteAnswer.objects.create(
            question=self.q4, answer_text="시원하고 깔끔한 보리차나 녹차", score_vector={"깔끔고소": 1}
        )

        # Q5: 맛있는 식사 후, 입안의 마무리는?
        self.q5 = TasteQuestion.objects.create(
            test=self.test, question_text="맛있는 식사 후, 입안의 마무리는?", sequence=5
        )
        self.q5_a = TasteAnswer.objects.create(
            question=self.q5, answer_text="입안이 싹 정리되는 깔끔한 느낌", score_vector={"깔끔고소": 1}
        )
        self.q5_b = TasteAnswer.objects.create(
            question=self.q5, answer_text="맛의 여운이 은은하게 남는 느낌", score_vector={"목적여운": 1}
        )

        # Q6: 특별한 날을 기념하기 위해, 술을 고른다면?
        self.q6 = TasteQuestion.objects.create(
            test=self.test, question_text="특별한 날을 기념하기 위해, 술을 고른다면?", sequence=6
        )
        self.q6_a = TasteAnswer.objects.create(
            question=self.q6, answer_text="달콤해서 파티 분위기를 띄워주는 술", score_vector={"달콤과일": 1}
        )
        self.q6_b = TasteAnswer.objects.create(
            question=self.q6, answer_text="오랜 시간 숙성되어 깊고 진한 풍미를 가진 술", score_vector={"목적여운": 1}
        )

    def test_달콤과일_순수형(self):
        """달콤과일 3점 → 순수형 달콤과일 결과"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_b.id},  # 달콤과일 +1
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_a.id},  # 깔끔고소 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1
        ]
        # 예상: 달콤과일 3점, 상큼톡톡 1점, 깔끔고소 2점 → 달콤과일 승

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["primary_type"], "달콤과일")
        self.assertEqual(result["type_count"], 1)  # 순수형
        self.assertEqual(scores["달콤과일"], 3)
        print(f"달콤과일 순수형: {result}, 점수: {scores}")

    def test_상큼톡톡_순수형(self):
        """상큼톡톡 3점 → 순수형 상큼톡톡 결과"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_b.id},  # 깔끔고소 +1
            {"question_id": 2, "answer_id": self.q2_a.id},  # 상큼톡톡 +1
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_a.id},  # 상큼톡톡 +1
            {"question_id": 5, "answer_id": self.q5_a.id},  # 깔끔고소 +1
            {"question_id": 6, "answer_id": self.q6_b.id},  # 목적여운 +1
        ]
        # 예상: 상큼톡톡 3점, 깔끔고소 2점, 목적여운 1점 → 상큼톡톡 승

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["primary_type"], "상큼톡톡")
        self.assertEqual(result["type_count"], 1)  # 순수형
        self.assertEqual(scores["상큼톡톡"], 3)
        print(f"상큼톡톡 순수형: {result}, 점수: {scores}")

    def test_혼합형_결과(self):
        """2개 유형이 동점 → 혼합형"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_a.id},  # 상큼톡톡 +1
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_b.id},  # 목적여운 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1
        ]
        # 예상: 달콤과일 2점, 상큼톡톡 2점, 깔끔고소 1점, 목적여운 1점
        # → 달콤과일 × 상큼톡톡 혼합형

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["type_count"], 2)  # 혼합형
        self.assertIn("×", result["primary_type"])  # 혼합 표시
        self.assertEqual(scores["달콤과일"], 2)
        self.assertEqual(scores["상큼톡톡"], 2)
        print(f"혼합형 결과: {result}, 점수: {scores}")

    def test_미식가_조건(self):
        """4개 유형 중 3개가 2점 이상 → 미식가"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_b.id},  # 달콤과일 +1 (총2점)
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_a.id},  # 상큼톡톡 +1 (총2점)
            {"question_id": 5, "answer_id": self.q5_b.id},  # 목적여운 +1
            {"question_id": 6, "answer_id": self.q6_b.id},  # 목적여운 +1 (총2점)
        ]
        # 예상: 달콤과일 2점, 상큼톡톡 2점, 목적여운 2점, 깔끔고소 0점
        # → 3개가 2점 이상이므로 미식가

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["primary_type"], "미식가")
        self.assertEqual(result["type_count"], 1)  # 미식가도 단일 결과
        # 3개 유형이 2점 이상인지 확인
        basic_types = ["달콤과일", "상큼톡톡", "목적여운", "깔끔고소"]
        two_plus_count = sum(1 for t in basic_types if scores[t] >= 2)
        self.assertGreaterEqual(two_plus_count, 3)
        print(f"미식가 결과: {result}, 점수: {scores}")

    def test_점수_계산_정확성(self):
        """점수 계산이 정확한지 검증"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_a.id},  # 상큼톡톡 +1
            {"question_id": 3, "answer_id": self.q3_b.id},  # 목적여운 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_a.id},  # 깔끔고소 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1
        ]

        scores = TasteScoreCalculator.calculate_scores(answers)

        # 예상 점수 검증
        self.assertEqual(scores["달콤과일"], 2)  # q1_a + q6_a
        self.assertEqual(scores["상큼톡톡"], 1)  # q2_a
        self.assertEqual(scores["목적여운"], 1)  # q3_b
        self.assertEqual(scores["깔끔고소"], 2)  # q4_b + q5_a
        self.assertEqual(scores["미식가"], 0)  # 없음

        print(f"점수 정확성 검증: {scores}")

    def test_목적여운_순수형(self):
        """목적여운 3점 → 순수형 목적여운 결과"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_b.id},  # 깔끔고소 +1
            {"question_id": 2, "answer_id": self.q2_a.id},  # 상큼톡톡 +1
            {"question_id": 3, "answer_id": self.q3_b.id},  # 목적여운 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_b.id},  # 목적여운 +1
            {"question_id": 6, "answer_id": self.q6_b.id},  # 목적여운 +1
        ]
        # 예상: 목적여운 3점, 깔끔고소 2점, 상큼톡톡 1점 → 목적여운 승

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["primary_type"], "목적여운")
        self.assertEqual(result["type_count"], 1)  # 순수형
        self.assertEqual(scores["목적여운"], 3)
        print(f"목적여운 순수형: {result}, 점수: {scores}")

    def test_깔끔고소_순수형(self):
        """깔끔고소 3점 → 순수형 깔끔고소 결과"""
        answers = [
            {"question_id": 1, "answer_id": self.q1_b.id},  # 깔끔고소 +1
            {"question_id": 2, "answer_id": self.q2_a.id},  # 상큼톡톡 +1
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_a.id},  # 깔끔고소 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1
        ]
        # 예상: 깔끔고소 3점, 상큼톡톡 2점, 달콤과일 1점 → 깔끔고소 승

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["primary_type"], "깔끔고소")
        self.assertEqual(result["type_count"], 1)  # 순수형
        self.assertEqual(scores["깔끔고소"], 3)
        print(f"깔끔고소 순수형: {result}, 점수: {scores}")

    def test_모든_0점_기본값(self):
        """모든 점수가 0점인 경우 기본값 처리"""
        # 빈 score_vector 답변 생성
        empty_answer = TasteAnswer.objects.create(question=self.q1, answer_text="테스트용 빈 답변", score_vector={})

        answers = [
            {"question_id": 1, "answer_id": empty_answer.id},  # 0점
            {"question_id": 2, "answer_id": empty_answer.id},  # 0점
            {"question_id": 3, "answer_id": empty_answer.id},  # 0점
            {"question_id": 4, "answer_id": empty_answer.id},  # 0점
            {"question_id": 5, "answer_id": empty_answer.id},  # 0점
            {"question_id": 6, "answer_id": empty_answer.id},  # 0점
        ]

        scores = TasteScoreCalculator.calculate_scores(answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        # 기본값 처리되어야 함
        self.assertEqual(result["primary_type"], "깔끔고소")  # 기본값
        self.assertEqual(result["type_count"], 1)
        self.assertEqual(result["confidence"], 0.3)  # 낮은 신뢰도
        print(f"기본값 처리: {result}, 점수: {scores}")

    def test_실제_플로우차트_시나리오들(self):
        """실제 플로우차트의 모든 가능한 경로 테스트"""

        # 가장 대표적인 시나리오들
        scenarios = [
            {
                "name": "달콤과일 매니아",
                "path": "A-B-B-B-B-A",  # 플로우차트 경로
                "answers": [self.q1_a.id, self.q2_b.id, self.q3_b.id, self.q4_b.id, self.q5_b.id, self.q6_a.id],
                "expected_winner": "달콤과일",
            },
            {
                "name": "상큼톡톡 청량파",
                "path": "B-A-A-A-A-B",
                "answers": [self.q1_b.id, self.q2_a.id, self.q3_a.id, self.q4_a.id, self.q5_a.id, self.q6_b.id],
                "expected_winner": "상큼톡톡",
            },
            {
                "name": "목적여운 탐험가",
                "path": "B-A-B-B-B-B",
                "answers": [self.q1_b.id, self.q2_a.id, self.q3_b.id, self.q4_b.id, self.q5_b.id, self.q6_b.id],
                "expected_winner": "목적여운",
            },
        ]

        for scenario in scenarios:
            with self.subTest(scenario=scenario["name"]):
                answers = [
                    {"question_id": i + 1, "answer_id": answer_id} for i, answer_id in enumerate(scenario["answers"])
                ]

                scores = TasteScoreCalculator.calculate_scores(answers)
                result = TasteScoreCalculator.determine_result_type(scores)

                print(f"\n=== {scenario['name']} ({scenario['path']}) ===")
                print(f"결과: {result['primary_type']}")
                print(f"점수: {scores}")
                print(f"신뢰도: {result['confidence']:.2f}")

                # 예상 승자 확인 (미식가가 아닌 경우)
                if result["primary_type"] != "미식가" and "×" not in result["primary_type"]:
                    max_score_type = max([k for k in scores.keys() if k != "미식가"], key=lambda x: scores[x])
                    self.assertEqual(max_score_type, scenario["expected_winner"])

    def test_경계값_테스트(self):
        """미식가 조건의 경계값 테스트"""

        # Case 1: 정확히 3개가 2점 (미식가 조건 만족)
        answers_boundary_pass = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_b.id},  # 달콤과일 +1 (총2점)
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_a.id},  # 상큼톡톡 +1 (총2점)
            {"question_id": 5, "answer_id": self.q5_b.id},  # 목적여운 +1
            {"question_id": 6, "answer_id": self.q6_b.id},  # 목적여운 +1 (총2점)
        ]

        scores = TasteScoreCalculator.calculate_scores(answers_boundary_pass)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertEqual(result["primary_type"], "미식가")
        print(f"경계값 통과 (3개가 2점): {result}, 점수: {scores}")

        # Case 2: 2개만 2점 (미식가 조건 불만족)
        answers_boundary_fail = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_b.id},  # 달콤과일 +1 (총2점)
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_a.id},  # 상큼톡톡 +1 (총2점)
            {"question_id": 5, "answer_id": self.q5_a.id},  # 깔끔고소 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1 (총3점)
        ]

        scores = TasteScoreCalculator.calculate_scores(answers_boundary_fail)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertNotEqual(result["primary_type"], "미식가")
        self.assertEqual(result["primary_type"], "달콤과일")  # 최고점
        print(f"경계값 실패 (2개만 2점): {result}, 점수: {scores}")

    def test_신뢰도_계산(self):
        """신뢰도 점수 계산 검증"""

        # 고신뢰도: 한 유형이 압도적
        high_confidence_answers = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_b.id},  # 달콤과일 +1
            {"question_id": 3, "answer_id": self.q3_b.id},  # 목적여운 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_a.id},  # 깔끔고소 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1
        ]
        # 달콤과일 3점으로 압도적

        scores = TasteScoreCalculator.calculate_scores(high_confidence_answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertGreater(result["confidence"], 0.7)  # 높은 신뢰도
        print(f"고신뢰도 케이스: 신뢰도 {result['confidence']:.2f}")

        # 저신뢰도: 혼합형
        low_confidence_answers = [
            {"question_id": 1, "answer_id": self.q1_a.id},  # 달콤과일 +1
            {"question_id": 2, "answer_id": self.q2_a.id},  # 상큼톡톡 +1
            {"question_id": 3, "answer_id": self.q3_a.id},  # 상큼톡톡 +1
            {"question_id": 4, "answer_id": self.q4_b.id},  # 깔끔고소 +1
            {"question_id": 5, "answer_id": self.q5_b.id},  # 목적여운 +1
            {"question_id": 6, "answer_id": self.q6_a.id},  # 달콤과일 +1
        ]
        # 달콤과일 2점, 상큼톡톡 2점 동점 → 혼합형

        scores = TasteScoreCalculator.calculate_scores(low_confidence_answers)
        result = TasteScoreCalculator.determine_result_type(scores)

        self.assertLess(result["confidence"], 0.7)  # 낮은 신뢰도
        self.assertEqual(result["type_count"], 2)  # 혼합형
        print(f"저신뢰도 케이스 (혼합형): 신뢰도 {result['confidence']:.2f}")
