import uuid

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart, CartItem
from apps.products.models import Product, ProductImage

User = get_user_model()


class CartAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        # self.client.force_authenticate(user=self.user) # 인증된 사용자 테스트를 위해 주석 처리

        self.product1 = Product.objects.create(name="Product 1", price=10000, id=uuid.uuid4())
        ProductImage.objects.create(product=self.product1, image_url="http://example.com/image1.jpg", is_main=True)

        self.product2 = Product.objects.create(name="Product 2", price=20000, id=uuid.uuid4())
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
        self.assertEqual(response.data["user"], self.user.id)
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total_price"], "0")

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
        self.assertEqual(response.data["items"][0]["total_price"], "10000")
        self.assertEqual(response.data["total_price"], "10000")
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
        self.assertEqual(response.data["items"][0]["total_price"], "30000")
        self.assertEqual(response.data["total_price"], "30000")

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
        self.assertEqual(response.data["items"][0]["total_price"], "30000")
        self.assertEqual(response.data["total_price"], "30000")

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
        self.assertEqual(response.data["total_price"], "0")

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
        self.assertEqual(response.data["total_price"], "0")

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
        self.assertEqual(response.data["total_price"], "40000")

    # --- 비로그인 사용자 테스트 추가 ---

    def test_get_or_create_cart_unauthenticated_user(self):
        """비로그인 사용자가 장바구니를 조회할 때, 장바구니가 없으면 생성되는지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)  # 인증 해제
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])
        self.assertIsNone(response.data["user"])  # 비로그인 사용자이므로 user는 None
        self.assertIsNotNone(response.data["session_key"])  # session_key가 있어야 함
        self.assertEqual(response.data["items"], [])
        self.assertEqual(response.data["total_price"], "0")

        # 두 번째 요청 시 기존 장바구니 반환 (동일 세션)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data["id"])
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_add_new_item_to_cart_unauthenticated_user(self):
        """비로그인 사용자가 장바구니에 새로운 상품을 추가하는지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"]["id"], str(self.product1.id))
        self.assertEqual(response.data["items"][0]["quantity"], 1)
        self.assertEqual(response.data["items"][0]["total_price"], "10000")
        self.assertEqual(response.data["total_price"], "10000")
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_add_existing_item_to_cart_unauthenticated_user(self):
        """비로그인 사용자가 장바구니에 이미 있는 상품을 추가할 때 수량이 증가하는지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)
        # 첫 번째 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        self.client.post(self.add_item_url, data, format="json")

        # 두 번째 추가
        data = {"product_id": str(self.product1.id), "quantity": 2}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 3)  # 1 + 2
        self.assertEqual(response.data["items"][0]["total_price"], "30000")
        self.assertEqual(response.data["total_price"], "30000")
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_update_item_quantity_unauthenticated_user(self):
        """비로그인 사용자가 장바구니 상품의 수량을 업데이트하는지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)
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
        self.assertEqual(response.data["items"][0]["total_price"], "30000")
        self.assertEqual(response.data["total_price"], "30000")
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_remove_item_by_setting_quantity_to_zero_unauthenticated_user(self):
        """비로그인 사용자가 수량을 0으로 설정하여 장바구니 상품이 제거되는지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)
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
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_remove_item_unauthenticated_user(self):
        """비로그인 사용자가 장바구니 상품을 제거하는지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)
        # 상품 추가
        data = {"product_id": str(self.product1.id), "quantity": 1}
        response = self.client.post(self.add_item_url, data, format="json")
        item_id = response.data["items"][0]["id"]

        # 상품 제거
        remove_data = {"item_id": item_id}
        response = self.client.delete(self.remove_item_url, remove_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)
        self.assertEqual(response.data["total_price"], "0")
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_add_multiple_items_and_check_total_unauthenticated_user(self):
        """비로그인 사용자가 여러 상품을 추가하고 총 가격이 올바른지 테스트 (세션 기반)"""
        self.client.force_authenticate(user=None)
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
        self.assertIsNone(response.data["user"])
        self.assertIsNotNone(response.data["session_key"])

    def test_unauthenticated_cart_merges_on_login(self):
        """비로그인 상태에서 담은 장바구니가 로그인 시 병합되는지 테스트"""
        # 1. 비로그인 상태로 상품 추가
        self.client.force_authenticate(user=None)
        data = {"product_id": str(self.product1.id), "quantity": 2}
        response = self.client.post(self.add_item_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        unauth_cart_id = response.data["id"]
        unauth_session_key = self.client.session.session_key  # 세션 키 저장

        # 2. 사용자 로그인
        self.client.force_authenticate(user=self.user)

        # 3. 로그인 후 장바구니 조회 (병합 확인)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"], self.user.id)  # 로그인한 사용자의 장바구니여야 함
        self.assertIsNone(response.data["session_key"])  # 로그인 후에는 session_key가 None이 되어야 함

        # 장바구니 아이템 확인
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["product"]["id"], str(self.product1.id))
        self.assertEqual(response.data["items"][0]["quantity"], 2)
        self.assertEqual(response.data["total_price"], "20000")

        # 비로그인 장바구니가 삭제되었는지 확인 (선택 사항, 구현에 따라 다름)
        # Cart.objects.filter(id=unauth_cart_id).exists()
        # 이 부분은 CartViewSet의 get_object 로직에 따라 달라짐.
        # 현재 구현은 로그인 시 기존 세션 카트를 사용자 카트로 옮기고 세션 카트를 삭제하는 로직이 없음.
        # 따라서 이 테스트는 현재 코드베이스의 동작을 반영해야 함.
        # 현재 코드에서는 로그인 시 새로운 카트를 생성하거나 기존 사용자 카트를 가져오고,
        # 세션 카트와의 병합 로직은 명시적으로 구현되어 있지 않음.
        # 이 테스트는 현재 코드의 한계를 드러낼 수 있음.
