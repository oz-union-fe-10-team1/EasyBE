from rest_framework import serializers
from .models import Feedback
from apps.orders.models import OrderItem


class FeedbackSerializer(serializers.ModelSerializer):
    # 응답에 보여줄 사용자 정보 (읽기 전용)
    user = serializers.StringRelatedField(read_only=True)
    
    # 요청 시 받을 주문 상품 ID (쓰기 전용)
    order_item_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id',
            'user',
            'order_item_id',
            'sweetness',
            'acidity',
            'body',
            'confidence',
            'overall_rating',
            'photo_url',
            'comment',
            'detailed_comment',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate_order_item_id(self, value):
        """요청받은 order_item_id가 유효한지, 현재 사용자가 작성할 수 있는지 검증"""
        try:
            order_item = OrderItem.objects.get(id=value)
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError("주문 내역을 찾을 수 없습니다.")

        # 현재 요청을 보낸 사용자가 해당 주문 상품의 소유자인지 확인
        if order_item.order.user != self.context['request'].user:
            raise serializers.ValidationError("피드백을 작성할 권한이 없습니다.")

        # 이미 해당 주문 상품에 대한 피드백이 존재하는지 확인
        if Feedback.objects.filter(order_item=order_item).exists():
            raise serializers.ValidationError("이미 이 상품에 대한 피드백을 작성했습니다.")

        return value
