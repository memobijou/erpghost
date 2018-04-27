from django.views import View
from reportlab.platypus import KeepTogether
from reportlab.platypus import LongTable

from client.pdfs import CustomPdf, format_number_thousand_decimal_points, right_align_bold_paragraph_style
from client.pdfs import get_logo_and_qr_code_from_client, create_right_align_header, size_nine_helvetica_leading_10, \
    add_new_line_to_string_at_index, get_reciver_address_list_from_object, size_nine_helvetica_bold, two_new_lines, \
    get_delivery_address_html_string_from_object, size_nine_helvetica, Table, TableStyle, size_twelve_helvetica_bold, \
    horizontal_line, size_ten_helvetica, underline
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from order.models import Order
from client.models import Client
from reportlab.graphics.shapes import Drawing, Line, colors


order_horizontal_line = Drawing(100, 1)
order_horizontal_line.add(Line(0, 0, 423, 0))


class OrderPdfView(View):

    @property
    def order(self):
        return Order.objects.get(pk=self.kwargs.get("pk"))

    @property
    def client(self):
        client = Client.objects.get(pk=self.request.session.get("client"))
        return client

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.story = []

    def get(self, request, *args, **kwargs):
        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)
        story = self.build_story()
        receiver_address = get_reciver_address_list_from_object(self.order.supplier)
        custom_pdf = CustomPdf(self.client, qr_code_url, logo_url=logo_url, story=story,
                               receiver_address=receiver_address)
        return custom_pdf.response

    def build_story(self):
        order_number = self.order.ordernumber

        order_number_html = f"<u>Bestellung: {order_number}</u>"

        order_paragraph = Paragraph(order_number_html, style=size_nine_helvetica_bold)

        self.build_right_align_header()

        self.story.extend([two_new_lines, order_paragraph])

        self.build_before_table()

        self.build_table_title()

        self.build_table()

        self.build_after_table()

        return self.story

    def build_right_align_header(self):
        created_date = f"{self.order.created_date.strftime('%d.%m.%Y')}"
        order_number = self.order.ordernumber

        right_align_header_data = []

        right_align_header_data.append(
            [
                Paragraph("Bestellung", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(order_number, 10), style=size_nine_helvetica_leading_10),
            ],
        )

        if self.order.supplier is not None:
            supplier_number = self.order.supplier.supplier_number or ""
            right_align_header_data.append([
                Paragraph("Lieferanten-Nr.", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(supplier_number, 10), style=size_nine_helvetica_leading_10),
            ])

        self.story.extend(create_right_align_header(created_date, additional_data=right_align_header_data,
                                                    x_position=260))

    def build_before_table(self):
        delivery_address_object = self.client.contact.delivery_address

        if self.order.delivery_address is not None:
            delivery_address_object = self.order.delivery_address

        delivery_address_html_string = get_delivery_address_html_string_from_object(delivery_address_object)
        delivery_date = self.order.delivery_date
        terms_of_delivery = self.order.terms_of_delivery
        terms_of_payment = self.order.terms_of_payment

        table_data = [
            [
                Paragraph("<br/>Wichtig: Bitte immer beachten!!! <br/>Jeder Lieferverzug ist uns unverzüglich "
                          "schriftlich mitzuteilen.", size_nine_helvetica)
            ],
            [
                 Paragraph("<br/><b>Lieferadresse:</b> ", style=size_nine_helvetica),
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
            [
                Paragraph(f"Liefertermin: {delivery_date.strftime('%d.%m.%Y')}<br/>", style=size_nine_helvetica),
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

        self.story.append(table)

    def build_table_title(self):
        order_title = f"<br/>Bestellung<br/><br/>"
        order_title_paragraph = Paragraph(order_title, size_twelve_helvetica_bold)
        self.story.extend([order_title_paragraph, order_horizontal_line])

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

        for productorder in self.order.productorder_set.all():

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(productorder.product.ean, style=size_nine_helvetica),
                    Paragraph(productorder.product.title, style=size_nine_helvetica),
                    Paragraph(str(productorder.amount), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(productorder.netto_price),
                              style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points((productorder.netto_price * productorder.amount)),
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

        for productorder in self.order.productorder_set.all():
            total_netto += productorder.amount * productorder.netto_price

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

        self.story.extend([table, order_horizontal_line, KeepTogether(betrag_table)])

        # from reportlab.lib import colors
        # table = Table(rows, hAlign='LEFT', colWidths=[doc.width/3.0]*3)
        # table.setStyle(TableStyle([('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
        #                                 ('BOX', (0, 0), (-1, -1), 0.25, colors.black)]))

    def build_after_table(self):
        first_warning_text = "Die gelieferte Ware bleibt unser Eigentum bis zur Bezahlung sämtlicher auch künftig"\
                             " entstehender Forderungen aus unserer Geschäftsverbindung. Reklamationen können nur "\
                             "innerhalb von 2 Tagen nach Lieferung anerkannt werden."

        first_warning_paragraph = Paragraph(first_warning_text, size_ten_helvetica)

        first_warning_data = [
            [first_warning_paragraph, Paragraph("", size_ten_helvetica)],
        ]

        first_warning_table = Table(first_warning_data, colWidths=[430, 10])

        first_warning_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        second_warning_text = f"Reklamation von Waren können wir nur anerkennen, wenn diese unverzüglich nach der"\
                              f" Anlieferung erfolgen. Bitte prüfen Sie bei Lieferungen" \
                              f" unmittelbar die Ordnungsmäßigkeit"\
                              f" der Lieferung. Sollten Mängel oder Schäden an von uns gelieferten Waren festgestellt "\
                              f"werden, bitten wir Sie uns umgehend darüber zu informieren." \
                              f" Von Rücksendungen - ohne unsere"\
                              f" vorherige Zustimmung - bitten wir abzusehen."\
                              f"<br/><br/>"\
                              f"Retouren müssen nach unseren Richtlinien ordnungsgemäß zurück gesendet werden."

        second_warning_paragraph = Paragraph(second_warning_text, size_ten_helvetica)

        second_warning_data = [[second_warning_paragraph, Paragraph("", size_ten_helvetica)]]

        second_warning_table = Table(second_warning_data, colWidths=[430, 10])

        second_warning_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        warning_paragraphs = []

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

        for warning_string in warning_list:
            warning_paragraph = Paragraph(warning_string, size_ten_helvetica)
            warning_paragraphs.append(warning_paragraph)
        self.story.extend([two_new_lines, two_new_lines])
        self.story.extend(warning_paragraphs)
