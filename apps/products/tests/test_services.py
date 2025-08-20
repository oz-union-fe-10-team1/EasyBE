# apps/products/tests/test_services.py

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.http import QueryDict
from django.test import TestCase

from apps.products.models import Product, ProductLike
from apps.products.services import LikeService, ProductService, SearchService

from .test_helpers import TestDataCreator

User = get_user_model()


class BaseServiceTestCase(TestCase):
    """서비스 테스트 기본 클래스"""

    def setUp(self):
        self.test_data = TestDataCreator.create_full_dataset()
        self.individual_products = self.test_data["individual_products"]
        self.package_products = self.test_data["package_products"]
        self.all_products = self.test_data["all_products"]
        self.user = TestDataCreator.create_user()

    def tearDown(self):
        TestDataCreator.clean_all_data()


class ProductServiceTest(BaseServiceTestCase):
    """ProductService 테스트"""

    def test_get_product_detail_increments_view_count(self):
        """상품 상세 조회 시 조회수 증가 테스트"""
        product = self.individual_products[0]
        initial_view_count = product.view_count

        # Service 메서드 호출
        result_product = ProductService.get_product_detail(str(product.pk))

        # 조회수 증가 확인
        self.assertEqual(result_product.view_count, initial_view_count + 1)

        # DB에서도 확인
        product.refresh_from_db()
        self.assertEqual(product.view_count, initial_view_count + 1)

    def test_get_product_detail_nonexistent_product(self):
        """존재하지 않는 상품 조회 시 404 에러"""
        import uuid

        from django.http import Http404

        invalid_id = str(uuid.uuid4())

        with self.assertRaises(Http404):
            ProductService.get_product_detail(invalid_id)

    def test_get_section_products_popular(self):
        """인기 상품 섹션 테스트"""
        # 조회수 설정
        self.all_products[0].view_count = 100
        self.all_products[0].save()
        self.all_products[1].view_count = 50
        self.all_products[1].save()

        products = ProductService.get_section_products("popular", limit=8)

        # 결과 확인
        self.assertLessEqual(len(products), 8)
        if len(products) >= 2:
            self.assertGreaterEqual(products[0].view_count, products[1].view_count)

    def test_get_section_products_monthly(self):
        """이달의 전통주 섹션 테스트"""
        products = ProductService.get_section_products("monthly", limit=3)

        # 개별 술만 반환되는지 확인
        self.assertLessEqual(len(products), 3)
        for product in products:
            self.assertIsNotNone(product.drink)

    def test_get_section_products_featured(self):
        """추천 패키지 섹션 테스트"""
        products = ProductService.get_section_products("featured", limit=4)

        # 패키지 상품만 반환되는지 확인
        for product in products:
            self.assertIsNotNone(product.package)
            self.assertIsNone(product.drink)

        # 최신순으로 정렬되는지 확인 (created_at 기준)
        if len(products) > 1:
            for i in range(len(products) - 1):
                self.assertGreaterEqual(products[i].created_at, products[i + 1].created_at)

    def test_get_section_products_invalid_type(self):
        """잘못된 섹션 타입 테스트"""
        products = ProductService.get_section_products("invalid_type", limit=4)

        # 빈 쿼리셋 반환
        self.assertEqual(len(products), 0)


class LikeServiceTest(BaseServiceTestCase):
    """LikeService 테스트"""

    def test_toggle_product_like_add(self):
        """좋아요 추가 테스트"""
        product = self.individual_products[0]
        initial_like_count = product.like_count

        # 좋아요 추가
        is_liked, like_count = LikeService.toggle_product_like(self.user, str(product.pk))

        # 결과 확인
        self.assertTrue(is_liked)
        self.assertEqual(like_count, initial_like_count + 1)

        # DB 확인
        self.assertTrue(ProductLike.objects.filter(user=self.user, product=product).exists())

    def test_toggle_product_like_remove(self):
        """좋아요 제거 테스트"""
        product = self.individual_products[0]

        # 먼저 좋아요 추가
        ProductLike.objects.create(user=self.user, product=product)
        initial_like_count = ProductLike.objects.filter(product=product).count()

        # 좋아요 제거
        is_liked, like_count = LikeService.toggle_product_like(self.user, str(product.pk))

        # 결과 확인
        self.assertFalse(is_liked)
        self.assertEqual(like_count, initial_like_count - 1)

        # DB 확인
        self.assertFalse(ProductLike.objects.filter(user=self.user, product=product).exists())

    def test_toggle_product_like_nonexistent_product(self):
        """존재하지 않는 상품 좋아요 시 404 에러"""
        import uuid

        from django.http import Http404

        invalid_id = str(uuid.uuid4())

        with self.assertRaises(Http404):
            LikeService.toggle_product_like(self.user, invalid_id)

    def test_check_user_liked_product(self):
        """사용자 좋아요 확인 테스트"""
        product = self.individual_products[0]

        # 좋아요 하지 않은 상태
        self.assertFalse(LikeService.check_user_liked_product(self.user, str(product.pk)))

        # 좋아요 추가 후
        ProductLike.objects.create(user=self.user, product=product)
        self.assertTrue(LikeService.check_user_liked_product(self.user, str(product.pk)))


class SearchServiceTest(BaseServiceTestCase):
    """SearchService 테스트"""

    def test_apply_taste_filters(self):
        """맛 프로필 필터 적용 테스트"""
        # 맛 프로필이 있는 개별 상품만 테스트
        queryset = Product.objects.filter(drink__isnull=False, status="ACTIVE")

        query_params = QueryDict("sweetness=3.0&acidity=2.5")

        filtered_queryset = SearchService.apply_taste_filters(queryset, query_params)

        # 필터가 적용되었는지 확인 (쿼리 변화)
        self.assertNotEqual(str(queryset.query), str(filtered_queryset.query))

    def test_apply_category_filters(self):
        """카테고리 필터 적용 테스트"""
        # 프리미엄 상품 설정
        self.all_products[0].is_premium = True
        self.all_products[0].save()

        queryset = Product.objects.filter(status="ACTIVE")
        query_params = QueryDict("premium=true")

        filtered_queryset = SearchService.apply_category_filters(queryset, query_params)

        # 프리미엄 상품만 반환되는지 확인
        for product in filtered_queryset:
            self.assertTrue(product.is_premium)

    def test_get_search_queryset_with_multiple_filters(self):
        """여러 필터 동시 적용 테스트"""
        # 테스트 데이터 설정
        product = self.all_products[0]
        product.is_premium = True
        product.save()

        query_params = QueryDict("premium=true&gift_suitable=true")

        queryset = SearchService.get_search_queryset(query_params)

        # 할인율 계산이 포함된 쿼리셋인지 확인
        first_product = queryset.first()
        if first_product:
            self.assertTrue(hasattr(first_product, "discount_rate"))

    def test_validate_search_params_valid(self):
        """유효한 검색 파라미터 검증 테스트"""
        query_params = QueryDict("sweetness=3.0&acidity=2.5&body=4.0")

        errors = SearchService.validate_search_params(query_params)

        # 에러가 없어야 함
        self.assertEqual(len(errors), 0)

    def test_validate_search_params_invalid(self):
        """잘못된 검색 파라미터 검증 테스트"""
        query_params = QueryDict("sweetness=6.0&acidity=invalid&body=-1.0")

        errors = SearchService.validate_search_params(query_params)

        # 에러가 있어야 함
        self.assertGreater(len(errors), 0)
        self.assertIn("sweetness", errors)  # 범위 초과
        self.assertIn("acidity", errors)  # 잘못된 형식
        self.assertIn("body", errors)  # 음수

    def test_get_applied_filters(self):
        """적용된 필터 목록 반환 테스트"""
        query_params = QueryDict("sweetness=3.0&premium=true&invalid_param=test")

        applied_filters = SearchService._get_applied_filters(query_params)

        # 유효한 필터만 반환되는지 확인
        self.assertIn("sweetness", applied_filters)
        self.assertIn("premium", applied_filters)
        self.assertNotIn("invalid_param", applied_filters)

        self.assertEqual(applied_filters["sweetness"], 3.0)
        self.assertTrue(applied_filters["premium"])
