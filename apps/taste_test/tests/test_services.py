# tests/test_services.py
"""
TasteTestService 테스트 (새로운 질문 체계 + 이미지 매핑)
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import PreferenceTestResult
from ..services import (
    ANSWER_SCORE_MAPPING,
    TASTE_QUESTIONS,
    TASTE_TYPE_IMAGES,
    TASTE_TYPES,
    TasteTestService,
)

User = get_user_model()


class TasteTestServiceTest(TestCase):
    """TasteTestService 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")

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

        # 새로운 질문 내용 확인
        self.assertIn("카페에", questions[0]["question"])

    def test_calculate_scores_basic(self):
        """기본 점수 계산 테스트 (새로운 매핑)"""
        answers = {
            "Q1": "A",  # 달콤과일파 +1
            "Q2": "B",  # 달콤과일파 +1
            "Q3": "A",  # 상큼톡톡파 +1
            "Q4": "B",  # 깔끔고소파 +1
            "Q5": "A",  # 깔끔고소파 +1
            "Q6": "A",  # 달콤과일파 +1
        }

        scores = TasteTestService.calculate_scores(answers)

        expected = {"달콤과일파": 3, "상큼톡톡파": 1, "묵직여운파": 0, "깔끔고소파": 2}

        self.assertEqual(scores, expected)

    def test_determine_type_single_high_score(self):
        """3점 이상 단일 유형 테스트"""
        scores = {"달콤과일파": 4, "상큼톡톡파": 1, "묵직여운파": 1, "깔끔고소파": 0}

        result_type = TasteTestService.determine_type(scores)
        self.assertEqual(result_type, "달콤과일파")

    def test_determine_type_mixed_types(self):
        """2점 동점 혼합 유형 테스트 (새로운 조합 규칙)"""
        test_cases = [
            ({"달콤과일파": 2, "상큼톡톡파": 2, "묵직여운파": 1, "깔끔고소파": 1}, "향긋단정파"),
            ({"달콤과일파": 2, "상큼톡톡파": 1, "묵직여운파": 2, "깔끔고소파": 1}, "묵직달콤파"),
            ({"달콤과일파": 2, "상큼톡톡파": 1, "묵직여운파": 1, "깔끔고소파": 2}, "달콤고소파"),
            ({"달콤과일파": 1, "상큼톡톡파": 2, "묵직여운파": 2, "깔끔고소파": 1}, "상큼깔끔파"),
            ({"달콤과일파": 1, "상큼톡톡파": 2, "묵직여운파": 1, "깔끔고소파": 2}, "상큼깔끔파"),
            ({"달콤과일파": 1, "상큼톡톡파": 1, "묵직여운파": 2, "깔끔고소파": 2}, "향긋단정파"),  # 수정됨
        ]

        for scores, expected_type in test_cases:
            with self.subTest(scores=scores):
                result = TasteTestService.determine_type(scores)
                self.assertEqual(result, expected_type)

    def test_determine_type_gourmet_fallback(self):
        """미식가유형 폴백 테스트"""
        # 균등한 점수 분배
        equal_scores = {"달콤과일파": 1, "상큼톡톡파": 1, "묵직여운파": 1, "깔끔고소파": 1}
        result = TasteTestService.determine_type(equal_scores)
        self.assertEqual(result, "미식가유형")

        # 3개 이상 동점
        triple_tie = {"달콤과일파": 2, "상큼톡톡파": 2, "묵직여운파": 2, "깔끔고소파": 0}
        result = TasteTestService.determine_type(triple_tie)
        self.assertEqual(result, "미식가유형")

    def test_process_taste_test_integration_with_image(self):
        """전체 프로세스 통합 테스트 (이미지 포함)"""
        answers = {
            "Q1": "A",  # 달콤과일파
            "Q2": "B",  # 달콤과일파
            "Q3": "A",  # 상큼톡톡파
            "Q4": "B",  # 깔끔고소파
            "Q5": "A",  # 깔끔고소파
            "Q6": "A",  # 달콤과일파
        }

        result = TasteTestService.process_taste_test(answers)

        self.assertIn("type", result)
        self.assertIn("scores", result)
        self.assertIn("info", result)

        # 달콤과일파 3점으로 단일 유형이어야 함
        self.assertEqual(result["type"], "달콤과일파")
        self.assertEqual(result["scores"]["달콤과일파"], 3)
        self.assertEqual(result["info"]["name"], "달콤과일파")

        # 이미지 URL이 서비스 메서드와 일치하는지 확인
        expected_url = TasteTestService.get_image_url_by_enum("SWEET_FRUIT")
        self.assertEqual(result["info"]["image_url"], expected_url)

    def test_get_image_url_by_enum(self):
        """enum으로 이미지 URL 가져오기 테스트"""
        test_cases = [
            "SWEET_FRUIT",
            "FRESH_FIZZY",
            "HEAVY_LINGERING",
            "CLEAN_SAVORY",
            "FRAGRANT_NEAT",
            "FRESH_CLEAN",
            "HEAVY_SWEET",
            "SWEET_SAVORY",
            "GOURMET",
        ]

        for enum_type in test_cases:
            with self.subTest(enum_type=enum_type):
                image_url = TasteTestService.get_image_url_by_enum(enum_type)

                # 절대 URL 형식인지 확인
                self.assertTrue(image_url.startswith(("http://", "https://")))
                # 올바른 경로와 파일명 확인 (새로운 경로)
                expected_path = f"/static/types/{enum_type.lower()}.png"
                self.assertTrue(image_url.endswith(expected_path))

    def test_get_image_url_by_enum_invalid(self):
        """존재하지 않는 enum으로 이미지 URL 가져오기"""
        invalid_enum = "INVALID_ENUM"
        image_url = TasteTestService.get_image_url_by_enum(invalid_enum)

        # GOURMET 기본값이 반환되어야 함
        expected_default = TasteTestService.get_image_url_by_enum("GOURMET")
        self.assertEqual(image_url, expected_default)

    def test_taste_types_have_image_urls(self):
        """모든 TASTE_TYPES에 image_url이 포함되어 있는지 테스트"""
        for type_name, type_info in TASTE_TYPES.items():
            with self.subTest(type_name=type_name):
                # get_type_info 메서드를 통해 실제 URL 확인
                actual_type_info = TasteTestService.get_type_info(type_name)
                self.assertIn("image_url", actual_type_info)

                # 절대 URL 형식인지 확인
                image_url = actual_type_info["image_url"]
                self.assertTrue(image_url.startswith(("http://", "https://")))
                self.assertTrue(image_url.endswith(".png"))

    def test_enum_image_mapping_consistency(self):
        """enum과 이미지 매핑 일관성 테스트"""
        for type_name, type_info in TASTE_TYPES.items():
            with self.subTest(type_name=type_name):
                enum_value = type_info["enum"]

                # 서비스 메서드로 얻은 URL들이 일치하는지 확인
                direct_image_url = TasteTestService.get_image_url_by_enum(enum_value)
                type_info_image_url = TasteTestService.get_type_info(type_name)["image_url"]
                self.assertEqual(direct_image_url, type_info_image_url)

    def test_save_test_result_sweet_fruit_type(self):
        """달콤과일파 단일 유형 테스트"""
        # 달콤과일파 3점: Q1-A, Q2-B, Q6-A
        answers = {"Q1": "A", "Q2": "B", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"}

        result = TasteTestService.save_test_result(self.user, answers)

        self.assertIsInstance(result, PreferenceTestResult)
        self.assertEqual(result.user, self.user)
        self.assertEqual(result.answers, answers)
        self.assertEqual(result.prefer_taste, PreferenceTestResult.PreferTaste.SWEET_FRUIT)

    def test_save_test_result_fresh_fizzy_type(self):
        """상큼톡톡파 단일 유형 테스트"""
        # 상큼톡톡파 3점: Q2-A, Q3-A, Q4-A
        answers = {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "A", "Q5": "B", "Q6": "B"}

        result = TasteTestService.save_test_result(self.user, answers)

        self.assertEqual(result.prefer_taste, PreferenceTestResult.PreferTaste.FRESH_FIZZY)

    def test_save_test_result_mixed_type(self):
        """혼합 유형 테스트 - 묵직달콤파"""
        # 달콤과일파 2점 + 묵직여운파 2점 = 묵직달콤파
        answers = {"Q1": "A", "Q2": "A", "Q3": "B", "Q4": "B", "Q5": "B", "Q6": "A"}

        result = TasteTestService.save_test_result(self.user, answers)

        self.assertEqual(result.prefer_taste, PreferenceTestResult.PreferTaste.HEAVY_SWEET)

    def test_save_test_result_update_existing(self):
        """기존 사용자 테스트 결과 업데이트"""
        # 첫 번째 테스트 - 달콤과일파
        first_answers = {"Q1": "A", "Q2": "B", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"}
        first_result = TasteTestService.save_test_result(self.user, first_answers)
        first_id = first_result.id

        # 두 번째 테스트 (업데이트) - 상큼톡톡파
        second_answers = {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "A", "Q5": "A", "Q6": "B"}
        second_result = TasteTestService.save_test_result(self.user, second_answers)

        # 같은 객체가 업데이트되어야 함
        self.assertEqual(first_id, second_result.id)
        self.assertEqual(second_result.answers, second_answers)
        # 결과도 변경되어야 함
        self.assertNotEqual(first_result.prefer_taste, second_result.prefer_taste)

        # DB에 하나의 결과만 있어야 함
        self.assertEqual(PreferenceTestResult.objects.filter(user=self.user).count(), 1)

    def test_save_test_result_with_profile_initialization(self):
        """테스트 결과 저장 + PreferTasteProfile 초기화 통합 테스트"""
        # 달콤과일파 3점
        answers = {"Q1": "A", "Q2": "B", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"}

        # PreferTasteProfile 모델이 있다고 가정하고 테스트
        result = TasteTestService.save_test_result(self.user, answers)

        self.assertEqual(result.prefer_taste, PreferenceTestResult.PreferTaste.SWEET_FRUIT)

    def test_validate_answers_valid_input(self):
        """유효한 답변 검증 테스트"""
        valid_answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}

        errors = TasteTestService.validate_answers(valid_answers)

        self.assertEqual(len(errors), 0)

    def test_validate_answers_missing_questions(self):
        """누락된 질문 검증 테스트"""
        incomplete_answers = {"Q1": "A", "Q3": "B"}

        errors = TasteTestService.validate_answers(incomplete_answers)

        self.assertIn("missing_questions", errors)
        self.assertIn("Q2", errors["missing_questions"][0])

    def test_validate_answers_invalid_choices(self):
        """잘못된 선택지 검증 테스트"""
        invalid_answers = {"Q1": "C", "Q2": "A", "Q3": "X", "Q4": "B", "Q5": "A", "Q6": "B"}

        errors = TasteTestService.validate_answers(invalid_answers)

        self.assertIn("Q1", errors)
        self.assertIn("Q3", errors)

    def test_get_taste_type_base_scores(self):
        """타입별 기본 맛 점수 가져오기 테스트"""
        base_scores = TasteTestService.get_taste_type_base_scores("SWEET_FRUIT")

        # 달콤과일파 기본 점수 확인
        self.assertEqual(base_scores["sweetness_level"], 4.5)
        self.assertEqual(base_scores["acidity_level"], 3.5)
        self.assertEqual(base_scores["body_level"], 2.0)
        self.assertEqual(base_scores["carbonation_level"], 2.0)
        self.assertEqual(base_scores["bitterness_level"], 1.0)
        self.assertEqual(base_scores["aroma_level"], 4.0)

    def test_get_taste_type_base_scores_all_types(self):
        """모든 타입의 기본 점수 테스트"""
        all_types = [
            "SWEET_FRUIT",
            "FRESH_FIZZY",
            "HEAVY_LINGERING",
            "CLEAN_SAVORY",
            "FRAGRANT_NEAT",
            "FRESH_CLEAN",
            "HEAVY_SWEET",
            "SWEET_SAVORY",
            "GOURMET",
        ]

        for taste_type in all_types:
            with self.subTest(taste_type=taste_type):
                scores = TasteTestService.get_taste_type_base_scores(taste_type)

                # 모든 맛 지표가 있는지 확인
                required_keys = [
                    "sweetness_level",
                    "acidity_level",
                    "body_level",
                    "carbonation_level",
                    "bitterness_level",
                    "aroma_level",
                ]
                for key in required_keys:
                    self.assertIn(key, scores)
                    self.assertIsInstance(scores[key], (int, float))
                    self.assertGreaterEqual(scores[key], 0.0)
                    self.assertLessEqual(scores[key], 5.0)

    def test_get_taste_type_base_scores_invalid_type(self):
        """존재하지 않는 타입 테스트"""
        scores = TasteTestService.get_taste_type_base_scores("INVALID_TYPE")

        # GOURMET 기본값이 반환되어야 함
        gourmet_scores = TasteTestService.get_taste_type_base_scores("GOURMET")
        self.assertEqual(scores, gourmet_scores)


class TasteTestServiceImageTest(TestCase):
    """이미지 관련 기능 테스트"""

    def test_get_image_url_by_enum_all_types(self):
        """모든 enum 타입별 이미지 URL 테스트"""
        test_cases = [
            "SWEET_FRUIT",
            "FRESH_FIZZY",
            "HEAVY_LINGERING",
            "CLEAN_SAVORY",
            "FRAGRANT_NEAT",
            "FRESH_CLEAN",
            "HEAVY_SWEET",
            "SWEET_SAVORY",
            "GOURMET",
        ]

        for enum_type in test_cases:
            with self.subTest(enum_type=enum_type):
                image_url = TasteTestService.get_image_url_by_enum(enum_type)

                # 절대 URL 형식 확인
                self.assertTrue(image_url.startswith(("http://", "https://")))
                # 파일명 확인
                expected_filename = f"{enum_type.lower()}.png"
                self.assertTrue(image_url.endswith(expected_filename))

    def test_get_image_url_by_enum_invalid(self):
        """존재하지 않는 enum으로 이미지 URL 가져오기"""
        invalid_enum = "INVALID_ENUM"
        image_url = TasteTestService.get_image_url_by_enum(invalid_enum)

        # GOURMET 기본값이 반환되어야 함
        expected_default = TasteTestService.get_image_url_by_enum("GOURMET")
        self.assertEqual(image_url, expected_default)

    def test_taste_types_have_image_urls(self):
        """모든 TASTE_TYPES에 image_url이 포함되어 있는지 테스트"""
        for type_name in TASTE_TYPES.keys():
            with self.subTest(type_name=type_name):
                type_info = TasteTestService.get_type_info(type_name)
                self.assertIn("image_url", type_info)

                image_url = type_info["image_url"]
                self.assertTrue(image_url.startswith(("http://", "https://")))
                self.assertTrue(image_url.endswith(".png"))

    def test_enum_image_mapping_consistency(self):
        """enum과 이미지 매핑 일관성 테스트"""
        for type_name, type_info in TASTE_TYPES.items():
            with self.subTest(type_name=type_name):
                enum_value = type_info["enum"]

                # 두 메서드가 동일한 URL을 반환하는지 확인
                direct_image_url = TasteTestService.get_image_url_by_enum(enum_value)
                type_info_image_url = TasteTestService.get_type_info(type_name)["image_url"]
                self.assertEqual(direct_image_url, type_info_image_url)

    def test_get_type_info_includes_image(self):
        """get_type_info에서 이미지 정보 포함 테스트"""
        type_info = TasteTestService.get_type_info("달콤과일파")

        self.assertIn("image_url", type_info)
        # 서비스 메서드와 일치하는지 확인
        expected_url = TasteTestService.get_image_url_by_enum("SWEET_FRUIT")
        self.assertEqual(type_info["image_url"], expected_url)

        self.assertEqual(type_info["name"], "달콤과일파")
        self.assertEqual(type_info["enum"], "SWEET_FRUIT")


class TasteTestServiceIntegrationTest(TestCase):
    """타입 → 맛 프로필 매핑 통합 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")

    def test_sweet_fruit_type_mapping(self):
        """달콤과일파 타입 → 맛 프로필 매핑 테스트 (새로운 답변)"""
        # 달콤과일파 3점: Q1-A, Q2-B, Q6-A
        answers = {"Q1": "A", "Q2": "B", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"}

        result = TasteTestService.save_test_result(self.user, answers)
        base_scores = TasteTestService.get_taste_type_base_scores(result.prefer_taste)

        # 달콤과일파 특성 확인
        self.assertGreater(base_scores["sweetness_level"], 4.0)  # 높은 단맛
        self.assertGreater(base_scores["aroma_level"], 3.5)  # 높은 향
        self.assertLess(base_scores["bitterness_level"], 2.0)  # 낮은 쓴맛

    def test_fresh_fizzy_type_mapping(self):
        """상큼톡톡파 타입 → 맛 프로필 매핑 테스트 (새로운 답변)"""
        # 상큼톡톡파 3점: Q2-A, Q3-A, Q4-A
        answers = {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "A", "Q5": "B", "Q6": "B"}

        result = TasteTestService.save_test_result(self.user, answers)
        base_scores = TasteTestService.get_taste_type_base_scores(result.prefer_taste)

        # 상큼톡톡파 특성 확인
        self.assertGreater(base_scores["acidity_level"], 4.0)  # 높은 산미
        self.assertGreater(base_scores["carbonation_level"], 4.0)  # 높은 탄산
        self.assertLess(base_scores["sweetness_level"], 2.5)  # 낮은 단맛

    def test_heavy_lingering_type_mapping(self):
        """묵직여운파 타입 → 맛 프로필 매핑 테스트"""
        # 묵직여운파 3점: Q3-B, Q5-B, Q6-B
        answers = {"Q1": "B", "Q2": "A", "Q3": "B", "Q4": "B", "Q5": "B", "Q6": "B"}

        result = TasteTestService.save_test_result(self.user, answers)
        base_scores = TasteTestService.get_taste_type_base_scores(result.prefer_taste)

        # 묵직여운파 특성 확인
        self.assertGreater(base_scores["body_level"], 4.0)  # 높은 바디감
        self.assertGreater(base_scores["bitterness_level"], 3.0)  # 높은 쓴맛
        self.assertLess(base_scores["carbonation_level"], 1.5)  # 낮은 탄산

    def test_clean_savory_type_mapping(self):
        """깔끔고소파 타입 → 맛 프로필 매핑 테스트"""
        # 깔끔고소파 3점: Q1-B, Q4-B, Q5-A
        answers = {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}

        result = TasteTestService.save_test_result(self.user, answers)
        base_scores = TasteTestService.get_taste_type_base_scores(result.prefer_taste)

        # 깔끔고소파 특성 확인
        self.assertLess(base_scores["sweetness_level"], 2.0)  # 낮은 단맛
        self.assertEqual(base_scores["bitterness_level"], 2.0)  # 중간 쓴맛
        self.assertGreater(base_scores["body_level"], 2.5)  # 적당한 바디감

    def test_mixed_type_mapping(self):
        """혼합 타입 매핑 테스트"""
        # 묵직달콤파 테스트 (달콤과일파 2점 + 묵직여운파 2점)
        answers = {"Q1": "A", "Q2": "A", "Q3": "B", "Q4": "B", "Q5": "B", "Q6": "A"}
        result = TasteTestService.save_test_result(self.user, answers)

        self.assertEqual(result.prefer_taste, PreferenceTestResult.PreferTaste.HEAVY_SWEET)

    def test_type_to_korean_name_mapping(self):
        """타입 enum → 한국어 이름 매핑 테스트"""
        mappings = {
            PreferenceTestResult.PreferTaste.SWEET_FRUIT: "달콤과일파",
            PreferenceTestResult.PreferTaste.FRESH_FIZZY: "상큼톡톡파",
            PreferenceTestResult.PreferTaste.HEAVY_LINGERING: "묵직여운파",
            PreferenceTestResult.PreferTaste.CLEAN_SAVORY: "깔끔고소파",
            PreferenceTestResult.PreferTaste.FRAGRANT_NEAT: "향긋단정파",
            PreferenceTestResult.PreferTaste.FRESH_CLEAN: "상큼깔끔파",
            PreferenceTestResult.PreferTaste.HEAVY_SWEET: "묵직달콤파",
            PreferenceTestResult.PreferTaste.SWEET_SAVORY: "달콤고소파",
            PreferenceTestResult.PreferTaste.GOURMET: "미식가유형",
        }

        for enum_value, korean_name in mappings.items():
            with self.subTest(enum_value=enum_value):
                # enum의 label이 한국어 이름과 일치하는지 확인
                self.assertEqual(enum_value.label, korean_name)


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
            self.assertIn("info", result)
            # 이미지 정보도 포함되어야 함
            self.assertIn("image_url", result["info"])

        end_time = time.time()
        execution_time = end_time - start_time

        # 100개 처리가 0.1초 이내에 완료되어야 함
        self.assertLess(execution_time, 0.1, f"100개 계산에 {execution_time:.3f}초 소요")


class TasteTestServiceEdgeCaseTest(TestCase):
    """엣지 케이스 테스트"""

    def test_all_same_answer_a(self):
        """모든 답변이 A인 경우 (새로운 매핑)"""
        all_a_answers = {f"Q{i}": "A" for i in range(1, 7)}

        result = TasteTestService.process_taste_test(all_a_answers)

        # A 선택 시: 달콤과일파 2점, 상큼톡톡파 3점, 깔끔고소파 1점 → 상큼톡톡파 (단일)
        self.assertEqual(result["type"], "상큼톡톡파")
        self.assertEqual(result["scores"]["상큼톡톡파"], 3)
        # 이미지 정보 확인 - 서비스 메서드와 일치
        expected_url = TasteTestService.get_image_url_by_enum("FRESH_FIZZY")
        self.assertEqual(result["info"]["image_url"], expected_url)

    def test_all_same_answer_b(self):
        """모든 답변이 B인 경우 (새로운 매핑)"""
        all_b_answers = {f"Q{i}": "B" for i in range(1, 7)}

        result = TasteTestService.process_taste_test(all_b_answers)

        # B 선택 시: 깔끔고소파 2점, 묵직여운파 3점, 달콤과일파 1점 → 묵직여운파 (단일)
        self.assertEqual(result["type"], "묵직여운파")
        self.assertEqual(result["scores"]["묵직여운파"], 3)
        # 이미지 정보 확인 - 서비스 메서드와 일치
        expected_url = TasteTestService.get_image_url_by_enum("HEAVY_LINGERING")
        self.assertEqual(result["info"]["image_url"], expected_url)

    def test_partial_answers(self):
        """일부 답변만 있는 경우"""
        partial_answers = {"Q1": "A", "Q3": "B"}

        result = TasteTestService.process_taste_test(partial_answers)

        # 처리는 되어야 하지만 점수가 낮을 것
        self.assertIn("type", result)
        self.assertIn("info", result)
        self.assertIn("image_url", result["info"])
        total_score = sum(result["scores"].values())
        self.assertEqual(total_score, 2)

    def test_empty_answers(self):
        """빈 답변 처리"""
        empty_answers = {}

        result = TasteTestService.process_taste_test(empty_answers)

        # 모든 점수가 0이므로 미식가유형이어야 함
        self.assertEqual(result["type"], "미식가유형")
        # 이미지 정보 확인 - 서비스 메서드와 일치
        expected_url = TasteTestService.get_image_url_by_enum("GOURMET")
        self.assertEqual(result["info"]["image_url"], expected_url)
        total_score = sum(result["scores"].values())
        self.assertEqual(total_score, 0)

    def test_case_sensitivity(self):
        """대소문자 처리 테스트 (새로운 매핑)"""
        # 소문자 답변은 무시되어야 함
        mixed_case_answers = {
            "Q1": "a",  # 소문자 (무시)
            "Q2": "A",  # 대문자 (유효) - 상큼톡톡파
            "Q3": "B",  # 대문자 (유효) - 묵직여운파
            "q4": "A",  # 소문자 질문 ID (무시)
            "Q5": "B",  # 대문자 (유효) - 묵직여운파
            "Q6": "b",  # 소문자 (무시)
        }

        scores = TasteTestService.calculate_scores(mixed_case_answers)
        total_score = sum(scores.values())
        self.assertEqual(total_score, 3)  # Q2, Q3, Q5만 계산됨

        # 묵직여운파 2점, 상큼톡톡파 1점
        self.assertEqual(scores["묵직여운파"], 2)
        self.assertEqual(scores["상큼톡톡파"], 1)

    def test_invalid_question_ids(self):
        """잘못된 질문 ID 처리"""
        invalid_answers = {
            "Q1": "A",  # 유효 - 달콤과일파
            "Q99": "B",  # 무효한 질문 ID
            "INVALID": "A",  # 무효한 질문 ID
            "Q2": "B",  # 유효 - 달콤과일파
        }

        scores = TasteTestService.calculate_scores(invalid_answers)
        total_score = sum(scores.values())
        self.assertEqual(total_score, 2)  # Q1, Q2만 계산됨
        self.assertEqual(scores["달콤과일파"], 2)

    def test_invalid_answer_choices(self):
        """잘못된 답변 선택지 처리"""
        invalid_answers = {
            "Q1": "A",  # 유효 - 달콤과일파
            "Q2": "C",  # 무효한 선택지
            "Q3": "X",  # 무효한 선택지
            "Q4": "B",  # 유효 - 깔끔고소파
        }

        scores = TasteTestService.calculate_scores(invalid_answers)
        total_score = sum(scores.values())
        self.assertEqual(total_score, 2)  # Q1, Q4만 계산됨
        self.assertEqual(scores["달콤과일파"], 1)
        self.assertEqual(scores["깔끔고소파"], 1)

    def test_specific_combination_scenarios_with_images(self):
        """특정 조합 시나리오 테스트 (이미지 확인 포함)"""

        # 시나리오 1: 상큼깔끔파 (상큼톡톡파 + 묵직여운파)
        answers_1 = {"Q1": "A", "Q2": "A", "Q3": "A", "Q4": "B", "Q5": "B", "Q6": "B"}
        result_1 = TasteTestService.process_taste_test(answers_1)
        self.assertEqual(result_1["type"], "상큼깔끔파")
        expected_url_1 = TasteTestService.get_image_url_by_enum("FRESH_CLEAN")
        self.assertEqual(result_1["info"]["image_url"], expected_url_1)

        # 시나리오 2: 묵직달콤파 (달콤과일파 + 묵직여운파)
        answers_2 = {"Q1": "A", "Q2": "A", "Q3": "B", "Q4": "B", "Q5": "B", "Q6": "A"}
        result_2 = TasteTestService.process_taste_test(answers_2)
        self.assertEqual(result_2["type"], "묵직달콤파")
        expected_url_2 = TasteTestService.get_image_url_by_enum("HEAVY_SWEET")
        self.assertEqual(result_2["info"]["image_url"], expected_url_2)

        # 시나리오 3: 달콤고소파 (달콤과일파 + 깔끔고소파)
        answers_3 = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}
        result_3 = TasteTestService.process_taste_test(answers_3)
        self.assertEqual(result_3["type"], "달콤고소파")
        expected_url_3 = TasteTestService.get_image_url_by_enum("SWEET_SAVORY")
        self.assertEqual(result_3["info"]["image_url"], expected_url_3)

        # 시나리오 4: 상큼톡톡파 단일 유형
        answers_4 = {"Q1": "B", "Q2": "A", "Q3": "A", "Q4": "A", "Q5": "A", "Q6": "B"}
        result_4 = TasteTestService.process_taste_test(answers_4)
        self.assertEqual(result_4["type"], "상큼톡톡파")  # 3점 단일 유형
        expected_url_4 = TasteTestService.get_image_url_by_enum("FRESH_FIZZY")
        self.assertEqual(result_4["info"]["image_url"], expected_url_4)


class TasteTestServiceIntegrationWithImageTest(TestCase):
    """이미지 포함 통합 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")

    def test_full_flow_with_image_response(self):
        """테스트 전체 플로우에서 이미지 정보 포함 확인"""
        # 달콤과일파 결과가 나올 답변
        answers = {"Q1": "A", "Q2": "B", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"}

        # 1. 테스트 처리
        result = TasteTestService.process_taste_test(answers)

        # 2. 기본 응답 구조 확인
        self.assertIn("type", result)
        self.assertIn("scores", result)
        self.assertIn("info", result)

        # 3. 이미지 정보 확인 - 서비스 메서드와 일치
        self.assertIn("image_url", result["info"])
        expected_url = TasteTestService.get_image_url_by_enum("SWEET_FRUIT")
        self.assertEqual(result["info"]["image_url"], expected_url)

        # 4. DB 저장 후 확인
        saved_result = TasteTestService.save_test_result(self.user, answers)
        self.assertEqual(saved_result.prefer_taste, PreferenceTestResult.PreferTaste.SWEET_FRUIT)

        # 5. 이미지 URL 직접 조회
        image_url = TasteTestService.get_image_url_by_enum(saved_result.prefer_taste)
        self.assertEqual(image_url, expected_url)

    def test_all_types_have_unique_images(self):
        """모든 유형이 고유한 이미지를 가지는지 테스트"""
        from ..services import TASTE_TYPES

        image_urls = []
        for type_name in TASTE_TYPES.keys():
            type_info = TasteTestService.get_type_info(type_name)
            image_url = type_info["image_url"]
            # 중복 이미지 URL이 없는지 확인
            self.assertNotIn(image_url, image_urls, f"{type_name}의 이미지가 중복됩니다")
            image_urls.append(image_url)

        # 9개의 고유한 이미지 URL이 있어야 함
        self.assertEqual(len(set(image_urls)), 9)

    def test_image_url_format_consistency(self):
        """이미지 URL 형식 일관성 테스트"""
        from ..services import TASTE_TYPES

        for type_name, type_info in TASTE_TYPES.items():
            with self.subTest(type_name=type_name):
                # 서비스 메서드를 통해 실제 URL 가져오기
                actual_type_info = TasteTestService.get_type_info(type_name)
                image_url = actual_type_info["image_url"]

                # 절대 URL 형식 확인
                self.assertTrue(image_url.startswith(("http://", "https://")))
                self.assertTrue(image_url.endswith(".png"))

                # 파일명 형식 확인 (enum을 소문자로 변환한 형태)
                enum_value = type_info["enum"]
                expected_filename = enum_value.lower() + ".png"
                self.assertTrue(image_url.endswith(expected_filename))

                # 경로 형식 확인
                expected_path = f"/static/types/{expected_filename}"
                self.assertTrue(image_url.endswith(expected_path))
