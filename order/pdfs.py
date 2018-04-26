from django.http import HttpResponse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate
from reportlab.platypus import SimpleDocTemplate,BaseDocTemplate
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.graphics.shapes import Drawing, Line
from reportlab.platypus import Spacer
from reportlab.platypus.tables import Table, TableStyle, LongTable
from reportlab.lib.units import cm, mm
from reportlab.platypus import Frame, NextPageTemplate, PageBreakIfNotEmpty
from order.models import Order
from django.contrib.staticfiles.templatetags.staticfiles import static
from client.models import Client
from client.pdfs import get_logo_and_qr_code_from_client, create_right_align_header
from client.pdfs import CustomPdf

size_seven_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=7)
size_nine_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=9)
size_ten_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=10)
size_eleven_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=11)
size_twelve_helvetica_bold = ParagraphStyle(name="normal", fontName="Helvetica-Bold", fontSize=12)
size_nine_helvetica_bold = ParagraphStyle(name="normal", fontName="Helvetica-Bold", fontSize=9)
size_nine_helvetica_left_indent_310 = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=9,
                                                     leftIndent=310, align="RIGHT")
size_nine_helvetica_leading_10 = ParagraphStyle("adsadsa", leading=10, fontName="Helvetica", fontSize=9)

right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                             rightIndent=17)
right_align_bold_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica-Bold", fontSize=9,
                                                  rightIndent=17)
underline = "_____________________________"
spaces_13 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
spaces_6 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'

spaces_4 = "&nbsp;&nbsp;&nbsp;&nbsp;"
two_new_lines = Paragraph("<br/><br/>", style=size_nine_helvetica)
horizontal_line = Drawing(100, 1)
horizontal_line.add(Line(0, 0, 425, 0))


class OrderPdfView(View):

    @property
    def order(self):
        return Order.objects.get(pk=self.kwargs.get("pk"))

    @property
    def client(self):
        client = Client.objects.get(pk=self.request.session.get("client"))
        return client

    def get(self, request, *args, **kwargs):

        story = self.build_story()

        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)

        receiver_address_list = self.get_reciver_address_list_from_order()

        custom_pdf = CustomPdf(self.client, qr_code_url, logo_url=logo_url, receiver_address=receiver_address_list,
                               story=story)
        return custom_pdf.response

    def get_reciver_address_list_from_order(self):
        receiver_address = [self.order.supplier.contact.billing_address.firma,
                            f"{self.order.supplier.contact.billing_address.strasse} "
                            f"{self.order.supplier.contact.billing_address.hausnummer}",
                            f"{self.order.supplier.contact.billing_address.place} "
                            f"{self.order.supplier.contact.billing_address.zip}"]
        return receiver_address

    def build_story(self):
        supplier_number = self.order.supplier.supplier_number or ""
        created_date = f"{self.order.created_date.strftime('%d.%m.%Y')}"
        order_number = self.order.ordernumber
        your_delivery = f"<u>Bestellung: {order_number}</u>"
        delivery_note_title = f"<br/>Bestellung {order_number}<br/><br/>"
        delivery_date = self.order.delivery_date
        # FOOTER

        warning_list = [
            f"Bitte beachten Sie unsere Anliegerrichtlinien:<br/><br/>",
            f"Anlieferungen aufgrund von Bestellungen bedürfen einer Lieferankündigung von mindestens 24 Stunden "
            f"vor Eintreffen der Sendung. Die Ankündigung muss dabei per Mail an lager.we@btcgmbh.eu gerichtet "
            f"sein und Angaben über Bestellnummer, Lieferanschrift, Lieferdatum sowie Anzahl der Paletten und "
            f"Packstücke enthalten.<br/><br/>",
            f"Die Anlieferung kann von Montag bis Freitag in der Zeit von 08:00 bis 17:00 Uhr erfolgen. Anlieferungen"
            f" außerhalb dieser Zeiten sind nur möglich, wenn ein richtlinienkonformes Anliefern durch Verschulden"
            f" der btc GmbH nicht möglich war oder in Ausnahmefällen eine Absprache mit der btc Logistik, "
            f"Bereich Wareneingang erfolgt ist.<br/><br/>",
            f"Jeder Lieferverzug ist unverzüglich schriftlich mitzuteilen.",
        ]

        delivery_address = f"{self.order.delivery_address.firma}<br/>"

        if self.order.delivery_address.adresszusatz:
            delivery_address += f"{self.order.delivery_address.adresszusatz}<br/>"

        if self.order.delivery_address.adresszusatz2:
            delivery_address += f"{self.order.delivery_address.adresszusatz2}<br/>"

        delivery_address += f"{self.order.delivery_address.strasse} {self.order.delivery_address.hausnummer}<br/>" \
                            f"{self.order.delivery_address.zip} {self.order.delivery_address.place}"

        supplier_number_and_order_number = [
            [Paragraph("Bestellung", size_nine_helvetica_leading_10),
             Paragraph(add_new_line_to_string_at_index(order_number, 10), size_nine_helvetica_leading_10)],
            [Paragraph("Lieferanten-Nr.", size_nine_helvetica_leading_10),
             Paragraph(add_new_line_to_string_at_index(supplier_number, 10), size_nine_helvetica_leading_10)],
        ]

        date_customer_delivery_note_paragraph = create_right_align_header(created_date, x_position=260,
                                                                          additional_data=supplier_number_and_order_number)
        print(date_customer_delivery_note_paragraph)
        your_delivery_paragraph = Paragraph(your_delivery, style=size_nine_helvetica_bold)

        delivery_address_delivery_conditions_payment_conditions = self.build_conditions(delivery_date, delivery_address)

        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)

        tables_list = self.create_table()

        story = []

        story.extend(date_customer_delivery_note_paragraph)

        story.extend([
                 two_new_lines, your_delivery_paragraph, delivery_address_delivery_conditions_payment_conditions,
                 delivery_note_title_paragraph, horizontal_line]
)

        story.extend([table for table in tables_list])

        story.extend([two_new_lines, two_new_lines])

        warning_text = self.build_warning_text(warning_list)

        # print(f"JO: {warning_table_h}")
        story.extend(warning_text)
        return story

    def build_warning_text(self, warning_list):
        warning_paragraphs = []

        for warning_string in warning_list:
            warning_paragraph = Paragraph(warning_string, size_ten_helvetica)
            warning_paragraph_width, warning_paragraph_height = warning_paragraph.wrap(500, 500)
            warning_paragraphs.append(warning_paragraph)
        return warning_paragraphs

    def build_conditions(self, delivery_date, delivery_address):

        delivery_condition = self.order.terms_of_delivery

        payment_condition = self.order.terms_of_payment

        delivery_date = f"{delivery_date.strftime('%d.%m.%Y')}"

        table_data = [
            [
                Paragraph("<br/>Wichtig: Bitte immer beachten!!! <br/>Jeder Lieferverzug ist uns unverzüglich "
                          "schriftlich mitzuteilen.", size_nine_helvetica)
            ],
            [
                 Paragraph("<br/><b>Lieferadresse:</b> ", style=size_nine_helvetica),
            ],
            [
                Paragraph(delivery_address, style=size_nine_helvetica),
            ],
            [
                Paragraph(f"<br/>Lieferbedingungen: {delivery_condition}<br/>", style=size_nine_helvetica),
            ],
            [
                Paragraph(f"Zahlungsbedingungen: {payment_condition}<br/>", style=size_nine_helvetica),
            ],
            [
                Paragraph(f"Liefertermin: {delivery_date}<br/>", style=size_nine_helvetica),
            ]
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

        return table

    def create_date_customer_order_table(self, date, supplier_number, order):

        date = add_new_line_to_string_at_index(date, 10)
        supplier_number = add_new_line_to_string_at_index(supplier_number, 10)
        order = add_new_line_to_string_at_index(order, 10)

        right_table_data = [
            [
                Paragraph("Datum", style=size_nine_helvetica_leading_10), Paragraph(date, style=size_nine_helvetica_leading_10),
            ],
            [
                Paragraph("Bestellung", style=size_nine_helvetica_leading_10), Paragraph(order,
                                                                                     style=size_nine_helvetica_leading_10),
            ]
        ]

        if supplier_number is not "":
            right_table_data.append([
                Paragraph("Lieferanten-Nr.", style=size_nine_helvetica_leading_10),
                Paragraph(supplier_number, style=size_nine_helvetica_leading_10),
            ])

        right_table = Table(data=right_table_data)

        right_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
                ('TOPPADDING', (0, 0), (-1, -1), 1),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 1),

            ])
        )

        data = [
            ["", right_table],
        ]

        table = Table(data, splitByRow=True, colWidths=[300, 100])

        table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        return table

    def create_table(self):
        tables_list = []

        colwidths = [30, 68, 152, 60, 65, 65]

        data = []

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)
        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>Art-Nr.</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style),
            Paragraph("<b>Einzelpreis</b>", style=right_align_paragraph_style),
            Paragraph("<b>Betrag</b>", style=right_align_paragraph_style),

        ]

        data = []
        data.append(header)
        pos = 1

        for productorder in self.order.productorder_set.all():

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(productorder.product.ean, style=size_nine_helvetica),
                    Paragraph(productorder.product.title, style=size_nine_helvetica),
                    Paragraph(str(productorder.amount), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(productorder.netto_price),
                              style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points((productorder.netto_price*productorder.amount)),
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

        tables_list.append(table)

        total_netto = 0

        for productorder in self.order.productorder_set.all():
            total_netto += productorder.amount * productorder.netto_price

        horizontal_line_betrag = Drawing(20, 1)
        horizontal_line_betrag.add(Line(425, 0, 200, 0))

        betrag_data = [
            [
                horizontal_line,
            ],
            [
                Paragraph(f"Nettobetrag",
                          style=right_align_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto)} €", style=right_align_paragraph_style),
            ],
            [
                Paragraph(f"+ Umsatzsteuer (19,00%)", style=right_align_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto*0.19)} €", style=right_align_paragraph_style),
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
        betrag_table = Table(betrag_data, colWidths=[None, 70, 75])
        betrag_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        tables_list.append(betrag_table)

        return tables_list

        # from reportlab.lib import colors
        # table = Table(rows, hAlign='LEFT', colWidths=[doc.width/3.0]*3)
        # table.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        #                                 ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))


def add_new_line_to_string_at_index(string, index):
    if len(string) < index:
        return string
    import textwrap
    return '<br/>'.join(textwrap.wrap(string, index))


def format_number_thousand_decimal_points(number):
    number = '{:,.2f}'.format(number).replace(",", "X").replace(".", ",").replace("X", ".")
    return number
