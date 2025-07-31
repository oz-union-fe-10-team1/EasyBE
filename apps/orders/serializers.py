from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.serializers.product import ProductDetailSerializer # ProductDetailSerializer를 가져옵니다.


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductDetailSerializer(read_only=True)
    feedback_id = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "price", "subtotal", "feedback_id"]
        read_only_fields = ["id", "product", "price", "subtotal"]

    def get_feedback_id(self, obj):
        """OrderItem에 연결된 Feedback이 있으면 ID를, 없으면 null을 반환"""
        # hasattr를 사용하여 이미 prefetch되었거나 select_related된 feedback 객체가 있는지 확인
        if hasattr(obj, 'feedback') and obj.feedback:
            return obj.feedback.id
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "total_price", "status", "created_at", "updated_at", "items"]
        read_only_fields = ["id", "user", "total_price", "status", "created_at", "updated_at"]

    def to_representation(self, instance):
        """N+1 문제를 방지하기 위해 prefetch_related 사용"""
        # items와 관련된 feedback을 미리 가져옴
        instance.items.select_related('feedback')
        return super().to_representation(instance)


