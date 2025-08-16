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

from .test_data import (
    get_individual_product_creation_data,
    get_package_product_creation_data,
)
from .test_helpers import TestDataCreator

User = get_user_model()


class BaseProductCreationTestCase(APITestCase):
    """상품 생성 테스트 기본 클래스"""

    def setUp(self):
        self.user = TestDataCreator.create_user()
        self.client.force_authenticate(user=self.user)
        self.breweries = TestDataCreator.create_breweries()

    def tearDown(self):
        TestDataCreator.clean_all_data()


class IndividualProductCreationAPITest(BaseProductCreationTestCase):
    """개별 상품 생성 API 테스트"""

    def test_create_individual_product_success(self):
        """개별 상품 생성 성공 테스트"""
        # Given
        url = reverse("products:v1:products-individual-create")  # 🔄 네임스페이스 수정
        creation_data = get_individual_product_creation_data(self.breweries[0].id)

        initial_counts = {
            "drink": Drink.objects.count(),
            "product": Product.objects.count(),
            "image": ProductImage.objects.count(),
        }

        # When
        response = self.client.post(url, creation_data, format="json")

        # Then
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성된 데이터 검증
        self.assertEqual(Drink.objects.count(), initial_counts["drink"] + 1)
        self.assertEqual(Product.objects.count(), initial_counts["product"] + 1)
        self.assertEqual(ProductImage.objects.count(), initial_counts["image"] + 2)

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

    def test_create_individual_product_validation_errors(self):
        """개별 상품 생성 유효성 검사 실패 테스트"""
        url = reverse("products:v1:products-individual-create")  # 🔄 네임스페이스 수정

        # 빈 이름과 음수 가격
        invalid_data = get_individual_product_creation_data(self.breweries[0].id)
        invalid_data["drink_info"]["name"] = ""
        invalid_data["price"] = -1000

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drink_info", response.data)

    def test_create_individual_product_invalid_brewery(self):
        """존재하지 않는 양조장으로 상품 생성 실패 테스트"""
        url = reverse("products:v1:products-individual-create")  # 🔄 네임스페이스 수정
        invalid_data = get_individual_product_creation_data(999)  # 존재하지 않는 ID

        response = self.client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_individual_product_duplicate_name(self):
        """같은 양조장에서 동일한 이름의 술 생성 실패 테스트"""
        url = reverse("products:v1:products-individual-create")  # 🔄 네임스페이스 수정
        creation_data = get_individual_product_creation_data(self.breweries[0].id)

        # 첫 번째 상품 생성
        response = self.client.post(url, creation_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 같은 이름으로 다시 생성 시도
        response = self.client.post(url, creation_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_individual_product_unauthenticated(self):
        """비인증 사용자의 상품 생성 시도 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("products:v1:products-individual-create")  # 🔄 네임스페이스 수정
        creation_data = get_individual_product_creation_data(self.breweries[0].id)

        response = self.client.post(url, creation_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class IndividualProductCreationTransactionTest(TransactionTestCase):
    """개별 상품 생성 트랜잭션 테스트"""

    def setUp(self):
        self.breweries = TestDataCreator.create_breweries()
        self.user = TestDataCreator.create_user()

    def tearDown(self):
        TestDataCreator.clean_all_data()

    def test_product_creation_rollback_on_error(self):
        """상품 생성 실패 시 트랜잭션 롤백 테스트"""
        url = reverse("products:v1:products-individual-create")  # 🔄 네임스페이스 수정
        creation_data = get_individual_product_creation_data(self.breweries[0].id)

        initial_counts = {
            "drink": Drink.objects.count(),
            "product": Product.objects.count(),
            "image": ProductImage.objects.count(),
        }

        # 잘못된 데이터로 실패 유도 (이미지 없음)
        invalid_data = creation_data.copy()
        invalid_data["images"] = []

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 롤백 확인 - 부분적으로 생성된 데이터가 없어야 함
        self.assertEqual(Drink.objects.count(), initial_counts["drink"])
        self.assertEqual(Product.objects.count(), initial_counts["product"])
        self.assertEqual(ProductImage.objects.count(), initial_counts["image"])


class PackageProductCreationAPITest(BaseProductCreationTestCase):
    """패키지 상품 생성 API 테스트"""

    def setUp(self):
        super().setUp()
        self.test_data = TestDataCreator.create_full_dataset()
        self.drinks = self.test_data["drinks"]

    def test_get_drinks_for_package(self):
        """패키지 생성용 술 목록 조회 테스트"""
        url = reverse("products:v1:drinks-for-package")  # 🔄 네임스페이스 수정

        response = self.client.get(url)

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
        url = reverse("products:v1:products-package-create")  # 🔄 네임스페이스 수정
        drink_ids = [self.drinks[0].id, self.drinks[1].id, self.drinks[2].id]
        creation_data = get_package_product_creation_data(drink_ids)

        initial_counts = {
            "package": Package.objects.count(),
            "product": Product.objects.count(),
            "package_item": PackageItem.objects.count(),
        }

        response = self.client.post(url, creation_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성된 데이터 검증
        self.assertEqual(Package.objects.count(), initial_counts["package"] + 1)
        self.assertEqual(Product.objects.count(), initial_counts["product"] + 1)
        self.assertEqual(PackageItem.objects.count(), initial_counts["package_item"] + 3)

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

    def test_create_package_validation_errors(self):
        """패키지 생성 유효성 검사 테스트"""
        url = reverse("products:v1:products-package-create")  # 🔄 네임스페이스 수정

        # 잘못된 술 ID로 패키지 생성 시도
        invalid_data = get_package_product_creation_data([999, 1000])  # 존재하지 않는 ID
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 패키지 최소 구성 수 유효성 검사
        invalid_data = get_package_product_creation_data([self.drinks[0].id])  # 1개만
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 패키지 최대 구성 수 유효성 검사
        drink_ids = [drink.id for drink in self.drinks[:6]]  # 6개 (최대 5개 초과)
        if len(drink_ids) >= 6:
            invalid_data = get_package_product_creation_data(drink_ids)
            response = self.client.post(url, invalid_data, format="json")
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 중복 술 유효성 검사
        duplicate_ids = [self.drinks[0].id, self.drinks[0].id, self.drinks[1].id]
        invalid_data = get_package_product_creation_data(duplicate_ids)
        response = self.client.post(url, invalid_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_package_product_unauthenticated(self):
        """비인증 사용자의 패키지 생성 시도 테스트"""
        self.client.force_authenticate(user=None)
        url = reverse("products:v1:products-package-create")  # 🔄 네임스페이스 수정
        drink_ids = [self.drinks[0].id, self.drinks[1].id, self.drinks[2].id]
        creation_data = get_package_product_creation_data(drink_ids)

        response = self.client.post(url, creation_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PackageProductCreationTransactionTest(TransactionTestCase):
    """패키지 상품 생성 트랜잭션 테스트"""

    def setUp(self):
        self.breweries = TestDataCreator.create_breweries()
        self.drinks = TestDataCreator.create_drinks(self.breweries)
        self.user = TestDataCreator.create_user()

    def tearDown(self):
        TestDataCreator.clean_all_data()

    def test_package_creation_rollback_on_error(self):
        """패키지 생성 실패 시 트랜잭션 롤백 테스트"""
        url = reverse("products:v1:products-package-create")  # 🔄 네임스페이스 수정
        drink_ids = [self.drinks[0].id, self.drinks[1].id, self.drinks[2].id]
        creation_data = get_package_product_creation_data(drink_ids)

        initial_counts = {
            "package": Package.objects.count(),
            "product": Product.objects.count(),
            "package_item": PackageItem.objects.count(),
        }

        # 잘못된 데이터로 실패 유도 (이미지 없음)
        invalid_data = creation_data.copy()
        invalid_data["images"] = []

        from rest_framework.test import APIClient

        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.post(url, invalid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 롤백 확인
        self.assertEqual(Package.objects.count(), initial_counts["package"])
        self.assertEqual(Product.objects.count(), initial_counts["product"])
        self.assertEqual(PackageItem.objects.count(), initial_counts["package_item"])