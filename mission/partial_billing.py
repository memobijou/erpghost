from mission.billing_pdf import BillingPdfView
from mission.billing_pdf import *
from mission.models import DeliveryMissionProduct, Billing


class PartialPdfView(BillingPdfView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partial_billing = None
        self.partial_billing_number = None

    def dispatch(self, request, *args, **kwargs):
        self.partial_billing = Billing.objects.get(pk=self.kwargs.get("partial_billing_pk"))
        self.partial_billing_number = self.partial_billing.billing_number
        return super().dispatch(request, *args, **kwargs)

    def build_before_table(self):
        warning_text = "<br/>Sehr geehrte Damen, sehr geehrte Herren, wir danken für Ihren Auftrag, den wir unter " \
                       "Zugrundelegung unserer vereinbarten Liefer- und Zahlungsbedingungen und vorbehaltlich einer " \
                       "durchzuführenden internen Abstimmung Ihrer Bestellung annehmen. Die Preise auf dieser " \
                       "Auftragsbestätigung verstehen sich als Netto- Preise nach Abzug von eventuell bestehenden " \
                       "Rechnungsrabatten."
        warning_paragraph = Paragraph(warning_text, size_nine_helvetica)

        delivery_address_object = self.mission.customer.contact.delivery_address

        delivery_address_html_string = get_delivery_address_html_string_from_object(delivery_address_object)

        if self.partial_billing.delivery_date is not None:
            delivery_date = self.partial_billing.delivery_date
        else:
            delivery_date = self.mission.delivery_date

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

    def build_table(self):
        colwidths = [30, 70, 55, 100, 60, 65, 60]

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)
        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>EAN / SKU</b>", style=size_nine_helvetica),
            Paragraph("<b>Zustand</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style),
            Paragraph("<b>Einzelpreis</b>", style=right_align_paragraph_style),
            Paragraph("<b>Betrag</b>", style=right_align_paragraph_style),
        ]

        data = []
        data.append(header)
        pos = 1

        billing_number = f"{self.partial_billing_number}"

        for product_delivery in self.partial_billing.deliverynoteproductmission_set.all():
            productmission = product_delivery.product_mission

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(productmission.get_ean_or_sku(), style=size_nine_helvetica),
                    Paragraph(productmission.state, style=size_nine_helvetica),
                    Paragraph(productmission.product.title or "", style=size_nine_helvetica),
                    Paragraph(str(product_delivery.amount), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(productmission.netto_price),
                              style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(
                        (productmission.netto_price * product_delivery.amount)),
                              style=right_align_paragraph_style),
                ],
            )

            pos += 1

        # transport_service = models.CharField(choices=shipping_choices, blank=False, null=True, max_length=200,
        #                                      verbose_name="Transportdienstleister")
        # shipping_number_of_pieces = models.IntegerField(blank=False, null=True, verbose_name="Stückzahl Transport")
        # shipping_costs = models.FloatField(blank=False, null=True, max_length=200, verbose_name="Transportkosten")

        data.append([
            Paragraph(str(pos), style=size_nine_helvetica),
            Paragraph("", style=size_nine_helvetica),
            Paragraph("", style=size_nine_helvetica),
            Paragraph(f"Transportkosten: {self.partial_billing.transport_service}", style=size_nine_helvetica),
            Paragraph(str(self.partial_billing.shipping_number_of_pieces), style=right_align_paragraph_style),
            Paragraph(format_number_thousand_decimal_points(self.partial_billing.shipping_costs),
                      style=right_align_paragraph_style),
            Paragraph(format_number_thousand_decimal_points(
                (self.partial_billing.shipping_costs * self.partial_billing.shipping_number_of_pieces)),
                style=right_align_paragraph_style),
        ],)

        table = LongTable(data, splitByRow=True, colWidths=colwidths, repeatRows=1)
        table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        total_netto = 0

        for product_delivery in self.partial_billing.deliverynoteproductmission_set.all():
            productmission = product_delivery.product_mission
            amount = product_delivery.amount
            if amount is not None:
                pass
            else:
                continue

            total_netto += amount * productmission.netto_price

        total_netto += self.partial_billing.shipping_number_of_pieces * self.partial_billing.shipping_costs

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
