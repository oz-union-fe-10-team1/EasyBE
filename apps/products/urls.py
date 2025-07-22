# apps/products/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet

# DRF Router 설정
router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")

urlpatterns = [
    # DRF Router URLs
    path("", include(router.urls)),
    # 추가 커스텀 URL들 (향후 확장용)
    # path('products/recommend/', RecommendationView.as_view(), name='product-recommend'),
    # path('products/search/', ProductSearchView.as_view(), name='product-search'),
]

# URL 패턴 확인용
# python manage.py show_urls 명령어로 확인 가능
"""
예상 URL 패턴:
/api/products/                     GET, POST
/api/products/{id}/                GET, PUT, PATCH, DELETE
/api/products/popular/             GET
/api/products/featured/            GET  
/api/products/new/                 GET
/api/products/{id}/like/           POST
/api/products/{id}/similar/        GET
/api/products/filter_options/      GET
"""
