from collections import defaultdict

from PyPDF2 import PdfFileReader
from PyPDF2 import PdfFileWriter
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse

from django import views
from django.http import HttpResponseRedirect

from disposition.models import BusinessAccount
from mission.models import Mission, DeliveryNote, DeliveryNoteProductMission, Billing, BillingProductMission, \
    DeliveryNoteItem, BillingItem, Shipment
from client.models import Client
import base64
from xml.etree import ElementTree as Et
import requests
from django.views.generic import UpdateView
from django.urls import reverse_lazy

from online.forms import DhlForm, DPDForm
import os
from Crypto.Cipher import AES

from stock.models import Stock
from online.countries_list import countries_list
from bs4 import BeautifulSoup
import html
from io import BytesIO


def decrypt_encrypted_string(encrypted_string):
    enc_key = os.environ.get("enc_key")
    print(enc_key)
    iv456 = "randomshit123456"
    aes_object = AES.new(enc_key, AES.MODE_CFB, iv456)
    encrypted_bytes = encrypted_string.encode("ISO-8859-1")
    password = aes_object.decrypt(encrypted_bytes)
    return password


class DPDCreatePDFView(UpdateView):
    template_name = "online/dpd_form.html"
    form_class = DPDForm

    def __init__(self, **kwargs):
        self.transport_account = None
        self.username = None
        self.password = None
        self.headers = {"Content-Type": "application/soap+xml; charset=UTF-8"}
        self.login_service_url = "https://public-ws-stage.dpd.com/services/LoginService/V2_0/"
        self.shipment_service_url = "https://public-ws-stage.dpd.com/services/ShipmentService/V3_2/"
        self.token = None
        self.client = None
        self.mission = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        # if self.mission.online_picklist.completed is True:
        #     return HttpResponseRedirect(reverse_lazy("online:online_redirect"))
        self.client = self.mission.channel.client
        print(f"{self.mission} --- {self.client}")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "DPD Label erstellen"
        context["mission"] = self.mission
        return context

    def get_object(self, queryset=None):
        return self.mission.delivery_address

    def get_success_url(self, **kwargs):
        if self.request.GET.get("not_packing") is not None:
            if self.request.GET.get("is_export") is not None:
                return reverse_lazy("online:export") + "?" + self.request.GET.urlencode()
            else:
                return reverse_lazy("online:list")
        return reverse_lazy("online:packing", kwargs={"pk": self.mission.online_picklist.pk})

    def form_valid(self, form, **kwargs):
        main_shipments = list(self.mission.shipment_set.filter(main_shipment=True).values_list("pk", flat=True))
        print(f"klabat: {main_shipments}")
        if self.request.GET.get("packing") is not None:
            dpd_label_creator = DPDLabelCreator(multiple_missions=[self.mission], main_shipment=True)
        else:
            dpd_label_creator = DPDLabelCreator(multiple_missions=[self.mission], ignore_pickorder=True,
                                                main_shipment=True)
        parcel_label_numbers, message = dpd_label_creator.create_label()
        print(f"hey {message} --- {type(message)}")
        if message is not None and message != "":
            form.add_error(None, message)
            return super().form_invalid(form)
        else:
            if self.request.GET.get("not_packing") is not None and self.request.GET.get("is_export") is not None:
                self.mission.status = "Versandbereit"
                self.mission.save()

            if self.request.GET.get("packing") is not None:
                print(f"klablat 2 : {main_shipments}")
                main_shipments = Shipment.objects.filter(pk__in=main_shipments)
                print(f"klablat 3 : {main_shipments}")
                print(f"dont understand: {main_shipments}")
                main_shipments.delete()
        return super().form_valid(form)


class DPDLabelCreator:
    def __init__(self, mission=None, multiple_missions=None, ignore_pickorder=None, main_shipment=None):
        super().__init__()
        self.transport_account = None
        self.transport_accounts = {}
        self.username, self.password = None, None
        self.headers = {"Content-Type": "application/soap+xml; charset=UTF-8"}
        self.login_service_url = "https://public-ws.dpd.com/services/LoginService/V2_0/"
        self.shipment_service_url = "https://public-ws.dpd.com/services/ShipmentService/V3_2/"
        # self.login_service_url = "https://public-ws-stage.dpd.com/services/LoginService/V2_0/"  #  staging
        # self.shipment_service_url = "https://public-ws-stage.dpd.com/services/ShipmentService/V3_2/"  #  staging
        self.token = None
        self.ignore_pickorder = None
        if ignore_pickorder is True:
            self.ignore_pickorder = True

        self.main_shipment = None
        if main_shipment is True:
            self.main_shipment = main_shipment

        self.clients_missions = None
        if multiple_missions is not None:
            self.clients_missions = defaultdict(list)
            for mission in multiple_missions:
                client = mission.channel.client
                self.clients_missions[client].append(mission)

    def get_country_code(self, mission):
        country_code = None
        if mission.delivery_address.country_code is not None:
            country_code = mission.delivery_address.country_code
        else:
            for country_json in countries_list:
                for k, v in country_json.items():
                    if str.lower(v) == str.lower(mission.delivery_address.country):
                        country_code = country_json.get("code")
                        return country_code
        return country_code

    def create_label(self):
        parcel_label_number, message = self.create_label_through_dpd_api()
        return parcel_label_number, message

    def create_label_through_dpd_api(self):
        label_numbers = []

        xml_requests, error_msg = self.get_xml_requests()
        print(f"Shell: {xml_requests}")

        if error_msg is not None:
            return label_numbers, error_msg

        for doc in xml_requests:
            response = requests.post(url=self.shipment_service_url, data=doc.encode("utf-8"), headers=self.headers)

            root = Et.fromstring(response.content.decode("utf-8"))

            message = ""
            for el in root.iter("message"):
                message = el.text

            if message == "":
                for el in root.iter("faultstring"):
                    message = el.text

            print(f"why: {message}")
            print(response.text)

            if message != "":
                return label_numbers, message

            all_orders_pdf = ""
            for el in root.iter("parcellabelsPDF"):
                all_orders_pdf = el.text
                all_orders_pdf = base64.decodebytes(str.encode(all_orders_pdf))

            label_pdfs = self.split_pdf_file(all_orders_pdf)

            root = Et.fromstring(response.content.decode("utf-8"))

            for el in root.iter("parcelLabelNumber"):
                label_number = el.text
                label_numbers.append(label_number)

            for client, missions in self.clients_missions.items():
                for mission in missions:
                    shipment = self.create_shipment(mission)
                    shipment.tracking_number = label_numbers[0]
                    shipment.transport_service = self.transport_accounts[client].transport_service.name

                    if self.ignore_pickorder is True:
                        mission.ignore_pickorder = True
                        mission.save()

                    shipment.label_pdf.save("label_dpd", ContentFile(label_pdfs[0]))
                    shipment.save()

                    label_pdfs.pop(0)
                    label_numbers.pop(0)

            # weil label_numbers vorher beim hinterlegen der Aufträge gelöscht wird
            label_numbers = []
            for el in root.iter("parcelLabelNumber"):
                label_number = el.text
                label_numbers.append(label_number)

            return label_numbers, message

    def split_pdf_file(self, pdf_file):
        splitted_pdfs = []
        pdf_buffer = BytesIO(pdf_file)
        pdf_reader = PdfFileReader(pdf_buffer)

        for i in range(pdf_reader.numPages):
            output = PdfFileWriter()
            output.addPage(pdf_reader.getPage(i))
            split_file = BytesIO()
            output.write(split_file)
            splitted_pdfs.append(split_file.getvalue())

        return splitted_pdfs

    def get_xml_requests(self):
        xml_requests = []
        print(f"GHOST: {self.clients_missions}")
        if self.clients_missions is not None:
            for client, missions in self.clients_missions.items():

                error_msg = self.validate_missions(missions)

                if error_msg is not None:
                    return None, error_msg

                transport_account = BusinessAccount.objects.filter(
                    client=client, transport_service__name__iexact="DPD").first()

                self.transport_accounts[client] = transport_account

                username = transport_account.username
                password = decrypt_encrypted_string(transport_account.password_encrypted).decode("ISO-8859-1")
                token = self.get_authentication_token_from_dpd_api(username, password)

                xml_orders = ""
                for mission in missions:
                    xml_orders += self.get_single_xml_order(mission)
                doc = f'''
                    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                     xmlns:ns="http://dpd.com/common/service/types/Authentication/2.0"
                     xmlns:ns1="http://dpd.com/common/service/types/ShipmentService/3.2">
                       <soapenv:Header>
                          <ns:authentication>
                             <delisId>{username}</delisId>
                             <authToken>{token}</authToken>
                             <messageLanguage>de_DE</messageLanguage>
                          </ns:authentication>
                       </soapenv:Header>
                       <soapenv:Body>
                           <ns1:storeOrders>
                               <printOptions>
                                    <printerLanguage>PDF</printerLanguage>
                                    <paperFormat>A6</paperFormat>
                               </printOptions>
                                {xml_orders}
                           </ns1:storeOrders>
                       </soapenv:Body>
                    <soapenv:Envelope>
                '''
                doc = doc.replace("\n", "")
                xml_requests.append(doc)
        return xml_requests, None

    def validate_missions(self, missions):
        for mission in missions:
            if mission.delivery_address.strasse is None or mission.delivery_address.hausnummer is None:
                return f"Für den Auftrag {mission.mission_number} wurde entweder keine Straße oder Hausnumer hinterlegt"

    def get_single_xml_order(self, mission):
        client = mission.channel.client
        sender_company = client.contact.delivery_address.firma
        sender_full_name = f"{client.contact.delivery_address.vorname} {client.contact.delivery_address.nachname}"
        sender_street = client.contact.delivery_address.strasse
        sender_housenumber = client.contact.delivery_address.hausnummer
        sender_postal_code = client.contact.delivery_address.zip
        sender_place = client.contact.delivery_address.place
        mission_first_name_last_name = mission.delivery_address.first_name_last_name or ""
        mission_first_name_last_name = html.escape(mission_first_name_last_name)[:35]
        print(f"name::::: {mission_first_name_last_name} --- {len(mission_first_name_last_name)}")
        mission_adresszusatz = html.escape(mission.delivery_address.adresszusatz or "")
        mission_adresszusatz = mission_adresszusatz[:35]
        country_code = html.escape(self.get_country_code(mission))

        xml_order = f'''
            <order>
                <generalShipmentData>
                      <identificationNumber />
                      <sendingDepot>0160</sendingDepot>
                      <product>CL</product>
                      <sender>
                        <name1>{sender_company}</name1>
                        <name2>{sender_full_name}</name2>
                        <street>{sender_street}</street>
                        <houseNo>{sender_housenumber}</houseNo>
                        <country>DE</country>
                        <zipCode>{sender_postal_code}</zipCode>
                        <city>{sender_place}</city>
                        <gln>0</gln>
                      </sender>
                      <recipient>
                        <name1>{mission_first_name_last_name}</name1>
                        <name2>{mission_adresszusatz}</name2>
                        <street>{html.escape(mission.delivery_address.strasse)}</street>
                        <houseNo>{html.escape(mission.delivery_address.hausnummer)}</houseNo>
                        <country>{country_code}</country>
                        <zipCode>{html.escape(mission.delivery_address.zip)}</zipCode>
                        <city>{html.escape(mission.delivery_address.place)}</city>
                        <gln>0</gln>
                      </recipient>
                </generalShipmentData>
                <parcels>
                    <customerReferenceNumber1>{mission.channel_order_id}</customerReferenceNumber1>
                    <customerReferenceNumber2 />
                    <customerReferenceNumber3 />
                    <customerReferenceNumber4 />
                    <weight>0</weight>
                </parcels>
                <productAndServiceData>
                    <orderType>consignment</orderType>
                </productAndServiceData>
           </order>
        '''
        return xml_order

    def get_authentication_token_from_dpd_api(self, username, password):
        doc = f'''
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
             xmlns:ns="http://dpd.com/common/service/types/LoginService/2.0">
               <soapenv:Header/>
               <soapenv:Body>
                   <ns:getAuth>
                       <delisId>{username}</delisId>
                       <password>{password}</password>
                       <messageLanguage>de_DE</messageLanguage>
                   </ns:getAuth>
               </soapenv:Body>
            <soapenv:Envelope>
        '''
        doc = doc.replace("\n", "")
        response = requests.post(url=self.login_service_url, data=doc, headers=self.headers)
        root = Et.fromstring(response.content.decode("utf-8"))
        token = ""
        for el in root.iter("authToken"):
            token = el.text
        self.token = token
        return self.token

    def create_shipment(self, mission):
        shipment = Shipment(mission=mission, delivery_note=self.create_delivery_note(mission),
                            billing=self.create_billing(mission))
        if self.main_shipment is True:
            shipment.main_shipment = True
        return shipment

    @staticmethod
    def create_delivery_note(mission):
        if mission.delivery_address is not None:
            delivery_note = DeliveryNote.objects.create()

            bulk_instances = []
            for mission_product in mission.productmission_set.all():
                bulk_instances.append(DeliveryNoteItem(delivery_note=delivery_note,
                                                       amount=mission_product.amount,
                                                       ean=mission_product.ean,
                                                       sku=mission_product.online_sku_number,
                                                       state=mission_product.state,
                                                       description=mission_product.online_description))

            DeliveryNoteItem.objects.bulk_create(bulk_instances)
            return delivery_note

    @staticmethod
    def create_billing(mission):
        if mission.billing_address is not None:
            billing = Billing.objects.create()

            bulk_instances = []

            for mission_product in mission.productmission_set.all():
                netto_price = mission_product.brutto_price-(mission_product.brutto_price*0.19)

                bulk_instances.append(BillingItem(
                    billing=billing, amount=mission_product.amount, netto_price=netto_price,
                    ean=mission_product.ean, sku=mission_product.online_sku_number, state=mission_product.state,
                    description=mission_product.online_description, brutto_price=mission_product.brutto_price,
                    shipping_price=mission_product.shipping_price, discount=mission_product.discount,
                    shipping_discount=mission_product.shipping_discount
                ))
            BillingItem.objects.bulk_create(bulk_instances)
            return billing


class DPDGetLabelView(views.View):
    def __init__(self, **kwargs):
        self.shipment = None
        self.mission = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.shipment = Shipment.objects.get(pk=self.kwargs.get("pk"))
        self.mission = self.shipment.mission
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        label_pdf = self.shipment.label_pdf.read()
        response = HttpResponse(label_pdf, content_type='application/pdf')
        return response
