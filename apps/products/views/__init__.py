# apps/products/views/__init__.py 수정

from .brewery import (
    BreweryCreateView,
    BreweryDetailView,
    BreweryListView,
    BreweryManageView,
)
from .drink import (
    DrinkListView,
)
from .product import (
    AwardWinningProductsView,
    FeaturedProductsView,
    RecommendedProductsView,
    MakgeolliProductsView,
    PopularProductsView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductSearchView,
    RegionalProductsView,
)

__all__ = [
    # Brewery (관리자용)
    "BreweryListView",
    "BreweryDetailView",
    "BreweryCreateView",
    "BreweryManageView",
    # Drink (관리자용 - 목록만)
    "DrinkListView",
    # Product (UI용)
    "ProductSearchView",
    "ProductDetailView",
    "ProductLikeToggleView",
    "PopularProductsView",
    "FeaturedProductsView",
    "AwardWinningProductsView",
    "MakgeolliProductsView",
    "RegionalProductsView",
    "RecommendedProductsView",
]