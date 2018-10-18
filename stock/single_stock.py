from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import RedirectView

from sku.models import Sku
from stock.forms import StockUpdateForm, StockCreateForm
from stock.models import Stock
from stock.views import StockListView, StockDeleteView, StockUpdateView, BookProductToPositionView, PositionListView, \
    GeneratePositionsView, PositionDeleteView
from django.urls import reverse_lazy
from django import forms
from stock.models import Position


class SingleStockListView(StockListView):
    queryset = Stock.objects.filter(sku_instance__product__single_product=True).order_by("-pk")
    template_name = "stock/single_stock_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerbestand Einzelhandel"
        return context


class SingleStockDeleteView(StockDeleteView):
    success_url = reverse_lazy("stock:single_list")


class SingleStockCreateForm(StockCreateForm):
    class Meta:
        model = Stock
        fields = ["sku", "bestand", "lagerplatz"]
        labels = {"bestand": "IST Bestand"}
    zustand = None

    def clean(self, **kwargs):
        cleaned_data = super().clean()
        sku = cleaned_data.get("sku", "").strip()
        if sku != "":
            sku_instance = Sku.objects.filter(sku__iexact=sku).first()
            if sku_instance is not None:
                product = sku_instance.product
                if product is not None:
                    if product.single_product is not True:
                        self.add_error(None, "<h3 style='color:red;'>Die angegebene SKU ist kein Einzelartikel</h3>"
                                             "<p style='color:red;'>Sie können den Artikel unter Lager einbuchen</p>")
        return cleaned_data


class SingleStockUpdateForm(StockUpdateForm):
    class Meta:
        model = Stock
        fields = ["zustand", "sku", "bestand"]
        labels = {"bestand": "IST Bestand"}
    zustand = forms.ChoiceField(choices=((None, "----"), ("Neu", "Neu"), ("B", "B"), ("C", "C"),
                                         ("D", "D"), ("G", "G")), label=Stock._meta.get_field('zustand').verbose_name,
                                required=False)


class SingleStockUpdateView(StockUpdateView):
    form_class = SingleStockUpdateForm

    def dispatch(self, request, *args, **kwargs):
        self.object = Stock.objects.get(id=self.kwargs.get("pk"))
        if self.object is not None:
            self.position = Position.objects.filter(name__iexact=self.object.lagerplatz).first()
        self.instance = Stock.objects.get(id=self.kwargs.get("pk"))
        if (self.instance.sku_instance is not None and self.instance.sku_instance.product is not None and
                self.instance.sku_instance.product.single_product is not True):
            print(f"hää 3: {self.instance.sku_instance.product.single_product}")
            return HttpResponseRedirect(reverse_lazy("stock:edit", kwargs={"pk": self.instance.pk}))
        context = super().get_context_data(**kwargs)
        return render(request, self.template_name, context)


class SingleStockUpdateRedirectView(RedirectView):

    permanent = False
    query_string = True
    pattern_name = 'article-detail'

    def get_redirect_url(self, *args, **kwargs):
        stock = Stock.objects.filter(pk=self.kwargs.get("pk"))
        return super().get_redirect_url(*args, **kwargs)


class SingleBookProductToPositionView(BookProductToPositionView):
    form_class = SingleStockCreateForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Einzelartikel auf Position buchen"
        return context


class SinglePositionListView(PositionListView):
    template_name = "stock/position/single_position_list.html"


class SingleGeneratePositionsView(GeneratePositionsView):
    success_url = reverse_lazy("stock:single_position_list")


class SinglePositionDeleteView(PositionDeleteView):
    success_url = reverse_lazy("stock:single_position_list")
