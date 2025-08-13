from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"

    def ready(self):
        """앱 초기화 시 Signal 등록"""
        import apps.users.utils.signals  # utils/signals.py에서 Signal 핸들러 등록