from config.settings.base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# CORS 설정 (로컬환경 - 여러 개발서버 포트)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React 개발서버
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite 개발서버
    "http://127.0.0.1:5173",
    "http://localhost:8000",  # Django 개발서버
    "http://127.0.0.1:8000",
]
CORS_ALLOW_CREDENTIALS = True

# 개발환경용 추가 설정
# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "handlers": {
#         "console": {
#             "class": "logging.StreamHandler",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["console"],
#             "level": "INFO",
#         },
#     },
# }
