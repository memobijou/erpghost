from rest_framework import serializers
from .models import Order,PositionProductOrder,PositionProductOrderPicklist
from .models import Picklist


class OrderSerializer(serializers.ModelSerializer):
    str = serializers.SerializerMethodField("name")

    def name(self, object):
        return (str(object))

    class Meta:
        model = Order
        fields = ("id", "str", "delivery_date", "ordernumber")  # ("ean", ... )


class PositionProductOrderPicklistSerializer(serializers.ModelSerializer):

    anzahl = serializers.SerializerMethodField("getanzahl")
    positions = serializers.SerializerMethodField("getpositions")
    prdocut = serializers.SerializerMethodField("getprdocut")
    status = serializers.SerializerMethodField("getstatus")

    def getanzahl(self, object):
        return object.positionproductorder.amount

    def getpositions(self, object):
        return str(object.positionproductorder.positions)

    def getprdocut(self, object):
        return str(object.positionproductorder.productorder.product)

    def getorder(self, object):
        return str(object.positionproductorder.productorder.order)

    def getstatus(self, object):
        return str(object.positionproductorder.status)

    class Meta:
        model = PositionProductOrderPicklist
        fields = ("anzahl","comment","positions","prdocut","belegt","status")


class PositionProductOrderSerializer(serializers.ModelSerializer):

    comment = serializers.SerializerMethodField("getcomment")
    complete = serializers.SerializerMethodField("getcomplete")
    end_time = serializers.SerializerMethodField("getend_time")
    start_time = serializers.SerializerMethodField("getstart_time")
    status = serializers.SerializerMethodField("getstatus")

    artikeln= PositionProductOrderPicklistSerializer(many=True)

    def name(self, object):
        return (str(object))

    def getcomment(self, object):
        return object.comment

    def getcomplete(self, object):
        return object.complete

    def getend_time(self, object):
        return object.end_time

    def getstart_time(self, object):
        return object.start_time

    def getstatus(self, object):
        return object.status



    class Meta:
        model = Picklist
        fields = ("id","bestellungsnummer","artikeln","comment","complete","end_time","start_time","status")