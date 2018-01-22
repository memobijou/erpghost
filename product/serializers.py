from rest_framework import serializers
from .models import Product
from order.models import ProductOrder
from rest_framework.serializers import ModelSerializer


class ProductSerializer(serializers.ModelSerializer):
    str = serializers.SerializerMethodField("name")
    str1 = serializers.SerializerMethodField("nameF")

    def name(self, object):
        return (str(object))

    def nameF(self, object):
        return (str(object))

    class Meta:
        model = Product
        fields = ("id", "ean", "str", "str1")  # ("ean", ... )


class IncomeSerializer(ModelSerializer):
    class Meta:
        model = ProductOrder
        fields = ("id", "product", "order", "amount", "confirmed")  # ("ean", ... )
