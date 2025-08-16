# apps/products/views/__init__.py

from .brewery import (
    BreweryCreateView,
    BreweryDetailView,
    BreweryListView,
    BreweryManageView,
)
from .drink import (
    DrinkListView,
)

# 새로운 product 패키지 구조에서 import
from .product import (
    # 일반 사용자용 API
    ProductSearchView,
    ProductDetailView,
    ProductLikeToggleView,

    # 메인페이지 섹션들
    MonthlyFeaturedDrinksView,
    PopularProductsView,
    RecommendedProductsView,

    # 패키지페이지 섹션들
    FeaturedProductsView,
    AwardWinningProductsView,
    MakgeolliProductsView,
    RegionalProductsView,

    # 관리자용 API (필요한 경우)
    IndividualProductCreateView,
    PackageProductCreateView,
    DrinksForPackageView,
    ProductManageView,
    ProductManageListView,
)

__all__ = [
    # Brewery (관리자용)
    "BreweryListView",
    "BreweryDetailView",
    "BreweryCreateView",
    "BreweryManageView",

    # Drink (관리자용 - 목록만)
    "DrinkListView",

    # Product - 일반 사용자용 API
    "ProductSearchView",
    "ProductDetailView",
    "ProductLikeToggleView",

    # Product - 메인페이지 섹션들
    "MonthlyFeaturedDrinksView",
    "PopularProductsView",
    "RecommendedProductsView",

    # Product - 패키지페이지 섹션들
    "FeaturedProductsView",
    "AwardWinningProductsView",
    "MakgeolliProductsView",
    "RegionalProductsView",

    # Product - 관리자용 API
    "IndividualProductCreateView",
    "PackageProductCreateView",
    "DrinksForPackageView",
    "ProductManageView",
    "ProductManageListView",
]