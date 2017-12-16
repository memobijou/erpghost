from django.shortcuts import render
from django.views.generic import ListView
from .models import Order
from utils.utils import get_field_names, get_queries_as_json
from .serializers import OrderSerializer
from rest_framework.generics import ListAPIView

# Create your views here.


class OrderListView(ListView):
	def get_queryset(self):
		queryset = Order.objects.all()
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(OrderListView, self).get_context_data(*args, **kwargs)

		context["field_names"] = get_field_names(context["object_list"], ["id"])
		context["rows"] = get_queries_as_json(context["object_list"])
		context["title"] = "Bestellung"
		return context

class OrderListAPIView(ListAPIView):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer