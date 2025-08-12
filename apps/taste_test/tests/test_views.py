# tests/test_views.py
"""
API 뷰 테스트 (최적화된 버전)
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import PreferenceTestResult

User = get_user_model()


class TasteTestAPITest(APITestCase):
    """API 뷰 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")
        self.client.force_authenticate(user=self.user)

    def test_get_questions(self):
        """질문 목록 조회 테스트"""
        url = reverse("taste_test:questions")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        self.assertIn("카페에", response.data[0]["question"])

    def test_submit_answers_success(self):
        """답변 제출 성공 테스트"""
        url = reverse("taste_test:submit")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "A"}}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("type", response.data)
        self.assertIn("scores", response.data)
        self.assertIn("info", response.data)
        self.assertIn("saved", response.data)

        # 이미지 정보 확인
        self.assertIn("image_url", response.data["info"])
        self.assertTrue(response.data["info"]["image_url"].startswith("images/types/"))
        self.assertTrue(response.data["saved"])  # 로그인한 상태이므로 저장됨

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
        """프로필 조회 (테스트 결과 있음) - 완전한 결과 포함"""
        PreferenceTestResult.objects.create(
            user=self.user,
            answers={"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"},
            prefer_taste="SWEET_FRUIT",
        )

        url = reverse("taste_test:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_test"])
        self.assertIn("result", response.data)

        # 완전한 테스트 결과 확인
        result = response.data["result"]
        self.assertEqual(result["prefer_taste"], "SWEET_FRUIT")
        self.assertIn("answers", result)  # 답변 내역 포함
        self.assertIn("taste_description", result)
        self.assertIn("image_url", result)
        self.assertIn("type_info", result)

    def test_get_profile_without_result(self):
        """프로필 조회 (테스트 결과 없음)"""
        url = reverse("taste_test:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_test"])
        self.assertNotIn("result", response.data)

    def test_get_types(self):
        """취향 유형 목록 테스트"""
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

    def test_retake_success(self):
        """재테스트 성공"""
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

        # 이미지 정보 확인
        self.assertIn("image_url", response.data["info"])

    def test_retake_no_existing_result(self):
        """재테스트 - 기존 결과 없음"""
        url = reverse("taste_test:retake")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("message", response.data)

    def test_submit_invalid_answers(self):
        """잘못된 답변 제출 테스트"""
        url = reverse("taste_test:submit")

        # 부족한 답변
        data = {"answers": {"Q1": "A", "Q2": "B"}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 잘못된 선택지
        data = {"answers": {"Q1": "C", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

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
