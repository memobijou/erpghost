from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView
from .models import Order, ProductOrder
from .forms import OrderForm
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview,\
filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview
from .serializers import OrderSerializer
from rest_framework.generics import ListAPIView
from django.forms import modelform_factory, inlineformset_factory
from django import forms

# Create your views here.

class OrderCreateView(CreateView):
	template_name = "order/form.html"
	form_class = OrderForm

	def get_context_data(self, *args, **kwargs):
		context = super(OrderCreateView, self).get_context_data(*args, **kwargs)
		context["title"] = "Bestellung anlegen"
		context["product_match"] = "Product"
		formset_class = inlineformset_factory(Order, ProductOrder, can_delete=False, extra=3, exclude=["id"])

		if self.request.POST:
			formset = formset_class(self.request.POST, self.request.FILES, instance=self.object)
		else:
			formset = formset_class(instance=self.object)

		context["formset"] = formset
		return context

	def form_valid(self, form, *args, **kwargs):
		self.object = form.save()

		context = self.get_context_data(*args, **kwargs)
		formset = context["formset"]

		if formset.is_valid():
			formset.save()
		else:
			return render(self.request, self.template_name, context)

		return HttpResponseRedirect(self.get_success_url())


class OrderDetailView(DetailView):
	
	def get_object(self):
		obj = get_object_or_404(Order, pk=self.kwargs.get("pk"))
		return obj

	def get_context_data(self, *args, **kwargs):
		context = super(OrderDetailView, self).get_context_data(*args, **kwargs)
		context["title"] = "Bestellung " + context["object"].ordernumber
		set_object_ondetailview(context, Order, ["id"], [], {"products": ["id"]})
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