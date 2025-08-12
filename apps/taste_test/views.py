from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PreferenceTestResult
from .serializers import (
    PreferenceTestResultProfileSerializer,
    PreferenceTestResultSerializer,
    TasteTestAnswersSerializer,
    TasteTestResultSerializer,
    TasteTypeInfoSerializer,
)
from .services import TasteTestData, TasteTestService


class TasteTestQuestionsView(APIView):
    """취향 테스트 질문 목록 조회"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="테스트 질문 목록",
        description="취향 테스트용 6개 질문을 반환합니다",
        responses={
            200: {
                "description": "질문 목록",
                "example": [
                    {
                        "id": "Q1",
                        "question": "카페에 가면 주로 시키는 메뉴는?",
                        "options": {
                            "A": "달콤한 바닐라 라떼나 과일 에이드",
                            "B": "깔끔한 아메리카노나 고소한 곡물 라떼",
                        },
                    }
                ],
            }
        },
        tags=["테스트"],
    )
    def get(self, request):
        questions = TasteTestService.get_questions()
        return Response(questions, status=status.HTTP_200_OK)


class TasteTestSubmitView(APIView):
    """취향 테스트 답변 제출"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="테스트 답변 제출",
        description="6개 질문에 대한 답변을 제출하고 취향 유형을 분석합니다. 로그인한 사용자의 경우 결과가 자동 저장됩니다.",
        request=TasteTestAnswersSerializer,
        responses={
            201: OpenApiResponse(
                response=TasteTestResultSerializer,
                description="테스트 결과",
                examples=[
                    OpenApiExample(
                        "성공 응답",
                        value={
                            "type": "달콤과일파",
                            "scores": {"달콤과일파": 3, "상큼톡톡파": 1, "묵직여운파": 1, "깔끔고소파": 1},
                            "info": {
                                "name": "달콤과일파",
                                "enum": "SWEET_FRUIT",
                                "description": "당신은 부드럽고 달콤한 맛에서 행복을 느끼는군요!",
                                "characteristics": ["달콤함", "과일향", "로맨틱", "부드러움"],
                                "image_url": "images/types/sweet_fruit.png",
                            },
                            "saved": True,
                        },
                    )
                ],
            ),
            400: {
                "description": "잘못된 요청",
                "example": {"errors": {"missing_questions": ["다음 질문에 답변해주세요: Q1, Q2"]}},
            },
        },
        tags=["테스트"],
    )
    def post(self, request):
        answers = request.data.get("answers", {})

        # 답변 유효성 검증
        errors = TasteTestService.validate_answers(answers)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # 테스트 결과 계산
        result = TasteTestService.process_taste_test(answers)

        # 로그인 사용자의 경우 DB 저장
        saved = False
        if request.user.is_authenticated:
            try:
                TasteTestService.save_test_result(request.user, answers)
                saved = True
            except Exception:
                # 저장 실패해도 결과는 반환
                pass

        result["saved"] = saved
        return Response(result, status=status.HTTP_201_CREATED)


class TasteTestResultView(APIView):
    """사용자 테스트 결과 조회"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="내 테스트 결과 조회",
        description="로그인한 사용자의 저장된 취향 테스트 결과를 조회합니다",
        responses={
            200: PreferenceTestResultSerializer,
            404: {"description": "테스트 결과 없음", "example": {"message": "아직 테스트를 완료하지 않았습니다."}},
        },
        tags=["사용자"],
    )
    def get(self, request):
        try:
            result = PreferenceTestResult.objects.select_related("user").get(user=request.user)
            serializer = PreferenceTestResultSerializer(result)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PreferenceTestResult.DoesNotExist:
            return Response({"message": "아직 테스트를 완료하지 않았습니다."}, status=status.HTTP_404_NOT_FOUND)


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
        # 기존 결과 확인
        try:
            PreferenceTestResult.objects.get(user=request.user)
        except PreferenceTestResult.DoesNotExist:
            return Response(
                {"message": "기존 테스트 결과가 없습니다. /submit/ 을 이용해주세요."}, status=status.HTTP_404_NOT_FOUND
            )

        # 답변 검증
        answers = request.data.get("answers", {})
        errors = TasteTestService.validate_answers(answers)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # 결과 업데이트
        TasteTestService.save_test_result(request.user, answers)
        result = TasteTestService.process_taste_test(answers)
        result["saved"] = True

        return Response(result, status=status.HTTP_200_OK)


class UserProfileView(APIView):
    """사용자 프로필 조회"""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="사용자 프로필",
        description="로그인한 사용자의 기본 정보와 테스트 완료 여부를 조회합니다. 테스트 완료시 상세 결과 포함 (답변 내역 제외).",
        responses={
            200: {
                "description": "사용자 프로필",
                "example": {
                    "user": "사용자닉네임",
                    "has_test": True,
                    "result": {
                        "id": 1,
                        "user_nickname": "사용자닉네임",
                        "prefer_taste": "SWEET_FRUIT",
                        "prefer_taste_display": "달콤과일파",
                        "taste_description": "당신은 부드럽고 달콤한 맛에서 행복을 느끼는군요!",
                        "image_url": "images/types/sweet_fruit.png",
                        "created_at": "2024-01-01T00:00:00Z",
                    },
                },
            }
        },
        tags=["사용자"],
    )
    def get(self, request):
        has_test = hasattr(request.user, "preference_test_result")

        data = {"user": request.user.nickname, "has_test": has_test}

        if has_test:
            serializer = PreferenceTestResultProfileSerializer(request.user.preference_test_result)
            data["result"] = serializer.data

        return Response(data, status=status.HTTP_200_OK)


class TasteTypesView(APIView):
    """취향 유형 목록 조회"""

    permission_classes = [AllowAny]

    @extend_schema(
        summary="취향 유형 목록",
        description="9가지 취향 유형의 상세 정보를 조회합니다",
        responses={
            200: {
                "description": "유형 목록",
                "example": {
                    "types": [
                        {
                            "name": "달콤과일파",
                            "enum": "SWEET_FRUIT",
                            "description": "당신은 부드럽고 달콤한 맛에서 행복을 느끼는군요!",
                            "characteristics": ["달콤함", "과일향", "로맨틱", "부드러움"],
                            "image_url": "images/types/sweet_fruit.png",
                        }
                    ],
                    "total": 9,
                },
            }
        },
        tags=["정보"],
    )
    def get(self, request):
        types_data = list(TasteTestData.TYPE_INFO.values())
        return Response({"types": types_data, "total": len(types_data)}, status=status.HTTP_200_OK)
