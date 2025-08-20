from rest_framework import serializers
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PreferTasteProfile, User


class StateSerializer(serializers.Serializer):
    """소셜 로그인 용 state"""

    state = serializers.CharField(help_text="임시 저장할 state 값")


class KakaoLoginSerializer(serializers.Serializer):
    """카카오 로그인 요청 데이터"""

    code = serializers.CharField(help_text="카카오에서 받은 authorization code")
    # state = serializers.CharField(help_text="카카오에서 받은 state 값")


class NaverLoginSerializer(serializers.Serializer):
    """네이버 로그인 요청 데이터"""

    code = serializers.CharField(help_text="네이버에서 받은 authorization code")
    state = serializers.CharField(help_text="네이버에서 받은 state 값")


class GoogleLoginSerializer(serializers.Serializer):
    """구글 로그인 요청 데이터"""

    code = serializers.CharField(help_text="구글에서 받은 authorization code")
    # state = serializers.CharField(help_text="구글에서 받은 state 값")


class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 응답"""

    class Meta:
        model = User
        fields = ["nickname", "email", "role", "created_at", "notification_agreed"]


class UserUpdateSerializer(serializers.ModelSerializer):
    """사용자 정보 수정용 시리얼라이저 (닉네임, 알림 동의)"""

    generate_random_nickname = serializers.BooleanField(
        required=False, write_only=True, help_text="랜덤 닉네임 생성 요청"
    )

    class Meta:
        model = User
        fields = ["nickname", "notification_agreed", "generate_random_nickname"]

    def validate_nickname(self, value):
        """닉네임 유효성 검사"""
        if not value or not value.strip():
            raise serializers.ValidationError("닉네임은 필수입니다.")

        if len(value.strip()) < 2:
            raise serializers.ValidationError("닉네임은 최소 2자 이상이어야 합니다.")

        if len(value.strip()) > 20:
            raise serializers.ValidationError("닉네임은 최대 20자까지 가능합니다.")

        # 현재 사용자가 아닌 다른 사용자가 같은 닉네임을 사용하고 있는지 확인
        if User.objects.exclude(pk=self.instance.pk).filter(nickname=value.strip()).exists():
            raise serializers.ValidationError("이미 사용 중인 닉네임입니다.")

        return value.strip()

    def validate(self, attrs):
        """전체 데이터 유효성 검사"""
        # 랜덤 닉네임 생성 요청 시 닉네임 필드 무시
        if attrs.get("generate_random_nickname"):
            # nickname 필드가 있어도 무시하고 랜덤 생성할 예정
            attrs.pop("nickname", None)

        return attrs

    def update(self, instance, validated_data):
        """사용자 정보 업데이트"""
        generate_random = validated_data.pop("generate_random_nickname", False)

        if generate_random:
            from apps.users.utils.nickname_generator import NicknameGenerator

            validated_data["nickname"] = NicknameGenerator.generate_unique_nickname(User)

        return super().update(instance, validated_data)


class LoginResponseSerializer(serializers.Serializer):
    """로그인 성공 응답"""

    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer()
    auth_type = serializers.CharField(help_text="new_user, existing_social, linked_to_existing")


class TasteProfileSerializer(serializers.ModelSerializer):
    """취향 프로필 응답"""

    taste_scores = serializers.SerializerMethodField()
    description = serializers.CharField(source="analysis_description")

    class Meta:
        model = PreferTasteProfile
        fields = ["id", "taste_scores", "description"]

    def get_taste_scores(self, obj):
        """맛 점수들을 딕셔너리로 반환"""
        return obj.get_taste_scores_dict()


class UserRestoreSerializer(serializers.Serializer):
    email = serializers.CharField()
    code = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        help_text="로그아웃할 사용자의 refresh token", write_only=True, style={"input_type": "text"}
    )

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            refresh_token = RefreshToken(self.token)
            refresh_token.blacklist()
        except TokenError:
            raise serializers.ValidationError("Invalid or expired token")
