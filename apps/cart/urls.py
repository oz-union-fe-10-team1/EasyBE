from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CartItemViewSet

router = DefaultRouter()
router.register(r"", CartItemViewSet, basename="cart-item")

urlpatterns = [
    path("", include(router.urls)),
]
