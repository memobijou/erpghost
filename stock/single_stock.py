from stock.models import Stock
from stock.views import StockListView, StockDeleteView
from django.urls import reverse_lazy


class SingleStockListView(StockListView):
    queryset = Stock.objects.filter(product__single_product=True).order_by("-pk")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Lagerbestand Einzelhandel"
        return context


class SingleStockDeleteView(StockDeleteView):
    success_url = reverse_lazy("stock:single_list")
