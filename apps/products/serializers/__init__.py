# apps/products/serializers/__init__.py

from .brewery import (
    BreweryListSerializer,
    BrewerySerializer,
    BrewerySimpleSerializer,
)
from .drink import (
    DrinkListSerializer,
)
from .product import (
    ProductImageSerializer,
    ProductListSerializer,
)

__all__ = [
    # Brewery (관리자용 - 모든 기능 유지)
    "BreweryListSerializer",
    "BrewerySerializer",
    "BrewerySimpleSerializer",
    # Drink (관리자용 - 목록만)
    "DrinkListSerializer",
    # Product (UI용 + 관리자용)
    "ProductImageSerializer",
    "ProductListSerializer",
]
