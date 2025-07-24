from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.products.models import Product, ProductImage

User = get_user_model()


class CartAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.client.force_authenticate(user=self.user)

        # Product 모델에 price 필드가 DecimalField이므로 Decimal 값으로 설정
        self.product1 = Product.objects.create(name="Product 1", price=10000)
        ProductImage.objects.create(product=self.product1, image_url="http://example.com/image1.jpg", is_main=True)

        self.product2 = Product.objects.create(name="Product 2", price=20000)
        ProductImage.objects.create(product=self.product2, image_url="http://example.com/image2.jpg", is_main=True)

        self.cart_url = "/api/cart/"
        self.add_item_url = "/api/cart/add-item/"
        self.update_item_url = "/api/cart/update-item/"

    def test_get_or_create_cart(self):
        """인증된 사용자가 장바구니를 조회할 때, 장바구니가 없으면 생성되는지 테스트"""
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total_price"], "0")
        self.assertEqual(response.data["final_total"], "0")

        # 두 번째 요청 시 기존 장바구니 반환
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])

    def test_add_new_item_to_cart(self):
        """장바구니에 새로운 상품을 추가하는지 테스트"""
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"]["id"], str(self.product1.id))
        self.assertEqual(response.data["items"][0]["quantity"], 1)
        self.assertEqual(response.data["items"][0]["subtotal"], "10000")
        self.assertEqual(response.data["total_price"], "10000")
        self.assertEqual(response.data["final_total"], "10000")
        self.assertEqual(response.data["items"][0]["product"]["main_image_url"], "http://example.com/image1.jpg")

    def test_add_existing_item_to_cart(self):
        """장바구니에 이미 있는 상품을 추가할 때 수량이 증가하는지 테스트"""
        # 첫 번째 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        self.client.post(self.add_item_url, data, format="json")

        # 두 번째 추가
        data = {"product_id": str(self.product1.id), "quantity": 2}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 3)  # 1 + 2
        self.assertEqual(response.data["items"][0]["subtotal"], "30000")
        self.assertEqual(response.data["total_price"], "30000")

    def test_update_item_quantity(self):
        """장바구니 상품의 수량을 업데이트하는지 테스트"""
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
        self.assertEqual(response.data["items"][0]["subtotal"], "30000")
        self.assertEqual(response.data["total_price"], "30000")

    def test_remove_item_by_setting_quantity_to_zero(self):
        """수량을 0으로 설정하여 장바구니 상품이 제거되는지 테스트"""
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        # 수량을 0으로 업데이트
        update_data = {"item_id": item_id, "quantity": 0}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)  # 장바구니가 비어있어야 함
        self.assertEqual(response.data["total_price"], "0")

    def test_add_multiple_items_and_check_total(self):
        """여러 상품을 추가하고 총 가격이 올바른지 테스트"""
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
        self.assertEqual(response.data["total_price"], "40000")
        self.assertEqual(response.data["final_total"], "40000")

    def test_unauthenticated_access(self):
        """인증되지 않은 사용자가 API에 접근할 때 401 응답을 받는지 테스트"""
        self.client.force_authenticate(user=None)  # 인증 해제
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.post(self.add_item_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.client.put(self.update_item_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_item_product_not_found(self):
        """존재하지 않는 상품을 추가할 때 400 응답을 받는지 테스트"""
        non_existent_product_id = "12345678-1234-5678-1234-567812345678"
        data = {"product_id": non_existent_product_id, "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST
        )  # Serializer에서 Product.DoesNotExist를 ValidationError로 변환
        self.assertIn("Product not found.", str(response.data))

    def test_update_item_not_found(self):
        """존재하지 않는 장바구니 아이템을 업데이트할 때 404 응답을 받는지 테스트"""
        non_existent_item_id = "87654321-4321-8765-4321-876543218765"
        update_data = {"item_id": non_existent_item_id, "quantity": 2}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Cart item not found.", str(response.data))

    def test_add_item_invalid_quantity(self):
        """유효하지 않은 수량으로 상품을 추가할 때 오류가 발생하는지 테스트"""
        data = {"product_id": str(self.product1.id), "quantity": -1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)

    def test_update_item_invalid_quantity(self):
        """
        유효하지 않은 수량으로 장바구니 상품을 업데이트할 때 오류가 발생하는지 테스트
        (수량 0은 제거로 처리되므로, 음수 값에 대한 테스트)
        """
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        # 수량을 음수로 업데이트
        update_data = {"item_id": item_id, "quantity": -5}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # 수량 0 이하로 처리되어 삭제됨
        self.assertEqual(len(response.data["items"]), 0)

    def test_add_item_missing_product_id(self):
        """product_id 없이 상품을 추가할 때 오류가 발생하는지 테스트"""
        data = {"quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product_id", response.data)

    def test_update_item_missing_item_id(self):
        """item_id 없이 상품 수량을 업데이트할 때 오류가 발생하는지 테스트"""
        update_data = {"quantity": 2}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_update_item_missing_quantity(self):
        """quantity 없이 상품 수량을 업데이트할 때 오류가 발생하는지 테스트"""
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        update_data = {"item_id": item_id}
        response = self.client.put(self.update_item_url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    def test_cart_model_str_methods(self):
        """Cart와 CartItem 모델의 __str__ 메소드 테스트"""
        cart = Cart.objects.get(user=self.user)
        self.assertIsInstance(str(cart), str)
        self.assertIn(self.user.username, str(cart))

        cart_item = CartItem.objects.create(cart=cart, product=self.product1, quantity=1)
        self.assertIsInstance(str(cart_item), str)
        self.assertIn(self.product1.name, str(cart_item))
        self.assertIn(str(cart_item.quantity), str(cart_item))
