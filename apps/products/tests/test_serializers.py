# apps/products/tests/test_serializers.py

from django.test import TestCase

from apps.products.models import ProductImage

from .test_helpers import clean_test_data, create_full_test_dataset


class BrewerySerializerTest(TestCase):
    """양조장 시리얼라이저 테스트"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.brewery = self.test_data["breweries"][0]

    def tearDown(self):
        clean_test_data()

    def test_brewery_serialization_fields(self):
        """양조장 직렬화 필드 검증"""
        from apps.products.serializers.brewery import BrewerySerializer

        # Given
        serializer = BrewerySerializer(self.brewery)

        # When
        data = serializer.data

        # Then
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

        # Given
        breweries = self.test_data["breweries"]
        serializer = BreweryListSerializer(breweries, many=True)

        # When
        data = serializer.data

        # Then
        self.assertEqual(len(data), 3)
        first_brewery = data[0]
        expected_fields = {"id", "name", "region", "image_url", "product_count"}
        self.assertEqual(set(first_brewery.keys()), expected_fields)


class DrinkSerializerTest(TestCase):
    """개별 술 시리얼라이저 테스트"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.drink = self.test_data["drinks"][0]

    def tearDown(self):
        clean_test_data()

    def test_drink_serialization_basic_fields(self):
        """술 기본 필드 직렬화 검증"""
        from apps.products.serializers.drink import DrinkSerializer

        # Given
        serializer = DrinkSerializer(self.drink)

        # When
        data = serializer.data

        # Then
        self.assertEqual(data["name"], "우리쌀막걸리")
        self.assertEqual(data["abv"], "6.50")
        self.assertEqual(data["volume_ml"], 750)
        self.assertEqual(data["alcohol_type"], "MAKGEOLLI")
        self.assertEqual(data["brewery"]["name"], "우리술양조장")
        self.assertEqual(data["alcohol_type_display"], "막걸리")

    def test_drink_taste_profile_serialization(self):
        """술 맛 프로필 직렬화 검증"""
        from apps.products.serializers.drink import DrinkSerializer

        # Given
        serializer = DrinkSerializer(self.drink)

        # When
        data = serializer.data

        # Then - 맛 프로필 필드들
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

        # Given
        serializer = DrinkForPackageSerializer(self.drink)

        # When
        data = serializer.data

        # Then
        expected_fields = {"id", "name", "brewery", "alcohol_type", "abv", "main_image", "price"}
        self.assertEqual(set(data.keys()), expected_fields)

        brewery_data = data["brewery"]
        expected_brewery_fields = {"id", "name", "region"}
        self.assertEqual(set(brewery_data.keys()), expected_brewery_fields)


class PackageSerializerTest(TestCase):
    """패키지 시리얼라이저 테스트"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.package = self.test_data["packages"][0]

    def tearDown(self):
        clean_test_data()

    def test_package_serialization(self):
        """패키지 직렬화 검증"""
        from apps.products.serializers.package import PackageSerializer

        # Given
        serializer = PackageSerializer(self.package)

        # When
        data = serializer.data

        # Then
        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["type"], "CURATED")
        self.assertEqual(data["type_display"], "큐레이티드")
        self.assertIn("drinks", data)
        self.assertGreater(len(data["drinks"]), 0)
        self.assertEqual(data["drink_count"], 2)


class ProductSerializerTest(TestCase):
    """상품 시리얼라이저 테스트"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.individual_product = self.test_data["individual_products"][0]
        self.package_product = self.test_data["package_products"][0]

    def tearDown(self):
        clean_test_data()

    def test_individual_product_serialization(self):
        """개별 상품 직렬화 검증"""
        from apps.products.serializers.product import ProductDetailSerializer

        # Given
        serializer = ProductDetailSerializer(self.individual_product)

        # When
        data = serializer.data

        # Then
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

        # Given
        serializer = ProductDetailSerializer(self.package_product)

        # When
        data = serializer.data

        # Then
        self.assertEqual(data["name"], "전통주 입문세트")
        self.assertEqual(data["product_type"], "package")
        self.assertIsNotNone(data["discount"])
        self.assertTrue(data["is_on_sale"])
        self.assertIsNone(data["drink"])
        self.assertIsNotNone(data["package"])

    def test_product_list_serialization(self):
        """상품 목록 직렬화 검증"""
        from apps.products.serializers.product import ProductListSerializer

        # Given
        all_products = self.test_data["all_products"]
        serializer = ProductListSerializer(all_products, many=True)

        # When
        data = serializer.data

        # Then
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

        # Given
        no_discount_product = self.test_data["individual_products"][1]
        serializer = ProductDetailSerializer(no_discount_product)

        # When
        data = serializer.data

        # Then
        self.assertIsNone(data["original_price"])
        self.assertIsNone(data["discount"])
        self.assertEqual(data["discount_rate"], 0)
        self.assertEqual(data["final_price"], data["price"])
        self.assertFalse(data["is_on_sale"])


class ProductCreationSerializerTest(TestCase):
    """상품 생성 시리얼라이저 테스트"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.breweries = self.test_data["breweries"]

    def tearDown(self):
        clean_test_data()

    def test_individual_product_creation_validation(self):
        """개별 상품 생성 유효성 검사"""
        from apps.products.serializers.product import (
            IndividualProductCreationSerializer,
        )

        # Given
        valid_data = {
            "drink_info": {
                "name": "신제품막걸리",
                "brewery_id": self.breweries[0].id,
                "ingredients": "쌀(국산 100%), 누룩, 정제수",
                "alcohol_type": "MAKGEOLLI",
                "abv": 6.0,
                "volume_ml": 750,
                "sweetness_level": 4.2,
                "acidity_level": 2.1,
                "body_level": 3.0,
                "carbonation_level": 3.5,
                "bitterness_level": 1.2,
                "aroma_level": 3.8,
            },
            "product_info": {
                "price": 15000,
                "original_price": 18000,
                "discount": 3000,
                "description": "부드럽고 달콤한 프리미엄 막걸리입니다.",
                "description_image_url": "https://cdn.example.com/desc.jpg",
                "is_gift_suitable": True,
                "is_premium": True,
            },
            "images": [
                {"image_url": "https://cdn.example.com/main.jpg", "is_main": True},
                {"image_url": "https://cdn.example.com/detail.jpg", "is_main": False},
            ],
        }

        # When
        serializer = IndividualProductCreationSerializer(data=valid_data)

        # Then
        self.assertTrue(serializer.is_valid())

        # 잘못된 데이터 테스트
        invalid_data = valid_data.copy()
        invalid_data["drink_info"]["name"] = ""

        serializer = IndividualProductCreationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("drink_info", serializer.errors)

    def test_package_product_creation_validation(self):
        """패키지 상품 생성 유효성 검사"""
        from apps.products.serializers.product import PackageProductCreationSerializer

        # Given
        drinks = self.test_data["drinks"]
        valid_data = {
            "package_info": {"name": "나만의 전통주 세트", "type": "MY_CUSTOM"},
            "drink_ids": [drinks[0].id, drinks[1].id, drinks[2].id],
            "product_info": {
                "price": 80000,
                "original_price": 95000,
                "discount": 15000,
                "description": "엄선된 3종의 전통주를 담은 프리미엄 세트입니다.",
                "description_image_url": "https://cdn.example.com/package-desc.jpg",
                "is_gift_suitable": True,
                "is_premium": True,
            },
            "images": [{"image_url": "https://cdn.example.com/package-main.jpg", "is_main": True}],
        }

        # When
        serializer = PackageProductCreationSerializer(data=valid_data)

        # Then
        self.assertTrue(serializer.is_valid())

        # 잘못된 데이터 테스트 - 술 개수 부족
        invalid_data = valid_data.copy()
        invalid_data["drink_ids"] = [drinks[0].id]

        serializer = PackageProductCreationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("drink_ids", serializer.errors)


class ProductFilterSerializerTest(TestCase):
    """상품 필터 시리얼라이저 테스트"""

    def test_filter_validation(self):
        """UI 기반 필터 유효성 검사"""
        from apps.products.serializers.product import ProductFilterSerializer

        # Given
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

        # When
        serializer = ProductFilterSerializer(data=valid_data)

        # Then
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
        self.assertIn("sweetness_level", serializer.errors)
        self.assertIn("acidity_level", serializer.errors)
        self.assertIn("bitterness_level", serializer.errors)
        self.assertIn("ordering", serializer.errors)

    def test_taste_profile_boundary_validation(self):
        """맛 프로필 경계값 검사"""
        from apps.products.serializers.product import ProductFilterSerializer

        # Given
        boundary_data = {
            "sweetness_level": 0.0,
            "acidity_level": 5.0,
            "bitterness_level": 2.5,
        }

        # When
        serializer = ProductFilterSerializer(data=boundary_data)

        # Then
        self.assertTrue(serializer.is_valid())

        # 범위 초과 테스트
        out_of_range_data = {
            "sweetness_level": -0.1,
            "acidity_level": 5.1,
        }

        serializer = ProductFilterSerializer(data=out_of_range_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("sweetness_level", serializer.errors)
        self.assertIn("acidity_level", serializer.errors)
