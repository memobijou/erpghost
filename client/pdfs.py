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
from reportlab.lib.utils import ImageReader


class CustomPdf:

    @property
    def response(self):
        return self.pdf_response

    def __init__(self, client, qr_code_url, logo_url=None, story=[], receiver_address=[]):
        self.pdf_response = HttpResponse(content_type='application/pdf')
        self.doc = BaseDocTemplate(self.pdf_response)
        self.qr_code_url = qr_code_url
        self.story = []
        self.logo_url = logo_url
        self.client = client
        self.add_footer_to_document()
        self.add_sender_address_to_story(client)
        self.add_receiver_address_to_story(receiver_address)
        self.story.extend(story)
        self.build_document()

    def build_document(self):
        CustomCanvas.logo_url = self.logo_url
        self.doc.build(self.story, canvasmaker=CustomCanvas)

    def add_sender_address_to_story(self, client):
        sender_address = f"<br/><br/><br/>{client.contact.billing_address.firma} - " \
                         f"{client.contact.billing_address.strasse} "\
                         f"{client.contact.billing_address.hausnummer}- {client.contact.billing_address.zip} "\
                         f"{client.contact.billing_address.place}"
        self.story.append(Paragraph(sender_address, size_seven_helvetica))

    def add_receiver_address_to_story(self, receiver_address_list):
        paragraph_string = ""
        for row in receiver_address_list:
            paragraph_string += f"{row}<br/>"
        self.story.append(Paragraph(paragraph_string, style=size_nine_helvetica_bold))

    def add_footer_to_document(self):
        first_page_frame = Frame(self.doc.leftMargin, self.doc.bottomMargin+50, self.doc.width, self.doc.height,
                                 id='first_frame')
        next_page_frame = Frame(self.doc.leftMargin, self.doc.bottomMargin+50, self.doc.width, self.doc.height,
                                id='last_frame')

        first_template = PageTemplate(id='first', frames=first_page_frame, onPage=self.footer)
        next_template = PageTemplate(id='next', frames=next_page_frame, onPage=self.footer)
        self.doc.addPageTemplates([first_template, next_template])
        self.story.append(NextPageTemplate(['*', 'next']))

    def footer(self, canvas, doc):
        footer_style = ParagraphStyle("footer_style", alignment=TA_CENTER, fontSize=7)
        footer_text = f"<br/><br/><br/> "\
                      f"<b>{self.client.contact.billing_address.firma} | {self.client.contact.billing_address.strasse} "\
                      f"{self.client.contact.billing_address.hausnummer} | {self.client.contact.billing_address.zip} "\
                      f"{self.client.contact.billing_address.place}</b><br/>"\
                      f"tel {self.client.contact.telefon} | fax {self.client.contact.fax} | " \
                      f"{self.client.contact.email} | {self.client.contact.website}"\
                      f"<br/>"\
                      f"{self.client.contact.bank.first().bank} | BIC: {self.client.contact.bank.first().bic} | "\
                      f"IBAN: {self.client.contact.bank.first().iban}"\
                      f"<br/>"\
                      f"{self.client.contact.commercial_register} | St.Nr. {self.client.contact.tax_number} | "\
                      f"Ust-IdNr. {self.client.contact.sales_tax_identification_number}"\
                      f"<br/>"\

        if self.client.contact.billing_address.vorname and self.client.contact.billing_address.nachname:
            footer_text += f"Geschäftsführer: {self.client.contact.billing_address.vorname} " \
                           f"{self.client.contact.billing_address.nachname}"
        footer_text += f"<br/>"
        footer_paragraph = Paragraph(footer_text, footer_style)
        canvas.saveState()
        w, h = footer_paragraph.wrap(doc.width, doc.bottomMargin)
        footer_paragraph.drawOn(canvas, doc.leftMargin + 18, h - 70)

        if self.qr_code_url is not None:
            qr_code = ImageReader(self.qr_code_url)
            canvas.drawImage(qr_code, doc.leftMargin, h - 74, width=1 * inch, height=1 * inch)
        canvas.restoreState()


class CustomCanvas(canvas.Canvas):
    """
    http://code.activestate.com/recipes/546511-page-x-of-y-with-reportlab/
    http://code.activestate.com/recipes/576832/
    """
    logo_url = None
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
            self.draw_logo(433, 705, self.logo_width, self.logo_height)

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
        if self.logo_url is None:
            return
        print(f"WTF {self.logo_url}")
        logo = ImageReader(self.logo_url)
        if logo.getSize()[0] > 2000:  # Discount König Resize ...
            width += 40
            height += 40
            x -= 43
        self.drawImage(logo, x, y, width=width, height=height)
        # qr_code = ImageReader('http://127.0.0.1:8000/static/qrcodebtc.png')
        # canvas.drawImage(qr_code, self.doc.leftMargin + 30, h - 35, width=1 * inch, height=1 * inch)


def get_logo_and_qr_code_from_client(request, client):
    logo_url = None
    qr_code_url = None

    scheme = request.is_secure() and "https" or "http"
    print(client.contact.company_image)

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


def create_right_align_header(date, x_position=230, additional_data=None):

    date = add_new_line_to_string_at_index(date, 10)

    right_table_data = [
        [
            Paragraph("Datum", style=size_nine_helvetica_leading_10),
            Paragraph(date, style=size_nine_helvetica_leading_10),
        ],
    ]

    if additional_data is not None:
        right_table_data.extend(additional_data)

    right_table = Table(data=right_table_data, colWidths=[80, 100])

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

    table = Table(data, splitByRow=True, colWidths=[x_position, 100], spaceAfter=30, spaceBefore=50)

    table.setStyle(
        TableStyle([
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('VALIGN', (0, 0), (-1, -1), "TOP"),
        ])
    )

    return [table]


def get_reciver_address_list_from_object(object_):
    receiver_address = [object_.contact.billing_address.firma,
                        f"{object_.contact.billing_address.strasse} "
                        f"{object_.contact.billing_address.hausnummer}",
                        f"{object_.contact.billing_address.place} "
                        f"{object_.contact.billing_address.zip}"]
    return receiver_address


def get_delivery_address_html_string_from_object(delivery_address):

    delivery_address_string = f"{delivery_address.firma}<br/>"

    if delivery_address.adresszusatz:
        delivery_address_string += f"{delivery_address.adresszusatz}<br/>"

    if delivery_address.adresszusatz2:
        delivery_address_string += f"{delivery_address.adresszusatz2}<br/>"

    delivery_address_string += f"{delivery_address.strasse} {delivery_address.hausnummer}<br/>" \
                               f"{delivery_address.zip} {delivery_address.place}"

    return delivery_address_string


def add_new_line_to_string_at_index(string, index):
    if len(string) < index:
        return string
    import textwrap
    return '<br/>'.join(textwrap.wrap(string, index))


def format_number_thousand_decimal_points(number):
    number = '{:,.2f}'.format(number).replace(",", "X").replace(".", ",").replace("X", ".")
    return number


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

size_nine_helvetica_leading_10 = ParagraphStyle("adsadsa", leading=10, fontName="Helvetica", fontSize=9)

underline = "_____________________________"
spaces_13 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
spaces_6 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'

spaces_4 = "&nbsp;&nbsp;&nbsp;&nbsp;"
two_new_lines = Paragraph("<br/><br/>", style=size_nine_helvetica)
horizontal_line = Drawing(100, 1)
horizontal_line.add(Line(0, 0, 425, 0))
