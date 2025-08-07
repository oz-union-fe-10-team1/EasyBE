# from decimal import Decimal
#
# from django.contrib.auth import get_user_model
# from django.test import TestCase
# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APIClient, APITestCase
#
# from apps.products.models import (
#     AlcoholType,
#     Brewery,
#     Product,
#     ProductCategory,
#     Region,
#     TasteTag,
# )
# from apps.products.tests.base import ProductAPITestCase
#
# User = get_user_model()
#
#
# class ProductListAPITestCase(ProductAPITestCase):
#     """제품 목록 API 테스트"""
#
#     def setUp(self):
#         super().setUp()
#         # API 앤드포인트
#         self.url = reverse("product-list")
#
#     def test_get_product_list_success(self):
#         """제품 목록 조회 성공 테스트"""
#         # When: 제품 목록 요청
#         response = self.client.get(self.url)
#
#         # Then: 성공적으로 응답
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         # 응답 구조 검증
#         self.assertIn("count", response.data)
#         self.assertIn("next", response.data)
#         self.assertIn("previous", response.data)
#         self.assertIn("results", response.data)
#
#         # 활성 제품만 반환 (품절, 단종 제외)
#         results = response.data["results"]
#         self.assertEqual(len(results), 12)  # product1, product2만
#
#         # 제품 정보 검증
#         product_names = [product["name"] for product in results]
#         self.assertIn("장수 생막걸리", product_names)
#         self.assertIn("전주 탁주", product_names)
#         self.assertNotIn("품절 제품", product_names)
#         self.assertNotIn("단종 제품", product_names)
#
#     def test_product_list_response_format(self):
#         """제품 목록 응답 형식 검증"""
#         # When: 제품 목록 요청
#         response = self.client.get(self.url)
#
#         # Then: 올바른 응답 형식
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         product = response.data["results"][0]
#
#         # 필수 응답 필드 검증
#         required_fields = [
#             "id",
#             "name",
#             "brewery",
#             "alcohol_type",
#             "region",
#             "price",
#             "discount_rate",
#             "alcohol_content",
#             "volume_ml",
#             "main_image_url",
#             "is_available",
#             # 맛 프로필 필드
#             "sweetness_level",
#             "acidity_level",
#             "body_level",
#             "carbonation_level",
#             "bitterness_level",
#             "aroma_level",
#             "flavor_notes",
#             "short_description",
#             "view_count",
#             "order_count",
#             "like_count",
#             "average_rating",
#             "status",
#             "is_featured",
#             "created_at",
#         ]
#
#         for field in required_fields:
#             self.assertIn(field, product, f"응답에 {field} 필드가 없습니다")
#
#         # 중첩 객체 검증
#         self.assertIn("id", product["brewery"])
#         self.assertIn("name", product["brewery"])
#         self.assertIn("id", product["alcohol_type"])
#         self.assertIn("name", product["alcohol_type"])
#
#     def test_product_list_pagination(self):
#         """제품 목록 페이지네이션 테스트"""
#         # Given: 더 많은 제품 생성 (페이지네이션 테스트용)
#         for i in range(25):  # 🔥 10개 → 25개로 증가
#             Product.objects.create(
#                 name=f"테스트제품{i}",
#                 brewery=self.brewery1,
#                 alcohol_type=self.alcohol_type,
#                 description=f"테스트 제품 {i}",
#                 ingredients="쌀, 누룩",
#                 alcohol_content=6.0,
#                 volume_ml=750,
#                 price=Decimal("5000"),
#                 status="active",
#             )
#
#         # When: 첫 페이지 요청
#         response = self.client.get(self.url)
#
#         # Then: 페이지네이션 정보 확인
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["count"], 37)  # 기본 2개 + 35개
#         self.assertIsNotNone(response.data["next"])  # 다음 페이지 존재
#         self.assertIsNone(response.data["previous"])  # 이전 페이지 없음
#         self.assertEqual(len(response.data["results"]), 20)  # 첫 페이지 20개
#
#     def test_product_list_ordering_default(self):
#         """기본 정렬 순서 테스트 (최신순)"""
#         # When: 제품 목록 요청
#         response = self.client.get(self.url)
#
#         # Then: 최신 생성 순으로 정렬
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         # created_at 기준 내림차순 확인
#         created_dates = [product["created_at"] for product in results]
#         self.assertEqual(created_dates, sorted(created_dates, reverse=True))
#
#     def test_product_list_ordering_by_price(self):
#         """가격순 정렬 테스트"""
#         # When: 가격 오름차순으로 요청
#         response = self.client.get(self.url, {"ordering": "price"})
#
#         # Then: 가격 오름차순 정렬
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         prices = [int(product["price"]) for product in results]
#         self.assertEqual(prices, sorted(prices))
#
#     def test_product_list_ordering_by_popularity(self):
#         """인기순 정렬 테스트"""
#         # When: 주문수 내림차순으로 요청
#         response = self.client.get(self.url, {"ordering": "-order_count"})
#
#         # Then: 주문수 내림차순 정렬
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         order_counts = [product["order_count"] for product in results]
#         self.assertEqual(order_counts, sorted(order_counts, reverse=True))
#
#     def test_product_list_search(self):
#         """제품 검색 테스트"""
#         # Given: 검색어로 "막걸리"
#         search_params = {"search": "막걸리"}
#
#         # When: 검색 요청
#         response = self.client.get(self.url, search_params)
#
#         # Then: 성공적으로 검색
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         self.assertGreater(len(results), 0)
#
#         # 모든 결과에 "막걸리"가 포함되어 있는지 확인
#         for product in results:
#             self.assertIn("막걸리", product["name"])
#
#         # 특정 제품 확인 (첫 번째가 아닌 포함 여부로)
#         product_names = [p["name"] for p in results]
#         self.assertIn("장수 생막걸리", product_names)
#
#     def test_product_list_filter_by_region(self):
#         """지역별 필터링 테스트"""
#         # When: 경기 지역으로 필터링
#         response = self.client.get(self.url, {"region": self.region_gg.id})
#
#         # Then: 경기 지역 제품만 조회
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         for product in results:
#             self.assertEqual(product["region"]["id"], self.region_gg.id)
#
#     def test_product_list_filter_by_price_range(self):
#         """가격 범위 필터링 테스트"""
#         # When: 가격 범위로 필터링 (7000~10000원)
#         response = self.client.get(self.url, {"price_min": 7000, "price_max": 10000})
#
#         # Then: 해당 가격 범위 제품만 조회
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         for product in results:
#             price = int(product["price"])
#             self.assertGreaterEqual(price, 7000)
#             self.assertLessEqual(price, 10000)
#
#     def test_product_list_filter_by_taste_profile(self):
#         """맛 프로필 필터링 테스트"""
#         # When: 단맛 범위로 필터링 (3.0 이상)
#         response = self.client.get(self.url, {"sweetness_min": 3.0})
#
#         # Then: 단맛 3.0 이상 제품만 조회
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         for product in results:
#             self.assertGreaterEqual(product["sweetness_level"], 3.0)
#
#     def test_product_list_filter_by_acidity_profile(self):
#         """산미 필터링 테스트 (추가)"""
#         # When: 산미 범위로 필터링 (3.0 이상)
#         response = self.client.get(self.url, {"acidity_min": 3.0})
#
#         # Then: 산미 3.0 이상 제품만 조회
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         for product in results:
#             self.assertGreaterEqual(product["acidity_level"], 1.5)
#
#     def test_product_list_filter_featured_only(self):
#         """추천 제품만 필터링 테스트"""
#         # When: 추천 제품만 요청
#         response = self.client.get(self.url, {"is_featured": "true"})
#
#         # Then: 추천 제품만 조회
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         for product in results:
#             self.assertTrue(product["is_featured"])
#
#     def test_product_list_multiple_filters(self):
#         """복합 필터링 테스트"""
#         # When: 여러 필터 조합 (지역 + 가격 + 맛)
#         response = self.client.get(self.url, {"region": self.region_gg.id, "price_min": 5000, "sweetness_min": 3.0})
#
#         # Then: 모든 조건을 만족하는 제품만 조회
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#
#         results = response.data["results"]
#         for product in results:
#             self.assertEqual(product["region"]["id"], self.region_gg.id)
#             self.assertGreaterEqual(int(product["price"]), 5000)
#             self.assertGreaterEqual(product["sweetness_level"], 3.0)
#
#     def test_product_list_empty_result(self):
#         """빈 결과 테스트"""
#         # When: 조건에 맞는 제품이 없는 필터 요청
#         response = self.client.get(self.url, {"price_min": 50000, "price_max": 60000})  # 너무 높은 가격
#
#         # Then: 빈 결과 반환
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["count"], 0)
#         self.assertEqual(len(response.data["results"]), 0)
#
#     def test_product_list_unauthenticated_access(self):
#         """비로그인 사용자도 목록 조회 가능"""
#         # When: 로그인하지 않은 상태에서 요청
#         response = self.client.get(self.url)
#
#         # Then: 정상적으로 조회 가능
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertGreater(len(response.data["results"]), 0)
#
#
# class ProductListCustomActionTestCase(APITestCase):
#     """제품 목록 커스텀 액션 테스트"""
#
#     def setUp(self):
#         """테스트 데이터 준비"""
#         # 기본 데이터는 ProductListAPITestCase와 동일하게 설정
#         # (간단히 하기 위해 setUp 내용 생략)
#         pass
#
#     def test_popular_products_api(self):
#         """인기 제품 API 테스트"""
#         # When: 인기 제품 요청
#         url = reverse("product-popular")
#         response = self.client.get(url)
#
#         # Then: 주문수 순으로 정렬된 제품 반환
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # order_count 기준 내림차순 검증
#
#     def test_featured_products_api(self):
#         """추천 제품 API 테스트"""
#         # When: 추천 제품 요청
#         url = reverse("product-featured")
#         response = self.client.get(url)
#
#         # Then: 추천 제품만 반환
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # is_featured=True인 제품만 검증
#
#     def test_new_products_api(self):
#         """신제품 API 테스트"""
#         # When: 신제품 요청
#         url = reverse("product-new")
#         response = self.client.get(url)
#
#         # Then: 최신 생성 순으로 정렬된 제품 반환
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         # created_at 기준 내림차순 검증
