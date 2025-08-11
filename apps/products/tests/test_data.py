# apps/products/tests/test_data.py

# 공통 맛 프로필 템플릿
TASTE_PROFILES = {
    "makgeolli_sweet": {
        "sweetness_level": 4.2,
        "acidity_level": 2.1,
        "body_level": 3.0,
        "carbonation_level": 3.5,
        "bitterness_level": 1.2,
        "aroma_level": 3.8,
    },
    "cheongju_clean": {
        "sweetness_level": 2.5,
        "acidity_level": 2.8,
        "body_level": 4.2,
        "carbonation_level": 1.0,
        "bitterness_level": 2.0,
        "aroma_level": 4.5,
    },
    "soju_strong": {
        "sweetness_level": 1.5,
        "acidity_level": 1.8,
        "body_level": 4.5,
        "carbonation_level": 0.0,
        "bitterness_level": 1.0,
        "aroma_level": 4.0,
    },
    "fruit_wine_sweet": {
        "sweetness_level": 4.0,
        "acidity_level": 3.2,
        "body_level": 2.8,
        "carbonation_level": 0.5,
        "bitterness_level": 0.8,
        "aroma_level": 4.2,
    },
}

# 양조장 데이터
BREWERY_DATA = [
    {
        "name": "우리술양조장",
        "region": "경기",
        "address": "경기도 성남시 분당구 전통주로 123",
        "phone": "031-123-4567",
        "description": "3대째 이어온 전통 막걸리 양조장. 우리쌀만을 사용하여 깊고 진한 맛의 막걸리를 빚습니다.",
        "image_url": "https://cdn.example.com/brewery/woori-logo.jpg",
    },
    {
        "name": "전통주방",
        "region": "충남",
        "address": "충남 공주시 전통로 456",
        "phone": "041-999-8888",
        "description": "70년 전통의 청주 전문 양조장. 지하 암반수와 엄선된 쌀로 청아한 맛의 청주를 생산합니다.",
        "image_url": "https://cdn.example.com/brewery/traditional-logo.jpg",
    },
    {
        "name": "한옥소주",
        "region": "전북",
        "address": "전북 전주시 한옥마을길 789",
        "phone": "063-555-7777",
        "description": "전통 한옥에서 100년간 이어온 증류 기법으로 깔끔한 소주를 만듭니다.",
    },
]

# 개별 술 데이터
DRINK_DATA = [
    {
        "name": "우리쌀막걸리",
        "brewery_index": 0,
        "ingredients": "쌀(국산 100%), 누룩, 정제수",
        "alcohol_type": "MAKGEOLLI",
        "abv": 6.5,
        "volume_ml": 750,
        **TASTE_PROFILES["makgeolli_sweet"],
    },
    {
        "name": "프리미엄청주",
        "brewery_index": 1,
        "ingredients": "쌀(충남산), 누룩, 암반수",
        "alcohol_type": "CHEONGJU",
        "abv": 15.0,
        "volume_ml": 500,
        **TASTE_PROFILES["cheongju_clean"],
    },
    {
        "name": "한옥증류소주",
        "brewery_index": 2,
        "ingredients": "쌀, 누룩, 정제수",
        "alcohol_type": "SOJU",
        "abv": 25.0,
        "volume_ml": 375,
        **TASTE_PROFILES["soju_strong"],
    },
    {
        "name": "복분자와인",
        "brewery_index": 1,
        "ingredients": "복분자, 설탕",
        "alcohol_type": "FRUIT_WINE",
        "abv": 12.0,
        "volume_ml": 375,
        **TASTE_PROFILES["fruit_wine_sweet"],
    },
]

# 패키지 데이터
PACKAGE_DATA = [
    {"name": "전통주 입문세트", "type": "CURATED", "drink_indices": [0, 1]},
    {"name": "프리미엄 컬렉션", "type": "CURATED", "drink_indices": [1, 2, 3]},
]

# 공통 상품 특성 템플릿
PRODUCT_FEATURES = {
    "premium_gift": {
        "is_gift_suitable": True,
        "is_premium": True,
        "is_regional_specialty": True,
    },
    "award_winning": {
        "is_gift_suitable": True,
        "is_premium": True,
        "is_award_winning": True,
    },
    "limited_premium": {
        "is_premium": True,
        "is_limited_edition": True,
        "is_regional_specialty": True,
    },
    "organic_gift": {
        "is_gift_suitable": True,
        "is_organic": True,
    },
}

# 개별 상품 데이터
INDIVIDUAL_PRODUCT_DATA = [
    {
        "drink_index": 0,
        "price": 15000,
        "original_price": 18000,
        "discount": 3000,
        "description": "100% 우리쌀로 빚은 부드럽고 달콤한 프리미엄 막걸리입니다.",
        "description_image_url": "https://cdn.example.com/products/makgeolli1-desc.jpg",
        **PRODUCT_FEATURES["premium_gift"],
    },
    {
        "drink_index": 1,
        "price": 35000,
        "description": "지하 암반수로 빚은 깔끔하고 향긋한 전통 청주입니다.",
        "description_image_url": "https://cdn.example.com/products/cheongju1-desc.jpg",
        **PRODUCT_FEATURES["award_winning"],
    },
    {
        "drink_index": 2,
        "price": 45000,
        "description": "100년 전통 한옥에서 천천히 증류한 프리미엄 소주입니다.",
        "description_image_url": "https://cdn.example.com/products/soju1-desc.jpg",
        **PRODUCT_FEATURES["limited_premium"],
    },
    {
        "drink_index": 3,
        "price": 28000,
        "original_price": 32000,
        "discount": 4000,
        "description": "국내산 복분자로 만든 달콤하고 상큼한 과실주입니다.",
        "description_image_url": "https://cdn.example.com/products/bokbunja-desc.jpg",
        **PRODUCT_FEATURES["organic_gift"],
    },
]

# 패키지 상품 데이터
PACKAGE_PRODUCT_DATA = [
    {
        "package_index": 0,
        "price": 45000,
        "original_price": 53000,
        "discount": 8000,
        "description": "전통주 입문자를 위한 큐레이티드 세트입니다.",
        "description_image_url": "https://cdn.example.com/products/starter-set-desc.jpg",
        "is_gift_suitable": True,
        "is_premium": False,
    },
    {
        "package_index": 1,
        "price": 95000,
        "original_price": 108000,
        "discount": 13000,
        "description": "엄선된 프리미엄 전통주 컬렉션입니다.",
        "description_image_url": "https://cdn.example.com/products/premium-collection-desc.jpg",
        "is_gift_suitable": True,
        "is_premium": True,
        "is_award_winning": True,
    },
]

# 상품 이미지 데이터
PRODUCT_IMAGE_DATA = [
    {
        "product_type": "individual",
        "product_index": 0,
        "image_url": "https://cdn.example.com/products/makgeolli1-main.jpg",
        "is_main": True,
    },
    {
        "product_type": "individual",
        "product_index": 0,
        "image_url": "https://cdn.example.com/products/makgeolli1-detail.jpg",
        "is_main": False,
    },
    {
        "product_type": "individual",
        "product_index": 1,
        "image_url": "https://cdn.example.com/products/cheongju1-main.jpg",
        "is_main": True,
    },
    {
        "product_type": "individual",
        "product_index": 2,
        "image_url": "https://cdn.example.com/products/soju1-main.jpg",
        "is_main": True,
    },
    {
        "product_type": "individual",
        "product_index": 3,
        "image_url": "https://cdn.example.com/products/bokbunja-main.jpg",
        "is_main": True,
    },
    {
        "product_type": "package",
        "product_index": 0,
        "image_url": "https://cdn.example.com/products/starter-set-main.jpg",
        "is_main": True,
    },
    {
        "product_type": "package",
        "product_index": 1,
        "image_url": "https://cdn.example.com/products/premium-collection-main.jpg",
        "is_main": True,
    },
]

# 사용자 데이터
USER_DATA = [
    {
        "nickname": "testuser1",
        "email": "test1@example.com",
        "password": "testpass123",
        "is_adult": True,
        "notification_agreed": True,
    },
    {
        "nickname": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123",
        "is_adult": True,
        "notification_agreed": False,
    },
]


# 상품 생성용 테스트 데이터 (통합된 구조)
def get_individual_product_creation_data(brewery_id):
    """개별 상품 생성 데이터 생성 함수"""
    return {
        "drink_info": {
            "name": "신제품막걸리",
            "brewery_id": brewery_id,
            "ingredients": "쌀(국산 100%), 누룩, 정제수",
            "alcohol_type": "MAKGEOLLI",
            "abv": 6.0,
            "volume_ml": 750,
            **TASTE_PROFILES["makgeolli_sweet"],
        },
        "price": 15000,
        "original_price": 18000,
        "discount": 3000,
        "description": "부드럽고 달콤한 프리미엄 막걸리입니다.",
        "description_image_url": "https://cdn.example.com/desc.jpg",
        **PRODUCT_FEATURES["premium_gift"],
        "images": [
            {"image_url": "https://cdn.example.com/main.jpg", "is_main": True},
            {"image_url": "https://cdn.example.com/detail.jpg", "is_main": False},
        ],
    }


def get_package_product_creation_data(drink_ids):
    """패키지 상품 생성 데이터 생성 함수"""
    return {
        "package_info": {
            "name": "나만의 전통주 세트",
            "type": "MY_CUSTOM",
            "drink_ids": drink_ids,
        },
        "price": 80000,
        "original_price": 95000,
        "discount": 15000,
        "description": "엄선된 3종의 전통주를 담은 프리미엄 세트입니다.",
        "description_image_url": "https://cdn.example.com/package-desc.jpg",
        "is_gift_suitable": True,
        "is_premium": True,
        "images": [{"image_url": "https://cdn.example.com/package-main.jpg", "is_main": True}],
    }
