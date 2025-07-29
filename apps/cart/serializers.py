from rest_framework import serializers

from apps.cart.models import Cart, CartItem
from apps.products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    main_image_url = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = ["id", "name", "price", "main_image_url"]


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "product_id", "quantity", "subtotal"]
        read_only_fields = ["subtotal"]

    def create(self, validated_data):
        product_id = validated_data.pop("product_id")
        quantity = validated_data.get("quantity", 1)
        cart = validated_data.get("cart")

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found.")

        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return cart_item

    def update(self, instance, validated_data):
        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save()
        return instance


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
    final_total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ["id", "customer", "items", "total_price", "final_total", "created_at", "updated_at"]
        read_only_fields = ["customer", "created_at", "updated_at"]

    def get_final_total(self, obj):
        return obj.total_price
