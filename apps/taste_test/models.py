from django.conf import settings
from django.db import models


class PreferenceTestResult(models.Model):
    """사용자 취향 테스트 결과"""

    class PreferTaste(models.TextChoices):
        SWEET_FRUIT = "SWEET_FRUIT", "달콤과일파"
        FRESH_FIZZY = "FRESH_FIZZY", "상큼톡톡파"
        HEAVY_LINGERING = "HEAVY_LINGERING", "묵직여운파"
        CLEAN_SAVORY = "CLEAN_SAVORY", "깔끔고소파"
        FRAGRANT_NEAT = "FRAGRANT_NEAT", "향긋단정파"
        FRESH_CLEAN = "FRESH_CLEAN", "상큼깔끔파"
        HEAVY_SWEET = "HEAVY_SWEET", "묵직달콤파"
        SWEET_SAVORY = "SWEET_SAVORY", "달콤고소파"
        GOURMET = "GOURMET", "미식가유형"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preference_test_result"
    )
    answers = models.JSONField(help_text="테스트 답변 (예: {'Q1': 'A', 'Q2': 'B', 'Q3': 'C'})")
    prefer_taste = models.CharField(max_length=20, choices=PreferTaste.choices, help_text="분석된 취향 유형")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "preference_test_results"
        indexes = [
            models.Index(fields=["prefer_taste"]),
            models.Index(fields=["-created_at"]),
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 동적 속성 초기화 (mypy 타입 체크용)
        self.profile_update_result = None

    def __str__(self):
        return f"{self.user.nickname} - {self.get_prefer_taste_display()}"

    def get_taste_description(self):
        """취향 유형별 설명 반환"""
        # services.py의 TASTE_TYPES에서 가져오도록 위임
        from .services import TasteTestService

        return TasteTestService.get_type_info_by_enum(self.prefer_taste).get("description", "")

    def get_recommended_taste_profile(self):
        """취향 유형별 추천 맛 프로필 반환"""
        from .services import TasteTestService

        return TasteTestService.get_taste_type_base_scores(self.prefer_taste)
