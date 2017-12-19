from django.shortcuts import render
from django.views.generic import ListView
from .models import Order
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview,\
filter_queryset_from_request
from .serializers import OrderSerializer
from rest_framework.generics import ListAPIView

# Create your views here.


class OrderListView(ListView):
	def get_queryset(self):
		# queryset = Order.objects.all()
		queryset = filter_queryset_from_request(self.request, Order)
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(OrderListView, self).get_context_data(*args, **kwargs)
		context["title"] = "Bestellung"

		# context["field_names"] = get_field_names(context["object_list"], ["id"])
		# context["object_list_as_json"] = get_queries_as_json(context["object_list"])

		set_field_names_onview(context["object_list"], ["id"], context, Order)

		set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

		context["option_fields"] = {"status": ["WARENEINGANG", "WARENAUSGANG"]}

		return context

class OrderListAPIView(ListAPIView):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer