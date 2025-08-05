from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.orders.models import Order, OrderItem
from apps.products.models import Brewery, Product

from .models import Feedback

User = get_user_model()


class FeedbackAPITest(APITestCase):
    def setUp(self):
        """모든 테스트를 위한 공통 Given (주어진 상황)"""
        # 사용자 2명 생성
        self.user1 = User.objects.create_user(nickname="user1")
        self.user2 = User.objects.create_user(nickname="user2")

        # 상품 및 주문 생성
        brewery = Brewery.objects.create(name="Test Brewery")
        product = Product.objects.create(
            name="Test Product",
            price=10000,
            brewery=brewery,
            description="Desc",
            ingredients="Ingr",
            alcohol_content=10.0,
            volume_ml=360,
        )

        # user1의 주문
        order1 = Order.objects.create(user=self.user1, total_price=10000)
        self.order_item1 = OrderItem.objects.create(order=order1, product=product, quantity=1, price=10000)

        # user2의 주문 (다른 사용자의 주문)
        order2 = Order.objects.create(user=self.user2, total_price=10000)
        self.order_item2 = OrderItem.objects.create(order=order2, product=product, quantity=1, price=10000)

        # user2가 미리 작성해 둔 피드백 (월간 베스트 테스트용)
        self.feedback_for_user2 = Feedback.objects.create(
            order_item=self.order_item2,
            user=self.user2,
            sweetness=5,
            acidity=5,
            body=5,
            confidence=100,
            overall_rating=5,
            view_count=100,
        )
        # 한 달 이상 된 피드백 (월간 베스트 테스트용)
        old_order = Order.objects.create(user=self.user2, total_price=10000)
        old_order_item = OrderItem.objects.create(order=old_order, product=product, quantity=1, price=10000)
        self.old_feedback = Feedback.objects.create(
            order_item=old_order_item,
            user=self.user2,
            sweetness=1,
            acidity=1,
            body=1,
            confidence=1,
            overall_rating=1,
            view_count=999,
        )
        self.old_feedback.created_at = timezone.now() - timedelta(days=35)
        self.old_feedback.save()

    def test_create_feedback_success(self):
        """Scenario: 사용자가 자신의 주문 상품에 대해 성공적으로 후기를 작성한다."""
        # Given: user1이 로그인했고, 작성할 후기 데이터가 있다.
        self.client.force_authenticate(user=self.user1)
        data = {
            "order_item_id": self.order_item1.id,
            "sweetness": 4,
            "acidity": 3,
            "body": 2,
            "confidence": 80,
            "overall_rating": 5,
            "comment": "맛있어요!",
        }

        # When: 후기 생성 API를 호출한다.
        response = self.client.post("/api/v1/feedbacks/", data, format="json")

        # Then: 성공(201)하고, 생성된 후기 정보가 반환된다.
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["comment"], "맛있어요!")
        self.assertEqual(Feedback.objects.count(), 3)  # setUp에서 만든 2개 + 방금 1개

    def test_create_feedback_for_others_order_fails(self):
        """Scenario: 사용자가 다른 사람의 주문 상품에 후기를 작성하려고 시도한다."""
        # Given: user1이 로그인했고, user2의 주문 상품 ID로 후기를 작성하려 한다.
        self.client.force_authenticate(user=self.user1)
        data = {
            "order_item_id": self.order_item2.id,
            "overall_rating": 5,
            "sweetness": 1,
            "acidity": 1,
            "body": 1,
            "confidence": 1,
        }  # 필요한 필드 추가

        # When: 후기 생성 API를 호출한다.
        response = self.client.post("/api/v1/feedbacks/", data, format="json")

        # Then: 권한 없음(400, Serializer Validation) 오류가 발생한다.
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("권한이 없습니다", str(response.data))

    def test_list_my_feedbacks(self):
        """Scenario: 사용자가 자신이 작성한 후기 목록만 조회한다."""
        # Given: user2로 로그인했다. (user2는 1개의 최신 후기와 1개의 오래된 후기를 가지고 있다)
        self.client.force_authenticate(user=self.user2)

        # When: "내 후기 목록 조회" API를 호출한다.
        response = self.client.get("/api/v1/feedbacks/")

        # Then: 성공(200)하고, user2가 작성한 2개의 후기만 반환된다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["user"], str(self.user2))

    def test_retrieve_feedback_increments_view_count(self):
        """Scenario: 후기 상세 조회 시 조회수가 1 증가한다."""
        # Given: user2로 로그인했고, 조회할 후기의 초기 조회수는 100이다.
        self.client.force_authenticate(user=self.user2)
        self.assertEqual(self.feedback_for_user2.view_count, 100)

        # When: "내 후기 상세 조회" API를 호출한다.
        response = self.client.get(f"/api/v1/feedbacks/{self.feedback_for_user2.id}/")

        # Then: 성공(200)하고, 조회수는 101이 되어야 한다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["view_count"], 101)

    def test_list_all_feedbacks_publicly(self):
        """Scenario: 로그인하지 않은 사용자도 전체 후기 목록을 볼 수 있다."""
        # Given: 인증되지 않은 클라이언트가 있다.
        # When: "전체 후기 목록 조회" API를 호출한다.
        response = self.client.get("/api/v1/feedbacks/all/")

        # Then: 성공(200)하고, 시스템의 모든 후기(2개)가 반환된다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_monthly_best_feedbacks(self):
        """Scenario: 월간 베스트 후기 목록을 조회한다."""
        # Given: user1로 로그인했다.
        self.client.force_authenticate(user=self.user1)

        # When: "월간 베스트 후기" API를 호출한다.
        response = self.client.get("/api/v1/feedbacks/monthly-best/")

        # Then: 성공(200)하고, 한 달 이내에 작성된 후기 중 조회수가 높은 것(feedback_for_user2)만 반환된다.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.feedback_for_user2.id)
