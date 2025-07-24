from rest_framework import serializers

from .models import User


class KakaoLoginSerializer(serializers.Serializer):
    """카카오 로그인 요청 데이터"""

    code = serializers.CharField(help_text="카카오에서 받은 authorization code")


class NaverLoginSerializer(serializers.Serializer):
    """네이버 로그인 요청 데이터"""

    code = serializers.CharField(help_text="네이버에서 받은 authorization code")
    state = serializers.CharField(help_text="네이버에서 받은 state 값")

class GoogleLoginSerializer(serializers.Serializer):
    """구글 로그인 요청 데이터"""
    code = serializers.CharField(help_text="구글에서 받은 authorization code")


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
