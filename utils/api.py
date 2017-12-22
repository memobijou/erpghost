from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from product.models import Product

def match_product(request, ean_sku):
	if len(ean_sku) == 13:
		products = Product.objects.filter(ean=ean_sku)
		print(products)
		if products.exists():
			return JsonResponse({"match": True, "id": products[0].id})
	elif(len(ean_sku) == 7):
		pass
	return JsonResponse({"match": False})