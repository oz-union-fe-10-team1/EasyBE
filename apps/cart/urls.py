from rest_framework.routers import DefaultRouter
from django.urls import include, path

from apps.cart.views import CartViewSet

router = DefaultRouter()
router.register(r'', CartViewSet, basename='cart')

urlpatterns = [
    path('', include(router.urls)),
]
