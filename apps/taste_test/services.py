# apps/taste_test/services.py

from django.utils import timezone
from django.db import transaction
from django.conf import settings
import json
import logging
from typing import Dict, List, Tuple, Any

from .models import TasteAnswer, TasteType, UserProfile, TasteTypeRecommendation
from .exceptions import TasteAnalysisError

logger = logging.getLogger(__name__)


class TasteScoreCalculator:
    """실제 6문항 테스트 점수 계산기"""

    # 실제 5가지 맛 유형
    TASTE_TYPES = ['달콤과일', '상큼톡톡', '목적여운', '깔끔고소', '미식가']

    @classmethod
    def calculate_scores(cls, answers: List[Dict]) -> Dict[str, int]:
        """
        실제 테스트 점수 계산: 각 질문당 1점, 총 6점 만점
        답변의 score_vector에서 직접 유형별 점수를 가져옴
        """
        type_scores = {type_name: 0 for type_name in cls.TASTE_TYPES}

        try:
            for answer in answers:
                answer_obj = TasteAnswer.objects.get(id=answer['answer_id'])
                score_vector = cls._parse_score_vector(answer_obj.score_vector)

                # score_vector에서 각 유형별 점수를 직접 더함
                for type_name in cls.TASTE_TYPES:
                    if type_name in score_vector:
                        type_scores[type_name] += score_vector[type_name]

        except Exception as e:
            logger.error(f"점수 계산 중 오류: {e}")
            raise TasteAnalysisError(f"점수 계산 실패: {str(e)}")

        logger.info(f"계산된 점수: {type_scores}")
        return type_scores

    @classmethod
    def _parse_score_vector(cls, score_vector: Any) -> Dict:
        """score_vector 파싱"""
        if isinstance(score_vector, dict):
            return score_vector
        elif isinstance(score_vector, str):
            try:
                return json.loads(score_vector)
            except json.JSONDecodeError:
                logger.warning(f"잘못된 score_vector 형식: {score_vector}")
                return {}
        else:
            return {}

    @classmethod
    def determine_result_type(cls, type_scores: Dict[str, int]) -> Dict[str, Any]:
        """
        실제 알고리즘:
        1. 미식가 우선 판정 (4개 기본 유형 중 3개가 2점 이상)
        2. 순수형 (한 유형이 최고점)
        3. 혼합형 (최고점이 2개)
        """
        # 미식가 제외 4개 기본 유형
        basic_types = ['달콤과일', '상큼톡톡', '목적여운', '깔끔고소']
        basic_scores = {k: v for k, v in type_scores.items() if k in basic_types}

        # 1. 미식가 우선 판정
        gourmet_result = cls._check_gourmet_type(basic_scores)
        if gourmet_result:
            return gourmet_result

        # 2. 기본 유형들 중에서 결과 결정
        return cls._determine_basic_result(basic_scores)

    @classmethod
    def _check_gourmet_type(cls, basic_scores: Dict[str, int]) -> Dict[str, Any]:
        """미식가 조건: 4개 기본 유형 중 3개가 2점 이상"""
        two_plus_count = sum(1 for score in basic_scores.values() if score >= 2)

        if two_plus_count >= 3:
            return {
                'primary_type': '미식가',
                'type_count': 1,
                'description': '다양한 맛을 균형있게 즐기는 미식가 유형입니다. 특정 맛에 치우치지 않고 상황과 기분에 따라 다른 스타일의 전통주를 선택할 줄 아는 폭넓은 취향을 가지고 있습니다.',
                'characteristics': ['다양성', '균형감', '미식안목', '상황적응', '폭넓은취향'],
                'confidence': 0.75  # 미식가는 중간 신뢰도
            }
        return None

    @classmethod
    def _determine_basic_result(cls, basic_scores: Dict[str, int]) -> Dict[str, Any]:
        """기본 유형들 중에서 순수형/혼합형 결정"""
        sorted_scores = sorted(basic_scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_scores or sorted_scores[0][1] == 0:
            # 모든 점수가 0인 경우 기본값
            return cls._get_default_result()

        first_type, first_score = sorted_scores[0]
        second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0

        # 혼합형 조건: 1위와 2위가 동점이거나 차이가 작을 때
        if first_score == second_score and first_score > 0:
            second_type = sorted_scores[1][0]
            return {
                'primary_type': f"{first_type} × {second_type}",
                'type_count': 2,
                'description': f'{first_type}과 {second_type}의 특성을 모두 가진 균형잡힌 유형입니다. 다양한 상황에서 여러 스타일의 전통주를 즐길 수 있는 폭넓은 취향을 가지고 있습니다.',
                'characteristics': cls._get_mixed_characteristics([first_type, second_type]),
                'confidence': 0.65  # 혼합형은 상대적으로 낮은 신뢰도
            }

        # 순수형
        return {
            'primary_type': first_type,
            'type_count': 1,
            'description': cls._get_type_description(first_type),
            'characteristics': cls._get_type_characteristics(first_type),
            'confidence': min(0.9, first_score / 6.0 + 0.3)  # 점수 비례 신뢰도
        }

    @classmethod
    def _get_default_result(cls) -> Dict[str, Any]:
        """기본 결과 (모든 점수가 0인 경우)"""
        return {
            'primary_type': '깔끔고소',  # 가장 무난한 타입을 기본값으로
            'type_count': 1,
            'description': '깔끔하고 고소한 맛을 선호하는 균형감 있는 유형입니다.',
            'characteristics': ['깔끔함', '고소함', '균형감', '부담없음', '다용도'],
            'confidence': 0.3
        }

    @classmethod
    def _get_type_description(cls, type_name: str) -> str:
        """유형별 설명"""
        descriptions = {
            '달콤과일': '달콤하고 과일향이 풍부한 전통주를 좋아하는 유형입니다. 부드럽고 감미로운 맛을 선호하며, 특별한 날이나 파티 분위기에 어울리는 술을 즐깁니다.',
            '상큼톡톡': '상큼하고 톡톡 튀는 청량감을 좋아하는 유형입니다. 가벼운 탄산감과 시원한 맛을 선호하며, 친구들과의 즐거운 시간을 좋아합니다.',
            '목적여운': '진하고 깊은 풍미를 추구하는 유형입니다. 복잡하고 오래 숙성된 맛을 좋아하며, 여운이 긴 술을 선호합니다. 전통주의 진수를 느끼고 싶어합니다.',
            '깔끔고소': '깔끔하고 고소한 맛을 선호하는 균형감 있는 유형입니다. 부담스럽지 않으면서도 깊이 있는 맛을 추구하며, 다양한 상황에 어울리는 술을 선호합니다.',
        }
        return descriptions.get(type_name, f'{type_name} 유형입니다.')

    @classmethod
    def _get_type_characteristics(cls, type_name: str) -> List[str]:
        """유형별 특성"""
        characteristics_map = {
            '달콤과일': ['달콤함', '과일향', '부드러움', '감미로움', '파티분위기'],
            '상큼톡톡': ['상큼함', '청량감', '가벼움', '톡톡함', '시원함'],
            '목적여운': ['진한맛', '깊은풍미', '복잡함', '긴여운', '전통미'],
            '깔끔고소': ['깔끔함', '고소함', '균형감', '부담없음', '다용도'],
            '미식가': ['다양성', '균형감', '미식안목', '상황적응', '폭넓은취향']
        }
        return characteristics_map.get(type_name, ['개성적', '독특함', '특별함', '고유함'])

    @classmethod
    def _get_mixed_characteristics(cls, type_names: List[str]) -> List[str]:
        """혼합형 특성"""
        all_chars = []
        for type_name in type_names:
            all_chars.extend(cls._get_type_characteristics(type_name))

        # 중복 제거하고 처음 5개만
        unique_chars = list(dict.fromkeys(all_chars))
        return unique_chars[:5]


class TasteAnalyzer:
    """취향 분석 서비스 (회원 전용)"""

    def __init__(self, user, test_id: int, answers: List[Dict]):
        self.user = user
        self.test_id = test_id
        self.answers = answers
        self.algorithm_version = getattr(settings, 'TASTE_ALGORITHM_VERSION', 'v2.0')

    @transaction.atomic
    def analyze_and_save(self) -> Any:
        """분석 및 저장"""
        try:
            # 점수 계산
            type_scores = TasteScoreCalculator.calculate_scores(self.answers)

            # 유형 결정
            result_data = TasteScoreCalculator.determine_result_type(type_scores)

            # 프로필 생성/업데이트
            profile = self._create_or_update_profile(result_data, type_scores)

            # 결과 객체 생성
            result = self._create_result_object(profile, result_data, type_scores)

            logger.info(
                f"맛 분석 완료 - User: {self.user.id}, "
                f"Type: {result_data['primary_type']}, "
                f"Confidence: {result_data.get('confidence', 0):.2f}"
            )

            return result

        except Exception as e:
            logger.error(f"맛 분석 중 오류: {e}")
            raise TasteAnalysisError(f"분석 처리 실패: {str(e)}")

    def _create_or_update_profile(self, result_data: Dict, type_scores: Dict) -> UserProfile:
        """프로필 생성 또는 업데이트"""
        # 프로필 조회/생성
        profile, created = UserProfile.objects.get_or_create(
            user=self.user,
            defaults={}
        )

        # 맛 타입 조회/생성
        taste_type, type_created = TasteType.objects.get_or_create(
            type_name=result_data['primary_type'],
            defaults={
                'type_description': result_data['description'],
                'type_image_url': self._get_type_image_url(result_data['primary_type'])
            }
        )

        if type_created:
            logger.info(f"새로운 맛 타입 생성: {taste_type.type_name}")

        # 프로필 업데이트
        profile.initial_taste_type = taste_type
        profile.taste_test_completed_at = timezone.now()

        # 상세 결과 저장
        profile.test_results = {
            'type_scores': type_scores,
            'result_data': result_data,
            'algorithm_version': self.algorithm_version,
            'test_id': self.test_id,
            'completed_at': timezone.now().isoformat()
        }

        profile.save()

        return profile

    def _get_type_image_url(self, type_name: str) -> str:
        """유형별 기본 이미지 URL 반환"""
        # 혼합형 처리
        if '×' in type_name:
            return 'https://example.com/images/taste_types/mixed.jpg'

        type_images = {
            '달콤과일': 'https://example.com/images/taste_types/sweet_fruit.jpg',
            '상큼톡톡': 'https://example.com/images/taste_types/fresh_sparkling.jpg',
            '목적여운': 'https://example.com/images/taste_types/deep_lingering.jpg',
            '깔끔고소': 'https://example.com/images/taste_types/clean_nutty.jpg',
            '미식가': 'https://example.com/images/taste_types/gourmet.jpg'
        }
        return type_images.get(type_name, 'https://example.com/images/taste_types/default.jpg')

    def _create_result_object(self, profile: UserProfile, result_data: Dict, type_scores: Dict) -> Any:
        """결과 객체 생성"""
        # 추천 상품 조회
        recommended_products = self._get_recommended_products(result_data['primary_type'])

        # 결과 객체 생성 (동적 클래스)
        result = type('TasteResult', (), {
            'profile': profile,
            'type_count': result_data['type_count'],
            'all_scores': type_scores,
            'characteristics': result_data['characteristics'],
            'confidence': result_data.get('confidence', 0.0),
            'recommended_products': recommended_products
        })()

        return result

    def _get_recommended_products(self, taste_type: str) -> List[Dict]:
        """맛 타입에 따른 추천 상품 조회"""
        try:
            # 혼합형인 경우 첫 번째 타입 기준으로 추천
            if '×' in taste_type:
                taste_type = taste_type.split(' × ')[0]

            # 맛 타입별 추천 상품 조회
            recommendations = TasteTypeRecommendation.objects.filter(
                taste_type__type_name=taste_type
            ).select_related('taste_type').order_by('recommendation_order')[:3]

            products = []
            for rec in recommendations:
                products.append({
                    'id': rec.product_id,
                    'name': f'추천 상품 {rec.recommendation_order}',  # 임시 이름
                    'price': 15000 + (rec.recommendation_order * 3000),  # 임시 가격
                    'image_url': f'https://example.com/images/product_{rec.product_id}.jpg',
                    'reason': rec.recommendation_reason or f'{taste_type} 유형에 어울리는 상품입니다.'
                })

            # 추천 상품이 없으면 기본 상품 생성
            if not products:
                products = self._get_default_recommendations(taste_type)

            return products

        except Exception as e:
            logger.warning(f"추천 상품 조회 실패: {e}")
            return self._get_default_recommendations(taste_type)

    def _get_default_recommendations(self, taste_type: str) -> List[Dict]:
        """기본 추천 상품"""
        return [
            {
                'id': f'default-{taste_type.lower()}-001',
                'name': f'{taste_type} 추천주 1',
                'price': 18000,
                'image_url': 'https://example.com/images/default-product-1.jpg',
                'reason': f'{taste_type} 유형에 어울리는 대표적인 전통주입니다.'
            },
            {
                'id': f'default-{taste_type.lower()}-002',
                'name': f'{taste_type} 추천주 2',
                'price': 22000,
                'image_url': 'https://example.com/images/default-product-2.jpg',
                'reason': f'{taste_type} 특성을 잘 나타내는 프리미엄 전통주입니다.'
            }
        ]


# 하위 호환성을 위한 예외 클래스들 (exceptions.py에서 임포트)
class TasteTestError(Exception):
    """맛 테스트 관련 오류"""
    pass