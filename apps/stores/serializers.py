from rest_framework import serializers

from apps.stores.models import Store


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            "id",
            "name",
            "address",
            "latitude",
            "longitude",
            "contact",
            "opening_days",
            "opening_hours",
            "closed_days",
            "has_tasting",
            "has_parking",
            "image",
            "status",
        ]
