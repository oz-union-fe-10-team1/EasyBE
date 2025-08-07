import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Order(models.Model):
    """주문"""

    class Status(models.TextChoices):
        PENDING = "PENDING", "주문 완료"
        CONFIRMED = "CONFIRMED", "주문 확인"
        READY = "READY", "픽업 준비 완료"
        COMPLETED = "COMPLETED", "픽업 완료"
        CANCELLED = "CANCELLED", "주문 취소"

    id = models.BigAutoField(primary_key=True)
    order_number = models.CharField(max_length=20, unique=True, help_text="사용자에게 보여줄 주문 번호")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")

    # 주문 금액
    total_price = models.PositiveIntegerField(help_text="총 주문 금액")

    # 주문 상태
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "orders"
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["order_number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """주문 번호 생성 (예: ORD20250107001)"""
        today = timezone.now().strftime("%Y%m%d")

        # 오늘 생성된 주문 수 + 1
        today_orders_count = Order.objects.filter(created_at__date=timezone.now().date()).count()

        sequence = str(today_orders_count + 1).zfill(3)
        return f"ORD{today}{sequence}"

    def __str__(self):
        return f"주문 {self.order_number} - {self.user.nickname}"

    def can_cancel(self):
        """취소 가능한지 확인"""
        return self.status in [self.Status.PENDING, self.Status.CONFIRMED]

    def cancel(self):
        """주문 취소"""
        if self.can_cancel():
            self.status = self.Status.CANCELLED
            self.save(update_fields=["status", "updated_at"])

            # 재고 복구
            for item in self.items.all():
                item.restore_stock()
            return True
        return False

    def mark_ready(self):
        """픽업 준비 완료"""
        if self.status == self.Status.CONFIRMED:
            self.status = self.Status.READY
            self.save(update_fields=["status", "updated_at"])

    def complete(self):
        """주문 완료 (픽업 완료)"""
        if self.status == self.Status.READY:
            self.status = self.Status.COMPLETED
            self.save(update_fields=["status", "updated_at"])


class OrderItem(models.Model):
    """주문 아이템"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="order_items")

    # 주문 당시의 가격 (가격 변동에 영향 받지 않도록)
    price = models.PositiveIntegerField(help_text="주문 당시 상품 단가")
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)], help_text="주문 수량")

    # 픽업 정보
    pickup_store = models.ForeignKey(
        "stores.Store", on_delete=models.CASCADE, related_name="order_items", help_text="픽업 매장"
    )
    pickup_day = models.DateField(help_text="픽업 예정 날짜")
    pickup_status = models.BooleanField(default=False, help_text="픽업 완료 여부")

    # 선물 관련
    is_gift = models.BooleanField(default=False, help_text="선물 포장 여부")
    gift_message = models.TextField(null=True, blank=True, help_text="선물 메시지")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_items"
        indexes = [
            models.Index(fields=["order"]),
            models.Index(fields=["product"]),
            models.Index(fields=["pickup_store"]),
            models.Index(fields=["pickup_day"]),
            models.Index(fields=["pickup_status"]),
        ]

    def __str__(self):
        return f"{self.order.order_number} - {self.product.name} x{self.quantity}"

    @property
    def total_price(self):
        """해당 아이템의 총 가격"""
        return self.price * self.quantity

    def reserve_stock(self):
        """재고 차감 (주문 시)"""
        try:
            stock = self.product.stocks.get(store=self.pickup_store)
            if stock.reduce_stock(self.quantity):
                return True
            else:
                raise ValueError("재고가 부족합니다")
        except:
            raise ValueError("해당 매장에 재고가 없습니다")

    def restore_stock(self):
        """재고 복구 (주문 취소 시)"""
        try:
            stock = self.product.stocks.get(store=self.pickup_store)
            stock.add_stock(self.quantity)
        except:
            # 재고 정보가 없으면 새로 생성
            from apps.stores.models import ProductStock

            ProductStock.objects.create(product=self.product, store=self.pickup_store, quantity=self.quantity)

    def mark_picked_up(self):
        """픽업 완료 처리"""
        self.pickup_status = True
        self.save(update_fields=["pickup_status"])

        # 모든 아이템이 픽업 완료되면 주문 완료
        if not self.order.items.filter(pickup_status=False).exists():
            self.order.complete()

    def can_pickup(self):
        """픽업 가능한지 확인"""
        return self.order.status in [Order.Status.CONFIRMED, Order.Status.READY] and not self.pickup_status
