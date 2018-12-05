from django.db.models import Q, Sum
from django.http import HttpResponseRedirect
from django.views import View
from django.shortcuts import render
from django import forms
from django.urls import reverse_lazy
from stock.models import Stock, RebookOrder, RebookOrderItem, RebookOrderItemDestinationStock
from django.contrib.auth.models import User
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from stock.rebook import RebookOnPositionOverviewBase, BookStockOnPositionBase, BookStockOnPositionFormBase


class RebookOrderForm(forms.ModelForm):
    class Meta:
        model = RebookOrder
        fields = ["user"]
        widgets = {
            'user': forms.RadioSelect(),
        }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fields['user'].required = True


class RebookOrderItemForm(forms.ModelForm):
    class Meta:
        model = RebookOrderItem
        fields = ["amount"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
        self.fields['amount'].required = True

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        print(f"{self.instance.stock}")
        if amount > self.instance.stock.bestand:
            self.add_error("amount", "Umzubuchende Menge kann nicht größer als der Bestand sein")
        if amount <= 0:
            self.add_error("amount", "Umzubuchende Menge muss mindestens 1 sein")
        return amount


class AssignRebookOrderView(LoginRequiredMixin, View):
    template_name = "rebook/order/accept_rebook.html"
    title = "Umbuchauftrag anlegen"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.stocks = None
        self.context = None
        self.form = None
        self.rebookitem_forms = None

    def dispatch(self, request, *args, **kwargs):
        self.stocks = Stock.objects.filter(pk__in=request.GET.getlist("item"))
        self.form = self.get_form()
        self.rebookitem_forms = self.get_rebookitem_forms()
        self.context = self.get_context()
        return super().dispatch(request, *args, **kwargs)

    def get_rebookitem_forms(self):
        forms = []
        index = 0
        for stock in self.stocks:
            data = {}
            if self.request.method == "POST":
                amount = self.request.POST.getlist("amount")[index]
                data["amount"] = amount
            form = RebookOrderItemForm(data=data)
            form.instance.stock = stock
            form.instance.position = stock.lagerplatz
            form.instance.sku = stock.sku_instance
            forms.append((form, stock))
            index += 1
        return forms

    def get_form(self):
        if self.request.method == "POST":
            form = RebookOrderForm(data=self.request.POST)
        else:
            form = RebookOrderForm()
        return form

    def get_context(self):
        context = {"title": self.title, "stocks": self.stocks, "form": self.form,
                   "rebookitem_forms": self.rebookitem_forms}
        return context

    def get(self, request, *args, **kwargs):
        print(f"Hey dead: ")
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        if self.form.is_valid() is True:
            has_invalid_form = None
            for form, stock in self.rebookitem_forms:
                print(f"3anlash: {request.method}")
                print(f"sam: {form.data}")
                if form.is_valid() is False:
                    has_invalid_form = True
            if has_invalid_form is True:
                return render(request, self.template_name, self.context)
            else:
                self.save_rebook_order()
                return HttpResponseRedirect(reverse_lazy("stock:list"))
        else:
            return render(request, self.template_name, self.context)

    def save_rebook_order(self):
        rebook_order_instance = self.form.save()
        for rebookitem_form, stock in self.rebookitem_forms:
            rebookitem_form_instance = rebookitem_form.save(commit=False)
            rebookitem_form_instance.rebook_order = rebook_order_instance
            rebookitem_form_instance.save()


class RebookOrderListView(LoginRequiredMixin, generic.ListView):
    template_name = "rebook/order/rebook_order_list.html"
    paginate_by = 15
    title = "Umbuchaufträge Übersicht"

    def get_queryset(self):
        queryset = RebookOrder.objects.filter(user=self.request.user)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.get_context())
        return context

    def get_context(self):
        return {"title": self.title}


class RebookOrderView(LoginRequiredMixin, View):
    template_name = "rebook/order/rebook_order.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rebook_order = None
        self.rebook_order_items = None
        self.item = None
        self.context = None

    def dispatch(self, request, *args, **kwargs):
        self.rebook_order = RebookOrder.objects.get(pk=self.kwargs.get("pk"))
        self.rebook_order_items = []
        for item in self.rebook_order.rebookorderitem_set.all():
            rebooked_amount = item.rebookorderitemdestinationstock_set.all().aggregate(
                total=Sum("rebooked_amount")).get("total", 0) or 0
            self.rebook_order_items.append((item, rebooked_amount))

        self.context = self.get_context()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def get_context(self):
        return {"title": f"Umbuchauftrag {self.rebook_order.pk}", "rebook_order": self.rebook_order,
                "rebook_order_items": self.rebook_order_items}


class RebookOrderRebookOnPositionOverview(RebookOnPositionOverviewBase):
    template_name = "rebook/order/rebook_on_position_list.html"

    def get_position_from_GET_or_session(self):
        get_value = self.request.GET.get("position", "") or ""

        if get_value != "":
            self.request.session["rebook_order_position"] = get_value
            return get_value.strip()
        else:
            return (self.request.session.get("rebook_order_position", "") or "").strip()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rebook_order = None
        self.item = None

    def pre_dispatch(self):
        self.rebook_order = RebookOrder.objects.get(pk=self.kwargs.get("pk"))
        self.item = RebookOrderItem.objects.get(pk=self.kwargs.get("item_pk"))
        self.stock = Stock.objects.get(pk=self.item.stock.pk)
        self.position = self.get_position_from_GET_or_session()

    def redirect(self):
        if self.item.rebooked is True and self.item.amount == self.item.rebooked_amount:
            return HttpResponseRedirect(reverse_lazy("stock:rebook_order", kwargs={"pk": self.rebook_order.pk}))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["rebook_order"] = self.rebook_order
        context["rebook_order_item"] = self.item
        rebooked_amount = self.item.rebookorderitemdestinationstock_set.all().aggregate(
            total=Sum("rebooked_amount")).get("total", 0) or 0
        context["rebook_amount"] = self.item.amount-rebooked_amount or 0
        return context


class BookStockOrderOnPositionForm(BookStockOnPositionFormBase):
    def __init__(self, item=None, **kwargs):
        super().__init__(**kwargs)
        self.item = item
        self.stock = self.item.stock

    def get_amount_limit(self):
        rebooked_amount = self.item.rebookorderitemdestinationstock_set.all().aggregate(
            total=Sum("rebooked_amount")).get("total", 0) or 0
        rebooked_amount = self.item.amount-rebooked_amount or 0
        return rebooked_amount


class RebookOrderBookStockOnPosition(BookStockOnPositionBase):
    template_name = "rebook/order/book_stock_on_position.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rebook_order = None
        self.item = None
        self.destination_stock = None
        self.item_destination_stock = None

    def pre_dispatch(self):
        self.rebook_order = RebookOrder.objects.get(pk=self.kwargs.get("pk"))
        self.item = RebookOrderItem.objects.get(pk=self.kwargs.get("item_pk"))
        self.stock = self.item.stock

    def get_context(self):
        context = super().get_context()
        context["rebook_order"] = self.rebook_order
        context["rebook_order_item"] = self.item
        rebooked_amount = self.item.rebookorderitemdestinationstock_set.all().aggregate(
            total=Sum("rebooked_amount")).get("total", 0) or 0
        context["rebook_amount"] = self.item.amount-rebooked_amount or 0
        return context

    def pre_rebook_stock_to_destination(self, destination_stock, destination_sku, destination_position):
        if self.item is not None:
            self.item_destination_stock = RebookOrderItemDestinationStock(
                destination_stock=destination_stock, destination_position=destination_position,
                destination_sku=destination_sku, rebook_order_item=self.item,
                rebooked_amount=self.form.cleaned_data.get("amount"))

    def post(self, request, *args, **kwargs):
        if self.stock.id is None:
            self.item.stock = None
        self.item_destination_stock.save()
        total_amount = self.item.rebookorderitemdestinationstock_set.all().aggregate(
            total=Sum("rebooked_amount")).get("total")
        if self.item.amount == total_amount:
            self.item.rebooked = True
            self.item.save()
        self.finish_rebook_order_if_finished()
        return HttpResponseRedirect(reverse_lazy("stock:rebook_order", kwargs={"pk": self.rebook_order.pk}))

    def finish_rebook_order_if_finished(self):
        items = self.rebook_order.rebookorderitem_set.all()
        for item in items:
            rebooked_amount = 0
            for destination_stock_item in item.rebookorderitemdestinationstock_set.all():
                rebooked_amount += destination_stock_item.rebooked_amount or 0
            if rebooked_amount != item.amount or item.rebooked is not True:
                return

        if items.count() > 0:
            self.rebook_order.completed = True
            self.rebook_order.save()

    def get_form(self):
        if self.request.method == "POST":
            self.form = BookStockOrderOnPositionForm(data=self.request.POST, item=self.item)
        else:
            self.form = BookStockOrderOnPositionForm(item=self.item)
        return self.form
