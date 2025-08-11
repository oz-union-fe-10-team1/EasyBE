from rest_framework import serializers

from apps.orders.models import Order, OrderItem
from apps.products.models import Product  # Product 모델 직접 임포트
from apps.stores.serializers import StoreSerializer


class SimpleProductSerializer(serializers.ModelSerializer):
    """주문 내역에 필요한 최소한의 상품 정보 시리얼라이저"""

    main_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "main_image_url"]

    def get_main_image_url(self, obj):
        # Product 모델에 main_image_url property가 있다고 가정
        # 없다면, obj.images.filter(is_main=True).first().image_url 등으로 구현 필요
        if hasattr(obj, 'main_image_url'):
            return obj.main_image_url
        # ProductImage 모델을 직접 참조해야 할 경우
        main_image = obj.images.filter(is_main=True).first()
        return main_image.image_url if main_image else None


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer(read_only=True)
    pickup_store = StoreSerializer(read_only=True)
    feedback_id = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "product",
            "quantity",
            "price",
            "pickup_store",
            "pickup_day",
            "pickup_status",
            "is_gift",
            "gift_message",
            "feedback_id",
        ]
        read_only_fields = fields

    def get_feedback_id(self, obj):
        if hasattr(obj, "feedback") and obj.feedback:
            return obj.feedback.id
        return None


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "user",
            "total_price",
            "status",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = fields
