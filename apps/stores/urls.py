from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.stores.views import StoreViewSet

router = DefaultRouter()
router.register(r"", StoreViewSet, basename="stores")

urlpatterns = [
    path("", include(router.urls)),
]
