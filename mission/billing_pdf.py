from django.shortcuts import render
from django.views import View
from reportlab.platypus import KeepTogether
from reportlab.platypus import LongTable

from client.pdfs import CustomPdf, format_number_thousand_decimal_points, right_align_bold_paragraph_style
from client.pdfs import get_logo_and_qr_code_from_client, create_right_align_header, size_nine_helvetica_leading_10, \
    add_new_line_to_string_at_index, get_reciver_address_list_from_object, size_nine_helvetica_bold, two_new_lines, \
    get_delivery_address_html_string_from_object, size_nine_helvetica, Table, TableStyle, size_twelve_helvetica_bold, \
    horizontal_line, size_ten_helvetica, underline, size_seven_helvetica
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from mission.models import Mission
from client.models import Client
from reportlab.graphics.shapes import Drawing, Line, colors


mission_horizontal_line = Drawing(100, 1)
mission_horizontal_line.add(Line(0, 0, 423, 0))


class BillingPdfView(View):

    @property
    def mission(self):
        return Mission.objects.get(pk=self.kwargs.get("pk"))

    @property
    def client(self):
        client = Client.objects.get(pk=self.request.session.get("client"))
        return client

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partial_billing_number = None
        self.story = []
        self.delivery_date = None

    def dispatch(self, request, *args, **kwargs):
        self.delivery_date = self.mission.delivery_date
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        exception = self.validate_pdf()
        if exception is not None:
            return exception
        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)
        story = self.build_story()
        receiver_address = get_reciver_address_list_from_object(self.mission.customer)
        custom_pdf = CustomPdf(self.client, qr_code_url, logo_url=logo_url, story=story,
                               receiver_address=receiver_address)
        return custom_pdf.response

    def build_story(self):

        your_mission_number = f"<u>Unsere Auftragsnummer: {self.mission.mission_number}</u>"
        print(self.mission.customer_order_number)
        if self.mission.customer_order_number is not None and self.mission.customer_order_number != "":
            your_mission_number = f"<u> Ihrer Bestellung: {self.mission.customer_order_number}</u>"

        your_delivery_paragraph = Paragraph(your_mission_number, style=size_nine_helvetica_bold)

        self.build_right_align_header()

        self.story.extend([your_delivery_paragraph])

        self.build_before_table()

        self.build_table_title()

        self.build_table()

        self.build_after_table()

        return self.story

    def build_right_align_header(self):
        created_date = f"{self.mission.created_date.strftime('%d.%m.%Y')}"
        mission_number = self.mission.mission_number
        billing_number = self.mission.billing_number

        if self.partial_billing_number is not None:
            billing_number = self.partial_billing_number

        right_align_header_data = []

        if self.mission.customer_order_number is not None and self.mission.customer_order_number != "":
            print(self.mission.customer_order_number)
            right_align_header_data.append(
                [
                    Paragraph("Ihre Bestellung", style=size_nine_helvetica_leading_10),
                    Paragraph(add_new_line_to_string_at_index(self.mission.customer_order_number, 20),
                              style=size_nine_helvetica_leading_10),
                ],
            )

        right_align_header_data.append(
            [
                Paragraph("Unser Auftrag", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(mission_number, 20), style=size_nine_helvetica_leading_10),
            ],
        )

        right_align_header_data.append([
            Paragraph("Rechnungs-Nr.", style=size_nine_helvetica_leading_10),
            Paragraph(add_new_line_to_string_at_index(billing_number, 20), style=size_nine_helvetica_leading_10),
        ])

        if self.mission.customer is not None:
            customer_number = self.mission.customer.customer_number or ""
            right_align_header_data.append([
                Paragraph("Kunden-Nr.", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(customer_number, 20), style=size_nine_helvetica_leading_10),
            ])

        self.story.extend(create_right_align_header(created_date, additional_data=right_align_header_data))

    def build_before_table(self):
        warning_text = "<br/>Sehr geehrte Damen, sehr geehrte Herren, wir danken für Ihren Auftrag, den wir unter " \
                       "Zugrundelegung unserer vereinbarten Liefer- und Zahlungsbedingungen und vorbehaltlich einer " \
                       "durchzuführenden internen Abstimmung Ihrer Bestellung annehmen. Die Preise auf dieser " \
                       "Auftragsbestätigung verstehen sich als Netto- Preise nach Abzug von eventuell bestehenden " \
                       "Rechnungsrabatten."
        warning_paragraph = Paragraph(warning_text, size_nine_helvetica)

        delivery_address_object = self.mission.customer.contact.delivery_address

        delivery_address_html_string = get_delivery_address_html_string_from_object(delivery_address_object)
        delivery_date = self.delivery_date
        terms_of_delivery = self.mission.terms_of_delivery
        terms_of_payment = self.mission.terms_of_payment

        table_data = [
            [
                warning_paragraph
             ],
            [
                Paragraph(f"<br/><b>Liefertermin:</b> {delivery_date.strftime('%d.%m.%Y')}<br/>",
                          style=size_twelve_helvetica_bold),
            ],
            [
                 Paragraph("<br/>Lieferadresse: ", style=size_nine_helvetica),
            ],
            [
                Paragraph(delivery_address_html_string, style=size_nine_helvetica),
            ],
            [
                Paragraph(f"<br/>Lieferbedingungen: {terms_of_delivery}<br/>", style=size_nine_helvetica),
            ],
            [
                Paragraph(f"Zahlungsbedingungen: {terms_of_payment}<br/>", style=size_nine_helvetica),
            ],
        ]
        table = Table(table_data)
        table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )
        table_width, table_height = table.wrap(440, 0)

        self.story.append(table)

    def build_table_title(self):
        billing_number = self.mission.billing_number

        if self.partial_billing_number is not None:
            billing_number = self.partial_billing_number

        delivery_note_title = f"<br/>Rechnung {billing_number}<br/><br/>"
        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)
        delivery_note_title_warning = f"Das Rechnungsdatum entspricht dem Leistungsdatum<br/>"
        delivery_note_title_warning_paragraph = Paragraph(delivery_note_title_warning, size_seven_helvetica)

        self.story.extend([delivery_note_title_paragraph, delivery_note_title_warning_paragraph,
                           mission_horizontal_line])

    def build_table(self):
        colwidths = [30, 68, 152, 60, 65, 65]

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)
        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>EAN / SKU</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style),
            Paragraph("<b>Einzelpreis</b>", style=right_align_paragraph_style),
            Paragraph("<b>Betrag</b>", style=right_align_paragraph_style),
        ]

        data = []
        data.append(header)
        pos = 1

        for productmission in self.mission.productmission_set.all():

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(productmission.get_ean_or_sku(), style=size_nine_helvetica),
                    Paragraph(productmission.product.title, style=size_nine_helvetica),
                    Paragraph(str(productmission.amount), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(productmission.netto_price),
                              style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(
                        (productmission.netto_price * productmission.amount)),
                              style=right_align_paragraph_style),
                ],
            )

            pos += 1
        table = LongTable(data, splitByRow=True, colWidths=colwidths, repeatRows=1)
        table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        total_netto = 0

        for productmission in self.mission.productmission_set.all():
            total_netto += productmission.amount * productmission.netto_price

        horizontal_line_betrag = Drawing(20, 1)
        horizontal_line_betrag.add(Line(425, 0, 200, 0))

        betrag_data = [
            [
                Paragraph(f"Nettobetrag",
                          style=right_align_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto)} €", style=right_align_paragraph_style),
            ],
            [
                Paragraph(f"+ Umsatzsteuer (19,00%)", style=right_align_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto*0.19)} €",
                          style=right_align_paragraph_style),
            ],
            [
                horizontal_line_betrag,
            ],
            [
                Paragraph(f"GESAMT", style=right_align_bold_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto+(total_netto*0.19))} €",
                          style=right_align_bold_paragraph_style),
            ]
        ]
        betrag_table = Table(betrag_data, colWidths=[None, 90, 75])
        betrag_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        self.story.extend([table, mission_horizontal_line, KeepTogether(betrag_table)])

        # from reportlab.lib import colors
        # table = Table(rows, hAlign='LEFT', colWidths=[doc.width/3.0]*3)
        # table.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        #                                 ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))

    def build_after_table(self):
        first_warning_text = f"Es gelten die Allgemeinen Verkaufsbedingungen der " \
                             f"{self.client.name}.<br/>"\
                             f"Verkauf erfolgt unter Zugrundelegung unserer Allgemeinen Geschäftsbedingungen.<br/>"\
                             f"AGB's gelesen und Akzeptiert.<br/>"
        if self.client.contact.website_conditions_link is not None\
                and self.client.contact.website_conditions_link != "":
            abg_text = f"Es besteht auch die Möglichkeit, die Bedingungen unter folgender Internet-Adresse " \
                       f"einzusehen, herunterzuladen oder auszudrucken: " \
                       f"{self.client.contact.website_conditions_link}."
            first_warning_text += abg_text
        first_warning_paragraph = Paragraph(first_warning_text, size_ten_helvetica)

        first_warning_data = [
            [first_warning_paragraph, Paragraph("", size_ten_helvetica)],
        ]

        first_warning_table = Table(first_warning_data, colWidths=[430, 10], spaceBefore=20)

        first_warning_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        self.story.extend([first_warning_table])

    def validate_pdf(self, *args, **kwargs):
        context = {"title": "PDF Fehler",
                   "object": self.mission
                   }
        template_name = "mission/pdf_exception.html"

        if self.mission.customer is None or self.mission.customer.contact is None:
            context["message"] = "Sie müssen dem Auftrag einen Kunden zuweisen, um eine PDF zu generieren."
            return render(self.request, template_name, context)
        if self.mission.terms_of_delivery is None or self.mission.terms_of_delivery == "":
            context["message"] = "Sie müssen eine Lieferkondition angeben, um eine PDF zu generieren."
            return render(self.request, template_name, context)
        if self.mission.terms_of_payment is None or self.mission.terms_of_payment == "":
            context["message"] = "Sie müssen eine Zahlungsbedingung angeben, um eine PDF zu generieren."
            return render(self.request, template_name, context)
        if self.mission.productmission_set.count() == 0:
            context["message"] = "Der Auftrag muss mindestens einen Artikel beinhalten, um eine PDF zu generieren."
            return render(self.request, template_name, context)