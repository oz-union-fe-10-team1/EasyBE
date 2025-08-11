# apps/products/views/__init__.py

from .brewery import (
    BreweryCreateView,
    BreweryDetailView,
    BreweryListView,
    BreweryManageView,
)
from .drink import (
    DrinkCreateView,
    DrinkDetailView,
    DrinkListView,
    DrinkManageView,
)
from .package import (
    PackageCreateView,
    PackageDetailView,
    PackageListView,
    PackageManageView,
)
from .product import (
    DrinksForPackageView,
    FeaturedProductsView,
    IndividualProductCreateView,
    PackageProductCreateView,
    PopularProductsView,
    ProductDeleteView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductListView,
)

__all__ = [
    # Brewery
    "BreweryListView",
    "BreweryDetailView",
    "BreweryCreateView",
    "BreweryManageView",
    # Drink
    "DrinkListView",
    "DrinkDetailView",
    "DrinkCreateView",
    "DrinkManageView",
    # Package
    "PackageListView",
    "PackageDetailView",
    "PackageCreateView",
    "PackageManageView",
    # Product
    "ProductListView",
    "ProductDetailView",
    "ProductDeleteView",
    "IndividualProductCreateView",
    "PackageProductCreateView",
    "DrinksForPackageView",
    "ProductLikeToggleView",
    "PopularProductsView",
    "FeaturedProductsView",
]
