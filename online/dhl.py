from django import views
from django.http import HttpResponse
import os
import base64
import requests
from xml.etree import ElementTree as Et

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import UpdateView
from mission.models import Mission
from client.models import Client
from online.forms import DhlForm
from django.urls import reverse_lazy
import pycountry


class DHLCreatePdfView(UpdateView):
    template_name = "online/dhl_form.html"
    form_class = DhlForm

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.mission = None

    def dispatch(self, request, *args, **kwargs):
        self.mission = Mission.objects.get(pk=self.kwargs.get("pk"))
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
        place = form.cleaned_data.get("place")
        country_code = self.mission.delivery_address.country_code
        dhl_label_creator = DHLLabelCreator(self.mission, self.client)
        dhl_label, errors = dhl_label_creator.create_label(package_weight, name, street, street_number, postal_code,
                                                           place, country_code)
        if errors is not None:
            for error in errors:
                form.add_error(None, error)
            return super().form_invalid(form)
        # self.mission.tracking_number = dhl_label
        return super().form_valid(form)


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
        self.package_weight, self.name_1, self.street, self.street_number = None, None, None, None
        self.postal_code, self.place, self.country_code = None, None, None

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
            self.mission.shipped = True
            self.mission.save()
            return pdf_content, None
        else:
            errors = []
            for el in root.iter("statusMessage"):
                if el.text not in errors:
                    errors.append(el.text)
            return None, errors

    def get_xml_request_file(self):
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
                  <customerReference>Sendungsreferenz</customerReference>
                  <shipmentDate>2018-09-28</shipmentDate>
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