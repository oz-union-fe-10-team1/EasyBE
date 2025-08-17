"""
응답 관련 시리얼라이저
"""

from rest_framework import serializers

from ..services import TasteTestService


class TasteTestResultSerializer(serializers.Serializer):
    """테스트 결과 응답용 시리얼라이저"""

    type = serializers.CharField(help_text="결정된 취향 유형 (한국어)")
    scores = serializers.DictField(child=serializers.IntegerField(), help_text="각 기본 유형별 점수")
    info = serializers.DictField(help_text="유형 상세 정보")
    saved = serializers.BooleanField(default=False, help_text="DB 저장 여부")


class TasteTypeInfoSerializer(serializers.Serializer):
    """취향 유형 정보 시리얼라이저"""

    name = serializers.CharField(help_text="유형명")
    enum = serializers.CharField(help_text="enum 값")
    description = serializers.CharField(help_text="유형 설명")
    characteristics = serializers.ListField(child=serializers.CharField(), help_text="특징 목록")
    image_url = serializers.CharField(help_text="이미지 URL")