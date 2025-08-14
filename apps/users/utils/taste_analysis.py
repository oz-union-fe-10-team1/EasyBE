# apps/users/utils/taste_analysis.py
import math
from decimal import Decimal
from typing import Dict

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
        피드백을 바탕으로 진화하는 취향 점수 업데이트
        """
        from apps.taste_test.services import TasteTestData

        # 1. 기본 데이터 수집
        drink = feedback.order_item.product.drink
        if not drink:
            return

        # 2. 진화하는 기준점 계산 (기본값 + 최근 취향)
        evolving_anchor = TasteAnalysisService._calculate_evolving_anchor(
            profile,
            TasteTestData.TASTE_PROFILES.get(
                profile.user.preference_test_result.prefer_taste, TasteTestData.TASTE_PROFILES["GOURMET"]
            ),
        )

        # 3. 적응적 학습률 계산
        learning_rate = TasteAnalysisService._calculate_adaptive_learning_rate(feedback, profile.total_reviews_count)

        # 4. 각 맛 특성별 업데이트
        taste_fields = {
            "sweetness_level": "sweetness",
            "acidity_level": "acidity",
            "body_level": "body",
            "carbonation_level": "carbonation",
            "bitterness_level": "bitterness",
            "aroma_level": "aroma",
        }

        for profile_field, feedback_field in taste_fields.items():
            user_feedback = getattr(feedback, feedback_field)
            if user_feedback is None:
                continue

            # 현재 사용자 취향
            current_preference = float(getattr(profile, profile_field))

            # 진화하는 기준점 (기본값 + 최근 학습된 패턴)
            anchor_preference = evolving_anchor[profile_field]

            # 제품의 실제 맛 특성
            drink_characteristic = float(getattr(drink, profile_field))

            # 사용자 피드백 점수
            user_feedback_score = float(user_feedback)

            # 5. 진화적 취향 조정 계산
            adjustment = TasteAnalysisService._calculate_evolutionary_adjustment(
                current_preference=current_preference,
                anchor_preference=anchor_preference,
                drink_characteristic=drink_characteristic,
                user_feedback_score=user_feedback_score,
                learning_rate=learning_rate,
                rating=feedback.rating,
                review_count=profile.total_reviews_count,
            )

            # 6. 새로운 취향 점수 적용
            new_preference = current_preference + adjustment
            new_preference = max(0.0, min(5.0, new_preference))

            setattr(profile, profile_field, Decimal(str(round(new_preference, 1))))

        # 7. 메타데이터 업데이트
        profile.total_reviews_count += 1
        profile.save()

    @staticmethod
    def _calculate_evolving_anchor(profile: PreferTasteProfile, base_scores: Dict) -> Dict[str, float]:
        """
        진화하는 기준점 계산 (기본값 영향력이 시간에 따라 감소)
        """
        review_count = profile.total_reviews_count

        # 1. 기본값 영향력 시간 감쇠
        base_influence = max(0.1, 1.0 / (1 + review_count * 0.15))
        # 리뷰 0개: 1.0, 5개: 0.57, 10개: 0.4, 20개: 0.25, 50개: 0.12

        # 2. 최근 취향 중심 계산 (최근 학습된 패턴)
        recent_influence = 1.0 - base_influence

        # 3. 최근 취향 중심점 (현재 값이 최근 학습 결과를 반영)
        current_scores = profile.get_taste_scores_dict()

        # 4. 진화하는 기준점 = 기본값 * 감쇠율 + 현재값 * 증가율
        evolving_anchor = {}

        for field in [
            "sweetness_level",
            "acidity_level",
            "body_level",
            "carbonation_level",
            "bitterness_level",
            "aroma_level",
        ]:
            base_value = float(base_scores[field])
            current_value = current_scores[field]

            # 가중 평균으로 새로운 기준점 계산
            anchor_value = (base_value * base_influence) + (current_value * recent_influence)
            evolving_anchor[field] = anchor_value

        return evolving_anchor

    @staticmethod
    def _calculate_adaptive_learning_rate(feedback, total_review_count: int) -> dict:
        """
        적응적 학습률 계산 (더 자유로운 학습)
        """
        # 1. 기본 학습률 (더 관대하게 조정)
        base_rate = 0.9 / (1 + math.log(1 + total_review_count * 0.3))
        # 초기 학습률을 높이고, 감소 속도를 완화

        # 2. 평점 기반 가중치 (극단적 평점일수록 더 강한 신호)
        if feedback.rating <= 2:
            rating_multiplier = 2.0  # 부정적 경험 강화
        elif feedback.rating >= 4:
            rating_multiplier = 1.6  # 긍정적 경험 강화
        else:
            rating_multiplier = 1.2  # 보통 평점도 적극 반영

        # 3. 신뢰도 가중치
        confidence_weight = 0.6 + (feedback.confidence / 100.0) * 0.4  # 0.6~1.0 범위

        # 4. 초기 학습 부스트 (더 긴 기간 동안)
        if total_review_count < 10:  # 첫 10개까지 부스트
            early_boost = 1.8 - (total_review_count * 0.08)  # 1.8 → 1.0
        else:
            early_boost = 1.0

        # 5. 최종 학습률 (제한을 더 관대하게)
        final_rate = base_rate * rating_multiplier * confidence_weight * early_boost

        return {
            "base_rate": base_rate,
            "rating_multiplier": rating_multiplier,
            "confidence_weight": confidence_weight,
            "early_boost": early_boost,
            "final_rate": min(final_rate, 0.8),  # 최대 0.8로 상향
        }

    @staticmethod
    def _calculate_evolutionary_adjustment(
        current_preference: float,
        anchor_preference: float,
        drink_characteristic: float,
        user_feedback_score: float,
        learning_rate: dict,
        rating: int,
        review_count: int,
    ) -> float:
        """
        진화적 취향 조정값 계산 (자유로운 변화 허용)
        """

        # 1. 개선된 예상 점수 계산
        expected_score = TasteAnalysisService._calculate_improved_expected_score(
            current_preference, drink_characteristic
        )

        # 2. 실제 vs 예상 차이 (정규화)
        feedback_difference = user_feedback_score - expected_score
        normalized_difference = feedback_difference / 5.0

        # 3. 제품 특성 신뢰도
        characteristic_confidence = TasteAnalysisService._calculate_characteristic_confidence(drink_characteristic)

        # 4. 진화적 안정성 팩터 (기존보다 훨씬 관대)
        evolution_factor = TasteAnalysisService._calculate_evolution_factor(
            current_preference, anchor_preference, review_count
        )

        # 5. 방향성 조정
        direction_factor = TasteAnalysisService._calculate_direction_factor(
            current_preference, drink_characteristic, user_feedback_score, rating
        )

        # 6. 최종 조정값 계산
        base_adjustment = normalized_difference * learning_rate["final_rate"]

        adjustment = (
            base_adjustment
            * characteristic_confidence
            * evolution_factor  # 기존 deviation_penalty 대신
            * direction_factor
        )

        # 7. 진화적 최대 조정값 (더 관대하게)
        if review_count < 5:
            max_adjustment = 0.8  # 초기에는 매우 자유롭게
        elif review_count < 15:
            max_adjustment = 0.6  # 중기에도 관대하게
        else:
            max_adjustment = 0.4  # 후기에도 기존보다 관대

        return max(-max_adjustment, min(max_adjustment, adjustment))

    @staticmethod
    def _calculate_evolution_factor(current_preference: float, anchor_preference: float, review_count: int) -> float:
        """
        진화 팩터 계산 (기본값 의존도를 점진적으로 감소)
        """
        deviation = abs(current_preference - anchor_preference)

        # 리뷰 수에 따른 자유도 증가
        freedom_level = min(1.0, review_count / 20.0)  # 20개 리뷰 후 완전 자유

        # 기본 제약 (매우 관대)
        if deviation > 3.0:  # 기존 2.5 → 3.0
            base_constraint = 0.6  # 기존 0.3 → 0.6
        elif deviation > 2.0:  # 기존 1.5 → 2.0
            base_constraint = 0.8  # 기존 0.6 → 0.8
        else:
            base_constraint = 1.0

        # 자유도 적용 (리뷰가 많을수록 제약 완화)
        final_factor = base_constraint + (1.0 - base_constraint) * freedom_level

        return final_factor

    @staticmethod
    def _calculate_improved_expected_score(user_preference: float, drink_characteristic: float) -> float:
        """개선된 예상 점수 계산"""
        # 기존과 동일
        linear_component = (user_preference / 5.0) * drink_characteristic

        if user_preference >= 4.0 and drink_characteristic >= 4.0:
            synergy_bonus = 0.5
        elif user_preference <= 2.0 and drink_characteristic >= 4.0:
            synergy_bonus = -1.0
        elif user_preference >= 4.0 and drink_characteristic <= 2.0:
            synergy_bonus = -0.5
        else:
            synergy_bonus = 0.0

        expected = linear_component + synergy_bonus
        return max(0.0, min(5.0, expected))

    @staticmethod
    def _calculate_characteristic_confidence(drink_characteristic: float) -> float:
        """제품 특성 신뢰도 계산"""
        # 기존과 동일
        distance_from_center = abs(drink_characteristic - 2.5)

        if distance_from_center >= 2.0:
            return 1.3
        elif distance_from_center >= 1.5:
            return 1.1
        else:
            return 1.0

    @staticmethod
    def _calculate_direction_factor(
        current_preference: float, drink_characteristic: float, user_feedback_score: float, rating: int
    ) -> float:
        """방향성 조정 팩터"""
        # 기존과 동일
        if user_feedback_score >= 4.0:
            base_direction = 1.2
        elif user_feedback_score <= 2.0:
            base_direction = 1.2
        else:
            base_direction = 1.0

        expected_rating_from_feedback = user_feedback_score
        rating_consistency = 1.0 - abs(rating - expected_rating_from_feedback) * 0.1

        return base_direction * max(0.5, rating_consistency)
