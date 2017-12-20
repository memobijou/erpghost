from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView
from .models import Order
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview,\
filter_queryset_from_request, get_query_as_json
from .serializers import OrderSerializer
from rest_framework.generics import ListAPIView
from django.forms import modelform_factory

# Create your views here.

class OrderCreateView(CreateView):
	template_name = "order/form.html"
	form_class = modelform_factory(Order, exclude=('id',))

	def get_context_data(self, *args, **kwargs):
		context = super(OrderCreateView, self).get_context_data(*args, **kwargs)
		context["title"] = "Bestellung anlegen"
		return context

	def form_valid(self, form, *args, **kwargs):
		self.object = form.save()
		return HttpResponseRedirect(self.get_success_url())

class OrderDetailView(DetailView):
	
	def get_object(self):
		obj = get_object_or_404(Order, pk=self.kwargs.get("pk"))
		return obj

	def get_context_data(self, *args, **kwargs):
		context = super(OrderDetailView, self).get_context_data(*args, **kwargs)
		context["title"] = "Bestellung " + context["object"].ordernumber
		set_field_names_onview(context["object"], ["id"], context, Order)
		context["object_as_json"] = get_query_as_json(context["object"])


		return context

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

		set_field_names_onview(context["object_list"], ["id", "products"], context, Order)

		set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

		context["option_fields"] = [{"status": ["WARENEINGANG", "WARENAUSGANG"]}]

		return context

class OrderListAPIView(ListAPIView):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer