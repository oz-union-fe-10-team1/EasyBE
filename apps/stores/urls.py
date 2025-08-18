from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.stores.views import StoreViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"stores", StoreViewSet, basename="stores")

urlpatterns = [
    path("", include(router.urls)),
]
