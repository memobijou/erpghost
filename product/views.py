from django.shortcuts import render
from django.views.generic import ListView
#from .models import Product

# Create your views here.

class ProductListView(ListView):
    pass
	#def get_queryset(self):
		#queryset = Product.objects.all()
		#return queryset