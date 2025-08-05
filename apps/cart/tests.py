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
            description="Desc 1",
            ingredients="Ingr 1",
            alcohol_content=10.0,
            volume_ml=360,
            id=uuid.uuid4(),
        )
        self.product2 = Product.objects.create(
            name="Product 2",
            price=20000,
            brewery=self.brewery,
            description="Desc 2",
            ingredients="Ingr 2",
            alcohol_content=12.5,
            volume_ml=500,
            id=uuid.uuid4(),
        )
        self.product3 = Product.objects.create(
            name="Product 3",
            price=30000,
            brewery=self.brewery,
            description="Desc 3",
            ingredients="Ingr 3",
            alcohol_content=15.0,
            volume_ml=750,
            id=uuid.uuid4(),
        )

        self.cart_url = "/api/cart/"
        self.add_item_url = "/api/cart/add-item/"
        self.add_package_url = "/api/cart/add-package/"
        self.update_item_url = "/api/cart/update-item/"
        self.remove_item_url = "/api/cart/remove-item/"

    def test_get_or_create_cart_authenticated_user(self):
        """인증된 사용자가 장바구니를 조회할 때, 장바구니가 없으면 생성되는지 테스트"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(len(response.data["single_items"]), 0)
        self.assertEqual(len(response.data["packages"]), 0)

    def test_add_new_item_to_cart_authenticated_user(self):
        """인증된 사용자가 장바구니에 새로운 단일 상품을 추가하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["single_items"]), 1)
        self.assertEqual(response.data["single_items"][0]["product"]["id"], str(self.product1.id))

    # ... (기존 단일 상품 테스트들은 유지) ...

    def test_add_package_to_cart(self):
        """패키지를 장바구니에 성공적으로 추가하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        product_ids = [str(self.product1.id), str(self.product2.id), str(self.product3.id)]
        data = {"product_ids": product_ids}
        response = self.client.post(self.add_package_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["packages"]), 1)
        self.assertEqual(len(response.data["packages"][0]["items"]), 3)
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("60000.00"))  # 10000 + 20000 + 30000

    def test_add_package_with_invalid_product_count(self):
        """상품 개수가 3개가 아닐 때 패키지 추가가 실패하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        product_ids = [str(self.product1.id), str(self.product2.id)]  # 2개만 보냄
        data = {"product_ids": product_ids}
        response = self.client.post(self.add_package_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_package_with_invalid_product_id(self):
        """존재하지 않는 상품 ID로 패키지 추가 시도가 실패하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        invalid_uuid = uuid.uuid4()
        product_ids = [str(self.product1.id), str(self.product2.id), str(invalid_uuid)]
        data = {"product_ids": product_ids}
        response = self.client.post(self.add_package_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # DB 롤백 확인 (장바구니 자체가 생성되지 않아야 함)
        self.assertFalse(Cart.objects.filter(user=self.user).exists())

    def test_remove_package_from_cart(self):
        """package_group_id로 패키지 전체가 삭제되는지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 먼저 패키지 추가
        product_ids = [str(self.product1.id), str(self.product2.id), str(self.product3.id)]
        response = self.client.post(self.add_package_url, {"product_ids": product_ids}, format="json")
        package_group_id = response.data["packages"][0]["package_group_id"]

        # 패키지 삭제
        remove_data = {"package_group_id": package_group_id}
        response = self.client.delete(self.remove_item_url, remove_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["packages"]), 0)
        self.assertEqual(Decimal(response.data["total_price"]), Decimal("0.00"))

    def test_update_item_on_package_item_fails(self):
        """패키지에 속한 상품의 수량 변경 시도가 실패하는지 테스트"""
        self.client.force_authenticate(user=self.user)
        # 패키지 추가
        product_ids = [str(self.product1.id), str(self.product2.id), str(self.product3.id)]
        response = self.client.post(self.add_package_url, {"product_ids": product_ids}, format="json")
        item_in_package_id = response.data["packages"][0]["items"][0]["id"]

        # 수량 업데이트 시도
        update_data = {"item_id": item_in_package_id, "quantity": 2}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
