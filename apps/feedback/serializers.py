from django.utils import timezone
from rest_framework import serializers

from apps.orders.models import OrderItem

from .models import Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    order_item_id = serializers.IntegerField(write_only=True)

    # 응답에 추가될 필드
    product_name = serializers.CharField(source="order_item.product.name", read_only=True)
    order_date = serializers.DateTimeField(source="order_item.order.created_at", read_only=True)

    # selected_tags는 이제 모델의 JSONField와 직접 매핑됨
    # 유효성 검사를 통해 리스트 형태이고, 최대 3개인지 확인
    selected_tags = serializers.ListField(child=serializers.CharField(max_length=50), max_length=3, required=False)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "user",
            "order_item_id",
            "product_name",
            "order_date",
            "sweetness",
            "acidity",
            "body",
            "confidence",
            "overall_rating",
            "photo_url",
            "comment",
            "detailed_comment",
            "selected_tags",
            "view_count",
            "days_after_purchase",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "view_count",
            "days_after_purchase",
            "created_at",
            "updated_at",
            "product_name",
            "order_date",
        ]

    def validate_order_item_id(self, value):
        try:
            order_item = OrderItem.objects.select_related("order").get(id=value)
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError("주문 내역을 찾을 수 없습니다.")

        if order_item.order.user != self.context["request"].user:
            raise serializers.ValidationError("피드백을 작성할 권한이 없습니다.")

        if hasattr(order_item, "feedback"):
            raise serializers.ValidationError("이미 이 상품에 대한 피드백을 작성했습니다.")

        # 검증이 끝나면 controller에서 사용할 수 있도록 order_item 객체를 context에 저장
        self.context["order_item"] = order_item
        return value

    def create(self, validated_data):
        # context에서 order_item 객체를 가져옴
        order_item = self.context.pop("order_item")

        # 구매 후 경과일 계산
        days_after_purchase = (timezone.now() - order_item.order.created_at).days
        validated_data["days_after_purchase"] = days_after_purchase

        validated_data["order_item"] = order_item
        return super().create(validated_data)
