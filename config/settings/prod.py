import os
from typing import Any, Dict

import sentry_sdk

from config.settings.base import *

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    send_default_pii=True,
    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", 1)),
    profile_session_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", 1)),
    profile_lifecycle="trace",
)

DEBUG = False
ALLOWED_HOSTS = [host.strip() for host in os.environ.get("ALLOWED_HOSTS", "").split(",") if host.strip()]

DATABASES: Dict[str, Dict[str, Any]] = {  # type: ignore[no-redef]
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        "OPTIONS": {"options": "-c search_path=hanjan"},
    }
}

# Static files 설정
STATIC_URL = "/static/"
STATIC_ROOT = "/root/hanjan/static"
MEDIA_URL = "/media/"
MEDIA_ROOT = "/root/hanjan/media"

# CORS 설정 (프로덕션)
CORS_ALLOWED_ORIGINS = [
    "https://hanjantest.store",
    "https://www.hanjantest.store",
    # 프론트엔드 도메인이 다르면 여기에 추가
    "https://moeun.kro.kr",
    # 프론트엔드 로컬에서 api연동 테스트를 위한 허용
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True

# CSRF 설정
CSRF_TRUSTED_ORIGINS = [
    "https://hanjantest.store",
    "https://www.hanjantest.store",
    "https://moeun.kro.kr",
    # 프론트엔드 로컬에서 api연동 테스트를 위한 허용
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 보안 설정
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# 로깅 설정 (프로덕션) - 임시 주석 처리
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "file": {
#             "class": "logging.FileHandler",
#             "filename": "/var/log/django/django.log",
#         },
#         "console": {
#             "class": "logging.StreamHandler",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["file", "console"],
#             "level": "WARNING",
#         },
#         "apps": {
#             "handlers": ["file", "console"],
#             "level": "INFO",
#         },
#     },
# }
