# apps/products/tests/test_product_create_api.py

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.products.models import (
    AlcoholType,
    Brewery,
    Product,
    ProductCategory,
    Region,
    TasteTag,
)

User = get_user_model()


class ProductCreateAPITestCase(APITestCase):
    """제품 생성 API TDD 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        # API 클라이언트
        self.client = APIClient()

        # 관리자 사용자
        self.admin_user = User.objects.create(nickname="admin_test", email="admin@example.com", role=User.Role.ADMIN)

        # 일반 사용자
        self.normal_user = User.objects.create(nickname="normal_test", email="normal@example.com", role=User.Role.USER)

        # 기본 데이터 생성
        self.region = Region.objects.create(name="경기", code="GG", description="경기도 지역")

        self.alcohol_type = AlcoholType.objects.create(
            name="생막걸리", category="rice_wine", description="살아있는 효모 막걸리"
        )

        self.category = ProductCategory.objects.create(
            name="생막걸리", slug="fresh-makgeolli", description="신선한 생막걸리"
        )

        self.brewery = Brewery.objects.create(
            name="장수막걸리", region=self.region, address="경기도 포천시", phone="031-123-4567"
        )

        # API 엔드포인트
        self.url = reverse("product-list")  # DRF router URL
        # 또는 수동 URL: self.url = '/api/products/'

        # 유효한 제품 데이터
        self.valid_product_data = {
            "name": "장수 생막걸리",
            "brewery": self.brewery.id,
            "alcohol_type": self.alcohol_type.id,
            "region": self.region.id,
            "category": self.category.id,
            "description": "부드럽고 달콤한 생막걸리입니다.",
            "ingredients": "쌀, 누룩, 정제수",
            "alcohol_content": 6.0,
            "volume_ml": 750,
            "price": "8000",
            "original_price": "10000",
            "stock_quantity": 100,
            "min_stock_alert": 10,
            # 맛 프로필
            "sweetness_level": 3.5,
            "acidity_level": 2.0,
            "body_level": 3.0,
            "carbonation_level": 1.0,
            "bitterness_level": 1.0,
            "aroma_level": 4.0,
            "is_gift_suitable": True,
            "is_award_winning": False,
            "is_regional_specialty": True,
            "flavor_notes": "복숭아향, 달콤함",
            "short_description": "부드럽고 달콤한 생막걸리",
            "package_name": "장수 생막걸리 750ml",
            "is_limited_edition": False,
            "is_premium": False,
            "is_organic": True,
            "status": "active",
            "is_featured": False,
        }

    def test_create_product_success_with_admin(self):
        """관리자 권한으로 제품 생성 성공 테스트"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 유효한 데이터로 제품 생성 요청
        response = self.client.post(self.url, self.valid_product_data, format="json")

        # Then: 성공적으로 생성되어야 함
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 응답 데이터 검증
        self.assertEqual(response.data["name"], "장수 생막걸리")
        self.assertEqual(response.data["brewery"]["id"], self.brewery.id)
        self.assertEqual(response.data["brewery"]["name"], self.brewery.name)
        self.assertEqual(float(response.data["price"]), 8000.0)
        self.assertEqual(response.data["alcohol_content"], 6.0)
        self.assertTrue("id" in response.data)  # UUID 생성 확인

        # 데이터베이스에 실제로 저장되었는지 확인
        self.assertEqual(Product.objects.count(), 1)
        created_product = Product.objects.first()
        self.assertEqual(created_product.name, "장수 생막걸리")
        self.assertEqual(created_product.brewery, self.brewery)

    def test_create_product_unauthorized_without_login(self):
        """로그인하지 않은 상태에서 제품 생성 시 인증 오류"""
        # Given: 로그인하지 않은 상태

        # When: 제품 생성 요청
        response = self.client.post(self.url, self.valid_product_data, format="json")

        # Then: 인증 오류 반환
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_forbidden_with_normal_user(self):
        """일반 사용자 권한으로 제품 생성 시 권한 오류"""
        # Given: 일반 사용자로 로그인
        self.client.force_authenticate(user=self.normal_user)

        # When: 제품 생성 요청
        response = self.client.post(self.url, self.valid_product_data, format="json")

        # Then: 권한 오류 반환
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_missing_required_fields(self):
        """필수 필드 누락 시 유효성 검사 오류"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 필수 필드가 누락된 데이터로 요청
        invalid_data = {
            "name": "테스트 제품",
            # brewery, alcohol_type, description 등 필수 필드 누락
            "price": "5000",
        }
        response = self.client.post(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("brewery", response.data)
        self.assertIn("alcohol_type", response.data)
        self.assertIn("description", response.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_invalid_taste_levels(self):
        """맛 프로필 범위 초과 시 유효성 검사 오류"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 맛 프로필이 범위를 벗어난 데이터로 요청
        invalid_data = self.valid_product_data.copy()
        invalid_data.update(
            {
                "sweetness_level": 6.0,
                "acidity_level": -1.0,
                "bitterness_level": 10.0,
                "carbonation_level": -2.0,
                "aroma_level": 7.0,
            }
        )
        response = self.client.post(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sweetness_level", response.data)
        self.assertIn("acidity_level", response.data)
        self.assertIn("bitterness_level", response.data)
        self.assertIn("carbonation_level", response.data)
        self.assertIn("aroma_level", response.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_invalid_alcohol_content(self):
        """알코올 도수 범위 초과 시 유효성 검사 오류"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 알코올 도수가 범위를 벗어난 데이터로 요청
        invalid_data = self.valid_product_data.copy()
        invalid_data["alcohol_content"] = 150.0  # 100.0 초과
        response = self.client.post(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("alcohol_content", response.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_negative_price(self):
        """음수 가격 시 유효성 검사 오류"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 음수 가격으로 요청
        invalid_data = self.valid_product_data.copy()
        invalid_data["price"] = "-1000"
        response = self.client.post(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_nonexistent_brewery(self):
        """존재하지 않는 양조장 ID로 요청 시 오류"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 존재하지 않는 양조장 ID로 요청
        invalid_data = self.valid_product_data.copy()
        invalid_data["brewery"] = 99999  # 존재하지 않는 ID
        response = self.client.post(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("brewery", response.data)
        self.assertEqual(Product.objects.count(), 0)

    def test_create_product_with_optional_fields_null(self):
        """선택적 필드가 null인 경우 성공적으로 생성"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 선택적 필드를 null로 설정하여 요청
        minimal_data = {
            "name": "최소 데이터 제품",
            "brewery": self.brewery.id,
            "alcohol_type": self.alcohol_type.id,
            "description": "최소한의 데이터로 생성된 제품",
            "ingredients": "쌀, 누룩, 물",
            "alcohol_content": 6.0,
            "volume_ml": 750,
            "price": "5000",
            # region, category, original_price 등은 생략 (null 허용)
        }
        response = self.client.post(self.url, minimal_data, format="json")

        # Then: 성공적으로 생성되어야 함
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

        created_product = Product.objects.first()
        self.assertIsNone(created_product.region)
        self.assertIsNone(created_product.category)
        self.assertIsNone(created_product.original_price)

    def test_create_product_response_format(self):
        """제품 생성 후 응답 형식 검증"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 제품 생성 요청
        response = self.client.post(self.url, self.valid_product_data, format="json")

        # Then: 올바른 응답 형식이어야 함
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 필수 응답 필드 검증 (업데이트됨)
        required_fields = [
            "id",
            "name",
            "brewery",
            "alcohol_type",
            "price",
            "alcohol_content",
            "volume_ml",
            "description",
            # 맛 프로필 필드 (새로운 구조)
            "sweetness_level",  # 단맛
            "acidity_level",  # 산미
            "body_level",  # 바디감
            "carbonation_level",  # 탄산감
            "bitterness_level",  # 쓴맛:누룩맛
            "aroma_level",  # 향
            "is_available",
            "discount_rate",
            "main_image_url",
            "similarity_vector",
            "created_at",
            "updated_at",
        ]

        for field in required_fields:
            self.assertIn(field, response.data, f"응답에 {field} 필드가 없습니다")

        # 중첩 객체 검증
        self.assertIn("id", response.data["brewery"])
        self.assertIn("name", response.data["brewery"])
        self.assertIn("id", response.data["alcohol_type"])
        self.assertIn("name", response.data["alcohol_type"])

        # Property 필드 검증
        self.assertTrue(response.data["is_available"])
        self.assertEqual(response.data["discount_rate"], 20)
        self.assertEqual(response.data["main_image_url"], "")

        # 맛 프로필 값 검증 (새로운 구조)
        self.assertEqual(response.data["sweetness_level"], 3.5)
        self.assertEqual(response.data["acidity_level"], 2.0)
        self.assertEqual(response.data["body_level"], 3.0)
        self.assertEqual(response.data["carbonation_level"], 1.0)
        self.assertEqual(response.data["bitterness_level"], 1.0)
        self.assertEqual(response.data["aroma_level"], 4.0)

    def test_create_product_with_taste_tags(self):
        """맛 태그와 함께 제품 생성 테스트"""
        # Given: 맛 태그 생성
        sweet_tag = TasteTag.objects.create(name="달콤한", category="sweetness", color_code="#FF6B9D")
        fresh_tag = TasteTag.objects.create(name="상큼한", category="freshness", color_code="#4ECDC4")

        # 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 맛 태그 데이터와 함께 제품 생성 요청
        product_data_with_tags = self.valid_product_data.copy()
        product_data_with_tags["taste_tags"] = [
            {"taste_tag": sweet_tag.id, "intensity": 2.5},
            {"taste_tag": fresh_tag.id, "intensity": 1.8},
        ]

        response = self.client.post(self.url, product_data_with_tags, format="json")

        # Then: 성공적으로 생성되고 맛 태그도 연결되어야 함
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_product = Product.objects.first()
        self.assertEqual(created_product.taste_tags.count(), 2)

        # 맛 태그 관계 검증
        sweet_relation = created_product.producttastetag_set.get(taste_tag=sweet_tag)
        self.assertEqual(sweet_relation.intensity, 2.5)

    def test_create_product_duplicate_name_same_brewery(self):
        """같은 양조장에 동일한 이름의 제품 생성 시 처리"""
        # Given: 관리자로 로그인 및 기존 제품 생성
        self.client.force_authenticate(user=self.admin_user)
        Product.objects.create(
            name="장수 생막걸리",
            brewery=self.brewery,
            alcohol_type=self.alcohol_type,
            description="기존 제품",
            ingredients="쌀, 누룩, 물",
            alcohol_content=6.0,
            volume_ml=750,
            price=Decimal("5000"),
        )

        # When: 동일한 이름으로 새 제품 생성 시도
        response = self.client.post(self.url, self.valid_product_data, format="json")

        # Then: 중복 검사 로직에 따라 처리
        # 옵션 1: 중복 허용 (동일 제품의 다른 버전)
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 옵션 2: 중복 금지 (비즈니스 요구사항에 따라)
        # self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # self.assertIn('name', response.data)

        # 현재는 중복 허용으로 가정
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)


class ProductCreateViewTestCase(TestCase):
    """ProductCreate View 단위 테스트 (뷰 로직 검증)"""

    def setUp(self):
        self.admin_user = User.objects.create(nickname="admin_test", role=User.Role.ADMIN)

    def test_get_queryset_admin_only(self):
        """관리자와 일반 사용자의 쿼리셋 차이 확인"""
        from django.test import RequestFactory

        from apps.products.models import AlcoholType, Brewery, Product, Region
        from apps.products.views.product import ProductViewSet

        # 기본 데이터 생성
        region = Region.objects.create(name="경기", code="GG")
        alcohol_type = AlcoholType.objects.create(name="생막걸리", category="rice_wine")
        brewery = Brewery.objects.create(name="테스트양조장", region=region)

        # 활성/비활성 제품 생성
        active_product = Product.objects.create(
            name="활성제품",
            brewery=brewery,
            alcohol_type=alcohol_type,
            description="활성",
            ingredients="쌀",
            alcohol_content=6.0,
            volume_ml=750,
            price=5000,
            status="active",
        )
        inactive_product = Product.objects.create(
            name="비활성제품",
            brewery=brewery,
            alcohol_type=alcohol_type,
            description="비활성",
            ingredients="쌀",
            alcohol_content=6.0,
            volume_ml=750,
            price=5000,
            status="discontinued",
        )

        factory = RequestFactory()

        # 관리자 요청
        admin_request = factory.get("/api/products/")
        admin_request.user = self.admin_user
        admin_view = ProductViewSet()
        admin_view.request = admin_request
        admin_queryset = admin_view.get_queryset()

        # 일반 사용자 생성 및 요청
        normal_user = User.objects.create(nickname="normal_test", role=User.Role.USER)
        user_request = factory.get("/api/products/")
        user_request.user = normal_user
        user_view = ProductViewSet()
        user_view.request = user_request
        user_queryset = user_view.get_queryset()

        # 검증
        self.assertEqual(admin_queryset.count(), 2)  # 관리자는 모든 제품
        self.assertEqual(user_queryset.count(), 1)  # 일반 사용자는 활성 제품만

    def test_perform_create_sets_defaults(self):
        """제품 생성 시 기본값 설정 확인"""
        from django.test import RequestFactory

        from apps.products.models import AlcoholType, Brewery, Product, Region
        from apps.products.serializers import ProductCreateSerializer
        from apps.products.views.product import ProductViewSet

        # 기본 데이터 생성
        region = Region.objects.create(name="경기", code="GG")
        alcohol_type = AlcoholType.objects.create(name="생막걸리", category="rice_wine")
        brewery = Brewery.objects.create(name="테스트양조장", region=region)

        product_data = {
            "name": "기본값테스트제품",
            "brewery": brewery.id,
            "alcohol_type": alcohol_type.id,
            "description": "기본값 테스트",
            "ingredients": "쌀, 누룩",
            "alcohol_content": 6.0,
            "volume_ml": 750,
            "price": "8000",
        }

        # ViewSet 테스트
        factory = RequestFactory()
        request = factory.post("/api/products/", product_data)
        request.user = self.admin_user

        view = ProductViewSet()
        view.request = request
        view.format_kwarg = None

        serializer = ProductCreateSerializer(data=product_data)
        self.assertTrue(serializer.is_valid())
        view.perform_create(serializer)

        # 생성된 제품의 기본값 확인
        created_product = Product.objects.get(name="기본값테스트제품")
        self.assertEqual(created_product.stock_quantity, 0)  # 기본값
        self.assertEqual(created_product.status, "active")  # 기본값
        self.assertEqual(created_product.sweetness_level, 0.0)  # 기본값
        self.assertEqual(created_product.acidity_level, 0.0)  # 기본값
        self.assertEqual(created_product.carbonation_level, 0.0)  # 기본값
        self.assertEqual(created_product.aroma_level, 0.0)  # 기본값


# =============================================================================
# TDD 개발 순서 가이드
# =============================================================================

"""
🔥 TDD 개발 순서:

1. ✅ 위 테스트 코드 작성 완료!
2. ❌ 테스트 실행 → 당연히 실패 (아직 뷰/시리얼라이저 없음)
3. 🔧 최소한의 코드로 테스트 통과시키기:
   - ProductSerializer 생성
   - ProductViewSet 생성  
   - URL 연결
4. ♻️ 리팩토링
5. 🔄 반복

다음 단계:
- python manage.py test apps.products.tests.test_product_create_api
- 실패 확인 후 serializers.py, views.py 구현 시작!
"""
