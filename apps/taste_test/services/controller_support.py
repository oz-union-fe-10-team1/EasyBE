"""
컨트롤러 지원 서비스 - 뷰에서 사용할 고수준 서비스 메서드들
"""

from rest_framework import status
from rest_framework.response import Response

from ..models import PreferenceTestResult
from .base import TasteTestService


class ControllerService:
    """컨트롤러에서 사용할 고수준 서비스 메서드들"""

    @staticmethod
    def get_test_questions() -> Response:
        """테스트 질문 목록 조회"""
        questions = TasteTestService.get_questions()
        return Response(questions, status=status.HTTP_200_OK)

    @staticmethod
    def submit_test_answers(user, answers: dict) -> dict:
        """테스트 답변 제출 처리 (검증된 데이터만 받음)"""
        # 테스트 결과 계산
        result = TasteTestService.process_taste_test(answers)

        # 로그인 사용자의 경우 DB 저장
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
        # 기존 결과 확인
        if not ControllerService._has_existing_test_result(user):
            raise PreferenceTestResult.DoesNotExist("기존 테스트 결과가 없습니다.")

        # 결과 업데이트
        TasteTestService.save_test_result(user, answers)
        result = TasteTestService.process_taste_test(answers)
        result["saved"] = True

        return result

    @staticmethod
    def _has_existing_test_result(user) -> bool:
        """사용자의 기존 테스트 결과 존재 여부 확인"""
        try:
            PreferenceTestResult.objects.get(user=user)
            return True
        except PreferenceTestResult.DoesNotExist:
            return False