from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
	str = serializers.SerializerMethodField("name")

	def name(self, object):
		return (str(object))

	class Meta:
		model = Product
		fields = ("id", "ean", "str") # ("ean", ... )

