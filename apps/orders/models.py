from django.conf import settings
from django.db import models
from apps.products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "대기중"),
        ("processing", "처리중"),
        ("shipped", "배송중"),
        ("delivered", "배송완료"),
        ("cancelled", "취소됨"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="주문자",
    )
    total_price = models.DecimalField(
        max_digits=10, decimal_places=0, verbose_name="총 가격"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="주문 상태"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="주문일")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="수정일")

    class Meta:
        verbose_name = "주문"
        verbose_name_plural = "주문 목록"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="주문"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, verbose_name="상품"
    )
    quantity = models.PositiveIntegerField(verbose_name="수량")
    price = models.DecimalField(
        max_digits=10, decimal_places=0, verbose_name="단가"
    )

    class Meta:
        verbose_name = "주문 상품"
        verbose_name_plural = "주문 상품 목록"
        unique_together = ("order", "product")

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"

    @property
    def subtotal(self):
        return self.quantity * self.price