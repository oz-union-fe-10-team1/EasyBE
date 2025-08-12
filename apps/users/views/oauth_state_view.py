import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..serializers import StateSerializer
from ..utils.cache_oauth_state import OAuthStateService

logger = logging.getLogger(__name__)


class OAuthStateView(APIView):
    """
    OAuth State 저장 API
    POST /api/v1/auth/state
    """

    serializer_class = StateSerializer

    def post(self, request):
        serializer = StateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        state_value = serializer.validated_data["state"]

        try:
            # Redis에 state 저장
            OAuthStateService.save_state(state_value)

            return Response({"message": "State saved successfully"}, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Failed to save OAuth state: {e}")
            return Response({"error": "Failed to save state"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
