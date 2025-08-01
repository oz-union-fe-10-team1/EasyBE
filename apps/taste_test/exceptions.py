# apps/taste_test/exceptions.py


class TasteTestException(Exception):
    """맛 테스트 관련 기본 예외"""

    pass


class TasteTestError(TasteTestException):
    """맛 테스트 관련 오류"""

    pass


class TasteAnalysisError(TasteTestException):
    """맛 분석 관련 오류"""

    pass


class InvalidTasteDataError(TasteTestException):
    """잘못된 맛 데이터 오류"""

    pass
