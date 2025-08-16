# apps/products/serializers/product/__init__.py

"""
Product 관련 시리얼라이저들
"""

# 이미지 관련
from .image import (
    ProductImageSerializer,
    ProductImageCreateSerializer,
)

# TODO: 다른 시리얼라이저들도 추가 예정
# from .list import ProductListSerializer
# from .detail import ProductDetailSerializer
# from .create import IndividualProductCreateSerializer, PackageProductCreateSerializer

__all__ = [
    # 이미지
    'ProductImageSerializer',
    'ProductImageCreateSerializer',

    # TODO: 나중에 추가
    # 'ProductListSerializer',
    # 'ProductDetailSerializer',
    # 'IndividualProductCreateSerializer',
    # 'PackageProductCreateSerializer',
]