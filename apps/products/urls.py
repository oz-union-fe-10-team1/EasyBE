# apps/products/urls.py

from django.urls import include, path

from apps.products.views import (  # Brewery views; Drink views; Package views; Product views
    BreweryCreateView,
    BreweryDetailView,
    BreweryListView,
    BreweryManageView,
    DrinkCreateView,
    DrinkDetailView,
    DrinkListView,
    DrinkManageView,
    DrinksForPackageView,
    FeaturedProductsView,
    IndividualProductCreateView,
    PackageCreateView,
    PackageDetailView,
    PackageListView,
    PackageManageView,
    PackageProductCreateView,
    PopularProductsView,
    ProductDeleteView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductListView,
)

app_name = "products"

# v1 API 패턴
v1_patterns = [
    # 양조장 APIs
    path("breweries/", BreweryListView.as_view(), name="breweries-list"),
    path("breweries/create/", BreweryCreateView.as_view(), name="breweries-create"),
    path("breweries/<int:pk>/", BreweryDetailView.as_view(), name="breweries-detail"),
    path("breweries/<int:pk>/manage/", BreweryManageView.as_view(), name="breweries-manage"),
    # 술 APIs
    path("drinks/", DrinkListView.as_view(), name="drinks-list"),
    path("drinks/create/", DrinkCreateView.as_view(), name="drinks-create"),
    path("drinks/<int:pk>/", DrinkDetailView.as_view(), name="drinks-detail"),
    path("drinks/<int:pk>/manage/", DrinkManageView.as_view(), name="drinks-manage"),
    path("drinks/for-package/", DrinksForPackageView.as_view(), name="drinks-for-package"),
    # 패키지 APIs
    path("packages/", PackageListView.as_view(), name="packages-list"),
    path("packages/create/", PackageCreateView.as_view(), name="packages-create"),
    path("packages/<int:pk>/", PackageDetailView.as_view(), name="packages-detail"),
    path("packages/<int:pk>/manage/", PackageManageView.as_view(), name="packages-manage"),
    # 상품 조회 APIs (UI용)
    path("products/", ProductListView.as_view(), name="products-list"),
    path("products/popular/", PopularProductsView.as_view(), name="products-popular"),
    path("products/featured/", FeaturedProductsView.as_view(), name="products-featured"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="products-detail"),
    path("products/<uuid:pk>/like/", ProductLikeToggleView.as_view(), name="products-toggle-like"),
    path("products/<uuid:pk>/delete/", ProductDeleteView.as_view(), name="products-delete"),
    # 상품 생성 APIs (어드민용)
    path("products/individual/", IndividualProductCreateView.as_view(), name="products-individual-create"),
    path("products/package/", PackageProductCreateView.as_view(), name="products-package-create"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
