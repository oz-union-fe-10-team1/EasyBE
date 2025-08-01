# apps/products/tests/test_product_update_delete_api.py

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.products.models import Product, ProductTasteTag, TasteTag
from apps.products.tests.base import ProductAPITestCase

User = get_user_model()


class ProductUpdateAPITestCase(ProductAPITestCase):
    """제품 수정 API TDD 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        super().setUp()

        # 수정할 제품 (베이스 클래스의 첫 번째 제품 사용)
        self.product_to_update = self.product
        self.url = reverse("product-detail", kwargs={"pk": self.product_to_update.id})

        # 수정용 데이터 (모든 필수 필드 포함)
        self.update_data = {
            "name": "수정된 장수 생막걸리",
            "brewery": self.brewery1.id,  # 필수 필드
            "alcohol_type": self.alcohol_type.id,  # 필수 필드
            "region": self.region_gg.id,  # 선택 필드
            "category": self.category.id,  # 선택 필드
            "description": "수정된 설명입니다.",  # 필수 필드
            "ingredients": "쌀, 누룩, 정제수",  # 필수 필드
            "alcohol_content": 6.5,  # 필수 필드
            "volume_ml": 750,  # 필수 필드
            "price": "9500",  # 필수 필드
            "original_price": "12000",
            "stock_quantity": 150,
            "min_stock_alert": 10,
            # 맛 프로필 수정
            "sweetness_level": 3.0,
            "acidity_level": 3.5,
            "body_level": 4.0,
            "carbonation_level": 2.0,
            "bitterness_level": 2.5,
            "aroma_level": 3.5,
            # 제품 특성 수정
            "is_gift_suitable": False,
            "is_premium": True,
            "flavor_notes": "수정된 맛 노트",
            "short_description": "수정된 짧은 설명",
            "package_name": "수정된 패키지명",
            "status": "active",
        }

    def test_update_product_full_success_with_admin(self):
        """관리자 권한으로 제품 전체 수정 성공 테스트 (PUT)"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # 수정 전 값 확인
        original_name = self.product_to_update.name

        # When: 전체 수정 요청 (PUT)
        response = self.client.put(self.url, self.update_data, format="json")

        # 디버깅: 400 오류 시 상세 정보 출력
        if response.status_code == status.HTTP_400_BAD_REQUEST:
            print(f"\n=== 디버깅 정보 ===")
            print(f"URL: {self.url}")
            print(f"Request Data: {self.update_data}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Data: {response.data}")
            print(f"=================\n")

        # Then: 성공적으로 수정
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertEqual(response.data["name"], "수정된 장수 생막걸리")
        self.assertEqual(float(response.data["price"]), 9500.0)
        self.assertEqual(response.data["sweetness_level"], 3.0)

        # 데이터베이스 확인
        self.product_to_update.refresh_from_db()
        self.assertEqual(self.product_to_update.name, "수정된 장수 생막걸리")
        self.assertEqual(self.product_to_update.price, Decimal("9500"))
        self.assertNotEqual(self.product_to_update.name, original_name)

    def test_update_product_partial_success_with_admin(self):
        """관리자 권한으로 제품 부분 수정 성공 테스트 (PATCH)"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # 부분 수정 데이터 (일부 필드만)
        partial_data = {"name": "부분 수정된 이름", "price": "7500", "sweetness_level": 4.5}

        # 수정 전 다른 필드 값들 저장
        original_description = self.product_to_update.description
        original_stock = self.product_to_update.stock_quantity

        # When: 부분 수정 요청 (PATCH)
        response = self.client.patch(self.url, partial_data, format="json")

        # Then: 성공적으로 부분 수정
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 수정된 필드 확인
        self.assertEqual(response.data["name"], "부분 수정된 이름")
        self.assertEqual(float(response.data["price"]), 7500.0)
        self.assertEqual(response.data["sweetness_level"], 4.5)

        # 수정되지 않은 필드들은 그대로 유지
        self.product_to_update.refresh_from_db()
        self.assertEqual(self.product_to_update.description, original_description)
        self.assertEqual(self.product_to_update.stock_quantity, original_stock)

    def test_update_product_unauthorized_without_login(self):
        """로그인하지 않은 상태에서 제품 수정 시 인증 오류"""
        # Given: 로그인하지 않은 상태

        # When: 제품 수정 요청
        response = self.client.put(self.url, self.update_data, format="json")

        # Then: 인증 오류 반환
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 데이터베이스는 변경되지 않음
        self.product_to_update.refresh_from_db()
        self.assertNotEqual(self.product_to_update.name, "수정된 장수 생막걸리")

    def test_update_product_forbidden_with_normal_user(self):
        """일반 사용자 권한으로 제품 수정 시 권한 오류"""
        # Given: 일반 사용자로 로그인
        self.client.force_authenticate(user=self.user)

        # When: 제품 수정 요청
        response = self.client.put(self.url, self.update_data, format="json")

        # Then: 권한 오류 반환
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 데이터베이스는 변경되지 않음
        self.product_to_update.refresh_from_db()
        self.assertNotEqual(self.product_to_update.name, "수정된 장수 생막걸리")

    def test_update_product_invalid_data(self):
        """잘못된 데이터로 제품 수정 시 유효성 검사 오류"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # 잘못된 데이터
        invalid_data = {
            "name": "",  # 빈 이름
            "price": "-1000",  # 음수 가격
            "alcohol_content": 150.0,  # 범위 초과
            "sweetness_level": 10.0,  # 범위 초과
        }

        # When: 잘못된 데이터로 수정 요청
        response = self.client.patch(self.url, invalid_data, format="json")

        # Then: 유효성 검사 오류 반환
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", response.data)
        self.assertIn("alcohol_content", response.data)
        self.assertIn("sweetness_level", response.data)

    def test_update_product_not_found(self):
        """존재하지 않는 제품 수정 시 404 오류"""
        # Given: 관리자로 로그인 및 존재하지 않는 제품 ID
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("product-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"})

        # When: 존재하지 않는 제품 수정 요청
        response = self.client.put(url, self.update_data, format="json")

        # Then: 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_product_with_taste_tags(self):
        """맛 태그와 함께 제품 수정 테스트"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # 기존 맛 태그 수 확인
        original_tags_count = self.product_to_update.taste_tags.count()

        # 새로운 맛 태그 데이터
        update_data_with_tags = self.update_data.copy()
        update_data_with_tags["taste_tags"] = [
            {"taste_tag": self.rich_tag.id, "intensity": 4.0},
        ]

        # When: 맛 태그와 함께 수정 요청
        response = self.client.put(self.url, update_data_with_tags, format="json")

        # Then: 성공적으로 수정
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 맛 태그 관계 확인
        self.product_to_update.refresh_from_db()
        updated_tags_count = self.product_to_update.taste_tags.count()

        # 새로운 태그 관계가 생성되었는지 확인
        rich_relation = self.product_to_update.producttastetag_set.filter(taste_tag=self.rich_tag).first()
        self.assertIsNotNone(rich_relation)
        self.assertEqual(rich_relation.intensity, 4.0)

    def test_update_product_response_format(self):
        """제품 수정 후 응답 형식 검증"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)

        # When: 제품 수정 요청
        response = self.client.put(self.url, self.update_data, format="json")

        # Then: 올바른 응답 형식
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 필수 응답 필드 검증 (DetailSerializer 형식)
        required_fields = [
            "id",
            "name",
            "brewery",
            "alcohol_type",
            "description",
            "price",
            "original_price",
            "discount_rate",
            "stock_quantity",
            "sweetness_level",
            "acidity_level",
            "body_level",
            "is_available",
            "updated_at",
        ]

        for field in required_fields:
            self.assertIn(field, response.data, f"응답에 {field} 필드가 없습니다")

        # updated_at 필드가 갱신되었는지 확인
        self.assertIsNotNone(response.data["updated_at"])


class ProductDeleteAPITestCase(ProductAPITestCase):
    """제품 삭제 API TDD 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        super().setUp()

        # 삭제할 제품 (베이스 클래스의 두 번째 제품 사용)
        self.product_to_delete = self.product2
        self.url = reverse("product-detail", kwargs={"pk": self.product_to_delete.id})

    def test_delete_product_success_with_admin(self):
        """관리자 권한으로 제품 삭제 성공 테스트"""
        # Given: 관리자로 로그인 및 초기 제품 수 확인
        self.client.force_authenticate(user=self.admin_user)
        initial_count = Product.objects.count()

        # When: 제품 삭제 요청
        response = self.client.delete(self.url)

        # Then: 성공적으로 삭제
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 데이터베이스에서 제품이 삭제되었는지 확인
        self.assertEqual(Product.objects.count(), initial_count - 1)

        # 해당 제품이 실제로 삭제되었는지 확인
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=self.product_to_delete.id)

    def test_delete_product_unauthorized_without_login(self):
        """로그인하지 않은 상태에서 제품 삭제 시 인증 오류"""
        # Given: 로그인하지 않은 상태 및 초기 제품 수 확인
        initial_count = Product.objects.count()

        # When: 제품 삭제 요청
        response = self.client.delete(self.url)

        # Then: 인증 오류 반환
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # 제품이 삭제되지 않았는지 확인
        self.assertEqual(Product.objects.count(), initial_count)
        self.assertTrue(Product.objects.filter(id=self.product_to_delete.id).exists())

    def test_delete_product_forbidden_with_normal_user(self):
        """일반 사용자 권한으로 제품 삭제 시 권한 오류"""
        # Given: 일반 사용자로 로그인 및 초기 제품 수 확인
        self.client.force_authenticate(user=self.user)
        initial_count = Product.objects.count()

        # When: 제품 삭제 요청
        response = self.client.delete(self.url)

        # Then: 권한 오류 반환
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # 제품이 삭제되지 않았는지 확인
        self.assertEqual(Product.objects.count(), initial_count)
        self.assertTrue(Product.objects.filter(id=self.product_to_delete.id).exists())

    def test_delete_product_not_found(self):
        """존재하지 않는 제품 삭제 시 404 오류"""
        # Given: 관리자로 로그인 및 존재하지 않는 제품 ID
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("product-detail", kwargs={"pk": "00000000-0000-0000-0000-000000000000"})

        # When: 존재하지 않는 제품 삭제 요청
        response = self.client.delete(url)

        # Then: 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_product_with_related_data(self):
        """관련 데이터가 있는 제품 삭제 테스트"""
        # Given: 관리자로 로그인 및 맛 태그 관계가 있는 제품
        self.client.force_authenticate(user=self.admin_user)

        # 제품에 맛 태그 관계 추가
        ProductTasteTag.objects.create(product=self.product_to_delete, taste_tag=self.sweet_tag, intensity=3.0)

        # 관련 데이터 수 확인
        initial_taste_tag_relations = ProductTasteTag.objects.filter(product=self.product_to_delete).count()
        self.assertGreater(initial_taste_tag_relations, 0)

        # When: 제품 삭제 요청
        response = self.client.delete(self.url)

        # Then: 성공적으로 삭제
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 제품과 관련 데이터가 함께 삭제되었는지 확인 (CASCADE)
        with self.assertRaises(Product.DoesNotExist):
            Product.objects.get(id=self.product_to_delete.id)

        # 관련 맛 태그 관계도 삭제되었는지 확인
        remaining_relations = ProductTasteTag.objects.filter(product=self.product_to_delete).count()
        self.assertEqual(remaining_relations, 0)

    def test_delete_product_soft_delete_option(self):
        """소프트 삭제 옵션 테스트 (비즈니스 요구사항에 따라)"""
        # Given: 관리자로 로그인
        self.client.force_authenticate(user=self.admin_user)
        initial_count = Product.objects.count()

        # When: 제품 삭제 요청
        response = self.client.delete(self.url)

        # Then: 소프트 삭제 구현 시
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 하드 삭제 vs 소프트 삭제 선택
        # 옵션 1: 하드 삭제 (현재 테스트)
        self.assertEqual(Product.objects.count(), initial_count - 1)

        # 옵션 2: 소프트 삭제 (주석 처리 - 필요시 구현)
        # self.assertEqual(Product.objects.count(), initial_count)  # 수량 유지
        # self.product_to_delete.refresh_from_db()
        # self.assertEqual(self.product_to_delete.status, 'deleted')  # 상태만 변경

    def test_delete_multiple_products_batch(self):
        """다중 제품 삭제 테스트 (확장 기능)"""
        # 이 테스트는 다중 삭제 API가 구현된 경우에만 활성화
        self.skipTest("다중 삭제 기능은 추후 구현 예정")

        # Given: 관리자로 로그인 및 여러 제품 ID
        # self.client.force_authenticate(user=self.admin_user)
        # product_ids = [self.product.id, self.product2.id]

        # When: 다중 삭제 요청 (커스텀 액션)
        # response = self.client.post('/api/products/batch_delete/',
        #                           {'ids': product_ids}, format='json')

        # Then: 성공적으로 다중 삭제
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
