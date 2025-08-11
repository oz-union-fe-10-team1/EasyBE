# tests/test_views.py
"""
API 뷰 테스트 (오류 수정)
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
        # Token 대신 force_authenticate 사용
        self.client.force_authenticate(user=self.user)

    def test_get_questions(self):
        """질문 목록 조회 테스트"""
        url = reverse("taste_test:questions")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 6)
        self.assertIn("카페에", response.data[0]["question"])

    def test_submit_answers_success(self):
        """답변 제출 성공 테스트 (이미지 정보 포함)"""
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
        """인증 없이 답변 제출 테스트 (AllowAny이므로 가능)"""
        self.client.force_authenticate(user=None)  # 인증 해제

        url = reverse("taste_test:submit")
        # 완전한 답변 데이터로 수정
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}

        response = self.client.post(url, data, format="json")

        # AllowAny 권한이므로 성공해야 함 (단, 저장은 안됨)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("type", response.data)
        self.assertIn("saved", response.data)
        self.assertFalse(response.data["saved"])  # 로그인 안했으므로 저장 안됨

    def test_get_result_success(self):
        """결과 조회 성공 테스트 (이미지 정보 포함)"""
        # 먼저 테스트 결과 생성
        PreferenceTestResult.objects.create(user=self.user, answers={"Q1": "A", "Q2": "B"}, prefer_taste="SWEET_FRUIT")

        url = reverse("taste_test:result")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["prefer_taste"], "SWEET_FRUIT")

        # 이미지 정보 확인 (serializer에서 추가됨)
        self.assertIn("image_url", response.data)
        self.assertIn("type_info", response.data)

    def test_get_result_not_found(self):
        """결과 없을 때 테스트"""
        url = reverse("taste_test:result")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_profile_with_result(self):
        """프로필 조회 (테스트 결과 있음)"""
        PreferenceTestResult.objects.create(user=self.user, answers={"Q1": "A"}, prefer_taste="SWEET_FRUIT")

        url = reverse("taste_test:profile")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # views.py에서 has_test로 되어있음 (has_test_result가 아님)
        self.assertTrue(response.data["has_test"])
        self.assertIn("result", response.data)

    def test_get_types(self):
        """취향 유형 목록 테스트"""
        url = reverse("taste_test:types")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total"], 9)
        # views.py에서 types로 되어있음 (taste_types가 아님)
        self.assertEqual(len(response.data["types"]), 9)

        # 각 타입에 이미지 정보가 포함되어 있는지 확인
        for taste_type in response.data["types"]:
            self.assertIn("image_url", taste_type)

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
        # 이미지 정보 확인
        self.assertIn("image_url", response.data["info"])

    def test_retake_no_existing_result(self):
        """재테스트 - 기존 결과 없음"""
        # 기존 결과를 삭제해서 없는 상태로 만들기
        PreferenceTestResult.objects.filter(user=self.user).delete()

        url = reverse("taste_test:retake")
        data = {"answers": {"Q1": "A", "Q2": "B", "Q3": "A", "Q4": "B", "Q5": "A", "Q6": "B"}}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
