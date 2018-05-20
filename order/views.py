from django.db.models import Q
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from order.models import Order, ProductOrder, PositionProductOrder
from position.models import Position
from order.forms import OrderForm,ProductOrderFormsetUpdate, ProductOrderFormsetCreate, ProductOrderForm, \
    ProductOrderUpdateForm
from product.models import Product
from utils.utils import set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, set_object_ondetailview, save_picklist, search_positions_for_order, \
    search_all_wareneingang_products, get_verbose_names, get_filter_fields, \
    filter_complete_and_uncomplete_order_or_mission
from order.serializers import OrderSerializer, PositionProductOrderSerializer
from rest_framework.generics import ListAPIView
from django.forms import modelform_factory, inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from picklist.models import Picklist
from django.urls import reverse_lazy
from product.order_mission import validate_product_order_or_mission_from_post, \
    create_product_order_or_mission_forms_from_post, update_product_order_or_mission_forms_from_post, \
    validate_products_are_unique_in_form
from django.forms.models import model_to_dict
from django.forms import ValidationError


# search position for product which are on Wareneingang
def search_after_product_on_we(request):
    wePosition = Position.objects.get(halle="WE")
    gefunden_array = search_all_wareneingang_products()

    if len(gefunden_array) != 0:
        positions_products = save_picklist(gefunden_array, "Wareneingang", wePosition)
    else:
        positions_products = "NIX NEUES"

    wareneingang_products = PositionProductOrder.objects.filter(positions=wePosition)

    context = {"Positionen": positions_products,
               "we": wareneingang_products
               }
    return render(request, "order/position_product.html", context)


# function to search avaialble postion for productorder.
def search_positions(request, ordernummer):
    order = Order.objects.get(id=ordernummer)
    wePosition = Position.objects.get(halle="WE")

    all = search_positions_for_order(ordernummer)
    gefunden = all[0]
    alle = all[1]

    if len(gefunden) != 0:
        positions_products_new = save_picklist(gefunden, order, wePosition)
    else:
        positions_products_new = "NIX neues"

    positionproducts_all = PositionProductOrder.objects.filter(productorder__in=alle)
    positionproducts_we = PositionProductOrder.objects.filter(positions=wePosition)

    context = {"Positionen": positions_products_new,
               "alle": positionproducts_all,
               "we": positionproducts_we
               }

    return render(request, "order/position_product.html", context)


class ScanOrderUpdateView(UpdateView):
    template_name = "scan/scan.html"
    form_class = modelform_factory(ProductOrder, fields=("confirmed",))

    def get_object(self, *args, **kwargs):
        object = Order.objects.get(pk=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object(*args, **kwargs)
        context["title"] = "Wareneingang"
        product_orders = context.get("object").productorder_set.all()
        context["product_orders_or_missions"] = product_orders
        context["last_checked_checkbox"] = self.request.session.get("last_checked_checkbox")
        context["detail_url"] = reverse_lazy("order:detail", kwargs={"pk": self.kwargs.get("pk")})
        return context

    def form_valid(self, form, *args, **kwargs):
        object_ = form.save()
        self.update_scanned_product_order(object_)
        self.store_last_checked_checkbox_in_session()
        refresh_order_status(object_)
        return HttpResponseRedirect("")

    def update_scanned_product_order(self, object_):
        confirmed_bool = self.request.POST.get("confirmed")
        product_id = self.request.POST.get("product_id")
        missing_amount = self.request.POST.get("missing_amount")
        for product_order in object_.productorder_set.all():
            if str(product_order.pk) == str(product_id):
                if confirmed_bool == "0":
                    product_order.missing_amount = missing_amount
                elif confirmed_bool == "1":
                    product_order.missing_amount = None
                product_order.confirmed = confirmed_bool
                product_order.save()

    def store_last_checked_checkbox_in_session(self):
        self.request.session["last_checked_checkbox"] = self.request.POST.get("last_checked")


class OrderUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "order/form.html"
    login_url = "/login/"
    form_class = OrderForm

    def __init__(self):
        super().__init__()
        self.object = None
        self.product_forms = []

    def dispatch(self, request, *args, **kwargs):
        self.object = Order.objects.get(id=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Bestellung {self.object.ordernumber} bearbeiten"
        context["ManyToManyForms"] = self.build_product_order_forms()
        context["detail_url"] = reverse_lazy("order:detail", kwargs={"pk": self.kwargs.get("pk")})
        return context

    def build_product_order_forms(self):
        count = 0
        product_orders = self.object.productorder_set.all()

        for product_order in product_orders:
            if self.request.POST:
                data = self.get_data_from_post_on_index_x_to_form(count)
                product_order_form = ProductOrderUpdateForm(data=data)
            else:
                ean_or_sku, state = self.get_ean_or_sku_and_state(product_order)
                if product_order.product.ean != ean_or_sku:
                    state = None
                data = {"ean": ean_or_sku, "amount": product_order.amount,
                        "state": state, "netto_price": product_order.netto_price}
                product_order_form = ProductOrderUpdateForm(data=data)
            product = Product.objects.filter(Q(ean__exact=data.get("ean")) | Q(sku__sku=data.get("ean"))).first()
            self.product_forms.append((product_order_form, product))
            count += 1

        if self.request.method == "POST":
            amount_forms = self.get_amount_product_order_forms()
            for i in range(count, amount_forms):
                data = self.get_data_from_post_on_index_x_to_form(i)
                form = ProductOrderForm(data=data)
                product = Product.objects.filter(Q(ean__exact=data.get("ean")) | Q(sku__sku=data.get("ean"))).first()
                self.product_forms.append((form, product))
        else:
            if product_orders.count() == 0:
                self.product_forms.append((ProductOrderForm(), None))
        return self.product_forms

    def get_amount_product_order_forms(self):
        amount_forms = 0
        for field_name in ProductOrderForm.base_fields:
            if field_name in self.request.POST:
                amount_forms = len(self.request.POST.getlist(str(field_name)))
        return amount_forms

    def get_data_from_post_on_index_x_to_form(self, index):
        data = {}

        for field_name in ProductOrderForm.base_fields:
            if str(field_name) in self.request.POST:
                data[str(field_name)] = self.request.POST.getlist(str(field_name))[index]
        if "delete" in self.request.POST:
            if index < len(self.request.POST.getlist("delete")):
                data["delete"] = self.request.POST.getlist("delete")[index]
        return data

    def get_ean_or_sku_and_state(self, product_order):
        product = product_order.product
        ean_or_sku = None
        state = product_order.state

        if product.ean is not None and product.ean != "":
            ean_or_sku = product.ean
        else:
            sku_instance = product.sku_set.filter(state=product_order.state).first()
            if sku_instance is not None:
                ean_or_sku = sku_instance.sku
        return ean_or_sku, state

    def form_valid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        self.object = form.save(commit=False)

        if self.validate_product_forms_are_valid() is True:
            original_order_products = []

            for q in self.object.productorder_set.all():
                dict_ = {"product": str(q.product), "netto_price": q.netto_price, "amount": q.amount}
                original_order_products.append(dict_)

            self.create_order_products()
            self.update_order_products()
            refresh_order_status(self.object, original_order_products=original_order_products)
            return HttpResponseRedirect(self.get_success_url())
        else:
            return render(self.request, self.template_name, context)

    def validate_product_forms_are_valid(self):
        self.validate_product_forms_have_no_duplicates()
        self.validate_product_forms_have_no_skus_with_states()

        product_forms_are_valid = True
        for product_form, product in self.product_forms:
            if product_form.is_valid() is False:
                product_forms_are_valid = False
        return product_forms_are_valid

    def validate_product_forms_have_no_skus_with_states(self):
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            state = product_form.data.get("state")

            if product is not None and product.sku_set.filter(sku=ean_or_sku).count() > 0:
                if state is not None and state != "":
                    product_form.add_error("state",
                                           ValidationError(
                                               "Wenn Sie eine SKU angeben dürfen Sie keinen Zustand auswählen"))

    def validate_product_forms_have_no_duplicates(self):
        duplicates = []
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            ean, sku = None, None

            if product is not None:
                if product.ean == ean_or_sku:
                    ean = ean_or_sku
                elif product.sku_set.filter(sku=ean_or_sku).count() > 0:
                    sku = ean_or_sku

            state = product_form.data.get("state")
            if ean is not None:
                if (ean, state) not in duplicates:
                    duplicates.append((ean, state))
                else:
                    product_form.add_error('ean',
                                           ValidationError(f'Diese EAN in Kombinitation mit dem Zustand {state} darf'
                                                           f' nur einmal vorkommen'))

            elif sku is not None:
                if product is not None:
                    sku_instance = product.sku_set.filter(sku=ean_or_sku).first()
                    if product.ean is not None and product.ean != "":
                        if (product.ean, sku_instance.state) not in duplicates:
                            duplicates.append((product.ean, sku_instance.state))
                        else:
                            product_form.add_error('ean', ValidationError(
                                f'Dieser Artikel existiert bereits mit der EAN {product.ean} und dem Zustand'
                                f' {sku_instance.state} in diesem Auftrag'))
                else:
                    product_form.add_error('ean', ValidationError(f'Dieser Artikel existiert bereits in diesem'
                                                                  f' Auftrag'))

    def update_order_products(self):
        self.object.save()
        count = 0
        for (product_form, product), product_order_instance in zip(self.product_forms,
                                                                   self.object.productorder_set.all()):
            ean_or_sku = product_form.data.get("ean")
            amount = product_form.data.get("amount")
            netto_price = product_form.data.get("netto_price")
            to_delete = product_form.data.get("delete")

            state = product_form.data.get("state")

            if product_order_instance is not None:
                print(product_form.data)
                print(f"WAAATT ???: {ean_or_sku} - {amount} - {netto_price} - {state}")
                product_order_instance.product_id = product.pk
                product_order_instance.amount = amount
                product_order_instance.netto_price = netto_price
                product_order_instance.order_id = self.object.pk
            else:
                product_order_instance = ProductOrder(product_id=product.pk, amount=amount, netto_price=netto_price,
                                                      order_id=self.object.pk)

            if state is not None and state != "":
                product_order_instance.state = state
            else:
                product_order_instance.state = product.sku_set.filter(sku=ean_or_sku).first().state

            if to_delete == "on":
                product_order_instance.delete()
            else:
                product_order_instance.save()

            count += 1
        self.object.save()

    def create_order_products(self):
        index = self.object.productorder_set.all().count()
        amount_forms = self.get_amount_product_order_forms()

        for i in range(index, amount_forms):
            product_form, product = self.product_forms[i]
            ean_or_sku = product_form.data.get("ean")
            amount = product_form.data.get("amount")
            netto_price = product_form.data.get("netto_price")

            state = product_form.data.get("state")

            product_order_instance = ProductOrder(product_id=product.pk, amount=amount, netto_price=netto_price,
                                                  order_id=self.object.pk)
            if state is not None and state != "":
                product_order_instance.state = state
            else:
                product_order_instance.state = product.sku_set.filter(sku=ean_or_sku).first().state
            product_order_instance.save()
            self.object.productorder_set.add(product_order_instance)
        self.object.save()


class OrderCreateView(CreateView):
    template_name = "order/form.html"
    form_class = OrderForm
    amount_product_order_forms = 1

    def __init__(self):
        super().__init__()
        self.object = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Bestellung anlegen"
        context["ManyToManyForms"] = self.build_product_order_forms(self.amount_product_order_forms)
        context["detail_url"] = reverse_lazy("order:list")
        return context

    def build_product_order_forms(self, amount):
        if self.request.POST and len(self.request.POST.getlist("ean")) > 1:
            amount = len(self.request.POST.getlist("ean"))

        product_order_forms_list = []
        for i in range(0, amount):
            if self.request.POST:
                data = {}
                for k in self.request.POST:
                    if k in ProductOrderForm.base_fields:
                        data[k] = self.request.POST.getlist(k)[i]
                print(data)
                product_order_forms_list.append(ProductOrderForm(data=data))
            else:
                product_order_forms_list.append(ProductOrderForm())
        return product_order_forms_list

    def form_valid(self, form, *args, **kwargs):
        self.object = form.save(commit=False)

        duplicates = validate_products_are_unique_in_form(self.request.POST)
        if duplicates is not None:
            context = self.get_context_data(*args, **kwargs)
            context["duplicates"] = duplicates
            return render(self.request, self.template_name, context)

        valid_product_order_forms = \
            validate_product_order_or_mission_from_post(ProductOrderForm, self.amount_product_order_forms, self.request)

        if valid_product_order_forms is False:
            context = self.get_context_data(*args, **kwargs)
            return render(self.request, self.template_name, context)
        else:
            self.object.save()
            create_product_order_or_mission_forms_from_post(ProductOrder, ProductOrderForm,
                                                            self.amount_product_order_forms, "order", self.object,
                                                            self.request, 0)
            refresh_order_status(self.object)
        return HttpResponseRedirect(self.get_success_url())


def refresh_order_status(object_, original_order_products=None):
    product_orders = object_.productorder_set.all()
    all_scanned = True
    not_scanned_at_all = True

    for product_order in product_orders:
        if product_order.confirmed is True or product_order.confirmed is False:
            object_.status = "WARENEINGANG"
            not_scanned_at_all = False
        else:
            all_scanned = False

    if all_scanned and product_orders.exists():
        object_.status = "POSITIONIEREN"
        object_.save()
    print(not_scanned_at_all)
    if not_scanned_at_all is True:
        if object_.verified is True:
            # name changed - do something here
            object_.status = "AKZEPTIERT"

    if object_.verified is False:
        object_.status = "ABGELEHNT"

    if original_order_products is not None:
        print(f"{object_.productorder_set.count()} --- {len(original_order_products)}")
        if object_.productorder_set.count() != len(original_order_products):
            object_.status = "AUSSTEHEND"
            object_.verified = False
        else:
            has_changes = False
            for before_save_row, after_save_row in zip(original_order_products, object_.productorder_set.all()):
                if str(before_save_row.get("product")) != str(after_save_row.product)\
                        or str(before_save_row.get("netto_price")) != str(after_save_row.netto_price)\
                        or str(before_save_row.get("amount")) != str(after_save_row.amount):
                            has_changes = True
                            break
            print(f"HAS CHANGES: {has_changes}")
            if has_changes is True:
                object_.status = "AUSSTEHEND"
                object_.verified = False
    object_.save()


class OrderDetailView(DetailView):
    def get_object(self, *args, **kwargs):
        obj = get_object_or_404(Order, pk=self.kwargs.get("pk"))
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context["title"] = "Bestellung " + context["object"].ordernumber
        set_object_ondetailview(context=context, ModelClass=Order, exclude_fields=["id"],
                                exclude_relations=[], exclude_relation_fields={"products": ["id"]})
        context["fields"] = get_verbose_names(ProductOrder, exclude=["id", "order_id", "confirmed"])
        context["fields"].insert(1, "Titel")
        context["fields"][0] = "EAN / SKU"
        context["fields"].insert(len(context["fields"])-1, "Gesamtpreis (Netto)")
        return context


class OrderListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Order)
        queryset = filter_complete_and_uncomplete_order_or_mission(self.request, queryset, Order)
        queryset = queryset.order_by("-id")
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Bestellung"
        set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Order,
                               exclude_fields=["id", "products", "verified"],
                               exclude_filter_fields=["id", "products", "verified"])
        context["fields"] = get_verbose_names(Order, exclude=["id", "products", "invoice", "terms_of_payment",
                                                              "terms_of_delivery", "created_date", "modified_date",
                                                              "delivery_address_id"])
        context["fields"].insert(len(context["fields"])-1, "Fälligkeit")
        context["fields"].insert(len(context["fields"])-1, "Gesamt (Netto)")
        context["fields"].insert(len(context["fields"])-1, "Gesamt (Brutto)")
        set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["filter_fields"] = get_filter_fields(Order, exclude=["id", "products", "verified", "supplier_id",
                                                                     "invoice", "created_date", "modified_date"])
        context["option_fields"] = [{"status": ["OFFEN", "AKZEPTIERT", "ABGELEHNT",
                                                "WARENEINGANG", "POSITIONIEREN",] }]
        context["extra_options"] = [("complete", ["UNVOLLSTÄNDIG", "VOLLSTÄNDIG"])]
        return context


class OrderDeleteView(DeleteView):
    model = Order
    success_url = reverse_lazy("order:list")
    template_name = "order/order_confirm_delete.html"

    def get_object(self, queryset=None):
        return Order.objects.filter(id__in=self.request.GET.getlist('item'))


class OrderListAPIView(ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class PositionProductOrderListAPIView(ListAPIView):
    queryset = Picklist.objects.all()
    serializer_class = PositionProductOrderSerializer
