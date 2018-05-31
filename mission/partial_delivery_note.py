from mission.delivery_note_pdf import DeliveryNoteView
from mission.delivery_note_pdf import *
from mission.models import DeliveryNote


class PartialDeliveryNoteView(DeliveryNoteView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.partial_delivery_note = None

    def dispatch(self, request, *args, **kwargs):
        self.partial_delivery_note = DeliveryNote.objects.get(pk=self.kwargs.get("delivery_note_pk"))
        self.partial_delivery_note_number = self.partial_delivery_note.delivery_note_number
        return super().dispatch(request, *args, **kwargs)

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

        delivery_note_number = f"{self.partial_delivery_note.delivery_note_number}"

        print(self.partial_delivery_note.deliverynoteproductmission_set.all())

        for deliverynoteproductmission in self.partial_delivery_note.deliverynoteproductmission_set.all():

            data.append(
                [
                    Paragraph(str(pos), style=size_nine_helvetica),
                    Paragraph(deliverynoteproductmission.product_mission.get_ean_or_sku(),
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
