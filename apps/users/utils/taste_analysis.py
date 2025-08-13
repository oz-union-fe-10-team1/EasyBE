# apps/users/utils/taste_analysis.py

from decimal import Decimal
from apps.users.models import PreferTasteProfile


class TasteAnalysisService:
    """취향 분석 서비스 (규칙 기반)"""

    @staticmethod
    def generate_analysis(profile: PreferTasteProfile) -> str:
        """취향 프로필을 바탕으로 분석 설명 생성"""

        # 1. 맛 점수 가져오기
        scores = profile.get_taste_scores_dict()

        # 2. 점수 분석
        high_preferences = []  # 4.0 이상
        low_preferences = []  # 2.0 이하

        taste_names = {
            "sweetness_level": "단맛",
            "acidity_level": "산미",
            "body_level": "바디감",
            "carbonation_level": "탄산감",
            "bitterness_level": "쓴맛",
            "aroma_level": "향",
        }

        for taste_key, score in scores.items():
            taste_name = taste_names.get(taste_key, taste_key)
            if score >= 4.0:
                high_preferences.append(taste_name)
            elif score <= 2.0:
                low_preferences.append(taste_name)

        # 3. 리뷰 수에 따른 분석 신뢰도
        review_count = profile.total_reviews_count

        # 4. 분석 문구 생성
        analysis_parts = []

        if review_count == 0:
            return "아직 리뷰가 없어서 정확한 취향 분석이 어려워요. 술을 마시고 리뷰를 남겨보세요!"

        elif review_count < 3:
            analysis_parts.append("아직 리뷰가 적어서 대략적인 취향만 파악할 수 있어요.")

        elif review_count < 10:
            analysis_parts.append("최근 리뷰를 보니")

        else:
            analysis_parts.append(f"{review_count}개의 리뷰를 분석한 결과")

        # 5. 선호도 분석
        if high_preferences:
            if len(high_preferences) == 1:
                analysis_parts.append(f"{high_preferences[0]}를 특히 좋아하시는 것 같아요.")
            else:
                analysis_parts.append(f"{', '.join(high_preferences[:-1])}와 {high_preferences[-1]}를 좋아하시네요.")

        if low_preferences:
            if len(low_preferences) == 1:
                analysis_parts.append(f"{low_preferences[0]}는 별로 선호하지 않으시는 것 같아요.")
            else:
                analysis_parts.append(
                    f"{', '.join(low_preferences[:-1])}와 {low_preferences[-1]}는 선호하지 않으시는 편이에요."
                )

        # 6. 추천 문구
        recommendation = TasteAnalysisService._get_recommendation(scores, high_preferences, low_preferences)
        if recommendation:
            analysis_parts.append(recommendation)

        return " ".join(analysis_parts)

    @staticmethod
    def _get_recommendation(scores: dict, high_prefs: list, low_prefs: list) -> str:
        """점수 패턴에 따른 추천 문구"""

        sweetness = scores["sweetness_level"]
        acidity = scores["acidity_level"]
        body = scores["body_level"]
        carbonation = scores["carbonation_level"]
        bitterness = scores["bitterness_level"]
        aroma = scores["aroma_level"]

        # 달콤과일파 패턴
        if sweetness >= 4.0 and aroma >= 4.0 and bitterness <= 2.0:
            return "과일의 달콤함과 향이 매력적인 약주나 리큐르가 잘 어울릴 것 같아요!"

        # 상큼톡톡파 패턴
        elif acidity >= 4.0 and carbonation >= 4.0:
            return "상큼한 산미와 톡톡한 탄산감이 있는 스파클링 사케나 발포주를 추천해요!"

        # 묵직여운파 패턴
        elif body >= 4.0 and bitterness >= 3.0:
            return "진하고 묵직한 맛이 일품인 전통 소주나 위스키 스타일 증류주가 취향에 맞을 거예요!"

        # 깔끔고소파 패턴
        elif sweetness <= 2.0 and bitterness <= 2.5 and body >= 2.5:
            return "깔끔하고 담백한 맛의 순미 사케나 곡물 소주를 즐겨보세요!"

        # 향긋단정파 패턴
        elif aroma >= 4.0 and body <= 3.0:
            return "은은한 꽃향기나 과일향이 매력적인 프리미엄 약주가 좋을 것 같아요!"

        # 기본 추천
        else:
            return "다양한 스타일의 술을 시도해보시면서 취향을 더 발견해보세요!"

    # =================== 새로 추가되는 계산 로직 ===================

    @staticmethod
    def update_taste_profile_from_feedback(profile: PreferTasteProfile, feedback):
        """
        피드백을 바탕으로 정교한 취향 점수 업데이트

        Args:
            profile: 업데이트할 취향 프로필
            feedback: 사용자 피드백 (Feedback 모델 인스턴스)
        """
        from apps.taste_test.services import TasteTestData

        # 1. 기본 데이터 수집
        drink = feedback.order_item.product.drink
        if not drink:
            # 패키지 상품의 경우 처리 로직 (필요시 구현)
            return

        # 사용자 기본 취향 점수 (테스트 결과 기반)
        base_scores = TasteTestData.TASTE_PROFILES.get(
            profile.user.preference_test_result.prefer_taste,
            TasteTestData.TASTE_PROFILES["GOURMET"]
        )

        # 2. 가중치 계산
        weights = TasteAnalysisService._calculate_weights(feedback, profile.total_reviews_count)

        # 3. 각 맛 특성별 업데이트
        taste_fields = {
            'sweetness_level': 'sweetness',
            'acidity_level': 'acidity',
            'body_level': 'body',
            'carbonation_level': 'carbonation',
            'bitterness_level': 'bitterness',
            'aroma_level': 'aroma'
        }

        for profile_field, feedback_field in taste_fields.items():
            user_feedback = getattr(feedback, feedback_field)
            if user_feedback is None:
                continue

            # 현재 사용자 취향
            current_preference = float(getattr(profile, profile_field))

            # 사용자 기본 취향 (테스트 결과)
            base_preference = float(base_scores[profile_field])

            # 제품의 실제 맛 특성
            drink_characteristic = float(getattr(drink, profile_field))

            # 사용자 피드백 점수
            user_feedback_score = float(user_feedback)

            # 4. 취향 조정 계산
            adjustment = TasteAnalysisService._calculate_taste_adjustment(
                current_preference=current_preference,
                base_preference=base_preference,
                drink_characteristic=drink_characteristic,
                user_feedback_score=user_feedback_score,
                weights=weights,
                rating=feedback.rating
            )

            # 5. 새로운 취향 점수 적용
            new_preference = current_preference + adjustment
            new_preference = max(0.0, min(5.0, new_preference))  # 범위 제한

            setattr(profile, profile_field, Decimal(str(round(new_preference, 1))))

        # 6. 메타데이터 업데이트
        profile.total_reviews_count += 1
        profile.save()

    @staticmethod
    def _calculate_weights(feedback, total_review_count: int) -> dict:
        """가중치 계산"""

        # 평점 가중치: 1점=0.2, 5점=1.0
        rating_weight = feedback.rating / 5.0

        # 신뢰도 가중치: 0%=0.1(최소), 100%=1.0
        confidence_weight = max(0.1, feedback.confidence / 100.0)

        # 리뷰 경험 가중치: 초기에는 변화 크게, 경험 쌓일수록 안정화
        experience_weight = min(1.0, 1.0 / (1.0 + total_review_count * 0.1))

        # 최종 가중치
        final_weight = rating_weight * confidence_weight * experience_weight

        return {
            'rating_weight': rating_weight,
            'confidence_weight': confidence_weight,
            'experience_weight': experience_weight,
            'final_weight': final_weight
        }

    @staticmethod
    def _calculate_expected_score(user_preference: float, drink_characteristic: float) -> float:
        """
        사용자 취향과 제품 특성을 바탕으로 예상 평가 점수 계산

        로직:
        - 사용자 취향과 제품 특성이 모두 높으면 → 높은 평가 예상
        - 사용자 취향은 높은데 제품 특성이 낮으면 → 낮은 평가 예상
        """
        # 단순한 곱셈 기반 예상 (개선 가능)
        # 정규화: (user_pref/5) * (drink_char/5) * 5 = 상호작용 점수
        normalized_user = user_preference / 5.0
        normalized_drink = drink_characteristic / 5.0

        # 기본 예상: 둘의 상호작용
        base_expected = normalized_user * normalized_drink * 5.0

        # 사용자 선호도가 낮을 때는 제품이 강해도 부정적일 수 있음
        if user_preference < 2.0 and drink_characteristic > 3.0:
            # 선호하지 않는 맛이 강하면 더 낮게 평가할 것으로 예상
            penalty = (drink_characteristic - 2.0) * 0.3
            base_expected = max(0.0, base_expected - penalty)

        return base_expected

    @staticmethod
    def _calculate_taste_adjustment(current_preference: float, base_preference: float,
                                    drink_characteristic: float, user_feedback_score: float,
                                    weights: dict, rating: int) -> float:
        """
        취향 조정값 계산

        다양한 시나리오 고려:
        1. 예상보다 높게 평가 → 해당 맛에 대한 선호도 증가
        2. 예상보다 낮게 평가 → 해당 맛에 대한 선호도 감소
        3. 평점이 낮으면 → 더 큰 조정 (부정적 경험은 강하게 기억)
        4. 극단적인 제품에서의 피드백 → 더 신뢰할 만한 데이터
        """

        # 예상 점수 계산
        expected_score = TasteAnalysisService._calculate_expected_score(
            current_preference, drink_characteristic
        )

        # 실제 vs 예상 차이
        feedback_difference = user_feedback_score - expected_score

        # 기본 조정: 피드백 차이에 비례
        base_adjustment = feedback_difference * 0.1

        # 평점에 따른 조정 강도
        if rating <= 2:
            # 낮은 평점: 부정적 경험을 강하게 반영
            rating_multiplier = 1.5
        elif rating >= 4:
            # 높은 평점: 긍정적 경험을 적당히 반영
            rating_multiplier = 1.2
        else:
            # 보통 평점: 표준 반영
            rating_multiplier = 1.0

        # 제품 특성의 극단성을 고려
        # 극단적인 제품(0.5 이하 또는 4.5 이상)에서의 피드백은 더 신뢰할 만함
        extremeness_bonus = 0.0
        if drink_characteristic <= 0.5 or drink_characteristic >= 4.5:
            extremeness_bonus = 0.2
        elif drink_characteristic <= 1.0 or drink_characteristic >= 4.0:
            extremeness_bonus = 0.1

        # 기본 취향으로부터의 이탈 정도
        # 기본 취향에서 너무 멀어지면 조정 강도를 줄임 (안정성)
        deviation_from_base = abs(current_preference - base_preference)
        if deviation_from_base > 2.0:
            # 기본 취향에서 많이 벗어났으면 급격한 변화 제한
            stability_factor = 0.5
        elif deviation_from_base > 1.0:
            stability_factor = 0.8
        else:
            stability_factor = 1.0

        # 최종 조정값 계산
        adjustment = (base_adjustment * rating_multiplier *
                      (1.0 + extremeness_bonus) * stability_factor * weights['final_weight'])

        # 조정값 제한 (한 번에 너무 크게 변하지 않도록)
        max_adjustment = 0.3
        adjustment = max(-max_adjustment, min(max_adjustment, adjustment))

        return adjustment