from mission.delivery_note_pdf import *
from mission.models import DeliveryNote


class OnlineDeliveryNoteView(DeliveryNoteView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partial_delivery_note = None

    def dispatch(self, request, *args, **kwargs):
        self.partial_delivery_note = DeliveryNote.objects.get(pk=self.kwargs.get("delivery_note_pk"))
        self.partial_delivery_note_number = self.partial_delivery_note.delivery_note_number
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        logo_url, qr_code_url = get_logo_and_qr_code_from_client(request, self.client)
        story = self.build_story()
        receiver_address = get_reciver_address_list_from_object(self.mission.delivery_address)
        custom_pdf = CustomPdf(self.client, qr_code_url, logo_url=logo_url, story=story,
                               receiver_address=receiver_address)
        return custom_pdf.response

    def build_before_table(self):
        delivery_address_object = self.mission.delivery_address

        delivery_address_html_string = get_delivery_address_html_string_from_object(delivery_address_object)

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

        for deliverynoteproductmission in self.partial_delivery_note.deliverynoteproductmission_set.all():

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(deliverynoteproductmission.product_mission.get_ean_or_sku(),
                              style=size_nine_helvetica),
                    Paragraph(deliverynoteproductmission.product_mission.state,
                              style=size_nine_helvetica),
                    Paragraph(deliverynoteproductmission.product_mission.product.title or "",
                              style=size_nine_helvetica),
                    Paragraph(str(deliverynoteproductmission.amount),
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