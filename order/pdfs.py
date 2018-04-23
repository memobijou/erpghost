from django.http import HttpResponse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from reportlab.lib.enums import TA_RIGHT, TA_LEFT, TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageTemplate
from reportlab.platypus import SimpleDocTemplate,BaseDocTemplate
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from reportlab.graphics.shapes import Drawing, Line
from reportlab.platypus import Spacer
from reportlab.platypus.tables import Table, TableStyle, LongTable
from reportlab.lib.units import cm, mm
from reportlab.platypus import Frame, NextPageTemplate, PageBreakIfNotEmpty
from order.models import Order
from django.contrib.staticfiles.templatetags.staticfiles import static
from client.models import Client

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
    qr_code_url = ""

    @property
    def order(self):
        return Order.objects.get(pk=self.kwargs.get("pk"))

    @property
    def client(self):
        client = Client.objects.get(pk=self.request.session.get("client"))
        return client

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='application/pdf')
        doc = BaseDocTemplate(response)

        self.document_height = doc.height

        order_number = self.order.ordernumber
        delivery_date = self.order.delivery_date
        print(order_number)
        # FOOTER

        first_page_frame = Frame(doc.leftMargin, doc.bottomMargin+50, doc.width, doc.height, id='first_frame')
        next_page_frame = Frame(doc.leftMargin, doc.bottomMargin+50, doc.width, doc.height, id='last_frame')

        first_template = PageTemplate(id='first', frames=first_page_frame, onPage=self.footer)
        next_template = PageTemplate(id='next', frames=next_page_frame, onPage=self.footer)

        doc.addPageTemplates([first_template, next_template])

        scheme = request.is_secure() and "https" or "http"
        self.qr_code_url = f"{scheme}://{request.get_host()}{static('qrcodebtc.png')}"
        # CustomCanvas.logo_url = f"{scheme}://{request.get_host()}{static('btclogo.jpg')}"
        print(self.qr_code_url)
        if "http" in self.client.contact.company_image.url:
            CustomCanvas.logo_url = self.client.contact.company_image.url
        else:
            CustomCanvas.logo_url = f"{scheme}://{request.get_host()}{self.client.contact.company_image.url}"
        print(CustomCanvas.logo_url)
        print(self.client.contact)
        print(self.order)
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

        delivery_address = f"{self.order.delivery_address.firma}<br/>"

        if self.order.delivery_address.adresszusatz:
            delivery_address += f"{self.order.delivery_address.adresszusatz}<br/>"

        if self.order.delivery_address.adresszusatz2:
            delivery_address += f"{self.order.delivery_address.adresszusatz2}<br/>"

        delivery_address += f"{self.order.delivery_address.strasse} {self.order.delivery_address.hausnummer}<br/>" \
                            f"{self.order.delivery_address.zip} {self.order.delivery_address.place}"

        story = self.build_story(
            sender_address=f"{self.client.contact.adress.firma} - {self.client.contact.adress.strasse} "
                           f"{self.client.contact.adress.hausnummer}- {self.client.contact.adress.zip} "
                           f"{self.client.contact.adress.place}",
            receiver_address=f"{self.order.supplier.contact.adress.firma}<br/>"
                             f"{self.order.supplier.contact.adress.strasse} "
                             f"{self.order.supplier.contact.adress.hausnummer}<br/>"
                             f"{self.order.supplier.contact.adress.place} {self.order.supplier.contact.adress.zip}<br/>",
            your_delivery=f"<u>Bestellung: {order_number}</u>",
            delivery_note_title=f"<br/>Bestellung {order_number}<br/><br/>",
            warning_list=warning_list, date=f"{self.order.created_date.strftime('%d.%m.%Y')}", customer="342323",
            order=order_number, delivery_date=delivery_date, delivery_address=delivery_address,
            document_height=doc.height,
        )
        doc.build(story, canvasmaker=CustomCanvas)

        return response

    last_table_height = None
    document_height = None
    header_height = None
    conditions_height = None

    def build_story(self, sender_address="", receiver_address="", your_delivery="", delivery_note_title="",
                    warning_list=list, date="", customer="", order="", delivery_date="", document_height="",
                    delivery_address=""):
        print(sender_address)
        print(receiver_address)

        sender_address_paragraph = Paragraph(sender_address, style=size_seven_helvetica)
        receiver_address_paragraph = Paragraph(receiver_address, style=size_nine_helvetica_bold)

        date_customer_delivery_note_paragraph = self.create_date_customer_order_table(date, customer, order)

        your_delivery_paragraph = Paragraph(your_delivery, style=size_nine_helvetica_bold)

        delivery_address_delivery_conditions_payment_conditions = self.build_conditions(delivery_date, delivery_address)

        delivery_note_title_paragraph = Paragraph(delivery_note_title, size_twelve_helvetica_bold)

        self.header_height = self.get_header_height([sender_address_paragraph, receiver_address_paragraph,
                                                    date_customer_delivery_note_paragraph, your_delivery_paragraph,
                                                    delivery_note_title_paragraph],
                                                    delivery_address_delivery_conditions_payment_conditions)

        tables_list = self.create_table()

        story = [NextPageTemplate(['*', 'next']), sender_address_paragraph, receiver_address_paragraph,
                 Paragraph("<br/><br/><br/>", style=size_eleven_helvetica), date_customer_delivery_note_paragraph,
                 two_new_lines, your_delivery_paragraph, delivery_address_delivery_conditions_payment_conditions,
                 delivery_note_title_paragraph, horizontal_line]

        story.extend([table for table in tables_list])

        story.extend([two_new_lines, two_new_lines])

        warning_text = self.build_warning_text(warning_list, document_height, tables_list)

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

    def build_warning_text(self, warning_list, document_height, tables_list):
        warning_paragraphs = []

        for warning_string in warning_list:
            warning_paragraph = Paragraph(warning_string, size_ten_helvetica)
            warning_paragraph_width, warning_paragraph_height = warning_paragraph.wrap(500, 500)
            warning_paragraphs.append(warning_paragraph)
        return warning_paragraphs

    def build_conditions(self, delivery_date, delivery_address):

        delivery_condition = self.order.terms_of_delivery

        payment_condition = self.order.terms_of_payment

        delivery_date = f"{delivery_date.strftime('%d.%m.%Y')}"

        table_data = [
            [
                Paragraph("<br/>Wichtig: Bitte immer beachten!!! <br/>Jeder Lieferverzug ist uns unverzüglich "
                          "schriftlich mitzuteilen.", size_nine_helvetica)
            ],
            [
                 Paragraph("<br/><b>Lieferadresse:</b> ", style=size_nine_helvetica),
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
            ["", right_table],
        ]

        table = Table(data, splitByRow=True, colWidths=[300, 100])

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

        colwidths = [30, 68, 152, 60, 65, 65]

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
                    Paragraph(format_number_thousand_decimal_points((productorder.netto_price*productorder.amount)
                              + (productorder.netto_price*productorder.amount)*0.19),
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

    def footer(self, canvas, doc):
        footer_style = ParagraphStyle("footer_style", alignment=TA_CENTER, fontSize=7)
        footer_text = f"<br/><br/><br/> "\
                      f"<b>{self.client.contact.adress.firma} | {self.client.contact.adress.strasse} "\
                      f"{self.client.contact.adress.hausnummer} | {self.client.contact.adress.zip} "\
                      f"{self.client.contact.adress.place}</b><br/>"\
                      f"tel {self.client.contact.telefon} | fax {self.client.contact.fax} | " \
                      f"{self.client.contact.email} | {self.client.contact.website}"\
                      f"<br/>"\
                      f"{self.client.contact.bank.first().bank} | BIC: {self.client.contact.bank.first().bic} | "\
                      f"IBAN: {self.client.contact.bank.first().iban}"\
                      f"<br/>"\
                      f"{self.client.contact.commercial_register} | St.Nr. {self.client.contact.tax_number} | "\
                      f"Ust-IdNr. {self.client.contact.sales_tax_identification_number}"\
                      f"<br/>"\

        if self.client.contact.adress.vorname and self.client.contact.adress.nachname:
            footer_text += f"Geschäftsführer: {self.client.contact.adress.vorname} {self.client.contact.adress.nachname}"
        footer_text += f"<br/>"
        print(footer_text)
        footer_paragraph = Paragraph(footer_text, footer_style)
        canvas.saveState()
        from reportlab.lib.utils import ImageReader

        w, h = footer_paragraph.wrap(doc.width, doc.bottomMargin)
        print(f"Footer: {h}")
        footer_paragraph.drawOn(canvas, doc.leftMargin + 18, h - 70)
        qr_code = ImageReader(self.qr_code_url)
        canvas.drawImage(qr_code, doc.leftMargin, h - 74, width=1 * inch, height=1 * inch)
        canvas.restoreState()


def add_new_line_to_string_at_index(string, index):
    import textwrap
    return '<br/>'.join(textwrap.wrap(string, index))


class CustomCanvas(canvas.Canvas):
    """
    http://code.activestate.com/recipes/546511-page-x-of-y-with-reportlab/
    http://code.activestate.com/recipes/576832/
    """
    logo_url = ""
    logo_width = 70
    logo_height = 70

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
            self.draw_logo(433, 740, self.logo_width, self.logo_height)

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

    def draw_logo(self, x, y, width, height):
        from reportlab.lib.utils import ImageReader
        logo = ImageReader(self.logo_url)
        if logo.getSize()[0] > 2000:  # Discount König Resize ...
            width += 40
            height += 40
            x -= 43
        self.drawImage(logo, x, y, width=width, height=height)
        # qr_code = ImageReader('http://127.0.0.1:8000/static/qrcodebtc.png')
        # canvas.drawImage(qr_code, self.doc.leftMargin + 30, h - 35, width=1 * inch, height=1 * inch)


def format_number_thousand_decimal_points(number):
    number = '{:,.2f}'.format(number).replace(",", "X").replace(".", ",").replace("X", ".")
    return number
