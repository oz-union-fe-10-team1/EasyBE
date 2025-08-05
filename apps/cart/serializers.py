from rest_framework import serializers
from .models import Cart, CartItem
from apps.products.models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "price"]

class CartItemSerializer(serializers.ModelSerializer):
    # item_type은 읽기 전용으로, 생성 시에는 다른 필드를 통해 유추
    item_type = serializers.CharField(read_only=True)
    item_details = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ["id", "item_type", "quantity", "item_details", "subtotal", "added_at"]

    def get_item_details(self, obj):
        if obj.item_type == CartItem.ItemType.PRODUCT:
            return ProductSerializer(obj.product).data
        # if obj.item_type == CartItem.ItemType.CUSTOM_TRIO:
        #     return CustomTrioSetSerializer(obj.custom_trio_set).data
        return None

    def get_subtotal(self, obj):
        if obj.item_type == CartItem.ItemType.PRODUCT:
            return obj.product.price * obj.quantity
        # if obj.item_type == CartItem.ItemType.CUSTOM_TRIO:
        #     return obj.custom_trio_set.final_price * obj.quantity
        return 0

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "user", "items", "total_price", "created_at", "updated_at"]

    def get_total_price(self, obj):
        # subtotal 계산 로직을 CartItemSerializer로 위임
        return sum(CartItemSerializer(item).get_subtotal(item) for item in obj.items.all())