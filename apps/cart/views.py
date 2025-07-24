from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.cart.models import Cart, CartItem
from apps.cart.serializers import CartItemSerializer, CartSerializer


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # 비로그인 사용자도 이용가능하게 변경

    def get_queryset(self):
        """
        현재 사용자의 장바구니를 필터링합니다.
        """
        if self.request.user.is_authenticated:
            return Cart.objects.filter(user=self.request.user)
        # 비로그인 사용자는 세션 키를 기반으로 필터링
        session_key = self.request.session.session_key
        if not session_key:
            return Cart.objects.none()  # 세션이 없으면 빈 쿼리셋 반환
        return Cart.objects.filter(session_key=session_key)

    def get_object(self):
        """
        사용자의 장바구니를 가져오거나 생성합니다.
        로그인한 경우: user 기준
        비로그인 경우: session_key 기준
        """
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(session_key=session_key, defaults={"user": None})
        return cart

    def retrieve(self, request, *args, **kwargs):
        """
        현재 인증된 사용자의 장바구니 상세 정보를 조회합니다.
        GET /api/cart/
        응답: 현재 사용자의 장바구니 객체와 그 안에 포함된 상품 목록을 반환합니다.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="add-item")
    def add_item(self, request):
        """
        장바구니에 상품을 추가하거나, 이미 있는 상품의 수량을 증가시킵니다.
        POST /api/cart/add-item/
        요청 본문: {"product_id": "<상품 UUID>", "quantity": <수량>}
        """
        cart = self.get_object()
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # CartItemSerializer의 create 메소드에서 장바구니에 상품을 추가하거나 수량을 업데이트합니다.
        # serializer.save() 호출 시 cart=cart를 전달하여 현재 사용자의 장바구니에 아이템이 추가되도록 합니다.
        serializer.save(cart=cart)

        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["put"], url_path="update-item")
    def update_item(self, request):
        """
        장바구니에 있는 특정 상품의 수량을 업데이트합니다.
        수량이 0이 되면 해당 상품을 장바구니에서 제거합니다.
        PUT /api/cart/update-item/
        요청 본문: {"item_id": "<장바구니 아이템 UUID>", "quantity": <새로운 수량>}
        """
        cart = self.get_object()
        item_id = request.data.get("item_id")
        quantity = request.data.get("quantity")

        if not item_id or quantity is None:
            return Response({"detail": "제품 ID와 갯수가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 현재 사용자의 장바구니에 속한 아이템인지 확인
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response({"detail": "제품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if quantity <= 0:
            # 수량이 0 이하이면 장바구니에서 아이템 제거
            cart_item.delete()
        else:
            # 수량 업데이트
            serializer = CartItemSerializer(instance=cart_item, data={"quantity": quantity}, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="remove-item")
    def remove_item(self, request):
        """
        장바구니에서 특정 상품을 제거합니다.
        DELETE /api/cart/remove-item/
        요청 본문: {"item_id": "<장바구니 아이템 UUID>"}
        """
        cart = self.get_object()
        item_id = request.data.get("item_id")

        if not item_id:
            return Response({"detail": "제품 ID가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 현재 사용자의 장바구니에 속한 아이템인지 확인
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
        except CartItem.DoesNotExist:
            return Response({"detail": "제품을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response(self.get_serializer(cart).data, status=status.HTTP_200_OK)

        """
        TODO : 비 로그인 유저도 장바구니를 사용할 수 있게 만들고
               그 데이터를 임시 저장하여 로그인 시 장바구니에 적용되게 구현
        """
