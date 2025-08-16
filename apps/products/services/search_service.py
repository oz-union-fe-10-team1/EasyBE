# apps/products/services/search_service.py

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from django.db.models import Case, DecimalField, F, QuerySet, When
from django.http import QueryDict

from apps.products.models import Product


class SearchService:
    """상품 검색 및 필터링 관련 비즈니스 로직"""

    # 맛 프로필 파라미터 매핑
    TASTE_PARAM_MAPPING = {
        "sweetness": "drink__sweetness_level",
        "acidity": "drink__acidity_level",
        "body": "drink__body_level",
        "carbonation": "drink__carbonation_level",
        "bitterness": "drink__bitterness_level",
        "aroma": "drink__aroma_level",
    }

    # 카테고리 필터 매핑
    CATEGORY_FILTER_MAPPING = {
        "gift_suitable": "is_gift_suitable",
        "regional_specialty": "is_regional_specialty",
        "limited_edition": "is_limited_edition",
        "premium": "is_premium",
        "award_winning": "is_award_winning",
    }

    # 맛 프로필 허용 범위
    TASTE_RANGE = Decimal("0.5")
    MIN_TASTE_VALUE = Decimal("0.0")
    MAX_TASTE_VALUE = Decimal("5.0")

    @staticmethod
    def get_search_queryset(query_params: QueryDict) -> QuerySet:
        """
        검색 파라미터를 기반으로 상품 쿼리셋 반환

        Args:
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            QuerySet: 검색 조건이 적용된 상품 쿼리셋
        """
        # 기본 쿼리셋 (할인율 계산 포함)
        queryset = SearchService._get_base_queryset_with_discount()

        # 맛 프로필 필터 적용
        queryset = SearchService.apply_taste_filters(queryset, query_params)

        # 카테고리 필터 적용
        queryset = SearchService.apply_category_filters(queryset, query_params)

        return queryset

    @staticmethod
    def _get_base_queryset_with_discount() -> QuerySet:
        """
        할인율 계산이 포함된 기본 쿼리셋 반환

        Returns:
            QuerySet: 할인율이 계산된 상품 쿼리셋
        """
        return (
            Product.objects.filter(status="ACTIVE")
            .select_related("drink__brewery", "package")
            .prefetch_related("images", "package__drinks__brewery")
            .annotate(
                discount_rate=Case(
                    When(
                        original_price__isnull=False,
                        discount__isnull=False,
                        original_price__gt=0,
                        then=F("discount") * 100.0 / F("original_price"),
                    ),
                    default=0.0,
                    output_field=DecimalField(max_digits=5, decimal_places=1),
                )
            )
        )

    @staticmethod
    def apply_taste_filters(queryset: QuerySet, query_params: QueryDict) -> QuerySet:
        """
        맛 프로필 슬라이더 필터링 적용

        Args:
            queryset: 기본 쿼리셋
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            QuerySet: 맛 프로필 필터가 적용된 쿼리셋
        """
        for param, field in SearchService.TASTE_PARAM_MAPPING.items():
            value = query_params.get(param)
            if value:
                try:
                    target = Decimal(str(value))

                    # 허용 범위 계산 (±0.5)
                    min_value = max(SearchService.MIN_TASTE_VALUE, target - SearchService.TASTE_RANGE)
                    max_value = min(SearchService.MAX_TASTE_VALUE, target + SearchService.TASTE_RANGE)

                    # 필터 적용
                    queryset = queryset.filter(
                        **{f"{field}__gte": min_value},
                        **{f"{field}__lte": max_value},
                    )

                except (ValueError, TypeError):
                    # 잘못된 값은 무시
                    continue

        return queryset

    @staticmethod
    def apply_category_filters(queryset: QuerySet, query_params: QueryDict) -> QuerySet:
        """
        카테고리 체크박스 필터링 적용

        Args:
            queryset: 기본 쿼리셋
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            QuerySet: 카테고리 필터가 적용된 쿼리셋
        """
        for param, field in SearchService.CATEGORY_FILTER_MAPPING.items():
            if query_params.get(param) == "true":
                queryset = queryset.filter(**{field: True})

        return queryset

    @staticmethod
    def apply_alcohol_type_filter(queryset: QuerySet, alcohol_type: str) -> QuerySet:
        """
        주종별 필터링 적용

        Args:
            queryset: 기본 쿼리셋
            alcohol_type: 주종 (MAKGEOLLI, SOJU, etc.)

        Returns:
            QuerySet: 주종 필터가 적용된 쿼리셋
        """
        if alcohol_type:
            queryset = queryset.filter(drink__alcohol_type=alcohol_type)
        return queryset

    @staticmethod
    def apply_price_range_filter(
        queryset: QuerySet, min_price: Optional[int] = None, max_price: Optional[int] = None
    ) -> QuerySet:
        """
        가격 범위 필터링 적용

        Args:
            queryset: 기본 쿼리셋
            min_price: 최소 가격
            max_price: 최대 가격

        Returns:
            QuerySet: 가격 범위 필터가 적용된 쿼리셋
        """
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    @staticmethod
    def apply_brewery_filter(queryset: QuerySet, brewery_id: Optional[int] = None) -> QuerySet:
        """
        양조장별 필터링 적용

        Args:
            queryset: 기본 쿼리셋
            brewery_id: 양조장 ID

        Returns:
            QuerySet: 양조장 필터가 적용된 쿼리셋
        """
        if brewery_id:
            queryset = queryset.filter(drink__brewery_id=brewery_id)
        return queryset

    @staticmethod
    def get_search_statistics(query_params: QueryDict) -> Dict[str, Any]:
        """
        검색 결과 통계 정보 반환

        Args:
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            Dict: 검색 통계 정보
        """
        queryset = SearchService.get_search_queryset(query_params)

        return {
            "total_count": queryset.count(),
            "has_filters": SearchService._has_active_filters(query_params),
            "applied_filters": SearchService._get_applied_filters(query_params),
        }

    @staticmethod
    def _has_active_filters(query_params: QueryDict) -> bool:
        """
        활성화된 필터가 있는지 확인

        Args:
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            bool: 필터 적용 여부
        """
        # 맛 프로필 필터 확인
        for param in SearchService.TASTE_PARAM_MAPPING.keys():
            if query_params.get(param):
                return True

        # 카테고리 필터 확인
        for param in SearchService.CATEGORY_FILTER_MAPPING.keys():
            if query_params.get(param) == "true":
                return True

        return False

    @staticmethod
    def _get_applied_filters(query_params: QueryDict) -> Dict[str, Any]:
        """
        적용된 필터 목록 반환

        Args:
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            Dict: 적용된 필터들
        """
        applied_filters = {}

        # 맛 프로필 필터
        for param in SearchService.TASTE_PARAM_MAPPING.keys():
            value = query_params.get(param)
            if value:
                try:
                    applied_filters[param] = float(value)
                except (ValueError, TypeError):
                    pass

        # 카테고리 필터
        for param in SearchService.CATEGORY_FILTER_MAPPING.keys():
            if query_params.get(param) == "true":
                applied_filters[param] = True

        return applied_filters

    @staticmethod
    def get_popular_search_terms() -> list:
        """
        인기 검색어 반환 (추후 구현 가능)

        Returns:
            list: 인기 검색어 목록
        """
        # TODO: 실제 검색 로그 기반으로 구현
        return ["막걸리", "소주", "전통주", "선물세트", "프리미엄"]

    @staticmethod
    def validate_search_params(query_params: QueryDict) -> Dict[str, list]:
        """
        검색 파라미터 유효성 검사

        Args:
            query_params: HTTP 요청의 쿼리 파라미터

        Returns:
            Dict: 유효성 검사 오류 목록
        """
        errors = {}

        # 맛 프로필 값 범위 검사
        for param in SearchService.TASTE_PARAM_MAPPING.keys():
            value = query_params.get(param)
            if value:
                try:
                    decimal_value = Decimal(str(value))
                    if not (SearchService.MIN_TASTE_VALUE <= decimal_value <= SearchService.MAX_TASTE_VALUE):
                        errors[param] = [
                            f"값은 {SearchService.MIN_TASTE_VALUE}~{SearchService.MAX_TASTE_VALUE} 사이여야 합니다."
                        ]
                except (ValueError, TypeError, InvalidOperation):
                    errors[param] = ["올바른 숫자 형식이 아닙니다."]

        return errors
