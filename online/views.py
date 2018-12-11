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
from online.amazon_import_tasks import AmazonImportTask, amazon_import_task
from online.ebay_import_tasks import EbayImportTask, ebay_import_task
from product.models import Product, get_states_totals_and_total
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
import dateutil
from django.contrib.auth.mixins import LoginRequiredMixin


class OnlineListView(LoginRequiredMixin, generic.ListView):
    template_name = "online/online_list.html"
    paginate_by = 15

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context = None

    def dispatch(self, request, *args, **kwargs):
        if self.request.GET.get("clear_filter", "") or "" == "1":
            filter_values = {
                             "q": None, "mission_number": None, "channel_order_id": None, "delivery_date_from": None,
                             "delivery_date_to": None, "channel": None,
                             "delivery_note_number": None, "billing_number": None,
                             "purchased_date": None, "payment_date": None, "customer": None, "tracking_number": None,
                             "status": None
                             }
            print(f"bibi: {filter_values}")
            for name, value in filter_values.items():
                request.session[name] = value
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = self.filter_queryset_from_request().filter(channel_order_id__isnull=False, is_online=True)
        return queryset

    def get_context_data(self, **kwargs):
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Aufträge Online"
        self.context["object_list"] = self.get_object_list()
        self.context["option_fields"] = ["Offen", "Verpackt", "am Picken", "auf Station", "Manuell",
                                         "Artikel nicht zugeordnet", "Artikel ohne EAN", "DHL"]
        self.set_GET_values()
        return self.context

    def set_GET_values(self):
        self.context.update({"q": self.get_value_from_GET_or_session("q"),
                             "mission_number": self.get_value_from_GET_or_session("mission_number"),
                             "channel_order_id": self.get_value_from_GET_or_session("channel_order_id"),
                             "delivery_date_from": self.get_value_from_GET_or_session("delivery_date_from"),
                             "delivery_date_to": self.get_value_from_GET_or_session("delivery_date_to"),
                             "channel": self.get_value_from_GET_or_session("channel"),
                             "delivery_note_number": self.get_value_from_GET_or_session("delivery_note_number"),
                             "billing_number": self.get_value_from_GET_or_session("billing_number"),
                             "purchased_date": self.get_value_from_GET_or_session("purchased_date"),
                             "payment_date": self.get_value_from_GET_or_session("payment_date"),
                             "customer": self.get_value_from_GET_or_session("customer"),
                             "tracking_number": self.get_value_from_GET_or_session("tracking_number"),
                             "status": self.get_values_list_from_GET_or_session("status"),
                             })

    def get_values_list_from_GET_or_session(self, name):
        values_list = self.request.GET.getlist(name)
        session_values_list = self.request.session.get(name)
        print(f"ben : {session_values_list}")
        print(f"sven: {self.request.GET.get(name)}")
        if values_list != []:
            print(f"steve : {values_list}")
            self.request.session[name] = values_list
            return values_list
        elif session_values_list is not [] and session_values_list is not None:
            if self.request.GET.get("q") is not None and self.request.GET.get(name) is None:
                print("richtig")
                self.request.session[name] = []
            return self.request.session[name]
        else:
            return []

    def get_value_from_GET_or_session(self, name):
        get_value = self.request.GET.get(name)
        if get_value is not None:
            get_value = get_value.strip()
            self.request.session[name] = get_value
            return get_value
        else:
            if get_value == "":
                self.request.session[name] = ""
            return self.request.session.get(name, "") or ""

    def get_object_list(self):
        object_list = self.context.get("object_list")
        payment_totals = []

        for obj in object_list:
            payment_totals.append(self.get_payment_amounts(obj))
        missions_products = []

        need_refill_list = []
        for obj in object_list:
            mission_products = obj.productmission_set.all().get_online_stocks().annotate(
                packing_unit_amount_minus_online_total=F("packing_unit_amount")-F("online_total"))

            need_refill = None
            for mission_product in mission_products:
                print(f"hello: {mission_product.packing_unit_amount} --- {mission_product.online_total}")
                if mission_product.sku is not None:
                    if mission_product.packing_unit_amount > mission_product.online_total:
                        need_refill = True
                        break

            need_refill_list.append(need_refill)

            missions_products.append(mission_products)

        return list(zip(object_list, payment_totals, missions_products, need_refill_list))

    def get_payment_amounts(self, obj):
        total, discount, shipping_discount, shipping_price = 0.0, 0.0, 0.0, 0.0
        for mission_product in obj.productmission_set.all():
            total += mission_product.amount*mission_product.brutto_price or 0.0
            discount += mission_product.discount or 0.0
            shipping_discount += mission_product.shipping_discount or 0.0
            shipping_price += mission_product.shipping_price or 0.0
        return {"payment_total": total, "total_discount": discount, "total_shipping_discount": shipping_discount,
                "shipping_price": shipping_price, "shipping_discount": shipping_discount}

    def filter_queryset_from_request(self):
        q_filter = Q()

        mission_number = self.get_value_from_GET_or_session("mission_number")

        if mission_number != "":
            q_filter &= Q(mission_number__icontains=mission_number)

        channel_order_id = self.get_value_from_GET_or_session("channel_order_id")

        if channel_order_id != "":
            q_filter &= Q(channel_order_id__icontains=channel_order_id)

        tracking_number = self.get_value_from_GET_or_session("tracking_number")

        if tracking_number != "":
            q_filter &= Q(tracking_number__icontains=tracking_number)

        delivery_note_number = self.get_value_from_GET_or_session("delivery_note_number")

        if delivery_note_number != "":
            q_filter &= Q(online_picklist__online_delivery_note__delivery_note_number__icontains=delivery_note_number)

        channel = self.get_value_from_GET_or_session("channel")

        if channel != "":
            q_filter &= Q(channel__name__icontains=channel)

        purchased_date = self.get_value_from_GET_or_session("purchased_date")

        if purchased_date != "":
            purchased_date = dateutil.parser.parse(purchased_date, ignoretz=True, dayfirst=True)
            print(f"babababa: {purchased_date}")
            q_filter &= Q(purchased_date__year=purchased_date.year, purchased_date__month=purchased_date.month,
                          purchased_date__day=purchased_date.day)

        payment_date = self.get_value_from_GET_or_session("payment_date")

        if payment_date != "":
            payment_date = dateutil.parser.parse(payment_date, ignoretz=True, dayfirst=True)
            print(f"babababa: {payment_date} - {payment_date.year} - {payment_date.month} - {payment_date.day}")
            q_filter &= Q(payment_date__year=payment_date.year, payment_date__month=payment_date.month,
                          payment_date__day=payment_date.day)

        delivery_date_from = self.get_value_from_GET_or_session("delivery_date_from")

        if delivery_date_from != "":
            delivery_date_from = dateutil.parser.parse(delivery_date_from, ignoretz=True, dayfirst=True)
            print(f"babababa: {delivery_date_from}")
            q_filter &= Q(delivery_date_from__year=delivery_date_from.year,
                          delivery_date_from__month=delivery_date_from.month,
                          delivery_date_from__day=delivery_date_from.day)

        delivery_date_to = self.get_value_from_GET_or_session("delivery_date_to")

        if delivery_date_to != "":
            delivery_date_to = dateutil.parser.parse(delivery_date_to, ignoretz=True, dayfirst=True)
            print(f"babababa: {delivery_date_to}")
            q_filter &= Q(delivery_date_to__year=delivery_date_to.year,
                          delivery_date_to__month=delivery_date_to.month,
                          delivery_date_to__day=delivery_date_to.day)
        print(q_filter)
        status_filter = Q()

        status_list = self.get_values_list_from_GET_or_session("status")
        print(f"status_list {status_list}")

        for status in status_list:
            if status == "Verpackt":
                status_filter |= Q(status__iexact="Verpackt")
            elif status == "Offen":
                status_filter |= Q(status__iexact="Offen")
            elif status == "am Picken":
                status_filter |= Q(status__iexact="am Picken")
            elif "auf Station" in status:
                status_filter |= Q(status__icontains="auf Station")
            elif status == "Manuell":
                status_filter |= Q(status__iexact="Manuell")
            elif status == "Artikel nicht zugeordnet":
                status_filter |= Q(status__iexact="Artikel nicht zugeordnet")
            elif status == "Artikel ohne EAN":
                status_filter |= Q(status__iexact="Artikel ohne EAN")
            elif status == "DHL":
                status_filter |= Q(status__iexact="DHL")

        print(f"bababbaba: {status_filter}")

        q_filter &= status_filter

        search_filter = Q()
        search_value = self.get_value_from_GET_or_session("q")

        if search_value is not None and search_value != "":
            search_value = search_value.strip()
            search_filter |= Q(mission_number__icontains=search_value)
            search_filter |= Q(online_picklist__online_delivery_note__delivery_note_number__icontains=search_value)
            search_filter |= Q(channel_order_id__icontains=search_value)
            search_filter |= Q(tracking_number__icontains=search_value)
            search_filter |= Q(online_picklist__online_delivery_note__delivery_note_number__icontains=search_value)
            search_filter |= Q(channel__name__icontains=search_value)
            search_filter |= Q(productmission__sku__product__ean__icontains=search_value)
            search_filter |= Q(productmission__sku__sku__iexact=search_value)

        q_filter &= search_filter

        from django.db.models.functions import Now
        from django.db.models import DurationField, Case, When

        queryset = Mission.objects.filter(q_filter).annotate(delta=Case(
            When(purchased_date__gte=Now(), then=F('purchased_date') - Now()),
            When(purchased_date__lt=Now(), then=Now() - F('purchased_date')),
            output_field=DurationField())).order_by("delta").distinct()

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
        self.need_refill = None
        self.context = None

    def dispatch(self, request, *args, **kwargs):
        self.object = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        self.mission_products = self.object.productmission_set.all()
        self.mission_products = self.mission_products.get_online_stocks().annotate(
                packing_unit_amount_minus_online_total=F("packing_unit_amount")-F("online_total"))

        for mission_product in self.mission_products:
            print(f"hello: {mission_product.packing_unit_amount} --- {mission_product.online_total}")
            if mission_product.sku is not None:
                if mission_product.packing_unit_amount > mission_product.online_total:
                    self.need_refill = True

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
        self.context = super().get_context_data(**kwargs)
        self.context["title"] = "Auftrag " + self.object.mission_number
        self.context["fields"] = self.build_fields()
        self.context["mission_products"] = self.mission_products
        self.context["status"] = self.object.status
        self.context["picklist_products"] = self.picklist_products
        self.context["need_refill"] = self.need_refill
        self.set_payment_amounts_in_context()
        return self.context

    def set_payment_amounts_in_context(self):
        total, discount, shipping_discount, shipping_price = 0.0, 0.0, 0.0, 0.0
        for mission_product in self.mission_products:
            total += mission_product.amount*mission_product.brutto_price or 0.0
            discount += mission_product.discount or 0.0
            shipping_discount += mission_product.shipping_discount or 0.0
            shipping_price += mission_product.shipping_price or 0.0
        self.context.update({"payment_total": total, "total_discount": discount,
                             "total_shipping_discount": shipping_discount, "shipping_price": shipping_price,
                             "shipping_discount": shipping_discount})

    def build_fields(self):
        fields = get_verbose_names(ProductMission, exclude=["id", "mission_id", "confirmed"])
        fields.insert(1, "Titel")
        fields.insert(5, "Reale Menge")
        fields[0] = "EAN / SKU"
        fields.insert(len(fields), "Gesamtpreis (Netto)")
        return fields


class ImportMissionBaseView(LoginRequiredMixin, View):
    class Meta:
        abstract = True

    template_name = None
    title = None
    success_url = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context = None
        self.form = None
        self.header, self.result = None, None

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def get_context(self):
        self.context = {"title": self.title, "form": self.form}
        return self.context

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
                return HttpResponseRedirect(self.success_url)
            if result.status == "PENDING":
                self.context["still_pending"] = True

        print("But why !?")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        if self.request.method == "POST":
            print("waaaas?")
            return ImportForm(self.request.POST, self.request.FILES)
        else:
            return ImportForm()


class ImportMissionAmazonView(ImportMissionBaseView):
    template_name = "online/import_amazon_missions.html"
    title = "Amazon Bestellbericht importieren"
    success_url = reverse_lazy("online:import_amazon_mission")

    def post(self, request, *args, **kwargs):
        self.fetch_amazon_report()
        if self.header is not None and self.result is not None:
            print(f"HELLLOOO")
            response = amazon_import_task.delay([self.header, self.result])
            print(f"baby: {response.status}")
            print(f"baby: {response.id}")
            self.request.user.profile.celery_import_task_id = response.id
            self.request.user.profile.save()
        return HttpResponseRedirect(self.success_url)

    def fetch_amazon_report(self):
        if self.form.is_valid() is True:
            import_file = self.form.cleaned_data.get("import_file")
            print(f"banana: {import_file.name}")
            file_ending = import_file.name.split(".")[-1]
            print(file_ending)

            if file_ending.lower() == "txt":
                content_list = import_file.readlines()
                for index, row in enumerate(content_list):
                    # content_list[index] = content_list[index].decode("ISO-8859-1")
                    content_list[index] = content_list[index].decode("utf-8")

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


class IgnoreOnlineMissionView(LoginRequiredMixin, View):
    template_name = "online/ignore_pickorder.html"

    def __init__(self):
        super().__init__()
        self.items = None

    def dispatch(self, request, *args, **kwargs):
        self.items = self.get_items()
        return super().dispatch(request, *args, **kwargs)

    def get_items(self):
        return Mission.objects.filter(pk__in=self.request.GET.getlist("item"), is_online=True).exclude(
            Q(Q(online_picklist__completed=True) | Q(ignore_pickorder=True) | Q(online_picklist__isnull=False))
        )

    def get(self, request, *args, **kwargs):
        context = {"title": "Von Pickauftrag ablösen", "items": self.items}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        for item in self.items:
            item.ignore_pickorder = True
            item.save()
        return HttpResponseRedirect(reverse_lazy("online:list"))


class ImportMissionEbayView(ImportMissionBaseView):
    template_name = "online/import_ebay_missions.html"
    success_url = reverse_lazy("online:import_ebay_mission")
    title = "Ebay Bestellbericht importieren"

    def post(self, request, *args, **kwargs):
        print("FLANKE")
        self.fetch_ebay_report()
        if self.header is not None and self.result is not None:
            print(f"HELLLOOO")
            response = ebay_import_task.delay([self.header, self.result])
            print(f"baby: {response.status}")
            print(f"baby: {response.id}")
            self.request.user.profile.celery_import_task_id = response.id
            self.request.user.profile.save()
        return HttpResponseRedirect(self.success_url)

    def fetch_ebay_report(self):
        if self.form.is_valid() is True:
            import csv
            import codecs
            import_file = self.form.cleaned_data.get("import_file")
            import chardet
            encoding = chardet.detect(import_file.read()).get("encoding", "utf-8")
            # import_file = codecs.EncodedFile(import_file, encoding)
            import_file.seek(0)

            print(f"hadha: {encoding}")
            print(f"banana: {import_file.name}")
            print(f"apple: {import_file.charset}")
            file_ending = import_file.name.split(".")[-1]
            print(file_ending)
            if file_ending.lower() == "csv":
                print(f"??????????????")
                print(f"sam: {import_file.read()}")
                import_file.seek(0)
                from io import TextIOWrapper
                data = TextIOWrapper(import_file.file, encoding=encoding)
                # data = codecs.iterdecode(import_file, encoding)
                if encoding.lower() != "windows-1252":
                    self.header = self.get_csv_header(data)
                    self.result = self.get_csv_content(data)
                    print(f"HEADER: {self.header}")
                    print(f"babo: {self.result}")

    def get_csv_header(self, data):
        import csv
        csv_reader = csv.reader(data, delimiter=";")
        self.header = []
        for row in csv_reader:
            print(f"hey: {len(row)}")
            print(f"what: {row}")
            if len(row) > 0:
                found_header = False
                for col in row:
                    print(f"hehe: {col}")
                    if col != "":
                        self.header = row
                        found_header = True
                        break
                if found_header is True:
                    break

        tmp_header = []
        for col in self.header:
            tmp_header.append(col.replace("\t", ""))
        self.header = tmp_header
        print(f"header and so: {self.header}")
        return self.header

    def get_csv_content(self, data):
        import csv
        csv_iterator = csv.DictReader(data, delimiter=';', fieldnames=self.header)

        self.result = []
        for row in csv_iterator:
            print(f"DIGI: {row}")
            self.result.append(row)
        return self.result
