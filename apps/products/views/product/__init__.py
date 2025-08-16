# apps/products/views/product/__init__.py

"""
Product 관련 뷰들
"""

# 일반 사용자용 API
from .public import (
    BaseProductListView,
    ProductSearchView,
    ProductDetailView,
    ProductLikeToggleView,
)

# 메인/패키지 페이지 섹션들
from .sections import (
    BaseSectionView,
    MonthlyFeaturedDrinksView,
    PopularProductsView,
    RecommendedProductsView,
    FeaturedProductsView,
    AwardWinningProductsView,
    MakgeolliProductsView,
    RegionalProductsView,
)

# 관리자용 API
from .admin import (
    IndividualProductCreateView,
    PackageProductCreateView,
    DrinksForPackageView,
    ProductManageView,
    ProductManageListView,
)

__all__ = [
    # Public
    'BaseProductListView',
    'ProductSearchView',
    'ProductDetailView',
    'ProductLikeToggleView',

    # Sections
    'BaseSectionView',
    'MonthlyFeaturedDrinksView',
    'PopularProductsView',
    'RecommendedProductsView',
    'FeaturedProductsView',
    'AwardWinningProductsView',
    'MakgeolliProductsView',
    'RegionalProductsView',

    # Admin
    'IndividualProductCreateView',
    'PackageProductCreateView',
    'DrinksForPackageView',
    'ProductManageView',
    'ProductManageListView',
]