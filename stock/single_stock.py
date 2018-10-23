from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import RedirectView

from sku.models import Sku
from stock.forms import StockUpdateForm, StockCreateForm
from stock.models import Stock
from stock.views import StockDeleteView, StockUpdateView, BookProductToPositionView, PositionListView, \
    GeneratePositionsView, PositionDeleteView, StockListBaseView, StockDeleteQuerySetView
from django.urls import reverse_lazy
from django import forms
from stock.models import Position


class SingleStockListView(StockListBaseView):
    queryset = Stock.objects.filter(sku_instance__product__single_product=True).order_by("-pk")
    template_name = "stock/single_stock_list.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get("clear_filter", "") or "" == "1":
            filter_values = {"single_stock_lagerplatz": None, "single_stock_sku": None, "single_stock_zustand": None,
                             "single_stock_title": None, "single_stock_ean_vollstaendig": None,
                             "single_stock_name": None, "single_stock_q": None}
            for name, value in filter_values.items():
                self.request.session[name] = value
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerbestand Einzelhandel"
        return context

    def set_filter_and_search_values_in_context(self, position, sku, state, title, ean, person, q):
        self.context = {"single_stock_lagerplatz": position, "single_stock_sku": sku, "single_stock_zustand": state,
                        "single_stock_title": title, "single_stock_ean_vollstaendig": ean, "single_stock_name": person,
                        "single_stock_q": q}
        print("UND ???????")

    def get_value_from_GET_or_session(self, value, request):
        get_value = request.GET.get(value)
        if get_value is not None:
            request.session[f"single_stock_{value}"] = get_value.strip()
            return get_value
        else:
            if request.GET.get("q") is None:
                return request.session.get(f"single_stock_{value}", "") or ""
            else:
                request.session[f"single_stock_{value}"] = ""
                return ""


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


class SingleStockDeleteQuerySetView(StockDeleteQuerySetView):
    success_url = reverse_lazy("stock:single_list")