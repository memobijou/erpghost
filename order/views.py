from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView, FormView
from position.models import Position
from product.models import PositionProduct
from order.models import Order, ProductOrder,Product
from order.forms import OrderForm, ProductOrderFormsetInline
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview,\
filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview,get_model_references
from order.serializers import OrderSerializer
from rest_framework.generics import ListAPIView
from django.forms import modelform_factory, inlineformset_factory
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser

# Create your views here

def post_detail(request,myid):
	allPositions = Position.objects.all()
	print(allPositions)

	print(myid)
	context = {"myid": myid}
	order = Order.objects.get(id=myid)
	productswithamount = []
	products = []
	b = order.productorder_set.all()
	print("myorder" + str(b))
	for x in b:
		print("confirmd" + str(x.confirmed))
		if x.confirmed == True:
			print("produkt"+ str(x))
			a = PositionProduct.objects.filter(status="WE")
			if a.exists() == True:
				for y in a:
					if y.products == x.product:
						status = "WE"
						break
					else:
						status = "kein WE"
					break
			else:
				status="WE"
			
			if status == "WE":
				if hasattr(x.product,"masterdata"):
					i = 0
					while i < x.amount:
						print(i)
						print(x.amount)
						i = i + 1
						gefunden = False
						for p in allPositions:
							if float(p.available_volume) > x.product.masterdata.calc_volume:
								print(x.product.masterdata.calc_volume)
								print("FREIIII-----" + str(p) + "davor " +  str(p.available_volume))
								customPosPro = PositionProduct()
								customPosPro.status = "auf den WEG"
								customPosPro.products  = x.product
								customPosPro.positions = p
								customPosPro.amount = 1
								customPosPro.save()
								print("danach : " + str(p.available_volume))
								productswithamount.append({"product" : x.product,"amount": 1,"Position":p})
								gefunden = True
								break
							if gefunden == False:
								print(x.product.masterdata.calc_volume)
								print("Belegegt-----" + str(p) + "davor " +  str(p.available_volume))
								a = PositionProduct.objects.filter(status="WE")
								if a.exists() == True:
									for y in a:
										if y.products == x.product:
											break
										else:
											customPosPro = PositionProduct()
											customPosPro.status = "WE"
											customPosPro.products  = x.product
											custom = Position.objects.get(level="WE")
											customPosPro.positions = custom
											dif = x.amount - i 
											customPosPro.amount = dif + 1
											customPosPro.save()
											print("Belegegt ------- danach : " + str(p.available_volume))
											break
											productswithamount.append({"product" : x.product,"amount": x.amount,"Position":p})
								else:
									customPosPro = PositionProduct()
									customPosPro.status = "WE"
									customPosPro.products  = x.product
									custom = Position.objects.get(level="WE")
									customPosPro.positions = custom
									dif = x.amount - i 
									customPosPro.amount = dif
									customPosPro.save()
									print("Belegegt ------- danach : " + str(p.available_volume))
									break
									productswithamount.append({"product" : x.product,"amount": x.amount,"Position":p})


					else:
						productswithamount.append({"product" : x.product,"amount": x.amount,"Volummen": None})
	print("myarray" + str(productswithamount))

	return render(request,"order/findpositionorder.html",context)

class ScanOrderTemplateView(UpdateView):
	template_name = "order/scan_order.html"
	form_class = modelform_factory(ProductOrder, fields=("confirmed", ))

	def get_object(self, *args, **kwargs):
		object = Order.objects.get(pk=self.kwargs.get("pk"))
		return object

	def get_context_data(self, *args, **kwargs):
		context = super(ScanOrderTemplateView, self).get_context_data(*args, **kwargs)
		context["object"] = self.get_object(*args, **kwargs)

		product_orders = context["object"].productorder_set.all()

		context["product_orders"] = product_orders

		if product_orders.count() > 0:

			set_field_names_onview(queryset=context["object"], context=context, ModelClass=Order,\
		    exclude_fields=["id"], exclude_filter_fields=["id"])

			set_field_names_onview(queryset=product_orders, context=context, ModelClass=ProductOrder,\
		    exclude_fields=["id", "order"], exclude_filter_fields=["id", "order"], template_tagname="product_order_field_names",\
		    				allow_related=True)
		else:
			context["product_orders"] = None

		return context

	def form_valid(self, form, *args, **kwargs):
		object = form.save()

		context = self.get_context_data(*args, **kwargs)
		
		confirmed_bool = self.request.POST.get("confirmed")
		product_id = self.request.POST.get("product_id")

		for product_order in object.productorder_set.all():
			print("FFFFFF: " + str(product_order.pk) + " : " + str(product_id))

			if str(product_order.pk) == str(product_id):
				print("PPPPPP: " + str(product_order.pk) + " : " + str(product_id))

				product_order.confirmed = confirmed_bool
				product_order.save()
				print("WHAAT: " + str(product_order))


		print("BRAND NEW: " + str(confirmed_bool) + " : " + str(product_id))
		print("****************************CONFIRMED: " + str(self.request.POST.get("confirmed")))
		return HttpResponseRedirect("")




# def ScanOrderTemplateView(request, *args, **kwargs):
# 	if request.method == "POST":


# 	context = {}

# 	object = Order.objects.get(pk=kwargs.get("pk"))

# 	context["object"] = object

# 	product_orders = context["object"].productorder_set.all()

# 	context["product_orders"] = product_orders


# 	if product_orders.count() > 0:
# 		set_field_names_onview(queryset=context["object"], context=context, ModelClass=Order,\
# 		exclude_fields=["id"], exclude_filter_fields=["id"])

# 		set_field_names_onview(queryset=product_orders, context=context, ModelClass=ProductOrder,\
# 		exclude_fields=["id", "order"], exclude_filter_fields=["id", "order"], template_tagname="product_order_field_names",\
# 					allow_related=True)
# 	else:
# 		context["product_orders"] = None


# 	return render(request, "order/scan_order.html", context )


# class ScanOrderTemplateView(TemplateView):
# 	template_name = "order/scan_order.html"
# 	def get_object(self, *args, **kwargs):
# 		object = Order.objects.get(pk=self.kwargs.get("pk"))
# 		return object

# 	def get_context_data(self, *args, **kwargs):
# 		context = super(ScanOrderTemplateView, self).get_context_data(*args, **kwargs)
# 		context["object"] = self.get_object(*args, **kwargs)

# 		product_orders = context["object"].productorder_set.all()

# 		context["product_orders"] = product_orders

# 		print("*********************: " + str(product_orders.count()))

# 		if product_orders.count() > 0:

# 			set_field_names_onview(queryset=context["object"], context=context, ModelClass=Order,\
# 		    exclude_fields=["id"], exclude_filter_fields=["id"])

# 			set_field_names_onview(queryset=product_orders, context=context, ModelClass=ProductOrder,\
# 		    exclude_fields=["id", "order"], exclude_filter_fields=["id", "order"], template_tagname="product_order_field_names",\
# 		    				allow_related=True)
# 		else:
# 			context["product_orders"] = None

# 		return context

# 	def post(self, request, *args, **kwargs):
# 		return HttpResponseRedirect(self.success_url)


class OrderUpdateView(LoginRequiredMixin, UpdateView):
	template_name = "order/form.html"
	login_url = "/login/"
	form_class = OrderForm

	def get_object(self):
		object = Order.objects.get(id=self.kwargs.get("pk"))
		return object

	def dispatch(self, request, *args, **kwargs):
		# request.user = AnonymousUser()
		return super(OrderUpdateView, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(OrderUpdateView, self).get_context_data(*args, **kwargs)
		context["title"] = "Bestellung bearbeiten"
		context["matching_"] = "Product" # Hier Modelname übergbenen
		# if self.request.POST:
		# 	formset = ProductOrderFormsetInline(self.request.POST, self.request.FILES, instance=self.object)
		# else:
		if self.request.POST:
			formset = ProductOrderFormsetInline(self.request.POST, self.request.FILES, instance=self.object)
		else:
			formset = ProductOrderFormsetInline(instance=self.object)
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


class OrderCreateView(CreateView):
	template_name = "order/form.html"
	form_class = OrderForm

	def get_context_data(self, *args, **kwargs):
		context = super(OrderCreateView, self).get_context_data(*args, **kwargs)
		print("**context***" + str(context))
		context["title"] = "Bestellung anlegen"
		context["matching_"] = "Product" # Hier Modelname übergbenen
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
		set_object_ondetailview(context=context, ModelClass=Order, exclude_fields=["id"],\
							    exclude_relations=[], exclude_relation_fields={"products": ["id"]})
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

		set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Order,\
	    exclude_fields=["id", "products"], exclude_filter_fields=["id", "products"])


		set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

		context["option_fields"] = [{"status": ["WARENEINGANG", "WARENAUSGANG"]}]

		return context

class OrderListAPIView(ListAPIView):
	queryset = Order.objects.all()
	serializer_class = OrderSerializer