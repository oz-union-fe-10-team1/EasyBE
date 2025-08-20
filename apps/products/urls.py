# apps/products/urls.py

from django.urls import include, path

from apps.products.views import (  # Brewery views; Drink views; Product views - 일반 사용자용; Product views - 메인페이지 섹션들; Product views - 패키지페이지 섹션들; Product views - 관리자용
    AwardWinningProductsView,
    BreweryCreateView,
    BreweryDetailView,
    BreweryListView,
    BreweryManageView,
    DrinkListView,
    DrinksForPackageView,
    FeaturedProductsView,
    IndividualProductCreateView,
    MakgeolliProductsView,
    MonthlyFeaturedDrinksView,
    PackageProductCreateView,
    PopularProductsView,
    ProductDetailView,
    ProductLikeToggleView,
    ProductManageListView,
    ProductManageView,
    ProductSearchView,
    RecommendedProductsView,
    RegionalProductsView,
)

app_name = "products"

# v1 API 패턴
v1_patterns = [
    # ============================================================================
    # 양조장 APIs (관리자용)
    # ============================================================================
    path("breweries/", BreweryListView.as_view(), name="breweries-list"),
    path("breweries/create/", BreweryCreateView.as_view(), name="breweries-create"),
    path("breweries/<int:pk>/", BreweryDetailView.as_view(), name="breweries-detail"),
    path("breweries/<int:pk>/manage/", BreweryManageView.as_view(), name="breweries-manage"),
    # ============================================================================
    # 술 APIs (관리자용)
    # ============================================================================
    path("drinks/", DrinkListView.as_view(), name="drinks-list"),
    path("drinks/for-package/", DrinksForPackageView.as_view(), name="drinks-for-package"),
    # ============================================================================
    # 상품 APIs - 일반 사용자용
    # ============================================================================
    path("products/search/", ProductSearchView.as_view(), name="products-search"),
    path("products/<uuid:pk>/", ProductDetailView.as_view(), name="products-detail"),
    path("products/<uuid:pk>/like/", ProductLikeToggleView.as_view(), name="products-toggle-like"),
    # ============================================================================
    # 상품 APIs - 메인페이지 섹션들
    # ============================================================================
    path("products/monthly/", MonthlyFeaturedDrinksView.as_view(), name="products-monthly"),
    path("products/popular/", PopularProductsView.as_view(), name="products-popular"),
    path("products/recommended/", RecommendedProductsView.as_view(), name="products-recommended"),
    # ============================================================================
    # 상품 APIs - 패키지페이지 섹션들
    # ============================================================================
    path("products/featured/", FeaturedProductsView.as_view(), name="products-featured"),
    path("products/award-winning/", AwardWinningProductsView.as_view(), name="products-award-winning"),
    path("products/makgeolli/", MakgeolliProductsView.as_view(), name="products-makgeolli"),
    path("products/regional/", RegionalProductsView.as_view(), name="products-regional"),
    # ============================================================================
    # 상품 APIs - 관리자용
    # ============================================================================
    path("products/manage/", ProductManageListView.as_view(), name="products-manage-list"),
    path("products/<uuid:pk>/manage/", ProductManageView.as_view(), name="products-manage"),
    path("products/individual/create/", IndividualProductCreateView.as_view(), name="products-individual-create"),
    path("products/package/create/", PackageProductCreateView.as_view(), name="products-package-create"),
]

urlpatterns = [
    path("v1/", include((v1_patterns, "v1"), namespace="v1")),
]
