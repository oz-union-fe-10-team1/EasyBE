# apps/products/urls.py

from django.urls import include, path

from apps.products.views import (
    AwardWinningProductsView,
    BreweryCreateView,
    BreweryDetailView,
    BreweryListView,
    BreweryManageView,
    DrinkListView,
    FeaturedProductsView,
    MakgeolliProductsView,
    PopularProductsView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductSearchView,
    RegionalProductsView,
)
from apps.products.views.product import (
    DrinksForPackageView,
    IndividualProductCreateView,
    PackageProductCreateView,
    ProductManageView,
    RecommendedProductsView,
)

app_name = "products"

# v1 API 패턴
v1_patterns = [
    # 양조장 APIs (관리자용)
    path("breweries/", BreweryListView.as_view(), name="breweries-list"),
    path("breweries/create/", BreweryCreateView.as_view(), name="breweries-create"),
    path("breweries/<int:pk>/", BreweryDetailView.as_view(), name="breweries-detail"),
    path("breweries/<int:pk>/manage/", BreweryManageView.as_view(), name="breweries-manage"),

    # 술 APIs (관리자용 - 선택 목록)
    path("drinks/", DrinkListView.as_view(), name="drinks-list"),
    path("drinks/for-package/", DrinksForPackageView.as_view(), name="drinks-for-package"),

    # 상품 APIs (UI용 - 메인페이지 섹션들)
    path("products/search/", ProductSearchView.as_view(), name="products-list"),
    path("products/popular/", PopularProductsView.as_view(), name="products-popular"),
    path("products/featured/", FeaturedProductsView.as_view(), name="products-featured"),
    path("products/recommended/", RecommendedProductsView.as_view(), name="products-recommended"),
    path("products/award-winning/", AwardWinningProductsView.as_view(), name="products-award-winning"),
    path("products/makgeolli/", MakgeolliProductsView.as_view(), name="products-makgeolli"),
    path("products/regional/", RegionalProductsView.as_view(), name="products-regional"),

    # 상품 상세/관리
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="products-detail"),
    path("products/<uuid:pk>/like/", ProductLikeToggleView.as_view(), name="products-toggle-like"),
    path("products/<uuid:pk>/manage/", ProductManageView.as_view(), name="products-manage"),

    # 상품 생성 APIs (관리자용) - name 추가
    path("products/individual/create/", IndividualProductCreateView.as_view(), name="products-individual-create"),
    path("products/package/create/", PackageProductCreateView.as_view(), name="products-package-create"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]