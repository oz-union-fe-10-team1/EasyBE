# apps/products/tests/test_serializers.py

from django.test import TestCase

from apps.products.models import ProductImage

from .test_helpers import TestDataCreator


class BaseSerializerTestCase(TestCase):
    """시리얼라이저 테스트 기본 클래스"""

    def setUp(self):
        self.test_data = TestDataCreator.create_full_dataset()
        self.brewery = self.test_data["breweries"][0]
        self.drink = self.test_data["drinks"][0]
        self.package = self.test_data["packages"][0]
        self.individual_product = self.test_data["individual_products"][0]
        self.package_product = self.test_data["package_products"][0]

    def tearDown(self):
        TestDataCreator.clean_all_data()


class BrewerySerializerTest(BaseSerializerTestCase):
    """양조장 시리얼라이저 테스트"""

    def test_brewery_serialization_fields(self):
        """양조장 직렬화 필드 검증"""
        from apps.products.serializers.brewery import BrewerySerializer

        serializer = BrewerySerializer(self.brewery)
        data = serializer.data

        self.assertEqual(data["name"], "우리술양조장")
        self.assertEqual(data["region"], "경기")
        self.assertEqual(data["address"], "경기도 성남시 분당구 전통주로 123")
        self.assertEqual(data["phone"], "031-123-4567")
        self.assertIn("image_url", data)
        self.assertTrue(data["is_active"])
        self.assertIn("drink_count", data)
        self.assertIsInstance(data["drink_count"], int)

    def test_brewery_list_serialization(self):
        """양조장 목록 직렬화 테스트"""
        from apps.products.serializers.brewery import BreweryListSerializer

        breweries = self.test_data["breweries"]
        serializer = BreweryListSerializer(breweries, many=True)
        data = serializer.data

        self.assertEqual(len(data), 3)
        first_brewery = data[0]
        expected_fields = {"id", "name", "region", "image_url", "product_count"}
        self.assertEqual(set(first_brewery.keys()), expected_fields)


class DrinkSerializerTest(BaseSerializerTestCase):
    """개별 술 시리얼라이저 테스트"""

    def test_drink_serialization_basic_fields(self):
        """술 기본 필드 직렬화 검증"""
        from apps.products.serializers.drink import DrinkSerializer

        serializer = DrinkSerializer(self.drink)
        data = serializer.data

        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["abv"], "6.50")
        self.assertEqual(data["volume_ml"], 750)
        self.assertEqual(data["alcohol_type"], "MAKGEOLLI")
        self.assertEqual(data["brewery"]["name"], "우리술양조장")
        self.assertEqual(data["alcohol_type_display"], "막걸리")

    def test_drink_taste_profile_serialization(self):
        """술 맛 프로필 직렬화 검증"""
        from apps.products.serializers.drink import DrinkSerializer

        serializer = DrinkSerializer(self.drink)
        data = serializer.data

        # 맛 프로필 필드들
        self.assertEqual(data["sweetness_level"], "4.2")
        self.assertEqual(data["acidity_level"], "2.1")
        self.assertEqual(data["body_level"], "3.0")

        # 맛 프로필 벡터
        self.assertIn("taste_profile", data)
        taste_profile = data["taste_profile"]
        self.assertIn("sweetness", taste_profile)
        self.assertEqual(taste_profile["sweetness"], 4.2)

    def test_drink_for_package_serialization(self):
        """패키지용 술 직렬화 검증"""
        from apps.products.serializers.drink import DrinkForPackageSerializer

        serializer = DrinkForPackageSerializer(self.drink)
        data = serializer.data

        expected_fields = {"id", "name", "brewery", "alcohol_type", "abv", "main_image", "price"}
        self.assertEqual(set(data.keys()), expected_fields)

        brewery_data = data["brewery"]
        expected_brewery_fields = {"id", "name", "region"}
        self.assertEqual(set(brewery_data.keys()), expected_brewery_fields)


class PackageSerializerTest(BaseSerializerTestCase):
    """패키지 시리얼라이저 테스트"""

    def test_package_serialization(self):
        """패키지 직렬화 검증"""
        from apps.products.serializers.package import PackageSerializer

        serializer = PackageSerializer(self.package)
        data = serializer.data

        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["type"], "CURATED")
        self.assertEqual(data["type_display"], "큐레이티드")
        self.assertIn("drinks", data)
        self.assertGreater(len(data["drinks"]), 0)
        self.assertEqual(data["drink_count"], 2)


class ProductSerializerTest(BaseSerializerTestCase):
    """상품 시리얼라이저 테스트"""

    def test_individual_product_serialization(self):
        """개별 상품 직렬화 검증"""
        from apps.products.serializers.product import ProductDetailSerializer

        serializer = ProductDetailSerializer(self.individual_product)
        data = serializer.data

        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["product_type"], "individual")
        self.assertEqual(data["price"], 15000)
        self.assertEqual(data["original_price"], 18000)
        self.assertEqual(data["discount"], 3000)
        self.assertIsNotNone(data["drink"])
        self.assertIsNone(data["package"])

        # 할인 계산 검증
        expected_discount_rate = round((3000 / 18000) * 100, 1)
        self.assertEqual(data["discount_rate"], expected_discount_rate)
        self.assertEqual(data["final_price"], 15000)
        self.assertTrue(data["is_on_sale"])

    def test_package_product_serialization(self):
        """패키지 상품 직렬화 검증"""
        from apps.products.serializers.product import ProductDetailSerializer

        serializer = ProductDetailSerializer(self.package_product)
        data = serializer.data

        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["product_type"], "package")
        self.assertIsNotNone(data["discount"])
        self.assertTrue(data["is_on_sale"])
        self.assertIsNone(data["drink"])
        self.assertIsNotNone(data["package"])

    def test_product_list_serialization(self):
        """상품 목록 직렬화 검증"""
        from apps.products.serializers.product import ProductListSerializer

        all_products = self.test_data["all_products"]
        serializer = ProductListSerializer(all_products, many=True)
        data = serializer.data

        self.assertGreaterEqual(len(data), 4)

        first_product = data[0]
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

    def test_product_no_discount_serialization(self):
        """할인 없는 상품 직렬화 검증"""
        from apps.products.serializers.product import ProductDetailSerializer

        no_discount_product = self.test_data["individual_products"][1]
        serializer = ProductDetailSerializer(no_discount_product)
        data = serializer.data

        self.assertIsNone(data["original_price"])
        self.assertIsNone(data["discount"])
        self.assertEqual(data["discount_rate"], 0)
        self.assertEqual(data["final_price"], data["price"])
        self.assertFalse(data["is_on_sale"])


class ProductCreationSerializerTest(BaseSerializerTestCase):
    """상품 생성 시리얼라이저 테스트"""

    def test_individual_product_creation_validation(self):
        """개별 상품 생성 유효성 검사"""
        from apps.products.serializers.product import IndividualProductCreateSerializer
        from apps.products.tests.test_data import get_individual_product_creation_data

        valid_data = get_individual_product_creation_data(self.test_data["breweries"][0].id)
        serializer = IndividualProductCreateSerializer(data=valid_data)

        self.assertTrue(serializer.is_valid())

        # 잘못된 데이터 테스트
        invalid_data = valid_data.copy()
        invalid_data["drink_info"]["name"] = ""

        serializer = IndividualProductCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("drink_info", serializer.errors)

    def test_package_product_creation_validation(self):
        """패키지 상품 생성 유효성 검사"""
        from apps.products.serializers.product import PackageProductCreateSerializer
        from apps.products.tests.test_data import get_package_product_creation_data

        drinks = self.test_data["drinks"]
        drink_ids = [drinks[0].id, drinks[1].id, drinks[2].id]
        valid_data = get_package_product_creation_data(drink_ids)

        serializer = PackageProductCreateSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())

        # 잘못된 데이터 테스트 - 술 개수 부족
        invalid_data = valid_data.copy()
        invalid_data["package_info"]["drink_ids"] = [drinks[0].id]

        serializer = PackageProductCreateSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())


class ProductFilterSerializerTest(TestCase):
    """상품 필터 시리얼라이저 테스트"""

    def test_filter_validation(self):
        """UI 기반 필터 유효성 검사"""
        from apps.products.serializers.product import ProductFilterSerializer

        valid_data = {
            "is_gift_suitable": True,
            "is_regional_specialty": True,
            "is_award_winning": True,
            "is_limited_edition": True,
            "sweetness_level": 3.5,
            "acidity_level": 2.0,
            "bitterness_level": 1.5,
            "body_level": 4.0,
            "carbonation_level": 2.5,
            "aroma_level": 3.0,
            "search": "막걸리",
            "ordering": "-created_at",
        }

        serializer = ProductFilterSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid(), f"Errors: {serializer.errors}")

        # 잘못된 데이터 테스트
        invalid_data = {
            "sweetness_level": -1.0,
            "acidity_level": 6.0,
            "bitterness_level": "invalid",
            "ordering": "invalid_field",
        }

        serializer = ProductFilterSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())

    def test_taste_profile_boundary_validation(self):
        """맛 프로필 경계값 검사"""
        from apps.products.serializers.product import ProductFilterSerializer

        # 경계값 테스트
        boundary_data = {
            "sweetness_level": 0.0,
            "acidity_level": 5.0,
            "bitterness_level": 2.5,
        }

        serializer = ProductFilterSerializer(data=boundary_data)
        self.assertTrue(serializer.is_valid())

        # 범위 초과 테스트
        out_of_range_data = {
            "sweetness_level": -0.1,
            "acidity_level": 5.1,
        }

        serializer = ProductFilterSerializer(data=out_of_range_data)
        self.assertFalse(serializer.is_valid())
