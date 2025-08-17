from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import serializers
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
        fields = ["nickname", "email", "role", "created_at"]


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
        help_text="로그아웃할 사용자의 refresh token",
        write_only=True,
        style={'input_type': 'text'}
    )

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            refresh_token = RefreshToken(self.token)
            refresh_token.blacklist()
        except TokenError:
            raise serializers.ValidationError('Invalid or expired token')
