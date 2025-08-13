from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from apps.stores.models import Store
from apps.stores.serializers import StoreSerializer


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all().order_by("-created_at")
    serializer_class = StoreSerializer
    permission_classes = [IsAdminUser]