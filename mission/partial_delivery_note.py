from mission.delivery_note_pdf import DeliveryNoteView
from mission.delivery_note_pdf import *


class PartialDeliveryNoteView(DeliveryNoteView):
    def build_table(self):
        colwidths = [30, 68, 282, 60]

        right_align_paragraph_style = ParagraphStyle("adsadsa", alignment=TA_RIGHT, fontName="Helvetica", fontSize=9,
                                                     rightIndent=17)
        header = [
            Paragraph("<b>Pos</b>", style=size_nine_helvetica),
            Paragraph("<b>EAN / SKU</b>", style=size_nine_helvetica),
            Paragraph("<b>Bezeichnung</b>", style=size_nine_helvetica),
            Paragraph("<b>Menge</b>", style=right_align_paragraph_style),
        ]

        data = []
        data.append(header)
        pos = 1

        delivery_note_number = f"{self.kwargs.get('delivery_note_number')}"

        for productmission in self.mission.productmission_set.\
                filter(realamount__delivery_note_number=delivery_note_number):
            real_amount = productmission.realamount_set.filter(delivery_note_number=delivery_note_number).\
                first().real_amount

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(productmission.product.ean, style=size_nine_helvetica),
                    Paragraph(productmission.product.title, style=size_nine_helvetica),
                    Paragraph(str(real_amount), style=right_align_paragraph_style),
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
