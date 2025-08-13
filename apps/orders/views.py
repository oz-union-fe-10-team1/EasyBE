from datetime import date

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cart.models import CartItem
from apps.orders.models import Order, OrderItem
from apps.orders.serializers import FlatOrderItemSerializer, OrderSerializer
from apps.stores.models import Store


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items__product", "items__pickup_store")

    @action(detail=False, methods=["post"])
    def create_from_cart(self, request, *args, **kwargs):
        """
        장바구니의 모든 상품으로 주문을 생성합니다.
        재고 확인 및 차감, 장바구니 비우기 로직을 포함합니다.
        """
        user = request.user
        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"detail": "장바구니가 비어있습니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                total_price = sum(item.total_price for item in cart_items)

                # 1. 주문 생성
                order = Order.objects.create(user=user, total_price=total_price)

                # 2. 주문 항목 생성 및 재고 차감
                order_items_to_create = []
                for item in cart_items:
                    # CartItem에서 픽업 매장과 날짜를 가져옴
                    if not item.pickup_store or not item.pickup_date:
                        raise ValueError(
                            f"장바구니 항목 '{item.product.name}'에 픽업 매장 또는 픽업 날짜가 지정되지 않았습니다."
                        )

                    order_item = OrderItem(
                        order=order,
                        product=item.product,
                        price=item.product.price,  # 주문 당시 가격 기록
                        quantity=item.quantity,
                        pickup_store=item.pickup_store,  # CartItem의 픽업 매장 사용
                        pickup_day=item.pickup_date,  # CartItem의 픽업 날짜 사용
                    )
                    # 모델에 정의된 재고 차감 메소드 사용 (ValueError 발생 시 트랜잭션 롤백)
                    order_item.reserve_stock()
                    order_items_to_create.append(order_item)

                OrderItem.objects.bulk_create(order_items_to_create)

                # 3. 장바구니 비우기
                cart_items.delete()

                serializer = self.get_serializer(order)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Store.DoesNotExist:
            return Response(
                {"detail": "매장 정보를 찾을 수 없습니다. 먼저 매장을 생성해주세요."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        except ValueError as e:
            # 재고 부족 또는 재고 정보 없음 오류 처리
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OrderItemListViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FlatOrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            OrderItem.objects.filter(order__user=self.request.user)
            .select_related("order", "product", "pickup_store")
            .order_by("-order__created_at", "-id")
        )