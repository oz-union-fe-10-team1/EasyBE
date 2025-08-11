from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class CartItem(models.Model):
    """장바구니 아이템"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, help_text="수량")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "장바구니 항목"
        verbose_name_plural = "장바구니 항목 목록"
        db_table = "cart_items"
        unique_together = ("user", "product")  # 사용자당 상품별로 하나씩만
        ordering = ["-created_at"]
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
