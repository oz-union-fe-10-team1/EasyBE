# apps/products/views/pagination.py

from rest_framework.pagination import PageNumberPagination


class SearchPagination(PageNumberPagination):
    """검색 페이지용 페이지네이션 (16개)"""

    page_size = 16
    page_size_query_param = "page_size"
    max_page_size = 32
