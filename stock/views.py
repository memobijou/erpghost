from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.forms import modelform_factory
from .models import Stock, Stockdocument
from .forms import StockdocumentForm
from tablib import Dataset
from tablib import formats
from .resources import StockResource
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview,\
filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview
# Create your views here.

class StockListView(ListView):
	template_name = "stock/stock_list.html"
	def get_queryset(self):
		queryset = filter_queryset_from_request(self.request, Stock)
		return queryset

	def get_context_data(self, *args, **kwargs):
		context = super(StockListView, self).get_context_data(*args, **kwargs)
		context["title"] = "Inventar"

		context["amount"] = Stock.objects.count()

		set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Stock,\
	    exclude_fields=["id", "bestand", "ean_vollstaendig", "ean_upc", "zustand", "scanner", "name", "karton",
	    											  'box', 'bereich', 'ueberpruefung', 'aufnahme_datum'],\
	    exclude_filter_fields=["id", "bestand", "ean_vollstaendig", "ean_upc", "zustand", "scanner", "name", "karton",
	    											  'box', 'bereich', 'ueberpruefung', 'aufnahme_datum'])
		if context["object_list"]:
			set_paginated_queryset_onview(context["object_list"], self.request, 15, context)

		return context




class StockCreateView(CreateView):
	template_name = "stock/stock_create.html"
	form_class = StockdocumentForm

	def form_valid(self, form, *args, **kwargs):
		
		stock_resource = StockResource()
		dataset = Dataset()

		dataset.insert_col(0, col=[None,], header="id")
        # new_persons = request.FILES['myfile']

		document = form.cleaned_data["document"]
		#print("AAAA: " + str(document))
		# document = self.request.FILES["document"]
		# print("BBBBB: " + str(document))


		# imported_data = dataset.load(document.read())
		# result = stock_resource.import_data(dataset, dry_run=True)  # Test the data import

		# if not result.has_errors():
		# 	stock_resource.import_data(dataset, dry_run=False)  # Actually import now


		#person_resource = PersonResource()
        #dataset = Dataset()
        #new_persons = request.FILES['myfile']

		imported_data = dataset.load(document.read())
		#print("IMPPPPP: " + str(imported_data))

		for row in imported_data:
			#print("ROW: " + str(row[4]))
			#print("ABC: " + str(Stock.objects.filter(lagerplatz=row[4]).exists()))

			if Stock.objects.filter(lagerplatz=row[4]).exists() == True:
				return_ = super(StockCreateView, self).form_valid(form)
				return HttpResponseRedirect(self.get_success_url() + '?' + "status=false")
		result = stock_resource.import_data(dataset, dry_run=True)  # Test the data import
		#print("JAAAAAAAAAA")
		if not result.has_errors():
			stock_resource.import_data(dataset, dry_run=False)  # Actually import now

		return_ = super(StockCreateView, self).form_valid(form)
		return HttpResponseRedirect(self.get_success_url() + '?' + "status=true")
		# return super(StockCreateView, self).form_valid(form)

		# #/stock/document/
		# return HttpResponseRedirect(self.get_success_url() + '?' + request.META['QUERY_STRING'])
	
		# return render(self.request, self.template_name, self.get_context_data(*args, **kwargs))


class StockDetailView(DetailView):
	template_name = "stock/stock_detail.html"
	def get_object(self):
		obj = get_object_or_404(Stockdocument, pk=self.kwargs.get("pk"))
		return obj




class StockUpdateView(UpdateView):
	template_name = "stock/form.html"
	form_class = modelform_factory(model=Stock ,fields=["bestand"])

	def get_object(self):
		object = Stock.objects.get(id=self.kwargs.get("pk"))
		return object

	def dispatch(self, request, *args, **kwargs):
		# request.user = AnonymousUser()
		return super(StockUpdateView, self).dispatch(request, *args, **kwargs)

	def get_context_data(self, *args, **kwargs):
		context = super(StockUpdateView, self).get_context_data(*args, **kwargs)
		context["object"] = self.get_object(*args, **kwargs)
		#print("asdsadasdsa: " + str(context["object"]))

		context["title"] = "Inventar bearbeiten"
		# context["matching_"] = "Product" # Hier Modelname übergbenen
		# if self.request.POST:
		# 	formset = ProductOrderFormsetInline(self.request.POST, self.request.FILES, instance=self.object)
		# else:
		return context
