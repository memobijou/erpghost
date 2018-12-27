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
        export_condition = Q(
            Q(status__iexact="verpackt", online_picklist__completed=True)
            | Q(delivery_note__isnull=False, status__iexact="Von Pickauftrag abgelöst")
        )
        self.export_missions = self.missions.filter(export_condition)
        self.non_export_missions = self.missions.filter(~export_condition)
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
            pdf_generator = DeliveryNotePdfGenerator(mission=export_mission)
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
            packing_label_file = export_mission.label_pdf
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
        self.has_label_condition = None

    def dispatch(self, request, *args, **kwargs):
        print(f"?????: {request.GET.getlist('item')}")
        self.missions = Mission.objects.filter(pk__in=request.GET.getlist("item"))
        self.has_label_condition = Q(
            Q(status__iexact="verpackt", online_picklist__completed=True)
            | Q(delivery_note__isnull=False, status__iexact="Von Pickauftrag abgelöst")
        )
        self.non_label_missions = self.missions.filter(~self.has_label_condition)
        self.label_missions = self.missions.filter(self.has_label_condition)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        to_create_labels = self.non_label_missions.filter(status__iexact="offen")
        if to_create_labels.count() > 0:
            dpd_creator = DPDLabelCreator(multiple_missions=to_create_labels, ignore_pickorder=True)
            tracking_numbers, message = dpd_creator.create_label()
            if message is not None and message != "":
                print(f"?????? ----- ??? {message}")
                self.packing_labels_errors.append(message)

            for error in self.packing_labels_errors:
                if error is not None:
                    return render(request, ExportView.template_name, self.get_export_view_context())

        missions = self.non_label_missions | self.label_missions
        print(f"???: {missions}")
        query_dict = QueryDict(mutable=True)
        query_dict.setlist("item", missions.values_list("pk", flat=True))
        query_string = query_dict.urlencode()
        print(f"hey: {query_string}")
        return HttpResponseRedirect(reverse_lazy("online:export") + f"?" + query_string)

    def get_export_view_context(self):
        context = {"export_items": self.label_missions.filter(self.has_label_condition),
                   "non_export_items": self.non_label_missions.filter(~self.has_label_condition),
                   "errors": self.packing_labels_errors,
                   "title": "Lieferscheine und Paketlabels exportieren"}
        return context
