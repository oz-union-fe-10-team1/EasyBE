# # apps/products/views/product.py
#
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework import permissions, status, viewsets
# from rest_framework.decorators import action
# from rest_framework.filters import OrderingFilter, SearchFilter
# from rest_framework.pagination import PageNumberPagination
# from rest_framework.response import Response
#
# from apps.products.models import Product
# from apps.products.serializers import (
#     ProductCreateSerializer,
#     ProductDetailSerializer,
#     ProductListSerializer,
#     ProductUpdateSerializer,
# )
#
# from ..utils.filters import ProductFilter
# from ..utils.permissions import IsAdminOrReadOnly
#
#
# class ProductPagination(PageNumberPagination):
#     """제품 목록 페이지네이션"""
#
#     page_size = 20
#     page_size_query_param = "page_size"
#     max_page_size = 100
#
#
# class ProductViewSet(viewsets.ModelViewSet):
#     """
#     제품 CRUD ViewSet
#
#     list: 제품 목록 조회 (필터링, 검색, 정렬 지원)
#     retrieve: 제품 상세 조회
#     create: 제품 생성 (관리자만)
#     update: 제품 수정 (관리자만)
#     destroy: 제품 삭제 (관리자만)
#     """
#
#     queryset = (
#         Product.objects.select_related("brewery", "alcohol_type", "region", "category")
#         .prefetch_related("images", "taste_tags", "producttastetag_set__taste_tag")
#         .all()
#     )
#
#     # 권한: 조회는 모든 사용자, 생성/수정/삭제는 관리자만
#     permission_classes = [IsAdminOrReadOnly]
#
#     # 페이지네이션 설정
#     pagination_class = ProductPagination
#
#     # 필터링, 검색, 정렬
#     filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
#     filterset_class = ProductFilter
#     search_fields = ["name", "description", "flavor_notes"]
#     ordering_fields = [
#         "price",
#         "alcohol_content",
#         "created_at",
#         "order_count",
#         "average_rating",
#         "view_count",
#         "like_count",
#     ]
#     ordering = ["-created_at"]  # 기본 정렬: 최신순
#
#     def get_serializer_class(self):
#         """액션에 따른 Serializer 선택"""
#         if self.action == "list":
#             return ProductListSerializer
#         elif self.action == "create":
#             return ProductCreateSerializer
#         elif self.action in ["update", "partial_update"]:
#             return ProductUpdateSerializer
#         else:  # retrieve
#             return ProductDetailSerializer
#
#     def get_queryset(self):
#         """쿼리셋 최적화 및 필터링"""
#         queryset = self.queryset
#
#         # 관리자가 아닌 경우 활성 상태 제품만 조회
#         if not (
#             self.request.user.is_authenticated
#             and hasattr(self.request.user, "role")
#             and self.request.user.role == "ADMIN"
#         ):
#             queryset = queryset.filter(status="active")
#
#         return queryset
#
#     def perform_create(self, serializer):
#         """제품 생성 시 추가 로직"""
#         # 기본값 설정
#         product = serializer.save()
#
#         # 생성 로그 (향후 확장 가능)
#         # logger.info(f"Product created: {product.name} by {self.request.user}")
#
#     def perform_update(self, serializer):
#         """제품 수정 시 추가 로직"""
#         product = serializer.save()
#
#         # 수정 로그 (향후 확장 가능)
#         # logger.info(f"Product updated: {product.name} by {self.request.user}")
#
#     def retrieve(self, request, *args, **kwargs):
#         """제품 상세 조회 (조회수 증가)"""
#         instance = self.get_object()
#
#         # 조회수 증가 (관리자 제외)
#         if not (request.user.is_authenticated and hasattr(request.user, "role") and request.user.role == "ADMIN"):
#             instance.increment_view_count()
#
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def popular(self, request):
#         """인기 제품 목록 (주문수 + 조회수 기준)"""
#         popular_products = self.get_queryset().filter(status="active").order_by("-order_count", "-view_count")
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(popular_products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(popular_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def featured(self, request):
#         """추천 제품 목록 (is_featured=True)"""
#         featured_products = self.get_queryset().filter(status="active", is_featured=True).order_by("-created_at")
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(featured_products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(featured_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def award_winning(self, request):
#         """수상 제품 목록 (is_award_winning=True)"""
#         award_products = self.get_queryset().filter(status="active", is_award_winning=True).order_by("-created_at")
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(award_products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(award_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def regional_specialty(self, request):
#         """지역 특산물 제품 목록 (is_regional_specialty=True)"""
#         regional_products = (
#             self.get_queryset().filter(status="active", is_regional_specialty=True).order_by("-created_at")
#         )
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(regional_products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(regional_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def by_type(self, request):
#         """주류 타입별 제품 목록"""
#         alcohol_type_id = request.query_params.get("alcohol_type")
#
#         queryset = self.get_queryset().filter(status="active")
#
#         if alcohol_type_id:
#             try:
#                 alcohol_type_id = int(alcohol_type_id)
#                 queryset = queryset.filter(alcohol_type_id=alcohol_type_id)
#             except (ValueError, TypeError):
#                 # 잘못된 타입 ID인 경우 빈 결과 반환
#                 queryset = queryset.none()
#
#         queryset = queryset.order_by("-created_at")
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(queryset)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(queryset, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def new(self, request):
#         """신제품 목록 (최신순)"""
#         new_products = self.get_queryset().filter(status="active").order_by("-created_at")
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(new_products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(new_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
#     def liked(self, request):
#         """내가 좋아요한 제품 목록"""
#         from apps.products.models import ProductLike
#
#         # 사용자가 좋아요한 제품들 조회
#         liked_product_ids = ProductLike.objects.filter(user=request.user).values_list("product_id", flat=True)
#
#         liked_products = (
#             self.get_queryset().filter(id__in=liked_product_ids, status="active").order_by("-productlike__created_at")
#         )  # 최신 좋아요 순
#
#         # 페이지네이션 적용
#         page = self.paginate_queryset(liked_products)
#         if page is not None:
#             serializer = ProductListSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#
#         serializer = ProductListSerializer(liked_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
#     def like(self, request, pk=None):
#         """제품 좋아요/취소 토글"""
#         from django.db import models
#
#         from apps.products.models import ProductLike
#
#         product = self.get_object()
#
#         # 기존 좋아요 확인
#         like_obj, created = ProductLike.objects.get_or_create(user=request.user, product=product)
#
#         if created:
#             # 새로운 좋아요 생성
#             Product.objects.filter(id=product.id).update(like_count=models.F("like_count") + 1)
#             product.refresh_from_db()
#
#             return Response(
#                 {"message": "제품을 좋아요했습니다.", "liked": True, "like_count": product.like_count},
#                 status=status.HTTP_201_CREATED,
#             )
#         else:
#             # 기존 좋아요 취소
#             like_obj.delete()
#             Product.objects.filter(id=product.id).update(like_count=models.F("like_count") - 1)
#             product.refresh_from_db()
#
#             return Response(
#                 {"message": "좋아요를 취소했습니다.", "liked": False, "like_count": product.like_count},
#                 status=status.HTTP_200_OK,
#             )
#
#     @action(detail=True, methods=["get"])
#     def similar(self, request, pk=None):
#         """유사 제품 추천"""
#         product = self.get_object()
#
#         # 간단한 유사 제품 로직 (맛 프로필 기반)
#         similar_products = (
#             Product.objects.filter(alcohol_type=product.alcohol_type, status="active")
#             .exclude(id=product.id)
#             .order_by("?")[:5]
#         )  # 임시로 랜덤 5개
#
#         serializer = ProductListSerializer(similar_products, many=True)
#         return Response(serializer.data)
#
#     @action(detail=False, methods=["get"])
#     def filter_options(self, request):
#         """필터링 옵션 정보 제공"""
#         from django.db import models
#
#         queryset = self.get_queryset().filter(status="active")
#
#         filter_options = {
#             "price_range": {
#                 "min": queryset.aggregate(min_price=models.Min("price"))["min_price"] or 0,
#                 "max": queryset.aggregate(max_price=models.Max("price"))["max_price"] or 0,
#             },
#             "alcohol_content_range": {
#                 "min": queryset.aggregate(min_alcohol=models.Min("alcohol_content"))["min_alcohol"] or 0,
#                 "max": queryset.aggregate(max_alcohol=models.Max("alcohol_content"))["max_alcohol"] or 0,
#             },
#             "taste_ranges": {
#                 "sweetness": {"min": 0.0, "max": 5.0},
#                 "acidity": {"min": 0.0, "max": 5.0},  # sourness → acidity로 수정
#                 "bitterness": {"min": 0.0, "max": 5.0},
#                 "body": {"min": 0.0, "max": 5.0},
#                 "carbonation": {"min": 0.0, "max": 5.0},
#                 "aroma": {"min": 0.0, "max": 5.0},
#             },
#             "regions": list(
#                 queryset.values_list("region__name", flat=True).distinct().exclude(region__name__isnull=True)
#             ),
#             "alcohol_types": list(queryset.values_list("alcohol_type__name", flat=True).distinct()),
#             "categories": list(
#                 queryset.values_list("category__name", flat=True).distinct().exclude(category__name__isnull=True)
#             ),
#             "breweries": list(queryset.values_list("brewery__name", flat=True).distinct()),
#         }
#
#         return Response(filter_options)
