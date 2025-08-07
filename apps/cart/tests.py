from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import Brewery, Drink, Package, Product, ProductImage

# ERD 기반 모델 임포트 (products 앱이 수정되었다고 가정)
from apps.users.models import User

from .models import CartItem


class CartItemViewSetTest(APITestCase):
    """
    CartItemViewSet에 대한 테스트 클래스.
    Given-When-Then 형식을 주석으로 사용하여 테스트 케이스를 구성합니다.
    """

    @classmethod
    def setUpTestData(cls):
        """
        테스트 전체에서 사용될 공용 데이터를 한 번만 생성합니다.
        """
        # GIVEN: 2명의 사용자
        cls.user = User.objects.create_user(nickname="testuser", email="test@example.com", password="password123")
        cls.other_user = User.objects.create_user(
            nickname="otheruser", email="other@example.com", password="password123"
        )

        # GIVEN: 1개의 양조장
        cls.brewery = Brewery.objects.create(name="테스트 양조장")

        # GIVEN: 1개의 단일 술(Drink) 상품
        cls.drink = Drink.objects.create(name="테스트 막걸리", alcohol_content=6.0, volume_ml=750)

        # GIVEN: 1개의 기획 패키지(Package)
        cls.curated_package = Package.objects.create(name="한잔 추천 세트", type="Curated")

        # GIVEN: 2개의 판매 상품(Product) - 하나는 단일 술, 하나는 패키지
        cls.product_drink = Product.objects.create(
            drink=cls.drink,
            brewery=cls.brewery,
            price=10000,
            description="맛있는 테스트 막걸리",
        )
        cls.product_package = Product.objects.create(
            package=cls.curated_package,
            brewery=cls.brewery,
            price=25000,
            description="한잔이 추천하는 스페셜 세트",
        )

        # GIVEN: 각 상품의 대표 이미지
        ProductImage.objects.create(product=cls.product_drink, image_url="https://example.com/drink.jpg", is_main=True)
        ProductImage.objects.create(
            product=cls.product_package, image_url="https://example.com/package.jpg", is_main=True
        )

    def setUp(self):
        """
        각 테스트 메소드가 실행되기 전에 클라이언트를 인증합니다.
        """
        self.client.force_authenticate(user=self.user)

    def test_add_package_product_to_cart(self):
        """
        [성공] 장바구니에 패키지 상품을 추가하는 경우
        """
        # GIVEN: 장바구니에 추가할 패키지 상품 정보
        url = reverse("cart-item-list")
        data = {
            "product_id": str(self.product_package.id),
            "quantity": 1,
        }

        # WHEN: 장바구니 추가 API를 호출
        response = self.client.post(url, data, format="json")

        # THEN: 새로운 장바구니 항목이 생성되고 201 코드를 반환
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CartItem.objects.filter(user=self.user, product=self.product_package, quantity=1).exists())

    def test_list_cart_items_and_total_price(self):
        """
        [성공] 장바구니 조회 시 상품 정보와 총액이 올바르게 표시되는 경우
        """
        # GIVEN: 사용자의 장바구니에 2개의 다른 상품이 담겨 있음
        CartItem.objects.create(user=self.user, product=self.product_drink, quantity=3)  # 10000 * 3 = 30000
        CartItem.objects.create(user=self.user, product=self.product_package, quantity=1)  # 25000 * 1 = 25000
        url = reverse("cart-item-list")

        # WHEN: 장바구니 목록 조회 API를 호출
        response = self.client.get(url)

        # THEN: 200 코드와 함께 장바구니 항목 목록 및 총액을 반환
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("cart_items", response.data)
        self.assertIn("total_price", response.data)
        self.assertEqual(len(response.data["cart_items"]), 2)
        self.assertEqual(response.data["total_price"], 55000)  # 30000 + 25000

    def test_update_quantity_with_plus_minus_button(self):
        """
        [성공] 장바구니 상품의 수량을 +/- 버튼으로 조작하는 경우
        """
        # GIVEN: 장바구니에 상품이 1개 담겨 있음
        cart_item = CartItem.objects.create(user=self.user, product=self.product_drink, quantity=1)
        url = reverse("cart-item-detail", kwargs={"pk": cart_item.pk})
        data = {"quantity": 5}  # 사용자가 + 버튼을 여러 번 눌러 수량을 5로 변경

        # WHEN: 수량 변경 API(PATCH)를 호출
        response = self.client.patch(url, data, format="json")

        # THEN: 수량이 정상적으로 변경되고 200 코드를 반환
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 5)
        self.assertEqual(response.data["quantity"], 5)

    def test_remove_item_by_updating_quantity_to_zero(self):
        """
        [성공] 상품 수량을 0으로 업데이트하여 장바구니에서 제거하는 경우
        """
        # GIVEN: 장바구니에 제거할 상품이 존재함
        cart_item = CartItem.objects.create(user=self.user, product=self.product_drink, quantity=3)
        url = reverse("cart-item-detail", kwargs={"pk": cart_item.pk})
        data = {"quantity": 0}  # 사용자가 - 버튼을 눌러 수량을 0으로 변경

        # WHEN: 수량 변경 API(PATCH)를 호출
        response = self.client.patch(url, data, format="json")

        # THEN: 응답은 성공(200)하지만 내용은 비어있고, DB에서 항목은 삭제됨
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data)  # Serializer의 update에서 None을 반환
        self.assertFalse(CartItem.objects.filter(pk=cart_item.pk).exists())

    def test_user_cannot_access_others_cart(self):
        """
        [실패] 다른 사용자의 장바구니에 접근할 수 없는 경우
        """
        # GIVEN: 다른 사용자의 장바구니에 상품이 존재함
        other_cart_item = CartItem.objects.create(user=self.other_user, product=self.product_drink, quantity=1)

        # WHEN: 현재 사용자가 다른 사용자의 아이템을 수정하려고 시도
        detail_url = reverse("cart-item-detail", kwargs={"pk": other_cart_item.pk})
        patch_response = self.client.patch(detail_url, {"quantity": 2})

        # THEN: 다른 사용자의 아이템 접근은 404 에러를 반환
        self.assertEqual(patch_response.status_code, status.HTTP_404_NOT_FOUND)
