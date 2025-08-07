# from collections import defaultdict
#
# from rest_framework import serializers
#
# from apps.cart.models import Cart, CartItem
# from apps.products.models import Product
#
#
# class ProductSerializer(serializers.ModelSerializer):
#     main_image_url = serializers.ReadOnlyField()
#
#     class Meta:
#         model = Product
#         fields = ["id", "name", "price", "main_image_url"]
#
#
# class CartItemSerializer(serializers.ModelSerializer):
#     product = ProductSerializer(read_only=True)
#     product_id = serializers.UUIDField(write_only=True)
#
#     class Meta:
#         model = CartItem
#         fields = ["id", "product", "product_id", "quantity", "subtotal"]
#         read_only_fields = ["subtotal"]
#
#     def create(self, validated_data):
#         product_id = validated_data.pop("product_id")
#         quantity = validated_data.get("quantity", 1)
#         cart = validated_data.get("cart")
#
#         try:
#             product = Product.objects.get(id=product_id)
#         except Product.DoesNotExist:
#             raise serializers.ValidationError("Product not found.")
#
#         # 단일 상품(package_group=None)에 대해서만 get_or_create 적용
#         cart_item, created = CartItem.objects.get_or_create(
#             cart=cart, product=product, package_group=None, defaults={"quantity": quantity}
#         )
#
#         if not created:
#             cart_item.quantity += quantity
#             cart_item.save()
#
#         return cart_item
#
#     def update(self, instance, validated_data):
#         instance.quantity = validated_data.get("quantity", instance.quantity)
#         instance.save()
#         return instance
#
#
# class PackageItemSerializer(serializers.ModelSerializer):
#     """패키지에 속한 개별 상품을 위한 시리얼라이저"""
#
#     product = ProductSerializer(read_only=True)
#
#     class Meta:
#         model = CartItem
#         fields = ["id", "product", "quantity", "subtotal"]
#
#
# class CartPackageSerializer(serializers.Serializer):
#     """패키지 그룹을 위한 시리얼라이저"""
#
#     package_group_id = serializers.UUIDField()
#     items = PackageItemSerializer(many=True)
#     package_price = serializers.SerializerMethodField()  # 패키지 총 가격
#
#     def get_package_price(self, obj):
#         # 패키지 가격 정책은 여기서 정의 (예: 각 상품 가격의 합)
#         return sum(item.subtotal for item in obj["items"])
#
#
# class CartSerializer(serializers.ModelSerializer):
#     # items 필드는 더 이상 직접 사용하지 않고, to_representation에서 동적으로 구성
#     total_price = serializers.DecimalField(max_digits=10, decimal_places=0, read_only=True)
#     final_total = serializers.SerializerMethodField()
#
#     # 응답에 포함될 새로운 필드
#     single_items = serializers.SerializerMethodField()
#     packages = serializers.SerializerMethodField()
#
#     class Meta:
#         model = Cart
#         fields = [
#             "id",
#             "user",
#             "single_items",  # 단일 상품 목록
#             "packages",  # 패키지 목록
#             "total_price",
#             "final_total",
#             "created_at",
#             "updated_at",
#         ]
#         read_only_fields = ["user", "created_at", "updated_at"]
#
#     def get_final_total(self, obj):
#         return obj.total_price
#
#     def get_single_items(self, obj):
#         # package_group이 없는 아이템만 필터링
#         single_items = obj.items.filter(package_group__isnull=True)
#         return CartItemSerializer(single_items, many=True).data
#
#     def get_packages(self, obj):
#         # package_group이 있는 아이템들을 그룹화
#         packages = defaultdict(list)
#         packaged_items = obj.items.filter(package_group__isnull=False)
#         for item in packaged_items:
#             packages[item.package_group].append(item)
#
#         # 직렬화
#         result = []
#         for group_id, items in packages.items():
#             result.append({"package_group_id": group_id, "items": items})
#         return CartPackageSerializer(result, many=True).data
