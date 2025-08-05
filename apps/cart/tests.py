import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from apps.cart.models import Cart
from apps.products.models import Brewery, Product

User = get_user_model()


class CartAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create(nickname="testuser")
        self.brewery = Brewery.objects.create(name="Test Brewery")

        self.product1 = Product.objects.create(
            name="Product 1", price=10000, brewery=self.brewery, description="Desc 1",
            ingredients="Ingr 1", alcohol_content=10.0, volume_ml=360, id=uuid.uuid4()
        )
        self.product2 = Product.objects.create(
            name="Product 2", price=20000, brewery=self.brewery, description="Desc 2",
            ingredients="Ingr 2", alcohol_content=12.5, volume_ml=500, id=uuid.uuid4()
        )

        self.cart_url = "/api/v1/cart/"
        self.add_item_url = "/api/v1/cart/add-item/"
        self.update_item_url = "/api/v1/cart/update-item/"
        self.remove_item_url = "/api/v1/cart/remove-item/"

    def test_get_empty_cart(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.cart_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)

    def test_add_new_single_item(self):
        self.client.force_authenticate(user=self.user)
        request_data = {"product_id": str(self.product1.id), "quantity": 2}
        response = self.client.post(self.add_item_url, request_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)
