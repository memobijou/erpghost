from Crypto.Cipher import AES
from django.shortcuts import render
from django.views import View
import requests
import os
import base64
from client.models import Client
from xml.etree import ElementTree as ET
import urllib
from online.models import Channel
from mission.models import Mission
from datetime import datetime


def encrypt_message(message):
    enc_key = os.environ.get("enc_key")
    iv456 = "randomtask123456"
    aes_object = AES.new(enc_key, AES.MODE_CFB, iv456)
    encrypted_bytes = aes_object.encrypt(message)
    encrypted_string = encrypted_bytes.decode("ISO-8859-1")
    return encrypted_string


def decrypt_encrypted_string(encrypted_string):
    enc_key = os.environ.get("enc_key")
    print(enc_key)
    iv456 = "randomtask123456"
    aes_object = AES.new(enc_key, AES.MODE_CFB, iv456)
    encrypted_bytes = encrypted_string.encode("ISO-8859-1")
    password = aes_object.decrypt(encrypted_bytes)
    return password


class EbayView(View):
    api_url = "https://api.ebay.com/ws/api.dll"
    client_id = "MimounBi-ghost-PRD-281f16f17-13ac9e69"
    client_secret = "PRD-81f16f175250-f0d2-46fe-b208-2fd0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.client = None
        self.ebay_account = None
        self.access_token = None
        self.refresh_token = None
        self.headers = None

    def dispatch(self, request, *args, **kwargs):
        self.client = Client.objects.get(pk=request.session.get("client"))
        self.ebay_account = self.client.apidata_set.filter(pk=8).first()  # für test erstmal
        self.access_token = self.ebay_account.access_token
        self.refresh_token = self.ebay_account.refresh_token
        base_string = base64.b64encode(str.encode(f"{self.client_id}:{self.client_secret}")).decode()
        self.headers = {"Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {base_string}"
                        }
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.fetch_orders()
        return render(request, "online/ebay_test.html", {})

    def fetch_orders(self):
        if self.access_token is None:
            self.get_access_and_refresh_token()

        response = None

        if self.access_token is not None:
            response = requests.post(self.api_url, headers=self.http_headers(), data=self.request_body())

        if response is not None:
            if self.is_access_token_expired(response) is True:
                self.update_expired_access_token()
                response = requests.post(self.api_url, headers=self.http_headers(), data=self.request_body())
            print(f"krankkk: {response.text}")

    def http_headers(self):
        api_site_id = "77"  # Deutschland

        headers = {"X-EBAY-API-SITEID": api_site_id, "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                   "X-EBAY-API-CALL-NAME": "GetOrders", "X-EBAY-API-IAF-TOKEN": self.access_token}
        return headers

    def request_body(self):
        xml = '''
            <?xml version="1.0" encoding="utf-8"?>
            <GetOrdersRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <ErrorLanguage>de_DE</ErrorLanguage>
                <WarningLevel>High</WarningLevel>
                <CreateTimeFrom>2010-10-01</CreateTimeFrom>
                <CreateTimeTo>2010-12-01</CreateTimeTo>
              <OrderRole>Seller</OrderRole>
            </GetOrdersRequest>
        '''
        return xml

    def is_access_token_expired(self, response):
        root = ET.fromstring(response.content.decode("utf-8"))
        namespace = "{urn:ebay:apis:eBLBaseComponents}"

        error_code = None

        for el in root.iter(f"{namespace}ErrorCode"):
            error_code = el.text

        if error_code == "21917053":
            return True

        return False

    def update_expired_access_token(self):
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        url += f"?grant_type=refresh_token&refresh_token={urllib.parse.quote_plus(self.refresh_token)}"
        url += "&scope="
        url += "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly"
        url += f"&redirect_uri=Mimoun_Bijjou-MimounBi-ghost--dndbey"

        print(f"ukthi: {url}")
        print(self.headers)
        response = requests.post(url, headers=self.headers)

        if response.ok is True:
            response_json = response.json()
            access_token = response_json.get("access_token")
            self.ebay_account.access_token = access_token
            self.ebay_account.save()
            self.access_token = self.ebay_account.access_token

        print(f"yeaaaaaaah: {response.text}")

    def get_access_and_refresh_token(self):
        print(self.ebay_account.authentication_token)
        authorization_token = decrypt_encrypted_string(self.ebay_account.authentication_token)
        authorization_token = authorization_token.decode("utf-8")
        print(authorization_token)
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        url += f"?grant_type=authorization_code&code={authorization_token}"
        url += f"&redirect_uri=Mimoun_Bijjou-MimounBi-ghost--dndbey"
        response = requests.post(url, headers=self.headers)
        print(f"sasa: {response.text}")
        print(f"sasa: {response.url}")
        access_token = None
        refresh_token = None

        if response.ok is True:
            response_json = response.json()
            access_token = response_json.get("access_token")
            refresh_token = response_json.get("refresh_token")
            self.ebay_account.access_token = access_token
            self.ebay_account.refresh_token = refresh_token
            self.ebay_account.save()

            self.access_token = self.ebay_account.access_token
            self.refresh_token = self.ebay_account.refresh_token

        print(f"ACCESS: {access_token}")
        print(f"REFRESH: {refresh_token}")


class Ebay:
    api_url = "https://api.ebay.com/ws/api.dll"

    def __init__(self, client, ebay_account):
        super().__init__()
        self.client = client
        self.ebay_account = ebay_account
        self.access_token = self.ebay_account.access_token
        self.refresh_token = self.ebay_account.refresh_token
        self.client_id = self.ebay_account.app_client_id
        self.client_secret = self.ebay_account.client_secret
        base_string = base64.b64encode(str.encode(f"{self.client_id}:{self.client_secret}")).decode()
        self.headers = {"Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {base_string}"
                        }
        self.namespace = "{urn:ebay:apis:eBLBaseComponents}"

    def fetch_orders(self):
        if self.access_token is None:
            self.get_access_and_refresh_token()

        response = None

        if self.access_token is not None:
            response = requests.post(self.api_url, headers=self.http_headers(), data=self.request_body())

        if response is not None:
            if self.is_access_token_expired(response) is True:
                self.update_expired_access_token()
                response = requests.post(self.api_url, headers=self.http_headers(), data=self.request_body())
            print(f"krankkk: {response.text}")
            self.create_or_get_missions_from_response(response)

    def create_or_get_missions_from_response(self, response):
        root = ET.fromstring(response.content.decode('utf-8'))

        created_date = None
        for el in root.iter(f"{self.namespace}CreatedTime"):
            print(el.text)
            created_date = el.text
            break
        print(created_date)
        created_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%fZ")

        ebay_order_id = None
        for el in root.iter(f"{self.namespace}OrderID"):
            print(el.text)
            ebay_order_id = el.text
            break

        if ebay_order_id is not None:
            mission = Mission.objects.filter(channel_order_id=ebay_order_id).first()
            print(mission)
            if mission is None:
                print("???????????")
                channel = Channel.objects.filter(name__iexact="Ebay").first()
                if channel is None:
                    channel = Channel.objects.create(name="Ebay")

                Mission.objects.create(channel_order_id=ebay_order_id, channel=channel, purchased_date=created_date)

    def http_headers(self):
        api_site_id = "77"  # Deutschland

        headers = {"X-EBAY-API-SITEID": api_site_id, "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                   "X-EBAY-API-CALL-NAME": "GetOrders", "X-EBAY-API-IAF-TOKEN": self.access_token}
        return headers

    def request_body(self):
        xml = '''
            <?xml version="1.0" encoding="utf-8"?>
            <GetOrdersRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <ErrorLanguage>de_DE</ErrorLanguage>
                <WarningLevel>High</WarningLevel>
                <CreateTimeFrom>2010-10-01</CreateTimeFrom>
                <CreateTimeTo>2018-09-05</CreateTimeTo>
              <OrderRole>Seller</OrderRole>
            </GetOrdersRequest>
        '''
        return xml

    def is_access_token_expired(self, response):
        root = ET.fromstring(response.content.decode("utf-8"))

        error_code = None

        for el in root.iter(f"{self.namespace}ErrorCode"):
            error_code = el.text

        if error_code == "21917053":
            return True

        return False

    def update_expired_access_token(self):
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        url += f"?grant_type=refresh_token&refresh_token={urllib.parse.quote_plus(self.refresh_token)}"
        url += "&scope="
        url += "https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly"
        url += f"&redirect_uri=Mimoun_Bijjou-MimounBi-ghost--dndbey"

        print(f"ukthi: {url}")
        print(self.headers)
        response = requests.post(url, headers=self.headers)

        if response.ok is True:
            response_json = response.json()
            access_token = response_json.get("access_token")
            self.ebay_account.access_token = access_token
            self.ebay_account.save()
            self.access_token = self.ebay_account.access_token

        print(f"yeaaaaaaah: {response.text}")

    def get_access_and_refresh_token(self):
        print(self.ebay_account.authentication_token)
        authorization_token = decrypt_encrypted_string(self.ebay_account.authentication_token)
        authorization_token = authorization_token.decode("utf-8")
        print(authorization_token)
        url = "https://api.ebay.com/identity/v1/oauth2/token"
        url += f"?grant_type=authorization_code&code={authorization_token}"
        url += f"&redirect_uri=Mimoun_Bijjou-MimounBi-ghost--dndbey"
        response = requests.post(url, headers=self.headers)
        print(f"sasa: {response.text}")
        print(f"sasa: {response.url}")
        access_token = None
        refresh_token = None

        if response.ok is True:
            response_json = response.json()
            access_token = response_json.get("access_token")
            refresh_token = response_json.get("refresh_token")
            self.ebay_account.access_token = access_token
            self.ebay_account.refresh_token = refresh_token
            self.ebay_account.save()

            self.access_token = self.ebay_account.access_token
            self.refresh_token = self.ebay_account.refresh_token

        print(f"ACCESS: {access_token}")
        print(f"REFRESH: {refresh_token}")