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
    answers = models.JSONField(help_text="테스트 답변 (예: {'q1': 'A', 'q2': 'B', 'q3': 'C'})")
    prefer_taste = models.CharField(max_length=20, choices=PreferTaste.choices, help_text="분석된 취향 유형")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "preference_test_results"
        indexes = [
            models.Index(fields=["prefer_taste"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.prefer_taste}"

    def get_taste_description(self):
        """취향 유형별 설명 반환 (추천 시스템에서 활용)"""
        taste_descriptions = {
            self.PreferTaste.SWEET_FRUIT: "달콤하고 과일향이 풍부한 술을 좋아합니다",
            self.PreferTaste.FRESH_FIZZY: "상큼하고 톡 쏘는 탄산감을 즐깁니다",
            self.PreferTaste.HEAVY_LINGERING: "묵직하고 여운이 깊은 술을 선호합니다",
            self.PreferTaste.CLEAN_SAVORY: "깔끔하고 고소한 맛을 좋아합니다",
            self.PreferTaste.FRAGRANT_NEAT: "향긋하고 단정한 술을 선호합니다",
            self.PreferTaste.FRESH_CLEAN: "상큼하고 깔끔한 맛을 즐깁니다",
            self.PreferTaste.HEAVY_SWEET: "묵직하면서도 달콤한 술을 좋아합니다",
            self.PreferTaste.SWEET_SAVORY: "달콤하면서 고소한 맛을 선호합니다",
            self.PreferTaste.GOURMET: "다양한 맛을 즐기는 미식가입니다",
        }
        return taste_descriptions.get(self.prefer_taste, "")

    def get_recommended_taste_profile(self):
        """취향 유형별 추천 맛 프로필 반환 (상품 추천에 활용)"""
        # 각 유형별로 어떤 맛 특성을 가진 상품을 추천할지 정의
        profile_mapping = {
            self.PreferTaste.SWEET_FRUIT: {
                "sweetness_level": (4.0, 5.0),
                "acidity_level": (2.0, 4.0),
                "alcohol_type": ["FRUIT_WINE", "MAKGEOLLI"],
            },
            self.PreferTaste.FRESH_FIZZY: {
                "carbonation_level": (3.0, 5.0),
                "acidity_level": (3.0, 5.0),
                "alcohol_type": ["MAKGEOLLI"],
            },
            self.PreferTaste.HEAVY_LINGERING: {
                "body_level": (4.0, 5.0),
                "alcohol_content": (15.0, 25.0),
                "alcohol_type": ["YAKJU", "CHEONGJU"],
            },
            # ... 나머지 유형들도 추가
        }
        return profile_mapping.get(self.prefer_taste, {})
