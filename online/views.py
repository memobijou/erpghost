from django.db.models import Q
from django.shortcuts import render
from django.views import generic

# Create your views here.
from mission.models import Mission
from utils.utils import get_filter_fields, get_verbose_names
from django.core.paginator import Paginator
from django.db.models import F, Func
import datetime


class OnlineListView(generic.ListView):
    template_name = "online/online_list.html"

    def get_queryset(self):
        queryset = self.filter_queryset_from_request().filter(channel__isnull=True)
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
                                          "invoice", "pickable", "modified_date", "created_date", "confirmed"])
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
                                                     "shipping_costs", "shipping_number_of_pieces", "confirmed"])

        fields.insert(3, "Lieferungen")
        fields.insert(4, "Rechnugsnummern")
        fields.insert(5, "Lieferscheinnummern")
        fields.insert(6, "Fälligkeit")

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