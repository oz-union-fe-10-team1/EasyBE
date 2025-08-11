from django.core.cache import cache
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

class OAuthStateService:
    """OAuth State 관리 서비스"""

    @staticmethod
    def save_state(state_value):
        """State를 Redis에 저장"""
        cache_key = f"oauth_state:{state_value}"

        # 5분간 저장
        cache.set(
            cache_key,
            True,
            timeout=settings.OAUTH_STATE_EXPIRE_SECONDS
        )

        logger.info(f"OAuth state saved: {state_value[:8]}...")
        return True

    @staticmethod
    def verify_and_consume_state(state_value):
        """State 검증 후 즉시 삭제 (일회성)"""
        cache_key = f"oauth_state:{state_value}"

        # 존재하는지 확인
        if cache.get(cache_key):
            # 사용 후 즉시 삭제
            cache.delete(cache_key)
            logger.info(f"OAuth state verified and consumed: {state_value[:8]}...")
            return True

        logger.warning(f"Invalid or expired OAuth state: {state_value[:8]}...")
        return False