from rest_framework import serializers
from .models import Order


class OrderSerializer(serializers.ModelSerializer):
    str = serializers.SerializerMethodField("name")

    def name(self, object):
        return (str(object))

    class Meta:
        model = Order
        fields = ("id", "str", "delivery_date", "ordernumber")  # ("ean", ... )
