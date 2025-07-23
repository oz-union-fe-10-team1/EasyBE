# apps/products/utils/filters.py

import django_filters
from django.db import models

from apps.products.models import AlcoholType, Brewery, Product, ProductCategory, Region


class ProductFilter(django_filters.FilterSet):
    """제품 필터링 클래스"""

    # 가격 범위 필터
    price_min = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    price_max = django_filters.NumberFilter(field_name="price", lookup_expr="lte")

    # 알코올 도수 범위 필터
    alcohol_content_min = django_filters.NumberFilter(field_name="alcohol_content", lookup_expr="gte")
    alcohol_content_max = django_filters.NumberFilter(field_name="alcohol_content", lookup_expr="lte")

    # 용량 범위 필터
    volume_min = django_filters.NumberFilter(field_name="volume_ml", lookup_expr="gte")
    volume_max = django_filters.NumberFilter(field_name="volume_ml", lookup_expr="lte")

    # 맛 프로필 범위 필터
    sweetness_min = django_filters.NumberFilter(field_name="sweetness_level", lookup_expr="gte")
    sweetness_max = django_filters.NumberFilter(field_name="sweetness_level", lookup_expr="lte")

    sourness_min = django_filters.NumberFilter(field_name="sourness_level", lookup_expr="gte")
    sourness_max = django_filters.NumberFilter(field_name="sourness_level", lookup_expr="lte")

    bitterness_min = django_filters.NumberFilter(field_name="bitterness_level", lookup_expr="gte")
    bitterness_max = django_filters.NumberFilter(field_name="bitterness_level", lookup_expr="lte")

    umami_min = django_filters.NumberFilter(field_name="umami_level", lookup_expr="gte")
    umami_max = django_filters.NumberFilter(field_name="umami_level", lookup_expr="lte")

    alcohol_strength_min = django_filters.NumberFilter(field_name="alcohol_strength", lookup_expr="gte")
    alcohol_strength_max = django_filters.NumberFilter(field_name="alcohol_strength", lookup_expr="lte")

    body_min = django_filters.NumberFilter(field_name="body_level", lookup_expr="gte")
    body_max = django_filters.NumberFilter(field_name="body_level", lookup_expr="lte")

    # 관계 필드 필터
    region = django_filters.ModelChoiceFilter(queryset=Region.objects.all())
    region_code = django_filters.CharFilter(field_name="region__code", lookup_expr="exact")

    alcohol_type = django_filters.ModelChoiceFilter(queryset=AlcoholType.objects.all())
    alcohol_category = django_filters.CharFilter(field_name="alcohol_type__category", lookup_expr="exact")

    category = django_filters.ModelChoiceFilter(queryset=ProductCategory.objects.all())
    category_slug = django_filters.CharFilter(field_name="category__slug", lookup_expr="exact")

    brewery = django_filters.ModelChoiceFilter(queryset=Brewery.objects.all())
    brewery_name = django_filters.CharFilter(field_name="brewery__name", lookup_expr="icontains")

    # 제품 특성 필터
    is_gift_suitable = django_filters.BooleanFilter()
    is_award_winning = django_filters.BooleanFilter()
    is_regional_specialty = django_filters.BooleanFilter()
    is_limited_edition = django_filters.BooleanFilter()
    is_premium = django_filters.BooleanFilter()
    is_organic = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()

    # 상태 필터
    status = django_filters.ChoiceFilter(choices=Product.STATUS_CHOICES)

    # 재고 필터
    in_stock = django_filters.BooleanFilter(method="filter_in_stock")

    # 할인 제품 필터
    on_sale = django_filters.BooleanFilter(method="filter_on_sale")

    # 평점 범위 필터
    rating_min = django_filters.NumberFilter(field_name="average_rating", lookup_expr="gte")
    rating_max = django_filters.NumberFilter(field_name="average_rating", lookup_expr="lte")

    # 날짜 범위 필터
    created_after = django_filters.DateFilter(field_name="created_at", lookup_expr="gte")
    created_before = django_filters.DateFilter(field_name="created_at", lookup_expr="lte")

    # 맛 태그 필터
    taste_tags = django_filters.CharFilter(method="filter_taste_tags")

    class Meta:
        model = Product
        fields = {
            "name": ["exact", "icontains"],
            "description": ["icontains"],
            "flavor_notes": ["icontains"],
        }

    def filter_in_stock(self, queryset, name, value):
        """재고 있는 제품 필터"""
        if value:
            return queryset.filter(stock_quantity__gt=0, status="active")
        return queryset

    def filter_on_sale(self, queryset, name, value):
        """할인 제품 필터"""
        if value:
            return queryset.filter(original_price__isnull=False, original_price__gt=models.F("price"))
        return queryset

    def filter_taste_tags(self, queryset, name, value):
        """맛 태그 필터 (콤마로 구분된 태그 ID들)"""
        if value:
            tag_ids = [int(tag_id.strip()) for tag_id in value.split(",") if tag_id.strip().isdigit()]
            if tag_ids:
                return queryset.filter(taste_tags__in=tag_ids).distinct()
        return queryset


class BreweryFilter(django_filters.FilterSet):
    """양조장 필터링 클래스"""

    region = django_filters.ModelChoiceFilter(queryset=Region.objects.all())
    region_code = django_filters.CharFilter(field_name="region__code", lookup_expr="exact")

    founded_year_min = django_filters.NumberFilter(field_name="founded_year", lookup_expr="gte")
    founded_year_max = django_filters.NumberFilter(field_name="founded_year", lookup_expr="lte")

    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Brewery
        fields = {
            "name": ["exact", "icontains"],
            "address": ["icontains"],
        }
