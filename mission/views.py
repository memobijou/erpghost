from django.db.models import F
from django.db.models import Q
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

from product.models import Product
from product.order_mission import validate_product_order_or_mission_from_post, \
    create_product_order_or_mission_forms_from_post, update_product_order_or_mission_forms_from_post, \
    validate_products_are_unique_in_form
from stock.models import Stock
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview, \
    get_verbose_names, get_filter_fields, filter_complete_and_uncomplete_order_or_mission
from mission.models import Mission, ProductMission, RealAmount, Billing, DeliveryNote, DeliveryNoteProductMission, \
    Delivery, DeliveryMissionProduct, GoodsIssue, GoodsIssueDeliveryMissionProduct, PickList, PickListProducts
from mission.forms import MissionForm, ProductMissionFormsetUpdate, ProductMissionFormsetCreate, ProductMissionForm, \
    ProductMissionUpdateForm, BillingForm, PickForm
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
from django.forms import ValidationError
from django.core.paginator import Paginator
from django.contrib import messages


class MissionDetailView(DetailView):

    def __init__(self):
        super().__init__()
        self.object = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Auftrag " + context["object"].mission_number
        set_object_ondetailview(context=context, ModelClass=Mission, exclude_fields=["id"],\
                                exclude_relations=[], exclude_relation_fields={"products": ["id"]})
        context["fields"] = self.build_fields()
        context["products_from_stock"] = self.get_products_from_stock()
        context["deliveries"] = self.get_deliveries()
        return context

    def get_deliveries(self):
        deliveries = []
        for delivery in self.object.delivery_set.all():
            deliveries.append((delivery, list(zip(delivery.goodsissue_set.first().billing_set.all(),
                               delivery.goodsissue_set.first().deliverynote_set.all()))))
        return deliveries

    def build_fields(self):
        fields = get_verbose_names(ProductMission, exclude=["id", "mission_id", "confirmed"])
        fields.insert(1, "Titel")
        fields.insert(5, "Reale Menge")
        fields[0] = "EAN / SKU"
        fields.insert(len(fields), "Gesamtpreis (Netto)")
        return fields

    def add_real_amount_to_list(self, real_amount_rows, real_amounts_list):
        for real_amount_rows_from_list in real_amounts_list:
            for query in real_amount_rows_from_list:
                for row in real_amount_rows:
                    if query.billing.billing_number == row.billing.billing_number:
                        return
        real_amounts_list.append(real_amount_rows)

    def get_products_from_stock(self):
        products = []
        print(products)
        for product_mission in self.object.productmission_set.all():
            product_stock = self.get_product_stock(product_mission)

            amount = product_mission.amount

            missing_amount = product_mission.amount

            all_amounts_sum = 0

            for real_amount_row in DeliveryMissionProduct.objects.filter(product_mission=product_mission):
                all_amounts_sum += real_amount_row.amount

            missing_amount -= all_amounts_sum

            real_amount = amount-missing_amount

            if missing_amount == 0:
                missing_amount = ""

            print(f"ABI: {real_amount}")

            products.append((product_mission,  missing_amount,  product_stock, real_amount))
            print(products)
        return products

    def get_product_stock(self, product_mission):
        product = product_mission.product
        state = product_mission.state

        if product.ean is not None and product.ean != "":
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()
            if stock is not None:
                if state is None:
                    return stock.get_total_stocks().get("Gesamt")
                else:
                    return stock.get_total_stocks().get(state)

        for sku_instance in product.sku_set.all():
            if sku_instance is not None:
                if sku_instance.sku is not None and sku_instance.sku != "":
                    stock = Stock.objects.filter(sku=sku_instance.sku).first()
                    if stock is not None:
                        if state is None:
                                return stock.get_total_stocks().get("Gesamt")
                        else:
                                return stock.get_total_stocks().get(state)

    def get_available_product_stock(self, product_mission):
        product = product_mission.product
        state = product_mission.state

        if product.ean is not None and product.ean != "":
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()
            if stock is not None:
                if state is None:
                    return stock.get_available_total_stocks().get("Gesamt")
                else:
                    return stock.get_available_total_stocks().get(state)

        for sku_instance in product.sku_set.all():
            if sku_instance is not None:
                if sku_instance.sku is not None and sku_instance.sku != "":
                    stock = Stock.objects.filter(sku=sku_instance.sku).first()
                    if stock is not None:
                        if state is None:
                                return stock.get_available_total_stocks().get("Gesamt")
                        else:
                                return stock.get_available_total_stocks().get(state)


class MissionListView(ListView):
    template_name = "mission/mission_list.html"

    def get_queryset(self):
        # queryset = filter_queryset_from_request(self.request, Mission)
        queryset = self.filter_queryset_from_request()
        return self.set_pagination(queryset)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["title"] = "Auftrag"
        context["fields"] = self.build_fields()
        context["filter_fields"] = get_filter_fields(Mission, exclude=["id", "products", "supplier_id",
                                                                       "invoice", "pickable", "modified_date",
                                                                       "created_date"])
        context["object_list_zip"] = self.add_billing_numbers_and_delivery_note_numbers_to_list(context["object_list"])

        context["option_fields"] = [
            {"status": ["WARENAUSGANG", "PICKBEREIT", "AUSSTEHEND", "OFFEN", "LIEFERUNG"]}]
        context["extra_options"] = [("complete", ["UNVOLLSTÄNDIG", "VOLLSTÄNDIG"])]
        return context

    def add_billing_numbers_and_delivery_note_numbers_to_list(self, object_list):
        billing_numbers_list = []
        delivery_note_numbers_list = []

        for mission in object_list:
            billing_numbers = []
            for delivery in mission.delivery_set.all():
                for billing in delivery.goodsissue_set.first().billing_set.all():
                    billing_numbers.append(billing.billing_number)

            billing_numbers_list.append(billing_numbers)

        for mission in object_list:
            delivery_notes = []
            for delivery in mission.delivery_set.all():
                for delivery_note in delivery.goodsissue_set.first().deliverynote_set.all():
                    delivery_notes.append(delivery_note.delivery_note_number)

            delivery_note_numbers_list.append(delivery_notes)

        return zip(object_list, billing_numbers_list, delivery_note_numbers_list)

    def build_fields(self):
        fields = get_verbose_names(Mission, exclude=["id", "supplier_id", "products", "modified_date", "created_date",
                                                     "terms_of_payment", "terms_of_delivery", "delivery_note_number",
                                                     "billing_number"])
        fields.insert(len(fields) - 1, "Fälligkeit")

        fields.insert(3, "Rechnugsnummern")
        fields.insert(4, "Lieferscheinnummern")

        fields.insert(len(fields) - 1, "Gesamt (Netto)")
        fields.insert(len(fields) - 1, "Gesamt (Brutto)")
        return fields

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object

    def filter_queryset_from_request(self):
        fields = self.get_fields(exclude=["billing_number", "delivery_note_number", "id"])
        q_filter = Q()
        for field in fields:
            get_value = self.request.GET.get(field)

            if get_value is not None and get_value != "":
                q_filter &= Q(**{f"{field}__icontains": get_value.strip()})

        search_filter = Q()
        search_value = self.request.GET.get("q")
        print(f"{search_value}")
        if search_value is not None and search_value != "":
            search_filter |= Q(**{f"mission_number__icontains": search_value.strip()})
            search_filter |= Q(delivery__goodsissue__billing__billing_number__icontains=search_value.strip())
            search_filter |= Q(delivery__goodsissue__deliverynote__delivery_note_number__icontains=search_value.strip())
            search_filter |= Q(customer__contact__billing_address__firma__icontains=search_value.strip())

        print(f"s: {search_filter}")
        q_filter &= search_filter

        billing_number = self.request.GET.get("billing_number")
        delivery_note_number = self.request.GET.get("delivery_note_number")

        if billing_number is not None and billing_number != "":
            q_filter &= Q(delivery__goodsissue__billing__billing_number__icontains=billing_number)

        if delivery_note_number is not None and delivery_note_number != "":
            q_filter &= Q(delivery__goodsissue__deliverynote__delivery_note_number__icontains=delivery_note_number)

        queryset = Mission.objects.filter(q_filter).order_by("-id").distinct()
        return queryset

    def get_fields(self, exclude=None):
        from django.db import models
        fields = []
        for field in Mission._meta.get_fields():
            if exclude is not None and len(exclude) > 0:
                if field.name in exclude:
                    continue
            if isinstance(field, models.ManyToManyField):
                continue

            if isinstance(field, models.ManyToOneRel):
                continue

            fields.append(field.name)
        return fields


class MissionCreateView(CreateView):
    template_name = "mission/form.html"
    form_class = MissionForm

    def __init__(self):
        super().__init__()
        self.object = None
        self.product_forms = []

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Auftrag anlegen"
        context["ManyToManyForms"] = self.build_product_mission_forms()
        context["detail_url"] = reverse_lazy("mission:list")
        return context

    def build_product_mission_forms(self):
        if self.request.method == "POST":
            amount_forms = self.get_amount_product_mission_forms()
            for i in range(0, amount_forms):
                data = self.get_data_from_post_on_index_x_to_form(i)
                form = ProductMissionForm(data=data)
                product = Product.objects.filter(Q(ean__exact=data.get("ean")) | Q(sku__sku=data.get("ean"))).first()
                self.product_forms.append((form, product))
        else:
            self.product_forms.append((ProductMissionForm(), None))
        return self.product_forms

    def get_data_from_post_on_index_x_to_form(self, index):
        data = {}

        for field_name in ProductMissionForm.base_fields:
            if str(field_name) in self.request.POST:
                data[str(field_name)] = self.request.POST.getlist(str(field_name))[index].strip()
        return data

    def get_amount_product_mission_forms(self):
        amount_forms = 0
        for field_name in ProductMissionForm.base_fields:
            if field_name in self.request.POST:
                amount_forms = len(self.request.POST.getlist(str(field_name)))
        return amount_forms

    def form_valid(self, form, *args, **kwargs):
        context = self.get_context_data(*args, **kwargs)
        self.object = form.save(commit=False)

        if self.validate_product_forms_are_valid() is True:
            self.create_mission_products()
            return HttpResponseRedirect(reverse_lazy("mission:detail", kwargs={"pk": self.object.pk}))
        else:
            return render(self.request, self.template_name, context)

    def validate_product_forms_are_valid(self):
        self.validate_product_forms_have_no_duplicates()
        self.validate_product_forms_have_no_skus_with_states()
        self.validate_product_forms_have_no_ean_without_states()
        product_forms_are_valid = True
        for product_form, product in self.product_forms:
            if product_form.is_valid() is False:
                product_forms_are_valid = False
        return product_forms_are_valid

    def validate_product_forms_have_no_skus_with_states(self):
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            state = product_form.data.get("state")
            print(state)
            if product is not None and product.sku_set.filter(sku=ean_or_sku).count() > 0:
                if state is not None and state != "":
                    product_form.add_error("state",
                                           ValidationError(
                                               "Wenn Sie eine SKU angeben dürfen Sie keinen Zustand auswählen"))

    def validate_product_forms_have_no_ean_without_states(self):
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            state = product_form.data.get("state")
            print(state)
            if product is not None and product.sku_set.filter(sku=ean_or_sku).count() == 0:
                if state is None or state == "":
                    product_form.add_error("state",
                                           ValidationError(
                                               "Wenn Sie eine EAN eingeben, müssen Sie einen Zustand auswählen"))

    def validate_product_forms_have_no_duplicates(self):
        duplicates = []
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            state = product_form.data.get("state")

            ean, sku = None, None
            if product is not None:
                if product.ean == ean_or_sku:
                    ean = ean_or_sku
                elif product.sku_set.filter(sku=ean_or_sku).count() > 0:
                    sku = ean_or_sku
            else:
                if (ean_or_sku, state) in duplicates:
                    product_form.add_error('ean',
                                           ValidationError(f'Der Eintrag {ean_or_sku} mit dem Zustand {state} ist'
                                                           f' doppelt'))
                duplicates.append((ean_or_sku, state))

            if ean is not None:
                if (ean, state) not in duplicates:
                    duplicates.append((ean, state))
                else:
                    product_form.add_error('ean',
                                           ValidationError(f'Diese EAN in Kombinitation mit dem Zustand {state} darf'
                                                           f' nur einmal vorkommen'))
            elif sku is not None:
                if product.ean is not None:
                    sku_instance = product.sku_set.filter(sku=ean_or_sku).first()

                    if (product.ean, sku_instance.state) not in duplicates:
                        duplicates.append((product.ean, sku_instance.state))
                    else:
                        if product.ean is not None and product.ean != "":
                            product_form.add_error('ean', ValidationError(
                                f'Dieser Artikel existiert bereits mit der EAN {product.ean} und dem Zustand'
                                f' {sku_instance.state} in diesem Auftrag'))
                        else:
                            product_form.add_error('ean', ValidationError(f'Dieser Artikel existiert bereits in diesem'
                                                                          f' Auftrag'))

    def create_mission_products(self):
        self.object.save()
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            amount = product_form.data.get("amount")
            netto_price = product_form.data.get("netto_price")

            state = product_form.data.get("state")

            product_mission_instance = ProductMission(product_id=product.pk, amount=amount, netto_price=netto_price,
                                                      mission_id=self.object.pk)
            if state is not None and state != "":
                product_mission_instance.state = state
            else:
                product_mission_instance.state = product.sku_set.filter(sku=ean_or_sku).first().state
            product_mission_instance.save()
            self.object.productmission_set.add(product_mission_instance)
        self.object.save()


class MissionUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "mission/form.html"
    login_url = "/login/"
    form_class = MissionForm

    def __init__(self):
        super().__init__()
        self.object = None
        self.product_forms = None

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
        return context

    def build_product_mission_forms(self):
        self.product_forms = []
        count = 0
        product_missions = self.object.productmission_set.all()

        for product_mission in product_missions:
            if self.request.POST:
                data = self.get_data_from_post_on_index_x_to_form(count)
                product_mission_form = ProductMissionUpdateForm(
                    data=data, product_mission=product_mission)
            else:
                ean_or_sku, state = self.get_ean_or_sku_and_state(product_mission)
                if product_mission.product.ean != ean_or_sku:
                    state = None
                data = {"ean": ean_or_sku, "amount": product_mission.amount,
                        "state": state, "netto_price": product_mission.netto_price}
                product_mission_form = ProductMissionUpdateForm(data=data, product_mission=product_mission)
            product = Product.objects.filter(Q(ean__exact=data.get("ean")) | Q(sku__sku=data.get("ean"))).first()
            self.product_forms.append((product_mission_form, product))
            count += 1

        if self.request.method == "POST":
            amount_forms = self.get_amount_product_mission_forms()
            for i in range(count, amount_forms):
                data = self.get_data_from_post_on_index_x_to_form(i)
                form = ProductMissionForm(data=data)
                product = Product.objects.filter(Q(ean__exact=data.get("ean")) | Q(sku__sku=data.get("ean"))).first()
                self.product_forms.append((form, product))
        else:
            if product_missions.count() == 0:
                self.product_forms.append((ProductMissionForm(), None))
        # no update forms
        # product_mission_form = ProductMissionForm(data=self.get_data_from_post_on_index_x_to_form(count))
        return self.product_forms

    def get_ean_or_sku_and_state(self, product_mission):
        product = product_mission.product
        ean_or_sku = None
        state = product_mission.state

        if product.ean is not None and product.ean != "":
            ean_or_sku = product.ean
        else:
            sku_instance = product.sku_set.filter(state=product_mission.state).first()
            if sku_instance is not None:
                ean_or_sku = sku_instance.sku
        return ean_or_sku, state

    def get_amount_product_mission_forms(self):
        amount_forms = 0
        for field_name in ProductMissionForm.base_fields:
            if field_name in self.request.POST:
                amount_forms = len(self.request.POST.getlist(str(field_name)))
        return amount_forms

    def get_data_from_post_on_index_x_to_form(self, index):
        data = {}

        for field_name in ProductMissionForm.base_fields:
            if str(field_name) in self.request.POST:
                data[str(field_name)] = self.request.POST.getlist(str(field_name))[index].strip()
        if "delete" in self.request.POST:
            if index < len(self.request.POST.getlist("delete")):
                data["delete"] = self.request.POST.getlist("delete")[index]
        return data

    def form_valid(self, form, **kwargs):
        context = self.get_context_data(**kwargs)
        self.object = form.save(commit=False)
        if self.validate_product_forms_are_valid() is True:
            self.create_mission_products()
            self.update_mission_products()
            return HttpResponseRedirect(self.get_success_url())
        else:
            return render(self.request, self.template_name, context)

    def validate_product_forms_are_valid(self):
        self.validate_product_forms_have_no_duplicates()
        self.validate_product_forms_have_no_skus_with_states()
        self.validate_product_forms_have_no_ean_without_states()
        self.validate_product_forms_not_deleting_or_changing_delivery_products()

        product_forms_are_valid = True

        for product_form, product in self.product_forms:
            if product_form.is_valid() is False:
                product_forms_are_valid = False
        return product_forms_are_valid

    def validate_product_forms_have_no_ean_without_states(self):
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            state = product_form.data.get("state")
            print(state)
            if product is not None and product.sku_set.filter(sku=ean_or_sku).count() == 0:
                if state is None or state == "":
                    product_form.add_error("state",
                                           ValidationError(
                                               "Wenn Sie eine EAN eingeben, müssen Sie einen Zustand auswählen"))

    def validate_product_forms_have_no_skus_with_states(self):
        for product_form, product in self.product_forms:
            ean_or_sku = product_form.data.get("ean")
            state = product_form.data.get("state")
            print(state)
            if product is not None and product.sku_set.filter(sku=ean_or_sku).count() > 0:
                if state is not None and state != "":
                    product_form.add_error("state",
                                           ValidationError(
                                               "Wenn Sie eine SKU angeben dürfen Sie keinen Zustand auswählen"))
                    product_form.data["state"] = None

    def validate_product_forms_not_deleting_or_changing_delivery_products(self):
        form_index = 0
        for product_form, product in self.product_forms:

            product_mission = None
            if hasattr(product_form, "product_mission") is True:
                product_mission = product_form.product_mission

            if product_mission is None or product_mission == "":
                continue

            delete_value = self.request.POST.getlist("delete")[form_index]

            state_value = self.request.POST.getlist("state")[form_index]

            netto_price_value = self.request.POST.getlist("netto_price")[form_index]

            sum_all_amounts = 0

            for goods_issue_delivery_mission_product in DeliveryMissionProduct.objects.\
                    filter(product_mission=product_mission):
                sum_all_amounts += goods_issue_delivery_mission_product.amount

            if sum_all_amounts > 0:

                if delete_value == "on":
                    product_form.add_error("ean",  f"Dieser Artikel hat im Auftrag Lieferungen und kann daher "
                                                   f"nicht gelöscht werden")
                    product_form.data["delete"] = "off"

                if state_value != product_mission.state:
                    if product.ean is not None and product.ean != "":
                        product_form.add_error("state", f"Dieser Artikel hat im Auftrag Lieferungen, daher kann "
                                                        f"dessen Zustand nicht geändert werden")

                        if product_form.data["state"] is not None and product_form.data["state"] != "":
                            product_form.data["state"] = product_mission.state

                if float(netto_price_value) != float(product_mission.netto_price):
                    product_form.add_error("netto_price", f"Dieser Artikel hat im Auftrag Lieferungen, daher kann "
                                                          f"dessen Einzelpreis nicht geändert werden")
                    product_form.data["netto_price"] = product_mission.netto_price

            form_index += 1

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
                        if (sku_instance.sku, sku_instance.state) not in duplicates:
                            duplicates.append((sku_instance.sku, sku_instance.state))
                        else:
                            product_form.add_error('ean', ValidationError(
                                f'Dieser Artikel existiert bereits mit der SKU {sku_instance.sku} in diesem Auftrag'))
                else:
                    product_form.add_error('ean', ValidationError(f'Dieser Artikel existiert bereits in diesem'
                                                                  f' Auftrag'))

    def update_mission_products(self):
        self.object.save()
        count = 0
        for (product_form, product), product_mission_instance in zip(self.product_forms, self.object.productmission_set.all()):
            ean_or_sku = product_form.data.get("ean")
            amount = product_form.data.get("amount")
            netto_price = product_form.data.get("netto_price")
            to_delete = product_form.data.get("delete")

            state = product_form.data.get("state")

            if product_mission_instance is not None:
                print(product_form.data)
                print(f"WAAATT ???: {ean_or_sku} - {amount} - {netto_price} - {state}")
                product_mission_instance.product_id = product.pk
                product_mission_instance.amount = amount
                product_mission_instance.netto_price = netto_price
                product_mission_instance.mission_id = self.object.pk
            else:
                product_mission_instance = ProductMission(product_id=product.pk, amount=amount, netto_price=netto_price,
                                                          mission_id=self.object.pk)

            if state is not None and state != "":
                product_mission_instance.state = state
            else:
                product_mission_instance.state = product.sku_set.filter(sku=ean_or_sku).first().state

            if to_delete == "on":
                product_mission_instance.delete()
            else:
                product_mission_instance.save()

            count += 1
        self.object.save()

    def create_mission_products(self):
        index = self.object.productmission_set.all().count()
        amount_forms = self.get_amount_product_mission_forms()
        for i in range(index, amount_forms):
            product_form, product = self.product_forms[i]
            ean_or_sku = product_form.data.get("ean")
            amount = product_form.data.get("amount")
            netto_price = product_form.data.get("netto_price")

            state = product_form.data.get("state")

            product_mission_instance = ProductMission(product_id=product.pk, amount=amount, netto_price=netto_price,
                                                      mission_id=self.object.pk)
            if state is not None and state != "":
                product_mission_instance.state = state
            else:
                product_mission_instance.state = product.sku_set.filter(sku=ean_or_sku).first().state
            product_mission_instance.save()
            self.object.productmission_set.add(product_mission_instance)
        self.object.save()


class MissionDeleteView(DeleteView):
    model = Mission
    success_url = reverse_lazy("mission:list")
    template_name = "mission/mission_confirm_delete.html"

    def get_object(self, queryset=None):
        return Mission.objects.filter(id__in=self.request.GET.getlist('item'))


class ScanMissionUpdateView(UpdateView):
    template_name = "mission/scan/scan.html"
    form_class = modelform_factory(ProductMission, fields=("confirmed",))

    def __init__(self):
        super().__init__()
        self.context = {}
        self.delivery = None
        self.delivery_products = None
        self.picklist = None

    def dispatch(self, request, *args, **kwargs):
        self.delivery = Delivery.objects.get(pk=self.kwargs.get("delivery_pk"))
        self.delivery_products = self.get_delivery_products()
        self.picklist = self.delivery.picklist_set.first()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, *args, **kwargs):
        object = Mission.objects.get(pk=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["object"] = self.get_object(*args, **kwargs)
        self.context["delivery"] = self.delivery
        self.context["title"] = "Warenausgang"
        self.context["delivery_products"] = self.delivery_products
        self.context["picklist_all_picked"] = self.is_picklist_all_picked()
        self.context["picklist_has_goods"] = self.check_if_picklist_has_goods()
        self.context["last_checked_checkbox"] = self.request.session.get("last_checked_checkbox")
        self.context["detail_url"] = reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")})
        self.context["select_range"] = range(20)
        return self.context

    def check_if_picklist_has_goods(self):
        if self.picklist is None or self.picklist == "":
            return False

        picklist_rows = self.picklist.picklistproducts_set.all()

        if picklist_rows.count() > 0:
            goods_sum = 0
            for pick_row in picklist_rows:
                if pick_row.confirmed is not None:
                    goods_sum += int(pick_row.amount_minus_missing_amount())
            if goods_sum > 0:
                return True
            else:
                return False
        else:
            return False

    def is_picklist_all_picked(self):
        if self.picklist is None or self.picklist == "":
            return False

        picklist_rows = self.picklist.picklistproducts_set.all()

        if picklist_rows.count() > 0:
            for pick_row in picklist_rows:
                if pick_row.confirmed is None:
                    return False
            return True
        else:
            return False

    def get_delivery_products(self):
        goodsissue_products = self.delivery.goodsissue_set.first().goodsissuedeliverymissionproduct_set.all()
        exclude_amount_zero_ids = []
        for goodsissue_product in goodsissue_products:
            if goodsissue_product.scan_amount() is None or goodsissue_product.scan_amount() == 0:
                exclude_amount_zero_ids.append(goodsissue_product.pk)
        return self.delivery.goodsissue_set.first().goodsissuedeliverymissionproduct_set.all().\
            exclude(pk__in=exclude_amount_zero_ids)

    def add_real_amount_to_list(self, real_amount_rows, real_amounts_list):
        for real_amount_rows_from_list in real_amounts_list:
            for query in real_amount_rows_from_list:
                for row in real_amount_rows:
                    if query.billing.billing_number == row.billing.billing_number:
                        return
        real_amounts_list.append(real_amount_rows)

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

        for delivery_product in self.delivery_products:
            if str(delivery_product.pk) == str(product_id):
                if confirmed_bool == "0":
                    delivery_product.missing_amount = missing_amount
                    delivery_product.confirmed = False
                elif confirmed_bool == "1":
                    delivery_product.missing_amount = 0
                    delivery_product.confirmed = True
                delivery_product.save()

    def store_last_checked_checkbox_in_session(self):
        self.request.session["last_checked_checkbox"] = self.request.POST.get("last_checked")
        self.request.session["sku_length"] = self.request.POST.get("sku_length")


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
        self.delivery_products = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Mission.objects.get(pk=self.kwargs.get("pk"))
        self.delivery_products = self.get_delivery_products()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.context["title"] = "Lieferung erstellen"
        self.context["object"] = self.object
        self.context["delivery_products"] = self.delivery_products
        return render(request, self.template_name, self.context)

    def get_delivery_products(self):
        delivery_products = []
        for product_mission in self.object.productmission_set.all():
            amount = product_mission.amount
            product = product_mission.product
            state = product_mission.state
            stock = self.get_stock_from_product(product, state)
            print(f"BERND: {product.title} -  {stock}")
            delivery_amount = self.get_delivery_amount(product_mission)
            if int(delivery_amount) > 0:
                delivery_products.append((product_mission, delivery_amount, stock))
            print(f"RELOAD: {delivery_amount}/{amount} --- {state} --- {stock}")
        return delivery_products

    def get_delivery_amount(self, product_mission):
        amount = self.get_current_amount(product_mission)
        product = product_mission.product
        state = product_mission.state

        product_stock = product.stock_set.first()

        if product_stock is None:
            return 0

        available_stock = product_stock.get_available_total_stocks().get(state)

        if int(available_stock) >= amount:
            return amount
        else:
            if int(available_stock) > 0:
                return available_stock
            else:
                return 0

    def get_current_amount(self, product_mission):
        current_amount = product_mission.amount
        for delivery_amount in DeliveryMissionProduct.objects.filter(product_mission=product_mission):
            current_amount -= delivery_amount.amount
        return current_amount

    def get_stock_from_product(self, product, state):
        product_stock = product.stock_set.first()

        stock_dict = None

        if product_stock is not None and product_stock != "":
            stock_dict = product.stock_set.first().get_total_stocks()

        stock = 0

        if stock_dict is not None and stock_dict != "":
            stock = stock_dict.get(state)
        return stock

    def post(self, request, *args, **kwargs):
        if len(self.delivery_products) > 0:
            self.create_delivery()
        return HttpResponseRedirect(reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")}))

    def create_delivery(self):
        delivery = Delivery(mission=self.object)
        delivery.save()
        goods_issue = GoodsIssue(delivery=delivery)
        goods_issue.save()

        bulk_instances = []
        for product_mission, amount, product_stock in self.delivery_products:
            bulk_instances.append(DeliveryMissionProduct(delivery=delivery, product_mission=product_mission,
                                                         amount=amount))
        DeliveryMissionProduct.objects.bulk_create(bulk_instances)

        goods_issue_products_bulk_instances = []
        for delivery_mission_product in bulk_instances:
            goods_issue_products_bulk_instances.append(
                GoodsIssueDeliveryMissionProduct(goods_issue=goods_issue,
                                                 delivery_mission_product=delivery_mission_product,
                                                 amount=delivery_mission_product.amount))
        GoodsIssueDeliveryMissionProduct.objects.bulk_create(goods_issue_products_bulk_instances)


class CreatePartialDeliveryNote(View):
    template_name = "mission/partial_delivery_note_form.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.goods_issue = None
        self.goods_issue_products = None
        self.picklist = None
        self.context = None

    def dispatch(self, request, *args, **kwargs):
        self.goods_issue = GoodsIssue.objects.get(pk=self.kwargs.get("goods_issue_pk"))
        self.goods_issue_products = self.get_goods_issue_products()
        self.picklist = self.goods_issue.delivery.picklist_set.first()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        self.context = self.get_context()
        self.context["form"] = BillingForm
        return render(request, self.template_name, self.context)

    def post(self, request, **kwargs):
        if len(self.goods_issue_products) > 0:

            if BillingForm(data=request.POST).is_valid() is True:
                self.create_partial_delivery()
            else:
                self.goods_issue = GoodsIssue.objects.get(pk=self.kwargs.get("goods_issue_pk"))
                self.goods_issue_products = self.get_goods_issue_products()
                self.context = self.get_context()
                self.context["form"] = BillingForm(data=self.request.POST)
                return render(request, self.template_name, self.context)
        else:
            self.cancel_partial_delivery()
        return HttpResponseRedirect(reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")}))

    def get_context(self):
        self.context = {"title": "Lieferschein erstellen", "goods_issue": self.goods_issue,
                        "goods_issue_products": self.goods_issue_products,
                        "picklist": self.picklist,
                        "picklist_all_picked": self.picklist_all_picked(),
                        "picklist_with_pick_rows_exist": self.picklist_with_pick_rows_exist(),
                        "goods_issue_has_unscanned_products": self.goods_issue_has_unscanned_products(),
                        "goods_issue_has_nothing_to_scan": self.goods_issue_has_nothing_to_scan(),
                        }

        return self.context

    def goods_issue_has_unscanned_products(self):
        to_scan_rows = self.goods_issue.goodsissuedeliverymissionproduct_set.all()

        if to_scan_rows.count() > 0:
            for to_scan_row in to_scan_rows:
                if to_scan_row.confirmed is None:
                    return True
        return False

    def goods_issue_has_nothing_to_scan(self):
        to_scan_rows = self.goods_issue.goodsissuedeliverymissionproduct_set.all()
        sum_scan_amount = 0
        if to_scan_rows.count() > 0:
            for to_scan_row in to_scan_rows:
                if to_scan_row.confirmed is None:
                    sum_scan_amount += to_scan_row.scan_amount()
        if sum_scan_amount <= 0:
            return True
        else:
            return False

    def picklist_all_picked(self):
        if self.picklist is not None and self.picklist != "":
            picklist_rows = self.picklist.picklistproducts_set.all()
            if picklist_rows.count() > 0:
                for pick_row in picklist_rows:
                    if pick_row.confirmed is None:
                        return False
                return True

    def picklist_with_pick_rows_exist(self):
        if self.picklist is not None and self.picklist != "":
            picklist_rows = self.picklist.picklistproducts_set.all()
            if picklist_rows.count() > 0:
                return True
        else:
            return False

    def get_goods_issue_products(self):

        goods_issue_products = self.goods_issue.goodsissuedeliverymissionproduct_set.all().exclude(confirmed=None)
        exclude_amount_zero_ids = []
        for goodsissue_product in goods_issue_products:
            if goodsissue_product.scan_amount() is None or goodsissue_product.scan_amount() == 0:
                exclude_amount_zero_ids.append(goodsissue_product.pk)
            elif goodsissue_product.amount_minus_missing_amount() == 0:
                exclude_amount_zero_ids.append(goodsissue_product.pk)
        goods_issue_products = goods_issue_products.exclude(pk__in=exclude_amount_zero_ids)

        return goods_issue_products

    def create_partial_delivery(self):
        bulk_instances = []

        delivery_note = DeliveryNote(goods_issue=self.goods_issue)
        delivery_note.save()

        billing = Billing(goods_issue=self.goods_issue, transport_service=self.request.POST.get("transport_service"),
                          shipping_number_of_pieces=self.request.POST.get("shipping_number_of_pieces"),
                          shipping_costs=self.request.POST.get("shipping_costs"))
        billing.save()

        for goods_issue_product in self.goods_issue_products:
            print(goods_issue_product)
            instance = DeliveryNoteProductMission(delivery_note=delivery_note, billing=billing,
                                                  amount=goods_issue_product.amount_minus_missing_amount(),
                                                  product_mission=goods_issue_product.delivery_mission_product
                                                  .product_mission)
            bulk_instances.append(instance)

        DeliveryNoteProductMission.objects.bulk_create(bulk_instances)

        for goods_issue_product in self.goods_issue_products:
            goods_issue_product.missing_amount = 0
            goods_issue_product.confirmed = None
            goods_issue_product.save()

        self.goods_issue.delivery.picklist_set.all().delete()

    def cancel_partial_delivery(self):
        goods_issue_products = self.goods_issue.goodsissuedeliverymissionproduct_set.all()

        for goods_issue_product in goods_issue_products:
            goods_issue_product.missing_amount = 0
            goods_issue_product.confirmed = None
            goods_issue_product.save()

        self.goods_issue.delivery.picklist_set.all().delete()

    def get_product_position_with_stock(self, goods_issue_product):
        product_mission = goods_issue_product.delivery_mission_product.product_mission
        sku = product_mission.product.sku_set.filter(state=product_mission.state).first()
        product_stock = Stock.objects.filter(
            Q(Q(sku=sku, zustand="") |
              Q(zustand=product_mission.state, ean_vollstaendig=product_mission.product.ean))
        ).distinct("pk").order_by("pk", '-bestand')
        to_pick_stocks = []

        for single_stock in product_stock:
            print(f"sam sam: {single_stock.lagerplatz} --- {product_mission.get_ean_or_sku()} --- {sku} ---- "
                  f"{single_stock.bestand}")

            if int(single_stock.bestand) >= int(goods_issue_product.real_amount()):
                to_pick_stocks = [(single_stock, goods_issue_product.real_amount())]
                break
            else:
                sum_to_pick_stock = 0
                for _, amount in to_pick_stocks:
                    sum_to_pick_stock += int(amount)

                current_bestand = single_stock.bestand
                print(f"sharumula: {current_bestand}")

                if sum_to_pick_stock + int(current_bestand) >= goods_issue_product.real_amount():
                    to_pick_stocks.append((single_stock, int(goods_issue_product.real_amount()) - sum_to_pick_stock))
                    break
                else:
                    to_pick_stocks.append((single_stock, current_bestand))
        print(f"??????!!-- {to_pick_stocks}")
        return to_pick_stocks

    def get_product_mission_stock(self, product_mission):
        product = product_mission.product
        state = product_mission.state
        stock = 0
        if product.ean is not None and product.ean != "":
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()

        for sku_instance in product.sku_set.all():
            if sku_instance is not None:
                if sku_instance.sku is not None and sku_instance.sku != "":
                    tmp_stock = Stock.objects.filter(sku=sku_instance.sku).first()

                    if tmp_stock is not None and tmp_stock != "" and tmp_stock != 0:
                        stock = tmp_stock
                        break
        if stock is not None and stock != 0 and stock != "":
            return stock.get_total_stocks().get(state)

    def get_product_mission_available_stock(self, product_mission):
        product = product_mission.product
        state = product_mission.state
        stock = 0
        if product.ean is not None and product.ean != "":
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()

        for sku_instance in product.sku_set.all():
            if sku_instance is not None:
                if sku_instance.sku is not None and sku_instance.sku != "":
                    tmp_stock = Stock.objects.filter(sku=sku_instance.sku).first()

                    if tmp_stock is not None and tmp_stock != "" and tmp_stock != 0:
                        stock = tmp_stock
                        break
        if stock is not None and stock != 0 and stock != "":
            return stock.get_available_total_stocks().get(state)


class CreatePickListView(View):
    template_name = "mission/create_picklist.html"

    def __init__(self):
        super().__init__()
        self.object = None
        self.delivery = None

    def dispatch(self, request, *args, **kwargs):
        self.object = Mission.objects.get(pk=self.kwargs.get("pk"))
        self.delivery = Delivery.objects.get(pk=self.kwargs.get("delivery_pk"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        context = {
            "title": "Pickliste erstellen",
            "object": self.object,
            "delivery": self.delivery,
            "pickinglist": self.get_picking_list(),
            "created_picklist": self.delivery.picklist_set.all()
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        picking_list = self.get_picking_list()
        pick_list_instance = PickList(delivery=self.delivery)
        pick_list_instance.save()

        bulk_instances = []

        for goods_issue_product, stock, position in picking_list:
            bulk_instances.append(PickListProducts(pick_list=pick_list_instance,
                                                   product_mission=
                                                   goods_issue_product.delivery_mission_product.product_mission,
                                                   position=position[0].lagerplatz, amount=position[1]))
        PickListProducts.objects.bulk_create(bulk_instances)
        return HttpResponseRedirect(reverse_lazy("mission:picklist", kwargs={"pk": self.kwargs.get("pk"),
                                                                             "delivery_pk":
                                                                                 self.kwargs.get("delivery_pk")}))

    def get_picking_list(self):
        picking_list = []
        goods_issue_products = self.get_goods_issue_products()

        for goods_issue_product, stock in goods_issue_products:
            to_pick_stocks = self.get_product_position_with_stock(goods_issue_product)

            for to_pick_stock in to_pick_stocks:
                picking_list.append((goods_issue_product, stock, to_pick_stock))
        return picking_list

    def get_product_position_with_stock(self, goods_issue_product):
        product_mission = goods_issue_product.delivery_mission_product.product_mission
        sku = product_mission.product.sku_set.filter(state=product_mission.state).first()
        product_stock = Stock.objects.filter(
            Q(Q(sku=sku, zustand="") | Q(sku=sku, zustand=None) |
              Q(zustand=product_mission.state, ean_vollstaendig=product_mission.product.ean))
        ).exclude(bestand__lt=1).distinct("lagerplatz").order_by("lagerplatz")
        to_pick_stocks = []

        for single_stock in product_stock:
            current_bestand_minus_missing_amount = single_stock.bestand - (single_stock.missing_amount or 0)

            if current_bestand_minus_missing_amount == 0:
                continue

            if int(current_bestand_minus_missing_amount) >= int(goods_issue_product.real_amount()):
                to_pick_stocks = [(single_stock, goods_issue_product.real_amount())]
                break
            else:
                sum_to_pick_stock = 0
                for _, amount in to_pick_stocks:
                    sum_to_pick_stock += int(amount)

                print(f"sharumula: {current_bestand_minus_missing_amount}")

                if sum_to_pick_stock + int(current_bestand_minus_missing_amount) >= goods_issue_product.real_amount():
                    to_pick_stocks.append((single_stock, int(goods_issue_product.real_amount()) - sum_to_pick_stock))
                    break
                else:
                    to_pick_stocks.append((single_stock, current_bestand_minus_missing_amount))
        return to_pick_stocks

    def get_goods_issue_products(self):
        goods_issue_delivery_mission_products = \
            self.delivery.goodsissue_set.first().goodsissuedeliverymissionproduct_set.all()
        smaller_or_equal_than_zero_ids = []
        for goods_issue_delivery_mission_product in goods_issue_delivery_mission_products:
            if goods_issue_delivery_mission_product.real_amount() -\
                    (goods_issue_delivery_mission_product.missing_amount or 0) <= 0:
                smaller_or_equal_than_zero_ids.append(goods_issue_delivery_mission_product.pk)

        goods_issue_products = goods_issue_delivery_mission_products.exclude(pk__in=smaller_or_equal_than_zero_ids)

        print(f"test este {goods_issue_products.count()}")
        goods_issue_product_stocks = []
        for goods_issue_product in goods_issue_products:
            stock = self.get_product_mission_stock(goods_issue_product.delivery_mission_product.product_mission)
            goods_issue_product_stocks.append(stock)
        return list(zip(goods_issue_products, goods_issue_product_stocks))

    def get_product_mission_stock(self, product_mission):
        product = product_mission.product
        state = product_mission.state
        stock = 0
        if product.ean is not None and product.ean != "":
            stock = Stock.objects.filter(ean_vollstaendig=product.ean).first()

        for sku_instance in product.sku_set.all():
            if sku_instance is not None:
                if sku_instance.sku is not None and sku_instance.sku != "":
                    tmp_stock = Stock.objects.filter(sku=sku_instance.sku).first()

                    if tmp_stock is not None and tmp_stock != "" and tmp_stock != 0:
                        stock = tmp_stock
                        break
        if stock is not None and stock != 0 and stock != "":
            return stock.get_total_stocks().get(state)


class PickListView(View):
    template_name = "mission/picklist.html"

    def __init__(self, **kwargs):
        self.delivery = None
        self.picklist = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.delivery = Delivery.objects.get(pk=self.kwargs.get("delivery_pk"))
        self.picklist = self.get_picklist()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        context = {"title": "Pickliste", "delivery": self.delivery, "picklist": self.picklist}
        return render(request, self.template_name, context)

    def get_picklist(self):
        if self.delivery.picklist_set.first() is None:
            return []  # Keine Pickliste erstellt

        picklist = self.delivery.picklist_set.first().picklistproducts_set.all().order_by("-confirmed", "position")
        pickforms = []

        for _ in picklist:
            pickforms.append(PickForm())

        return list(zip(picklist, pickforms))

    def get_validated_picklist(self, pick_id):
        picklist = self.delivery.picklist_set.first().picklistproducts_set.all().order_by("-confirmed", "position")
        pickforms = []
        for pick_row in picklist:
            if int(pick_row.pk) == int(pick_id):
                form = PickForm(data=self.request.POST)
                form_validation = form.is_valid()

                if form_validation is True:
                    missing_amount = form.cleaned_data.get("missing_amount")
                    if missing_amount > pick_row.amount:
                        form.add_error("missing_amount", f"Die Fehlende Menge darf nicht größer als "
                                                         f"{pick_row.amount} sein.")
                pickforms.append(form)
            else:
                pickforms.append(PickForm())
        return list(zip(picklist, pickforms))

    def post(self, request, *args, **kwargs):
        pick_id = self.request.GET.get("pick_id")
        pick_row = PickListProducts.objects.get(pk=pick_id)
        missing_amount = self.request.POST.get("missing_amount")
        context = self.get_context()
        if missing_amount is not None and missing_amount != "":
            validated_picklist = self.get_validated_picklist(pick_id)
            context["picklist"] = validated_picklist

            for row, pick_form in validated_picklist:
                if int(row.pk) == int(pick_id):
                    if pick_form.is_valid() is False:
                        return render(request, "mission/picklist.html", context)

            if int(missing_amount) > 0:
                pick_row.confirmed = False
                pick_row.missing_amount = missing_amount
            if int(missing_amount) == 0:
                pick_row.confirmed = True
        else:
            pick_row.confirmed = True

        pick_row.save()

        stock = Stock.objects.filter(Q(lagerplatz=pick_row.position) &
                                     Q(
                                       Q(ean_vollstaendig=pick_row.product_mission.product.ean,
                                         zustand=pick_row.product_mission.state) |
                                       Q(sku=pick_row.product_mission.product.sku_set.
                                         filter(state=pick_row.product_mission.state).first())
                                    )
                                    ).first()

        if stock.bestand-pick_row.amount_minus_missing_amount() < 1:
            stock.delete()
        else:
            stock.bestand -= pick_row.amount_minus_missing_amount()
            if stock.missing_amount is None or stock.missing_amount == "":
                stock.missing_amount = pick_row.missing_amount
            else:
                if int(stock.missing_amount) > 0:
                    if pick_row.missing_amount is not None and pick_row.missing_amount != "":
                        stock.missing_amount = int(stock.missing_amount) + int(pick_row.missing_amount)
            stock.save()

        return HttpResponseRedirect(
            reverse_lazy("mission:picklist",
                         kwargs={"pk": self.kwargs.get("pk"), "delivery_pk": self.kwargs.get("delivery_pk")}))

    def get_context(self):
        context = {"title": "Pickliste", "delivery": self.delivery}
        return context


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


class GoToPickListView(View):
    def post(self, request, *args, **kwargs):
        pick_id = self.request.POST.get("pick_id")
        picklist = PickList.objects.filter(pick_id=pick_id).first()

        if picklist is not None:
            mission = picklist.delivery.mission
            return HttpResponseRedirect(reverse_lazy("mission:picklist", kwargs={"pk": mission.pk,
                                                                                 "delivery_pk": picklist.delivery.pk}))
        else:
            messages.add_message(self.request, messages.INFO, "Pickauftrag konnte nicht gefunden werden")
            return HttpResponseRedirect(reverse_lazy("mission:list"))


class GoToScanView(View):
    def post(self, request, *args, **kwargs):
        scan_id = self.request.POST.get("scan_id")
        packlist = GoodsIssue.objects.filter(scan_id=scan_id).first()

        if packlist is not None:
            mission = packlist.delivery.mission
            return HttpResponseRedirect(reverse_lazy("mission:scan", kwargs={"pk": mission.pk,
                                                                             "delivery_pk": packlist.delivery.pk}))
        else:
            messages.add_message(self.request, messages.INFO, "Verpackerliste konnte nicht gefunden werden")
            return HttpResponseRedirect(reverse_lazy("mission:list"))
