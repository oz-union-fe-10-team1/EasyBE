"""
취향 유형별 맛 프로필 데이터
"""

# 타입별 기본 맛 프로필 (0.0 ~ 5.0 스케일)
TASTE_PROFILES = {
    "SWEET_FRUIT": {
        "sweetness_level": 4.5,
        "acidity_level": 3.5,
        "body_level": 2.0,
        "carbonation_level": 2.0,
        "bitterness_level": 1.0,
        "aroma_level": 4.0,
    },
    "FRESH_FIZZY": {
        "sweetness_level": 2.0,
        "acidity_level": 4.5,
        "body_level": 2.0,
        "carbonation_level": 4.5,
        "bitterness_level": 1.5,
        "aroma_level": 3.0,
    },
    "HEAVY_LINGERING": {
        "sweetness_level": 2.5,
        "acidity_level": 2.0,
        "body_level": 4.5,
        "carbonation_level": 1.0,
        "bitterness_level": 3.5,
        "aroma_level": 4.0,
    },
    "CLEAN_SAVORY": {
        "sweetness_level": 1.5,
        "acidity_level": 2.0,
        "body_level": 3.0,
        "carbonation_level": 2.5,
        "bitterness_level": 2.0,
        "aroma_level": 2.5,
    },
    "FRAGRANT_NEAT": {
        "sweetness_level": 2.0,
        "acidity_level": 2.5,
        "body_level": 2.5,
        "carbonation_level": 2.0,
        "bitterness_level": 1.5,
        "aroma_level": 4.5,
    },
    "FRESH_CLEAN": {
        "sweetness_level": 2.0,
        "acidity_level": 4.0,
        "body_level": 2.0,
        "carbonation_level": 3.0,
        "bitterness_level": 1.5,
        "aroma_level": 3.0,
    },
    "HEAVY_SWEET": {
        "sweetness_level": 4.5,
        "acidity_level": 2.0,
        "body_level": 4.0,
        "carbonation_level": 1.5,
        "bitterness_level": 2.0,
        "aroma_level": 3.5,
    },
    "SWEET_SAVORY": {
        "sweetness_level": 4.0,
        "acidity_level": 2.0,
        "body_level": 3.5,
        "carbonation_level": 2.0,
        "bitterness_level": 2.5,
        "aroma_level": 3.0,
    },
    "GOURMET": {
        "sweetness_level": 3.0,
        "acidity_level": 3.0,
        "body_level": 3.5,
        "carbonation_level": 2.5,
        "bitterness_level": 3.0,
        "aroma_level": 4.0,
    },
}