# apps/products/tests/test_product_like_filter_api.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.products.models import AlcoholType, Product, ProductLike
from apps.products.tests.base import ProductAPITestCase

User = get_user_model()


class ProductLikeAPITestCase(ProductAPITestCase):
    """제품 좋아요 API TDD 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        super().setUp()

        # 좋아요하지 않은 제품을 대상으로 설정 (베이스에서 이미 좋아요한 제품 피하기)
        self.target_product = self.popular_product  # user가 좋아요하지 않은 제품
        self.like_url = reverse("product-like", kwargs={"pk": self.target_product.id})

    def test_like_product_success_authenticated_user(self):
        """인증된 사용자의 제품 좋아요 성공 테스트"""
        # Given: 인증된 사용자 및 좋아요하지 않은 제품 선택
        self.client.force_authenticate(user=self.user)

        # 베이스 클래스에서 이미 좋아요한 제품 말고 다른 제품 선택
        target_product = self.popular_product  # user가 좋아요하지 않은 제품
        like_url = reverse("product-like", kwargs={"pk": target_product.id})

        # 좋아요 전 상태 확인
        initial_like_count = target_product.like_count
        self.assertFalse(ProductLike.objects.filter(user=self.user, product=target_product).exists())

        # When: 좋아요 요청
        response = self.client.post(like_url)

        # Then: 성공적으로 좋아요
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 응답 데이터 검증
        self.assertIn("message", response.data)
        self.assertIn("liked", response.data)
        self.assertTrue(response.data["liked"])
        self.assertEqual(response.data["like_count"], initial_like_count + 1)

        # 데이터베이스 확인
        self.assertTrue(ProductLike.objects.filter(user=self.user, product=target_product).exists())

        # 제품의 좋아요 수 증가 확인
        target_product.refresh_from_db()
        self.assertEqual(target_product.like_count, initial_like_count + 1)

    def test_unlike_product_success_authenticated_user(self):
        """인증된 사용자의 제품 좋아요 취소 성공 테스트"""
        # Given: 이미 좋아요한 상태 (베이스 클래스에서 이미 설정됨)
        self.client.force_authenticate(user=self.user)

        # self.user가 이미 좋아요한 제품 사용
        target_product = self.product  # 베이스에서 이미 좋아요 설정됨
        like_url = reverse("product-like", kwargs={"pk": target_product.id})

        initial_like_count = target_product.like_count

        # 이미 좋아요한 상태인지 확인
        self.assertTrue(ProductLike.objects.filter(user=self.user, product=target_product).exists())

        # When: 좋아요 취소 요청 (같은 엔드포인트에 재요청)
        response = self.client.post(like_url)

        # Then: 성공적으로 좋아요 취소
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("message", response.data)
        self.assertIn("liked", response.data)
        self.assertFalse(response.data["liked"])
        self.assertEqual(response.data["like_count"], initial_like_count - 1)

        # 데이터베이스 확인
        self.assertFalse(ProductLike.objects.filter(user=self.user, product=target_product).exists())

    def test_like_product_unauthenticated_user(self):
        """비인증 사용자의 제품 좋아요 시 인증 오류"""
        # Given: 비인증 상태

        # When: 좋아요 요청
        response = self.client.post(self.like_url)

        # Then: 인증 오류 (DRF는 403을 반환)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_like_product_not_found(self):
        """존재하지 않는 제품 좋아요 시 404 오류"""
        # Given: 인증된 사용자 및 존재하지 않는 제품 ID
        self.client.force_authenticate(user=self.user)
        url = reverse("product-like", kwargs={"pk": "00000000-0000-0000-0000-000000000000"})

        # When: 존재하지 않는 제품 좋아요 요청
        response = self.client.post(url)

        # Then: 404 Not Found
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_like_product_duplicate_request_toggle(self):
        """중복 좋아요 요청 시 토글 동작 테스트"""
        # Given: 인증된 사용자 및 좋아요하지 않은 제품
        self.client.force_authenticate(user=self.user)

        # 좋아요하지 않은 제품 선택
        target_product = self.popular_product
        like_url = reverse("product-like", kwargs={"pk": target_product.id})

        # When: 첫 번째 좋아요 요청
        response1 = self.client.post(like_url)
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response1.data["liked"])

        # When: 두 번째 좋아요 요청 (취소)
        response2 = self.client.post(like_url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data["liked"])

        # When: 세 번째 좋아요 요청 (다시 좋아요)
        response3 = self.client.post(like_url)
        self.assertEqual(response3.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response3.data["liked"])


class ProductFilteringAPITestCase(ProductAPITestCase):
    """제품 필터링 API TDD 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        super().setUp()
        # 베이스 클래스에서 이미 다양한 제품들이 생성됨
        # 추가 데이터가 필요하면 여기서만 생성

    def test_get_popular_products_success(self):
        """인기 제품 목록 조회 성공 테스트"""
        # Given: URL 설정
        url = reverse("product-popular")

        # When: 인기 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("results", response.data)
        products = response.data["results"]

        # 디버깅: 처음 5개 제품의 정보 출력
        print(f"\n=== 인기 제품 정렬 디버깅 ===")
        for i, product in enumerate(products[:5]):
            print(
                f"{i + 1}. {product['name']}: order_count={product['order_count']}, view_count={product['view_count']}"
            )
        print("=" * 40)

        # 인기 제품이 있는지 확인
        self.assertGreater(len(products), 0)

        # 정렬 순서 확인 (단순화)
        if len(products) > 1:
            first_product = products[0]
            second_product = products[1]

            # 첫 번째 제품의 order_count가 두 번째보다 크거나 같아야 함
            self.assertGreaterEqual(
                first_product["order_count"],
                second_product["order_count"],
                f"정렬 오류: {first_product['name']}({first_product['order_count']}) vs {second_product['name']}({second_product['order_count']})",
            )

    def test_get_featured_products_success(self):
        """추천 제품 목록 조회 성공 테스트"""
        # Given: URL 설정
        url = reverse("product-featured")

        # When: 추천 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("results", response.data)
        products = response.data["results"]

        # 모든 제품이 is_featured=True인지 확인
        for product in products:
            self.assertTrue(product["is_featured"])

    def test_get_award_winning_products_success(self):
        """수상 제품 목록 조회 성공 테스트"""
        # Given: URL 설정
        url = reverse("product-award-winning")

        # When: 수상 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("results", response.data)
        products = response.data["results"]

        # 모든 제품이 is_award_winning=True인지 확인
        for product in products:
            self.assertTrue(product["is_award_winning"])

    def test_get_regional_specialty_products_success(self):
        """지역 특산물 제품 목록 조회 성공 테스트"""
        # Given: URL 설정
        url = reverse("product-regional-specialty")

        # When: 지역 특산물 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("results", response.data)
        products = response.data["results"]

        # 모든 제품이 is_regional_specialty=True인지 확인
        for product in products:
            self.assertTrue(product["is_regional_specialty"])

    def test_get_products_by_alcohol_type_success(self):
        """주류 타입별 제품 목록 조회 성공 테스트"""
        # Given: 주류 타입 파라미터와 함께 URL 설정
        url = reverse("product-by-type")

        # When: 특정 주류 타입으로 필터링 요청
        response = self.client.get(url, {"alcohol_type": self.alcohol_type.id})

        # Then: 성공적으로 조회
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("results", response.data)
        products = response.data["results"]

        # 모든 제품이 지정된 주류 타입인지 확인
        for product in products:
            self.assertEqual(product["alcohol_type"]["id"], self.alcohol_type.id)

    def test_get_products_by_invalid_alcohol_type(self):
        """존재하지 않는 주류 타입으로 조회 시 빈 결과 반환"""
        # Given: 존재하지 않는 주류 타입 ID
        url = reverse("product-by-type")

        # When: 존재하지 않는 주류 타입으로 요청
        response = self.client.get(url, {"alcohol_type": 99999})

        # Then: 성공적으로 조회되지만 빈 결과
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_filtering_with_pagination(self):
        """필터링과 페이지네이션 함께 동작 테스트"""
        # Given: 페이지 크기 설정
        url = reverse("product-popular")

        # When: 페이지네이션과 함께 요청
        response = self.client.get(url, {"page": 1, "page_size": 2})

        # Then: 성공적으로 조회 및 페이지네이션 동작
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 페이지네이션 정보 확인
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

        # 결과 수가 페이지 크기 이하인지 확인
        results_count = len(response.data["results"])
        self.assertLessEqual(results_count, 2)

    def test_multiple_filters_combination(self):
        """복합 필터 조건 테스트 (추천 + 수상)"""
        # Given: 추천이면서 수상 제품 생성
        featured_and_award_product = Product.objects.create(
            name="추천 수상 막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="추천 + 수상 제품",
            ingredients="쌀, 누룩",
            alcohol_content=6.0,
            volume_ml=750,
            price=15000,
            is_featured=True,
            is_award_winning=True,
            is_regional_specialty=False,
        )

        # When: 추천 제품 목록에서 수상 제품도 확인
        featured_url = reverse("product-featured")
        featured_response = self.client.get(featured_url)

        award_url = reverse("product-award-winning")
        award_response = self.client.get(award_url)

        # Then: 두 목록 모두에 포함되어야 함
        featured_names = [p["name"] for p in featured_response.data["results"]]
        award_names = [p["name"] for p in award_response.data["results"]]

        self.assertIn("추천 수상 막걸리", featured_names)
        self.assertIn("추천 수상 막걸리", award_names)


class ProductLikedFilterAPITestCase(ProductAPITestCase):
    """사용자가 좋아요한 제품 필터링 API TDD 테스트"""

    def setUp(self):
        """테스트 데이터 준비"""
        super().setUp()

        # 좋아요한 제품들 설정
        self.setup_liked_products()

    def setup_liked_products(self):
        """좋아요 테스트용 제품들 및 좋아요 관계 생성"""
        # 사용자가 좋아요할 제품들 생성
        self.liked_product1 = Product.objects.create(
            name="좋아요한 막걸리 1",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="첫 번째 좋아요한 제품",
            ingredients="쌀, 누룩",
            alcohol_content=6.0,
            volume_ml=750,
            price=8000,
        )

        self.liked_product2 = Product.objects.create(
            name="좋아요한 막걸리 2",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="두 번째 좋아요한 제품",
            ingredients="쌀, 누룩",
            alcohol_content=7.0,
            volume_ml=750,
            price=9000,
        )

        self.not_liked_product = Product.objects.create(
            name="좋아요하지 않은 막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="좋아요하지 않은 제품",
            ingredients="쌀, 누룩",
            alcohol_content=5.0,
            volume_ml=750,
            price=7000,
        )

        # 다른 사용자 생성
        self.other_user = User.objects.create(nickname="other_user", email="other@test.com", role=User.Role.USER)

        # self.user가 좋아요한 제품들
        ProductLike.objects.create(user=self.user, product=self.liked_product1)
        ProductLike.objects.create(user=self.user, product=self.liked_product2)

        # 다른 사용자가 좋아요한 제품 (self.user는 좋아요하지 않음)
        ProductLike.objects.create(user=self.other_user, product=self.not_liked_product)

    def test_get_liked_products_success_authenticated_user(self):
        """인증된 사용자의 좋아요한 제품 목록 조회 성공 테스트"""
        # Given: 인증된 사용자
        self.client.force_authenticate(user=self.user)
        url = reverse("product-liked")

        # When: 좋아요한 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답 데이터 검증
        self.assertIn("results", response.data)
        products = response.data["results"]

        # 좋아요한 제품들만 반환되는지 확인
        product_names = [p["name"] for p in products]
        self.assertIn("좋아요한 막걸리 1", product_names)
        self.assertIn("좋아요한 막걸리 2", product_names)
        self.assertNotIn("좋아요하지 않은 막걸리", product_names)

        # 정확히 5개의 제품만 반환되는지 확인
        self.assertEqual(len(products), 5)

        # 각 제품에 좋아요 상태 정보가 포함되어 있는지 확인
        for product in products:
            # 응답에 좋아요 여부나 관련 정보가 포함되어야 함
            self.assertIn("id", product)
            self.assertIn("name", product)

    def test_get_liked_products_unauthenticated_user(self):
        """비인증 사용자의 좋아요한 제품 목록 조회 시 인증 오류"""
        # Given: 비인증 상태
        url = reverse("product-liked")

        # When: 좋아요한 제품 목록 요청
        response = self.client.get(url)

        # Then: 인증 오류 (DRF는 403을 반환)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_liked_products_empty_list_no_likes(self):
        """좋아요한 제품이 없는 사용자의 빈 목록 반환 테스트"""
        # Given: 좋아요한 제품이 없는 새로운 사용자
        new_user = User.objects.create(nickname="new_user", email="new@test.com", role=User.Role.USER)
        self.client.force_authenticate(user=new_user)
        url = reverse("product-liked")

        # When: 좋아요한 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회되지만 빈 목록
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 0)

    def test_get_liked_products_with_pagination(self):
        """좋아요한 제품 목록의 페이지네이션 테스트"""
        # Given: 추가 좋아요 제품들 생성 (페이지네이션 테스트용)
        for i in range(3, 8):  # 5개 더 생성
            extra_product = Product.objects.create(
                name=f"추가 좋아요 막걸리 {i}",
                brewery=self.brewery1,
                alcohol_type=self.alcohol_type,
                description=f"추가 제품 {i}",
                ingredients="쌀, 누룩",
                alcohol_content=6.0,
                volume_ml=750,
                price=8000,
            )
            ProductLike.objects.create(user=self.user, product=extra_product)

        self.client.force_authenticate(user=self.user)
        url = reverse("product-liked")

        # When: 페이지 크기를 3으로 설정하여 요청
        response = self.client.get(url, {"page": 1, "page_size": 3})

        # Then: 페이지네이션이 올바르게 동작
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 페이지네이션 정보 확인
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)

        # 첫 페이지에 3개 항목이 있는지 확인
        self.assertEqual(len(response.data["results"]), 3)

        # 전체 좋아요 제품 수 확인 (기존 5개 + 새로 추가한 5개 = 7개)
        self.assertEqual(response.data["count"], 10)

    def test_get_liked_products_with_deleted_product(self):
        """좋아요한 제품이 삭제된 경우 처리 테스트"""
        # Given: 인증된 사용자 및 좋아요한 제품 중 하나 삭제
        self.client.force_authenticate(user=self.user)

        # 좋아요한 제품 중 하나 삭제
        deleted_product_id = self.liked_product1.id
        self.liked_product1.delete()

        url = reverse("product-liked")

        # When: 좋아요한 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회 (삭제된 제품은 제외)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 삭제된 제품은 목록에서 제외되어야 함
        product_names = [p["name"] for p in response.data["results"]]
        self.assertNotIn("좋아요한 막걸리 1", product_names)
        self.assertIn("좋아요한 막걸리 2", product_names)

        # 5-1 = 4개 제품만 반환되어야 함
        self.assertEqual(len(response.data["results"]), 4)

    def test_get_liked_products_ordered_by_recent(self):
        """좋아요한 제품들이 최신 좋아요 순으로 정렬되는지 테스트"""
        # Given: 인증된 사용자
        self.client.force_authenticate(user=self.user)

        # 새로운 제품에 나중에 좋아요 추가
        recent_product = Product.objects.create(
            name="최근 좋아요한 막걸리",
            brewery=self.brewery1,
            alcohol_type=self.alcohol_type,
            description="가장 최근에 좋아요한 제품",
            ingredients="쌀, 누룩",
            alcohol_content=6.0,
            volume_ml=750,
            price=8000,
        )
        ProductLike.objects.create(user=self.user, product=recent_product)

        url = reverse("product-liked")

        # When: 좋아요한 제품 목록 요청
        response = self.client.get(url)

        # Then: 성공적으로 조회 및 최신 순 정렬
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        products = response.data["results"]
        self.assertGreater(len(products), 0)

        # 첫 번째 제품이 가장 최근에 좋아요한 제품인지 확인
        first_product = products[0]
        self.assertEqual(first_product["name"], "최근 좋아요한 막걸리")

    def test_get_liked_products_different_users_isolation(self):
        """다른 사용자들의 좋아요 목록이 분리되어 조회되는지 테스트"""
        # Given: 두 명의 다른 사용자
        user1 = self.user
        user2 = self.other_user

        # User1으로 좋아요 목록 조회
        self.client.force_authenticate(user=user1)
        url = reverse("product-liked")
        response1 = self.client.get(url)

        # User2로 좋아요 목록 조회
        self.client.force_authenticate(user=user2)
        response2 = self.client.get(url)

        # Then: 각 사용자마다 다른 좋아요 목록 반환
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        user1_products = [p["name"] for p in response1.data["results"]]
        user2_products = [p["name"] for p in response2.data["results"]]

        # User1의 좋아요 목록 확인
        self.assertIn("좋아요한 막걸리 1", user1_products)
        self.assertIn("좋아요한 막걸리 2", user1_products)
        self.assertNotIn("좋아요하지 않은 막걸리", user1_products)

        # User2의 좋아요 목록 확인
        self.assertNotIn("좋아요한 막걸리 1", user2_products)
        self.assertNotIn("좋아요한 막걸리 2", user2_products)
        self.assertIn("좋아요하지 않은 막걸리", user2_products)
