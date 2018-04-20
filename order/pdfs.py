from django.http import HttpResponse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate
from reportlab.platypus import SimpleDocTemplate
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.graphics.shapes import Drawing, Line
from reportlab.platypus import Spacer
from reportlab.platypus.tables import Table, TableStyle, LongTable
from reportlab.lib.units import cm, mm
from reportlab.platypus import Frame, NextPageTemplate, PageBreakIfNotEmpty
from order.models import Order

size_seven_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=7)
size_nine_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=9)
size_ten_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=10)
size_eleven_helvetica = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=11)
size_twelve_helvetica_bold = ParagraphStyle(name="normal", fontName="Helvetica-Bold", fontSize=12)
size_nine_helvetica_bold = ParagraphStyle(name="normal", fontName="Helvetica-Bold", fontSize=9)
size_nine_helvetica_left_indent_310 = ParagraphStyle(name="normal", fontName="Helvetica", fontSize=9,
                                                     leftIndent=310, align="RIGHT")
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

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        doc = SimpleDocTemplate(response)

        self.document_height = doc.height

        order_number = self.order.ordernumber
        delivery_date = self.order.delivery_date
        print(order_number)
        # FOOTER

        first_page_frame = Frame(doc.leftMargin, doc.bottomMargin+50, doc.width, doc.height, id='first_frame')
        next_page_frame = Frame(doc.leftMargin, doc.bottomMargin+50, doc.width, doc.height, id='last_frame')

        first_template = PageTemplate(id='first', frames=[first_page_frame], onPage=footer)
        next_template = PageTemplate(id='next', frames=[next_page_frame], onPage=footer)

        doc.addPageTemplates([first_template, next_template])

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

        footer_width, footer_height = footer_paragraph.wrap(doc.width, doc.bottomMargin)
        self.footer_height = footer_height

        story = self.build_story(
            sender_address="Baschar Trading Center GmbH - Orber Str. 16 - 60386 Frankfurt am Main",
            receiver_address="Impex Service GmbH<br/>Kopernikusstr.17<br/>50126 Bergheim<br/>",
            your_delivery=f"<u>Bestellung: {order_number}</u>",
            delivery_note_title=f"<br/>Bestellung {order_number}<br/><br/>",
            warning_list=warning_list,
            date="06.03.2018", customer="342323", order=order_number, delivery_date=delivery_date,
            document_height=doc.height, footer_height=footer_height,
        )
        doc.build(story, canvasmaker=CustomCanvas, onLaterPages=footer, onFirstPage=footer)

        return response

    last_table_height = None
    document_height = None
    footer_height = None
    header_height = None
    conditions_height = None

    def build_story(self, sender_address="", receiver_address="", your_delivery="", delivery_note_title="",
                    warning_list=list, date="", customer="", order="", delivery_date="", document_height="",
                    footer_height=""):

        sender_address_paragraph = Paragraph(sender_address, style=size_seven_helvetica)
        receiver_address_paragraph = Paragraph(receiver_address, style=size_nine_helvetica_bold)

        date_customer_delivery_note_paragraph = self.create_date_customer_order_table(date, customer, order)

        your_delivery_paragraph = Paragraph(your_delivery, style=size_nine_helvetica_bold)

        delivery_address_delivery_conditions_payment_conditions = self.build_conditions(delivery_date)

        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)

        self.header_height = self.get_header_height([sender_address_paragraph, receiver_address_paragraph,
                                                    date_customer_delivery_note_paragraph, your_delivery_paragraph,
                                                    delivery_note_title_paragraph],
                                                    delivery_address_delivery_conditions_payment_conditions)

        tables_list = self.create_table()

        story = [NextPageTemplate(['*', 'next']), sender_address_paragraph, receiver_address_paragraph,
                 Paragraph("<br/><br/><br/>", style=size_eleven_helvetica), date_customer_delivery_note_paragraph, two_new_lines,
                 your_delivery_paragraph, delivery_address_delivery_conditions_payment_conditions,
                 delivery_note_title_paragraph, horizontal_line]

        story.extend([table for table in tables_list])

        story.extend([two_new_lines, two_new_lines])

        warning_text = self.build_warning_text(warning_list, document_height, footer_height, tables_list)

        # print(f"JO: {warning_table_h}")
        story.extend(warning_text)
        return story

    def get_header_height(self, paragraphs, delivery_address_delivery_conditions_payment_conditions):
        height = 0
        for paragraph in paragraphs:
            w, h = paragraph.wrap(500, 500)
            height = height + h
        height += self.conditions_height
        print(f"HEADER HEIGHT: {height}")
        return height

    def build_warning_text(self, warning_list, document_height, footer_height, tables_list):

        warning_paragraphs = []

        for warning_string in warning_list:
            warning_paragraph = Paragraph(warning_string, size_ten_helvetica)
            warning_paragraph_width, warning_paragraph_height = warning_paragraph.wrap(500, 500)
            warning_paragraphs.append(warning_paragraph)
        return warning_paragraphs

    def build_conditions(self, delivery_date):

        delivery_address = "Impex Service GmbH<br/>LGZ3 / Technologiepark West<br/>Zum Frenser Feld 11.6<br/>" \
                           "50127 Bergheim"

        delivery_condition = "CIF, Lieferung Frei Haus"

        payment_condition = "14 Tage Netto"

        delivery_date = f"{delivery_date}"

        table_data = [
            [
                Paragraph("<br/>Wichtig: Bitte immer beachten!!! <br/>Jeder Lieferverzug ist uns unverzüglich "
                          "schriftlich mitzuteilen.", size_nine_helvetica)
            ],
            [
                 Paragraph("<br/>Lieferadresse: ", style=size_nine_helvetica),
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
        self.conditions_height = table_height
        print(f"DONE: {table_height}")
        return table

    def create_date_customer_order_table(self, date, customer, order):

        date = add_new_line_to_string_at_index(date, 10)
        customer = add_new_line_to_string_at_index(customer, 10)
        order = add_new_line_to_string_at_index(order, 10)

        right_align_paragraph_style = ParagraphStyle("adsadsa", leading=10, fontName="Helvetica", fontSize=9)

        left_table_data = [
            [
                Paragraph("Datum<br/>Kunde<br/>Bestellung<br/>",
                          style=right_align_paragraph_style),
            ]
        ]

        left_table = Table(left_table_data)

        left_table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        right_table_data = [
            [
                Paragraph("Datum", style=right_align_paragraph_style), Paragraph(date, style=right_align_paragraph_style),
            ],
            [
                Paragraph("Kunde", style=right_align_paragraph_style), Paragraph(customer, style=right_align_paragraph_style),

            ],
            [
                Paragraph("Bestellung", style=right_align_paragraph_style),Paragraph(order, style=right_align_paragraph_style),
            ],
        ]

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
            ["", "", "", right_table],
        ]

        table = Table(data, splitByRow=True)



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

        data.append(header)

        table_with_header = LongTable(data, splitByRow=True)

        table_with_header.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )

        tables_list.append(table_with_header)

        data = []
        first_page = True
        pos = 1

        for productorder in self.order.productorder_set.all():

            data.append(
                [
                    Paragraph(add_new_line_to_string_at_index(str(pos), 20),
                              style=size_nine_helvetica),
                    Paragraph(add_new_line_to_string_at_index(productorder.product.ean, 20),
                              style=size_nine_helvetica),
                    Paragraph(add_new_line_to_string_at_index(productorder.product.title, 50), style=size_nine_helvetica),
                    Paragraph(add_new_line_to_string_at_index(str(productorder.amount), 20), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points(productorder.netto_price), style=right_align_paragraph_style),
                    Paragraph(format_number_thousand_decimal_points((productorder.netto_price*productorder.amount)
                              + (productorder.netto_price*productorder.amount)*0.19),
                              style=right_align_paragraph_style),
                ],
            )

            table = LongTable(data, splitByRow=True)

            table.setStyle(
                TableStyle([
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                    ('VALIGN', (0, 0), (-1, -1), "TOP"),
                ])
            )
            # tables_list.append(table)
            # tables_list.append(PageBreakIfNotEmpty())
            # data = []
            table_width, table_height = table.wrap(0, 0)
            print(f"{self.document_height - self.header_height - self.footer_height}")
            print(table_height)
            print(f"{self.document_height - self.header_height - self.footer_height - table_height}")

            if (self.document_height - self.header_height - self.footer_height - table_height) < -50 and first_page is True\
                    or table_height > 550 and first_page is False:
                print(f"GREATER: {self.document_height - self.header_height - self.footer_height - table_height}")
                print(table_height)
                last_item = data[-1]
                data = data[:-1]

                table = LongTable(data, splitByRow=True)
                table.setStyle(
                    TableStyle([
                        ('LEFTPADDING', (0, 0), (-1, -1), 0),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                        ('VALIGN', (0, 0), (-1, -1), "TOP"),
                    ])
                )
                tables_list.append(table)
                tables_list.append(PageBreakIfNotEmpty())
                data = [header, last_item]
                first_page = False

            pos += 1
        table = LongTable(data, splitByRow=True)
        table.setStyle(
            TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), "TOP"),
            ])
        )
        self.last_table_height = table_height
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

footer_style = ParagraphStyle("footer_style", alignment=TA_CENTER, fontSize=7)
footer_paragraph = Paragraph(
        f"<br/><br/><br/> "
        f"<b>Baschar Trading Center GmbH | Orber Straße 16 | 60386 Frankfurt a.M.</b>"
        f"<br/>"
        f"tel +49 (0) 69 20 23 50 93 | fax +49 (0) 69 20 32 89 52 | info@btcgmbh.eu | www.btcgmbh.eu"
        f"<br/>"
        f"Frankfurter Sparkasse | BIC: HELADEF1822 | IBAN: DE73 5005 0201 0200 5618 47"
        f"<br/>"
        f"Amtsgericht Ffm HRB 87651 | St.Nr. 45 229 07653 | Ust-IdNr. DE 270211471"
        f"<br/>"
        f"Geschäftsführer: Mohamed Makansi"
        f"<br/>",
        footer_style)


def footer(canvas, doc):
    canvas.saveState()
    from reportlab.lib.utils import ImageReader

    w, h = footer_paragraph.wrap(doc.width, doc.bottomMargin)
    print(f"Footer: {h}")
    footer_paragraph.drawOn(canvas, doc.leftMargin + 30, h - 70)
    qr_code = ImageReader('http://127.0.0.1:8000/static/qrcodebtc.png')
    canvas.drawImage(qr_code, doc.leftMargin + 30, h - 74, width=1 * inch, height=1 * inch)
    canvas.restoreState()

def add_new_line_to_string_at_index(string, index):
    import textwrap
    return '<br/>'.join(textwrap.wrap(string, index))


class CustomCanvas(canvas.Canvas):
    """
    http://code.activestate.com/recipes/546511-page-x-of-y-with-reportlab/
    http://code.activestate.com/recipes/576832/
    """

    # ----------------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        """Constructor"""
        canvas.Canvas.__init__(self, *args, **kwargs)

        self.pages = []

    # ----------------------------------------------------------------------
    def showPage(self):
        """
        On a page break, add information to the list
        """

        if len(self.pages) == 0:
            self.draw_logo(440, 740)

        self.pages.append(dict(self.__dict__))
        self._startPage()

    # ----------------------------------------------------------------------
    def save(self):
        """
        Add the page number to each page (page x of y)
        """

        page_count = len(self.pages)

        for page in self.pages:
            self.__dict__.update(page)
            self.draw_page_number(page_count)
            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    # ----------------------------------------------------------------------
    def draw_page_number(self, page_count):
        """
        Add the page number
        """
        page = f"Seite {self._pageNumber} von {page_count}"
        self.setFont("Helvetica", 9)
        self.drawRightString(530, 10, page)

    def draw_logo(self, x, y):
        from reportlab.lib.utils import ImageReader
        logo = ImageReader('http://127.0.0.1:8000/static/btclogo.jpg')
        self.drawImage(logo, x, y, width=1 * inch, height=1 * inch)
        # qr_code = ImageReader('http://127.0.0.1:8000/static/qrcodebtc.png')
        # canvas.drawImage(qr_code, self.doc.leftMargin + 30, h - 35, width=1 * inch, height=1 * inch)


def format_number_thousand_decimal_points(number):
    number = '{:,.2f}'.format(number).replace(",", "X").replace(".", ",").replace("X", ".")
    return number
