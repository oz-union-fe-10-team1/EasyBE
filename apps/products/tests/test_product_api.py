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

        # 관리자 사용자 생성
        self.admin_user = User.objects.create_user(
            username="admin", email="admin@example.com", password="admin123", is_staff=True, is_superuser=True
        )

        # 일반 사용자 생성
        self.normal_user = User.objects.create_user(username="user", email="user@example.com", password="user123")

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
            "sweetness_level": 3.5,
            "sourness_level": 2.0,
            "bitterness_level": 1.0,
            "umami_level": 2.5,
            "alcohol_strength": 2.0,
            "body_level": 3.0,
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
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
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
                "sweetness_level": 6.0,  # 5.0 초과
                "sourness_level": -1.0,  # 0.0 미만
            }
        )
        response = self.client.post(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("sweetness_level", response.data)
        self.assertIn("sourness_level", response.data)
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

        # 필수 응답 필드 검증
        required_fields = [
            "id",
            "name",
            "brewery",
            "alcohol_type",
            "price",
            "alcohol_content",
            "volume_ml",
            "description",
            "sweetness_level",
            "sourness_level",
            "bitterness_level",
            "is_available",
            "discount_rate",
            "main_image_url",
            "taste_profile_vector",
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
        self.assertEqual(response.data["discount_rate"], 20)  # (10000-8000)/10000*100
