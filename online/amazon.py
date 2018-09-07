from Crypto.Cipher import AES
from celery import shared_task
import mws
import os
from xml.etree import ElementTree as Et
from datetime import datetime, timedelta
import time
from adress.models import Adress
from contact.models import Contact
from customer.models import Customer
from mission.models import Mission, ProductMission
from product.models import Product
from online.models import Channel
from sku.models import Sku
import csv
from io import StringIO
import requests
import json
from client.models import Client


class OrderMws:
    def __init__(self, access_key, secret_key, account_id, api_data):
        self.api_data = api_data
        self.client = self.api_data.client

        self.orders_api = mws.Orders(access_key=os.environ.get("MWS_ACCESS_KEY"),
                                     secret_key=os.environ.get("MWS_SECRET_KEY"),
                                     account_id=os.environ['MWS_ACCOUNT_ID'],
                                     region="DE",
                                     )
        self.products_api = mws.Products(access_key=os.environ.get("MWS_ACCESS_KEY"),
                                         secret_key=os.environ.get("MWS_SECRET_KEY"),
                                         account_id=os.environ['MWS_ACCOUNT_ID'],
                                         region="DE",
                                         )
        self.reports_api = mws.Reports(access_key=os.environ.get("MWS_ACCESS_KEY"),
                                       secret_key=os.environ.get("MWS_SECRET_KEY"),
                                       account_id=os.environ['MWS_ACCOUNT_ID'],
                                       region="DE",
                                       )
        self.reports_api.get_report_request_list()
        self.orders_namespace = self.orders_api.NAMESPACE
        self.products_namespace = self.products_api.NAMESPACE
        self.reports_namespace = "{http://mws.amazonaws.com/doc/2009-01-01/}"
        self.orders = []
        super().__init__()

    def fetch_orders(self):
        yesterday = datetime.today() - timedelta(3)

        orders_request = self.orders_api.list_orders(marketplaceids=["A1PA6795UKMFR9"],
                                                     created_after=yesterday.strftime('%Y-%m-%d'))

        # orders_request = self.orders_api.list_orders(marketplaceids=["A1PA6795UKMFR9"],
        #                                              created_after='2018-07-08', created_before="2018-07-10")

        print(orders_request.response.text)

        orders_root = Et.fromstring(orders_request.response.content.decode("utf-8"))

        for order_node in orders_root.iter(f"{self.orders_namespace}Order"):
            order_dict = {}
            for col in order_node:
                if len(col):
                    col_dict = {}
                    for col_col in col:
                        col_dict[f'{col_col.tag.replace(self.orders_namespace, "")}'] = col_col.text
                    order_dict[f"{col.tag.replace(self.orders_namespace, '')}"] = col_dict
                else:
                    order_dict[f"{col.tag.replace(self.orders_namespace, '')}"] = col.text
            self.orders.append(order_dict)
        self.fetch_orders_items()
        self.get_or_create_products_from_orders()
        self.get_or_create_missions()
        return self.orders

    def fetch_orders_items(self):
        new_orders = []
        for order in self.orders:
            order_items_request = self.orders_api.list_order_items(amazon_order_id=order.get("AmazonOrderId"))

            order_items_root = Et.fromstring(order_items_request.response.content.decode("utf-8"))

            order_items = []
            for order_items_node in order_items_root.iter(f"{self.orders_namespace}OrderItem"):
                order_items_dict = {}
                for col in order_items_node:
                    if len(col):
                        col_dict = {}
                        for col_col in col:
                            col_dict[f'{col_col.tag.replace(self.orders_namespace, "")}'] = col_col.text
                        order_items_dict[f"{col.tag.replace(self.orders_namespace, '')}"] = col_dict
                    else:
                        order_items_dict[f"{col.tag.replace(self.orders_namespace, '')}"] = col.text
                order_items.append(order_items_dict)
            order["order_items"] = order_items
            new_orders.append(order)
            time.sleep(2)
        self.orders = new_orders
        return self.orders

    def get_or_create_products_from_orders(self):
        new_orders = []
        for order in self.orders:
            order_items = order.get("order_items")

            products = []

            for order_item in order_items:
                product = {}

                seller_sku = order_item.get("SellerSKU")
                asin = order_item.get("ASIN")
                title = order_item.get("Title")

                product_instance = Product.objects.filter(sku__sku=seller_sku).first()

                if product_instance is None:
                    product_instance = Product(title=title)
                    product_instance.save()
                    sku = Sku(sku=seller_sku, state="Neu", product=product_instance)
                    sku.save()

                product["seller_sku"] = order_item.get("SellerSKU")
                product["product"] = product_instance
                product["sku_pricing"] = self.get_price_from_sku(seller_sku)

                product["quantity_ordered"] = order_item.get("QuantityOrdered")
                product["quantity_shipped"] = order_item.get("QuantityShipped")

                if ("ItemPrice" in order_item) is True:
                    product["item_price"] = order_item.get("ItemPrice").get("Amount")

                if ("ItemTax" in order_item) is True:
                    product["item_tax"] = order_item.get("ItemTax").get("Amount")

                products.append(product)
            order["products"] = products
            new_orders.append(order)
        self.orders = new_orders
        return self.orders

    def get_price_from_sku(self, seller_sku):
        sku_pricing_r = self.products_api.get_my_price_for_sku(marketplaceid="A1PA6795UKMFR9", skus=[seller_sku])
        sku_pricing_root = Et.fromstring(sku_pricing_r.response.content.decode("utf-8"))

        sku_pricing_dict = {}
        for sku_pricing_node in sku_pricing_root.iter(f"{self.products_namespace}BuyingPrice"):
            for col in sku_pricing_node:
                if len(col):
                    col_dict = {}
                    for col_col in col:
                        col_dict[f'{col_col.tag.replace(self.products_namespace, "")}'] = col_col.text
                    sku_pricing_dict[f"{col.tag.replace(self.products_namespace, '')}"] = col_dict
                else:
                    sku_pricing_dict[f"{col.tag.replace(self.products_namespace, '')}"] = col.text
            break

        return sku_pricing_dict

    def get_or_create_missions(self):
        for order in self.orders:
            mission_instance = self.update_or_create_single_mission(order=order)
            self.update_or_create_shipping_address_from_order(order, mission_instance)
            self.update_or_create_customer_from_order(order, mission_instance)
            self.update_or_create_channel_from_order(order, mission_instance)
            self.add_product_items_from_order_to_mission_instance(order, mission_instance)
            mission_instance.save()

    def update_or_create_single_mission(self, order):
        purchase_date, earliest_ship_date = order.get("PurchaseDate"), order.get("EarliestShipDate")
        earliest_ship_date = datetime.strptime(earliest_ship_date.split("T")[0], '%Y-%m-%d')
        amazon_order_id = order.get("AmazonOrderId")

        mission_instance = Mission.objects.filter(channel_order_id=amazon_order_id).first()

        if mission_instance is None:
            mission_instance = Mission(delivery_date=earliest_ship_date, channel_order_id=amazon_order_id)
            mission_instance.save()

        is_prime, is_business_order = order.get("IsPrime"), order.get("IsBusinessOrder")
        is_premium_order = order.get("IsPremiumOrder")

        order_status = order.get("OrderStatus")
        mission_instance.status = order_status

        if order.get("FulfillmentChannel") == "AFN":
            mission_instance.is_amazon_fba = True
        else:
            mission_instance.is_amazon_fba = False

        return mission_instance

    def update_or_create_channel_from_order(self, order, mission_instance):
        sales_channel = order.get("SalesChannel")
        channel_instance = Channel.objects.filter(name=sales_channel).first()

        if channel_instance is None:
            channel_instance = Channel(name=sales_channel, api_data=self.api_data)
        else:
            channel_instance.name = sales_channel

            if channel_instance.api_data is None:
                channel_instance.api_data = self.api_data
        channel_instance.save()

        mission_instance.channel = channel_instance
        return channel_instance

    def update_or_create_customer_from_order(self, order, mission_instance):
        buyer_name = order.get("BuyerName")
        buyer_mail = order.get("BuyerEmail")

        if buyer_mail is None or buyer_mail == "":
            return

        customer_instance = Customer.objects.filter(contact__first_name_last_name=buyer_name,
                                                    contact__email=buyer_mail).first()

        if customer_instance is None:
            contact = Contact(email=buyer_mail, first_name_last_name=buyer_name)
            contact.save()
            customer_instance = Customer(contact=contact)
            customer_instance.save()
        else:
            customer_instance.email = buyer_mail
            customer_instance.first_name_last_name = buyer_name
            customer_instance.save()

        if mission_instance.customer is None:
            mission_instance.customer = customer_instance
        return customer_instance

    def update_or_create_shipping_address_from_order(self, order, mission_instance):
        shipping_address = order.get("ShippingAddress")
        # restlich werte aus json in Adresse speichern
        if shipping_address is not None:
            shipping_address_components = self.get_street_and_housenumber_from_shipping_address(shipping_address)
            address_components_from_google = None

            city_and_postal_code_have_changed = (mission_instance.delivery_address is not None
                                                 and mission_instance.delivery_address.place is not None
                                                 and mission_instance.delivery_address.zip is not None
                                                 and str.lower(shipping_address.get("City")) !=
                                                 str.lower(mission_instance.delivery_address.place)
                                                 and str.lower(shipping_address.get("PostalCode")) !=
                                                 str.lower(mission_instance.delivery_address.zip))

            postal_code_or_place_is_none = (mission_instance.delivery_address is not None
                                            and (mission_instance.delivery_address.place is None
                                                 or mission_instance.delivery_address.zip is None))

            if (mission_instance.delivery_address is None) or (city_and_postal_code_have_changed is True):
                address_components_from_google = self.get_address_components_from_google_api(shipping_address)

            street_number, street, street_and_housenumber = None, None, None
            street_and_housenumber = shipping_address_components.get("street_and_housenumber")

            if address_components_from_google is not None:
                street = address_components_from_google.get("route")
                street_number = address_components_from_google.get("street_number")
                city = address_components_from_google.get("city")
                postal_code = address_components_from_google.get("postal_code")

                if city is None:
                    city = shipping_address.get("City")

                if postal_code is None:
                    postal_code = shipping_address.get("PostalCode")
            else:
                city = shipping_address.get("City")
                postal_code = shipping_address.get("PostalCode")

            if mission_instance.delivery_address is None:
                shipping_address_instance = Adress(first_name_last_name=shipping_address.get("Name"),
                                                   strasse=street,
                                                   hausnummer=street_number,
                                                   street_and_housenumber=street_and_housenumber,
                                                   adresszusatz=None,
                                                   adresszusatz2=None,
                                                   place=city,
                                                   zip=postal_code,
                                                   country_code=shipping_address.get("CountryCode"))
                shipping_address_instance.save()
                mission_instance.delivery_address = shipping_address_instance
            else:
                if city_and_postal_code_have_changed is True or postal_code_or_place_is_none:
                    mission_instance.delivery_address.first_name_last_name = shipping_address.get("Name")
                    mission_instance.delivery_address.strasse = street
                    mission_instance.delivery_address.hausnummer = street_number
                    mission_instance.delivery_address.street_and_housenumber = street_and_housenumber
                    mission_instance.delivery_address.adresszusatz = None
                    mission_instance.delivery_address.adresszusatz2 = None
                    mission_instance.delivery_address.place = city
                    mission_instance.delivery_address.zip = postal_code
                    mission_instance.delivery_address.country_code = shipping_address.get("CountryCode")
                    mission_instance.delivery_address.save()

        return mission_instance.delivery_address

    def get_street_and_housenumber_from_shipping_address(self, shipping_address):
        street_components = {}

        if "AddressLine1" in shipping_address and "AddressLine2" in shipping_address:
            street_components["company"] = shipping_address.get("AddressLine1")
            street_components["street_and_housenumber"] = shipping_address.get("AddressLine2")
        elif "AddressLine1" in shipping_address and "AddressLine2" not in shipping_address:
            street_components["street_and_housenumber"] = shipping_address.get("AddressLine1")
        elif "AddressLine2" in shipping_address and "AddressLine1" not in shipping_address:
            street_components["street_and_housenumber"] = shipping_address.get("AddressLine2")

        return street_components

    def get_address_components_from_google_api(self, shipping_address):
        street_components = self.get_street_and_housenumber_from_shipping_address(shipping_address)

        city = shipping_address.get("City")
        postal_code = shipping_address.get("PostalCode")

        place_id = self.get_place_id_from_google_maps(street_components["street_and_housenumber"], city, postal_code)
        if place_id is None:
            return

        place_details = self.get_place_details_from_google_maps(place_id)

        if place_details is not None:
            return place_details

        # Checken ob Addresslinie 1 und 2 vorhanden, wenn ja dann, Company -> Adresse
        # Checken ob nur Addressline 1, wenn ja dann, Adresse
        # Checken ob nur Addressline 2, wenn ja dann, Adresse

        return

    def get_place_id_from_google_maps(self, street_and_housenumber, city, postal_code):
        google_maps_input = f"{street_and_housenumber} {city} {postal_code}"
        google_maps_url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
        query_string = f"?key={os.environ.get('GOOGLE_MAPS_KEY')}&inputtype=textquery&input={google_maps_input}"
        google_maps_url += query_string
        print(f"blablabla: {google_maps_url}")
        response = requests.get(google_maps_url)
        json_data = json.loads(response.text)

        if json_data["status"] == "ZERO_RESULTS":
            return

        if json_data["status"] == "OVER_QUERY_LIMIT":
            return

        print(json_data)
        candidates = json_data["candidates"]
        for candidate in candidates:
            print(f"{candidate}")
            place_id = candidate["place_id"]
            print(f"{place_id}")
            return place_id

    def get_place_details_from_google_maps(self, place_id):
        google_maps_url = "https://maps.googleapis.com/maps/api/place/details/json"
        query_string = f"?key={os.environ.get('GOOGLE_MAPS_KEY')}&placeid={place_id}"
        google_maps_url += query_string
        response = requests.get(google_maps_url)
        json_data = json.loads(response.text)

        if json_data["status"] == "ZERO_RESULTS":
            return

        if json_data["status"] == "OVER_QUERY_LIMIT":
            return

        result = json_data["result"]
        address_components = result["address_components"]
        street_number, route, city, postal_code = "", "", "", ""
        for address_component in address_components:
            if "street_number" in address_component.get("types"):
                street_number = address_component.get("long_name")
            if "route" in address_component.get("types"):
                route = address_component.get("long_name")
            if "locality" in address_component.get("types") and "political" in address_component.get("types"):
                city = address_component.get("long_name")
            if "postal_code" in address_component.get("types"):
                postal_code = address_component.get("long_name")
        print(f"FRONTEND: {route} {street_number} {postal_code} {city}")
        print(f"baduni {json_data}")
        return {"route": route, "street_number": street_number, "city": city, "postal_code": postal_code}

    def add_product_items_from_order_to_mission_instance(self, order, mission_instance):
        order_products = order.get("products")
        bulk_instances = []

        for item in order_products:
            product_instance = item["product"]
            sku_pricing = item["sku_pricing"]

            quantity_ordered = item["quantity_ordered"]
            quantity_shipped = item["quantity_shipped"]

            item_price = None

            if ("item_price" in item) is True:
                item_price = item.get("item_price")

            if ("item_tax" in item) is True:
                item_tax = item.get("item_tax")

            print(f"aoo: {item}")
            print(f"status: {order.get('OrderStatus')}")
            print(f"Amazon Order Id: {order.get('AmazonOrderId')}")
            print(f"boo: {item_price}")

            listing_price = None

            if item_price is None:
                if ("ListingPrice" in sku_pricing) is True:
                    listing_price = float(sku_pricing.get("ListingPrice").get("Amount"))
                    shipping_price = sku_pricing.get("Shipping").get("Amount")
            else:
                if quantity_ordered == "0":
                    listing_price = 0
                else:
                    listing_price = f"{float(item_price) / int(quantity_ordered)}"

            if listing_price is None:
                listing_price = self.get_price_from_report(item.get("seller_sku"))

            product_mission_instance = mission_instance.productmission_set.filter(product=product_instance).first()

            print(f"{listing_price}")

            if product_mission_instance is None:
                bulk_instances.append(ProductMission(product=product_instance, mission=mission_instance,
                                                     amount=quantity_ordered, netto_price=listing_price, state="Neu",
                                                     online_shipped_amount=quantity_shipped))
            else:
                product_mission_instance.product = product_instance
                product_mission_instance.amount = quantity_ordered
                product_mission_instance.netto_price = listing_price
                product_mission_instance.online_shipped_amount = quantity_shipped
                product_mission_instance.save()

        if len(bulk_instances) > 0:
            ProductMission.objects.bulk_create(bulk_instances)

    def get_price_from_report(self, seller_sku):
        price = 0
        report = self.get_report("_GET_MERCHANT_LISTINGS_INACTIVE_DATA_")
        for row in report:
            if row.get("seller-sku") == seller_sku:
                return row.get("price")
        print(row)
        return 0

    def get_report_request_id(self, report_type):
        request_id = None
        request_report = self.reports_api.request_report(report_type=report_type)
        response = request_report.response.text
        print(report_type)
        print(response)
        root = Et.fromstring(response)
        for el in root.iter(f"{self.reports_namespace}ReportRequestId"):
            request_id = el.text
        print(f"ba3da : {request_id}")
        return request_id

    def get_generated_report_id(self, request_id):
        generated_report_id = None

        count = 0
        while generated_report_id is None:
            report_request = self.reports_api.get_report_request_list(requestids=[request_id])
            response = report_request.response.text
            root = Et.fromstring(response)
            for el in root.iter(f"{self.reports_namespace}GeneratedReportId"):
                generated_report_id = el.text
            print(response)
            if generated_report_id is None:
                print("sleep")
                time.sleep(45)
            count += 1
            if count == 5:
                break
        return generated_report_id

    def get_report(self, report_type):
        request_id = self.get_report_request_id(report_type)
        report_id = self.get_generated_report_id(request_id)
        report = self.reports_api.get_report(report_id=report_id)
        table = report.response.text
        infile = StringIO(table)
        result = csv.DictReader(infile, dialect=csv.Sniffer().sniff(infile.read(1000)))
        infile.seek(0)
        return result
