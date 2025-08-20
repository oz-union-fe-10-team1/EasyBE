# apps/feedback/serializers.py

from rest_framework import serializers

from .models import TASTE_TAG_CHOICES, Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    # 이미지 업로드용 필드 (write_only)
    image = serializers.ImageField(write_only=True, required=False, help_text="피드백 이미지 파일")

    # 응답용 필드들 (read_only) - 모델 property 사용으로 통일
    image_url = serializers.URLField(read_only=True, help_text="업로드된 이미지 URL")
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.UUIDField(source="product.id", read_only=True)
    masked_username = serializers.CharField(read_only=True)
    has_image = serializers.BooleanField(read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "order_item",  # 필수 필드
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
            "image",  # 업로드용
            "image_url",  # 응답용
            "product_name",
            "product_id",
            "masked_username",
            "has_image",
            "view_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "view_count", "created_at", "updated_at"]

    def validate_order_item(self, value):
        """order_item 유효성 검사"""
        if not value:
            raise serializers.ValidationError("order_item은 필수 필드입니다.")

        # 요청한 사용자와 주문의 사용자가 일치하는지 확인 (추가 검증)
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            if value.order.user != request.user:
                raise serializers.ValidationError("본인의 주문에 대해서만 피드백을 작성할 수 있습니다.")

        return value

    def validate_selected_tags(self, value):
        """선택된 태그 유효성 검사"""
        if value:
            valid_tags = [choice[0] for choice in TASTE_TAG_CHOICES]
            invalid_tags = [tag for tag in value if tag not in valid_tags]
            if invalid_tags:
                raise serializers.ValidationError(f"허용되지 않은 태그: {invalid_tags}. " f"유효한 태그: {valid_tags}")
        return value

    def validate_image(self, value):
        """이미지 파일 유효성 검사 - 더 유연한 방식"""
        if value:
            # 파일 크기 제한 (예: 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("이미지 크기는 5MB를 초과할 수 없습니다.")

            # Content-Type과 파일 확장자 모두 체크
            allowed_content_types = ["image/jpeg", "image/png", "image/webp", "image/gif"]

            allowed_extensions = [".jpg", ".jpeg", ".png", ".webp", ".gif"]

            # 파일명에서 확장자 추출
            import os

            file_extension = os.path.splitext(value.name.lower())[1]

            # Content-Type 또는 확장자 중 하나라도 맞으면 허용
            content_type_valid = value.content_type in allowed_content_types
            extension_valid = file_extension in allowed_extensions

            if not (content_type_valid or extension_valid):
                raise serializers.ValidationError(
                    f"지원되지 않는 이미지 형식입니다. "
                    f"파일: {value.name} (타입: {value.content_type}), "
                    f"허용 확장자: {allowed_extensions}"
                )

        return value

    def create(self, validated_data):
        """피드백 생성 및 이미지 업로드"""
        # 이미지 파일 추출
        image_file = validated_data.pop("image", None)

        # 피드백 생성
        feedback = Feedback.objects.create(**validated_data)

        # 이미지 업로드 처리
        if image_file:
            success = self._upload_image(feedback, image_file)
            if not success:
                # 업로드 실패 시 피드백은 유지하고 경고만 로깅
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(f"피드백 {feedback.id}의 이미지 업로드 실패")

        return feedback

    def update(self, instance, validated_data):
        """피드백 수정 및 이미지 업데이트"""
        image_file = validated_data.pop("image", None)

        # 새 이미지가 있으면 기존 이미지 삭제 후 업로드
        if image_file:
            # 기존 이미지 삭제
            if instance.image_url:
                instance.delete_image()

            # 새 이미지 업로드
            self._upload_image(instance, image_file)

        # 나머지 필드 업데이트
        return super().update(instance, validated_data)

    def _upload_image(self, feedback_instance, image_file):
        """이미지 S3 업로드 헬퍼 메서드"""
        try:
            from core.utils.ncloud_manager import S3Uploader

            uploader = S3Uploader()

            # S3 키 생성 (feedback/{feedback_id}/{timestamp}_{filename})
            from django.utils import timezone

            timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"feedback/{feedback_instance.id}/{timestamp}_{image_file.name}"

            # S3에 업로드
            image_url = uploader.upload_file(image_file, s3_key)

            if image_url:
                feedback_instance.image_url = image_url
                feedback_instance.save(update_fields=["image_url"])
                return True

            return False

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"이미지 업로드 실패: {e}")
            return False


class FeedbackListSerializer(serializers.ModelSerializer):
    """피드백 목록용 간소화된 시리얼라이저"""

    product_name = serializers.CharField(source="product.name", read_only=True)
    product_id = serializers.UUIDField(source="product.id", read_only=True)  # 추가
    masked_username = serializers.CharField(read_only=True)
    has_image = serializers.BooleanField(read_only=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "rating",
            "comment",
            "selected_tags",
            "image_url",
            "product_name",
            "product_id",  # 추가
            "masked_username",
            "has_image",
            "view_count",
            "created_at",
        ]