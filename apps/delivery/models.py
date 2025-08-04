from django.db import models

class Delivery(models.Model):
    class STATUS(models.TextChoices):
        PENDING = "pending", "배송 준비 중"
        SHIPPING = "shipping", "배송 중"
        DELIVERED = "delivered", "배송 완료"
        CANCELLED = "cancelled", "배송 취소"

    delivery_id = models.BigAutoField(primary_key=True)
    order_id = models.CharField(max_length=20, help_text="주문 번호 (예: ORD20250722001)")
    product_name = models.CharField(max_length=100, help_text="배송되는 상품명")
    status = models.CharField(max_length=20, choices=STATUS.choices, default="pending", help_text="배송 상태")
    tracking_number = models.CharField(max_length=50, blank=True, null=True,help_text="송장 번호")
    courier = models.CharField(max_length=50, blank=True, null=True, help_text="택배사 이름")
    estimated_arrival = models.DateField(blank=True, null=True,help_text="예상 도착일")
    updated_at = models.DateTimeField(auto_now=True, help_text="배송 정보 마지막 업데이트 시간")

    class Meta:
        db_table = "delivery"