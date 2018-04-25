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
        sender_address = f"{client.contact.adress.firma} - {client.contact.adress.strasse} "\
                         f"{client.contact.adress.hausnummer}- {client.contact.adress.zip} "\
                         f"{client.contact.adress.place}"
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
            footer_text += f"Geschäftsführer: {self.client.contact.adress.vorname} " \
                           f"{self.client.contact.adress.nachname}"
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
underline = "_____________________________"
spaces_13 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
spaces_6 = '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'

spaces_4 = "&nbsp;&nbsp;&nbsp;&nbsp;"
two_new_lines = Paragraph("<br/><br/>", style=size_nine_helvetica)
horizontal_line = Drawing(100, 1)
horizontal_line.add(Line(0, 0, 425, 0))
