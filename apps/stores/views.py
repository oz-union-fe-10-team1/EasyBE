from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

from apps.stores.models import ProductStock, Store
from apps.stores.serializers import ProductStockSerializer, StoreSerializer


class StoreViewSet(viewsets.ModelViewSet):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAdminUser]


class ProductStockViewSet(viewsets.ModelViewSet):
    queryset = ProductStock.objects.all()
    serializer_class = ProductStockSerializer
    permission_classes = [IsAdminUser]
