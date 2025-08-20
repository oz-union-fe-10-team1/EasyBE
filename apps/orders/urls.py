from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.orders.views import OrderItemListViewSet, OrderViewSet

app_name = "orders"

router = DefaultRouter()
router.register(r"order-items", OrderItemListViewSet, basename="order-item")

urlpatterns = [
    path("", include(router.urls)),
    # OrderViewSet의 URL들을 수동으로 등록
    path("create_from_cart/", OrderViewSet.as_view({"post": "create_from_cart"}), name="order-create-from-cart"),
    path("", OrderViewSet.as_view({"get": "list"}), name="order-list"),
    path("<int:pk>/", OrderViewSet.as_view({"get": "retrieve"}), name="order-detail"),
]
