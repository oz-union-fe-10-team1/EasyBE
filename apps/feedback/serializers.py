# apps/feedback/serializers.py

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import TASTE_TAG_CHOICES, Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    """피드백 시리얼라이저"""

    masked_username = serializers.SerializerMethodField()
    product = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "user",
            "order_item",
            "rating",
            "sweetness",
            "acidity",
            "body",
            "carbonation",
            "bitterness",
            "aroma",
            "confidence",
            "comment",
            "selected_tags",
            "view_count",
            "last_viewed_at",
            "created_at",
            "updated_at",
            "masked_username",
            "product",
        ]
        read_only_fields = ["user", "view_count", "last_viewed_at", "created_at", "updated_at"]

    @extend_schema_field(serializers.CharField())
    def get_masked_username(self, obj) -> str:
        """사용자명 마스킹 처리"""
        return obj.masked_username

    def validate_selected_tags(self, value):
        """태그 검증"""
        if value:
            valid_tags = [choice[0] for choice in TASTE_TAG_CHOICES]
            invalid_tags = [tag for tag in value if tag not in valid_tags]
            if invalid_tags:
                raise serializers.ValidationError(f"허용되지 않은 태그: {invalid_tags}")
        return value
