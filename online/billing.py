from client.pdfs import right_align_bold_paragraph_style
from mission.delivery_note_pdf import *
from mission.models import Billing


class OnlineBillingView(View):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.billing = None
        self.billing_number = None
        self.story = []
        self.delivery_date = None
        self.mission = None
        self.client = None
        self.billing_address = None

    def dispatch(self, request, *args, **kwargs):
        self.billing = Billing.objects.get(pk=self.kwargs.get("billing_pk"))
        self.billing_number = self.billing.billing_number
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        self.billing_address = self.mission.billing_address
        self.client = Client.objects.get(pk=self.request.session.get("client"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        exception = self.validate_pdf()
        if exception is not None:
            return exception
        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)
        story = self.build_story()
        receiver_address = get_reciver_address_list_from_object(self.billing_address)
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

    def build_table_title(self):
        delivery_note_title = f"<br/>Rechnung {self.billing_number}<br/><br/>"
        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)
        delivery_note_title_warning = f"Das Rechnungsdatum entspricht dem Leistungsdatum<br/>"
        delivery_note_title_warning_paragraph = Paragraph(delivery_note_title_warning, size_seven_helvetica)

        self.story.extend([delivery_note_title_paragraph, delivery_note_title_warning_paragraph,
                           mission_horizontal_line])

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

    def build_before_table(self):
        billing_address_object = self.mission.billing_address

        delivery_address_html_string = get_delivery_address_html_string_from_object(self.mission.delivery_address)

        delivery_date = self.mission.delivery_date

        terms_of_delivery = self.mission.terms_of_delivery

        terms_of_payment = self.mission.terms_of_payment

        table_data = [
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
                Paragraph(f"<br/>Lieferbedingungen: {terms_of_delivery or 'N/A'}<br/>", style=size_nine_helvetica),
            ],
            [
                Paragraph(f"Zahlungsbedingungen: {terms_of_payment or 'N/A'}<br/>", style=size_nine_helvetica),
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
        from mission.billing_pdf import  format_number_thousand_decimal_points
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
        data.append(
            [
                Paragraph(str(pos), style=size_nine_helvetica),
                Paragraph("", style=size_nine_helvetica),
                Paragraph(f"Transportkosten", style=size_nine_helvetica),
                Paragraph("", style=right_align_paragraph_style),
                Paragraph("",
                          style=right_align_paragraph_style),
                Paragraph(format_number_thousand_decimal_points(self.mission.online_transport_cost or 0),
                          style=right_align_paragraph_style),
            ],
        )
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

        tax = total_netto*0.19+self.mission.online_transport_cost*0.19

        betrag_data = [
            [
                Paragraph(f"Nettobetrag",
                          style=right_align_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto+self.mission.online_transport_cost)} €",
                          style=right_align_paragraph_style),
            ],
            [
                Paragraph(f"+ Umsatzsteuer (19,00%)", style=right_align_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(tax)} €",
                          style=right_align_paragraph_style),
            ],
            [
                horizontal_line_betrag,
            ],
            [
                Paragraph(f"GESAMT", style=right_align_bold_paragraph_style),
                Paragraph(f"{format_number_thousand_decimal_points(total_netto+tax)} €",
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

    def build_right_align_header(self):
        created_date = f"{self.mission.created_date.strftime('%d.%m.%Y')}"
        mission_number = self.mission.mission_number

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
            Paragraph(add_new_line_to_string_at_index(self.billing_number, 20), style=size_nine_helvetica_leading_10),
        ])

        if self.mission.customer is not None:
            customer_number = self.mission.customer.customer_number or ""
            right_align_header_data.append([
                Paragraph("Kunden-Nr.", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(customer_number, 20), style=size_nine_helvetica_leading_10),
            ])

        self.story.extend(create_right_align_header(created_date, additional_data=right_align_header_data))

    def validate_pdf(self, *args, **kwargs):
        context = {"title": "PDF Fehler",
                   "object": self.mission
                   }
        template_name = "mission/pdf_exception.html"

        if self.mission.delivery_address is None:
            context["message"] = "Sie müssen dem Auftrag einen Lieferadresse zuweisen, um eine PDF zu generieren."
            return render(self.request, template_name, context)
        if self.mission.productmission_set.count() == 0:
            context["message"] = "Der Auftrag muss mindestens einen Artikel beinhalten, um eine PDF zu generieren."
            return render(self.request, template_name, context)


def get_reciver_address_list_from_object(address):
    if address is not None:
        print(f"wasasdasdsadasd {address.first_name_last_name}")
        receiver_address = [address.first_name_last_name,
                            f"{address.street_and_housenumber} ",
                            f"{address.place} "
                            f"{address.zip}"]
    else:
        receiver_address = ["", "", "", "", ""]
    return receiver_address


def get_billing_address_html_string_from_object(billing_address):
    billing_address_string = ""
    if billing_address is not None:
        billing_address_string = f"{billing_address.first_name_last_name}<br/>"

        if billing_address.adresszusatz:
            billing_address_string += f"{billing_address.adresszusatz}<br/>"

        if billing_address.adresszusatz2:
            billing_address_string += f"{billing_address.adresszusatz2}<br/>"

        billing_address_string += f"{billing_address.street_and_housenumber} <br/>" \
                                  f"{billing_address.zip} {billing_address.place}"

    return billing_address_string


def get_delivery_address_html_string_from_object(delivery_address):
    delivery_address_string = ""
    if delivery_address is not None:
        delivery_address_string = f"{delivery_address.first_name_last_name}<br/>"
        if delivery_address.address_line_1 is not None and delivery_address.address_line_1 != "":
            delivery_address_string += f"{delivery_address.address_line_1}<br/>"
        if delivery_address.address_line_2 is not None and delivery_address.address_line_2 != "":
            delivery_address_string += f"{delivery_address.address_line_2}<br/>"
        if delivery_address.address_line_3 is not None and delivery_address.address_line_3 != "":
            delivery_address_string += f"{delivery_address.address_line_3}<br/>"
        delivery_address_string += f"{delivery_address.zip} {delivery_address.place}<br/>"
    return delivery_address_string
