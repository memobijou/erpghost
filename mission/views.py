from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, HttpResponseRedirect
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate
from reportlab.platypus import SimpleDocTemplate
from reportlab.platypus import XPreformatted

from product.order_mission import validate_product_order_or_mission_from_post, \
    create_product_order_or_mission_forms_from_post, update_product_order_or_mission_forms_from_post
from utils.utils import get_field_names, get_queries_as_json, set_field_names_onview, set_paginated_queryset_onview, \
    filter_queryset_from_request, get_query_as_json, get_related_as_json, get_relation_fields, set_object_ondetailview, \
    get_verbose_names, get_filter_fields, filter_complete_and_uncomplete_order_or_mission
from mission.models import Mission, ProductMission
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


class MissionDetailView(DetailView):
    def get_object(self):
        obj = get_object_or_404(Mission, pk=self.kwargs.get("pk"))
        return obj

    def get_context_data(self, *args, **kwargs):
        context = super(MissionDetailView, self).get_context_data(*args, **kwargs)
        context["title"] = "Auftrag " + context["object"].mission_number
        set_object_ondetailview(context=context, ModelClass=Mission, exclude_fields=["id"], \
                                exclude_relations=[], exclude_relation_fields={"products": ["id"]})
        context["fields"] = get_verbose_names(ProductMission, exclude=["id", "mission_id"])
        context["fields"].insert(len(context["fields"]) - 1, "Gesamtpreis (Netto)")
        return context


class MissionListView(ListView):
    def get_queryset(self):
        queryset = filter_queryset_from_request(self.request, Mission)
        queryset = filter_complete_and_uncomplete_order_or_mission(self.request, queryset, Mission)
        return queryset

    def get_context_data(self, *args, **kwargs):
        context = super(MissionListView, self).get_context_data(*args, **kwargs)
        context["title"] = "Auftrag"

        set_field_names_onview(queryset=context["object_list"], context=context, ModelClass=Mission, \
                               exclude_fields=["id", "pickable"],
                               exclude_filter_fields=["id", "pickable"])
        context["fields"] = get_verbose_names(Mission, exclude=["id", "supplier_id", "products"])
        context["fields"].insert(len(context["fields"]) - 1, "Gesamt (Netto)")
        context["fields"].insert(len(context["fields"]) - 1, "Gesamt (Brutto)")
        if context["object_list"].count() > 0:
            set_paginated_queryset_onview(context["object_list"], self.request, 15, context)
        context["filter_fields"] = get_filter_fields(Mission, exclude=["id", "products", "supplier_id",
                                                                       "invoice", "pickable"])
        context["option_fields"] = [
            {"status": ["WARENAUSGANG", "PICKBEREIT", "AUSSTEHEND", "OFFEN", "LIEFERUNG"]}]
        context["extra_options"] = [("complete", ["UNVOLLSTÄNDIG", "VOLLSTÄNDIG"])]
        return context


class MissionCreateView(CreateView):
    template_name = "mission/form.html"
    form_class = MissionForm
    amount_product_mission_forms = 1

    def get_context_data(self, *args, **kwargs):
        context = super(MissionCreateView, self).get_context_data(*args, **kwargs)
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
        self.object = form.save()

        valid_product_mission_forms = \
            validate_product_order_or_mission_from_post(ProductMissionForm, self.amount_product_mission_forms,
                                                        self.request)

        if valid_product_mission_forms is False:
            context = self.get_context_data(*args, **kwargs)
            return render(self.request, self.template_name, context)
        else:
            create_product_order_or_mission_forms_from_post(ProductMission, ProductMissionForm,
                                                            self.amount_product_mission_forms, "mission", self.object,
                                                            self.request, 0)

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

    def get_object(self):
        object = Mission.objects.get(id=self.kwargs.get("pk"))
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Auftrag {self.object.mission_number} bearbeiten"
        context["ManyToManyForms"] = self.build_product_mission_forms()
        context["detail_url"] = reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")})
        return context

    def build_product_mission_forms(self):
        product_mission_forms_list = []
        product_mission_forms_list = self.object_instances_to_forms_list(product_mission_forms_list)
        product_mission_forms_list = self.non_object_forms_to_forms_list(product_mission_forms_list)
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
        if self.request.POST and len(self.request.POST.getlist("ean")) > 1:
            for i in range(len(forms_list), len(self.request.POST.getlist("ean"))):
                    data = {}
                    for k in self.request.POST:
                        if k in ProductMissionForm.base_fields:
                            data[k] = self.request.POST.getlist(k)[i]
                    forms_list.append(ProductMissionForm(data=data))
        return forms_list

    def form_valid(self, form, **kwargs):
        self.object = form.save()

        valid_product_mission_forms = \
            validate_product_order_or_mission_from_post(ProductMissionUpdateForm,
                                                        self.object.productmission_set.all().count(), self.request)

        if valid_product_mission_forms is False:
            context = self.get_context_data(**kwargs)
            return render(self.request, self.template_name, context)
        else:
            update_product_order_or_mission_forms_from_post("productmission_set", ProductMissionUpdateForm, "mission",
                                                            self.object, self.request, ProductMission)

        return HttpResponseRedirect(self.get_success_url())


class ScanMissionUpdateView(UpdateView):
    template_name = "scan/scan.html"
    form_class = modelform_factory(ProductMission, fields=("confirmed",))

    def get_object(self, *args, **kwargs):
        object = Mission.objects.get(pk=self.kwargs.get("pk"))
        return object

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context["object"] = self.get_object(*args, **kwargs)
        context["title"] = "Warenausgang"
        product_missions = context.get("object").productmission_set.all()
        context["product_orders_or_missions"] = product_missions
        context["last_checked_checkbox"] = self.request.session.get("last_checked_checkbox")
        context["detail_url"] = reverse_lazy("mission:detail", kwargs={"pk": self.kwargs.get("pk")})
        return context

    def form_valid(self, form, *args, **kwargs):
        object_ = form.save()
        self.update_scanned_product_mission(object_)
        self.store_last_checked_checkbox_in_session()
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


size_seven_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=7)
size_nine_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=9)
size_ten_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=10)
size_eleven_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=11)
size_twelve_helvetica_bold = ParagraphStyle(name="normal", fontName="Helvetica-Bold", fontSize=12)
size_nine_helvetica_bold = ParagraphStyle(name="normal", fontName="Helvetica-Bold", fontSize=9)
size_nine_helvetica_left_indent_310 = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=9,
                                                     leftIndent=310, align="RIGHT")
underline = "_____________________________"
spaces_13 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
spaces_4 = "&nbsp;&nbsp;&nbsp;&nbsp;"
two_new_lines = Paragraph("<br/><br/>", style=size_nine_helvetica)
horizontal_line = Drawing(100, 1)
horizontal_line.add(Line(0, 0, 425, 0))


class GenerateInvoicePdf(View):
    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        doc = SimpleDocTemplate(response)

        story = self.build_story(
            sender_address="Baschar Trading Center GmbH - Orber Str. 16 - 60386 Frankfurt am Main",
            receiver_address="Impex Service GmbH<br/>Kopernikusstr.17<br/>50126 Bergheim<br/>",
            your_delivery="<u>Ihre Bestellung: 501800279</u>",
            delivery_address="<br/>Lieferadresse:<br/>"
                             "Impex Service GmbH<br/>LGZ3 / Technologiepark West<br/>"
                             "Zum Frenser Feld 11.6<br/>50127 Bergheim",
            delivery_conditions="Lieferbedingungen: CIF, Lieferung Frei Haus"
                                "<br/>Zahlungsbedingungen: 14 Tage Netto<br/>",
            delivery_note_title="<br/>Lieferschein 12352<br/><br/>",
            driver_form=f"Ware vollständig erhalten laut Lieferschein<br/><br/>"
                        f"Name Fahrer:{underline}<br/><br/>"
                        f"Kennzeichen:{underline}<br/><br/>"
                        f"Spedition:{underline}<br/><br/><br/>"
                        f"Unterschrift Fahrer/Stempel:{underline}",
            warning=f"Reklamation von Waren können wir nur anerkennen, wenn diese unverzüglich nach der"
                    f" Anlieferugn erfolgen. Bitte prüfen Sie bei Lieferungen unmittelbar die Ordnungsmäßigkeit"
                    f" der Lieferung. Sollten Mängel oder Schäden an von uns gelieferten Waren festgestellt "
                    f"werden, bitten wir Sie uns umgehend darüber zu informieren. Von Rücksendungen - ohne unsere"
                    f" vorherige Zustimmung - bitten wir abzusehen."
            ,
            date_customer_delivery_note=f"Datum{spaces_13}<b>06.03.2018"
                                        f"</b><br/>Kunde{spaces_13}<b>32442</b>"
                                        f"<br/>Lieferschein"f"{spaces_4}<b>12352</b><br/>"
        )

        #doc.build(story, onFirstPage=footer, onLaterPages=footer)
        doc.build(story)

        return response

    def build_story(self, sender_address="", receiver_address="", date_customer_delivery_note="",
                    your_delivery="", delivery_address="", delivery_conditions="", delivery_note_title="",
                    driver_form="", warning=""):
        sender_address_para = Paragraph(sender_address,
                                        style=size_seven_helvetica)
        receiver_address_para = Paragraph(receiver_address,
                                          style=size_nine_helvetica_bold)

        story = [sender_address_para, receiver_address_para]
        return story

    def create_table(self):
        data = []

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)

        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>Art-Nr.</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style)
        ]

        data.append(header)

        data.append(
            [
                Paragraph(add_new_line_to_string_at_index("1", 20),
                          style=size_nine_helvetica),
                Paragraph(add_new_line_to_string_at_index("871869263453453453453443519456123456", 20),
                          style=size_nine_helvetica),
                Paragraph(add_new_line_to_string_at_index("Sodastream", 50), style=size_nine_helvetica),
                Paragraph(add_new_line_to_string_at_index("54", 20), style=right_align_paragraph_style)
            ],
        )

        data.append(
            [
                Paragraph(add_new_line_to_string_at_index("2", 20),
                          style=size_nine_helvetica),
                Paragraph(add_new_line_to_string_at_index("8718692619456123456", 20), style=size_nine_helvetica),
                Paragraph(
                    "Sodastream EASY Wassersprudler weiß EAN: 8718692619456Sodastream EASY Wassersprudler weiß EAN: "
                    "8718692619456",
                    style=size_nine_helvetica),
                Paragraph(add_new_line_to_string_at_index("43", 20),
                          style=right_align_paragraph_style)
            ]
        )

        for i in range(0, 6):
            data.append(
                [
                    Paragraph(add_new_line_to_string_at_index(f"{i+3}", 20),
                              style=size_nine_helvetica),
                    Paragraph(add_new_line_to_string_at_index("8718692619456123456", 20), style=size_nine_helvetica),
                    Paragraph(
                        "Sodastream EASY Wassersprudler weiß EAN: 8718692619456Sodastream EASY Wassersprudler weiß EAN: "
                        "8718692619456",
                        style=size_nine_helvetica),
                    Paragraph(add_new_line_to_string_at_index("43", 20),
                              style=right_align_paragraph_style)
                ]
            )

        # from reportlab.lib import colors
        # table = Table(rows, hAlign='LEFT', colWidths=[doc.width/3.0]*3)
        # table.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        #                                 ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))

        table = Table(data)
        from reportlab.lib import colors

        table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        return table


def add_new_line_to_string_at_index(string, index):
    import textwrap
    return '<br/>'.join(textwrap.wrap(string, index))


class PageNumCanvas(canvas.Canvas):
    """
    http://code.activestate.com/recipes/546511-page-x-of-y-with-reportlab/
    http://code.activestate.com/recipes/576832/
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)
        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """
        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """
        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        page = f"Seite {self._pageNumber} von {page_count}"
        self.setFont("Helvetica", 9)
        self.drawRightString(530, 10, page)