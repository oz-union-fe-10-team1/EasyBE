from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CartItem
from .serializers import CartItemSerializer


class CartItemViewSet(viewsets.ModelViewSet):
    """
    장바구니 항목 관리 ViewSet

    - list: 사용자의 장바구니에 담긴 모든 항목과 총액을 조회합니다.
    - create: 장바구니에 새로운 상품을 추가합니다.
    - update/partial_update: 장바구니에 담긴 상품의 수량을 변경합니다. (+/- 버튼)
    - destroy: 장바구니에서 특정 항목을 제거합니다.
    """

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
        """장바구니 목록과 총합계 금액을 함께 반환하도록 커스터마이징합니다."""
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
