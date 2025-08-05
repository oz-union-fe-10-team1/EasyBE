import uuid

from django.conf import settings
from django.db import models


class Cart(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="사용자",
    )
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
    quantity = models.PositiveIntegerField(verbose_name="수량")
    package_group = models.UUIDField(null=True, blank=True, verbose_name="패키지 그룹 ID")

    class Meta:
        verbose_name = "장바구니 상품"
        verbose_name_plural = "장바구니 상품 목록"
        # unique_together는 패키지 상품 때문에 더 이상 유효하지 않음
        # 대신, 단일 상품에 대해서만 중복을 방지하는 로직이 필요

    def __str__(self):
        if self.package_group:
            return f"[패키지] {self.product.name}"
        return f"{self.product.name} (수량: {self.quantity})"

    @property
    def subtotal(self):
        # 패키지 상품의 가격은 별도 로직으로 계산될 수 있음 (여기서는 단순 곱으로 가정)
        return self.product.price * self.quantity
