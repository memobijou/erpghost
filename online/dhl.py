from django import views
from django.db.models import Q
from django.http import HttpResponse
import os
import base64
import requests
from xml.etree import ElementTree as Et

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import UpdateView

from disposition.models import BusinessAccount
from mission.models import Mission, DeliveryNote, DeliveryNoteProductMission, Billing, BillingProductMission
from client.models import Client
from online.forms import DhlForm
from django.urls import reverse_lazy
import pycountry
import datetime
from online.countries_list import countries_list
from stock.models import Stock


class DHLCreatePdfView(UpdateView):
    template_name = "online/dhl_form.html"
    form_class = DhlForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.mission = None

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        if self.mission.online_picklist.completed is True:
            return HttpResponseRedirect(reverse_lazy("online:online_redirect"))
        self.client = Client.objects.get(pk=self.request.session.get("client"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "DHL Label erstellen"
        context["object"] = self.mission
        return context

    def get_object(self, queryset=None):
        return self.mission.delivery_address

    def get_success_url(self, **kwargs):
        return reverse_lazy("online:packing", kwargs={"pk": self.mission.online_picklist.pk})

    def form_valid(self, form, **kwargs):
        name = form.cleaned_data.get("first_name_last_name")
        package_weight = form.cleaned_data.get("package_weight")
        street = form.cleaned_data.get("strasse")
        street_number = form.cleaned_data.get("hausnummer")
        postal_code = form.cleaned_data.get("zip")
        print(f"what the: {postal_code}")
        print(f"but why: {self.client.contact.delivery_address.zip}")
        place = form.cleaned_data.get("place")
        country_code = self.get_country_code()
        dhl_label_creator = DHLLabelCreator(self.mission, self.client)
        dhl_label, errors = dhl_label_creator.create_label(package_weight, name, street, street_number, postal_code,
                                                           place, country_code)
        print(f"COOOL OF: {errors}")
        if errors is not None:
            for error in errors:
                form.add_error(None, error)
            return super().form_invalid(form)
        # self.mission.tracking_number = dhl_label
        picklist = self.mission.online_picklist
        if picklist is not None:
            self.create_delivery_note(picklist)
            self.create_billing(picklist)
        return super().form_valid(form)

    def get_country_code(self):
        country_code = None
        if self.mission.delivery_address.country_code is not None:
            country_code = self.mission.delivery_address.country_code
            return country_code
        else:
            for country_json in countries_list:
                for k, v in country_json.items():
                    if str.lower(v) == str.lower(self.mission.delivery_address.country):
                        country_code = country_json.get("code")
        return country_code

    def create_delivery_note(self, picklist):
        if picklist.online_delivery_note is not None:
            picklist.online_delivery_note.delete()
        picklist.online_delivery_note = DeliveryNote.objects.create()
        picklist.save()
        bulk_instances = []
        for pick_row in picklist.picklistproducts_set.all():
            bulk_instances.append(DeliveryNoteProductMission(product_mission=pick_row.product_mission,
                                                             delivery_note=picklist.online_delivery_note,
                                                             amount=pick_row.confirmed_amount, ))
        DeliveryNoteProductMission.objects.bulk_create(bulk_instances)

    def create_billing(self, picklist):
        if picklist.online_billing is not None:
            picklist.online_billing.delete()
        picklist.online_billing = Billing.objects.create()
        picklist.save()
        bulk_instances = []

        for pick_row in picklist.picklistproducts_set.all():
            bulk_instances.append(BillingProductMission(product_mission=pick_row.product_mission,
                                                        billing=picklist.online_billing,
                                                        amount=pick_row.confirmed_amount))
        BillingProductMission.objects.bulk_create(bulk_instances)


class DHLLabelCreator:
    def __init__(self, mission, client):
        super().__init__()
        self.user_id = "2222222222_01"
        self.user_signature = "pass"
        self.account_number = "22222222225301"
        self.return_shipment_account_number = "22222222220701"
        self.developer_id = os.environ.get("DHL_DEVELOPER_ID")
        self.password = os.environ.get("DHL_PASSWORD")
        self.url = "https://cig.dhl.de/services/sandbox/soap"
        self.mission = mission
        self.client = client
        self.transport_account = BusinessAccount.objects.filter(client=self.client,
                                                                transport_service__name__iexact="DHL").first()
        self.transport_service = (self.transport_account.transport_service if self.transport_account is not None
                                  else None)
        self.package_weight, self.name_1, self.street, self.street_number = None, None, None, None
        self.reference_number = self.mission.channel_order_id
        self.postal_code, self.place, self.country_code = None, None, None
        self.transport_account = BusinessAccount.objects.filter(client=self.client,
                                                                transport_service__name__iexact="DHL").first()
        self.transport_service = (self.transport_account.transport_service if self.transport_account is not None
                                  else None)

    def create_label(self, package_weight, name_1, street, street_number, postal_code, place, country_code):
        self.package_weight, self.name_1, self.street = package_weight, name_1, street
        self.street_number, self.postal_code, self.place = street_number, postal_code, place
        self.country_code = country_code
        self.package_weight = package_weight
        return self.create_label_through_dhl_api()

    def create_label_through_dhl_api(self):
        doc = self.get_xml_request_file()
        base_string = base64.b64encode(str.encode(f"{self.developer_id}:{self.password}")).decode()
        headers = {"Authorization": f"Basic {base_string}"}
        print(doc)
        print("????")
        r = requests.post(self.url, data=doc, headers=headers)

        print(r.content)

        root = Et.fromstring(r.text)
        label_url = ""

        for el in root.iter("labelUrl"):
            label_url = el.text

        shipment_number = None

        root = Et.fromstring(r.text.replace("cis:shipmentNumber", "shipmentNumber"))

        for el in root.iter("shipmentNumber"):
            shipment_number = el.text

        if label_url != "":
            pdf_content = requests.get(label_url, stream=True).content
            print(shipment_number)
            self.mission.tracking_number = shipment_number
            self.mission.online_transport_service = self.transport_service
            self.mission.shipped = True
            self.mission.save()
            return pdf_content, None
        else:
            errors = []
            for el in root.iter("statusMessage"):
                if el.text not in errors:
                    errors.append(el.text)
            for el in root.iter("faultstring"):
                if el.text not in errors:
                    errors.append(el.text)
            return None, errors

    def get_xml_request_file(self):
        print(f"rifaq: {self.country_code}")
        doc = f'''
<?xml version="1.0" encoding="Iso-8859-1" standalone="no"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cis="http://dhl.de/webservice/cisbase" xmlns:bus="http://dhl.de/webservices/businesscustomershipping">
   <soapenv:Header>
      <cis:Authentification>
         <cis:user>{self.user_id}</cis:user>
         <cis:signature>{self.user_signature}</cis:signature>
      </cis:Authentification>
   </soapenv:Header>
   <soapenv:Body>
      <bus:CreateShipmentOrderRequest>
         <bus:Version>
            <majorRelease>2</majorRelease>
            <minorRelease>0</minorRelease>
            <!--Optional:-->
            <build>?</build>
         </bus:Version>
         <!--1 to 30 repetitions:-->
         <ShipmentOrder>
            <sequenceNumber>01</sequenceNumber>
            <Shipment>
               <ShipmentDetails>
                  <product>V53WPAK</product>
                  <cis:accountNumber>{self.account_number}</cis:accountNumber>
                  <!--Optional:-->
                  <customerReference>{self.reference_number}</customerReference>
                  <shipmentDate>{datetime.date.today().strftime("%Y-%m-%d")}</shipmentDate>
                  <!--Optional:-->
                  <returnShipmentAccountNumber>{self.return_shipment_account_number}</returnShipmentAccountNumber>
                  <!--Optional:-->
                  <returnShipmentReference>Retouren-Sendungsreferenz</returnShipmentReference>
                  <ShipmentItem>
                     <weightInKG>{self.package_weight}</weightInKG>
                  </ShipmentItem>
                  <!--Optional:-->
                  <Service>
                     <!--You may enter the following 16 items in any order-->
                     <Endorsement active="1" type="AFTER_DEADLINE"/>
                     <!--Optional:-->
                     <GoGreen active="?"/>
                     <!--Optional:-->
                     <ReturnReceipt active="1"/>
                     <!--Optional:-->
                     <Premium active="1"/>
                     <!--Optional:-->
                     <CashOnDelivery active="?" codAmount="10"/>
                     <!--Optional:-->
                     <AdditionalInsurance active="1" insuranceAmount="2500"/>
                     <!--Optional:-->
                     <BulkyGoods active="1"/>
                  </Service>
                  <!--Optional:-->
                  <Notification>
                     <recipientEmailAddress>no-reply@deutschepost.de</recipientEmailAddress>
                  </Notification>
                  <!--Optional:-->
                  <BankData>
                     <cis:accountOwner>Max Mustermann</cis:accountOwner>
                     <cis:bankName>Postbank</cis:bankName>
                     <cis:iban>DE77100100100123456789</cis:iban>
                     <!--Optional:-->
                     <cis:note1>note 1</cis:note1>
                     <!--Optional:-->
                     <cis:note2>note 2</cis:note2>
                     <!--Optional:-->
                     <cis:bic>PBNKDEFFXXX</cis:bic>
                     <!--Optional:-->
                     <cis:accountreference>?</cis:accountreference>
                  </BankData>
               </ShipmentDetails>
               <Shipper>
                  <Name>
                     <cis:name1>{self.client.contact.delivery_address.firma}</cis:name1>
                     <!--Optional:-->
                     <cis:name2/>
                     <!--Optional:-->
                     <cis:name3/>
                  </Name>
                  <Address>
                     <cis:streetName>{self.client.contact.delivery_address.strasse}</cis:streetName>
                     <cis:streetNumber>{self.client.contact.delivery_address.hausnummer}</cis:streetNumber>
                     <!--0 to 2 repetitions:-->
                     <cis:addressAddition>?</cis:addressAddition>
                     <!--Optional:-->
                     <cis:dispatchingInformation>?</cis:dispatchingInformation>
                     <cis:zip>{self.client.contact.delivery_address.zip}</cis:zip>
                     <cis:city>{self.client.contact.delivery_address.place}</cis:city>
                     <!--Optional:-->
                     <cis:Origin>
                        <!--Optional:-->
                        <cis:country>Deutschland</cis:country>
                        <!--Optional:-->
                        <cis:countryISOCode>DE</cis:countryISOCode>
                        <!--Optional:-->
                        <cis:state>?</cis:state>
                     </cis:Origin>
                  </Address>
                  <Communication>
                     <!--Optional:-->
                     <!--Optional:-->
                     <cis:email/>
                     <!--Optional:-->
                     <cis:contactPerson/>
                  </Communication>
               </Shipper>
               <Receiver>
                  <cis:name1>{self.name_1}</cis:name1>
                  <!--You have a CHOICE of the next 4 items at this level-->
                  <Address>
                     <!--Optional:-->
                     <cis:name2/>
                     <!--Optional:-->
                     <cis:name3/>
                     <cis:streetName>{self.street}</cis:streetName>
                     <cis:streetNumber>{self.street_number}</cis:streetNumber>
                     <!--0 to 2 repetitions:-->
                     <cis:addressAddition></cis:addressAddition>
                     <!--Optional:-->
                     <cis:dispatchingInformation>?</cis:dispatchingInformation>
                     <cis:zip>{self.postal_code}</cis:zip>
                     <cis:city>{self.place}</cis:city>
                     <!--Optional:-->
                     <cis:Origin>
                        <!--Optional:-->
                        <!--Optional:-->
                        <cis:countryISOCode>{self.country_code}</cis:countryISOCode>
                        <!--Optional:-->
                        <cis:state>?</cis:state>
                     </cis:Origin>
                  </Address>
                  <Communication>
                     <!--Optional:-->
                     <!--Optional:-->
                     <cis:email/>
                     <!--Optional:-->
                     <cis:contactPerson/>
                  </Communication>
               </Receiver>
               <!--Optional:-->
               <!--Optional:-->
            </Shipment>
            <!--Optional:-->
            <!--Optional:-->
            <labelResponseType>URL</labelResponseType>
         </ShipmentOrder>
      </bus:CreateShipmentOrderRequest>
   </soapenv:Body>
</soapenv:Envelope>
                '''
        doc = doc.replace("\n", "")
        return doc


class DhlGetLabelView(views.View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = "2222222222_01"
        self.user_signature = "pass"
        self.account_number = "22222222225301"
        self.return_shipment_account_number = "22222222220701"
        self.developer_id = os.environ.get("DHL_DEVELOPER_ID")
        self.password = os.environ.get("DHL_PASSWORD")
        self.url = "https://cig.dhl.de/services/sandbox/soap"
        self.client = None
        self.mission = None
        self.shipment_number = None

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        self.shipment_number = self.kwargs.get("shipment_number")
        self.client = Client.objects.get(pk=self.request.session.get("client"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        dhl_label = self.get_label_from_dhl_api()
        response = HttpResponse(dhl_label, content_type='application/pdf')
        return response

    def get_label_from_dhl_api(self):
        doc = self.get_xml_request_doc(self.shipment_number)

        base_string = base64.b64encode(str.encode(f"{self.developer_id}:{self.password}")).decode()
        headers = {"Authorization": f"Basic {base_string}"}
        print(doc)
        print("????")
        r = requests.post(self.url, data=doc, headers=headers)

        print(r.content)

        root = Et.fromstring(r.text)
        label_data = ""

        for el in root.iter("labelData"):
            label_data = el.text
        print(label_data)

        label_pdf = None

        if label_data != "":
            label_pdf = base64.decodebytes(str.encode(label_data))

        return label_pdf

    def get_xml_request_doc(self, shipment_number):
        doc = f'''
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cis="http://dhl.de/webservice/cisbase"
 xmlns:bus="http://dhl.de/webservices/businesscustomershipping">
   <soapenv:Header>
      <cis:Authentification>
         <cis:user>{self.user_id}</cis:user>
         <cis:signature>{self.user_signature}</cis:signature>
      </cis:Authentification>
   </soapenv:Header>
   <soapenv:Body>
      <bus:GetLabelRequest>
         <bus:Version>
            <majorRelease>2</majorRelease>
            <minorRelease>0</minorRelease>
            <!--Optional:-->
            <build>?</build>
         </bus:Version>
         <!--1 to 30 repetitions:-->
         <cis:shipmentNumber>{shipment_number}</cis:shipmentNumber>
         <!--Optional:-->
         <labelResponseType>B64</labelResponseType>
      </bus:GetLabelRequest>
   </soapenv:Body>
</soapenv:Envelope>
        '''
        doc = doc.replace("\n", "")
        return doc


class DhlDeleteLabelView(views.View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_id = "2222222222_01"
        self.user_signature = "pass"
        self.account_number = "22222222225301"
        self.return_shipment_account_number = "22222222220701"
        self.developer_id = os.environ.get("DHL_DEVELOPER_ID")
        self.password = os.environ.get("DHL_PASSWORD")
        self.url = "https://cig.dhl.de/services/sandbox/soap"
        self.client = None
        self.mission = None
        self.shipment_number = None

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
        self.shipment_number = self.kwargs.get("shipment_number")
        self.client = Client.objects.get(pk=self.request.session.get("client"))
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, **kwargs):
        dhl_label = self.delete_label_through_dhl_api()
        self.mission.tracking_number = None
        self.mission.shipped = None
        self.mission.save()
        return HttpResponseRedirect(reverse_lazy("online:packing", kwargs={"pk": self.mission.online_picklist.pk}))

    def delete_label_through_dhl_api(self):
        doc = self.get_xml_request_doc(self.shipment_number)

        base_string = base64.b64encode(str.encode(f"{self.developer_id}:{self.password}")).decode()
        headers = {"Authorization": f"Basic {base_string}"}
        print(doc)
        print("????")
        r = requests.post(self.url, data=doc, headers=headers)

        print(r.content)

        root = Et.fromstring(r.text)
        label_data = ""

        for el in root.iter("labelData"):
            label_data = el.text
        print(label_data)

        label_pdf = None

        if label_data != "":
            label_pdf = base64.decodebytes(str.encode(label_data))

        return label_pdf

    def get_xml_request_doc(self, shipment_number):
        doc = f'''
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:cis="http://dhl.de/webservice/cisbase"
 xmlns:bus="http://dhl.de/webservices/businesscustomershipping">
   <soapenv:Header>
      <cis:Authentification>
         <cis:user>{self.user_id}</cis:user>
         <cis:signature>{self.user_signature}</cis:signature>
      </cis:Authentification>
   </soapenv:Header>
   <soapenv:Body>
      <bus:DeleteShipmentOrderRequest>
         <bus:Version>
            <majorRelease>2</majorRelease>
            <minorRelease>0</minorRelease>
            <!--Optional:-->
            <build>?</build>
         </bus:Version>
         <!--1 to 30 repetitions:-->
         <cis:shipmentNumber>{shipment_number}</cis:shipmentNumber>
      </bus:DeleteShipmentOrderRequest>
   </soapenv:Body>
</soapenv:Envelope>
        '''
        doc = doc.replace("\n", "")
        return doc