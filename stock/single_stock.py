from sku.models import Sku
from stock.forms import StockUpdateForm, StockCreateForm
from stock.models import Stock
from stock.views import StockListView, StockDeleteView, StockUpdateView, BookProductToPositionView, PositionListView, \
    GeneratePositionsView, PositionDeleteView
from django.urls import reverse_lazy


class SingleStockListView(StockListView):
    queryset = Stock.objects.filter(sku_instance__product__single_product=True).order_by("-pk")

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
