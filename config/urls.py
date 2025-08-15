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
    path("api/v1/", include("apps.orders.urls")),
    # API URL 패턴
    path("api/", include(("apps.users.urls", "users"), namespace="users")),
    path("api/", include(("apps.products.urls", "products"), namespace="api")),
    path("api/v1/taste-test/", include("apps.taste_test.urls")),
    path("api/v1/cart/", include("apps.cart.urls")),
    path("api/", include(("apps.feedback.urls", "feedback"), namespace="feedback")),
    # swagger 및 redoc URL 패턴
    path("api/v1/stores/", include("apps.stores.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("__debug__/", include("debug_toolbar.urls")),
]

# 이미지 서빙 설정 (개발/배포 환경 모두)
urlpatterns += static("/api/taste-test/images/", document_root=settings.BASE_DIR / "images")

# if settings.DEBUG:
#     if "debug_toolbar" in settings.INSTALLED_APPS:
#         urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
#     if "drf_spectacular" in settings.INSTALLED_APPS:
#         urlpatterns += [
#             path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
#             path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
#             path("api/schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
#         ]
