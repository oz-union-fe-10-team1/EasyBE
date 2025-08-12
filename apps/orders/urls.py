from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.orders.views import OrderItemListViewSet, OrderViewSet

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="order")
router.register(r"order-items", OrderItemListViewSet, basename="order-item")

urlpatterns = router.urls
