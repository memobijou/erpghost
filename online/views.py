from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.views import generic

# Create your views here.
from django.views.generic import DetailView
from django import views
from mission.models import Mission, ProductMission, PartialMissionProduct
from stock.models import Stock
from utils.utils import get_filter_fields, get_verbose_names, set_object_ondetailview
from django.core.paginator import Paginator
from django.db.models import F, Func
import datetime
import pycountry
from django.urls import reverse_lazy


class OnlineListView(generic.ListView):
    template_name = "online/online_list.html"

    def get_queryset(self):
        queryset = self.filter_queryset_from_request().filter(channel_order_id__isnull=False)
        return self.set_pagination(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Aufträge Online"
        context["fields"] = self.build_fields()
        context["filter_fields"] = self.get_filter_fields()
        context["object_list_zip"] = self.get_object_list(context["object_list"])

        context["option_fields"] = [
            {"status": ["OFFEN", "IN BEARBEITUNG", "BEENDET"]}]
        return context

    def get_filter_fields(self):
        filter_fields = get_filter_fields(Mission, exclude=["id", "products", "supplier_id",
                                          "invoice", "pickable", "modified_date", "created_date", "confirmed",
                                                            "label_pdf"])
        filter_fields.append(("delivery", "Lieferungsnummer"))
        return filter_fields

    def get_object_list(self, object_list):
        billing_numbers_list = []
        delivery_note_numbers_list = []

        for mission in object_list:
            billing_numbers = []
            for partial in mission.partial_set.all():
                for delivery in partial.delivery_set.all():
                    if delivery.billing is not None:
                        billing_numbers.append(delivery.billing.billing_number)

            billing_numbers_list.append(billing_numbers)

        for mission in object_list:
            delivery_notes = []
            for partial in mission.partial_set.all():
                for delivery in partial.delivery_set.all():
                    if delivery.delivery_note is not None:
                        delivery_notes.append(delivery.delivery_note.delivery_note_number)

            delivery_note_numbers_list.append(delivery_notes)

        return zip(object_list, billing_numbers_list, delivery_note_numbers_list)

    def build_fields(self):
        fields = get_verbose_names(Mission, exclude=["id", "supplier_id", "products", "modified_date", "created_date",
                                                     "terms_of_payment", "terms_of_delivery", "delivery_note_number",
                                                     "billing_number", "shipping", "delivery_address_id",
                                                     "shipping_costs", "shipping_number_of_pieces", "confirmed",
                                                     "is_amazon_fba", "label_pdf", "online_picklist_id",
                                                     "purchased_date", "shipped"])

        fields.insert(4, "Lieferung")
        fields.insert(5, "Fälligkeit")

        fields.insert(len(fields), "Gesamt (Netto)")
        fields.insert(len(fields), "Gesamt (Brutto)")

        return fields

    def set_pagination(self, queryset):
        page = self.request.GET.get("page")
        paginator = Paginator(queryset, 15)
        if not page:
            page = 1
        current_page_object = paginator.page(int(page))
        return current_page_object

    def filter_queryset_from_request(self):
        fields = self.get_fields(exclude=["billing_number", "delivery_note_number", "id", "status"])
        q_filter = Q()
        for field in fields:
            get_value = self.request.GET.get(field)

            if get_value is not None and get_value != "":
                q_filter &= Q(**{f"{field}__icontains": get_value.strip()})

        status_filter = Q()

        for status in self.request.GET.getlist("status"):
            status_filter |= Q(status=status)

        q_filter &= status_filter

        delivery = self.request.GET.get("delivery")

        if delivery is not None and delivery != "":
            q_filter &= Q(partial__delivery__delivery_id__icontains=delivery.strip())

        delivery_exact = self.request.GET.get("delivery_exact")

        if delivery_exact is not None and delivery_exact != "":
            q_filter &= Q(partial__delivery__delivery_id__iexact=delivery_exact.strip())

        search_filter = Q()
        search_value = self.request.GET.get("q")

        if search_value is not None and search_value != "":
            search_filter |= Q(**{f"mission_number__icontains": search_value.strip()})
            search_filter |= Q(partial__delivery__billing__billing_number__icontains=search_value.strip())
            search_filter |= Q(partial__delivery__delivery_note__delivery_note_number__icontains=search_value.strip())
            search_filter |= Q(customer__contact__billing_address__firma__icontains=search_value.strip())
            search_filter |= Q(partial__delivery__billing__transport_service__icontains=search_value.strip())
            search_filter |= Q(customer_order_number__icontains=search_value.strip())
            search_filter |= Q(partial__delivery__delivery_id__icontains=search_value.strip())

        q_filter &= search_filter

        billing_number = self.request.GET.get("billing_number")
        delivery_note_number = self.request.GET.get("delivery_note_number")

        if billing_number is not None and billing_number != "":
            q_filter &= Q(partial__delivery__billing__billing_number__icontains=billing_number)

        if delivery_note_number is not None and delivery_note_number != "":
            q_filter &= Q(partial__delivery__deliverynote__delivery_note_number__icontains=delivery_note_number)

        queryset = Mission.objects.filter(q_filter).annotate(
             delta=Func((F('delivery_date')-datetime.date.today()), function='ABS')).order_by("delta").distinct()

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


class OnlineDetailView(DetailView):
    template_name = "online/online_detail.html"

    def __init__(self):
        super().__init__()
        self.object = None
        self.mission_products = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        self.mission_products = self.object.productmission_set.all()
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return self.object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Auftrag " + context["object"].mission_number
        set_object_ondetailview(context=context, ModelClass=Mission, exclude_fields=["id"],
                                exclude_relations=[], exclude_relation_fields={"products": ["id"]})
        context["fields"] = self.build_fields()
        context["products_from_stock"] = self.get_detail_products()
        context["is_delivery_address_national"] = self.is_delivery_address_national()
        context["label_form_link"] = self.get_label_form_link()
        print(context["is_delivery_address_national"])
        return context

    def is_delivery_address_national(self):
        if self.object.delivery_address is not None and self.object.delivery_address.country_code is not None:
            delivery_address_country_code = self.object.delivery_address.country_code
            country = pycountry.countries.get(alpha_2=delivery_address_country_code)
            print(country.name)
            print(self.object.channel.api_data.client.businessaccount_set.all())

            if country.name == "Germany":
                return True
            else:
                return False

    def get_label_form_link(self):
        if self.object.delivery_address is not None and self.object.delivery_address.country_code is not None:
            delivery_address_country_code = self.object.delivery_address.country_code
            country = pycountry.countries.get(alpha_2=delivery_address_country_code)
            transport_accounts = self.object.channel.api_data.client.businessaccount_set.all()
            for transport_account in transport_accounts:
                print(f"{transport_account.type} : {country}")
                if transport_account.type == "national" and country.name == "Germany":
                    return reverse_lazy("online:dpd_pdf", kwargs={"pk": self.object.pk,
                                                                  "business_account_pk": transport_account.pk})
                elif transport_account.type == "foreign_country" and country != "Germany":
                    return reverse_lazy("online:dhl_pdf", kwargs={"pk": self.object.pk,
                                                                  "business_account_pk": transport_account.pk})
            return ""

    def build_fields(self):
        fields = get_verbose_names(ProductMission, exclude=["id", "mission_id", "confirmed"])
        fields.insert(1, "Titel")
        fields.insert(5, "Reale Menge")
        fields[0] = "EAN / SKU"
        fields.insert(len(fields), "Gesamtpreis (Netto)")
        return fields

    def get_detail_products(self):
        detail_products = []

        for product_mission in self.mission_products:
            product_stock = self.get_product_stock(product_mission)

            amount = product_mission.amount

            missing_amount = product_mission.amount

            reserved_amount_sum = 0

            sent_amount_sum = 0

            partial_products = PartialMissionProduct.objects.filter(product_mission=product_mission)

            for partial_product in partial_products:
                reserved_amount_sum += partial_product.amount
                sent_amount_sum += partial_product.real_amount()

            sent_amount = sent_amount_sum

            missing_amount -= reserved_amount_sum

            reserved_amount = amount-missing_amount

            if missing_amount == 0:
                missing_amount = ""

            detail_products.append((product_mission,  missing_amount,  product_stock, reserved_amount, sent_amount))
        return detail_products

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

