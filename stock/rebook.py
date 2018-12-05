from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render

from mission.models import PickListProducts
from stock.models import Stock
from stock.views import StockListBaseView
from sku.models import Sku
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
from stock.models import Position
from django.views import View
from django.urls import reverse_lazy
from django import forms
from abc import ABC, ABCMeta, abstractmethod


class RefillOverview(StockListBaseView):
    queryset = Stock.objects.all()
    states = Sku.objects.all().values_list("state", flat=True).distinct("state")
    title = "Umbuchlager"
    template_name = "rebook/stock_list.html"

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get("clear_filter", "") or "" == "1":
            filter_values = {"rebook_lagerplatz": None, "rebook_sku": None, "rebook_zustand": None,
                             "rebook_title": None,
                             "rebook_ean_vollstaendig": None, "rebook_name": None, "rebook_q": None}
            for name, value in filter_values.items():
                self.request.session[name] = value
        return super().dispatch(request, *args, **kwargs)

    def set_filter_and_search_values_in_context(self, position, sku, state, title, ean, person, q):
        self.context = {"rebook_lagerplatz": position, "rebook_sku": sku, "rebook_zustand": state,
                        "rebook_title": title, "rebook_ean_vollstaendig": ean, "rebook_name": person, "rebook_q": q}

    def get_value_from_GET_or_session(self, value, request):
        get_value = request.GET.get(value)
        if get_value is not None:
            request.session[f"rebook_{value}"] = get_value.strip()
            return get_value
        else:
            if request.GET.get("q") is None:
                return request.session.get(f"rebook_{value}", "") or ""
            else:
                request.session[f"rebook_{value}"] = ""
                return ""


class RebookOnPositionOverviewBase(ABC, LoginRequiredMixin, generic.ListView):
    __metaclass__ = ABCMeta

    queryset = Position.objects.all()
    template_name = "rebook/rebook_on_position_list.html"
    title = "Bestand umbuchen"
    paginate_by = 15

    def __init__(self, **kwargs):
        self.stock = None
        self.position = None
        super().__init__(**kwargs)

    @abstractmethod
    def pre_dispatch(self):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.pre_dispatch()
        redirect = self.redirect() or None
        print(f"???????")
        if redirect is not None:
            return redirect
        return super().dispatch(request, *args, **kwargs)

    def redirect(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title, "stock": self.stock,
                        "position": self.position,
                        })
        return context

    def get_position_from_GET_or_session(self):
        print(f"???? {self.request.session.get('rebook_position', '')}")
        get_value = self.request.GET.get("position", "") or ""
        print(f"krank: {get_value}")

        if get_value != "":
            self.request.session["rebook_position"] = get_value
            return get_value.strip()
        else:
            return (self.request.session.get("rebook_position", "") or "").strip()

    def get_queryset(self):
        if self.position != "":
            self.queryset = self.queryset.filter(name__icontains=self.position)
        return self.queryset


class RebookOnPositionOverview(RebookOnPositionOverviewBase):
    def pre_dispatch(self):
        self.stock = Stock.objects.get(pk=self.kwargs.get("stock_pk"))
        self.position = self.get_position_from_GET_or_session()


class BookStockOnPositionFormBase(forms.Form):
    amount = forms.IntegerField(label="Bestand", required=True)

    def __init__(self, stock=None, **kwargs):
        super().__init__(**kwargs)
        self.stock = stock
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get("amount")
        print(f"hey {self.stock}")
        if amount <= 0:
            self.add_error("amount", "Sie müssen eine Menge größe als 0 eingeben")

        amount_limit = self.get_amount_limit()

        if amount > amount_limit:
            self.add_error("amount", f"Die umzubuchende Menge darf nicht größer als {amount_limit} sein")

        online_skus = Sku.objects.filter(main_sku__isnull=True, state=self.stock.sku_instance.state,
                                         product=self.stock.sku_instance.product).values_list("pk", flat=True)

        online_picklist_products = PickListProducts.objects.filter(
            product_mission__sku__pk__in=online_skus, pick_list__completed__isnull=True,
            product_mission__mission__is_online=True, position=self.stock.lagerplatz)

        online_picklists_amount = online_picklist_products.aggregate(total=Sum("amount")).get("total") or 0

        print(f"clara: {online_picklists_amount} --- {amount}")

        if amount_limit-amount >= amount_limit-online_picklists_amount:
            self.add_error("amount", f"Sie können diesen Artikel maximal "
                                     f"{amount_limit-online_picklists_amount}x umbuchen")
        return cleaned_data

    def get_amount_limit(self):
        pass


class BookStockOnPositionForm(BookStockOnPositionFormBase):
    def get_amount_limit(self):
        return self.stock.bestand


class BookStockOnPositionBase(ABC, LoginRequiredMixin, View):
    __metaclass__ = ABCMeta

    template_name = "rebook/book_stock_on_position.html"

    def __init__(self, **kwargs):
        self.position = None
        self.stock = None
        self.destination_stock = None
        self.form = None
        super().__init__(**kwargs)

    @abstractmethod
    def pre_dispatch(self):
        pass

    def dispatch(self, request, *args, **kwargs):
        self.pre_dispatch()
        self.position = self.request.GET.get("position", "") or ""
        self.form = self.get_form()

        if self.position == "":
            return render(request, self.template_name, self.get_context())

        if self.form.is_valid() is True:
            self.rebook_stock_to_destination()
        else:
            return render(request, self.template_name, self.get_context())
        return super().dispatch(request, *args, **kwargs)

    def rebook_stock_to_destination(self):
        rebook_amount = self.form.cleaned_data.get("amount")

        self.destination_stock = Stock.objects.filter(
            lagerplatz=self.position, sku_instance=self.stock.sku_instance)

        if self.destination_stock.count() > 0:
            self.destination_stock = self.destination_stock.first()
        else:
            self.destination_stock = None

        if self.destination_stock is None:
            self.destination_stock = Stock(lagerplatz=self.position, sku_instance=self.stock.sku_instance,
                                           sku=self.stock.sku_instance.sku)

        if self.destination_stock is not None:
            if self.destination_stock.bestand is None:
                self.destination_stock.bestand = rebook_amount
            else:
                self.destination_stock.bestand += rebook_amount

        self.destination_stock.save()
        self.pre_rebook_stock_to_destination(self.destination_stock, self.destination_stock.sku_instance,
                                             self.destination_stock.lagerplatz)

        if rebook_amount > 0:
            if self.stock.bestand-rebook_amount >= 0:
                self.destination_stock.save()
                if self.stock.bestand-rebook_amount == 0:
                    self.stock.delete()
                else:
                    self.stock.bestand -= rebook_amount
                    self.stock.save()

    def pre_rebook_stock_to_destination(self, destination_stock, destination_sku, destination_position):
        pass

    def get_form(self):
        if self.request.method == "POST":
            self.form = BookStockOnPositionForm(data=self.request.POST, stock=self.stock)
        else:
            self.form = BookStockOnPositionForm(stock=self.stock)
        return self.form

    def get(self, request, *args, **kwargs):
        context = self.get_context()
        return render(request, self.template_name, context)

    def get_context(self):
        return {"title": "Auf Position einbuchen", "stock": self.stock, "position": self.position,
                "form": self.form}

    def post(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse_lazy("stock:list"))


class BookStockOnPosition(BookStockOnPositionBase):
    def pre_dispatch(self):
        self.stock = Stock.objects.get(pk=self.kwargs.get("stock_pk"))
