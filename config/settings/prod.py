from typing import Any, Dict

from config.settings.base import *

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
STATIC_ROOT = "/root/hanjan/media"
MEDIA_ROOT = "/root/hanjan/media"

# CSRF 설정
CSRF_TRUSTED_ORIGINS = [
    "https://hanjantest.store",
    "https://www.hanjantest.store",
]
