from django.shortcuts import render
from django.views import View
import requests
import os
import base64
from urllib.parse import unquote


class EbayTestView(View):
    api_url = "https://api.sandbox.ebay.com/ws/api.dll"
    client_id = "MimounBi-ghost-SBX-fc970d9ce-5c50fe4c"
    client_secret = "SBX-c970d9ced171-f8f6-49c3-a573-1585"

    def get(self, request, *args, **kwargs):
        response = requests.post(self.api_url, headers=self.http_headers(), data=self.request_body())
        print(f"was {response}")
        print(response.content)
        print(response.text)
        return render(request, "online/ebay_test.html", {})

    def http_headers(self):
        api_site_id = "77"  # Deutschland

        headers = {"X-EBAY-API-SITEID": api_site_id, "X-EBAY-API-COMPATIBILITY-LEVEL": "967",
                   "X-EBAY-API-CALL-NAME": "GetOrders", "X-EBAY-API-IAF-TOKEN": self.get_token()}
        return headers

    def get_token(self):
        permission_grant_url = f'''
        https://auth.sandbox.ebay.com/oauth2/authorize?client_id=MimounBi-ghost-SBX-fc970d9ce-5c50fe4c&response_type=code&grant_type=authorization_code&redirect_uri=Mimoun_Bijjou-MimounBi-ghost--uofqez&scope=https://api.ebay.com/oauth/api_scope https://api.ebay.com/oauth/api_scope/buy.order.readonly https://api.ebay.com/oauth/api_scope/buy.guest.order https://api.ebay.com/oauth/api_scope/sell.marketing.readonly https://api.ebay.com/oauth/api_scope/sell.marketing https://api.ebay.com/oauth/api_scope/sell.inventory.readonly https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account.readonly https://api.ebay.com/oauth/api_scope/sell.account https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly https://api.ebay.com/oauth/api_scope/sell.fulfillment https://api.ebay.com/oauth/api_scope/sell.analytics.readonly https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly https://api.ebay.com/oauth/api_scope/commerce.catalog.readonly https://api.ebay.com/oauth/api_scope/buy.shopping.cart
        '''
        response = requests.get(permission_grant_url)
        print(response.url)
        print(response.headers)
        token_url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

        print(f'hund: {response.content}')
        self.refresh_token()
        print(os.environ.get("ebay_token"))
        return os.environ.get("ebay_token")

    def refresh_token(self):
        authorization_token = '''v^1.1%23i^1%23I^3%23p^3%23r^1%23f^0%23t^Ul41Xzk6QTkwN0MyNUIwMDUzOTFBMUY1MzVBREJDQjY3MzE4RTlfMV8xI0VeMTI4NA%3D%3D'''
        url = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        url += f"?grant_type=authorization_code&code={authorization_token}"
        url += f"&redirect_uri=Mimoun_Bijjou-MimounBi-ghost--uofqez"
        base_string = base64.b64encode(str.encode(f"{self.client_id}:{self.client_secret}")).decode()

        headers = {"Content-Type": "application/x-www-form-urlencoded",
                   "Authorization": f"Basic {base_string}"
                   }
        print(headers)
        response = requests.post(url, headers=headers)
        print(f"sasa: {response.text}")
        print(f"sasa: {response.url}")
        access_token = None
        refresh_token = None

        if response.ok is True:
            response_json = response.json()
            access_token = response_json.get("access_token")
            refresh_token = response_json.get("refresh_token")

        print(f"ACCESS: {access_token}")
        print(f"REFRESH: {refresh_token}")

    def request_body(self):
        xml = '''
            <?xml version="1.0" encoding="utf-8"?>
            <GetOrdersRequest xmlns="urn:ebay:apis:eBLBaseComponents">
                <ErrorLanguage>de_DE</ErrorLanguage>
                <WarningLevel>High</WarningLevel>
                <CreateTimeFrom>2018-07-11</CreateTimeFrom>
                <CreateTimeTo>2018-08-29</CreateTimeTo>
              <OrderRole>Seller</OrderRole>
            </GetOrdersRequest>
        '''
        return xml
