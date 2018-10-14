from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib import messages
# Create your views here.
from django.views.generic import DetailView
from django import views
from online.models import Channel
from adress.models import Adress
from mission.models import Mission, ProductMission, PartialMissionProduct, PickListProducts
from online.tasks_import import AmazonImportTask, amazon_import_task
from product.models import Product
from stock.models import Stock
from utils.utils import get_filter_fields, get_verbose_names, set_object_ondetailview
from django.core.paginator import Paginator
from django.db.models import F, Func
import datetime
import pycountry
from django.urls import reverse_lazy
from django.views import View
from online.forms import ImportForm
from celery.result import AsyncResult
from erpghost import app


class OnlineListView(generic.ListView):
    template_name = "online/online_list.html"
    paginate_by = 15

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_fields = self.get_filter_fields()
        self.context = None

    def get_queryset(self):
        queryset = self.filter_queryset_from_request().filter(channel_order_id__isnull=False, is_online=True)
        return queryset

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Aufträge Online"
        self.context["filter_fields"] = self.filter_fields
        self.context["object_list"] = self.get_object_list()
        self.context["option_fields"] = [
            {"status": ["Offen", "Verpackt", "am Picken", "auf Station"]}
        ]
        return self.context

    def get_filter_fields(self):
        filter_fields = [("mission_number", "Auftragsnummer"), ("channel_order_id", "Fremd ID"),
                         ("delivery_date_from", "Lieferdatum von"), ("delivery_date_to", "Lieferdatum bis"),
                         ("channel", "Channel"), ("delivery_note_number", "Lieferscheinnummer"),
                         ("billing_number", "Rechnungsnummer"), ("purchased_date", "Kaufdatum"),
                         ("payment_date", "Bezahlungsdatum"), ("customer", "Kunde"),
                         ("delivery_address", "Lieferadresse"), ("tracking_number", "Tracking ID"),
                         ("status", "Status")]
        return filter_fields

    def get_object_list(self):
        object_list = self.context.get("object_list")
        status_list = []
        for obj in object_list:
            status_list.append(obj.get_online_status())
        return list(zip(object_list, status_list))

    def filter_queryset_from_request(self):
        q_filter = Q()

        mission_number = self.request.GET.get("mission_number")

        if mission_number is not None and mission_number != "":
            q_filter &= Q(mission_number__icontains=mission_number)

        channel_order_id = self.request.GET.get("channel_order_id")

        if channel_order_id is not None and channel_order_id != "":
            q_filter &= Q(channel_order_id__icontains=channel_order_id)

        tracking_number = self.request.GET.get("tracking_number")

        if tracking_number is not None and tracking_number != "":
            q_filter &= Q(tracking_number__icontains=tracking_number)

        delivery_note_number = self.request.GET.get("delivery_note_number")

        if delivery_note_number is not None and delivery_note_number != "":
            q_filter &= Q(online_picklist__online_delivery_note__delivery_note_number__icontains=delivery_note_number)

        channel = self.request.GET.get("channel")

        if channel is not None and channel != "":
            q_filter &= Q(channel__name__icontains=channel)

        print(q_filter)
        status_filter = Q()

        for status in self.request.GET.getlist("status"):
            if status == "Verpackt":
                status_filter |= Q(Q(online_picklist__completed=True) | Q(tracking_number__isnull=False))
            elif status == "Offen":
                status_filter |= Q(Q(online_picklist__isnull=True) & Q(tracking_number__isnull=True))
            elif status == "am Picken":
                status_filter |= Q(Q(online_picklist__isnull=False) & Q(tracking_number__isnull=True) &
                                   Q(online_picklist__pick_order__isnull=False))
            elif "auf Station" in status:
                status_filter |= Q(Q(online_picklist__isnull=False) & Q(online_picklist__pick_order__isnull=False)
                                   & Q(online_picklist__completed__isnull=True))

        print(f"bababbaba: {status_filter}")

        q_filter &= status_filter

        search_filter = Q()
        search_value = self.request.GET.get("q")

        if search_value is not None and search_value != "":
            search_value = search_value.strip()
            search_filter |= Q(mission_number__icontains=search_value)
            search_filter |= Q(online_picklist__online_delivery_note__delivery_note_number__icontains=search_value)
            search_filter |= Q(channel_order_id__icontains=search_value)
            search_filter |= Q(tracking_number__icontains=search_value)
            search_filter |= Q(online_picklist__online_delivery_note__delivery_note_number__icontains=search_value)
            search_filter |= Q(channel__name__icontains=search_value)
            search_filter |= Q(productmission__product__ean=search_value)
        q_filter &= search_filter

        queryset = Mission.objects.filter(q_filter).annotate(
             delta=Func((F('delivery_date_to')-datetime.date.today()), function='ABS')).order_by("delta").distinct()

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
        self.picklist_products = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        self.mission_products = self.object.productmission_set.all()
        self.get_picklist_products()
        return super().dispatch(request, *args, **kwargs)

    def get_picklist_products(self):
        picklist_products = []

        self.picklist_products = PickListProducts.objects.filter(
            product_mission__pk__in=self.mission_products.values_list("pk", flat=True))

        for mission_product in self.mission_products:
            picklist_rows = []
            product_tuple = (mission_product, picklist_rows)
            for picklist_product in self.picklist_products:
                if picklist_product.product_mission == mission_product:
                    picklist_rows.append(picklist_product)
            if len(picklist_rows) > 0:
                picklist_products.append(product_tuple)
        self.picklist_products = picklist_products

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
        context["status"] = self.object.get_online_status()
        context["picklist_products"] = self.picklist_products
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


class ImportMissionView(View):
    template_name = "online/import_missions.html"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context = None
        self.form = None
        self.header, self.result = None, None

    def dispatch(self, request, *args, **kwargs):
        self.form = self.get_form()
        self.context = self.get_context()
        profile = request.user.profile
        if profile is not None and profile.celery_import_task_id is not None:
            result = AsyncResult(request.user.profile.celery_import_task_id, app=app)
            print(result.status)
            print(f"baby 3: {result.status}")
            if result.status == "SUCCESS":
                request.user.profile.celery_import_task_id = None
                request.user.profile.save()
                messages.success(request, "Aufträge wurden erfolgreich importiert")
                return HttpResponseRedirect(reverse_lazy("online:list"))
            if result.status == "PENDING":
                self.context["still_pending"] = True

        print("But why !?")
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def get_context(self):
        self.context = {"title": "Aufträge importieren", "form": self.form}
        return self.context

    def get_form(self):
        if self.request.method == "POST":
            print("waaaas?")
            return ImportForm(self.request.POST, self.request.FILES)
        else:
            return ImportForm()

    def post(self, request, *args, **kwargs):
        self.fetch_amazon_report()
        if self.header is not None and self.result is not None:
            print(f"HELLLOOO")
            response = amazon_import_task.delay([self.header, self.result])
            print(f"baby: {response.status}")
            print(f"baby: {response.id}")
            self.request.user.profile.celery_import_task_id = response.id
            self.request.user.profile.save()
        return HttpResponseRedirect(reverse_lazy("online:import_mission"))

    def fetch_amazon_report(self):
        if self.form.is_valid() is True:
            import_file = self.form.cleaned_data.get("import_file")
            print(f"banana: {import_file.name}")
            file_ending = import_file.name.split(".")[-1]
            print(file_ending)
            if file_ending.lower() == "csv":
                from io import TextIOWrapper
                data = TextIOWrapper(import_file.file, encoding="latin1")
                self.result = self.get_csv_content(data)
                print(f"babo: {self.result}")

            if file_ending.lower() == "txt":
                content_list = import_file.readlines()
                for index, row in enumerate(content_list):
                    content_list[index] = content_list[index].decode("ISO-8859-1")

                self.header = []

                columns = content_list[:1][0].split("\t")
                for col in columns:
                    self.header.append(col)

                content_list = content_list[1:]

                print(f"Header: {len(self.header)} {self.header}")
                print(f"Content: {content_list}")

                self.result = []
                for row in content_list:
                    columns = row.split("\t")
                    columns_tuple = ()
                    for col in columns:
                        columns_tuple += (col,)
                    self.result.append(columns_tuple)
                print(self.result)
                for row in self.result:
                    if len(row) != len(self.header):
                        self.result.pop(self.result.index(row))

    def get_csv_header(self, data):
        import csv
        csv_reader = csv.reader(data, delimiter=";")
        self.header = []
        for row in csv_reader:
            if len(row) > 0:
                self.header = row
                break
        tmp_header = []
        for col in self.header:
            tmp_header.append(col.replace("\t", ""))
        self.header = tmp_header
        return self.header

    def get_csv_content(self, data):
        import csv
        self.header = self.get_csv_header(data)
        csv_iterator = csv.DictReader(data, delimiter=';', fieldnames=self.header)

        self.result = []
        for row in csv_iterator:
            print(f"DIGI: {row}")
            self.result.append(row)
        return self.result