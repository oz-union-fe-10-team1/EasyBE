"""
URL 생성 헬퍼 유틸리티
"""

from typing import Optional

from django.conf import settings

from ..constants import TYPE_INFO


class URLHelper:
    """URL 생성 관련 유틸리티"""

    @staticmethod
    def get_base_url() -> str:
        """기본 URL 반환"""
        return getattr(settings, "BASE_URL", "http://localhost:8000")

    @staticmethod
    def get_image_url_by_enum(enum_value: str) -> str:
        """enum 값으로 이미지 URL 조회 (절대 URL 반환)"""
        # 유효한 enum인지 확인
        for type_info in TYPE_INFO.values():
            if type_info["enum"] == enum_value:
                base_url = URLHelper.get_base_url()
                filename = f"{enum_value.lower()}.png"
                return f"{base_url}/static/types/{filename}"

        # 존재하지 않는 enum의 경우 GOURMET 기본값 반환
        base_url = URLHelper.get_base_url()
        return f"{base_url}/static/types/gourmet.png"

    @staticmethod
    def get_enum_by_korean_name(korean_name: str) -> Optional[str]:
        """한국어 이름으로 enum 값 조회"""
        type_info = TYPE_INFO.get(korean_name)
        return str(type_info["enum"]) if type_info else None

    @staticmethod
    def get_all_image_urls() -> dict:
        """모든 취향 유형의 이미지 URL 딕셔너리 반환"""
        return {
            str(type_info["enum"]): URLHelper.get_image_url_by_enum(str(type_info["enum"]))
            for type_info in TYPE_INFO.values()
        }