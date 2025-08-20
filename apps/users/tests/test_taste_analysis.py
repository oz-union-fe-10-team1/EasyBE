# apps/users/tests/test_taste_analysis.py

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.feedback.models import Feedback
from apps.orders.models import Order, OrderItem
from apps.products.models import Brewery, Drink, Product
from apps.taste_test.models import PreferenceTestResult
from apps.users.models import PreferTasteProfile
from apps.users.utils.taste_analysis import TasteAnalysisService

User = get_user_model()


class TasteAnalysisServiceTest(TestCase):
    """TasteAnalysisService 테스트 - 실제 객체 사용"""

    def setUp(self):
        """테스트 데이터 설정"""
        # 사용자 생성
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com")

        # 취향 테스트 결과 생성
        self.test_result = PreferenceTestResult.objects.create(
            user=self.user, prefer_taste=PreferenceTestResult.PreferTaste.SWEET_FRUIT, answers={"Q1": "A", "Q2": "B"}
        )

        # 취향 프로필 생성
        self.taste_profile = PreferTasteProfile.objects.create(
            user=self.user,
            sweetness_level=Decimal("4.0"),
            acidity_level=Decimal("2.5"),
            body_level=Decimal("2.0"),
            carbonation_level=Decimal("2.0"),
            bitterness_level=Decimal("1.5"),
            aroma_level=Decimal("4.0"),
            total_reviews_count=0,
        )

        # 제품 관련 객체들 생성
        self.brewery = Brewery.objects.create(name="테스트 양조장", region="서울")

        self.drink = Drink.objects.create(
            name="테스트 막걸리",
            brewery=self.brewery,
            ingredients="쌀, 누룩",
            alcohol_type=Drink.AlcoholType.MAKGEOLLI,
            abv=Decimal("6.0"),
            volume_ml=750,
            sweetness_level=Decimal("3.5"),
            acidity_level=Decimal("2.0"),
            body_level=Decimal("3.0"),
            carbonation_level=Decimal("2.5"),
            bitterness_level=Decimal("1.5"),
            aroma_level=Decimal("4.0"),
        )

        self.product = Product.objects.create(drink=self.drink, price=15000, description="달콤한 막걸리")

        # 매장 생성
        from apps.stores.models import Store

        self.store = Store.objects.create(name="테스트 매장", address="서울시 테스트구")

        # 주문 관련 객체들 생성
        self.order = Order.objects.create(user=self.user, total_price=15000, order_number="ORD20250813001")
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=15000,
            pickup_day=date.today(),
            pickup_store=self.store,
        )

    def test_generate_analysis_no_reviews(self):
        """리뷰가 없는 경우 분석 생성 테스트"""
        analysis = TasteAnalysisService.generate_analysis(self.taste_profile)

        self.assertIn("아직 리뷰가 없어서", analysis)
        self.assertIn("술을 마시고 리뷰를 남겨보세요", analysis)

    def test_generate_analysis_few_reviews(self):
        """리뷰가 적은 경우 분석 생성 테스트"""
        self.taste_profile.total_reviews_count = 2
        self.taste_profile.save()

        analysis = TasteAnalysisService.generate_analysis(self.taste_profile)

        self.assertIn("아직 리뷰가 적어서", analysis)
        self.assertIn("대략적인 취향만", analysis)

    def test_generate_analysis_many_reviews(self):
        """리뷰가 많은 경우 분석 생성 테스트"""
        self.taste_profile.total_reviews_count = 15
        self.taste_profile.sweetness_level = Decimal("4.5")  # 높은 선호도
        self.taste_profile.bitterness_level = Decimal("1.0")  # 낮은 선호도
        self.taste_profile.save()

        analysis = TasteAnalysisService.generate_analysis(self.taste_profile)

        self.assertIn("15개의 리뷰를 분석한 결과", analysis)
        self.assertIn("단맛", analysis)  # 높은 선호도 언급
        self.assertIn("쓴맛", analysis)  # 낮은 선호도 언급

    def test_get_recommendation_sweet_fruit_pattern(self):
        """달콤과일파 패턴 추천 테스트"""
        scores = {
            "sweetness_level": 4.5,
            "acidity_level": 3.0,
            "body_level": 2.0,
            "carbonation_level": 2.0,
            "bitterness_level": 1.0,
            "aroma_level": 4.5,
        }

        recommendation = TasteAnalysisService._get_recommendation(scores, ["단맛", "향"], ["쓴맛"])

        self.assertIn("과일의 달콤함", recommendation)
        self.assertIn("약주나 리큐르", recommendation)

    def test_update_taste_profile_from_feedback_real_objects(self):
        """실제 객체를 사용한 취향 프로필 업데이트 테스트"""
        # 초기 값 저장
        initial_sweetness = float(self.taste_profile.sweetness_level)
        initial_review_count = self.taste_profile.total_reviews_count

        # 실제 피드백 생성 (자동으로 취향 프로필 업데이트됨)
        feedback = Feedback.objects.create(
            user=self.user,
            order_item=self.order_item,
            rating=4,
            sweetness=Decimal("4.0"),
            acidity=Decimal("2.5"),
            body=Decimal("3.5"),
            carbonation=Decimal("2.0"),
            bitterness=Decimal("1.0"),
            aroma=Decimal("4.5"),
            confidence=80,
            comment="정말 맛있었어요!",
        )

        # 결과 확인
        self.taste_profile.refresh_from_db()

        # 리뷰 카운트 증가 확인
        self.assertEqual(self.taste_profile.total_reviews_count, initial_review_count + 1)

        # 값이 유효한 범위 내에 있는지 확인
        self.assertGreaterEqual(self.taste_profile.sweetness_level, 0)
        self.assertLessEqual(self.taste_profile.sweetness_level, 5)

        # 실제 값 변경 확인 (단맛이 높게 평가되었으니 증가했을 것)
        new_sweetness = float(self.taste_profile.sweetness_level)
        self.assertNotEqual(new_sweetness, initial_sweetness)

    def test_update_taste_profile_with_partial_feedback(self):
        """일부 필드만 있는 피드백 테스트"""
        # 새로운 주문 아이템 생성 (OneToOne 관계 때문에)
        order2 = Order.objects.create(user=self.user, total_price=15000, order_number="ORD20250813002")
        order_item2 = OrderItem.objects.create(
            order=order2,
            product=self.product,
            quantity=1,
            price=15000,
            pickup_day=date.today(),
            pickup_store=self.store,
        )

        initial_review_count = self.taste_profile.total_reviews_count

        # 피드백 생성 (자동으로 취향 프로필 업데이트됨)
        feedback = Feedback.objects.create(
            user=self.user,
            order_item=order_item2,
            rating=3,
            sweetness=Decimal("2.0"),  # 단맛만 평가
            # 다른 맛 필드들은 None
            confidence=60,
        )

        self.taste_profile.refresh_from_db()
        self.assertEqual(self.taste_profile.total_reviews_count, initial_review_count + 1)

    def test_update_taste_profile_low_rating(self):
        """낮은 평점의 피드백 테스트"""
        # 새로운 주문 아이템 생성 (OneToOne 관계 때문에)
        order3 = Order.objects.create(user=self.user, total_price=15000, order_number="ORD20250813003")
        order_item3 = OrderItem.objects.create(
            order=order3,
            product=self.product,
            quantity=1,
            price=15000,
            pickup_day=date.today(),
            pickup_store=self.store,
        )

        initial_bitterness = float(self.taste_profile.bitterness_level)

        # 피드백 생성 (자동으로 취향 프로필 업데이트됨)
        feedback = Feedback.objects.create(
            user=self.user,
            order_item=order_item3,
            rating=2,  # 낮은 평점
            sweetness=Decimal("1.0"),
            bitterness=Decimal("4.0"),  # 쓴맛이 강함
            confidence=90,
        )

        self.taste_profile.refresh_from_db()

        # 낮은 평점과 강한 쓴맛으로 인해 쓴맛 선호도가 조정되었을 것
        new_bitterness = float(self.taste_profile.bitterness_level)
        self.assertNotEqual(new_bitterness, initial_bitterness)

    def test_multiple_feedback_accumulation(self):
        """여러 피드백 누적 테스트"""
        initial_review_count = self.taste_profile.total_reviews_count

        # 첫 번째 피드백 (자동으로 취향 프로필 업데이트됨)
        feedback1 = Feedback.objects.create(
            user=self.user, order_item=self.order_item, rating=5, sweetness=Decimal("4.5"), confidence=80
        )

        self.taste_profile.refresh_from_db()

        intermediate_sweetness = float(self.taste_profile.sweetness_level)
        intermediate_count = self.taste_profile.total_reviews_count

        # 두 번째 주문 아이템 생성 (OneToOne 관계 때문에)
        order2 = Order.objects.create(user=self.user, total_price=15000, order_number="ORD20250813004")
        order_item2 = OrderItem.objects.create(
            order=order2,
            product=self.product,
            quantity=1,
            price=15000,
            pickup_day=date.today(),
            pickup_store=self.store,
        )

        # 두 번째 피드백 (자동으로 취향 프로필 업데이트됨)
        feedback2 = Feedback.objects.create(
            user=self.user, order_item=order_item2, rating=3, sweetness=Decimal("2.0"), confidence=70
        )

        self.taste_profile.refresh_from_db()

        # 리뷰 수 증가 확인
        self.assertEqual(self.taste_profile.total_reviews_count, initial_review_count + 2)
        self.assertEqual(intermediate_count + 1, self.taste_profile.total_reviews_count)

        # 값이 변경되었는지 확인
        final_sweetness = float(self.taste_profile.sweetness_level)
        self.assertNotEqual(final_sweetness, intermediate_sweetness)


class TasteAnalysisIntegrationTest(TestCase):
    """취향 분석 통합 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="integrationuser", email="integration@test.com")

        # 매장 생성
        from apps.stores.models import Store

        self.store = Store.objects.create(name="통합테스트 매장", address="서울시 통합구")

        # 취향 테스트 결과
        self.test_result = PreferenceTestResult.objects.create(
            user=self.user,
            prefer_taste=PreferenceTestResult.PreferTaste.FRESH_FIZZY,
            answers={"Q1": "A", "Q2": "A", "Q3": "A", "Q4": "A"},
        )

        # 취향 프로필 초기화
        self.taste_profile = PreferTasteProfile.objects.create(user=self.user)
        self.taste_profile.initialize_from_test_result(self.test_result)

    def test_full_feedback_flow_integration(self):
        """피드백 생성부터 취향 분석까지 전체 플로우 테스트"""
        # 제품 생성
        brewery = Brewery.objects.create(name="상큼 양조장")
        drink = Drink.objects.create(
            name="상큼한 탄산주",
            brewery=brewery,
            ingredients="쌀, 탄산",
            alcohol_type=Drink.AlcoholType.MAKGEOLLI,
            abv=Decimal("5.0"),
            volume_ml=500,
            sweetness_level=Decimal("2.0"),  # 낮은 단맛
            acidity_level=Decimal("4.5"),  # 높은 산미
            carbonation_level=Decimal("4.0"),  # 높은 탄산감
        )

        product = Product.objects.create(drink=drink, price=12000)
        order = Order.objects.create(user=self.user, total_price=12000, order_number="ORD20250813005")
        order_item = OrderItem.objects.create(
            order=order, product=product, quantity=1, price=12000, pickup_day=date.today(), pickup_store=self.store
        )

        initial_acidity = float(self.taste_profile.acidity_level)
        initial_carbonation = float(self.taste_profile.carbonation_level)

        # 사용자가 상큼톡톡파라면 이 제품을 좋아할 것
        # 피드백 생성 시 자동으로 취향 프로필 업데이트됨
        # 초기값보다 낮은 값으로 피드백을 주어서 변화를 확인
        feedback = Feedback.objects.create(
            user=self.user,
            order_item=order_item,
            rating=3,  # 중간 평점으로 변경
            acidity=Decimal("3.0"),  # 초기값 4.5보다 낮게
            carbonation=Decimal("3.0"),  # 초기값 4.5보다 낮게
            confidence=90,
        )

        self.taste_profile.refresh_from_db()

        # 산미와 탄산감 선호도가 감소했을 것
        self.assertLess(float(self.taste_profile.acidity_level), initial_acidity)
        self.assertLess(float(self.taste_profile.carbonation_level), initial_carbonation)

        # 분석 생성 테스트
        analysis = TasteAnalysisService.generate_analysis(self.taste_profile)
        self.assertIn("산미", analysis)  # 높은 선호도 언급 (여전히 4.0 이상일 것)
        self.assertIn("탄산감", analysis)  # 높은 선호도 언급 (여전히 4.0 이상일 것)
