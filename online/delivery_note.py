from mission.delivery_note_pdf import *
from mission.models import DeliveryNote, Shipment


class DeliveryNotePdfGenerator:
    def __init__(self, shipment=None, logo_url=None, qr_code_url=None):
        self.story = []
        self.shipment = shipment
        self.mission = self.shipment.mission
        self.client = self.mission.channel.client
        self.delivery_note = self.shipment.delivery_note
        self.delivery_note_number = self.delivery_note.delivery_note_number
        self.logo_url = logo_url
        self.qr_code_url = qr_code_url

    def create_pdf_file(self):
        story = self.build_story()
        receiver_address = get_reciver_address_list_from_object(self.mission.delivery_address)
        custom_pdf = CustomPdf(self.client, self.qr_code_url, logo_url=self.logo_url, story=story,
                               receiver_address=receiver_address)
        return custom_pdf

    def build_story(self):
        mission_number = self.mission.mission_number

        your_mission_number = f"<u>Unsere Auftragsnummer: {mission_number}</u>"

        if self.mission.customer_order_number is not None and self.mission.customer_order_number != "":
            your_mission_number = f"<u>Ihre Bestellung: {self.mission.customer_order_number}</u>"

        elif self.mission.channel_order_id is not None and self.mission.channel_order_id != "":
            your_mission_number = f"<u>Ihre Bestellung: {self.mission.channel_order_id}</u>"

        your_delivery_paragraph = Paragraph(your_mission_number, style=size_nine_helvetica_bold)

        self.build_right_align_header()

        self.story.extend([your_delivery_paragraph])

        self.build_before_table()

        self.build_table_title()

        self.build_table()

        self.build_after_table()

        return self.story

    def build_after_table(self):
        first_warning_text = "Die gelieferte Ware bleibt unser Eigentum bis zur Bezahlung sämtlicher auch künftig"\
                             " entstehender Forderungen aus unserer Geschäftsverbindung. Reklamationen können nur "\
                             "innerhalb von 2 Tagen nach Lieferung anerkannt werden."

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

        second_warning_table = Table(second_warning_data, colWidths=[430, 10], spaceBefore=20)

        second_warning_table.setStyle(
            tblstyle=TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        self.story.extend([KeepTogether(first_warning_table), KeepTogether(second_warning_table)])

    def build_table_title(self):
        delivery_note_title = f"<br/>Lieferschein<br/><br/>"
        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)
        self.story.extend([delivery_note_title_paragraph, mission_horizontal_line])

    def build_right_align_header(self):
        created_date = ""
        if self.delivery_note.created is not None:
            created_date = f"{self.delivery_note.created.strftime('%d.%m.%Y')}"
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

        delivery_note_number = self.mission.delivery_note_number

        if self.delivery_note_number is not None:
            delivery_note_number = self.delivery_note_number

        right_align_header_data.append(
            [
                Paragraph("Lieferschein", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(delivery_note_number, 20),
                          style=size_nine_helvetica_leading_10),
            ],
        )

        if self.mission.customer is not None:
            customer_number = self.mission.customer.customer_number or ""
            right_align_header_data.append([
                Paragraph("Kunden-Nr.", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(customer_number, 20), style=size_nine_helvetica_leading_10),
            ])

        self.story.extend(create_right_align_header(created_date, additional_data=right_align_header_data))

    def build_before_table(self):
        delivery_address_object = self.mission.delivery_address

        delivery_address_html_string = get_delivery_address_html_string_from_object(delivery_address_object)

        delivery_date_from = self.mission.delivery_date_from

        delivery_date_to = self.mission.delivery_date_to

        terms_of_delivery = self.mission.terms_of_delivery

        terms_of_payment = self.mission.terms_of_payment

        delivery_date_or_shipment_date = f""

        if delivery_date_from is not None and delivery_date_to is not None:
            delivery_date_or_shipment_date = f"<br/><b>Liefertermin:</b>" \
                                             f" {delivery_date_from.strftime('%d.%m.%Y')}-" \
                                             f"{delivery_date_to.strftime('%d.%m.%Y')}<br/>"

        table_data = [
            [
                Paragraph(delivery_date_or_shipment_date, style=size_twelve_helvetica_bold),
            ],
            [
                 Paragraph("<br/>Lieferadresse: ", style=size_nine_helvetica),
            ],
            [
                Paragraph(delivery_address_html_string, style=size_nine_helvetica),
            ],
        ]

        if terms_of_delivery is not None:
            table_data.extend(
                [
                    [
                        Paragraph(f"<br/>Lieferbedingungen: {terms_of_delivery or 'N/A'}<br/>",
                                  style=size_nine_helvetica)
                    ]
                ]
            )

        if terms_of_payment is not None:
            table_data.extend(
                [
                    [
                        Paragraph(f"Zahlungsbedingungen: {terms_of_payment or 'N/A'}<br/>", style=size_nine_helvetica),
                    ]
                ]
            )

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
        colwidths = [30, 70, 38, 242, 60]

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)
        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>EAN</b>", style=size_nine_helvetica),
            Paragraph("<b>Zustand</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style),
        ]

        data = [header]
        pos = 1


        delivery_note_items = []

        if self.shipment.delivery_note is not None:
            delivery_note_items = self.shipment.delivery_note.deliverynoteitem_set.all()

        for item in delivery_note_items:

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(f"{item.ean}",
                              style=size_nine_helvetica),
                    Paragraph(item.state,
                              style=size_nine_helvetica),
                    Paragraph(item.description or "",
                              style=size_nine_helvetica),
                    Paragraph(str(item.amount),
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

        self.story.extend([table, mission_horizontal_line])

    def get_logo_and_qr_code_from_client(self, request, client):
        logo_url = None
        qr_code_url = None

        scheme = request.is_secure() and "https" or "http"

        if bool(client.contact.company_image) is not False:
            if "http" in client.contact.company_image.url:
                logo_url = client.contact.company_image.url
            else:
                logo_url = f"{scheme}://{request.get_host()}{client.contact.company_image.url}"

        if bool(client.qr_code) is not False:
            if "http" in client.qr_code.url:
                qr_code_url = client.qr_code.url
            else:
                qr_code_url = f"{scheme}://{request.get_host()}{client.qr_code.url}"
        return logo_url, qr_code_url


class OnlineDeliveryNoteView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.delivery_note = None
        self.delivery_note_number = None
        self.shipment = None
        self.mission = None
        self.client = None
        self.story = []

    def dispatch(self, request, *args, **kwargs):
        self.shipment = Shipment.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.shipment.mission
        self.client = self.mission.channel.client
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        exception = self.validate_pdf()
        if exception is not None:
            return exception
        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)
        generator = DeliveryNotePdfGenerator(shipment=self.shipment, logo_url=logo_url, qr_code_url=qr_code_url)
        custom_pdf = generator.create_pdf_file()
        return custom_pdf.response

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
        receiver_address = [address.first_name_last_name]

        if address.address_line_1 is not None and address.address_line_1 != "":
            receiver_address += [address.address_line_1]
        if address.address_line_2 is not None and address.address_line_2 != "":
            receiver_address += [address.address_line_2]
        if address.address_line_3 is not None and address.address_line_3 != "":
            receiver_address += [address.address_line_3]

        receiver_address += [
            f"{address.place} "
            f"{address.zip}"
        ]
    else:
        receiver_address = ["", "", "", "", ""]
    return receiver_address


def get_delivery_address_html_string_from_object(delivery_address):
    delivery_address_string = ""
    if delivery_address is not None:
        delivery_address_string = f"{delivery_address.first_name_last_name}<br/>"

        if delivery_address.adresszusatz:
            delivery_address_string += f"{delivery_address.adresszusatz}<br/>"

        if delivery_address.adresszusatz2:
            delivery_address_string += f"{delivery_address.adresszusatz2}<br/>"

        delivery_address_string += f"{delivery_address.strasse} {delivery_address.hausnummer}<br/>" \
                                   f"{delivery_address.zip} {delivery_address.place}"

    return delivery_address_string

