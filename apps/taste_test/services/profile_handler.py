"""
프로필 처리 서비스
"""

from typing import Dict

from ..utils import MessageGenerator
from .analyzer import TypeAnalyzer


class ProfileHandler:
    """취향 프로필 처리 및 재테스트 관리"""

    @staticmethod
    def handle_taste_profile(user, test_result, is_new_test):
        """PreferTasteProfile 초기화/업데이트 처리 (개선된 재테스트 지원)"""
        try:
            from django.apps import apps

            PreferTasteProfile = apps.get_model("users", "PreferTasteProfile")

            profile, profile_created = PreferTasteProfile.objects.get_or_create(user=user)

            if profile_created or profile.total_reviews_count == 0:
                # 첫 테스트 또는 리뷰 경험이 없는 경우
                profile.initialize_from_test_result(test_result)
                return MessageGenerator.generate_profile_action_message("initialized")

            elif not is_new_test:
                # 재테스트인 경우
                retake_result = profile.handle_retake(test_result)
                return MessageGenerator.generate_profile_action_message(
                    "retake_applied",
                    influence_rate=retake_result["influence_rate"],
                    changes_made=retake_result["changes_made"],
                    message=retake_result["message"]
                )

            else:
                # 이미 테스트가 있는데 새 테스트로 들어온 경우 (예외 상황)
                return MessageGenerator.generate_profile_action_message("no_change")

        except (ImportError, LookupError):
            # PreferTasteProfile이 없는 경우
            return MessageGenerator.generate_profile_action_message("skipped")

    @staticmethod
    def get_retake_preview(user, answers: Dict[str, str]) -> Dict:
        """재테스트 시 변화 미리보기 (실제 저장하지 않음)"""
        try:
            from django.apps import apps
            from ..constants import TASTE_PROFILES

            PreferTasteProfile = apps.get_model("users", "PreferTasteProfile")

            # 현재 프로필 가져오기
            profile = PreferTasteProfile.objects.get(user=user)

            # 새 테스트 결과 계산
            test_result_data = TypeAnalyzer.process_complete_analysis(answers)
            korean_type = test_result_data["type"]

            enum_value = URLHelper.get_enum_by_korean_name(korean_type)
            if not enum_value:
                enum_value = "GOURMET"

            # 새로운 기본 점수
            new_base_scores = TASTE_PROFILES.get(enum_value, TASTE_PROFILES["GOURMET"])

            # 영향력 계산
            review_count = profile.total_reviews_count
            if review_count < 5:
                test_influence = 0.8
            elif review_count < 20:
                test_influence = 0.4
            else:
                test_influence = 0.1

            current_influence = 1.0 - test_influence

            # 변화 미리보기 계산
            preview_changes = {}
            taste_names = {
                "sweetness_level": "단맛",
                "acidity_level": "산미",
                "body_level": "바디감",
                "carbonation_level": "탄산감",
                "bitterness_level": "쓴맛",
                "aroma_level": "향",
            }

            for field in taste_names.keys():
                current_value = float(getattr(profile, field))
                new_base_value = float(new_base_scores[field])

                predicted_value = (current_value * current_influence) + (new_base_value * test_influence)
                predicted_value = max(0.0, min(5.0, predicted_value))

                change = predicted_value - current_value

                if abs(change) >= 0.2:
                    preview_changes[field] = {
                        "name": taste_names[field],
                        "current": round(current_value, 1),
                        "predicted": round(predicted_value, 1),
                        "change": round(change, 1),
                        "direction": "증가" if change > 0 else "감소",
                    }

            return {
                "new_type": korean_type,
                "current_type": TypeAnalyzer.get_type_info_by_enum(profile.user.preference_test_result.prefer_taste)["name"],
                "influence_rate": f"{int(test_influence * 100)}%",
                "review_count": review_count,
                "predicted_changes": preview_changes,
                "message": MessageGenerator.generate_preview_message(review_count, test_influence, len(preview_changes)),
            }

        except Exception as e:
            return {"error": "미리보기를 생성할 수 없습니다.", "details": str(e)}