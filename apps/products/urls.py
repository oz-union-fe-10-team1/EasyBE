# apps/products/urls.py

from django.urls import include, path

from apps.products.views import (  # Brewery (어드민용); Drink (어드민용); Package (어드민용 + UI용); Product (UI용)
    BreweryDetailView,
    BreweryListView,
    DrinkDetailView,
    DrinkListView,
    DrinksForPackageView,
    FeaturedProductsView,
    IndividualProductCreateView,
    PackageDetailView,
    PackageListView,
    PackageProductCreateView,
    PopularProductsView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductListView,
)

app_name = "products"

# v1 API 패턴
v1_patterns = [
    # 양조장 (어드민용)
    path("breweries/", BreweryListView.as_view(), name="breweries-list"),
    path("breweries/<int:pk>/", BreweryDetailView.as_view(), name="breweries-detail"),
    # 술 (어드민용)
    path("drinks/", DrinkListView.as_view(), name="drinks-list"),
    path("drinks/<int:pk>/", DrinkDetailView.as_view(), name="drinks-detail"),
    path("drinks/for-package/", DrinksForPackageView.as_view(), name="drinks-for-package"),
    # 패키지 (어드민용 + UI용)
    path("packages/", PackageListView.as_view(), name="packages-list"),
    path("packages/<int:pk>/", PackageDetailView.as_view(), name="packages-detail"),
    # 상품 조회 (UI용)
    path("products/", ProductListView.as_view(), name="products-list"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="products-detail"),
    path("products/<uuid:pk>/like/", ProductLikeToggleView.as_view(), name="products-toggle-like"),
    # 상품 생성 (어드민용)
    path("product/", IndividualProductCreateView.as_view(), name="product-create"),
    path("package/", PackageProductCreateView.as_view(), name="package-create"),
    # 메인페이지용 API
    path("products/popular/", PopularProductsView.as_view(), name="products-popular"),
    path("products/featured/", FeaturedProductsView.as_view(), name="products-featured"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
