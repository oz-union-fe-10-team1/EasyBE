import uuid

from django.db import transaction
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cart.models import Cart, CartItem
from apps.cart.serializers import CartItemSerializer, CartSerializer
from apps.products.models import Product


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        현재 사용자의 장바구니를 필터링합니다.
        """
        return Cart.objects.filter(user=self.request.user)

    def get_object(self):
        """
        현재 사용자의 장바구니를 가져오거나 생성합니다.
        """
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request, *args, **kwargs):
        """
        현재 인증된 사용자의 장바구니 상세 정보를 조회합니다.
        GET /api/cart/
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="add-item")
    def add_item(self, request):
        """
        장바구니에 단일 상품을 추가합니다.
        POST /api/cart/add-item/
        """
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(cart=cart)
        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="add-package")
    @transaction.atomic
    def add_package(self, request):
        """
        장바구니에 패키지 상품(3개 묶음)을 추가합니다.
        POST /api/cart/add-package/
        요청 본문: {"product_ids": ["<상품1 UUID>", "<상품2 UUID>", "<상품3 UUID>"]}
        """
        cart = self.get_object()
        product_ids = request.data.get("product_ids")

        if not isinstance(product_ids, list) or len(product_ids) != 3:
            return Response({"detail": "3개의 상품 ID 리스트가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        package_group_id = uuid.uuid4()
        for product_id in product_ids:
            try:
                product = Product.objects.get(id=product_id)
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=1,  # 패키지 내 상품 수량은 항상 1
                    package_group=package_group_id,
                )
            except Product.DoesNotExist:
                # transaction.atomic에 의해 모든 변경이 롤백됨
                raise serializers.ValidationError(f"Product with id {product_id} not found.")

        return Response(self.get_serializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["put"], url_path="update-item")
    def update_item(self, request):
        """
        장바구니에 있는 단일 상품의 수량을 업데이트합니다.
        PUT /api/cart/update-item/
        """
        cart = self.get_object()
        item_id = request.data.get("item_id")
        quantity = request.data.get("quantity")

        if not item_id or quantity is None:
            return Response({"detail": "제품 ID와 갯수가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 단일 상품(package_group=None)만 수정 가능
            cart_item = CartItem.objects.get(id=item_id, cart=cart, package_group=None)
        except CartItem.DoesNotExist:
            return Response({"detail": "수정할 수 있는 상품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = quantity
            cart_item.save()

        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="remove-item")
    def remove_item(self, request):
        """
        장바구니에서 특정 상품 또는 패키지 전체를 제거합니다.
        DELETE /api/cart/remove-item/
        요청 본문: {"item_id": "<장바구니 아이템 UUID>"} 또는 {"package_group_id": "<패키지 그룹 UUID>"}
        """
        cart = self.get_object()
        item_id = request.data.get("item_id")
        package_group_id = request.data.get("package_group_id")

        if not item_id and not package_group_id:
            return Response({"detail": "제품 ID 또는 패키지 그룹 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        if item_id:
            # 단일 상품 삭제
            deleted_count, _ = CartItem.objects.filter(id=item_id, cart=cart, package_group=None).delete()
        elif package_group_id:
            # 패키지 전체 삭제
            deleted_count, _ = CartItem.objects.filter(package_group=package_group_id, cart=cart).delete()

        if deleted_count == 0:
            return Response({"detail": "삭제할 상품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)
