import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class CartItem(models.Model):
    """장바구니 아이템"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)], help_text="수량")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cart_items"
        unique_together = ("user", "product")  # 사용자당 상품별로 하나씩만
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["product"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.product.name} x{self.quantity}"

    @property
    def total_price(self):
        """해당 아이템의 총 가격"""
        return self.product.price * self.quantity

    def increase_quantity(self, amount=1):
        """수량 증가"""
        self.quantity += amount
        self.save(update_fields=["quantity", "updated_at"])

    def decrease_quantity(self, amount=1):
        """수량 감소"""
        if self.quantity > amount:
            self.quantity -= amount
            self.save(update_fields=["quantity", "updated_at"])
        else:
            self.delete()  # 수량이 0 이하가 되면 삭제

    def update_quantity(self, new_quantity):
        """수량 업데이트"""
        if new_quantity <= 0:
            self.delete()
        else:
            self.quantity = new_quantity
            self.save(update_fields=["quantity", "updated_at"])

    def check_stock_availability(self, store=None):
        """재고 확인"""
        if store:
            # 특정 매장의 재고 확인
            try:
                stock = self.product.stocks.get(store=store)
                return stock.quantity >= self.quantity
            except:
                return False
        else:
            # 전체 매장 재고 확인
            total_stock = sum(stock.quantity for stock in self.product.stocks.all())
            return total_stock >= self.quantity

    def get_available_stores(self):
        """해당 수량만큼 재고가 있는 매장들 반환"""
        available_stores = []
        for stock in self.product.stocks.filter(quantity__gte=self.quantity):
            if stock.store.is_open:  # 운영 중인 매장만
                available_stores.append(stock.store)
        return available_stores

    def can_checkout(self, store):
        """해당 매장에서 주문 가능한지 확인"""
        return self.check_stock_availability(store) and store.is_open and self.product.status == "ACTIVE"
