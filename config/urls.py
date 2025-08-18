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
    # API URL 패턴
    path("api/", include(("apps.users.urls", "users"), namespace="users")),
    path("api/", include(("apps.products.urls", "products"), namespace="products")),
    path("api/", include(("apps.taste_test.urls", "taste_test"), namespace="taste_test")),
    path("api/", include(("apps.feedback.urls", "feedback"), namespace="feedback")),
    path("api/v1/", include("apps.orders.urls")),
    path("api/v1/cart/", include("apps.cart.urls")),
    path("api/v1/stores/", include("apps.stores.urls")),
    # swagger 및 redoc URL 패턴
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("__debug__", include("debug_toolbar.urls")),
]

# 이미지 서빙 설정 (개발/배포 환경 모두)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# if settings.DEBUG:
#     if "debug_toolbar" in settings.INSTALLED_APPS:
#         urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
#     if "drf_spectacular" in settings.INSTALLED_APPS:
#         urlpatterns += [
#             path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
#             path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
#             path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
#         ]
