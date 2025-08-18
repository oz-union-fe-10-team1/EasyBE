from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import CartItem
from apps.orders.models import Order
from apps.products.models import Brewery, Drink, Product
from apps.stores.models import Store

User = get_user_model()


class OrderFromCartAPITest(APITestCase):
    def setUp(self):
        # Given: 기본 데이터 설정
        self.user = User.objects.create_user(nickname="testuser")
        self.client.force_authenticate(user=self.user)

        self.brewery = Brewery.objects.create(name="Test Brewery")

        # Drink 객체 생성
        self.drink1 = Drink.objects.create(
            name="Test Drink 1",
            brewery=self.brewery,
            ingredients="Ingredients 1",
            alcohol_type=Drink.AlcoholType.MAKGEOLLI,
            abv=Decimal("6.0"),
            volume_ml=750,
        )
        self.drink2 = Drink.objects.create(
            name="Test Drink 2",
            brewery=self.brewery,
            ingredients="Ingredients 2",
            alcohol_type=Drink.AlcoholType.SOJU,
            abv=Decimal("19.0"),
            volume_ml=360,
        )

        # Product 객체 생성 (Drink와 연결)
        self.product1 = Product.objects.create(
            drink=self.drink1, price=10000, description="Desc 1", description_image_url="http://example.com/desc1.jpg"
        )
        self.product2 = Product.objects.create(
            drink=self.drink2, price=20000, description="Desc 2", description_image_url="http://example.com/desc2.jpg"
        )

        # 매장 설정
        self.store1 = Store.objects.create(name="Store 1", address="Address 1")
        self.store2 = Store.objects.create(name="Store 2", address="Address 2")

        # URL
        self.create_order_url = "/api/v1/orders/create_from_cart"

    def test_create_order_from_cart_success(self):
        """장바구니에서 주문 생성 성공 테스트"""
        # Given: 장바구니에 상품 추가
        CartItem.objects.create(
            user=self.user, product=self.product1, quantity=2, pickup_store=self.store1, pickup_date=date.today()
        )
        CartItem.objects.create(
            user=self.user, product=self.product2, quantity=1, pickup_store=self.store1, pickup_date=date.today()
        )

        # When: 주문 생성 API 호출
        response = self.client.post(self.create_order_url)

        # Then: 주문이 성공적으로 생성되고, 장바구니가 비워짐
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.total_price, 40000)  # (10000 * 2) + (20000 * 1)
        self.assertEqual(order.items.count(), 2)

        # 장바구니 비워졌는지 확인
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_create_order_from_empty_cart(self):
        """빈 장바구니에서 주문 생성 시도 테스트"""
        # Given: 사용자의 장바구니가 비어있는 상태

        # When: 주문 생성 API 호출
        response = self.client.post(self.create_order_url)

        # Then: 400 에러와 함께 장바구니가 비었다는 메시지를 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("장바구니가 비어있습니다", response.data["detail"])

    def test_create_order_from_cart_fails_if_no_pickup_info(self):
        """장바구니에 픽업 정보가 없을 때 주문 생성 실패 테스트"""
        # Given: 장바구니에 픽업 정보 없이 상품 추가
        CartItem.objects.create(user=self.user, product=self.product1, quantity=1)  # No pickup_store or pickup_date

        # When: 주문 생성 API 호출
        response = self.client.post(self.create_order_url)

        # Then: 400 에러와 함께 픽업 정보 부족 메시지를 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("픽업매장을 선택해주세요.", response.data["detail"])
        self.assertEqual(Order.objects.count(), 0)  # Order should not be created

    def test_unauthenticated_user_cannot_create_order_from_cart(self):
        """인증되지 않은 사용자의 주문 생성 실패 테스트"""
        # Given: 로그아웃된 클라이언트
        self.client.force_authenticate(user=None)

        # When: 주문 생성 API 호출
        response = self.client.post(self.create_order_url)

        # Then: 403 Forbidden 에러를 반환
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
