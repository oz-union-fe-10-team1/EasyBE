import uuid
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.products.models import Product, ProductImage, Brewery, AlcoholType, Region # Region 추가
from apps.orders.models import Order, OrderItem

User = get_user_model()


class OrderAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_normal_user(nickname="testuser", password="password123")
        self.client.force_authenticate(user=self.user)

        # Product 생성을 위한 필수 필드 추가
        self.brewery = Brewery.objects.create(name="Test Brewery")
        self.alcohol_type = AlcoholType.objects.create(name="Test Type", category="rice_wine")
        self.region = Region.objects.create(name="Test Region", code="TR") # Region 추가

        self.product1 = Product.objects.create(
            name="Product 1",
            price=10000,
            id=uuid.uuid4(),
            brewery=self.brewery,
            alcohol_type=self.alcohol_type,
            description="Test Description 1",
            ingredients="Test Ingredients 1",
            alcohol_content=10.0,
            volume_ml=750,
            region=self.region, # Region 추가
        )
        ProductImage.objects.create(product=self.product1, image_url="http://example.com/image1.jpg", is_main=True)

        self.product2 = Product.objects.create(
            name="Product 2",
            price=20000,
            id=uuid.uuid4(),
            brewery=self.brewery,
            alcohol_type=self.alcohol_type,
            description="Test Description 2",
            ingredients="Test Ingredients 2",
            alcohol_content=15.0,
            volume_ml=360,
            region=self.region, # Region 추가
        )
        ProductImage.objects.create(product=self.product2, image_url="http://example.com/image2.jpg", is_main=True)

        self.cart_url = "/api/cart/"
        self.add_item_url = "/api/cart/add-item/"
        self.create_order_url = "/api/orders/create-from-cart/"
        self.orders_list_url = "/api/orders/"

    def test_create_order_from_cart_success(self):
        """장바구니에서 주문 생성 성공 테스트"""
        # 장바구니에 상품 추가
        self.client.post(self.add_item_url, {"product_id": str(self.product1.id), "quantity": 2}, format="json")
        self.client.post(self.add_item_url, {"product_id": str(self.product2.id), "quantity": 1}, format="json")

        # 주문 생성 API 호출
        response = self.client.post(self.create_order_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 주문이 올바르게 생성되었는지 확인
        order = Order.objects.get(id=response.data["id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, 40000) # (10000 * 2) + (20000 * 1)
        self.assertEqual(order.status, "pending")

        # 주문 상품이 올바르게 생성되었는지 확인
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 2)

        item1 = order_items.get(product=self.product1)
        self.assertEqual(item1.quantity, 2)
        self.assertEqual(item1.price, 10000)

        item2 = order_items.get(product=self.product2)
        self.assertEqual(item2.quantity, 1)
        self.assertEqual(item2.price, 20000)

        # 장바구니가 비워졌는지 확인
        with self.assertRaises(Cart.DoesNotExist):
            Cart.objects.get(user=self.user)

    def test_create_order_from_empty_cart(self):
        """빈 장바구니에서 주문 생성 시도 테스트"""
        # 사용자의 장바구니가 비어있는 상태를 보장
        Cart.objects.filter(user=self.user).delete() # 기존 장바구니 삭제
        Cart.objects.create(user=self.user) # 빈 장바구니 생성

        response = self.client.post(self.create_order_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("장바구니가 비어있습니다.", response.data["detail"])

    def test_list_orders(self):
        """주문 목록 조회 테스트"""
        # 주문 생성
        self.client.post(self.add_item_url, {"product_id": str(self.product1.id), "quantity": 1}, format="json")
        self.client.post(self.create_order_url, format="json")

        self.client.post(self.add_item_url, {"product_id": str(self.product2.id), "quantity": 2}, format="json")
        self.client.post(self.create_order_url, format="json")

        # 주문 목록 조회
        response = self.client.get(self.orders_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_single_order(self):
        """단일 주문 상세 조회 테스트"""
        # 주문 생성
        self.client.post(self.add_item_url, {"product_id": str(self.product1.id), "quantity": 3}, format="json")
        create_response = self.client.post(self.create_order_url, format="json")
        order_id = create_response.data["id"]

        # 단일 주문 조회
        response = self.client.get(f"{self.orders_list_url}{order_id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], order_id)
        self.assertEqual(response.data["total_price"], "30000")
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"]["id"], str(self.product1.id))

    def test_unauthenticated_order_access(self):
        """인증되지 않은 사용자의 주문 API 접근 테스트"""
        self.client.logout() # 세션 초기화
        self.client.force_authenticate(user=None) # 인증 해제

        # 주문 생성 시도
        response = self.client.post(self.create_order_url, HTTP_AUTHORIZATION='', format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 주문 목록 조회 시도
        response = self.client.get(self.orders_list_url, HTTP_AUTHORIZATION='')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 단일 주문 조회 시도 (존재하지 않는 ID로)
        response = self.client.get(f"{self.orders_list_url}{uuid.uuid4()}/", HTTP_AUTHORIZATION='')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
