# apps/products/views/__init__.py

from .brewery import BreweryDetailView, BreweryListView
from .drink import DrinkDetailView, DrinkListView
from .package import PackageDetailView, PackageListView
from .product import (
    DrinksForPackageView,
    FeaturedProductsView,
    IndividualProductCreateView,
    PackageProductCreateView,
    PopularProductsView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductListView,
)

__all__ = [
    # Brewery
    "BreweryListView",
    "BreweryDetailView",
    # Drink
    "DrinkListView",
    "DrinkDetailView",
    # Package
    "PackageListView",
    "PackageDetailView",
    # Product
    "ProductListView",
    "ProductDetailView",
    "IndividualProductCreateView",
    "PackageProductCreateView",
    "DrinksForPackageView",
    "ProductLikeToggleView",
    "PopularProductsView",
    "FeaturedProductsView",
]
