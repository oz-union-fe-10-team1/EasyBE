from rest_framework import serializers
from .models import Feedback
from apps.orders.models import OrderItem

# 임시 맛 태그 선택지 (나중에 실제 12가지로 교체)
TASTE_TAG_CHOICES = [
    "단맛", "신맛", "쓴맛", "과일향", "꽃향", "허브향",
    "진한맛", "가벼운맛", "탄산감", "감칠맛", "떫은맛", "견과류향",
]

class FeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    order_item_id = serializers.IntegerField(write_only=True)

    # 요청 시에는 리스트로 받고, 응답 시에는 문자열을 리스트로 변환하여 보여줌
    taste_tags = serializers.ListField(
        child=serializers.ChoiceField(choices=TASTE_TAG_CHOICES),
        write_only=True,
        max_length=3,
        help_text="맛 태그 목록 (최대 3개)",
        required=False # 선택 사항이므로 필수 아님
    )
    selected_tags = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Feedback
        fields = [
            'id', 'user', 'order_item_id', 'sweetness', 'acidity', 'body',
            'confidence', 'overall_rating', 'photo_url', 'comment', 'detailed_comment',
            'taste_tags', 'selected_tags', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_selected_tags(self, obj):
        return obj.taste_tags.split(',') if obj.taste_tags else []

    def _handle_taste_tags(self, validated_data):
        if 'taste_tags' in validated_data:
            tags_list = validated_data.pop('taste_tags', [])
            validated_data['taste_tags'] = ','.join(tags_list)
        return validated_data

    def create(self, validated_data):
        validated_data = self._handle_taste_tags(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._handle_taste_tags(validated_data)
        return super().update(instance, validated_data)

    def validate_order_item_id(self, value):
        # ... (기존 검증 로직 유지) ...
        try:
            order_item = OrderItem.objects.get(id=value)
        except OrderItem.DoesNotExist:
            raise serializers.ValidationError("주문 내역을 찾을 수 없습니다.")
        if order_item.order.user != self.context['request'].user:
            raise serializers.ValidationError("피드백을 작성할 권한이 없습니다.")
        if Feedback.objects.filter(order_item=order_item).exists():
            raise serializers.ValidationError("이미 이 상품에 대한 피드백을 작성했습니다.")
        return value