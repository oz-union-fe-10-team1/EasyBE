from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cart.models import Cart
from apps.orders.models import Order, OrderItem
from apps.orders.serializers import OrderSerializer
from apps.products.models import Product


class OrderViewSet(viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    # authentication_classes를 명시하지 않아 settings.py의 기본값을 따르도록 함

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items__feedback'
        )

    def list(self, request, *args, **kwargs):
        """
        주문 목록을 조회합니다.
        GET /api/orders/list/
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        """
        장바구니 기반으로 주문을 생성합니다.
        POST /api/orders/
        """
        user = request.user
        try:
            cart = Cart.objects.get(user=user)
            cart_items = cart.items.all()

            if not cart_items.exists():
                return Response(
                    {"detail": "장바구니가 비어있습니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                total_price = sum(item.subtotal for item in cart_items)
                order = Order.objects.create(user=user, total_price=total_price)

                order_items = []
                for cart_item in cart_items:
                    order_items.append(
                        OrderItem(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price,
                        )
                    )
                OrderItem.objects.bulk_create(order_items)

                cart.items.all().delete()
                cart.delete()

            serializer = self.get_serializer(order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Cart.DoesNotExist:
            return Response(
                {"detail": "장바구니를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "장바구니에 존재하지 않는 상품이 포함되어 있습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"detail": f"주문 생성 중 오류 발생: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )