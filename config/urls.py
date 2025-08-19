from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("apps.users.urls", namespace="users")),
    path("api/", include("apps.products.urls", namespace="products")),
    path("api/", include("apps.feedback.urls", namespace="feedback")),
    path("api/v1/orders/", include("apps.orders.urls", namespace="orders")),
    path("api/v1/cart/", include("apps.cart.urls", namespace="cart")),
    path("api/v1/stores/", include("apps.stores.urls", namespace="stores")),
    path("api/", include("apps.taste_test.urls", namespace="taste_test")),
    # Swagger and Redoc URL patterns
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("__debug__/", include("debug_toolbar.urls")),
]

# Image serving settings (development/deployment environments)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
