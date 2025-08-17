"""
컨트롤러 지원 서비스 - 뷰에서 사용할 고수준 서비스 메서드들
"""

from typing import Any, Dict, cast

from ..constants import TYPE_INFO
from ..models import PreferenceTestResult
from .base import TasteTestService


class ControllerService:
    """컨트롤러에서 사용할 고수준 서비스 메서드들"""

    @staticmethod
    def get_test_questions() -> list:
        """테스트 질문 목록 조회"""
        return TasteTestService.get_questions()

    @staticmethod
    def submit_test_answers(user, answers: dict) -> dict:
        """테스트 답변 제출 처리 (검증된 데이터만 받음)"""
        # 1. 테스트 결과 계산
        result = TasteTestService.process_taste_test(answers)

        # 2. 로그인 사용자의 경우 DB 저장
        saved = False
        if user.is_authenticated:
            try:
                TasteTestService.save_test_result(user, answers)
                saved = True
            except Exception:
                # 저장 실패해도 결과는 반환
                pass

        result["saved"] = saved
        return result

    @staticmethod
    def retake_test(user, answers: dict) -> dict:
        """테스트 재응시 처리 (검증된 데이터만 받음)"""
        # 1. 기존 결과 확인
        if not ControllerService._has_existing_test_result(user):
            raise PreferenceTestResult.DoesNotExist("기존 테스트 결과가 없습니다.")

        # 2. 결과 업데이트
        TasteTestService.save_test_result(user, answers)
        result = TasteTestService.process_taste_test(answers)
        result["saved"] = True

        return result

    @staticmethod
    def get_user_profile_data(user) -> dict:
        """사용자 프로필 데이터 조회"""
        has_test = hasattr(user, "preference_test_result")

        data = {"user": user.nickname, "has_test": has_test}

        if has_test:
            test_result = user.preference_test_result
            data.update(
                {
                    "id": test_result.id,
                    "prefer_taste": test_result.prefer_taste,
                    "prefer_taste_display": test_result.get_prefer_taste_display(),
                    "taste_description": test_result.get_taste_description(),
                    "image_url": TasteTestService.get_image_url_by_enum(test_result.prefer_taste),
                    "created_at": test_result.created_at,
                }
            )

        return data

    @staticmethod
    def get_taste_types_data() -> Dict[str, Any]:
        """취향 유형 목록 데이터 조회"""
        types_data = []

        for type_info in TYPE_INFO.values():
            type_info_copy = type_info.copy()
            # enum 값을 안전하게 str로 캐스팅
            enum_value = cast(str, type_info["enum"])
            type_info_copy["image_url"] = TasteTestService.get_image_url_by_enum(enum_value)
            types_data.append(type_info_copy)

        return {"types": types_data, "total": len(types_data)}

    @staticmethod
    def _has_existing_test_result(user) -> bool:
        """사용자의 기존 테스트 결과 존재 여부 확인"""
        try:
            PreferenceTestResult.objects.get(user=user)
            return True
        except PreferenceTestResult.DoesNotExist:
            return False
