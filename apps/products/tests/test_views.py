# apps/products/tests/test_views.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .test_helpers import TestDataCreator

User = get_user_model()


class BaseAPITestCase(APITestCase):
    """API 테스트 기본 클래스"""

    def setUp(self):
        self.test_data = TestDataCreator.create_full_dataset()
        self.breweries = self.test_data["breweries"]
        self.drinks = self.test_data["drinks"]
        self.packages = self.test_data["packages"]
        self.individual_products = self.test_data["individual_products"]
        self.package_products = self.test_data["package_products"]
        self.all_products = self.test_data["all_products"]

    def tearDown(self):
        TestDataCreator.clean_all_data()


class BreweryAPITest(BaseAPITestCase):
    """양조장 API 테스트"""

    def test_brewery_list_api(self):
        """양조장 목록 API 테스트"""
        url = reverse("products:v1:breweries-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)

        first_brewery = response.data["results"][0]
        expected_fields = {"id", "name", "region", "image_url", "product_count"}
        self.assertEqual(set(first_brewery.keys()), expected_fields)

    def test_brewery_detail_api(self):
        """양조장 상세 API 테스트"""
        brewery = self.breweries[0]
        url = reverse("products:v1:breweries-detail", kwargs={"pk": brewery.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["name"], "우리술양조장")
        self.assertEqual(data["phone"], "031-123-4567")
        self.assertEqual(data["region"], "경기")
        self.assertIn("description", data)
        self.assertIn("address", data)
        self.assertIn("drink_count", data)


class ProductSearchAPITest(BaseAPITestCase):
    """상품 검색 API 테스트"""

    def test_product_search_basic(self):
        """기본 상품 검색 API 테스트"""
        url = reverse("products:v1:products-search")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

        results = response.data["results"]
        self.assertEqual(len(results), 8)

        # 응답 필드 확인
        first_product = results[0]
        expected_fields = {
            "id",
            "name",
            "product_type",
            "price",
            "original_price",
            "discount",
            "discount_rate",
            "final_price",
            "is_on_sale",
            "main_image_url",
            "brewery_name",
            "alcohol_type",
            "is_gift_suitable",
            "is_regional_specialty",
            "is_limited_edition",
            "is_premium",
            "is_award_winning",
            "view_count",
            "like_count",
            "status",
            "created_at",
        }
        self.assertTrue(expected_fields.issubset(set(first_product.keys())))

    def test_product_search_with_keyword(self):
        """키워드 검색 테스트"""
        url = reverse("products:v1:products-search")
        response = self.client.get(url, {"search": "막걸리"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 검색 결과가 있으면 막걸리가 포함되어야 함
        results = response.data["results"]
        if results:
            found = any("막걸리" in product["name"] for product in results)
            self.assertTrue(found)

    def test_product_search_ordering(self):
        """상품 정렬 테스트"""
        url = reverse("products:v1:products-search")

        # 가격 오름차순 정렬
        response = self.client.get(url, {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        prices = [product["price"] for product in results]
        self.assertEqual(prices, sorted(prices))

    def test_product_category_filters(self):
        """카테고리 필터 테스트"""
        url = reverse("products:v1:products-search")

        # 프리미엄 상품 설정
        self.all_products[0].is_premium = True
        self.all_products[0].save()

        response = self.client.get(url, {"premium": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        if results:
            for product in results:
                self.assertTrue(product["is_premium"])

    def test_product_taste_profile_filters(self):
        """맛 프로필 필터 테스트"""
        url = reverse("products:v1:products-search")

        response = self.client.get(
            url,
            {
                "sweetness": 3.0,
                "acidity": 2.0,
                "body": 4.0,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 필터가 정상 작동하는지만 확인 (HTTP 200)


class ProductDetailAPITest(BaseAPITestCase):
    """상품 상세 조회 API 테스트"""

    def test_individual_product_detail(self):
        """개별 상품 상세 조회 테스트"""
        product = self.individual_products[0]
        url = reverse("products:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["product_type"], "individual")
        self.assertIsNotNone(data["drink"])
        self.assertIsNone(data["package"])

    def test_package_product_detail(self):
        """패키지 상품 상세 조회 테스트"""
        product = self.package_products[0]
        url = reverse("products:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["product_type"], "package")
        self.assertIsNone(data["drink"])
        self.assertIsNotNone(data["package"])

    def test_product_detail_view_count_increment(self):
        """상품 상세 조회 시 조회수 증가 확인"""
        product = self.individual_products[0]
        initial_view_count = product.view_count

        url = reverse("products:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회수가 증가했는지 확인
        product.refresh_from_db()
        self.assertEqual(product.view_count, initial_view_count + 1)

    def test_product_detail_not_found(self):
        """존재하지 않는 상품 조회 시 404 에러"""
        import uuid

        invalid_uuid = str(uuid.uuid4())
        url = reverse("products:v1:products-detail", kwargs={"pk": invalid_uuid})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductLikeAPITest(BaseAPITestCase):
    """상품 좋아요 API 테스트"""

    def setUp(self):
        super().setUp()
        self.user = TestDataCreator.create_user()

    def test_product_like_toggle_authenticated(self):
        """인증된 사용자의 좋아요 토글 테스트"""
        self.client.force_authenticate(user=self.user)
        product = self.individual_products[0]

        url = reverse("products:v1:products-toggle-like", kwargs={"pk": product.pk})

        # 좋아요 추가
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 1)

        # 좋아요 제거
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 0)

    def test_product_like_toggle_unauthenticated(self):
        """비인증 사용자의 좋아요 시도 테스트"""
        product = self.individual_products[0]
        url = reverse("products:v1:products-toggle-like", kwargs={"pk": product.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class MainPageSectionAPITest(BaseAPITestCase):
    """메인페이지 섹션 API 테스트"""

    def test_monthly_featured_drinks_api(self):
        """이달의 전통주 API 테스트"""
        url = reverse("products:v1:products-monthly")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)
        self.assertEqual(response.data["title"], "이달의 전통주")

        products = response.data["products"]
        self.assertLessEqual(len(products), 3)

    def test_popular_products_api(self):
        """인기 패키지 API 테스트"""
        url = reverse("products:v1:products-popular")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)
        self.assertEqual(response.data["title"], "인기 패키지")

    def test_recommended_products_api(self):
        """추천 전통주 API 테스트"""
        url = reverse("products:v1:products-recommended")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)
        self.assertEqual(response.data["title"], "추천 전통주")

    def test_featured_products_api(self):
        """추천 패키지 API 테스트"""
        url = reverse("products:v1:products-featured")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)
        self.assertEqual(response.data["title"], "추천 패키지")


class PackagePageSectionAPITest(BaseAPITestCase):
    """패키지페이지 섹션 API 테스트"""

    def test_award_winning_products_api(self):
        """수상작 패키지 API 테스트"""
        url = reverse("products:v1:products-award-winning")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)

    def test_makgeolli_products_api(self):
        """막걸리 패키지 API 테스트"""
        url = reverse("products:v1:products-makgeolli")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)

    def test_regional_products_api(self):
        """지역 특산주 패키지 API 테스트"""
        url = reverse("products:v1:products-regional")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)


class AdminAPITest(BaseAPITestCase):
    """관리자 API 테스트"""

    def setUp(self):
        super().setUp()
        self.admin_user = TestDataCreator.create_user(is_staff=True)

    def test_drinks_for_package_list(self):
        """패키지용 술 목록 API 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("products:v1:drinks-for-package")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_product_manage_list(self):
        """관리자용 상품 목록 API 테스트"""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse("products:v1:products-manage-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
