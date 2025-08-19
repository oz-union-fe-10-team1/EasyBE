from apps.products.models import Product

from .models import CartItem


class CartService:
    @staticmethod
    def add_or_update_item(user, product_id, quantity, pickup_store, pickup_date):
        """
        장바구니에 상품을 추가하거나, 이미 있는 경우 수량을 업데이트합니다.
        """
        product = Product.objects.get(id=product_id)

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            pickup_store=pickup_store,
            pickup_date=pickup_date,
            defaults={"quantity": quantity},
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item

    @staticmethod
    def update_item_quantity(cart_item, quantity):
        """
        장바구니 상품의 수량을 업데이트합니다. 0 이하면 삭제합니다.
        """
        if quantity <= 0:
            cart_item.delete()
            return None
        else:
            cart_item.quantity = quantity
            cart_item.save()
            return cart_item

    @staticmethod
    def get_cart_info(user):
        """
        사용자의 장바구니 정보(항목 목록, 총액)를 반환합니다.
        """
        cart_items = CartItem.objects.filter(user=user).select_related("product", "pickup_store")
        total_price = sum(item.total_price for item in cart_items)
        return cart_items, total_price
