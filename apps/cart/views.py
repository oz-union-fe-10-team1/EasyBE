from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CartItem
from .serializers import CartItemSerializer
from .services import CartService


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """현재 인증된 사용자의 장바구니 항목만 조회하도록 필터링합니다."""
        return CartItem.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        """시리얼라이저에 request 객체를 전달합니다."""
        return {"request": self.request}

    def list(self, request, *args, **kwargs):
        """
        사용자의 장바구니에 담긴 모든 항목과 총액을 조회합니다.
        """
        cart_items, total_price = CartService.get_cart_info(user=request.user)
        serializer = self.get_serializer(cart_items, many=True)

        data = {
            "cart_items": serializer.data,
            "total_price": total_price,
        }
        return Response(data)

    def update(self, request, *args, **kwargs):
        """
        장바구니에 담긴 상품의 수량을 변경합니다.
        수량이 0 이하로 들어오면 항목을 삭제합니다.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_instance = serializer.save()

        if updated_instance is None:  # 아이템이 삭제된 경우
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(self.get_serializer(updated_instance).data)
