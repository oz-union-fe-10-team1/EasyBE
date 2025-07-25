from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.serializers.product import ProductDetailSerializer # ProductDetailSerializer를 가져옵니다.


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer(read_only=True) # 상품 상세 정보를 읽기 전용으로 포함
    product_id = serializers.CharField(write_only=True) # 상품 ID는 쓰기 전용으로 받음

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_id", "quantity", "price", "subtotal"]
        read_only_fields = ["id", "product", "price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True) # 주문 상품 목록을 중첩하여 포함
    total_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "total_price", "status", "created_at", "updated_at", "items"]
        read_only_fields = ["id", "user", "total_price", "status", "created_at", "updated_at"]


