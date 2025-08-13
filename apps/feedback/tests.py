from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.feedback.models import TASTE_TAG_CHOICES, Feedback
from apps.orders.models import Order, OrderItem
from apps.products.models import Brewery, Drink, Product
from apps.stores.models import Store

User = get_user_model()


class FeedbackModelTest(TestCase):
    """Feedback 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com", password="testpass123")

        self.brewery = Brewery.objects.create(name="테스트 양조장", description="테스트용 양조장입니다.")

        self.drink = Drink.objects.create(
            name="테스트 소주",
            brewery=self.brewery,
            ingredients="쌀, 물",
            alcohol_type=Drink.AlcoholType.SOJU,
            abv=Decimal("17.5"),
            volume_ml=500,
            sweetness_level=Decimal("2.5"),
            acidity_level=Decimal("3.0"),
            body_level=Decimal("2.0"),
            carbonation_level=Decimal("0.0"),
            bitterness_level=Decimal("1.5"),
            aroma_level=Decimal("3.5"),
        )

        self.product = Product.objects.create(
            drink=self.drink,
            price=15000,
            description="테스트 상품 설명",
            description_image_url="http://example.com/image.jpg",
        )

        self.order = Order.objects.create(user=self.user, total_price=Decimal("15000"), status=Order.Status.COMPLETED)

        # 매장 생성
        self.store = Store.objects.create(
            name="테스트 매장", address="서울시 테스트구 테스트동", contact="010-1234-5678"
        )

        # 주문 아이템 생성
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("15000"),
            pickup_store=self.store,
            pickup_day=date.today(),
        )

    def test_feedback_creation(self):
        feedback = Feedback.objects.create(
            user=self.user,
            order_item=self.order_item,
            rating=5,
            sweetness=Decimal("3.0"),
            acidity=Decimal("2.5"),
            body=Decimal("4.0"),
            confidence=80,
            comment="정말 맛있는 소주입니다!",
            selected_tags=["달콤한", "부드러운"],
        )
        self.assertEqual(feedback.rating, 5)
        self.assertEqual(feedback.sweetness, Decimal("3.0"))
        self.assertEqual(feedback.confidence, 80)
        self.assertEqual(len(feedback.selected_tags), 2)
        self.assertIn("달콤한", feedback.selected_tags)

    def test_feedback_str_method(self):
        feedback = Feedback.objects.create(
            user=self.user, order_item=self.order_item, rating=4, comment="좋은 술입니다."
        )
        expected_str = f"{self.user.nickname} - {self.product.name} (4점)"
        self.assertEqual(str(feedback), expected_str)

    def test_masked_username_property(self):
        feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        self.assertEqual(feedback.masked_username, "tes*****")

        self.user.nickname = "abcdefg"
        self.user.save()
        feedback.refresh_from_db()
        self.assertEqual(feedback.masked_username, "abc****")

        self.user.nickname = "abc"
        self.user.save()
        feedback.refresh_from_db()
        self.assertEqual(feedback.masked_username, "a**")

    def test_product_property(self):
        feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        self.assertEqual(feedback.product, self.product)

    def test_increment_view_count(self):
        feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        initial_count = feedback.view_count
        feedback.increment_view_count()
        feedback.refresh_from_db()
        self.assertEqual(feedback.view_count, initial_count + 1)
        self.assertIsNotNone(feedback.last_viewed_at)

    def test_invalid_tags_validation(self):
        feedback = Feedback(
            user=self.user, order_item=self.order_item, rating=4, selected_tags=["잘못된태그", "달콤한"]
        )
        with self.assertRaises(ValidationError):
            feedback.clean()

    def test_valid_tags_validation(self):
        valid_tags = [choice[0] for choice in TASTE_TAG_CHOICES[:3]]
        feedback = Feedback(user=self.user, order_item=self.order_item, rating=4, selected_tags=valid_tags)
        try:
            feedback.clean()
        except ValidationError:
            self.fail("valid tags should not raise ValidationError")

    def test_review_count_increment_on_save(self):
        initial_review_count = self.product.review_count
        Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_count, initial_review_count + 1)

    def test_review_count_decrement_on_delete(self):
        feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        self.product.refresh_from_db()
        review_count_after_create = self.product.review_count
        feedback.delete()
        self.product.refresh_from_db()
        self.assertEqual(self.product.review_count, review_count_after_create - 1)


class FeedbackQuerySetTest(TestCase):
    """Feedback QuerySet 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com", password="testpass123")
        self.brewery = Brewery.objects.create(name="테스트 양조장")
        self.drink = Drink.objects.create(
            name="테스트 소주",
            brewery=self.brewery,
            ingredients="쌀, 물",
            alcohol_type=Drink.AlcoholType.SOJU,
            abv=Decimal("17.5"),
            volume_ml=500,
        )
        self.product = Product.objects.create(
            drink=self.drink,
            price=15000,
            description="테스트 상품 설명",
            description_image_url="http://example.com/image.jpg",
        )
        # 매장 생성
        self.store = Store.objects.create(
            name="테스트 매장", address="서울시 테스트구 테스트동", contact="010-1234-5678"
        )

        self.order = Order.objects.create(user=self.user, total_price=Decimal("15000"))
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("15000"),
            pickup_day=date.today(),
            pickup_store=self.store,
        )

    def test_high_rated_queryset(self):
        high_feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=5)
        order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("15000"),
            pickup_day=date.today(),
            pickup_store=self.store,
        )
        low_feedback = Feedback.objects.create(user=self.user, order_item=order_item2, rating=2)
        high_rated_feedbacks = Feedback.objects.high_rated()
        self.assertIn(high_feedback, high_rated_feedbacks)
        self.assertNotIn(low_feedback, high_rated_feedbacks)

    def test_with_taste_profile_queryset(self):
        with_taste = Feedback.objects.create(
            user=self.user, order_item=self.order_item, rating=4, sweetness=Decimal("3.0")
        )
        order_item2 = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("15000"),
            pickup_day=date.today(),
            pickup_store=self.store,
        )
        without_taste = Feedback.objects.create(user=self.user, order_item=order_item2, rating=4)
        taste_profile_feedbacks = Feedback.objects.with_taste_profile()
        self.assertIn(with_taste, taste_profile_feedbacks)
        self.assertNotIn(without_taste, taste_profile_feedbacks)


class FeedbackAPITest(APITestCase):
    """Feedback API 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(nickname="testuser", email="test@example.com", password="testpass123")
        self.brewery = Brewery.objects.create(name="테스트 양조장")
        self.drink = Drink.objects.create(
            name="테스트 소주",
            brewery=self.brewery,
            ingredients="쌀, 물",
            alcohol_type=Drink.AlcoholType.SOJU,
            abv=Decimal("17.5"),
            volume_ml=500,
        )
        self.product = Product.objects.create(
            drink=self.drink,
            price=15000,
            description="테스트 상품 설명",
            description_image_url="http://example.com/image.jpg",
        )
        # 매장 생성
        self.store = Store.objects.create(
            name="테스트 매장", address="서울시 테스트구 테스트동", contact="010-1234-5678"
        )

        self.order = Order.objects.create(user=self.user, total_price=Decimal("15000"))
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
            price=Decimal("15000"),
            pickup_day=date.today(),
            pickup_store=self.store,
        )

    def test_create_feedback_authenticated(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "order_item": self.order_item.id,
            "rating": 5,
            "sweetness": "3.5",
            "acidity": "2.0",
            "body": "4.0",
            "confidence": 80,
            "comment": "정말 맛있습니다!",
            "selected_tags": ["달콤한", "부드러운"],
        }
        url = reverse("feedback:v1:feedbacks-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feedback.objects.count(), 1)
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.user, self.user)
        self.assertEqual(feedback.rating, 5)

    def test_create_feedback_unauthenticated(self):
        data = {"order_item": self.order_item.id, "rating": 5, "comment": "좋은 술입니다."}
        url = reverse("feedback:v1:feedbacks-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_feedback_increments_view_count(self):
        feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        initial_count = feedback.view_count
        url = reverse("feedback:v1:feedbacks-detail", kwargs={"pk": feedback.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        feedback.refresh_from_db()
        self.assertEqual(feedback.view_count, initial_count + 1)

    def test_list_recent_feedbacks(self):
        Feedback.objects.create(user=self.user, order_item=self.order_item, rating=5)
        url = reverse("feedback:v1:feedbacks-recent")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_my_feedbacks(self):
        self.client.force_authenticate(user=self.user)
        feedback = Feedback.objects.create(user=self.user, order_item=self.order_item, rating=4)
        url = reverse("feedback:v1:feedbacks-my")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], feedback.id)

    def test_invalid_tag_validation_api(self):
        self.client.force_authenticate(user=self.user)
        data = {"order_item": self.order_item.id, "rating": 4, "selected_tags": ["잘못된태그", "달콤한"]}
        url = reverse("feedback:v1:feedbacks-list")
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("selected_tags", response.data)
