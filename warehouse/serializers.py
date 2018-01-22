from rest_framework import serializers
from .models import Warehouse


class WarehouseSerializer(serializers.ModelSerializer):
    # # str = serializers.SerializerMethodField("name")

    # # def name(self, object):
    # # 	return (str(object))

    # # def nameF(self, object):r
    # return (str(object))

    class Meta:
        model = Warehouse
        fields = "__all__"
