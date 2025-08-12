from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CartItem
from .serializers import CartItemSerializer


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """현재 인증된 사용자의 장바구니 항목만 조회하도록 필터링합니다."""
        # N+1 문제를 방지하기 위해 product와 관련된 정보들을 미리 불러옵니다.
        return CartItem.objects.filter(user=self.request.user).select_related("product")

    def get_serializer_context(self):
        """시리얼라이저에 request 객체를 전달합니다."""
        return {"request": self.request}

    def list(self, request, *args, **kwargs):
        """
        사용자의 장바구니에 담긴 모든 항목과 총액을 조회합니다.
        GET /cart/items/
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # 총합계 금액 계산
        total_price = sum(item.product.price * item.quantity for item in queryset)

        # 최종 응답 데이터 구성
        data = {
            "cart_items": serializer.data,
            "total_price": total_price,
        }

        return Response(data)

    def create(self, request, *args, **kwargs):
        """
        장바구니에 새로운 상품을 추가합니다.
        POST /cart/items/
        """
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        특정 장바구니 항목의 상세 정보를 조회합니다.
        GET /cart/items/{pk}/
        """
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        장바구니에 담긴 상품의 수량을 변경합니다.
        수량이 0 이하로 들어오면 항목을 삭제합니다.
        PUT /cart/items/{pk}/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data.get("quantity", instance.quantity)

        if quantity <= 0:
            self.perform_destroy(instance)  # Use perform_destroy to ensure proper deletion
            return Response(status=status.HTTP_204_NO_CONTENT)

        self.perform_update(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        """
        장바구니에 담긴 상품의 수량을 부분적으로 변경합니다.
        PATCH /cart/items/{pk}/
        """
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        장바구니에서 특정 항목을 제거합니다.
        DELETE /cart/items/{pk}/
        """
        return super().destroy(request, *args, **kwargs)
