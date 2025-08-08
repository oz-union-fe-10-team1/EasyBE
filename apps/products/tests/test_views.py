# apps/products/tests/test_views.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .test_helpers import clean_test_data, create_full_test_dataset, create_test_user

User = get_user_model()


class BreweryAPITest(APITestCase):
    """양조장 API 테스트 (어드민용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.breweries = self.test_data["breweries"]

    def tearDown(self):
        clean_test_data()

    def test_brewery_list_api(self):
        """양조장 목록 API 테스트"""
        url = reverse("api:v1:breweries-list")  # GET /api/v1/breweries/
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

        # 첫 번째 양조장 데이터 구조 확인
        first_brewery = response.data["results"][0]
        expected_fields = {"id", "name", "region", "image_url", "product_count"}
        self.assertEqual(set(first_brewery.keys()), expected_fields)

    def test_brewery_detail_api(self):
        """양조장 상세 API 테스트"""
        brewery = self.breweries[0]  # 우리술양조장
        url = reverse("api:v1:breweries-detail", kwargs={"pk": brewery.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 기본 정보 확인
        self.assertEqual(data["name"], "우리술양조장")
        self.assertEqual(data["phone"], "031-123-4567")
        self.assertEqual(data["region"], "경기")

        # 상세 정보 포함 확인
        self.assertIn("description", data)
        self.assertIn("address", data)
        self.assertIn("drink_count", data)


class DrinkAPITest(APITestCase):
    """개별 술 API 테스트 (어드민용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.drinks = self.test_data["drinks"]

    def tearDown(self):
        clean_test_data()

    def test_drink_list_api(self):
        """술 목록 API 테스트"""
        url = reverse("api:v1:drinks-list")  # GET /api/v1/drinks/
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 4)  # 4개 술

    def test_drink_detail_api(self):
        """술 상세 API 테스트"""
        drink = self.drinks[0]  # 우리쌀막걸리
        url = reverse("api:v1:drinks-detail", kwargs={"pk": drink.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 기본 정보 확인
        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["abv"], "6.50")
        self.assertEqual(data["alcohol_type"], "MAKGEOLLI")

        # 양조장 정보 확인
        self.assertEqual(data["brewery"]["name"], "우리술양조장")

        # 맛 프로필 확인
        self.assertIn("taste_profile", data)

    def test_drink_filtering_by_alcohol_type(self):
        """술 목록 주종별 필터링 테스트"""
        url = reverse("api:v1:drinks-list")

        # 막걸리만 필터링
        response = self.client.get(url, {"alcohol_type": "MAKGEOLLI"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 결과가 막걸리여야 함
        for drink in response.data["results"]:
            self.assertEqual(drink["alcohol_type"], "MAKGEOLLI")


class PackageAPITest(APITestCase):
    """패키지 API 테스트 (어드민용 + UI용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.packages = self.test_data["packages"]

    def tearDown(self):
        clean_test_data()

    def test_package_list_api(self):
        """패키지 목록 API 테스트"""
        url = reverse("api:v1:packages-list")  # GET /api/v1/packages/
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)  # 2개 패키지

    def test_package_detail_api(self):
        """패키지 상세 API 테스트"""
        package = self.packages[0]  # 전통주 입문세트
        url = reverse("api:v1:packages-detail", kwargs={"pk": package.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 기본 정보 확인
        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["type"], "CURATED")

        # 포함된 술들 확인
        self.assertIn("drinks", data)
        self.assertEqual(data["drink_count"], 2)


class ProductListAPITest(APITestCase):
    """상품 목록 조회 API 테스트 (UI 검색페이지용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.all_products = self.test_data["all_products"]

    def tearDown(self):
        clean_test_data()

    def test_product_list_api(self):
        """상품 목록 API 테스트"""
        url = reverse("api:v1:products-list")  # GET /api/v1/products/
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 개별 상품 4개 + 패키지 상품 2개 = 총 6개
        self.assertEqual(len(response.data["results"]), 6)

        # 첫 번째 상품 데이터 구조 확인 (할인 필드 포함)
        first_product = response.data["results"][0]
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
            "is_regional_specialty",  # 추가
            "is_limited_edition",  # 추가
            "is_premium",
            "is_award_winning",
            "view_count",
            "like_count",
            "status",
            "created_at",
        }
        self.assertTrue(expected_fields.issubset(set(first_product.keys())))

    def test_product_list_filtering_by_gift_suitable(self):
        """선물용 상품 필터링 테스트"""
        url = reverse("api:v1:products-list")

        # 선물용 체크박스 선택
        response = self.client.get(url, {"is_gift_suitable": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 결과가 선물용 상품이어야 함
        for product in response.data["results"]:
            self.assertTrue(product["is_gift_suitable"])

    def test_product_list_filtering_by_regional_specialty(self):
        """지역 특산주 필터링 테스트"""
        url = reverse("api:v1:products-list")

        # 지역 특산주 체크박스 선택
        response = self.client.get(url, {"is_regional_specialty": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 결과가 지역 특산주여야 함
        for product in response.data["results"]:
            self.assertTrue(product["is_regional_specialty"])

    def test_product_list_filtering_by_award_winning(self):
        """주류 대상 수상 필터링 테스트"""
        url = reverse("api:v1:products-list")

        # 주류 대상 수상 체크박스 선택
        response = self.client.get(url, {"is_award_winning": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 결과가 수상작이어야 함
        for product in response.data["results"]:
            self.assertTrue(product["is_award_winning"])

    def test_product_list_filtering_by_limited_edition(self):
        """리미티드 에디션 필터링 테스트"""
        url = reverse("api:v1:products-list")

        # 리미티드 에디션 체크박스 선택
        response = self.client.get(url, {"is_limited_edition": True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 결과가 리미티드 에디션이어야 함
        for product in response.data["results"]:
            self.assertTrue(product["is_limited_edition"])

    def test_product_list_search(self):
        """상품 목록 검색 테스트"""
        url = reverse("api:v1:products-list")

        # '막걸리' 검색
        response = self.client.get(url, {"search": "막걸리"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 검색 결과에 '막걸리'가 포함된 상품이 있어야 함
        found = any("막걸리" in product["name"] for product in response.data["results"])
        self.assertTrue(found)

    def test_product_list_ordering(self):
        """상품 목록 정렬 테스트"""
        url = reverse("api:v1:products-list")

        # 가격 오름차순 정렬
        response = self.client.get(url, {"ordering": "price"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        # 가격이 오름차순으로 정렬되었는지 확인
        prices = [product["price"] for product in results]
        self.assertEqual(prices, sorted(prices))

        # 조회수 내림차순 정렬
        response = self.client.get(url, {"ordering": "-view_count"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]

        # 조회수가 내림차순으로 정렬되었는지 확인
        view_counts = [product["view_count"] for product in results]
        self.assertEqual(view_counts, sorted(view_counts, reverse=True))


class ProductDetailAPITest(APITestCase):
    """상품 상세 조회 API 테스트 (UI용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.individual_product = self.test_data["individual_products"][0]
        self.package_product = self.test_data["package_products"][0]

    def tearDown(self):
        clean_test_data()

    def test_individual_product_detail_api(self):
        """개별 상품 상세 API 테스트"""
        product = self.individual_product
        url = reverse("api:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 기본 정보 확인
        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["product_type"], "individual")
        self.assertEqual(data["price"], 15000)

        # 할인 정보 확인
        self.assertEqual(data["original_price"], 18000)
        self.assertEqual(data["discount"], 3000)
        self.assertEqual(data["final_price"], 15000)  # price가 이미 할인된 가격
        self.assertTrue(data["is_on_sale"])

        # 개별 술 정보 포함 확인
        self.assertIsNotNone(data["drink"])
        self.assertIsNone(data["package"])

        # 술 정보 확인
        self.assertEqual(data["drink"]["name"], "우리쌀막걸리")
        self.assertEqual(data["drink"]["alcohol_type"], "MAKGEOLLI")

    def test_package_product_detail_api(self):
        """패키지 상품 상세 API 테스트"""
        product = self.package_product
        url = reverse("api:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # 기본 정보 확인
        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["product_type"], "package")

        # 할인 정보 확인
        self.assertIsNotNone(data["discount"])
        self.assertTrue(data["is_on_sale"])

        # 패키지 정보 포함 확인
        self.assertIsNone(data["drink"])
        self.assertIsNotNone(data["package"])

        # 패키지 정보 확인
        self.assertEqual(data["package"]["name"], "전통주 입문세트")
        self.assertEqual(data["package"]["drink_count"], 2)

    def test_product_detail_view_count_increment(self):
        """상품 상세 조회 시 조회수 증가 테스트"""
        product = self.individual_product
        initial_view_count = product.view_count

        url = reverse("api:v1:products-detail", kwargs={"pk": product.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회수가 증가했는지 확인
        product.refresh_from_db()
        self.assertEqual(product.view_count, initial_view_count + 1)

    def test_product_detail_not_found(self):
        """존재하지 않는 상품 조회 테스트"""
        import uuid

        invalid_uuid = str(uuid.uuid4())
        url = reverse("api:v1:products-detail", kwargs={"pk": invalid_uuid})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductLikeAPITest(APITestCase):
    """상품 좋아요 API 테스트 (UI용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.product = self.test_data["individual_products"][0]
        self.user = create_test_user()

    def tearDown(self):
        clean_test_data()

    def test_product_like_toggle_authenticated(self):
        """인증된 사용자의 좋아요 토글 테스트"""
        self.client.force_authenticate(user=self.user)

        url = reverse("api:v1:products-toggle-like", kwargs={"pk": self.product.pk})

        # 첫 번째 요청: 좋아요 추가
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 1)

        # 두 번째 요청: 좋아요 제거
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 0)

    def test_product_like_toggle_unauthenticated(self):
        """비인증 사용자의 좋아요 시도 테스트"""
        url = reverse("api:v1:products-toggle-like", kwargs={"pk": self.product.pk})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_like_invalid_product(self):
        """존재하지 않는 상품 좋아요 시도 테스트"""
        self.client.force_authenticate(user=self.user)

        import uuid

        invalid_uuid = str(uuid.uuid4())
        url = reverse("api:v1:products-toggle-like", kwargs={"pk": invalid_uuid})

        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MainPageAPITest(APITestCase):
    """메인페이지 API 테스트 (UI용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.products = self.test_data["all_products"]

    def tearDown(self):
        clean_test_data()

    def test_popular_products_api(self):
        """인기 상품 API 테스트"""
        # 일부 상품의 조회수를 높여서 인기 상품으로 만들기
        self.products[0].view_count = 100
        self.products[0].save()
        self.products[1].view_count = 50
        self.products[1].save()

        url = reverse("api:v1:products-popular")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회수가 높은 순으로 정렬되어야 함
        results = response.data["results"]
        if len(results) >= 2:
            first_views = results[0]["view_count"]
            second_views = results[1]["view_count"]
            self.assertGreaterEqual(first_views, second_views)

    def test_featured_products_api(self):
        """추천 상품 API 테스트"""
        url = reverse("api:v1:products-featured")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 프리미엄 상품들이 반환되어야 함
        for product in response.data["results"]:
            self.assertTrue(product["is_premium"])


class ProductTasteProfileFilterTest(APITestCase):
    """상품 맛 프로필 필터링 테스트 (UI 검색페이지용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.drinks = self.test_data["drinks"]

    def tearDown(self):
        clean_test_data()

    def test_multiple_taste_profile_with_tolerance(self):
        """UI 시나리오: 여러 맛 프로필 동시 필터링 (±1 범위)"""
        url = reverse("api:v1:products-list")

        # 슬라이더에서 단맛 3.0, 산미 2.0, 쓴맛 1.5, 바디감 4.0, 탄산감 2.5, 풍미 3.5 선택
        response = self.client.get(
            url,
            {
                "sweetness_level": 3.0,  # 단 맛: 2.0~4.0 범위
                "acidity_level": 2.0,  # 산 미: 1.0~3.0 범위
                "bitterness_level": 1.5,  # 쓴 맛: 0.5~2.5 범위
                "body_level": 4.0,  # 바디감: 3.0~5.0 범위
                "carbonation_level": 2.5,  # 탄산감: 1.5~3.5 범위
                "aroma_level": 3.5,  # 풍 미: 2.5~4.5 범위
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 개별 상품들이 모든 조건을 만족하는지 확인
        for product in response.data["results"]:
            if product["product_type"] == "individual":
                # 각 맛 프로필이 ±1 범위 내에 있어야 함
                drink_data = product.get("drink", {})

                sweetness = float(drink_data.get("sweetness_level", 0))
                acidity = float(drink_data.get("acidity_level", 0))
                bitterness = float(drink_data.get("bitterness_level", 0))
                body = float(drink_data.get("body_level", 0))
                carbonation = float(drink_data.get("carbonation_level", 0))
                aroma = float(drink_data.get("aroma_level", 0))

                # 단 맛 (3.0 ± 1.0)
                self.assertGreaterEqual(sweetness, 2.0)
                self.assertLessEqual(sweetness, 4.0)

                # 산 미 (2.0 ± 1.0)
                self.assertGreaterEqual(acidity, 1.0)
                self.assertLessEqual(acidity, 3.0)

                # 쓴 맛 (1.5 ± 1.0)
                self.assertGreaterEqual(bitterness, 0.5)
                self.assertLessEqual(bitterness, 2.5)

                # 바디감 (4.0 ± 1.0)
                self.assertGreaterEqual(body, 3.0)
                self.assertLessEqual(body, 5.0)

                # 탄산감 (2.5 ± 1.0)
                self.assertGreaterEqual(carbonation, 1.5)
                self.assertLessEqual(carbonation, 3.5)

                # 풍 미 (3.5 ± 1.0)
                self.assertGreaterEqual(aroma, 2.5)
                self.assertLessEqual(aroma, 4.5)


class PackageTypeFilterTest(APITestCase):
    """패키지 타입 필터링 테스트 (UI 패키지페이지용)"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.packages = self.test_data["packages"]

    def tearDown(self):
        clean_test_data()

    def test_package_type_filtering(self):
        """UI 시나리오: 패키지 타입별 필터링"""
        url = reverse("api:v1:packages-list")

        # 큐레이티드 패키지만 필터링
        response = self.client.get(url, {"type": "CURATED"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 응답이 PackageListSerializer 형태인지 확인 (Product 기반)
        for item in response.data["results"]:
            # Package 정보는 중첩된 객체로 포함됨
            if item.get("package"):
                self.assertEqual(item["package"]["type"], "CURATED")

        # 마이 커스텀 패키지만 필터링
        response = self.client.get(url, {"type": "MY_CUSTOM"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 모든 결과가 마이 커스텀 타입이어야 함
        for item in response.data["results"]:
            if item.get("package"):
                self.assertEqual(item["package"]["type"], "MY_CUSTOM")

    def test_package_category_filtering(self):
        """UI 시나리오: 패키지 카테고리별 필터링"""
        url = reverse("api:v1:packages-list")

        # 추천 패키지 (프리미엄)
        response = self.client.get(url, {"is_premium": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data["results"]:
            self.assertTrue(item["is_premium"])  # Product 필드

        # 주류 대상 수상 5종
        response = self.client.get(url, {"is_award_winning": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data["results"]:
            self.assertTrue(item["is_award_winning"])

        # 지역 특산주
        response = self.client.get(url, {"is_regional_specialty": True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        for item in response.data["results"]:
            self.assertTrue(item["is_regional_specialty"])

        # 막걸리 패키지
        response = self.client.get(url, {"category": "makgeolli"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 결과가 있을 경우 모두 막걸리만 포함된 패키지여야 함
        for item in response.data["results"]:
            if item.get("package") and item["package"].get("drinks"):
                for drink in item["package"]["drinks"]:
                    self.assertEqual(drink["alcohol_type"], "MAKGEOLLI")
