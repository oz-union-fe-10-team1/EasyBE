from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.stores.views import ProductStockViewSet, StoreViewSet

router = DefaultRouter()
router.register(r"", StoreViewSet, basename="stores")
router.register(r"stock", ProductStockViewSet, basename="product-stock")

urlpatterns = [
    path("", include(router.urls)),
]
