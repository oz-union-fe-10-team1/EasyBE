from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import PreferTasteProfile
from apps.users.serializers import TasteProfileSerializer
from apps.users.utils.taste_analysis import TasteAnalysisService


class TasteProfileView(APIView):
    """
    사용자 취향 프로필 조회 API
    GET /api/v1/users/taste-profile/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # 1. 사용자 취향 프로필 조회 또는 생성
            profile, created = PreferTasteProfile.objects.get_or_create(user=request.user)

            # 2. 분석 업데이트가 필요한지 확인
            if profile.needs_analysis_update():
                # 3. AI 분석 실행 (규칙 기반)
                analysis_description = TasteAnalysisService.generate_analysis(profile)
                profile.update_analysis(analysis_description)

            # 4. 응답 데이터 구성
            serializer = TasteProfileSerializer(profile)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"취향 프로필 조회 중 오류가 발생했습니다: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
