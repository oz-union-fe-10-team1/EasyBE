"""
취향 테스트 관련 뷰 - 단계별 처리 과정 명시
"""

from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import PreferenceTestResult
from ..serializers import (
    TasteTestAnswersSerializer,
    TasteTestResultSerializer,
)
from ..services.controller_support import ControllerService


class TasteTestQuestionsView(APIView):
    """취향 테스트 질문 목록 조회"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="테스트 질문 목록",
        description="취향 테스트용 6개 질문을 반환합니다",
        tags=["테스트"],
    )
    def get(self, request):
        """질문 목록 조회"""
        # 1. 서비스에서 질문 데이터 조회
        questions = ControllerService.get_test_questions()

        # 2. 응답 반환
        return Response(questions, status=status.HTTP_200_OK)


class TasteTestSubmitView(APIView):
    """취향 테스트 답변 제출"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="테스트 답변 제출",
        description="6개 질문에 대한 답변을 제출하고 취향 유형을 분석합니다. 로그인한 사용자의 경우 결과가 자동 저장됩니다.",
        request=TasteTestAnswersSerializer,
        tags=["테스트"],
    )
    def post(self, request):
        """테스트 답변 제출"""
        # 1. 데이터 검증 (Serializer 활용)
        serializer = TasteTestAnswersSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. 검증된 데이터로 비즈니스 로직 처리
        validated_answers = serializer.validated_data["answers"]
        result = ControllerService.submit_test_answers(request.user, validated_answers)

        # 3. 결과 반환 (CORS 헤더 추가)
        response = Response(result, status=status.HTTP_201_CREATED)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

    def options(self, request):
        """CORS preflight 요청 처리"""
        response = Response(status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response


class TasteTestRetakeView(APIView):
    """테스트 재응시"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="테스트 재응시",
        description="기존 테스트 결과를 새로운 답변으로 업데이트합니다",
        request=TasteTestAnswersSerializer,
        responses={
            200: TasteTestResultSerializer,
            400: {"description": "잘못된 요청"},
            404: {
                "description": "기존 결과 없음",
                "example": {"message": "기존 테스트 결과가 없습니다. /submit/ 을 이용해주세요."},
            },
        },
        tags=["테스트"],
    )
    def put(self, request):
        """테스트 재응시"""
        # 1. 데이터 검증 (Serializer 활용)
        serializer = TasteTestAnswersSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # 2. 검증된 데이터로 재테스트 처리
        validated_answers = serializer.validated_data["answers"]
        try:
            result = ControllerService.retake_test(request.user, validated_answers)
        except PreferenceTestResult.DoesNotExist:
            return Response(
                {"message": "기존 테스트 결과가 없습니다. /submit/ 을 이용해주세요."}, status=status.HTTP_404_NOT_FOUND
            )

        # 3. 결과 반환 (CORS 헤더 추가)
        response = Response(result, status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "PUT, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response

    def options(self, request):
        """CORS preflight 요청 처리"""
        response = Response(status=status.HTTP_200_OK)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "PUT, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response
