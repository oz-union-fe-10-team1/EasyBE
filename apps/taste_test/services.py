"""
입맛 테스트 비즈니스 로직 서비스
"""

from decimal import Decimal
from typing import Dict, List, Optional

from django.conf import settings
from django.contrib.auth import get_user_model

from .models import PreferenceTestResult

User = get_user_model()


class TasteTestData:
    """테스트 데이터를 관리하는 클래스"""

    # 6개 질문
    QUESTIONS = [
        {
            "id": "Q1",
            "question": "카페에 가면 주로 시키는 메뉴는?",
            "options": {"A": "달콤한 바닐라 라떼나 과일 에이드", "B": "깔끔한 아메리카노나 고소한 곡물 라떼"},
        },
        {
            "id": "Q2",
            "question": "둘 중 더 좋아하는 과일 스타일은?",
            "options": {"A": "침이 고이는 레몬,유자,자몽", "B": "잘 익은 달콤한 수박,복숭아"},
        },
        {
            "id": "Q3",
            "question": "디저트를 딱 하나만 고른다면?",
            "options": {
                "A": "입안이 상쾌해지는 과일 소르베나 요거트 아이스크림",
                "B": "커피나 위스키가 생각나는 진한 치즈케이크나 티라미수",
            },
        },
        {
            "id": "Q4",
            "question": "평소 즐겨 마시는 음료는?",
            "options": {"A": "톡 쏘는 탄산수나 상큼한 콤부차", "B": "시원하고 깔끔한 보리차나 녹차"},
        },
        {
            "id": "Q5",
            "question": "맛있는 식사 후, 입안의 마무리는?",
            "options": {"A": "입안이 싹 정리되는 깔끔한 느낌", "B": "맛의 여운이 은은하게 남는 느낌"},
        },
        {
            "id": "Q6",
            "question": "특별한 날을 기념하기 위해, 술을 고른다면?",
            "options": {"A": "달콤해서 파티 분위기를 띄워주는 술", "B": "오랜 시간 숙성되어 깊고 진한 풍미를 가진 술"},
        },
    ]

    # 답변별 점수 매핑
    ANSWER_MAPPING = {
        "Q1": {"A": "달콤과일파", "B": "깔끔고소파"},
        "Q2": {"A": "상큼톡톡파", "B": "달콤과일파"},
        "Q3": {"A": "상큼톡톡파", "B": "묵직여운파"},
        "Q4": {"A": "상큼톡톡파", "B": "깔끔고소파"},
        "Q5": {"A": "깔끔고소파", "B": "묵직여운파"},
        "Q6": {"A": "달콤과일파", "B": "묵직여운파"},
    }

    # 9가지 취향 유형 정보
    TYPE_INFO = {
        "달콤과일파": {
            "name": "달콤과일파",
            "enum": "SWEET_FRUIT",
            "description": "당신은 부드럽고 달콤한 맛에서 행복을 느끼는군요!\n쓴맛이나 강한 신맛보다는, 입안 가득 퍼지는 과일의 향기와\n기분 좋은 달콤함을 즐기는 타입입니다.",
            "characteristics": ["달콤함", "과일향", "로맨틱", "부드러움"],
        },
        "상큼톡톡파": {
            "name": "상큼톡톡파",
            "enum": "FRESH_FIZZY",
            "description": "당신은 평범한 걸 거부한다!\n입맛을 깨우는 새콤함과 톡 쏘는 청량감에서 즐거움을 느끼는,\n활기 넘치는 타입입니다. 세련된 취향을 가졌네요.",
            "characteristics": ["상큼함", "톡톡함", "경쾌함", "청량감"],
        },
        "묵직여운파": {
            "name": "묵직여운파",
            "enum": "HEAVY_LINGERING",
            "description": "당신은 '술은 술다워야지' 라고 생각하는군요.\n알코올의 존재감이 느껴지는, 진하고 깊은 풍미와\n묵직한 여운을 즐기는 타입입니다.",
            "characteristics": ["묵직함", "진한맛", "여운", "존재감"],
        },
        "깔끔고소파": {
            "name": "깔끔고소파",
            "enum": "CLEAN_SAVORY",
            "description": "당신은 인위적인 맛보다는, 재료 본연의 깔끔하고 담백한 맛을 즐길 줄 아는 미식가시네요!\n쌀이나 곡물이 주는 은은한 고소함과\n군더더기 없는 마무리를 좋아합니다.",
            "characteristics": ["깔끔함", "고소함", "담백함", "자연스러움"],
        },
        "향긋단정파": {
            "name": "향긋단정파",
            "enum": "FRAGRANT_NEAT",
            "description": "강렬한 맛보다는 은은하게 피어오르는 꽃이나 과일 향기,\n그리고 부드러운 목넘김을 즐기는\n섬세한 타입입니다.",
            "characteristics": ["향긋함", "단정함", "섬세함", "우아함"],
        },
        "상큼깔끔파": {
            "name": "상큼깔끔파",
            "enum": "FRESH_CLEAN",
            "description": "상큼한 첫맛으로 입맛을 돋우되,\n끝맛은 군더더기 없이 깔끔하게 떨어지는 맛을 즐기는 당신!\n세련된 취향을 가졌네요.",
            "characteristics": ["상큼함", "깔끔함", "세련됨", "균형감"],
        },
        "묵직달콤파": {
            "name": "묵직달콤파",
            "enum": "HEAVY_SWEET",
            "description": "입안을 꽉 채우는 진한 질감과 함께 오는\n기분 좋은 달콤함을 선호하는 당신!\n디저트 와인처럼 풍성한 맛을 즐기는군요.",
            "characteristics": ["묵직함", "달콤함", "풍성함", "진한맛"],
        },
        "달콤고소파": {
            "name": "달콤고소파",
            "enum": "SWEET_SAVORY",
            "description": "달콤하지만 끝은 구수한, 밸런스 좋은 맛을 선호하는 당신!\n부드러운 첫인상과 담백한 마무리를\n모두 중요하게 생각하는군요.",
            "characteristics": ["달콤함", "고소함", "균형", "조화"],
        },
        "미식가유형": {
            "name": "미식가유형",
            "enum": "GOURMET",
            "description": "상황에 따라 다양한 술의 매력을 즐길 줄 아는 술 애호가입니다.\n새로운 술을 시도하는 데도 주저하지 않으며,\n어떤 술이든 그 자체의 맛을 음미할 줄 아는 폭넓은 스펙트럼의 균형 잡힌 미식가입니다.",
            "characteristics": ["다양성", "개방성", "균형감", "미식가적"],
        },
    }

    # 2개 유형 동점 시 혼합 유형 매핑
    MIXED_TYPE_MAPPING = {
        frozenset(["달콤과일파", "상큼톡톡파"]): "향긋단정파",
        frozenset(["달콤과일파", "묵직여운파"]): "묵직달콤파",
        frozenset(["달콤과일파", "깔끔고소파"]): "달콤고소파",
        frozenset(["상큼톡톡파", "묵직여운파"]): "상큼깔끔파",
        frozenset(["상큼톡톡파", "깔끔고소파"]): "상큼깔끔파",
        frozenset(["묵직여운파", "깔끔고소파"]): "향긋단정파",
    }

    # 타입별 기본 맛 프로필
    TASTE_PROFILES = {
        "SWEET_FRUIT": {
            "sweetness_level": 4.5,
            "acidity_level": 3.5,
            "body_level": 2.0,
            "carbonation_level": 2.0,
            "bitterness_level": 1.0,
            "aroma_level": 4.0,
        },
        "FRESH_FIZZY": {
            "sweetness_level": 2.0,
            "acidity_level": 4.5,
            "body_level": 2.0,
            "carbonation_level": 4.5,
            "bitterness_level": 1.5,
            "aroma_level": 3.0,
        },
        "HEAVY_LINGERING": {
            "sweetness_level": 2.5,
            "acidity_level": 2.0,
            "body_level": 4.5,
            "carbonation_level": 1.0,
            "bitterness_level": 3.5,
            "aroma_level": 4.0,
        },
        "CLEAN_SAVORY": {
            "sweetness_level": 1.5,
            "acidity_level": 2.0,
            "body_level": 3.0,
            "carbonation_level": 2.5,
            "bitterness_level": 2.0,
            "aroma_level": 2.5,
        },
        "FRAGRANT_NEAT": {
            "sweetness_level": 2.0,
            "acidity_level": 2.5,
            "body_level": 2.5,
            "carbonation_level": 2.0,
            "bitterness_level": 1.5,
            "aroma_level": 4.5,
        },
        "FRESH_CLEAN": {
            "sweetness_level": 2.0,
            "acidity_level": 4.0,
            "body_level": 2.0,
            "carbonation_level": 3.0,
            "bitterness_level": 1.5,
            "aroma_level": 3.0,
        },
        "HEAVY_SWEET": {
            "sweetness_level": 4.5,
            "acidity_level": 2.0,
            "body_level": 4.0,
            "carbonation_level": 1.5,
            "bitterness_level": 2.0,
            "aroma_level": 3.5,
        },
        "SWEET_SAVORY": {
            "sweetness_level": 4.0,
            "acidity_level": 2.0,
            "body_level": 3.5,
            "carbonation_level": 2.0,
            "bitterness_level": 2.5,
            "aroma_level": 3.0,
        },
        "GOURMET": {
            "sweetness_level": 3.0,
            "acidity_level": 3.0,
            "body_level": 3.5,
            "carbonation_level": 2.5,
            "bitterness_level": 3.0,
            "aroma_level": 4.0,
        },
    }

    @classmethod
    def get_enum_by_korean_name(cls, korean_name: str) -> Optional[str]:
        """한국어 이름으로 enum 값 조회"""
        type_info = cls.TYPE_INFO.get(korean_name)
        return str(type_info["enum"]) if type_info else None

    @classmethod
    def get_image_url_by_enum(cls, enum_value: str) -> str:
        """enum 값으로 이미지 URL 조회 (절대 URL 반환)"""
        # 유효한 enum인지 확인
        for type_info in cls.TYPE_INFO.values():
            if type_info["enum"] == enum_value:
                base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
                filename = f"{enum_value.lower()}.png"
                return f"{base_url}/api/v1/taste-test/images/types/{filename}"

        # 존재하지 않는 enum의 경우 GOURMET 기본값 반환
        base_url = getattr(settings, "BASE_URL", "http://localhost:8000")
        return f"{base_url}/api/v1/taste-test/images/types/gourmet.png"


class TasteTestService:
    """입맛 테스트 서비스 (진화하는 취향 시스템 지원)"""

    @staticmethod
    def get_questions() -> List[Dict]:
        """질문 목록 반환"""
        return TasteTestData.QUESTIONS

    @staticmethod
    def calculate_scores(answers: Dict[str, str]) -> Dict[str, int]:
        """답변을 기반으로 각 유형별 점수 계산"""
        scores = {"달콤과일파": 0, "상큼톡톡파": 0, "묵직여운파": 0, "깔끔고소파": 0}

        for question_id, answer in answers.items():
            if question_id in TasteTestData.ANSWER_MAPPING:
                taste_type = TasteTestData.ANSWER_MAPPING[question_id].get(answer)
                if taste_type in scores:
                    scores[taste_type] += 1

        return scores

    @staticmethod
    def determine_type(scores: Dict[str, int]) -> str:
        """점수를 바탕으로 최종 유형 결정"""
        max_score = max(scores.values())
        top_types = [type_name for type_name, score in scores.items() if score == max_score]

        # 단일 유형 (3점 이상)
        if max_score >= 3 and len(top_types) == 1:
            return top_types[0]

        # 2개 유형 동점 - 혼합 유형
        if max_score == 2 and len(top_types) == 2:
            combination = frozenset(top_types)
            return TasteTestData.MIXED_TYPE_MAPPING.get(combination, "미식가유형")

        # 기타 경우
        return "미식가유형"

    @staticmethod
    def get_type_info(korean_name: str) -> Dict:
        """한국어 유형명으로 유형 정보 반환 (절대 URL로 변환)"""
        type_info = TasteTestData.TYPE_INFO.get(korean_name, TasteTestData.TYPE_INFO["미식가유형"]).copy()
        # 절대 URL로 변환
        type_info["image_url"] = TasteTestData.get_image_url_by_enum(str(type_info["enum"]))
        return type_info

    @staticmethod
    def get_type_info_by_enum(enum_value: str) -> Dict:
        """enum 값으로 유형 정보 반환 (절대 URL로 변환)"""
        for type_info in TasteTestData.TYPE_INFO.values():
            if type_info["enum"] == enum_value:
                result = type_info.copy()
                result["image_url"] = TasteTestData.get_image_url_by_enum(enum_value)
                return result
        result = TasteTestData.TYPE_INFO["미식가유형"].copy()
        result["image_url"] = TasteTestData.get_image_url_by_enum("GOURMET")
        return result

    @staticmethod
    def get_image_url_by_enum(enum_value: str) -> str:
        """enum 값으로 이미지 URL 반환 (절대 URL)"""
        return TasteTestData.get_image_url_by_enum(enum_value)

    @staticmethod
    def get_taste_type_base_scores(enum_value: str) -> Dict[str, float]:
        """enum 값으로 기본 맛 점수 반환"""
        return TasteTestData.TASTE_PROFILES.get(enum_value, TasteTestData.TASTE_PROFILES["GOURMET"])

    @classmethod
    def process_taste_test(cls, answers: Dict[str, str]) -> Dict:
        """테스트 전체 처리"""
        scores = cls.calculate_scores(answers)
        determined_type = cls.determine_type(scores)
        type_info = cls.get_type_info(determined_type)

        return {
            "type": determined_type,
            "scores": scores,
            "info": type_info,
        }

    @classmethod
    def save_test_result(cls, user, answers: Dict[str, str]) -> PreferenceTestResult:
        """테스트 결과를 DB에 저장 (개선된 재테스트 지원)"""
        # 테스트 결과 처리
        test_result_data = cls.process_taste_test(answers)
        korean_type = test_result_data["type"]

        # enum 값 가져오기
        enum_value = TasteTestData.get_enum_by_korean_name(korean_type)
        if not enum_value or not hasattr(PreferenceTestResult.PreferTaste, enum_value):
            enum_value = "GOURMET"

        prefer_taste_enum = getattr(PreferenceTestResult.PreferTaste, enum_value)

        # 기존 테스트 결과 확인
        existing_result = PreferenceTestResult.objects.filter(user=user).first()
        is_new_test = existing_result is None

        # DB 저장 (재테스트면 업데이트, 신규면 생성)
        result, created = PreferenceTestResult.objects.update_or_create(
            user=user, defaults={"answers": answers, "prefer_taste": prefer_taste_enum}
        )

        # PreferTasteProfile 처리
        profile_result = cls._handle_taste_profile(user, result, is_new_test)

        # 결과에 프로필 처리 정보 추가
        result.profile_update_result = profile_result

        return result

    @classmethod
    def get_retake_preview(cls, user, answers: Dict[str, str]) -> Dict:
        """재테스트 시 변화 미리보기 (실제 저장하지 않음)"""
        try:
            from django.apps import apps

            PreferTasteProfile = apps.get_model("users", "PreferTasteProfile")

            # 현재 프로필 가져오기
            profile = PreferTasteProfile.objects.get(user=user)

            # 새 테스트 결과 계산
            test_result_data = cls.process_taste_test(answers)
            korean_type = test_result_data["type"]

            enum_value = TasteTestData.get_enum_by_korean_name(korean_type)
            if not enum_value:
                enum_value = "GOURMET"

            # 새로운 기본 점수
            new_base_scores = TasteTestData.TASTE_PROFILES.get(enum_value, TasteTestData.TASTE_PROFILES["GOURMET"])

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

            for field in [
                "sweetness_level",
                "acidity_level",
                "body_level",
                "carbonation_level",
                "bitterness_level",
                "aroma_level",
            ]:
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
                "current_type": cls.get_type_info_by_enum(profile.user.preference_test_result.prefer_taste)["name"],
                "influence_rate": f"{int(test_influence * 100)}%",
                "review_count": review_count,
                "predicted_changes": preview_changes,
                "message": cls._generate_preview_message(review_count, test_influence, len(preview_changes)),
            }

        except Exception as e:
            return {"error": "미리보기를 생성할 수 없습니다.", "details": str(e)}

    @classmethod
    def _handle_taste_profile(cls, user, test_result, is_new_test):
        """PreferTasteProfile 초기화/업데이트 처리 (개선된 재테스트 지원)"""
        try:
            from django.apps import apps

            PreferTasteProfile = apps.get_model("users", "PreferTasteProfile")

            profile, profile_created = PreferTasteProfile.objects.get_or_create(user=user)

            if profile_created or profile.total_reviews_count == 0:
                # 첫 테스트 또는 리뷰 경험이 없는 경우
                profile.initialize_from_test_result(test_result)
                return {"action": "initialized", "message": "취향 프로필이 초기화되었습니다."}

            elif not is_new_test:
                # 재테스트인 경우
                retake_result = profile.handle_retake(test_result)
                return {
                    "action": "retake_applied",
                    "influence_rate": retake_result["influence_rate"],
                    "changes_made": retake_result["changes_made"],
                    "message": retake_result["message"],
                }

            else:
                # 이미 테스트가 있는데 새 테스트로 들어온 경우 (예외 상황)
                return {"action": "no_change", "message": "기존 테스트 결과가 유지됩니다."}

        except (ImportError, LookupError):
            # PreferTasteProfile이 없는 경우
            return {"action": "skipped", "message": "취향 프로필 처리를 건너뛰었습니다."}

    @classmethod
    def _generate_preview_message(cls, review_count: int, test_influence: float, change_count: int) -> str:
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
    def validate_answers(answers: Dict[str, str]) -> Dict[str, List[str]]:
        """답변 유효성 검증"""
        errors: Dict[str, List[str]] = {}

        # 타입 안전하게 question id 추출
        required_questions = {str(q["id"]) for q in TasteTestData.QUESTIONS}
        provided_questions = {str(k) for k in answers.keys()}

        # 누락/추가 질문 확인
        missing = required_questions - provided_questions
        if missing:
            missing_sorted = sorted(missing)
            errors["missing_questions"] = [f"다음 질문에 답변해주세요: {', '.join(missing_sorted)}"]

        extra = provided_questions - required_questions
        if extra:
            extra_sorted = sorted(extra)
            errors["extra_questions"] = [f"존재하지 않는 질문입니다: {', '.join(extra_sorted)}"]

        # 각 답변 유효성 확인
        for question_id, answer in answers.items():
            if question_id in TasteTestData.ANSWER_MAPPING:
                valid_choices = list(TasteTestData.ANSWER_MAPPING[question_id].keys())
                if answer not in valid_choices:
                    errors[question_id] = [f"유효한 선택지는 {', '.join(valid_choices)}입니다."]

        return errors


# 하위 호환성을 위한 함수들과 상수들
def get_questions() -> List[Dict]:
    return TasteTestService.get_questions()


def process_taste_test(answers: Dict[str, str]) -> Dict:
    return TasteTestService.process_taste_test(answers)


# 기존 테스트에서 사용하던 상수들 (하위 호환성)
TASTE_QUESTIONS = TasteTestData.QUESTIONS
ANSWER_SCORE_MAPPING = TasteTestData.ANSWER_MAPPING
TASTE_TYPES = TasteTestData.TYPE_INFO
TASTE_TYPE_IMAGES = {
    str(type_info["enum"]): TasteTestData.get_image_url_by_enum(str(type_info["enum"]))
    for type_info in TasteTestData.TYPE_INFO.values()
}
