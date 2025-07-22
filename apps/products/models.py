import uuid

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models, transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils import timezone


class Region(models.Model):
    """전통주 생산 지역"""

    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)  # 예: "GB" (경기), "JL" (전라)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "지역"
        verbose_name_plural = "지역"
        ordering = ["name"]

    def __str__(self):
        return self.name


class AlcoholType(models.Model):
    """전통주 주종 분류"""

    CATEGORY_CHOICES = [
        ("rice_wine", "막걸리/탁주"),
        ("clear_wine", "청주"),
        ("distilled", "소주/증류주"),
        ("fruit_wine", "과실주"),
        ("herb_wine", "약주/한방주"),
        ("other", "기타"),
    ]

    name = models.CharField(max_length=50)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "주종"
        verbose_name_plural = "주종"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class TasteTag(models.Model):
    """맛 태그 (단맛, 신맛, 쓴맛 등)"""

    TASTE_CATEGORY_CHOICES = [
        ("sweetness", "단맛"),
        ("sourness", "신맛"),
        ("bitterness", "쓴맛"),
        ("umami", "감칠맛"),
        ("astringency", "떫은맛"),
        ("freshness", "청량감"),
        ("richness", "진한맛"),
        ("lightness", "가벼운맛"),
        ("fruitiness", "과일향"),
        ("floral", "꽃향"),
        ("herbal", "허브향"),
        ("nutty", "견과류향"),
        ("spicy", "향신료맛"),
    ]

    name = models.CharField(max_length=30)
    category = models.CharField(max_length=20, choices=TASTE_CATEGORY_CHOICES)
    description = models.TextField(blank=True)
    color_code = models.CharField(
        max_length=7,
        default="#000000",
        validators=[
            RegexValidator(
                regex=r"^#(?:[0-9a-fA-F]{3}){1,2}$",
                message="올바른 HEX 색상 코드를 입력하세요.",
            )
        ],
        help_text="시각화용 색상 (#000000 형식)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "맛 태그"
        verbose_name_plural = "맛 태그"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class Brewery(models.Model):
    """양조장"""

    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # 양조장 특성
    founded_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    # 이미지
    logo_image = models.URLField(blank=True)
    cover_image = models.URLField(blank=True)

    # 상태
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "양조장"
        verbose_name_plural = "양조장"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """전통주 제품"""

    STATUS_CHOICES = [
        ("active", "판매중"),
        ("out_of_stock", "품절"),
        ("discontinued", "단종"),
        ("coming_soon", "출시예정"),
    ]

    # 기본 정보
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    brewery = models.ForeignKey(Brewery, on_delete=models.CASCADE, related_name="products")
    # 분류 정보
    alcohol_type = models.ForeignKey(AlcoholType, on_delete=models.SET_NULL, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(
        "ProductCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="상세 제품 카테고리 (알코올 타입보다 세분화)",
    )

    # 상품 상세 정보
    description = models.TextField()
    ingredients = models.TextField(help_text="주요 원료 (쌀, 누룩, 물 등)")
    alcohol_content = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="알코올 도수 (%)",
    )
    volume_ml = models.IntegerField(help_text="용량 (ml)")

    # 가격 정보
    price = models.DecimalField(max_digits=10, decimal_places=0, help_text="판매가격 (원)")
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        help_text="정가 (할인가 표시용)",
    )

    # 재고 관리
    stock_quantity = models.IntegerField(default=0, help_text="재고 수량")
    min_stock_alert = models.IntegerField(default=10, help_text="최소 재고 알림 기준")

    # 맛 프로필 (표준 맛 지수 - 추천 알고리즘 핵심) - UI 요구사항에 맞게 0~5 범위
    sweetness_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="단맛 지수 (0.0 ~ 5.0)",
    )
    sourness_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="신맛 지수 (0.0 ~ 5.0)",
    )
    bitterness_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="쓴맛 지수 (0.0 ~ 5.0)",
    )
    umami_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="감칠맛 지수 (0.0 ~ 5.0)",
    )
    alcohol_strength = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="알코올 강도 (0.0 ~ 5.0)",
    )
    body_level = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        help_text="바디감 (0.0: 가벼움, 5.0: 진함)",
    )

    # 제품 특성 정보 (UI 필터링 요구사항)
    is_gift_suitable = models.BooleanField(default=False, help_text="선물용 적합")
    is_award_winning = models.BooleanField(default=False, help_text="주류 대상 수상작")
    is_regional_specialty = models.BooleanField(default=False, help_text="지역 특산주")

    # UI 표시용 추가 필드
    flavor_notes = models.CharField(max_length=100, blank=True, help_text="향미 특징 (예: 복숭아향)")
    short_description = models.CharField(max_length=200, blank=True, help_text="간단 설명")
    package_name = models.CharField(max_length=100, blank=True, help_text="패키지명")

    # 맛 태그
    taste_tags = models.ManyToManyField(TasteTag, through="ProductTasteTag", blank=True)

    # 제품 특성
    is_limited_edition = models.BooleanField(default=False, help_text="한정판 여부")
    is_premium = models.BooleanField(default=False, help_text="프리미엄 제품 여부")
    is_organic = models.BooleanField(default=False, help_text="유기농 여부")

    # 추천 시스템용 메타데이터
    similarity_vector = models.JSONField(default=dict, blank=True, help_text="유사도 계산용 벡터 (캐시용)")
    recommendation_score = models.FloatField(default=0.0, help_text="기본 추천 점수")

    # 통계 정보
    view_count = models.PositiveIntegerField(default=0)
    order_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    review_count = models.PositiveIntegerField(default=0)

    # 상태 관리
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    is_featured = models.BooleanField(default=False, help_text="추천 제품 여부")
    launch_date = models.DateField(null=True, blank=True, help_text="출시일")

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO
    meta_title = models.CharField(max_length=100, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)

    class Meta:
        verbose_name = "전통주 제품"
        verbose_name_plural = "전통주 제품"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "is_featured"]),
            models.Index(fields=["alcohol_type", "region"]),
            models.Index(fields=["price"]),
            models.Index(fields=["-order_count"]),
            models.Index(fields=["-average_rating"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.brewery.name})"

    @property
    def is_available(self):
        """구매 가능 여부"""
        return self.status == "active" and self.stock_quantity > 0

    @property
    def discount_rate(self):
        """할인율 계산"""
        if self.original_price and self.original_price > self.price:
            return int((self.original_price - self.price) / self.original_price * 100)
        return 0

    @property
    def main_image_url(self):
        """메인 이미지 URL 반환"""
        main_image = self.images.filter(is_main=True).first()
        return main_image.image_url if main_image else ""

    @property
    def taste_profile_vector(self):
        """맛 프로필을 벡터로 반환 (추천 알고리즘용)"""
        return [
            float(self.sweetness_level),
            float(self.sourness_level),
            float(self.bitterness_level),
            float(self.umami_level),
            float(self.alcohol_strength),
            float(self.body_level),
        ]

    def increment_view_count(self):
        """조회수 증가"""
        self.view_count += 1
        self.save(update_fields=["view_count"])

    def update_rating(self, new_rating, review_count_change=1):
        """평점 업데이트"""
        if self.review_count == 0:
            self.average_rating = new_rating
        else:
            total_score = self.average_rating * self.review_count
            total_score += new_rating * review_count_change
            self.review_count += review_count_change
            self.average_rating = total_score / self.review_count if self.review_count > 0 else 0

        self.save(update_fields=["average_rating", "review_count"])


class ProductTasteTag(models.Model):
    """제품-맛태그 중간 테이블 (가중치 포함)"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    taste_tag = models.ForeignKey(TasteTag, on_delete=models.CASCADE)
    intensity = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.1), MaxValueValidator(3.0)],
        help_text="태그 강도 (0.1: 약함, 1.0: 보통, 3.0: 강함)",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "제품 맛 태그"
        verbose_name_plural = "제품 맛 태그"
        unique_together = ["product", "taste_tag"]

    def __str__(self):
        return f"{self.product.name} - {self.taste_tag.name} ({self.intensity:.1f})"


class ProductCategory(models.Model):
    """제품 카테고리 (추가 분류용)"""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

    # 카테고리 이미지
    image = models.URLField(blank=True)

    # 표시 순서
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "제품 카테고리"
        verbose_name_plural = "제품 카테고리"
        ordering = ["sort_order", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name


class ProductImage(models.Model):
    """제품 이미지"""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "제품 이미지"
        verbose_name_plural = "제품 이미지"
        ordering = ["sort_order"]

    def save(self, *args, **kwargs):
        """메인 이미지 무결성 보장"""
        if self.is_main:
            # 같은 제품의 다른 이미지들을 모두 메인에서 해제
            with transaction.atomic():
                ProductImage.objects.filter(product=self.product).exclude(pk=self.pk if self.pk else None).update(
                    is_main=False
                )

        super().save(*args, **kwargs)

        # 저장 후 메인 이미지가 없다면 이 이미지를 메인으로 설정
        if not self.is_main and not ProductImage.objects.filter(product=self.product, is_main=True).exists():
            self.is_main = True
            ProductImage.objects.filter(pk=self.pk).update(is_main=True)

    def __str__(self):
        main_text = " (메인)" if self.is_main else ""
        return f"{self.product.name} 이미지 {self.sort_order}{main_text}"


class ProductLike(models.Model):
    """제품 찜하기/좋아요"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "제품 좋아요"
        verbose_name_plural = "제품 좋아요"
        unique_together = ["user", "product"]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class ProductRecommendation(models.Model):
    """개인화 추천 결과 캐시"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # 추천 점수 및 근거
    score = models.FloatField(help_text="추천 점수 (0.0 ~ 1.0)")
    reason = models.TextField(help_text="추천 이유")
    algorithm_version = models.CharField(max_length=20, default="v1.0")

    # 추천 카테고리
    RECOMMENDATION_TYPE_CHOICES = [
        ("taste_based", "취향 기반"),
        ("similar_user", "유사 사용자"),
        ("trending", "인기 상품"),
        ("new_product", "신제품"),
        ("seasonal", "계절 추천"),
        ("onboarding", "온보딩 추천"),
    ]
    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPE_CHOICES)

    # 캐시 관리
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "제품 추천"
        verbose_name_plural = "제품 추천"
        unique_together = ["user", "product", "recommendation_type"]
        indexes = [
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["recommendation_type", "-score"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name} ({self.score:.2f})"

    @property
    def is_expired(self):
        """추천 만료 여부"""
        return timezone.now() > self.expires_at

    @classmethod
    def cleanup_expired(cls):
        """만료된 추천 데이터 정리"""
        expired_count = cls.objects.filter(expires_at__lt=timezone.now()).count()
        cls.objects.filter(expires_at__lt=timezone.now()).delete()
        return expired_count


# =============================================================================
# Django 시그널: 메인 이미지 삭제 시 자동 처리
# =============================================================================

from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=ProductImage)
def ensure_main_image_exists(sender, instance, **kwargs):
    """메인 이미지 삭제 시 다른 이미지를 자동으로 메인으로 설정"""
    if instance.is_main:
        # 같은 제품의 다른 이미지 중 첫 번째를 메인으로 설정
        next_image = ProductImage.objects.filter(product=instance.product).order_by("sort_order").first()

        if next_image:
            next_image.is_main = True
            next_image.save()
