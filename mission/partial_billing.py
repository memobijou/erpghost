from mission.billing_pdf import BillingPdfView
from mission.billing_pdf import *


class PartialPdfView(BillingPdfView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partial_billing_number = None

    def dispatch(self, request, *args, **kwargs):
        self.partial_billing_number = self.kwargs.get("billing_number")
        return super().dispatch(request, *args, **kwargs)

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

        billing_number = f"{self.kwargs.get('billing_number')}"

        for productmission in self.mission.productmission_set.filter(realamount__billing_number=billing_number):
            real_amount = productmission.realamount_set.filter(billing_number=billing_number).first().real_amount
            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(productmission.product.ean, style=size_nine_helvetica),
                    Paragraph(productmission.product.title, style=size_nine_helvetica),
                    Paragraph(str(real_amount), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(productmission.netto_price),
                              style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(
                        (productmission.netto_price * real_amount)),
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
            real_amount = productmission.realamount_set.filter(billing_number=billing_number).first()
            if real_amount is not None:
                real_amount = real_amount.real_amount
            else:
                continue

            total_netto += real_amount * productmission.netto_price

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
