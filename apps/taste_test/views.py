# apps/taste_test/views.py

import logging
from datetime import datetime, timedelta

from django.core.cache import cache
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TasteTest, TasteType, UserProfile
from .serializers import (
    TasteResultSerializer,
    TasteTestQuestionsListSerializer,
    TasteTestSubmitSerializer,
    TasteTypeSerializer,
    UserProfileSerializer,
)
from .services import TasteAnalysisError, TasteTestError

logger = logging.getLogger(__name__)


class TasteTestQuestionsView(APIView):
    """맛 테스트 질문 목록 조회"""

    permission_classes = [permissions.AllowAny]

    @method_decorator(cache_page(60 * 15))  # 15분 캐싱
    def get(self, request):
        """활성화된 테스트의 질문 목록 반환"""
        try:
            # 활성화된 테스트 조회
            test = TasteTest.objects.filter(is_active=True).first()
            if not test:
                return Response({"error": "현재 이용 가능한 테스트가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

            # 직렬화
            serializer = TasteTestQuestionsListSerializer({"test": test})
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"테스트 질문 조회 오류: {e}")
            return Response(
                {"error": "질문을 불러오는 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TasteTestSubmitView(APIView):
    """맛 테스트 제출 및 결과 분석 (회원만)"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """테스트 답변 제출 및 결과 반환"""
        try:
            # 요청 데이터 검증
            serializer = TasteTestSubmitSerializer(data=request.data, context={"request": request})

            if not serializer.is_valid():
                return Response(
                    {"error": "입력 데이터가 올바르지 않습니다.", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 테스트 분석 및 저장
            result = serializer.save()

            # 결과 직렬화
            result_serializer = TasteResultSerializer(result)

            return Response(
                {"message": "맛 테스트가 완료되었습니다.", "result": result_serializer.data},
                status=status.HTTP_201_CREATED,
            )

        except TasteTestError as e:
            logger.error(f"맛 테스트 오류: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except TasteAnalysisError as e:
            logger.error(f"맛 분석 오류: {e}")
            return Response(
                {"error": "맛 유형 분석 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error(f"예상치 못한 오류: {e}")
            return Response(
                {"error": "서비스 처리 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UserTasteProfileView(APIView):
    """사용자 맛 프로필 조회 (회원만)"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """맛 프로필 조회"""
        try:
            # 프로필 조회 또는 생성
            profile, created = UserProfile.objects.get_or_create(user=request.user, defaults={})

            if created:
                logger.info(f"새 사용자 프로필 생성: {request.user.id}")

            # 직렬화
            serializer = UserProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"프로필 조회 오류: {e}")
            return Response({"error": "사용자 프로필을 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)


class TasteTestStatisticsView(APIView):
    """맛 테스트 통계 조회 (관리자용)"""

    permission_classes = [permissions.IsAdminUser]

    @method_decorator(cache_page(60 * 30))  # 30분 캐싱
    def get(self, request):
        """테스트 통계 반환"""
        try:
            # 캐시에서 먼저 확인
            cache_key = "taste_test_statistics"
            stats = cache.get(cache_key)

            if not stats:
                # 통계 계산
                total_tests = UserProfile.objects.filter(taste_test_completed_at__isnull=False).count()

                # 유형별 분포
                type_distribution = (
                    UserProfile.objects.filter(taste_test_completed_at__isnull=False, initial_taste_type__isnull=False)
                    .values("initial_taste_type__type_name")
                    .annotate(count=Count("id"))
                    .order_by("-count")
                )

                # 혼합형 분석 (test_results에서 추출)
                mixed_types = []
                profiles_with_mixed = UserProfile.objects.filter(
                    taste_test_completed_at__isnull=False, test_results__result_data__type_count=2
                )

                mixed_count = 0
                for profile in profiles_with_mixed:
                    if "result_data" in profile.test_results:
                        primary_type = profile.test_results["result_data"].get("primary_type", "")
                        if "×" in primary_type:
                            mixed_count += 1

                # 최근 30일 테스트 수
                thirty_days_ago = datetime.now() - timedelta(days=30)
                recent_tests = UserProfile.objects.filter(taste_test_completed_at__gte=thirty_days_ago).count()

                # 평균 점수 계산
                average_scores = {}
                taste_types = ["달콤과일", "상큼톡톡", "목적여운", "깔끔고소", "미식가"]

                for taste_type in taste_types:
                    profiles = UserProfile.objects.filter(
                        taste_test_completed_at__isnull=False, test_results__type_scores__has_key=taste_type
                    )

                    total_score = 0
                    count = 0
                    for profile in profiles:
                        if "type_scores" in profile.test_results:
                            score = profile.test_results["type_scores"].get(taste_type, 0)
                            total_score += score
                            count += 1

                    average_scores[taste_type] = round(total_score / count, 1) if count > 0 else 0.0

                # 일별 통계 (최근 7일)
                daily_tests = []
                for i in range(7):
                    date = datetime.now().date() - timedelta(days=6 - i)
                    count = UserProfile.objects.filter(taste_test_completed_at__date=date).count()
                    daily_tests.append({"date": date.strftime("%Y-%m-%d"), "count": count})

                # 유형별 분포에 혼합형 추가
                type_list = list(type_distribution)
                if mixed_count > 0:
                    type_list.append(
                        {
                            "type_name": "혼합형",
                            "count": mixed_count,
                            "percentage": round((mixed_count / total_tests * 100), 1) if total_tests > 0 else 0,
                        }
                    )

                # 퍼센티지 계산
                for item in type_list:
                    if "percentage" not in item:
                        item["percentage"] = round((item["count"] / total_tests * 100), 1) if total_tests > 0 else 0

                stats = {
                    "total_completed_tests": total_tests,
                    "recent_tests_30_days": recent_tests,
                    "type_distribution": type_list,
                    "completion_rate": self._calculate_completion_rate(),
                    "average_scores": average_scores,
                    "daily_tests_last_week": daily_tests,
                }

                # 캐시에 저장 (30분)
                cache.set(cache_key, stats, 60 * 30)

            return Response(stats, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"통계 조회 오류: {e}")
            return Response(
                {"error": "통계 조회 중 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_completion_rate(self):
        """테스트 완료율 계산"""
        try:
            from django.contrib.auth import get_user_model

            User = get_user_model()

            total_users = User.objects.count()
            completed_users = User.objects.filter(taste_profile__taste_test_completed_at__isnull=False).count()

            if total_users > 0:
                return round((completed_users / total_users) * 100, 2)
            return 0.0

        except Exception:
            return 0.0


@api_view(["GET"])
@permission_classes([permissions.AllowAny])
def taste_types_list(request):
    """맛 타입 목록 조회"""
    try:
        taste_types = TasteType.objects.all().order_by("type_name")
        serializer = TasteTypeSerializer(taste_types, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"맛 타입 목록 조회 오류: {e}")
        return Response({"error": "서버 내부 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
