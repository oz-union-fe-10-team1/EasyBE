# apps/products/tests/base.py

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase

from apps.products.models import (
    AlcoholType,
    Brewery,
    Product,
    ProductCategory,
    ProductLike,
    ProductTasteTag,
    Region,
    TasteTag,
)

User = get_user_model()


class ProductTestMixin:
    """제품 테스트용 공통 데이터 Mixin"""

    def create_users(self):
        """사용자 데이터 생성"""
        self.user = User.objects.create(nickname="testuser", email="user@example.com", role=User.Role.USER)

        self.admin_user = User.objects.create(nickname="admin_test", email="admin@example.com", role=User.Role.ADMIN)

        # 추가 테스트 사용자들
        self.user2 = User.objects.create(nickname="testuser2", email="user2@example.com", role=User.Role.USER)

        self.premium_user = User.objects.create(
            nickname="premium_user", email="premium@example.com", role=User.Role.USER
        )

    def create_basic_data(self):
        """기본 마스터 데이터 생성"""
        # 지역 데이터 (확장)
        self.region_gg = Region.objects.create(name="경기", code="GG", description="경기도 지역")

        self.region_jl = Region.objects.create(name="전라", code="JL", description="전라도 지역")

        self.region_gs = Region.objects.create(name="경상", code="GS", description="경상도 지역")

        self.region_cc = Region.objects.create(name="충청", code="CC", description="충청도 지역")

        self.region_gw = Region.objects.create(name="강원", code="GW", description="강원도 지역")

        # 주류 타입 (확장)
        self.alcohol_type = AlcoholType.objects.create(
            name="생막걸리", category="rice_wine", description="살아있는 효모 막걸리"
        )

        self.soju_type = AlcoholType.objects.create(name="소주", category="distilled", description="전통 증류주")

        self.clear_wine_type = AlcoholType.objects.create(name="청주", category="clear_wine", description="맑은 전통주")

        self.fruit_wine_type = AlcoholType.objects.create(
            name="과실주", category="fruit_wine", description="과일로 만든 술"
        )

        self.herb_wine_type = AlcoholType.objects.create(
            name="약주", category="herb_wine", description="한방 재료가 들어간 술"
        )

        # 카테고리 (확장)
        self.category = ProductCategory.objects.create(
            name="생막걸리", slug="fresh-makgeolli", description="신선한 생막걸리"
        )

        self.premium_category = ProductCategory.objects.create(
            name="프리미엄 막걸리", slug="premium-makgeolli", description="고급 막걸리", sort_order=1
        )

        self.traditional_category = ProductCategory.objects.create(
            name="전통주", slug="traditional-liquor", description="전통 방식의 술", sort_order=2
        )

        # 양조장 (확장)
        self.brewery1 = Brewery.objects.create(
            name="장수막걸리",
            region=self.region_gg,
            address="경기도 포천시",
            phone="031-123-4567",
            founded_year=1925,
            is_active=True,
        )

        self.brewery2 = Brewery.objects.create(
            name="전주막걸리",
            region=self.region_jl,
            address="전라북도 전주시",
            phone="063-987-6543",
            founded_year=1950,
            is_active=True,
        )

        self.brewery3 = Brewery.objects.create(
            name="경주법주",
            region=self.region_gs,
            address="경상북도 경주시",
            phone="054-111-2222",
            founded_year=1900,
            is_active=True,
        )

        self.brewery4 = Brewery.objects.create(
            name="충주양조장",
            region=self.region_cc,
            address="충청북도 충주시",
            phone="043-333-4444",
            founded_year=1960,
            is_active=True,
        )

        self.brewery5 = Brewery.objects.create(
            name="춘천주조",
            region=self.region_gw,
            address="강원도 춘천시",
            phone="033-555-6666",
            founded_year=1980,
            is_active=True,
        )

    def create_taste_tags(self):
        """맛 태그 데이터 생성 (확장)"""
        # 단맛 계열
        self.sweet_tag = TasteTag.objects.create(name="달콤한", category="sweetness", color_code="#FF6B9D")

        self.honey_tag = TasteTag.objects.create(name="꿀맛", category="sweetness", color_code="#FFD700")

        # 청량감 계열
        self.fresh_tag = TasteTag.objects.create(name="상큼한", category="freshness", color_code="#4ECDC4")

        self.cool_tag = TasteTag.objects.create(name="시원한", category="freshness", color_code="#87CEEB")

        # 바디감 계열
        self.rich_tag = TasteTag.objects.create(name="진한", category="richness", color_code="#8B4513")

        self.light_tag = TasteTag.objects.create(name="가벼운", category="lightness", color_code="#F0F8FF")

        # 향 계열
        self.floral_tag = TasteTag.objects.create(name="꽃향", category="floral", color_code="#DDA0DD")

        self.fruit_tag = TasteTag.objects.create(name="과일향", category="fruitiness", color_code="#FF6347")

        self.nutty_tag = TasteTag.objects.create(name="견과류향", category="nutty", color_code="#D2691E")

        # 기타
        self.spicy_tag = TasteTag.objects.create(name="매콤한", category="spicy", color_code="#FF4500")

    def create_products(self):
        """테스트용 제품 데이터 생성 (대폭 확장)"""
        # 1. 메인 테스트 제품 (기존)
        self.product = Product.objects.create(
            name="장수 생막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            region=self.region_gg,
            category=self.category,
            description="부드럽고 달콤한 생막걸리입니다. 전통 방식으로 빚어낸 생막걸리로 깔끔한 맛이 특징입니다.",
            ingredients="쌀(국내산), 누룩, 정제수",
            alcohol_content=6.0,
            volume_ml=750,
            price=Decimal("8000"),
            original_price=Decimal("10000"),
            stock_quantity=100,
            min_stock_alert=10,
            # 맛 프로필
            sweetness_level=4.0,
            acidity_level=2.5,
            body_level=3.0,
            carbonation_level=1.5,
            bitterness_level=1.0,
            aroma_level=4.5,
            # 제품 특성
            is_gift_suitable=True,
            is_award_winning=True,
            is_regional_specialty=True,
            is_limited_edition=False,
            is_premium=False,
            is_organic=True,
            # UI 표시용
            flavor_notes="복숭아향, 달콤함, 깔끔한 목 넘김",
            short_description="부드럽고 달콤한 생막걸리",
            package_name="장수 생막걸리 750ml",
            # 상태
            status="active",
            is_featured=True,
            # 통계
            view_count=150,
            order_count=75,
            like_count=25,
            average_rating=4.5,
            review_count=12,
            # SEO
            meta_title="장수 생막걸리 - 전통 생막걸리의 진수",
            meta_description="부드럽고 달콤한 장수 생막걸리. 전통 방식으로 빚어낸 프리미엄 생막걸리를 만나보세요.",
        )

        # 2. 두 번째 제품 (기존)
        self.product2 = Product.objects.create(
            name="전주 탁주",
            brewery=self.brewery2,
            alcohol_type=self.alcohol_type,
            region=self.region_jl,
            category=self.category,
            description="전통 방식의 탁주",
            ingredients="쌀, 누룩, 물",
            alcohol_content=7.0,
            volume_ml=500,
            price=Decimal("12000"),
            stock_quantity=50,
            sweetness_level=2.0,
            acidity_level=4.0,
            body_level=4.0,
            carbonation_level=0.5,
            bitterness_level=3.0,
            aroma_level=3.5,
            status="active",
            view_count=200,
            order_count=30,
        )

        # 3. 인기 제품 (높은 주문수, 조회수)
        self.popular_product = Product.objects.create(
            name="인기 막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            region=self.region_gg,
            category=self.category,
            description="가장 인기가 많은 제품입니다",
            ingredients="쌀, 누룩, 정제수",
            alcohol_content=6.5,
            volume_ml=750,
            price=Decimal("9000"),
            stock_quantity=200,
            sweetness_level=3.5,
            acidity_level=2.0,
            body_level=3.5,
            status="active",
            view_count=2000,  # 매우 높은 조회수
            order_count=500,  # 매우 높은 주문수
            like_count=150,
            average_rating=4.8,
            review_count=85,
            is_featured=False,
            is_award_winning=False,
            is_regional_specialty=False,
        )

        # 4. 추천 제품 (featured)
        self.featured_product = Product.objects.create(
            name="에디터 추천 막걸리",
            brewery=self.brewery2,
            alcohol_type=self.alcohol_type,
            region=self.region_jl,
            category=self.premium_category,
            description="에디터가 엄선한 추천 제품",
            ingredients="프리미엄 쌀, 특수 누룩",
            alcohol_content=7.5,
            volume_ml=750,
            price=Decimal("15000"),
            stock_quantity=80,
            sweetness_level=3.0,
            acidity_level=3.0,
            body_level=4.0,
            status="active",
            view_count=800,
            order_count=120,
            like_count=45,
            average_rating=4.6,
            is_featured=True,  # 추천 제품
            is_award_winning=False,
            is_regional_specialty=False,
            is_premium=True,
        )

        # 5. 수상 제품 (award winning)
        self.award_product = Product.objects.create(
            name="대상 수상 막걸리",
            brewery=self.brewery3,
            alcohol_type=self.alcohol_type,
            region=self.region_gs,
            category=self.premium_category,
            description="전국 막걸리 품평회 대상 수상작",
            ingredients="유기농 쌀, 전통 누룩",
            alcohol_content=8.0,
            volume_ml=750,
            price=Decimal("25000"),
            original_price=Decimal("30000"),
            stock_quantity=30,
            sweetness_level=2.5,
            acidity_level=3.5,
            body_level=5.0,
            status="active",
            view_count=600,
            order_count=80,
            like_count=35,
            average_rating=4.9,
            is_featured=False,
            is_award_winning=True,  # 수상 제품
            is_regional_specialty=False,
            is_premium=True,
            is_organic=True,
        )

        # 6. 지역 특산물 (regional specialty)
        self.regional_product = Product.objects.create(
            name="강원도 특산 막걸리",
            brewery=self.brewery5,
            alcohol_type=self.alcohol_type,
            region=self.region_gw,
            category=self.traditional_category,
            description="강원도 지역에서만 생산되는 특산주",
            ingredients="강원도 토종쌀, 산양삼",
            alcohol_content=6.0,
            volume_ml=750,
            price=Decimal("18000"),
            stock_quantity=60,
            sweetness_level=3.0,
            acidity_level=2.0,
            body_level=3.5,
            status="active",
            view_count=400,
            order_count=50,
            like_count=20,
            is_featured=False,
            is_award_winning=False,
            is_regional_specialty=True,  # 지역 특산물
            is_organic=True,
        )

        # 7. 소주 제품 (다른 주류 타입)
        self.soju_product = Product.objects.create(
            name="전통 소주",
            brewery=self.brewery4,
            alcohol_type=self.soju_type,  # 다른 주류 타입
            region=self.region_cc,
            category=self.traditional_category,
            description="전통 방식으로 증류한 소주",
            ingredients="쌀, 누룩, 정제수",
            alcohol_content=25.0,
            volume_ml=375,
            price=Decimal("35000"),
            stock_quantity=40,
            sweetness_level=1.0,
            acidity_level=1.5,
            body_level=4.5,
            bitterness_level=2.0,
            status="active",
            view_count=300,
            order_count=25,
            is_featured=False,
            is_award_winning=False,
            is_regional_specialty=True,
            is_premium=True,
        )

        # 8. 청주 제품
        self.clear_wine_product = Product.objects.create(
            name="프리미엄 청주",
            brewery=self.brewery3,
            alcohol_type=self.clear_wine_type,
            region=self.region_gs,
            category=self.premium_category,
            description="깔끔하고 우아한 청주",
            ingredients="프리미엄 쌀, 정선된 누룩",
            alcohol_content=15.0,
            volume_ml=750,
            price=Decimal("45000"),
            stock_quantity=25,
            sweetness_level=2.0,
            acidity_level=2.5,
            body_level=3.0,
            status="active",
            view_count=250,
            order_count=15,
            is_featured=True,
            is_award_winning=True,
            is_premium=True,
        )

        # 9. 과실주 제품
        self.fruit_wine_product = Product.objects.create(
            name="복분자 과실주",
            brewery=self.brewery2,
            alcohol_type=self.fruit_wine_type,
            region=self.region_jl,
            description="전라도 복분자로 만든 과실주",
            ingredients="복분자, 쌀, 누룩",
            alcohol_content=12.0,
            volume_ml=500,
            price=Decimal("28000"),
            stock_quantity=45,
            sweetness_level=4.5,
            acidity_level=3.0,
            body_level=2.5,
            status="active",
            view_count=180,
            order_count=20,
            is_featured=False,
            is_regional_specialty=True,
        )

        # 10. 한정판 제품
        self.limited_product = Product.objects.create(
            name="한정판 막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            region=self.region_gg,
            category=self.premium_category,
            description="연간 100병만 생산되는 한정판",
            ingredients="희귀 쌀 품종, 100년 누룩",
            alcohol_content=9.0,
            volume_ml=750,
            price=Decimal("100000"),
            stock_quantity=5,
            sweetness_level=3.5,
            acidity_level=2.0,
            body_level=5.0,
            status="active",
            view_count=500,
            order_count=3,
            like_count=50,
            is_featured=True,
            is_award_winning=True,
            is_limited_edition=True,  # 한정판
            is_premium=True,
            is_organic=True,
        )

        # 11. 신제품 (최근 출시)
        self.new_product = Product.objects.create(
            name="신제품 막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            region=self.region_gg,
            description="갓 출시된 신제품",
            ingredients="신품종 쌀, 개량 누룩",
            alcohol_content=6.5,
            volume_ml=750,
            price=Decimal("11000"),
            stock_quantity=100,
            sweetness_level=3.8,
            acidity_level=2.2,
            body_level=3.2,
            status="active",
            view_count=50,  # 낮은 조회수 (신제품)
            order_count=5,  # 낮은 주문수 (신제품)
            is_featured=False,
        )

        # 12. 비활성 제품들 (기존)
        self.out_of_stock_product = Product.objects.create(
            name="품절 제품",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="현재 품절된 제품",
            ingredients="쌀, 누룩",
            alcohol_content=6.0,
            volume_ml=750,
            price=Decimal("5000"),
            stock_quantity=0,
            status="out_of_stock",
        )

        self.discontinued_product = Product.objects.create(
            name="단종된 제품",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="단종된 제품입니다",
            ingredients="쌀, 누룩",
            alcohol_content=6.0,
            volume_ml=750,
            price=Decimal("7000"),
            status="discontinued",
        )

        # 13. 복합 특성 제품 (여러 특성 동시 보유)
        self.multi_feature_product = Product.objects.create(
            name="올인원 프리미엄 막걸리",
            brewery=self.brewery2,
            alcohol_type=self.alcohol_type,
            region=self.region_jl,
            category=self.premium_category,
            description="추천+수상+지역특산 모든 조건을 만족하는 제품",
            ingredients="유기농 쌀, 전통 누룩, 특수 첨가물",
            alcohol_content=7.8,
            volume_ml=750,
            price=Decimal("35000"),
            original_price=Decimal("45000"),
            stock_quantity=20,
            sweetness_level=3.2,
            acidity_level=2.8,
            body_level=4.2,
            status="active",
            view_count=800,
            order_count=90,
            like_count=40,
            average_rating=4.7,
            is_featured=True,  # 추천 제품
            is_award_winning=True,  # 수상 제품
            is_regional_specialty=True,  # 지역 특산물
            is_premium=True,
            is_organic=True,
        )

    def create_product_taste_tags(self):
        """제품-맛태그 관계 생성 (확장)"""
        # 메인 제품에 맛 태그 연결 (기존)
        ProductTasteTag.objects.create(product=self.product, taste_tag=self.sweet_tag, intensity=4.0)

        ProductTasteTag.objects.create(product=self.product, taste_tag=self.fresh_tag, intensity=3.0)

        # 두 번째 제품에도 연결 (기존)
        ProductTasteTag.objects.create(product=self.product2, taste_tag=self.rich_tag, intensity=3.5)

        # 인기 제품 태그
        ProductTasteTag.objects.create(product=self.popular_product, taste_tag=self.sweet_tag, intensity=3.5)
        ProductTasteTag.objects.create(product=self.popular_product, taste_tag=self.fruit_tag, intensity=2.8)

        # 추천 제품 태그
        ProductTasteTag.objects.create(product=self.featured_product, taste_tag=self.rich_tag, intensity=4.0)
        ProductTasteTag.objects.create(product=self.featured_product, taste_tag=self.floral_tag, intensity=3.2)

        # 수상 제품 태그
        ProductTasteTag.objects.create(product=self.award_product, taste_tag=self.honey_tag, intensity=4.5)
        ProductTasteTag.objects.create(product=self.award_product, taste_tag=self.nutty_tag, intensity=3.8)

        # 지역 특산물 태그
        ProductTasteTag.objects.create(product=self.regional_product, taste_tag=self.fresh_tag, intensity=4.2)
        ProductTasteTag.objects.create(product=self.regional_product, taste_tag=self.light_tag, intensity=3.5)

        # 소주 제품 태그
        ProductTasteTag.objects.create(product=self.soju_product, taste_tag=self.spicy_tag, intensity=2.5)
        ProductTasteTag.objects.create(product=self.soju_product, taste_tag=self.rich_tag, intensity=4.0)

    def create_product_likes(self):
        """제품 좋아요 관계 생성"""
        # user가 좋아요한 제품들
        ProductLike.objects.create(user=self.user, product=self.product)
        ProductLike.objects.create(user=self.user, product=self.featured_product)
        ProductLike.objects.create(user=self.user, product=self.award_product)

        # user2가 좋아요한 제품들
        ProductLike.objects.create(user=self.user2, product=self.popular_product)
        ProductLike.objects.create(user=self.user2, product=self.regional_product)

        # premium_user가 좋아요한 제품들
        ProductLike.objects.create(user=self.premium_user, product=self.limited_product)
        ProductLike.objects.create(user=self.premium_user, product=self.clear_wine_product)
        ProductLike.objects.create(user=self.premium_user, product=self.multi_feature_product)

    def setup_test_data(self):
        """모든 테스트 데이터 생성 (순서 중요)"""
        self.create_users()
        self.create_basic_data()
        self.create_taste_tags()
        self.create_products()
        self.create_product_taste_tags()
        self.create_product_likes()

        # 기존 테스트와의 호환성을 위한 별칭들
        self.brewery = self.brewery1  # 별칭 추가
        self.region = self.region_gg  # 별칭 추가


class ProductAPITestCase(ProductTestMixin, APITestCase):
    """제품 API 테스트 베이스 클래스"""

    def setUp(self):
        """공통 setUp"""
        self.client = APIClient()
        self.setup_test_data()

    def authenticate_admin(self):
        """관리자 인증"""
        self.client.force_authenticate(user=self.admin_user)

    def authenticate_user(self):
        """일반 사용자 인증"""
        self.client.force_authenticate(user=self.user)

    def logout(self):
        """로그아웃"""
        self.client.logout()


class ProductTestDataFactory:
    """테스트 데이터 팩토리 (선택적 사용)"""

    @staticmethod
    def create_simple_product(**kwargs):
        """간단한 제품 생성"""
        defaults = {
            "name": "Test Product",
            "description": "Test Description",
            "ingredients": "쌀, 누룩",
            "alcohol_content": 6.0,
            "volume_ml": 750,
            "price": Decimal("5000"),
            "status": "active",
        }
        defaults.update(kwargs)
        return Product.objects.create(**defaults)

    @staticmethod
    def create_product_with_tags(product, tags_data):
        """제품에 맛 태그 연결"""
        for tag_data in tags_data:
            ProductTasteTag.objects.create(
                product=product, taste_tag=tag_data["tag"], intensity=tag_data.get("intensity", 1.0)
            )
        return product
