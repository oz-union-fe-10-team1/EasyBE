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
