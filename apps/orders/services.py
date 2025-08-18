from django.db import transaction

from apps.cart.models import CartItem
from apps.orders.models import Order, OrderItem


class OrderCreationError(Exception):
    """주문 생성 관련 최상위 예외"""

    pass


class CartIsEmptyError(OrderCreationError):
    """장바구니가 비어있을 때 발생하는 예외"""

    pass


class MissingPickupInfoError(OrderCreationError):
    """픽업 정보가 누락되었을 때 발생하는 예외"""

    pass


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user):
        cart_items = CartItem.objects.filter(user=user).select_related("product", "pickup_store")

        if not cart_items.exists():
            raise CartIsEmptyError("장바구니가 비어있습니다.")

        total_price = sum(item.total_price for item in cart_items)

        # 1. 주문 생성
        order = Order.objects.create(user=user, total_price=total_price)

        # 2. 주문 항목 생성
        order_items_to_create = []
        for item in cart_items:
            if not item.pickup_store or not item.pickup_date:
                raise MissingPickupInfoError(f"{item.product.name} 상품의 픽업 정보가 없습니다.")

            order_item = OrderItem(
                order=order,
                product=item.product,
                price=item.product.price,  # 주문 당시 가격 기록
                quantity=item.quantity,
                pickup_store=item.pickup_store,
                pickup_day=item.pickup_date,
            )
            order_items_to_create.append(order_item)

        OrderItem.objects.bulk_create(order_items_to_create)

        # 3. 장바구니 비우기
        cart_items.delete()

        return order
