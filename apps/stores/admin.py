from django.contrib import admin

from .models import ProductStock, Store

# Register your models here.
admin.site.register(Store)
admin.site.register(ProductStock)
