"""
메시지 생성 유틸리티
"""

from typing import Dict


class MessageGenerator:
    """사용자 메시지 생성"""

    @staticmethod
    def generate_preview_message(review_count: int, test_influence: float, change_count: int) -> str:
        """재테스트 미리보기 메시지 생성"""
        if review_count < 5:
            base_msg = f"초기 단계라 테스트 결과가 {int(test_influence * 100)}% 반영됩니다."
        elif review_count < 20:
            base_msg = f"기존 학습과 새 테스트 결과를 {int(test_influence * 100)}% 비율로 조합합니다."
        else:
            base_msg = f"오랜 경험이 쌓여서 새 테스트 결과는 {int(test_influence * 100)}%만 반영됩니다."

        if change_count == 0:
            return f"{base_msg} 큰 변화는 예상되지 않습니다."
        elif change_count <= 2:
            return f"{base_msg} 일부 취향에서 미세한 변화가 예상됩니다."
        else:
            return f"{base_msg} 여러 취향 요소에서 변화가 예상됩니다."

    @staticmethod
    def generate_profile_action_message(action: str, **kwargs) -> Dict:
        """프로필 처리 결과 메시지 생성"""
        if action == "initialized":
            return {"action": "initialized", "message": "취향 프로필이 초기화되었습니다."}

        elif action == "retake_applied":
            return {
                "action": "retake_applied",
                "influence_rate": kwargs.get("influence_rate", "알 수 없음"),
                "changes_made": kwargs.get("changes_made", []),
                "message": kwargs.get("message", "재테스트 결과가 반영되었습니다."),
            }

        elif action == "no_change":
            return {"action": "no_change", "message": "기존 테스트 결과가 유지됩니다."}

        elif action == "skipped":
            return {"action": "skipped", "message": "취향 프로필 처리를 건너뛰었습니다."}

        else:
            return {"action": "unknown", "message": "알 수 없는 처리 결과입니다."}