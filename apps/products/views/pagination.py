# apps/products/views/pagination.py

from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """표준 페이지네이션 - 일반적인 목록용"""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class MainPagePagination(PageNumberPagination):
    """메인페이지용 페이지네이션 (8개)"""

    page_size = 8
    page_size_query_param = "page_size"
    max_page_size = 20


class SearchPagination(PageNumberPagination):
    """검색/패키지페이지용 페이지네이션 (16개)"""

    page_size = 16
    page_size_query_param = "page_size"
    max_page_size = 100
