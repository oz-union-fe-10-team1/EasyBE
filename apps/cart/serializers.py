from rest_framework import serializers

from apps.products.models import Product, ProductImage
from apps.stores.models import Store
from apps.stores.serializers import StoreSerializer

from .models import CartItem


class _CartProductSerializer(serializers.ModelSerializer):
    """
    장바구니 내부에 표시될 상품 정보를 위한 내부 시리얼라이저.
    Product가 drink인지 package인지에 따라 이름과 이미지를 가져옵니다.
    """

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

    # WRITE-ONLY fields for creating/updating cart items
    pickup_store_id = serializers.PrimaryKeyRelatedField(
        queryset=Store.objects.all(), write_only=True, source="pickup_store", required=True
    )
    pickup_date = serializers.DateField(required=True)

    # READ-ONLY fields for displaying cart items
    pickup_store_name = serializers.CharField(source="pickup_store.name", read_only=True)
    pickup_store_contact = serializers.CharField(source="pickup_store.contact", read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product",
            "product_id",
            "quantity",
            "subtotal",
            "pickup_store_id",
            "pickup_date",
            "pickup_store_name",
            "pickup_store_contact",
        ]
        read_only_fields = [
            "id",
            "product",
            "subtotal",
            "pickup_store_name",
            "pickup_store_contact",
        ]

    def get_subtotal(self, obj):
        """항목별 소계 (가격 * 수량)를 계산합니다."""
        return obj.product.price * obj.quantity

    def create(self, validated_data):
        """
        장바구니에 아이템을 추가하거나, 이미 있는 경우 수량을 업데이트합니다.
        고유성은 user, product, pickup_store, pickup_date를 기준으로 합니다.
        """
        user = self.context["request"].user
        product_id = validated_data.pop("product_id")
        product = Product.objects.get(id=product_id)
        pickup_store = validated_data.get("pickup_store")
        pickup_date = validated_data.get("pickup_date")
        quantity = validated_data.get("quantity", 1)

        cart_item, created = CartItem.objects.get_or_create(
            user=user,
            product=product,
            pickup_store=pickup_store,
            pickup_date=pickup_date,
            defaults={"quantity": quantity},
        )

        if not created:
            # 이미 동일한 항목(같은 상품, 같은 픽업 장소, 같은 픽업 날짜)이 존재하면 수량만 더합니다.
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item

    def update(self, instance, validated_data):
        """
        수량, 픽업 매장, 픽업 날짜 업데이트 로직을 커스터마이징합니다.
        수량이 0 이하로 들어오면 항목을 삭제하고, 그렇지 않으면 수량을 업데이트합니다.
        """
        quantity = validated_data.get("quantity", instance.quantity)
        pickup_store = validated_data.get("pickup_store", instance.pickup_store)
        pickup_date = validated_data.get("pickup_date", instance.pickup_date)

        if quantity <= 0:
            instance.delete()
            return None  # 삭제된 경우 아무것도 반환하지 않음
        else:
            instance.quantity = quantity
            instance.pickup_store = pickup_store
            instance.pickup_date = pickup_date
            instance.save()
            return instance
