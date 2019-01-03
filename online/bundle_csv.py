from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from mission.models import Mission
from django.shortcuts import render
from PyPDF2 import PdfFileMerger, PdfFileReader
from io import StringIO, BytesIO
from online.delivery_note import DeliveryNotePdfGenerator
from online.dpd import DPDLabelCreator
from django.urls import reverse_lazy
from django.http import QueryDict
import asyncio
from django.db.models import Count, Case, When


class ExportView(LoginRequiredMixin, View):
    template_name = "online/export/export.html"

    def __init__(self):
        super().__init__()
        self.missions = None
        self.export_missions = None
        self.non_export_missions = None
        self.context = None

    def dispatch(self, request, *args, **kwargs):
        self.missions = Mission.objects.filter(pk__in=request.GET.getlist("item"))
        self.missions = self.missions.annotate(
            main_shipment_count=Count(Case(When(shipment__main_shipment=True, then="shipment"))))
        self.export_missions = self.missions.filter(main_shipment_count__gt=0).distinct()
        self.non_export_missions = self.missions.filter(main_shipment_count=0).distinct()
        errors = []
        for _ in self.non_export_missions:
            errors.append(None)
        self.non_export_missions = self.non_export_missions
        print(f"jo: {self.missions}")
        self.context = self.get_context()
        return super().dispatch(request, *args, **kwargs)

    def get_context(self):
        context = {"export_items": self.export_missions, "non_export_items": self.non_export_missions,
                   "title": "Lieferscheine und Paketlabels exportieren"}
        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.context)

    def post(self, request, *args, **kwargs):
        pdf_response = None
        print(f"hello world: {request.POST.get('type')}")
        if request.POST.get("type") == "delivery_notes":
            print(f"perefekt ...")
            pdf_response = self.get_delivery_notes_as_pdf()

        if request.POST.get("type") == "packing_labels":
            pdf_response = self.get_packing_labels_as_pdf()

        print(f"?!?!?!: {pdf_response}")
        return pdf_response
        # return render(request, self.template_name, self.context)

    def get_delivery_notes_as_pdf(self):
        merger = PdfFileMerger()

        for export_mission in self.export_missions:
            pdf_generator = DeliveryNotePdfGenerator(shipment=export_mission.get_main_shipment())
            logo_url, qr_code_url = pdf_generator.get_logo_and_qr_code_from_client(
                self.request, export_mission.channel.client)
            pdf_generator.logo_url = logo_url
            pdf_generator.qr_code_url = qr_code_url
            pdf_file = pdf_generator.create_pdf_file()
            print(f"TESTTEST PDF: {pdf_file.response.content}")

            pdf_buffer = BytesIO(pdf_file.response.content)
            merger.append(PdfFileReader(pdf_buffer))

        pdf_response = HttpResponse(content_type='application/pdf')
        merger.write(pdf_response)
        return pdf_response

    def get_packing_labels_as_pdf(self):
        merger = PdfFileMerger()

        for export_mission in self.export_missions:
            shipment = export_mission.get_main_shipment()
            packing_label_file = shipment.label_pdf
            if packing_label_file is not None:
                pdf_buffer = BytesIO(packing_label_file.read())
                merger.append(PdfFileReader(pdf_buffer))

        pdf_response = HttpResponse(content_type='application/pdf')
        merger.write(pdf_response)
        return pdf_response


class CreatePackingLabels(LoginRequiredMixin, View):
    def __init__(self):
        super().__init__()
        self.missions = None
        self.non_label_missions = None
        self.label_missions = None
        self.packing_labels_errors = []

    def dispatch(self, request, *args, **kwargs):
        from django.db.models import Count, Case, When
        print(f"?????: {request.GET.getlist('item')}")
        self.missions = Mission.objects.filter(pk__in=request.GET.getlist("item")).distinct()
        self.missions = self.missions.annotate(
            main_shipment_count=Count(Case(When(shipment__main_shipment=True, then="shipment"))))
        self.non_label_missions = self.missions.filter(main_shipment_count=0).distinct()
        self.label_missions = self.missions.filter(main_shipment_count__gt=0).distinct()
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        to_create_labels = self.non_label_missions.filter(status__iexact="offen")
        if to_create_labels.count() > 0:
            dpd_creator = DPDLabelCreator(
                multiple_missions=to_create_labels, ignore_pickorder=True, main_shipment=True)
            tracking_numbers, message = dpd_creator.create_label()
            if message is not None and message != "":
                print(f"?????? ----- ??? {message}")
                self.packing_labels_errors.append(message)

            for error in self.packing_labels_errors:
                if error is not None:
                    return render(request, ExportView.template_name, self.get_export_view_context())

        for mission in to_create_labels:
            mission.status = "Versandbereit"
            mission.save()

        missions = self.non_label_missions | self.label_missions
        print(f"???: {missions}")

        query_dict = QueryDict(mutable=True)
        query_dict.setlist("item", missions.values_list("pk", flat=True))
        query_string = query_dict.urlencode()
        print(f"hey: {query_string}")
        return HttpResponseRedirect(reverse_lazy("online:export") + f"?" + query_string)

    def get_export_view_context(self):
        context = {"export_items": self.label_missions.all(),
                   "non_export_items": self.non_label_missions.all(),
                   "errors": self.packing_labels_errors,
                   "title": "Lieferscheine und Paketlabels exportieren"}
        return context
