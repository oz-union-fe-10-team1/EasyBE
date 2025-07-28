import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.products.models import Brewery, Product, ProductImage

User = get_user_model()


class CartAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(nickname="testuser")
        self.brewery = Brewery.objects.create(name="Test Brewery")

        self.product1 = Product.objects.create(
            name="Product 1",
            price=10000,
            brewery=self.brewery,
            description="Test Description 1",
            ingredients="Test Ingredients 1",
            alcohol_content=10.0,
            volume_ml=360,
            id=uuid.uuid4(),
        )
        ProductImage.objects.create(product=self.product1, image_url="http://example.com/image1.jpg", is_main=True)

        self.product2 = Product.objects.create(
            name="Product 2",
            price=20000,
            brewery=self.brewery,
            description="Test Description 2",
            ingredients="Test Ingredients 2",
            alcohol_content=12.5,
            volume_ml=500,
            id=uuid.uuid4(),
        )
        ProductImage.objects.create(product=self.product2, image_url="http://example.com/image2.jpg", is_main=True)

        self.cart_url = "/api/cart/"
        self.add_item_url = "/api/cart/add-item/"
        self.update_item_url = "/api/cart/update-item/"
        self.remove_item_url = "/api/cart/remove-item/"  # remove_item_url 추가

    def test_get_or_create_cart_authenticated_user(self):
        """인증된 사용자가 장바구니를 조회할 때, 장바구니가 없으면 생성되는지 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])
        self.assertEqual(response.data["customer"], self.user.id)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("0.00"))

        # 두 번째 요청 시 기존 장바구니 반환
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])

    def test_add_new_item_to_cart_authenticated_user(self):
        """인증된 사용자가 장바구니에 새로운 상품을 추가하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"]["id"], str(self.product1.id))
        self.assertEqual(response.data["items"][0]["quantity"], 1)
        self.assertEqual(Decimal(response.data["items"][0]["subtotal"]), Decimal("10000.00"))
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("10000.00"))
        self.assertEqual(response.data["items"][0]["product"]["main_image_url"], "http://example.com/image1.jpg")

    def test_add_existing_item_to_cart_authenticated_user(self):
        """인증된 사용자가 장바구니에 이미 있는 상품을 추가할 때 수량이 증가하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 첫 번째 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        self.client.post(self.add_item_url, data, format="json")

        # 두 번째 추가
        data = {"product_id": str(self.product1.id), "quantity": 2}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 3)  # 1 + 2
        self.assertEqual(Decimal(response.data["items"][0]["subtotal"]), Decimal("30000.00"))
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("30000.00"))

    def test_update_item_quantity_authenticated_user(self):
        """인증된 사용자가 장바구니 상품의 수량을 업데이트하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 5}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        # 수량 업데이트
        update_data = {"item_id": item_id, "quantity": 3}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 3)
        self.assertEqual(Decimal(response.data["items"][0]["subtotal"]), Decimal("30000.00"))
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("30000.00"))

    def test_remove_item_by_setting_quantity_to_zero_authenticated_user(self):
        """인증된 사용자가 수량을 0으로 설정하여 장바구니 상품이 제거되는지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        # 수량을 0으로 업데이트
        update_data = {"item_id": item_id, "quantity": 0}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)  # 장바구니가 비어있어야 함
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("0.00"))

    def test_remove_item_authenticated_user(self):
        """인증된 사용자가 장바구니 상품을 제거하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        # 상품 제거
        remove_data = {"item_id": item_id}
        response = self.client.delete(self.remove_item_url, remove_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("0.00"))

    def test_add_multiple_items_and_check_total_authenticated_user(self):
        """인증된 사용자가 여러 상품을 추가하고 총 가격이 올바른지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 상품1 추가
        data1 = {"product_id": str(self.product1.id), "quantity": 2}
        self.client.post(self.add_item_url, data1, format="json")

        # 상품2 추가
        data2 = {"product_id": str(self.product2.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data2, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 2)
        # 상품1: 10000 * 2 = 20000
        # 상품2: 20000 * 1 = 20000
        # 총합: 40000
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("40000.00"))
