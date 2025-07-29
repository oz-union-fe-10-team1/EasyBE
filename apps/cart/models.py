from django.conf import settings
from django.db import models


class Cart(models.Model):
    customer = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="고객",
    )
    pickup_store_name = models.CharField(max_length=100, null=True, blank=True, verbose_name="픽업 매장 이름")
    pickup_store_phone = models.CharField(max_length=20, null=True, blank=True, verbose_name="매장 전화번호")
    pickup_datetime = models.DateTimeField(null=True, blank=True, verbose_name="픽업 일시")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="생성일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "장바구니"
        verbose_name_plural = "장바구니 목록"

    def __str__(self):
        return f"{self.customer.username}의 장바구니"

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
