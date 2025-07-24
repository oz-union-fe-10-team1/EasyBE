from django.conf import settings
from django.db import models


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="사용자",
        null=True,
        blank=True,
    )
    session_key = models.CharField(max_length=40, null=True, blank=True, verbose_name="세션 키")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "장바구니"
        verbose_name_plural = "장바구니 목록"

    def __str__(self):
        return f"{self.user.username}의 장바구니"

    @property
    def total_price(self):
        return sum(item.subtotal for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="장바구니",
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="상품",
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="수량")

    class Meta:
        verbose_name = "장바구니 상품"
        verbose_name_plural = "장바구니 상품 목록"
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.product.name} (수량: {self.quantity})"

    @property
    def subtotal(self):
        return self.product.price * self.quantity
