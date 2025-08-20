from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.stores.models import Store


class CartItem(models.Model):
    """장바구니 아이템"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="cart_items")
    quantity = models.PositiveIntegerField(default=1, help_text="수량")
    pickup_store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="cart_items_for_pickup",
        help_text="픽업 매장",
    )
    pickup_date = models.DateField(null=True, blank=True, help_text="픽업 날짜")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "장바구니 항목"
        verbose_name_plural = "장바구니 항목 목록"
        db_table = "cart_items"
        unique_together = ("user", "product", "pickup_store", "pickup_date")
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
