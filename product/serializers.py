from rest_framework import serializers
from .models import Product
from order.models import ProductOrder
from rest_framework.serializers import ModelSerializer


class ProductSerializer(serializers.ModelSerializer):
    verbose_names = serializers.SerializerMethodField("verbose_names_function")

    def verbose_names_function(self, object):
        verbose_names = {}
        for field in object._meta.get_fields():
            if hasattr(field, "verbose_name"):
                verbose_names[field.attname] = field.verbose_name
        return verbose_names

    class Meta:
        model = Product
        fields = "__all__"


class IncomeSerializer(ModelSerializer):
    class Meta:
        model = ProductOrder
        fields = ("id", "product", "order", "amount", "confirmed")  # ("ean", ... )
