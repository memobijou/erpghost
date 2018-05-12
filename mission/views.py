from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import FormView
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import XPreformatted

from product.order_mission import validate_product_order_or_mission_from_post, \
    create_product_order_or_mission_forms_from_post, update_product_order_or_mission_forms_from_post, \
    validate_products_are_unique_in_form
from stock.models import Stock
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview, \
    get_verbose_names, get_filter_fields, filter_complete_and_uncomplete_order_or_mission
from mission.models import Mission, ProductMission, RealAmount
from mission.forms import MissionForm, ProductMissionFormsetUpdate, ProductMissionFormsetCreate, ProductMissionForm, \
    ProductMissionUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import inlineformset_factory, modelform_factory
from django.urls import reverse_lazy
from django.template.loader import get_template
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.graphics.shapes import Drawing, Line
from reportlab.platypus.tables import Table, TableStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import Frame, NextPageTemplate, PageBreak
from django.forms.models import model_to_dict
from django.views import View


class MissionBillingFormView(View):
    template_name = "mission/billing_form.html"
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {}
        context["object"] = self.object
        context["title"] = "Rechnung und Lieferschein generieren"
        context["billing_delivery_note_products"] = self.get_billing_delivery_note_products()
        return render(request, self.template_name, context)

    def get_billing_delivery_note_products(self):
        billing_products = []

        for product_mission in self.object.productmission_set.all():
            if product_mission.confirmed is None:
                continue
            real_amount = 0
            for real_amount_row in product_mission.realamount_set.all():
                real_amount += real_amount_row.real_amount
            if (product_mission.real_amount - real_amount) <= 0:
                continue
            billing_products.append((product_mission, product_mission.real_amount - real_amount))
        return billing_products

    def post(self, request, *args, **kwargs):

        bulk_instances = []

        new_billing_number = self.get_new_billing_number()
        new_delivery_note_number = self.get_new_delivery_note_number()

        for product_mission in self.object.productmission_set.all():
            if product_mission.confirmed is None:
                continue
            real_amount = product_mission.real_amount
            all_amounts_sum = 0
            for real_amount_row in product_mission.realamount_set.all():
                all_amounts_sum += real_amount_row.real_amount

            real_amount -= all_amounts_sum

            if product_mission.realamount_set.count() == 0:
                real_amount = product_mission.real_amount
            if all_amounts_sum < product_mission.real_amount:
                bulk_instances.append(RealAmount(product_mission=product_mission, billing_number=new_billing_number,
                                                 delivery_note_number=new_delivery_note_number,
                                                 real_amount=real_amount))
        RealAmount.objects.bulk_create(bulk_instances)
        return HttpResponseRedirect(reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")}))

    def get_new_billing_number(self):
        max_billing_number = self.get_max_billing_number()
        if max_billing_number is not None and "-" in max_billing_number:
            billing_number = f'{self.object.billing_number}-{int(max_billing_number.split("-", 1)[1])+1}'
        else:
            billing_number = f"{self.object.billing_number}-1"
        return billing_number

    def get_new_delivery_note_number(self):
        max_delivery_note_number = self.get_max_delivery_note_number()
        if max_delivery_note_number is not None and "-" in max_delivery_note_number:
            delivery_note_number = \
                f'{self.object.delivery_note_number}-{int(max_delivery_note_number.split("-", 1)[1])+1}'
        else:
            delivery_note_number = f"{self.object.delivery_note_number}-1"
        return delivery_note_number

    def get_billing_numbers(self):
        billing_numbers = []
        product_missions = self.object.productmission_set.all()
        for product_mission in product_missions:

            for real_amount in product_mission.realamount_set.all():
                if real_amount.billing_number not in billing_numbers:
                    billing_numbers.append(real_amount.billing_number)
        return billing_numbers

    def get_delivery_note_numbers(self):
        delivery_note_numbers = []
        product_missions = self.object.productmission_set.all()
        for product_mission in product_missions:
            for real_amount in product_mission.realamount_set.all():
                if real_amount.delivery_note_number not in delivery_note_numbers:
                    delivery_note_numbers.append(real_amount.delivery_note_number)
        return delivery_note_numbers

    def get_max_billing_number(self):
        billing_numbers = self.get_billing_numbers()

        max_billing_number = None
        billing_number_counter = 0
        for billing_number in billing_numbers:
            if "-" in billing_number and max_billing_number is None:
                max_billing_number = billing_number
                continue

            if "-" in billing_number:
                if int(billing_number.split("-", 1)[1]) > billing_number_counter:
                    max_billing_number = billing_number
                    billing_number_counter = int(billing_number.split("-", 1)[1])

        return max_billing_number

    def get_max_delivery_note_number(self):
        delivery_note_numbers = self.get_delivery_note_numbers()

        max_delivery_note_number = None
        delivery_note_number_counter = 0

        for delivery_note_number in delivery_note_numbers:
            if "-" in delivery_note_number and max_delivery_note_number is None:
                max_delivery_note_number = delivery_note_number
                continue

            if "-" in delivery_note_number:
                if int(delivery_note_number.split("-", 1)[1]) > delivery_note_number_counter:
                    max_delivery_note_number = delivery_note_number
                    delivery_note_number_counter = int(delivery_note_number.split("-", 1)[1])

        return max_delivery_note_number


class MissionDetailView(DetailView):
    object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = "Auftrag " + context["object"].mission_number
        set_object_ondetailview(context=context, ModelClass=Mission, exclude_fields=["id"],\
                                exclude_relations=[], exclude_relation_fields={"products": ["id"]})
        context["fields"] = get_verbose_names(ProductMission, exclude=["id", "mission_id"])
        context["fields"].insert(1, "Titel")
        context["fields"].insert(4, "Reale Menge")
        context["fields"][0] = "EAN / SKU"
        context["fields"].insert(len(context["fields"]) - 1, "Gesamtpreis (Netto)")
        context["products_from_stock"] = self.get_products_from_stock()
        context["real_amounts"] = self.get_real_amounts()
        return context

    def get_real_amounts(self):
        real_amounts = []

        for mission_product in self.object.productmission_set.all():
            billing_numbers_and_delivery_note_numbers = \
                mission_product.realamount_set.values("billing_number", "delivery_note_number").distinct()

            for dict_ in billing_numbers_and_delivery_note_numbers:
                billing_number = dict_.get('billing_number')
                delivery_note_number = dict_.get('delivery_note_number')

                real_amount_rows = RealAmount.objects.filter(billing_number=billing_number,
                                                             delivery_note_number=delivery_note_number)

                self.add_real_amount_to_list(real_amount_rows, real_amounts)

        # real_amounts.sort(key=lambda real_amounts: real_amounts[0])

        return real_amounts

    def add_real_amount_to_list(self, real_amount_rows, real_amounts_list):
        for real_amount_rows_from_list in real_amounts_list:
            for query in real_amount_rows_from_list:
                for row in real_amount_rows:
                    if query.billing_number == row.billing_number:
                        return
        real_amounts_list.append(real_amount_rows)

    def get_products_from_stock(self):
        billing_products = []
        print(billing_products)
        for product_mission in self.object.productmission_set.all():
            product_stock = self.get_product_stock(product_mission.product)
            stock = 0
            if product_stock is None:
                stock = 0

            amount = product_mission.amount

            if product_stock >= amount:
                stock = amount
            else:
                stock = product_stock

            real_amount = amount-(amount-stock)

            billing_products.append((product_mission,  amount-stock,  product_stock, real_amount))
            print(billing_products)
        return billing_products

    def get_product_stock(self, product):
        if product.ean is not None:
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()
            if stock is not None:
                return stock.total_amount_ean()


class MissionListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Mission)
        queryset = filter_complete_and_uncomplete_order_or_mission(self.request, queryset, Mission)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = "Auftrag"

        set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Mission,\
                               exclude_fields=["id", "pickable"],
                               exclude_filter_fields=["id", "pickable"])
        context["fields"] = get_verbose_names(Mission, exclude=["id", "supplier_id", "products",
                                                                "modified_date", "created_date", "terms_of_payment",
                                                                "terms_of_delivery"])
        context["fields"].insert(len(context["fields"]) - 1, "Fälligkeit")
        # ignore
        context["fields"].insert(len(context["fields"]) - 1, "Gesamt (Netto)")
        context["fields"].insert(len(context["fields"]) - 1, "Gesamt (Brutto)")
        if context["object_list"].count() > 0:
            set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["filter_fields"] = get_filter_fields(Mission, exclude=["id", "products", "supplier_id",
                                                                       "invoice", "pickable", "modified_date",
                                                                       "created_date"])
        context["option_fields"] = [
            {"status": ["WARENAUSGANG", "PICKBEREIT", "AUSSTEHEND", "OFFEN", "LIEFERUNG"]}]
        context["extra_options"] = [("complete", ["UNVOLLSTÄNDIG", "VOLLSTÄNDIG"])]
        return context


class MissionCreateView(CreateView):
    template_name = "mission/form.html"
    form_class = MissionForm
    amount_product_mission_forms = 1

    def __init__(self):
        super().__init__()
        self.object = None

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Auftrag anlegen"
        context["ManyToManyForms"] = self.build_product_mission_forms(self.amount_product_mission_forms)
        context["detail_url"] = reverse_lazy("mission:list")
        return context

    def build_product_mission_forms(self, amount):
        if self.request.POST and len(self.request.POST.getlist("ean")) > 1:
            amount = len(self.request.POST.getlist("ean"))

        product_mission_forms_list = []
        for i in range(0, amount):
            if self.request.POST:
                data = {}
                for k in self.request.POST:
                    if k in ProductMissionForm.base_fields:
                        data[k] = self.request.POST.getlist(k)[i]
                print(data)
                product_mission_forms_list.append(ProductMissionForm(data=data))
            else:
                product_mission_forms_list.append(ProductMissionForm())
        return product_mission_forms_list

    def form_valid(self, form, *args, **kwargs):
        self.object = form.save(commit=False)

        duplicates = validate_products_are_unique_in_form(self.request.POST)
        if duplicates is not None:
            context = self.get_context_data(**kwargs)
            context["duplicates"] = duplicates
            return render(self.request, self.template_name, context)

        valid_product_mission_forms = \
            validate_product_order_or_mission_from_post(ProductMissionForm, self.amount_product_mission_forms,
                                                        self.request)

        if valid_product_mission_forms is False:
            context = self.get_context_data(*args, **kwargs)
            return render(self.request, self.template_name, context)
        else:
            self.object.save()

            create_product_order_or_mission_forms_from_post(ProductMission, ProductMissionForm,
                                                            self.amount_product_mission_forms, "mission", self.object,
                                                            self.request, 0)
            refresh_mission_status(self.object)
        return HttpResponseRedirect(self.get_success_url())


class MissionDeleteView(DeleteView):
    model = Mission
    success_url = reverse_lazy("mission:list")
    template_name = "mission/mission_confirm_delete.html"

    def get_object(self, queryset=None):
        return Mission.objects.filter(id__in=self.request.GET.getlist('item'))


class MissionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "mission/form.html"
    login_url = "/login/"
    form_class = MissionForm

    def __init__(self):
        super().__init__()
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Mission.objects.get(id=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Auftrag {self.object.mission_number} bearbeiten"
        context["ManyToManyForms"] = self.build_product_mission_forms()
        context["detail_url"] = reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")})
        if self.object_has_products() is True:
            context["object_has_products"] = True
        context["amount_update_forms"] = self.object.productmission_set.count()
        return context

    def object_has_products(self):
        object_ = self.get_object()
        if object_.productmission_set.all().count() >= 1:
            return True
        else:
            return False

    def build_product_mission_forms(self):
        product_mission_forms_list = []
        product_mission_forms_list = self.object_instances_to_forms_list(product_mission_forms_list)
        product_mission_forms_list = self.non_object_forms_to_forms_list(product_mission_forms_list)
        if len(product_mission_forms_list) == 0:
            product_mission_forms_list.append(ProductMissionForm())

        return product_mission_forms_list

    def object_instances_to_forms_list(self, forms_list):
        product_missions = self.object.productmission_set.all()
        i = 0
        for product_mission in product_missions:
            if self.request.POST:
                data = {}
                for k in self.request.POST:
                    if k in ProductMissionUpdateForm.base_fields:
                        data[k] = self.request.POST.getlist(k)[i]
                forms_list.append(ProductMissionUpdateForm(data=data))
            else:
                data = model_to_dict(product_mission)
                data["ean"] = product_mission.product.ean
                forms_list.append(ProductMissionUpdateForm(data=data))
            i += 1
        return forms_list

    def non_object_forms_to_forms_list(self, forms_list):
        if self.request.POST and len(self.request.POST.getlist("ean")) >= 1:
            for i in range(len(forms_list), len(self.request.POST.getlist("ean"))):
                    data = {}
                    for k in self.request.POST:
                        if k in ProductMissionForm.base_fields:
                            data[k] = self.request.POST.getlist(k)[i]
                    forms_list.append(ProductMissionForm(data=data))
        return forms_list

    def form_valid(self, form, **kwargs):
        self.object = form.save(commit=False)

        duplicates = validate_products_are_unique_in_form(self.request.POST)
        if duplicates is not None:
            context = self.get_context_data(**kwargs)
            context["duplicates"] = duplicates
            return render(self.request, self.template_name, context)

        valid_product_mission_forms = \
            validate_product_order_or_mission_from_post(ProductMissionUpdateForm,
                                                        self.object.productmission_set.all().count(), self.request)

        if valid_product_mission_forms is False:
            context = self.get_context_data(**kwargs)
            if len(self.request.POST.getlist("ean")) >= 1:
                context["object_has_products"] = True
            return render(self.request, self.template_name, context)
        else:
            original_mission = Mission.objects.get(pk=self.object.pk)

            original_mission_products = []
            for q in original_mission.productmission_set.all():
                dict_ = {"product": str(q.product), "netto_price": q.netto_price, "amount": q.amount}
                original_mission_products.append(dict_)

            print(original_mission_products)
            print(len(original_mission_products))
            self.object.save()
            update_product_order_or_mission_forms_from_post("productmission_set", ProductMissionUpdateForm, "mission",
                                                            self.object, self.request, ProductMission)
            refresh_mission_status(self.object, original_mission_products=original_mission_products)
        return HttpResponseRedirect(self.get_success_url())


class ScanMissionUpdateView(UpdateView):
    template_name = "mission/scan/scan.html"
    form_class = modelform_factory(ProductMission, fields=("confirmed",))

    def get_object(self, *args, **kwargs):
        object = Mission.objects.get(pk=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object(*args, **kwargs)
        context["title"] = "Warenausgang"
        product_missions = context.get("object").productmission_set.all()
        context["mission_products"] = self.get_products_from_stock()
        context["last_checked_checkbox"] = self.request.session.get("last_checked_checkbox")
        context["detail_url"] = reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")})
        return context

    def get_products_from_stock(self):
        billing_products = []
        print(billing_products)
        for product_mission in self.object.productmission_set.all():
            product_stock = self.get_product_stock(product_mission.product)
            stock = 0
            if product_stock is None:
                stock = 0

            amount = product_mission.amount

            all_amounts_sum = 0

            for real_amount_row in product_mission.realamount_set.all():
                all_amounts_sum += real_amount_row.real_amount

            if all_amounts_sum < amount:
                amount -= all_amounts_sum

            if amount <= 0:
                continue

            else:
                if product_stock >= amount:
                    stock = amount
                else:
                    stock = product_stock

            billing_products.append((product_mission, amount,  amount-stock,  stock))
            print(billing_products)
        return billing_products

    def get_product_stock(self, product):
        if product.ean is not None:
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()
            if stock is not None:
                return stock.total_amount_ean()

    def form_valid(self, form, *args, **kwargs):
        object_ = form.save()
        self.update_scanned_product_mission(object_)
        self.store_last_checked_checkbox_in_session()
        refresh_mission_status(object_)
        return HttpResponseRedirect("")

    def update_scanned_product_mission(self, object_):
        confirmed_bool = self.request.POST.get("confirmed")
        product_id = self.request.POST.get("product_id")
        missing_amount = self.request.POST.get("missing_amount")
        for product_mission in object_.productmission_set.all():
            if str(product_mission.pk) == str(product_id):
                if confirmed_bool == "0":
                    product_mission.missing_amount = missing_amount
                elif confirmed_bool == "1":
                    product_mission.missing_amount = None
                product_mission.confirmed = confirmed_bool
                product_mission.save()

    def store_last_checked_checkbox_in_session(self):
        self.request.session["last_checked_checkbox"] = self.request.POST.get("last_checked")


def refresh_mission_status(object_, original_mission_products=None):
    product_missions = object_.productmission_set.all()
    all_scanned = True
    has_confirmed_false = False
    not_scanned_at_all = True

    for product_mission in product_missions:
        if product_mission.confirmed is True or product_mission.confirmed is False:
            object_.status = "WARENAUSGANG"
            if product_mission.confirmed is False:
                has_confirmed_false = True
            not_scanned_at_all = False
        else:
            all_scanned = False
    if all_scanned is True and product_missions.exists():
        object_.status = "LIEFERUNG"
        if has_confirmed_false is True:
            object_.status = "TEILLIEFERUNG"

    if not_scanned_at_all:
        if object_.confirmed is True:
            object_.status = "PICKBEREIT"

    if object_.confirmed is False:
        object_.status = "AUSSTEHEND"

    if original_mission_products is not None:
        print(f"{object_.productmission_set.count()} --- {len(original_mission_products)}")
        if object_.productmission_set.count() != len(original_mission_products):
            object_.status = "AUSSTEHEND"
            object_.confirmed = False
        else:
            has_changes = False
            for before_save_row, after_save_row in zip(original_mission_products, object_.productmission_set.all()):
                if str(before_save_row.get("product")) != str(after_save_row.product)\
                        or str(before_save_row.get("netto_price")) != str(after_save_row.netto_price)\
                        or str(before_save_row.get("amount")) != str(after_save_row.amount):
                            has_changes = True
                            break

            if has_changes is True:
                object_.status = "AUSSTEHEND"
                object_.confirmed = False
    object_.save()


class MissionStockCheckForm(View):
    template_name = "mission/stock_check.html"

    def __init__(self):
        super().__init__()
        self.context = {}
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Mission.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.context["title"] = "Auftrag zum Versenden freigeben"
        self.context["object"] = self.object
        self.context["products_from_stock"] = self.get_products_from_stock()

        return render(request, self.template_name, self.context)

    def get_products_from_stock(self):
        billing_products = []
        print(billing_products)
        for product_mission in self.object.productmission_set.all():
            product_stock = self.get_product_stock(product_mission.product)
            stock = 0
            if product_stock is None:
                stock = 0

            amount = product_mission.amount
            all_amounts_sum = 0

            for real_amount_row in product_mission.realamount_set.all():
                all_amounts_sum += real_amount_row.real_amount

            amount -= all_amounts_sum

            if amount <= 0:
                continue

            else:
                if product_stock >= amount:
                    stock = amount
                else:
                    stock = product_stock

            billing_products.append((product_mission, amount,  amount-stock,  stock))
            print(billing_products)
        return billing_products

    def get_product_stock(self, product):
        if product.ean is not None:
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()
            if stock is not None:
                return stock.total_amount_ean()

        # if product.sku is not None:
        #     stock = Stock.objects.filter(sku=product.sku).first()
        #     if stock is not None:
        #         return stock.total_amount_ean()

    def post(self, request, *args, **kwargs):

        bulk_instances = []

        new_billing_number = self.get_new_billing_number()
        new_delivery_note_number = self.get_new_delivery_note_number()

        for product_mission in self.object.productmission_set.all():
            product_stock = self.get_product_stock(product_mission.product)

            if product_stock == 0:
                continue

            if product_stock < product_mission.amount:
                real_amount = product_mission.amount-(product_mission.amount-product_stock)
            else:
                real_amount = product_mission.amount

            if real_amount <= 0:
                continue

            all_amounts_sum = 0

            for real_amount_row in product_mission.realamount_set.all():
                all_amounts_sum += real_amount_row.real_amount
            real_amount -= all_amounts_sum

            print(f"{real_amount} --- {all_amounts_sum}")

            if real_amount <= (product_mission.amount-all_amounts_sum):
                bulk_instances.append(RealAmount(product_mission=product_mission, billing_number=new_billing_number,
                                                 delivery_note_number=new_delivery_note_number,
                                                 real_amount=real_amount))
        print(bulk_instances)
        RealAmount.objects.bulk_create(bulk_instances)
        return HttpResponseRedirect(reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")}))

    def get_new_billing_number(self):
        max_billing_number = self.get_max_billing_number()
        if max_billing_number is not None and "-" in max_billing_number:
            billing_number = f'{self.object.billing_number}-{int(max_billing_number.split("-", 1)[1])+1}'
        else:
            billing_number = f"{self.object.billing_number}-1"
        return billing_number

    def get_new_delivery_note_number(self):
        max_delivery_note_number = self.get_max_delivery_note_number()
        if max_delivery_note_number is not None and "-" in max_delivery_note_number:
            delivery_note_number = \
                f'{self.object.delivery_note_number}-{int(max_delivery_note_number.split("-", 1)[1])+1}'
        else:
            delivery_note_number = f"{self.object.delivery_note_number}-1"
        return delivery_note_number

    def get_billing_numbers(self):
        billing_numbers = []
        product_missions = self.object.productmission_set.all()
        for product_mission in product_missions:

            for real_amount in product_mission.realamount_set.all():
                if real_amount.billing_number not in billing_numbers:
                    billing_numbers.append(real_amount.billing_number)
        return billing_numbers

    def get_delivery_note_numbers(self):
        delivery_note_numbers = []
        product_missions = self.object.productmission_set.all()
        for product_mission in product_missions:
            for real_amount in product_mission.realamount_set.all():
                if real_amount.delivery_note_number not in delivery_note_numbers:
                    delivery_note_numbers.append(real_amount.delivery_note_number)
        return delivery_note_numbers

    def get_max_billing_number(self):
        billing_numbers = self.get_billing_numbers()

        max_billing_number = None
        billing_number_counter = 0
        for billing_number in billing_numbers:
            if "-" in billing_number and max_billing_number is None:
                max_billing_number = billing_number
                continue

            if "-" in billing_number:
                if int(billing_number.split("-", 1)[1]) > billing_number_counter:
                    max_billing_number = billing_number
                    billing_number_counter = int(billing_number.split("-", 1)[1])

        return max_billing_number

    def get_max_delivery_note_number(self):
        delivery_note_numbers = self.get_delivery_note_numbers()

        max_delivery_note_number = None
        delivery_note_number_counter = 0

        for delivery_note_number in delivery_note_numbers:
            if "-" in delivery_note_number and max_delivery_note_number is None:
                max_delivery_note_number = delivery_note_number
                continue

            if "-" in delivery_note_number:
                if int(delivery_note_number.split("-", 1)[1]) > delivery_note_number_counter:
                    max_delivery_note_number = delivery_note_number
                    delivery_note_number_counter = int(delivery_note_number.split("-", 1)[1])

        return max_delivery_note_number


class ConfirmView(View):
    def post(self, request, *args, **kwargs):
        self.object.confirmed = True
        self.object.save()
        original_mission = Mission.objects.get(pk=self.object.pk)

        original_mission_products = []
        for q in original_mission.productmission_set.all():
            dict_ = {"product": str(q.product), "netto_price": q.netto_price, "amount": q.amount}
            original_mission_products.append(dict_)

        refresh_mission_status(self.object, original_mission_products=original_mission_products)
        return HttpResponseRedirect(reverse_lazy("mission:detail", kwargs={"pk": self.object.pk}))