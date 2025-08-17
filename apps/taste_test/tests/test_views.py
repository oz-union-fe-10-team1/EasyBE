# tests/test_views.py
"""
API 뷰 테스트 (새로운 모듈 구조 반영)
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import PreferenceTestResult
from ..services import TasteTestService

User = get_user_model()


class TasteTestAPITest(APITestCase):
    """API 뷰 테스트 (새로운 컨트롤러 패턴)"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")
        self.client.force_authenticate(user=self.user)

    def test_get_questions(self):
        """질문 목록 조회 테스트 - 새로운 컨트롤러 패턴"""
        url = reverse("taste_test:questions")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        self.assertIn("카페에", response.data[0]["question"])

        # 새로운 뷰 구조에서도 동일한 응답 형식 유지
        self.assertIn("id", response.data[0])
        self.assertIn("options", response.data[0])

    def test_submit_answers_success(self):
        """답변 제출 성공 테스트 - DRF 표준 패턴"""
        url = reverse("taste_test:submit")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("type", response.data)
        self.assertIn("scores", response.data)
        self.assertIn("info", response.data)
        self.assertIn("saved", response.data)

        # 이미지 정보 확인 - 절대 URL 형식
        self.assertIn("image_url", response.data["info"])
        image_url = response.data["info"]["image_url"]
        self.assertTrue(image_url.startswith(("http://", "https://")))
        self.assertTrue(image_url.endswith(".png"))
        self.assertIn("/static/types/", image_url)
        self.assertTrue(response.data["saved"])  # 로그인한 상태이므로 저장됨

    def test_submit_answers_validation_error(self):
        """답변 제출 검증 에러 테스트 - Serializer 검증"""
        url = reverse("taste_test:submit")

        # 누락된 답변
        data = {"answers": {"Q1": "A", "Q2": "B"}}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 새로운 DRF 패턴에서는 serializer.errors 형식
        self.assertIn("answers", response.data)

    def test_submit_answers_without_auth(self):
        """인증 없이 답변 제출 테스트"""
        self.client.force_authenticate(user=None)  # 인증 해제

        url = reverse("taste_test:submit")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("type", response.data)
        self.assertIn("saved", response.data)
        self.assertFalse(response.data["saved"])  # 로그인 안했으므로 저장 안됨

    def test_get_profile_with_result(self):
        """프로필 조회 (테스트 결과 있음) - 새로운 서비스 패턴"""
        PreferenceTestResult.objects.create(
            user=self.user,
            answers={"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            prefer_taste="SWEET_FRUIT",
        )

        url = reverse("taste_test:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_test"])

        # 새로운 ControllerService.get_user_profile_data 구조 확인
        self.assertEqual(response.data["prefer_taste"], "SWEET_FRUIT")
        self.assertIn("id", response.data)
        self.assertIn("taste_description", response.data)
        self.assertIn("image_url", response.data)
        self.assertIn("prefer_taste_display", response.data)
        self.assertIn("created_at", response.data)

        # 이미지 URL 형식 확인
        image_url = response.data["image_url"]
        self.assertTrue(image_url.startswith(("http://", "https://")))
        self.assertTrue(image_url.endswith(".png"))

    def test_get_profile_without_result(self):
        """프로필 조회 (테스트 결과 없음)"""
        url = reverse("taste_test:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_test"])

        # 테스트 결과 관련 필드들이 없어야 함
        self.assertNotIn("id", response.data)
        self.assertNotIn("prefer_taste", response.data)
        self.assertNotIn("taste_description", response.data)

    def test_get_types(self):
        """취향 유형 목록 테스트 - 새로운 ControllerService.get_taste_types_data"""
        url = reverse("taste_test:types")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 9)
        self.assertEqual(len(response.data["types"]), 9)

        # 각 타입에 이미지 정보가 포함되어 있는지 확인
        for taste_type in response.data["types"]:
            self.assertIn("image_url", taste_type)
            self.assertIn("name", taste_type)
            self.assertIn("description", taste_type)
            self.assertIn("characteristics", taste_type)

            # 이미지 URL 형식 확인
            image_url = taste_type["image_url"]
            self.assertTrue(image_url.startswith(("http://", "https://")))
            self.assertTrue(image_url.endswith(".png"))
            self.assertIn("/static/types/", image_url)

    def test_retake_success(self):
        """재테스트 성공 - DRF 표준 패턴"""
        # 기존 결과 생성
        PreferenceTestResult.objects.create(
            user=self.user,
            answers={"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            prefer_taste="SWEET_FRUIT",
        )

        url = reverse("taste_test:retake")
        data = {"answers": {"Q1": "B", "Q2": "A", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "A"}}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("type", response.data)
        self.assertIn("info", response.data)
        self.assertIn("saved", response.data)
        self.assertTrue(response.data["saved"])

        # 이미지 정보 확인 - 절대 URL 형식
        self.assertIn("image_url", response.data["info"])
        image_url = response.data["info"]["image_url"]
        self.assertTrue(image_url.startswith(("http://", "https://")))
        self.assertTrue(image_url.endswith(".png"))

    def test_retake_no_existing_result(self):
        """재테스트 - 기존 결과 없음"""
        url = reverse("taste_test:retake")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("message", response.data)

    def test_retake_validation_error(self):
        """재테스트 검증 에러 - Serializer 검증"""
        # 기존 결과 생성
        PreferenceTestResult.objects.create(
            user=self.user,
            answers={"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            prefer_taste="SWEET_FRUIT",
        )

        url = reverse("taste_test:retake")
        # 잘못된 답변 데이터
        data = {"answers": {"Q1": "C", "Q2": "B"}}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # DRF 표준 패턴에서는 serializer.errors 형식
        self.assertIn("answers", response.data)

    def test_submit_invalid_answers(self):
        """잘못된 답변 제출 테스트 - Serializer 검증"""
        url = reverse("taste_test:submit")

        # 부족한 답변
        data = {"answers": {"Q1": "A", "Q2": "B"}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answers", response.data)

        # 잘못된 선택지
        data = {"answers": {"Q1": "C", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("answers", response.data)

    def test_profile_unauthenticated(self):
        """인증 없이 프로필 조회 시 401 에러"""
        self.client.force_authenticate(user=None)
        url = reverse("taste_test:profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retake_unauthenticated(self):
        """인증 없이 재테스트 시 401 에러"""
        self.client.force_authenticate(user=None)
        url = reverse("taste_test:retake")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_questions_anonymous_access(self):
        """질문 목록 익명 접근 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("taste_test:questions")
        response = self.client.get(url)

        # AllowAny 권한이므로 익명 사용자도 접근 가능
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_types_anonymous_access(self):
        """취향 유형 목록 익명 접근 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("taste_test:types")
        response = self.client.get(url)

        # AllowAny 권한이므로 익명 사용자도 접근 가능
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TasteTestViewFlowTest(APITestCase):
    """뷰 플로우 통합 테스트 - 새로운 컨트롤러 패턴"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")

    def test_complete_test_flow_authenticated(self):
        """완전한 테스트 플로우 - 인증된 사용자"""
        self.client.force_authenticate(user=self.user)

        # 1. 질문 조회
        questions_url = reverse("taste_test:questions")
        questions_response = self.client.get(questions_url)
        self.assertEqual(questions_response.status_code, status.HTTP_200_OK)

        # 2. 답변 제출
        submit_url = reverse("taste_test:submit")
        submit_data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}}
        submit_response = self.client.post(submit_url, submit_data, format="json")
        self.assertEqual(submit_response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(submit_response.data["saved"])

        # 3. 프로필 조회 (결과 포함)
        profile_url = reverse("taste_test:profile")
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertTrue(profile_response.data["has_test"])

        # 4. 재테스트
        retake_url = reverse("taste_test:retake")
        retake_data = {"answers": {"Q1": "B", "Q2": "A", "Q3": "B", "Q4": "A", "Q5": "B", "Q6": "B"}}
        retake_response = self.client.put(retake_url, retake_data, format="json")
        self.assertEqual(retake_response.status_code, status.HTTP_200_OK)
        self.assertTrue(retake_response.data["saved"])

    def test_complete_test_flow_anonymous(self):
        """완전한 테스트 플로우 - 익명 사용자"""
        # 익명 사용자 (인증 안함)

        # 1. 질문 조회 (익명 가능)
        questions_url = reverse("taste_test:questions")
        questions_response = self.client.get(questions_url)
        self.assertEqual(questions_response.status_code, status.HTTP_200_OK)

        # 2. 답변 제출 (익명 가능, 저장 안됨)
        submit_url = reverse("taste_test:submit")
        submit_data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}}
        submit_response = self.client.post(submit_url, submit_data, format="json")
        self.assertEqual(submit_response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(submit_response.data["saved"])

        # 3. 취향 유형 목록 조회 (익명 가능)
        types_url = reverse("taste_test:types")
        types_response = self.client.get(types_url)
        self.assertEqual(types_response.status_code, status.HTTP_200_OK)

        # 4. 프로필 조회 (익명 불가)
        profile_url = reverse("taste_test:profile")
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_401_UNAUTHORIZED)


class TasteTestViewDataConsistencyTest(APITestCase):
    """뷰 데이터 일관성 테스트 - 새로운 서비스 패턴"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")
        self.client.force_authenticate(user=self.user)

    def test_service_view_data_consistency(self):
        """서비스와 뷰 데이터 일관성 확인"""
        answers = {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}

        # 서비스에서 직접 호출
        service_result = TasteTestService.process_taste_test(answers)

        # API를 통해 호출
        url = reverse("taste_test:submit")
        api_response = self.client.post(url, {"answers": answers}, format="json")

        # 결과 비교 (saved 필드 제외)
        api_data = api_response.data.copy()
        api_data.pop("saved", None)

        self.assertEqual(service_result["type"], api_data["type"])
        self.assertEqual(service_result["scores"], api_data["scores"])
        self.assertEqual(service_result["info"], api_data["info"])

    def test_image_url_consistency_across_endpoints(self):
        """모든 엔드포인트에서 이미지 URL 일관성 확인"""
        # 테스트 결과 생성
        PreferenceTestResult.objects.create(
            user=self.user,
            answers={"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"},
            prefer_taste="SWEET_FRUIT",
        )

        # 1. 답변 제출에서 이미지 URL
        submit_url = reverse("taste_test:submit")
        submit_response = self.client.post(
            submit_url, {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}}, format="json"
        )
        submit_image_url = submit_response.data["info"]["image_url"]

        # 2. 프로필에서 이미지 URL
        profile_url = reverse("taste_test:profile")
        profile_response = self.client.get(profile_url)
        profile_image_url = profile_response.data["image_url"]

        # 3. 취향 유형 목록에서 해당 유형의 이미지 URL
        types_url = reverse("taste_test:types")
        types_response = self.client.get(types_url)
        sweet_fruit_type = next((t for t in types_response.data["types"] if t["enum"] == "SWEET_FRUIT"), None)
        types_image_url = sweet_fruit_type["image_url"] if sweet_fruit_type else None

        # 모든 이미지 URL이 동일해야 함
        self.assertEqual(submit_image_url, profile_image_url)
        self.assertEqual(profile_image_url, types_image_url)

        # 서비스 메서드와도 일치해야 함
        service_image_url = TasteTestService.get_image_url_by_enum("SWEET_FRUIT")
        self.assertEqual(profile_image_url, service_image_url)
