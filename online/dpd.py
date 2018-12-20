from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse

from django import views
from django.http import HttpResponseRedirect

from disposition.models import BusinessAccount
from mission.models import Mission, DeliveryNote, DeliveryNoteProductMission, Billing, BillingProductMission, \
    DeliveryNoteItem, BillingItem
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
            return reverse_lazy("online:list")
        return reverse_lazy("online:packing", kwargs={"pk": self.mission.online_picklist.pk})

    # def get(self, request, **kwargs):
    #     dpd_label = self.get_label_from_dpd_api()
    #     response = HttpResponse(dpd_label, content_type='application/pdf')
    #     return response

    def form_valid(self, form, **kwargs):
        dpd_label_creator = DPDLabelCreator(self.mission, self.client)
        parcel_label_number, message = dpd_label_creator.create_label()
        print(f"hey {message} --- {type(message)}")
        if message is not None and message != "":
            form.add_error(None, message)
            return super().form_invalid(form)
        if parcel_label_number is not None:
            self.mission.tracking_number = parcel_label_number

            if self.mission.online_picklist is not None:
                self.create_delivery_note(picklist=self.mission.online_picklist)
                self.create_billing(picklist=self.mission.online_picklist)
                self.mission.online_picklist.save()

            elif self.request.GET.get("not_packing") is not None:
                self.create_delivery_note()
                self.create_billing()
            self.mission.save()
        return super().form_valid(form)

    def create_delivery_note(self, picklist=None):
        delivery_note = None

        if picklist is not None:
            delivery_note = DeliveryNote.objects.create()
            picklist.online_delivery_note = delivery_note
            picklist.save()
        else:
            delivery_note = DeliveryNote.objects.create()
            self.mission.delivery_note = delivery_note
            self.mission.ignore_pickorder = True



        bulk_instances = []
        for mission_product in self.mission.productmission_set.all():
            bulk_instances.append(DeliveryNoteItem(delivery_note=delivery_note,
                                                   amount=mission_product.amount,
                                                   ean=mission_product.ean,
                                                   sku=mission_product.online_sku_number,
                                                   state=mission_product.state,
                                                   description=mission_product.online_description))

        DeliveryNoteItem.objects.bulk_create(bulk_instances)

    def create_billing(self, picklist=None):
        if self.mission.billing_address is not None:
            billing = None
            if picklist is not None:
                billing = Billing.objects.create()
                picklist.online_billing = billing
                picklist.save()
            else:
                billing = Billing.objects.create()
                self.mission.billing = billing
                self.mission.ignore_pickorder = True

            bulk_instances = []

            for mission_product in self.mission.productmission_set.all():
                netto_price = mission_product.brutto_price-(mission_product.brutto_price*0.19)

                bulk_instances.append(BillingItem(
                    billing=billing, amount=mission_product.amount, netto_price=netto_price,
                    ean=mission_product.ean, sku=mission_product.online_sku_number, state=mission_product.state,
                    description=mission_product.online_description, brutto_price=mission_product.brutto_price,
                    shipping_price=mission_product.shipping_price, discount=mission_product.discount,
                    shipping_discount=mission_product.shipping_discount
                ))
            BillingItem.objects.bulk_create(bulk_instances)


class DPDLabelCreator:
    def __init__(self, mission, client):
        super().__init__()
        self.transport_account = None
        self.username, self.password = None, None
        self.headers = {"Content-Type": "application/soap+xml; charset=UTF-8"}
        self.login_service_url = "https://public-ws.dpd.com/services/LoginService/V2_0/"
        self.shipment_service_url = "https://public-ws.dpd.com/services/ShipmentService/V3_2/"
        # self.login_service_url = "https://public-ws-stage.dpd.com/services/LoginService/V2_0/"  #  staging
        # self.shipment_service_url = "https://public-ws-stage.dpd.com/services/ShipmentService/V3_2/"  #  staging
        self.token = None
        self.client, self.mission = client, mission
        self.transport_account = BusinessAccount.objects.filter(client=self.client,
                                                                transport_service__name__iexact="DPD").first()
        self.transport_service = (self.transport_account.transport_service if self.transport_account is not None
                                  else None)
        self.username = self.transport_account.username
        self.password = decrypt_encrypted_string(self.transport_account.password_encrypted).decode("ISO-8859-1")

        self.country_code = self.get_country_code()

    def get_country_code(self):
        if self.mission.delivery_address.country_code is not None:
            self.country_code = self.mission.delivery_address.country_code
        else:
            for country_json in countries_list:
                for k, v in country_json.items():
                    if str.lower(v) == str.lower(self.mission.delivery_address.country):
                        self.country_code = country_json.get("code")
                        break
        print(f"smile::: {self.country_code}")
        return self.country_code

    def create_label(self):
        parcel_label_number, message = self.create_label_through_dpd_api()
        if parcel_label_number is not None and parcel_label_number != "":
            self.mission.tracking_number = parcel_label_number
            self.mission.online_transport_service = self.transport_service
            self.mission.save()
        return parcel_label_number, message

    def create_label_through_dpd_api(self):
        self.get_authentication_token_from_dpd_api()
        print(f"wie ?? {self.client}")
        first_name_last_name = self.mission.delivery_address.first_name_last_name or ""
        first_name_last_name = first_name_last_name[:35]
        adresszusatz = self.mission.delivery_address.adresszusatz or ""
        adresszusatz = adresszusatz[:35]
        doc = f'''
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
             xmlns:ns="http://dpd.com/common/service/types/Authentication/2.0"
             xmlns:ns1="http://dpd.com/common/service/types/ShipmentService/3.2">
               <soapenv:Header>
                  <ns:authentication>
                     <delisId>{self.username}</delisId>
                     <authToken>{self.token}</authToken>
                     <messageLanguage>de_DE</messageLanguage>
                  </ns:authentication>
               </soapenv:Header>
               <soapenv:Body>
                   <ns1:storeOrders>
                       <printOptions>
                            <printerLanguage>PDF</printerLanguage>
                            <paperFormat>A6</paperFormat>
                       </printOptions>
                       <order>
                            <generalShipmentData>
                                  <identificationNumber />
                                  <sendingDepot>0160</sendingDepot>
                                  <product>CL</product>
                                  <sender>
        <name1>{self.client.contact.delivery_address.firma}</name1>
        <name2>{self.client.contact.delivery_address.vorname} {self.client.contact.delivery_address.nachname}</name2>
        <street>{self.client.contact.delivery_address.strasse}</street>
        <houseNo>{self.client.contact.delivery_address.hausnummer}</houseNo>
                                    <country>DE</country>
                                    <zipCode>{self.client.contact.delivery_address.zip}</zipCode>
                                    <city>{self.client.contact.delivery_address.place}</city>
                                    <gln>0</gln>
                                  </sender>
                                  <recipient>
                                    <name1>{first_name_last_name}</name1>
                                    <name2>{adresszusatz}</name2>
                                    <street>{self.mission.delivery_address.strasse}</street>
                                    <houseNo>{self.mission.delivery_address.hausnummer}</houseNo>
                                    <country>{self.country_code}</country>
                                    <zipCode>{self.mission.delivery_address.zip}</zipCode>
                                    <city>{self.mission.delivery_address.place}</city>
                                    <gln>0</gln>
                                  </recipient>
                            </generalShipmentData>
                            <parcels>
                                <customerReferenceNumber1>{self.mission.channel_order_id}</customerReferenceNumber1>
                                <customerReferenceNumber2 />
                                <customerReferenceNumber3 />
                                <customerReferenceNumber4 />
                                <weight>0</weight>
                            </parcels>
                            <productAndServiceData>
                                <orderType>consignment</orderType>
                            </productAndServiceData>
                       </order>
                   </ns1:storeOrders>
               </soapenv:Body>
            <soapenv:Envelope>
        '''
        doc = doc.replace("\n", "")
        response = requests.post(url=self.shipment_service_url, data=doc.encode("utf-8"), headers=self.headers)
        root = Et.fromstring(response.content.decode("utf-8"))
        print(response.text)
        label_pdf = ""
        for el in root.iter("parcellabelsPDF"):
            label_pdf = el.text
        print(label_pdf)
        label_pdf = base64.decodebytes(str.encode(label_pdf))
        print(label_pdf)

        self.mission.label_pdf.save("label_dpd", ContentFile(label_pdf))
        self.mission.save()

        root = Et.fromstring(response.content.decode("utf-8"))

        parcel_label_number = ""
        for el in root.iter("parcelLabelNumber"):
            parcel_label_number = el.text

        message = ""
        for el in root.iter("message"):
            message = el.text

        return parcel_label_number, message

    def get_authentication_token_from_dpd_api(self):
        doc = f'''
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
             xmlns:ns="http://dpd.com/common/service/types/LoginService/2.0">
               <soapenv:Header/>
               <soapenv:Body>
                   <ns:getAuth>
                       <delisId>{self.username}</delisId>
                       <password>{self.password}</password>
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


class DPDGetLabelView(views.View):
    def __init__(self, **kwargs):
        self.client = None
        self.mission = None
        super().__init__(**kwargs)

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        label_pdf = self.mission.label_pdf.read()
        response = HttpResponse(label_pdf, content_type='application/pdf')
        return response
