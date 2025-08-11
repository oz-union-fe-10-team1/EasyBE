# apps/products/tests/test_helpers.py

from django.contrib.auth import get_user_model

from apps.products.models import (
    Brewery,
    Drink,
    Package,
    PackageItem,
    Product,
    ProductImage,
    ProductLike,
)

from .test_data import (
    BREWERY_DATA,
    DRINK_DATA,
    INDIVIDUAL_PRODUCT_DATA,
    PACKAGE_DATA,
    PACKAGE_PRODUCT_DATA,
    PRODUCT_IMAGE_DATA,
)

User = get_user_model()


class TestDataCreator:
    """테스트 데이터 생성 헬퍼 클래스"""

    @staticmethod
    def create_user(nickname="testuser", email="test@example.com", password="testpass123", **kwargs):
        """테스트용 사용자 생성"""
        if User.objects.filter(nickname=nickname).exists():
            return User.objects.get(nickname=nickname)

        user_data = {"nickname": nickname, "email": email, "is_adult": True, "notification_agreed": True, **kwargs}
        return User.objects.create_user(password=password, **user_data)

    @staticmethod
    def create_breweries():
        """테스트용 양조장들 생성"""
        breweries = []
        for data in BREWERY_DATA:
            brewery, created = Brewery.objects.get_or_create(name=data["name"], defaults=data)
            breweries.append(brewery)
        return breweries

    @staticmethod
    def create_drinks(breweries=None):
        """테스트용 개별 술들 생성"""
        if breweries is None:
            breweries = TestDataCreator.create_breweries()

        drinks = []
        for data in DRINK_DATA:
            drink_data = data.copy()
            brewery_index = drink_data.pop("brewery_index")
            drink_data["brewery"] = breweries[brewery_index]

            drink, created = Drink.objects.get_or_create(
                name=data["name"], brewery=drink_data["brewery"], defaults=drink_data
            )
            drinks.append(drink)
        return drinks

    @staticmethod
    def create_packages(drinks=None):
        """테스트용 패키지들 생성"""
        if drinks is None:
            drinks = TestDataCreator.create_drinks()

        packages = []
        for data in PACKAGE_DATA:
            package_data = data.copy()
            drink_indices = package_data.pop("drink_indices")

            package, created = Package.objects.get_or_create(name=data["name"], defaults=package_data)

            # PackageItem 생성 (패키지에 포함된 술들)
            if created:
                for drink_index in drink_indices:
                    PackageItem.objects.create(package=package, drink=drinks[drink_index])

            packages.append(package)
        return packages

    @staticmethod
    def create_individual_products(drinks=None):
        """테스트용 개별 술 상품들 생성"""
        if drinks is None:
            drinks = TestDataCreator.create_drinks()

        products = []
        for data in INDIVIDUAL_PRODUCT_DATA:
            product_data = data.copy()
            drink_index = product_data.pop("drink_index")
            product_data["drink"] = drinks[drink_index]

            # 기존 상품이 있는지 확인 (OneToOne 관계)
            existing_product = Product.objects.filter(drink=drinks[drink_index]).first()
            if existing_product:
                products.append(existing_product)
            else:
                product = Product.objects.create(**product_data)
                products.append(product)

        return products

    @staticmethod
    def create_package_products(packages=None):
        """테스트용 패키지 상품들 생성"""
        if packages is None:
            packages = TestDataCreator.create_packages()

        products = []
        for data in PACKAGE_PRODUCT_DATA:
            product_data = data.copy()
            package_index = product_data.pop("package_index")
            product_data["package"] = packages[package_index]

            # 기존 상품이 있는지 확인 (OneToOne 관계)
            existing_product = Product.objects.filter(package=packages[package_index]).first()
            if existing_product:
                products.append(existing_product)
            else:
                product = Product.objects.create(**product_data)
                products.append(product)

        return products

    @staticmethod
    def create_product_images(individual_products=None, package_products=None):
        """테스트용 상품 이미지들 생성"""
        if individual_products is None:
            individual_products = TestDataCreator.create_individual_products()
        if package_products is None:
            package_products = TestDataCreator.create_package_products()

        images = []
        for data in PRODUCT_IMAGE_DATA:
            image_data = data.copy()
            product_type = image_data.pop("product_type")
            product_index = image_data.pop("product_index")

            if product_type == "individual":
                image_data["product"] = individual_products[product_index]
            elif product_type == "package":
                image_data["product"] = package_products[product_index]

            # 메인 이미지 중복 방지
            if image_data["is_main"]:
                existing_main = ProductImage.objects.filter(product=image_data["product"], is_main=True).first()
                if existing_main:
                    continue

            image = ProductImage.objects.create(**image_data)
            images.append(image)

        return images

    @staticmethod
    def create_full_dataset():
        """모든 테스트 데이터를 한 번에 생성"""
        # 기본 데이터 생성
        breweries = TestDataCreator.create_breweries()
        drinks = TestDataCreator.create_drinks(breweries)
        packages = TestDataCreator.create_packages(drinks)

        # 상품 데이터 생성
        individual_products = TestDataCreator.create_individual_products(drinks)
        package_products = TestDataCreator.create_package_products(packages)
        all_products = individual_products + package_products

        # 이미지 생성
        images = TestDataCreator.create_product_images(individual_products, package_products)

        # 통계 업데이트
        for product in all_products:
            product.like_count = ProductLike.objects.filter(product=product).count()
            product.save(update_fields=["like_count"])

        return {
            "breweries": breweries,
            "drinks": drinks,
            "packages": packages,
            "individual_products": individual_products,
            "package_products": package_products,
            "all_products": all_products,
            "images": images,
        }

    @staticmethod
    def clean_all_data():
        """테스트 데이터 정리"""
        ProductLike.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        PackageItem.objects.all().delete()
        Package.objects.all().delete()
        Drink.objects.all().delete()
        Brewery.objects.all().delete()
        User.objects.filter(nickname__startswith="test").delete()


# 기존 함수들도 유지 (하위 호환성)
def create_test_user(nickname="testuser", email="test@example.com", password="testpass123", **kwargs):
    """테스트용 사용자 생성 (기존 호환)"""
    return TestDataCreator.create_user(nickname, email, password, **kwargs)


def create_test_breweries():
    """테스트용 양조장들 생성 (기존 호환)"""
    return TestDataCreator.create_breweries()


def create_test_drinks(breweries=None):
    """테스트용 개별 술들 생성 (기존 호환)"""
    return TestDataCreator.create_drinks(breweries)


def create_test_packages(drinks=None):
    """테스트용 패키지들 생성 (기존 호환)"""
    return TestDataCreator.create_packages(drinks)


def create_test_individual_products(drinks=None):
    """테스트용 개별 술 상품들 생성 (기존 호환)"""
    return TestDataCreator.create_individual_products(drinks)


def create_test_package_products(packages=None):
    """테스트용 패키지 상품들 생성 (기존 호환)"""
    return TestDataCreator.create_package_products(packages)


def create_test_product_images(individual_products=None, package_products=None):
    """테스트용 상품 이미지들 생성 (기존 호환)"""
    return TestDataCreator.create_product_images(individual_products, package_products)


def create_full_test_dataset():
    """모든 테스트 데이터를 한 번에 생성 (기존 호환)"""
    return TestDataCreator.create_full_dataset()


def clean_test_data():
    """테스트 데이터 정리 (기존 호환)"""
    TestDataCreator.clean_all_data()
