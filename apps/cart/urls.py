from django.urls import path
from .views import CartViewSet

urlpatterns = [
    path('', CartViewSet.as_view({'get': 'get_cart'}), name='get-cart'),
    path('items/', CartViewSet.as_view({'post': 'add_or_update_item'}), name='add-cart-item'),
    path('items/<int:item_id>/', CartViewSet.as_view({'delete': 'remove_item'}), name='remove-cart-item'),
]