from django.urls import path

from apps.orders.views import OrderViewSet

urlpatterns = [
    path("", OrderViewSet.as_view({"post": "create"}), name="order-create"),
    path("list/", OrderViewSet.as_view({"get": "list"}), name="order-list"),
]
