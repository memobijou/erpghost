from mission.delivery_note_pdf import *
from mission.models import DeliveryNote


class OnlineDeliveryNoteView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partial_delivery_note = None
        self.partial_delivery_note_number = None
        self.mission = None
        self.client = None
        self.story = []

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        first_product = self.mission.productmission_set.first()
        self.client = first_product.sku.channel.client
        self.partial_delivery_note = DeliveryNote.objects.get(pk=self.kwargs.get("delivery_note_pk"))
        self.partial_delivery_note_number = self.partial_delivery_note.delivery_note_number
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        exception = self.validate_pdf()
        if exception is not None:
            return exception
        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)
        story = self.build_story()
        receiver_address = get_reciver_address_list_from_object(self.mission.delivery_address)
        custom_pdf = CustomPdf(self.client, qr_code_url, logo_url=logo_url, story=story,
                               receiver_address=receiver_address)
        return custom_pdf.response

    def build_story(self):
        mission_number = self.mission.mission_number

        your_mission_number = f"<u>Unsere Auftragsnummer: {mission_number}</u>"

        if self.mission.customer_order_number is not None and self.mission.customer_order_number != "":
            your_mission_number = f"<u>Ihre Bestellung: {self.mission.customer_order_number}</u>"

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
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        driver_form_title = Paragraph("<br/><br/><b>Ware vollständig erhalten laut Lieferschein</b><br/><br/>",
                                      size_ten_helvetica)

        driver_data = [
            [
                driver_form_title
            ],
            [
                 Paragraph(f"{underline}___", size_ten_helvetica),
                 Paragraph("", size_ten_helvetica)
            ],
            [
                 Paragraph("Name Fahrer", size_nine_helvetica),
                 Paragraph("", size_ten_helvetica)
            ],

            [],
            [
                Paragraph(f"{underline}___", size_ten_helvetica),
                Paragraph("", size_ten_helvetica)
            ],
            [
                Paragraph("Kennzeichen", size_nine_helvetica),
                Paragraph("", size_ten_helvetica)
            ],

            [],
            [
                Paragraph(f"{underline}___", size_ten_helvetica),
                Paragraph("", size_ten_helvetica)
            ],
            [
                Paragraph("Spedition", size_nine_helvetica),
                Paragraph("", size_ten_helvetica)
            ],

            [],
            [
                Paragraph(f"{underline}___", size_ten_helvetica),
                Paragraph("", size_ten_helvetica)
            ],
            [
                Paragraph("Unterschrift Fahrer/Stempel", size_nine_helvetica),
                Paragraph("", size_ten_helvetica)
            ],

            [],
            # [Paragraph(f"Name Fahrer:{underline}", size_ten_helvetica)],
            # [],
            # [Paragraph(f"Kennzeichen:{underline}", size_ten_helvetica)],
            # [],
            # [Paragraph(f"Spedition:{underline}", size_ten_helvetica)],
            # [],
            # [],
            # [Paragraph(f"Unterschrift Fahrer/Stempel:{underline}", size_ten_helvetica)],
            # []
        ]

        driver_table = Table(driver_data, colWidths=[320, 100])

        driver_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        quality_form_title = Paragraph("<br/><br/><b>Qualitätskontrolle</b><br/><br/>", size_ten_helvetica)

        quality_data = [
            [quality_form_title],

            [Paragraph(f"{underline}___", size_ten_helvetica),
             Paragraph(f"{underline}___", size_ten_helvetica),
             Paragraph("", size_ten_helvetica)],

            [Paragraph("Name Kommissionierer", size_nine_helvetica),
             Paragraph("Datum/Unterschrift", size_nine_helvetica),
             Paragraph("", size_ten_helvetica)],

            [],

            [Paragraph(f"{underline}___", size_ten_helvetica), Paragraph(f"{underline}___", size_ten_helvetica),
             Paragraph("", size_ten_helvetica)],

            [Paragraph("Name Kontrolleur", size_nine_helvetica),
             Paragraph("Datum/Unterschrift", size_nine_helvetica), Paragraph("", size_ten_helvetica)],

            [],

            [Paragraph(f"{underline}___", size_ten_helvetica), Paragraph(f"{underline}___", size_ten_helvetica),
             Paragraph("", size_ten_helvetica)],

            [Paragraph("Name Verlader", size_nine_helvetica),
             Paragraph("Datum/Unterschrift", size_nine_helvetica), Paragraph("", size_ten_helvetica)],

            [],

            [Paragraph(f"{underline}___", size_ten_helvetica), Paragraph(f"{underline}___", size_ten_helvetica),
             Paragraph("", size_ten_helvetica)],

            [Paragraph("Name Verantwortlicher", size_nine_helvetica),
             Paragraph("Datum/Unterschrift", size_nine_helvetica), Paragraph("", size_ten_helvetica)],

            [],
        ]

        quality_form_table = Table(quality_data, colWidths=[195, 240, 0])

        quality_form_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        driver_and_quality_data = [
            [driver_table],
            [quality_form_table],
        ]

        driver_and_quality_table = Table(driver_and_quality_data)

        self.story.extend([first_warning_table, KeepTogether(driver_and_quality_table), second_warning_table])

    def build_table_title(self):
        delivery_note_title = f"<br/>Lieferschein<br/><br/>"
        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)
        self.story.extend([delivery_note_title_paragraph, mission_horizontal_line])

    def build_right_align_header(self):
        created_date = ""
        if self.partial_delivery_note.created is not None:
            created_date = f"{self.partial_delivery_note.created.strftime('%d.%m.%Y')}"
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

        if self.partial_delivery_note_number is not None:
            partial_delivery_note_number = self.partial_delivery_note_number

        right_align_header_data.append(
            [
                Paragraph("Lieferschein", style=size_nine_helvetica_leading_10),
                Paragraph(add_new_line_to_string_at_index(partial_delivery_note_number, 20),
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

        table_data = [
            [
                Paragraph(f"<br/><b>Liefertermin:</b> {delivery_date_from.strftime('%d.%m.%Y')}-"
                          f"{delivery_date_to.strftime('%d.%m.%Y')}<br/>",
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
        colwidths = [30, 70, 38, 242, 60]

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)
        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>EAN / SKU</b>", style=size_nine_helvetica),
            Paragraph("<b>Zustand</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style),
        ]

        data = []
        data.append(header)
        pos = 1

        delivery_note_number = f"{self.partial_delivery_note.delivery_note_number}"

        print(self.partial_delivery_note.deliverynoteproductmission_set.all())

        for mission_product in self.mission.productmission_set.all():

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(mission_product.get_ean_or_sku(),
                              style=size_nine_helvetica),
                    Paragraph(mission_product.sku.state,
                              style=size_nine_helvetica),
                    Paragraph(mission_product.sku.product.title or "",
                              style=size_nine_helvetica),
                    Paragraph(str(mission_product.amount),
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
        receiver_address = [address.first_name_last_name,
                            f"{address.strasse} "
                            f"{address.hausnummer}",
                            f"{address.place} "
                            f"{address.zip}"]
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

