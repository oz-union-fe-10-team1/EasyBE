from rest_framework import serializers

from apps.products.models import Product, ProductImage

from .models import CartItem


class _CartProductSerializer(serializers.ModelSerializer):
    """
    장바구니 내부에 표시될 상품 정보를 위한 내부 시리얼라이저.
    Product가 drink인지 package인지에 따라 이름과 이미지를 가져옵니다.
    """

    name = serializers.CharField(source="product.name", read_only=True)
    main_image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "main_image"]

    def get_main_image(self, obj):
        """상품의 메인 이미지를 반환합니다."""
        try:
            image = ProductImage.objects.filter(product=obj, is_main=True).first()
            return image.image_url if image else None
        except Exception:
            return None


class CartItemSerializer(serializers.ModelSerializer):
    """
    장바구니 항목 CRUD를 위한 메인 시리얼라이저
    """

    product = _CartProductSerializer(read_only=True)
    product_id = serializers.CharField(write_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal"]
        read_only_fields = ["id", "product", "subtotal"]

    def get_subtotal(self, obj):
        """항목별 소계 (가격 * 수량)를 계산합니다."""
        return obj.product.price * obj.quantity

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        # 이미 장바구니에 있는 상품이면 수량만 더해줌
        product_id = validated_data.get("product_id")
        product = Product.objects.get(id=product_id)
        quantity = validated_data.get("quantity")
        cart_item, created = CartItem.objects.get_or_create(
            user=validated_data["user"],
            product=product,
            defaults={"quantity": quantity},
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return cart_item

    def update(self, instance, validated_data):
        """
        수량 업데이트 로직을 커스터마이징합니다.
        수량이 0 이하로 들어오면 항목을 삭제하고, 그렇지 않으면 수량을 업데이트합니다.
        """
        quantity = validated_data.get("quantity", instance.quantity)

        if quantity <= 0:
            instance.delete()
            return None  # 삭제된 경우 아무것도 반환하지 않음
        else:
            instance.quantity = quantity
            instance.save()
            return instance
