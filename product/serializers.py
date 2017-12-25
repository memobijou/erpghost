from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
	str = serializers.SerializerMethodField("name")
	str1 = serializers.SerializerMethodField("nameF")

	def name(self, object):
		return (str(object))


	def nameF(self, object):
		return (str(object))

	class Meta:
		model = Product
		fields = ("id", "ean", "str","str1") # ("ean", ... )