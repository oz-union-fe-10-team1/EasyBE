from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import IntegrityError

from .models import Cart, CartItem
from .serializers import CartSerializer

class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user).prefetch_related(
            'items__product', # 'items__custom_trio_set'
        )

    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    @action(detail=False, methods=['get'], url_path='')
    def get_cart(self, request):
        cart = self.get_object()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='items')
    def add_or_update_item(self, request):
        cart = self.get_object()
        product_id = request.data.get('product_id')
        # package_id = request.data.get('package_id') # 보류
        quantity = int(request.data.get('quantity', 1))

        if not product_id: # and not package_id:
            return Response({"detail": "product_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity <= 0:
            return Response({"detail": "수량은 1 이상이어야 합니다."}, status=status.HTTP_400_BAD_REQUEST)

        item_defaults = {'quantity': quantity}
        if product_id:
            item_data = {'cart': cart, 'product_id': product_id, 'item_type': CartItem.ItemType.PRODUCT}
        # elif package_id:
        #     item_data = {'cart': cart, 'custom_trio_set_id': package_id, 'item_type': CartItem.ItemType.CUSTOM_TRIO}
        
        try:
            cart_item, created = CartItem.objects.get_or_create(**item_data, defaults=item_defaults)
            if not created:
                cart_item.quantity = quantity
                cart_item.save()
        except IntegrityError:
            return Response({"detail": "잘못된 상품 ID입니다."}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['delete'], url_path='items/(?P<item_id>[^/.]+)')
    def remove_item(self, request, item_id=None):
        cart = self.get_object()
        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
            item.delete()
        except CartItem.DoesNotExist:
            return Response({"detail": "삭제할 상품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(status=status.HTTP_204_NO_CONTENT)