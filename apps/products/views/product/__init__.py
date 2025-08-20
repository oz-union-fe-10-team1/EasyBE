# apps/products/views/product/__init__.py

"""
Product 관련 뷰들
"""

# 관리자용 API
from .admin import (
    DrinksForPackageView,
    IndividualProductCreateView,
    PackageProductCreateView,
    ProductManageListView,
    ProductManageView,
)

# 일반 사용자용 API
from .public import (
    BaseProductListView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductSearchView,
)

# 메인/패키지 페이지 섹션들
from .sections import (
    AwardWinningProductsView,
    BaseSectionView,
    FeaturedProductsView,
    MakgeolliProductsView,
    MonthlyFeaturedDrinksView,
    PopularProductsView,
    RecommendedProductsView,
    RegionalProductsView,
)

__all__ = [
    # Public
    "BaseProductListView",
    "ProductSearchView",
    "ProductDetailView",
    "ProductLikeToggleView",
    # Sections
    "BaseSectionView",
    "MonthlyFeaturedDrinksView",
    "PopularProductsView",
    "RecommendedProductsView",
    "FeaturedProductsView",
    "AwardWinningProductsView",
    "MakgeolliProductsView",
    "RegionalProductsView",
    # Admin
    "IndividualProductCreateView",
    "PackageProductCreateView",
    "DrinksForPackageView",
    "ProductManageView",
    "ProductManageListView",
]
