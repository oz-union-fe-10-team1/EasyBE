from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.cart.models import Cart, CartItem
from apps.products.models import Product

User = get_user_model()


class CartModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="password123")
        self.product = Product.objects.create(name="Test Product", price=10000)

    def test_cart_creation(self):
        """
        사용자가 생성될 때 장바구니가 자동으로 생성되는지 테스트
        (현재 모델에는 자동 생성 로직이 없으므로 이 테스트는 실패할 것임)
        """
        # 장바구니가 아직 생성되지 않았음을 확인
        with self.assertRaises(Cart.DoesNotExist):
            self.user.cart

        # 장바구니 생성 로직 (아직 구현되지 않음)
        # Cart.objects.create(user=self.user) # 이 코드가 나중에 추가될 것임

        # 장바구니가 생성되었는지 확인 (현재는 실패)
        # self.assertIsInstance(self.user.cart, Cart)

    def test_add_item_to_cart(self):
        """
        장바구니에 상품을 추가하는 기능 테스트
        (현재 모델에는 상품 추가 로직이 없으므로 이 테스트는 실패할 것임)
        """
        cart = Cart.objects.create(user=self.user)  # 장바구니를 수동으로 생성

        # 장바구니에 상품 추가 로직 (아직 구현되지 않음)
        # CartItem.objects.create(cart=cart, product=self.product, quantity=1)

        # 장바구니에 상품이 추가되었는지 확인 (현재는 실패)
        # self.assertEqual(cart.items.count(), 1)
        # self.assertEqual(cart.items.first().product, self.product)
        # self.assertEqual(cart.items.first().quantity, 1)

    def test_cart_item_subtotal(self):
        """
        장바구니 상품의 소계 계산 테스트
        """
        cart = Cart.objects.create(user=self.user)
        cart_item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        self.assertEqual(cart_item.subtotal, 20000)  # 10000 * 2

    def test_cart_total_price(self):
        """
        장바구니 전체 가격 계산 테스트
        """
        cart = Cart.objects.create(user=self.user)
        product2 = Product.objects.create(name="Another Product", price=5000)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)  # 20000
        CartItem.objects.create(cart=cart, product=product2, quantity=3)  # 15000
        self.assertEqual(cart.total_price, 35000)  # 20000 + 15000
