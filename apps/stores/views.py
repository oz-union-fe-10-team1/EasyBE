from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.stores.models import Store
from apps.stores.serializers import StoreSerializer


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [AllowAny]
