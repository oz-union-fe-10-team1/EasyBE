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


class ProductListAPITest(BaseAPITestCase):
    """상품 목록 조회 API 테스트"""

    def test_product_search_api(self):
        """상품 검색 API 테스트"""
        url = reverse("products:v1:products-search")  # 🔄 변경된 URL name
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)

        results = response.data["results"]
        self.assertEqual(len(results), 8)

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

    def test_product_filtering_tests(self):
        """상품 필터링 테스트들"""
        url = reverse("products:v1:products-search")  # 🔄 변경된 URL name

        # 선물용 상품 필터링 테스트
        self.all_products[0].is_gift_suitable = True
        self.all_products[0].save()

        response = self.client.get(url, {"gift_suitable": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        self.assertGreater(len(results), 0)
        for product in results:
            self.assertTrue(product["is_gift_suitable"])

        # 지역 특산주 필터링 테스트
        self.all_products[1].is_regional_specialty = True
        self.all_products[1].save()

        response = self.client.get(url, {"regional_specialty": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        if results:
            for product in results:
                self.assertTrue(product["is_regional_specialty"])

        # 리미티드 에디션 필터링 테스트
        self.all_products[2].is_limited_edition = True
        self.all_products[2].save()

        response = self.client.get(url, {"limited_edition": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        if results:
            for product in results:
                self.assertTrue(product["is_limited_edition"])

        # 프리미엄 필터링 테스트
        self.all_products[3].is_premium = True
        self.all_products[3].save()

        response = self.client.get(url, {"premium": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        if results:
            for product in results:
                self.assertTrue(product["is_premium"])

    def test_product_search_and_ordering(self):
        """상품 검색 및 정렬 테스트"""
        url = reverse("products:v1:products-search")  # 🔄 변경된 URL name

        # 검색 테스트
        response = self.client.get(url, {"search": "막걸리"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        found = any("막걸리" in product["name"] for product in results)
        self.assertTrue(found)

        # 가격 오름차순 정렬
        response = self.client.get(url, {"ordering": "price"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        prices = [product["price"] for product in results]
        self.assertEqual(prices, sorted(prices))

        # 조회수 내림차순 정렬
        response = self.client.get(url, {"ordering": "-view_count"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        view_counts = [product["view_count"] for product in results]
        self.assertEqual(view_counts, sorted(view_counts, reverse=True))


class ProductDetailAPITest(BaseAPITestCase):
    """상품 상세 조회 API 테스트"""

    def test_individual_product_detail_api(self):
        """개별 상품 상세 API 테스트"""
        product = self.individual_products[0]
        url = reverse("products:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["product_type"], "individual")
        self.assertEqual(data["price"], 15000)
        self.assertEqual(data["original_price"], 18000)
        self.assertEqual(data["discount"], 3000)
        self.assertEqual(data["final_price"], 15000)
        self.assertTrue(data["is_on_sale"])
        self.assertIsNotNone(data["drink"])
        self.assertIsNone(data["package"])

    def test_package_product_detail_api(self):
        """패키지 상품 상세 API 테스트"""
        product = self.package_products[0]
        url = reverse("products:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["product_type"], "package")
        self.assertIsNotNone(data["discount"])
        self.assertTrue(data["is_on_sale"])
        self.assertIsNone(data["drink"])
        self.assertIsNotNone(data["package"])

    def test_product_detail_view_count_increment(self):
        """상품 상세 조회 시 조회수 증가 테스트"""
        product = self.individual_products[0]
        initial_view_count = product.view_count

        url = reverse("products:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product.refresh_from_db()
        self.assertEqual(product.view_count, initial_view_count + 1)

    def test_product_detail_not_found(self):
        """존재하지 않는 상품 조회 테스트"""
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


class MainPageAPITest(BaseAPITestCase):
    """메인페이지 API 테스트"""

    def test_monthly_featured_drinks_api(self):
        """이달의 전통주 API 테스트"""  # 🆕 새로 추가
        url = reverse("products:v1:products-monthly")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)
        self.assertEqual(response.data["title"], "이달의 전통주")

        products = response.data["products"]
        self.assertLessEqual(len(products), 3)  # TOP 3개까지

    def test_popular_products_api(self):
        """인기 패키지 API 테스트"""
        self.all_products[0].view_count = 100
        self.all_products[0].save()
        self.all_products[1].view_count = 50
        self.all_products[1].save()

        url = reverse("products:v1:products-popular")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data)
        self.assertIn("products", response.data)

        products = response.data["products"]
        if len(products) >= 2:
            first_views = products[0]["view_count"]
            second_views = products[1]["view_count"]
            self.assertGreaterEqual(first_views, second_views)

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

        products = response.data["products"]
        for product in products:
            self.assertTrue(product["is_premium"])


class ProductTasteProfileFilterTest(BaseAPITestCase):
    """상품 맛 프로필 필터링 테스트"""

    def test_multiple_taste_profile_filtering(self):
        """여러 맛 프로필 동시 필터링 테스트"""
        url = reverse("products:v1:products-search")  # 🔄 변경된 URL name

        response = self.client.get(
            url,
            {
                "sweetness": 3.0,
                "acidity": 2.0,
                "bitterness": 1.5,
                "body": 4.0,
                "carbonation": 2.5,
                "aroma": 3.5,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        results = response.data["results"]
        for product in results:
            if product["product_type"] == "individual":
                self.assertIsNotNone(product.get("alcohol_type"))


# 🆕 관리자 API 테스트 추가
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
