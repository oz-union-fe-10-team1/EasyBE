# apps/users/tests/test_models.py

from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.users.models import PreferTasteProfile
from apps.users.utils.taste_analysis import TasteAnalysisService

User = get_user_model()


class PreferTasteProfileModelTest(TestCase):
    """PreferTasteProfile 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")
        self.profile = PreferTasteProfile.objects.create(user=self.user)

    @patch.object(TasteAnalysisService, "update_taste_profile_from_feedback")
    def test_update_from_review_calls_service(self, mock_update):
        """update_from_review가 TasteAnalysisService를 호출하는지 테스트"""
        mock_feedback = Mock()

        self.profile.update_from_review(mock_feedback)

        # 서비스 메서드가 올바른 인수로 호출되었는지 확인
        mock_update.assert_called_once_with(self.profile, mock_feedback)

    def test_get_taste_scores_dict(self):
        """get_taste_scores_dict 메서드 테스트"""
        self.profile.sweetness_level = Decimal("4.5")
        self.profile.acidity_level = Decimal("2.0")
        self.profile.save()

        scores = self.profile.get_taste_scores_dict()

        self.assertEqual(scores["sweetness_level"], 4.5)
        self.assertEqual(scores["acidity_level"], 2.0)
        self.assertIsInstance(scores["sweetness_level"], float)

    def test_needs_analysis_update(self):
        """분석 업데이트 필요 여부 테스트"""
        # 분석이 없는 경우
        self.assertTrue(self.profile.needs_analysis_update())

        # 분석 설명 추가
        self.profile.analysis_description = "테스트 분석"
        self.profile.save()

        # 분석 업데이트 시간이 없는 경우
        self.assertTrue(self.profile.needs_analysis_update())

    def test_update_analysis(self):
        """분석 업데이트 메서드 테스트"""
        description = "새로운 분석 설명"

        self.profile.update_analysis(description)

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.analysis_description, description)
        self.assertIsNotNone(self.profile.analysis_updated_at)

    def test_initialize_from_test_result(self):
        """취향 테스트 결과로 초기값 설정 테스트"""
        # Mock test result
        mock_test_result = Mock()
        mock_test_result.prefer_taste = "SWEET_FRUIT"

        with patch("apps.taste_test.services.TasteTestData.TASTE_PROFILES") as mock_profiles:
            mock_profiles.get.return_value = {
                "sweetness_level": 4.5,
                "acidity_level": 3.0,
                "body_level": 2.0,
                "carbonation_level": 2.0,
                "bitterness_level": 1.0,
                "aroma_level": 4.0,
            }

            self.profile.initialize_from_test_result(mock_test_result)

            self.profile.refresh_from_db()
            self.assertEqual(self.profile.sweetness_level, Decimal("4.5"))
            self.assertEqual(self.profile.acidity_level, Decimal("3.0"))

    def test_str_method(self):
        """__str__ 메서드 테스트"""
        expected = f"{self.user.nickname} 취향 프로필"
        self.assertEqual(str(self.profile), expected)


class UserModelTest(TestCase):
    """User 모델 기본 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")

    def test_create_user(self):
        """사용자 생성 테스트"""
        self.assertEqual(self.user.nickname, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.role, User.Role.USER)
        self.assertFalse(self.user.is_adult)

    def test_user_properties(self):
        """사용자 속성 테스트"""
        self.assertTrue(self.user.is_user)
        self.assertFalse(self.user.is_admin)
        self.assertFalse(self.user.is_staff)

    def test_make_admin(self):
        """관리자 승격 테스트"""
        self.user.make_admin()

        self.assertEqual(self.user.role, User.Role.ADMIN)
        self.assertTrue(self.user.is_admin)
        self.assertTrue(self.user.is_staff)

    def test_verify_adult(self):
        """성인 인증 테스트"""
        self.user.verify_adult()

        self.assertTrue(self.user.is_adult)
        self.assertIsNotNone(self.user.adult_verified_at)

    def test_str_method(self):
        """__str__ 메서드 테스트"""
        expected = f"{self.user.nickname} ({self.user.role})"
        self.assertEqual(str(self.user), expected)
