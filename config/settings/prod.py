from typing import Any, Dict

import sentry_sdk

from config.settings.base import *

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # Add data like request headers and IP for users;
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", 1)),
    # To collect profiles for all profile sessions,
    # set `profile_session_sample_rate` to 1.0.
    profile_session_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", 1)),
    # Profiles will be automatically collected while
    # there is an active span.
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
MEDIA_ROOT = "/root/hanjan/media"

# CSRF 설정
CSRF_TRUSTED_ORIGINS = [
    "https://hanjantest.store",
    "https://www.hanjantest.store",
]
