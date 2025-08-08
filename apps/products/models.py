# apps/products/models.py

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Brewery(models.Model):
    """양조장 정보"""

    name = models.CharField(max_length=100)
    region = models.CharField(max_length=30, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_url = models.URLField(max_length=255, null=True, blank=True)  # image → image_url
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "breweries"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["region"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name


class Drink(models.Model):
    """개별 술 정보"""

    class AlcoholType(models.TextChoices):
        MAKGEOLLI = "MAKGEOLLI", "막걸리"
        YAKJU = "YAKJU", "약주"
        CHEONGJU = "CHEONGJU", "청주"
        SOJU = "SOJU", "소주"
        FRUIT_WINE = "FRUIT_WINE", "과실주"

    name = models.CharField(max_length=100)
    brewery = models.ForeignKey(Brewery, on_delete=models.CASCADE, related_name="drinks")
    ingredients = models.TextField(help_text="원재료")
    alcohol_type = models.CharField(max_length=20, choices=AlcoholType.choices, help_text="주종")
    abv = models.DecimalField(  # alcohol_content → abv
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="알코올 도수",
    )
    volume_ml = models.PositiveIntegerField(help_text="용량(ml)")

    # 맛 프로필 (0.0 ~ 5.0)
    sweetness_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )
    acidity_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )
    body_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )
    carbonation_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )
    bitterness_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )
    aroma_level = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=Decimal("0.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drinks"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["alcohol_type"]),
            models.Index(fields=["abv"]),  # alcohol_content → abv
        ]

    def __str__(self):
        return f"{self.name} ({self.abv}%)"


class Package(models.Model):
    """패키지 (세트 상품)"""

    class PackageType(models.TextChoices):
        CURATED = "CURATED", "큐레이티드"
        MY_CUSTOM = "MY_CUSTOM", "마이 커스텀"

    name = models.CharField(max_length=30)
    type = models.CharField(max_length=10, choices=PackageType.choices, default=PackageType.CURATED)
    drinks = models.ManyToManyField(Drink, through="PackageItem", related_name="packages")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "packages"
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class PackageItem(models.Model):
    """패키지에 포함된 술들"""

    drink = models.ForeignKey(Drink, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "package_items"
        unique_together = ("drink", "package")  # 같은 패키지에 같은 술 중복 방지


class Product(models.Model):
    """상품 (개별 술 또는 패키지)"""

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "활성"
        INACTIVE = "INACTIVE", "비활성"
        OUT_OF_STOCK = "OUT_OF_STOCK", "품절"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 상품은 개별 술이거나 패키지 중 하나
    drink = models.OneToOneField(Drink, on_delete=models.CASCADE, null=True, blank=True, related_name="product")
    package = models.OneToOneField(Package, on_delete=models.CASCADE, null=True, blank=True, related_name="product")

    # 가격 정보 (할인 정책 포함)
    price = models.PositiveIntegerField(help_text="판매가격")
    original_price = models.PositiveIntegerField(null=True, blank=True, help_text="정가")
    discount = models.PositiveIntegerField(null=True, blank=True, help_text="할인금액")

    # 상품 설명
    description = models.TextField()
    description_image_url = models.URLField(max_length=255)

    # 상품 특성
    is_gift_suitable = models.BooleanField(default=False)
    is_award_winning = models.BooleanField(default=False)
    is_regional_specialty = models.BooleanField(default=False)
    is_limited_edition = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    is_organic = models.BooleanField(default=False)

    # 통계
    view_count = models.PositiveIntegerField(default=0)
    order_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "products"
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["-view_count"]),
            models.Index(fields=["-order_count"]),
        ]

    def clean(self):
        """drink와 package 중 하나는 반드시 있어야 함"""
        if not self.drink and not self.package:
            raise ValidationError("상품은 개별 술이거나 패키지 중 하나여야 합니다.")
        if self.drink and self.package:
            raise ValidationError("상품은 개별 술과 패키지를 동시에 가질 수 없습니다.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        if self.drink:
            return f"상품: {self.drink.name}"
        elif self.package:
            return f"상품: {self.package.name}"
        return f"상품 ID: {self.id}"

    @property
    def name(self):
        """상품명 반환"""
        if self.drink:
            return self.drink.name
        elif self.package:
            return self.package.name
        return "Unknown Product"

    @property
    def product_type(self):
        """상품 타입 반환"""
        if self.drink:
            return "individual"
        elif self.package:
            return "package"
        return "unknown"

    def get_discount_rate(self):
        """할인율 계산 (퍼센트)"""
        if self.original_price and self.discount:
            return round((self.discount / self.original_price) * 100, 1)
        return 0

    def get_final_price(self):
        """최종 판매가 계산"""
        # price가 이미 할인된 가격이라고 가정
        return self.price

    def is_on_sale(self):
        """할인 중인지 확인"""
        return bool(self.discount and self.discount > 0)

    def get_savings_amount(self):
        """절약 금액"""
        return self.discount if self.discount else 0


class ProductImage(models.Model):
    """상품 이미지"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=255)
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_images"
        indexes = [
            models.Index(fields=["product", "is_main"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["product"], condition=models.Q(is_main=True), name="unique_main_image_per_product"
            )
        ]

    def clean(self):
        """메인 이미지는 상품당 하나만 허용"""
        if self.is_main:
            existing_main = ProductImage.objects.filter(product=self.product, is_main=True).exclude(pk=self.pk)
            if existing_main.exists():
                raise ValidationError("상품당 메인 이미지는 하나만 설정할 수 있습니다.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {'메인' if self.is_main else '서브'} 이미지"


class ProductLike(models.Model):
    """상품 좋아요"""

    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="liked_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product_likes"
        unique_together = ("user", "product")
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["product"]),
        ]

    def __str__(self):
        return f"{self.user.nickname} - {self.product.name}"
