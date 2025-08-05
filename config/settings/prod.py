from config.settings.base import *
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(' ')

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
        'OPTIONS': {
           # 'sslmode': 'require',  # NCP는 SSL 연결 필수
            'options': '-c search_path=hanjan'
            }
    }
}

# Static files 설정
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# HTTPS 설정
#SECURE_SSL_REDIRECT = True
#SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
#USE_TLS = True

# CSRF 설정
CSRF_TRUSTED_ORIGINS = [
    "https://hanjantest.store",
    "https://www.hanjantest.store",
]