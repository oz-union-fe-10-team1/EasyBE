from datetime import date

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.orders.models import Order, OrderItem
from apps.orders.serializers import FlatOrderItemSerializer, OrderSerializer
from apps.orders.services import (
    CartIsEmptyError,
    MissingPickupInfoError,
    OrderCreationError,
    OrderService,
)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product", "items__pickup_store")

    @action(detail=False, methods=["post"])
    def create_from_cart(self, request, *args, **kwargs):
        """
        장바구니의 모든 상품으로 주문을 생성
        """
        try:
            order = OrderService.create_order_from_cart(user=request.user)
            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except (CartIsEmptyError, MissingPickupInfoError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except OrderCreationError as e:
            # 기타 주문 생성 관련 예외 처리
            return Response(
                {"detail": f"주문 생성 중 오류가 발생했습니다: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OrderItemListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FlatOrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            OrderItem.objects.filter(order__user=self.request.user)
            .select_related("order", "product", "pickup_store")
            .order_by("-order__created_at", "-id")
        )
