from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated # AllowAny 추가
from rest_framework.response import Response
from django.db import transaction

from apps.cart.models import Cart, CartItem
from apps.orders.models import Order, OrderItem
from apps.orders.serializers import OrderSerializer
from apps.products.models import Product


from rest_framework.authentication import SessionAuthentication # 추가


class OrderViewSet(viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication] # 추가

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True) # get_serializer_class 사용
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="create-from-cart")
    def create_order_from_cart(self, request):
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
                    # 주문 당시의 상품 가격을 저장
                    order_items.append(
                        OrderItem(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price,  # 현재 상품 가격을 저장
                        )
                    )
                    # 재고 감소 로직 (선택 사항, 필요 시 추가)
                    # cart_item.product.stock_quantity -= cart_item.quantity
                    # cart_item.product.save()

                OrderItem.objects.bulk_create(order_items)

                # 장바구니 비우기
                cart.items.all().delete()
                cart.delete() # 장바구니 자체도 삭제

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