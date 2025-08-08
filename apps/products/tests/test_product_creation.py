# apps/products/tests/test_product_creation.py

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.products.models import (
    Brewery,
    Drink,
    Package,
    PackageItem,
    Product,
    ProductImage,
)

from .test_data import INDIVIDUAL_PRODUCT_CREATION_DATA, PACKAGE_PRODUCT_CREATION_DATA
from .test_helpers import (
    clean_test_data,
    create_full_test_dataset,
    create_test_breweries,
    create_test_drinks,
    create_test_user,
)

User = get_user_model()


class IndividualProductCreationAPITest(APITestCase):
    """개별 상품 생성 API 테스트"""

    def setUp(self):
        self.breweries = create_test_breweries()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

        # 테스트 데이터에 brewery_id 설정
        self.creation_data = INDIVIDUAL_PRODUCT_CREATION_DATA.copy()
        self.creation_data["drink_info"]["brewery_id"] = self.breweries[0].id

    def tearDown(self):
        clean_test_data()

    def test_create_individual_product_success(self):
        """개별 상품 생성 성공 테스트"""
        # Given
        url = reverse("api:v1:product-create")
        initial_drink_count = Drink.objects.count()
        initial_product_count = Product.objects.count()
        initial_image_count = ProductImage.objects.count()

        # When
        response = self.client.post(url, self.creation_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성된 데이터 검증
        self.assertEqual(Drink.objects.count(), initial_drink_count + 1)
        self.assertEqual(Product.objects.count(), initial_product_count + 1)
        self.assertEqual(ProductImage.objects.count(), initial_image_count + 2)  # 2개 이미지

        # 생성된 술 검증
        drink = Drink.objects.get(name="신제품막걸리")
        self.assertEqual(drink.brewery, self.breweries[0])
        self.assertEqual(drink.alcohol_type, "MAKGEOLLI")
        self.assertEqual(float(drink.abv), 6.0)

        # 생성된 상품 검증
        product = Product.objects.get(drink=drink)
        self.assertEqual(product.price, 15000)
        self.assertEqual(product.original_price, 18000)
        self.assertEqual(product.discount, 3000)
        self.assertTrue(product.is_premium)

        # 생성된 이미지 검증
        images = ProductImage.objects.filter(product=product)
        self.assertEqual(images.count(), 2)
        main_images = images.filter(is_main=True)
        self.assertEqual(main_images.count(), 1)

        # 응답 데이터 검증
        response_data = response.data
        self.assertEqual(response_data["name"], "신제품막걸리")
        self.assertEqual(response_data["product_type"], "individual")
        self.assertIsNotNone(response_data["drink"])
        self.assertIsNone(response_data["package"])

    def test_create_individual_product_validation_error(self):
        """개별 상품 생성 유효성 검사 실패 테스트"""
        # Given
        url = reverse("api:v1:product-create")
        invalid_data = self.creation_data.copy()
        invalid_data["drink_info"]["name"] = ""  # 빈 이름
        invalid_data["product_info"]["price"] = -1000  # 음수 가격

        # When
        response = self.client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drink_info", response.data)
        self.assertIn("product_info", response.data)

    def test_create_individual_product_invalid_brewery(self):
        """존재하지 않는 양조장으로 상품 생성 실패 테스트"""
        # Given
        url = reverse("api:v1:product-create")
        invalid_data = self.creation_data.copy()
        invalid_data["drink_info"]["brewery_id"] = 999  # 존재하지 않는 ID

        # When
        response = self.client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_individual_product_duplicate_name(self):
        """같은 양조장에서 동일한 이름의 술 생성 실패 테스트"""
        # Given
        url = reverse("api:v1:product-create")

        # When
        # 첫 번째 상품 생성
        response = self.client.post(url, self.creation_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 같은 이름으로 다시 생성 시도
        response = self.client.post(url, self.creation_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_individual_product_unauthenticated(self):
        """비인증 사용자의 상품 생성 시도 테스트"""
        # Given
        self.client.force_authenticate(user=None)
        url = reverse("api:v1:product-create")

        # When
        response = self.client.post(url, self.creation_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class IndividualProductCreationTransactionTest(TransactionTestCase):
    """개별 상품 생성 트랜잭션 테스트"""

    def setUp(self):
        self.breweries = create_test_breweries()
        self.user = create_test_user()

    def tearDown(self):
        clean_test_data()

    def test_product_creation_rollback_on_error(self):
        """상품 생성 실패 시 트랜잭션 롤백 테스트"""
        # Given
        url = reverse("api:v1:product-create")
        creation_data = INDIVIDUAL_PRODUCT_CREATION_DATA.copy()
        creation_data["drink_info"]["brewery_id"] = self.breweries[0].id

        initial_drink_count = Drink.objects.count()
        initial_product_count = Product.objects.count()
        initial_image_count = ProductImage.objects.count()

        # 잘못된 데이터로 실패 유도 (이미지 없음)
        invalid_data = creation_data.copy()
        invalid_data["images"] = []  # 빈 이미지 리스트

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user)

        # When
        response = client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 롤백 확인 - 부분적으로 생성된 데이터가 없어야 함
        self.assertEqual(Drink.objects.count(), initial_drink_count)
        self.assertEqual(Product.objects.count(), initial_product_count)
        self.assertEqual(ProductImage.objects.count(), initial_image_count)


class PackageProductCreationAPITest(APITestCase):
    """패키지 상품 생성 API 테스트"""

    def setUp(self):
        self.test_data = create_full_test_dataset()
        self.breweries = self.test_data["breweries"]
        self.drinks = self.test_data["drinks"]
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)

        # 테스트 데이터에 drink_ids 설정
        self.creation_data = PACKAGE_PRODUCT_CREATION_DATA.copy()
        self.creation_data["drink_ids"] = [self.drinks[0].id, self.drinks[1].id, self.drinks[2].id]

    def tearDown(self):
        clean_test_data()

    def test_get_drinks_for_package(self):
        """패키지 생성용 술 목록 조회 테스트"""
        # Given
        url = reverse("api:v1:drinks-for-package")

        # When
        response = self.client.get(url)

        # Then
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_count = Drink.objects.filter(product__isnull=False, product__status="ACTIVE").count()
        self.assertEqual(len(response.data["results"]), expected_count)

        if response.data["results"]:
            first_drink = response.data["results"][0]
            expected_fields = {"id", "name", "brewery", "alcohol_type", "abv", "main_image", "price"}
            self.assertTrue(expected_fields.issubset(set(first_drink.keys())))

            # 양조장 정보 포함 확인
            self.assertIn("name", first_drink["brewery"])
            self.assertIn("region", first_drink["brewery"])

    def test_create_package_product_success(self):
        """패키지 상품 생성 성공 테스트"""
        # Given
        url = reverse("api:v1:package-create")
        initial_package_count = Package.objects.count()
        initial_product_count = Product.objects.count()
        initial_package_item_count = PackageItem.objects.count()

        # When
        response = self.client.post(url, self.creation_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성된 데이터 검증
        self.assertEqual(Package.objects.count(), initial_package_count + 1)
        self.assertEqual(Product.objects.count(), initial_product_count + 1)
        self.assertEqual(PackageItem.objects.count(), initial_package_item_count + 3)  # 3개 술

        # 생성된 패키지 검증
        package = Package.objects.get(name="나만의 전통주 세트")
        self.assertEqual(package.type, "MY_CUSTOM")
        self.assertEqual(package.drinks.count(), 3)

        # 생성된 상품 검증
        product = Product.objects.get(package=package)
        self.assertEqual(product.price, 80000)
        self.assertEqual(product.original_price, 95000)
        self.assertEqual(product.discount, 15000)

        # 응답 데이터 검증
        response_data = response.data
        self.assertEqual(response_data["name"], "나만의 전통주 세트")
        self.assertEqual(response_data["product_type"], "package")
        self.assertIsNone(response_data["drink"])
        self.assertIsNotNone(response_data["package"])

    def test_create_package_with_invalid_drinks(self):
        """잘못된 술 ID로 패키지 생성 실패 테스트"""
        # Given
        url = reverse("api:v1:package-create")
        invalid_data = self.creation_data.copy()
        invalid_data["drink_ids"] = [999, 1000]  # 존재하지 않는 ID

        # When
        response = self.client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_package_minimum_drinks_validation(self):
        """패키지 최소 구성 수 유효성 검사 테스트"""
        # Given
        url = reverse("api:v1:package-create")
        invalid_data = self.creation_data.copy()
        invalid_data["drink_ids"] = [self.drinks[0].id]  # 1개만

        # When
        response = self.client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drink_ids", response.data)

    def test_create_package_maximum_drinks_validation(self):
        """패키지 최대 구성 수 유효성 검사 테스트"""
        # Given
        url = reverse("api:v1:package-create")
        invalid_data = self.creation_data.copy()
        invalid_data["drink_ids"] = [
            self.drinks[0].id,
            self.drinks[1].id,
            self.drinks[2].id,
            self.drinks[3].id,
            self.drinks[0].id,
            self.drinks[1].id,  # 6개
        ]

        # When
        response = self.client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_package_duplicate_drinks_validation(self):
        """패키지 내 중복 술 유효성 검사 테스트"""
        # Given
        url = reverse("api:v1:package-create")
        invalid_data = self.creation_data.copy()
        invalid_data["drink_ids"] = [self.drinks[0].id, self.drinks[0].id, self.drinks[1].id]  # 중복

        # When
        response = self.client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drink_ids", response.data)

    def test_create_package_product_unauthenticated(self):
        """비인증 사용자의 패키지 생성 시도 테스트"""
        # Given
        self.client.force_authenticate(user=None)
        url = reverse("api:v1:package-create")

        # When
        response = self.client.post(url, self.creation_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PackageProductCreationTransactionTest(TransactionTestCase):
    """패키지 상품 생성 트랜잭션 테스트"""

    def setUp(self):
        self.breweries = create_test_breweries()
        self.drinks = create_test_drinks(self.breweries)
        self.user = create_test_user()

    def tearDown(self):
        clean_test_data()

    def test_package_creation_rollback_on_error(self):
        """패키지 생성 실패 시 트랜잭션 롤백 테스트"""
        # Given
        url = reverse("api:v1:package-create")
        creation_data = PACKAGE_PRODUCT_CREATION_DATA.copy()
        creation_data["drink_ids"] = [self.drinks[0].id, self.drinks[1].id, self.drinks[2].id]

        initial_package_count = Package.objects.count()
        initial_product_count = Product.objects.count()
        initial_package_item_count = PackageItem.objects.count()

        # 잘못된 데이터로 실패 유도 (이미지 없음)
        invalid_data = creation_data.copy()
        invalid_data["images"] = []  # 빈 이미지 리스트

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user)

        # When
        response = client.post(url, invalid_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 롤백 확인
        self.assertEqual(Package.objects.count(), initial_package_count)
        self.assertEqual(Product.objects.count(), initial_product_count)
        self.assertEqual(PackageItem.objects.count(), initial_package_item_count)
