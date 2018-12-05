import dateutil.parser
from celery import Task
from celery import shared_task
import pycountry
import re
from adress.models import Adress
from mission.models import Mission, ProductMission
from collections import OrderedDict

from sku.models import Sku


class AmazonImportTask(Task):
    ignore_result = True

    def __init__(self, arg):
        self.arg = arg
        self.header, self.result = self.arg

    def run(self):
        self.get_amazon_mission_instances()

    def get_amazon_mission_instances(self):
        not_matchables = {}

        for i, row in enumerate(self.result):
            channel_order_id = self.column_from_row("order-id", row)
            sku = self.column_from_row("sku", row)
            print(f"this is channel and sku: {channel_order_id} - {sku}")

            if channel_order_id == "" or sku == "":
                continue

            sku_instance = None

            if sku != "":
                sku_instance = Sku.objects.filter(sku__iexact=sku.strip(), main_sku__isnull=True).first()

            delivery_date_from = self.parse_date(self.column_from_row('earliest-delivery-date', row))

            delivery_date_to = self.parse_date(self.column_from_row("latest-delivery-date", row))

            ship_date_from = self.parse_date(self.column_from_row('earliest-ship-date', row))

            ship_date_to = self.parse_date(self.column_from_row("latest-ship-date", row))

            purchased_date = self.parse_date(self.column_from_row("purchase-date", row))

            payment_date = self.parse_date(self.column_from_row("payments-date", row))

            instance_data = {"channel_order_id": channel_order_id, "is_online": True,
                             "purchased_date": purchased_date, "delivery_date_from": delivery_date_from,
                             "delivery_date_to": delivery_date_to, "ship_date_from": ship_date_from,
                             "ship_date_to": ship_date_to, "payment_date": payment_date, "is_amazon": True
                             }

            channel = None
            if sku_instance is not None:
                instance_data["channel"] = sku_instance.channel
                channel = sku_instance.channel

            shipping_address_instance = self.get_shipping_address_instance(row)
            billing_address_instance = self.get_billing_address_instance(row)

            if shipping_address_instance is not None:
                instance_data.update({"delivery_address_id": shipping_address_instance.pk})

                if channel is not None:
                    business_account = self.get_business_account(shipping_address_instance, channel)
                    if business_account is not None:
                        instance_data.update({"online_business_account_id": business_account.pk})

                self.break_down_address_in_street_and_house_number(shipping_address_instance)

            if billing_address_instance is not None:
                instance_data.update({"billing_address_id": billing_address_instance.pk})

                self.break_down_address_in_street_and_house_number(billing_address_instance)

            if sku_instance is None or (sku_instance.product.ean is None or sku_instance.product.ean == ""):
                instance_data["not_matchable"] = True

            mission_instance = Mission.objects.filter(channel_order_id=channel_order_id).first()

            if mission_instance is None:
                if purchased_date != "" and delivery_date_from != "" and delivery_date_to != "" and payment_date != "":
                    mission_instance = Mission(**instance_data)

            if instance_data.get("not_matchable", None) is True:
                not_matchables[channel_order_id] = True

            if not_matchables.get(channel_order_id, None) is not True:
                instance_data["not_matchable"] = None
                mission_instance.not_matchable = None

            mission_instance.save()

            if mission_instance is not None:

                productmission_data = {"mission": mission_instance}

                product_description = self.column_from_row("product-name", row)

                if product_description != "":
                    productmission_data["online_description"] = product_description

                order_item_id = self.column_from_row("order-item-id", row)

                if order_item_id != "":
                    productmission_data["online_identifier"] = order_item_id

                quantity_purchased = self.column_from_row("quantity-purchased", row)
                try:
                    quantity_purchased = int(quantity_purchased)
                    productmission_data["amount"] = quantity_purchased
                except ValueError:
                    print(f"- {quantity_purchased} -  kann nicht in int geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                item_price = self.column_from_row("item-price", row)
                try:
                    item_price = float(item_price)
                    if quantity_purchased != "":
                        productmission_data["brutto_price"] = item_price/quantity_purchased
                except ValueError:
                    print(f"- {item_price} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                shipping_price = self.column_from_row("shipping-price", row)
                try:
                    shipping_price = float(shipping_price)
                    productmission_data["shipping_price"] = shipping_price
                except ValueError:
                    print(f"- {shipping_price} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                discount = self.column_from_row("item-promotion-discount", row)
                try:
                    discount = float(discount)
                    productmission_data["discount"] = discount
                except ValueError:
                    print(f"- {discount} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                shipping_discount = self.column_from_row("ship-promotion-discount", row)
                try:
                    shipping_discount = float(shipping_discount)
                    productmission_data["shipping_discount"] = shipping_discount
                except ValueError:
                    print(f"- {shipping_discount} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                if sku_instance is not None:
                    productmission_data["sku"] = sku_instance
                    productmission_instance = ProductMission.objects.filter(
                        sku=sku_instance, mission=mission_instance).first()
                elif sku != "":
                    productmission_data["no_match_sku"] = sku
                    productmission_instance = ProductMission.objects.filter(
                        no_match_sku=sku, mission=mission_instance).first()

                print(f"ENTON 123456:::  {sku} ------- {productmission_instance or 'No'}")

                if sku != "" or sku_instance is not None:
                    if productmission_instance is None:
                        productmission_instance = ProductMission.objects.create(**productmission_data)

                    productmission_instance.save()
                    mission_instance.save()  # damit der richtige Status gesetzt wird

    def get_shipping_address_instance(self, row):
        address_line_1 = self.column_from_row("ship-address-1", row)
        address_line_2 = self.column_from_row("ship-address-2", row)
        address_line_3 = self.column_from_row("ship-address-3", row)

        if address_line_1 == "" and address_line_2 == "" and address_line_3 == "":
            return

        shipping_address = self.get_street_and_housenumber_from_address(address_line_1, address_line_2,
                                                                        address_line_3)
        recipient_name, ship_city = self.column_from_row("recipient-name", row), self.column_from_row("ship-city", row)
        ship_country_code = self.column_from_row("ship-country", row)
        ship_postal_code = self.column_from_row("ship-postal-code", row)

        address_data = {"first_name_last_name": recipient_name, "adresszusatz": None, "adresszusatz2": None,
                        "street_and_housenumber": shipping_address.get("street_and_housenumber"),
                        "address_line_1": address_line_1, "address_line_2": address_line_2,
                        "address_line_3": address_line_3, "place": ship_city, "zip": ship_postal_code,
                        "country_code": ship_country_code
                        }

        shipping_address_instance = Adress.objects.filter(**address_data).first()
        if shipping_address_instance is None:
            shipping_address_instance = Adress(**address_data)
            shipping_address_instance.save()
        return shipping_address_instance

    def get_billing_address_instance(self, row):
        address_line_1 = self.column_from_row("bill-address-1", row)
        address_line_2 = self.column_from_row("bill-address-2", row)
        address_line_3 = self.column_from_row("bill-address-3", row)

        if address_line_1 == "" and address_line_2 == "" and address_line_3 == "":
            return

        billing_address = self.get_street_and_housenumber_from_address(address_line_1, address_line_2,
                                                                       address_line_3)
        buyer_name, billing_city = self.column_from_row("buyer-name", row), self.column_from_row("bill-city", row)
        billing_country_code = self.column_from_row("bill-country", row)
        billing_postal_code = self.column_from_row("bill-postal-code", row)

        address_data = {"first_name_last_name": buyer_name, "adresszusatz": None, "adresszusatz2": None,
                        "street_and_housenumber": billing_address.get("street_and_housenumber"),
                        "address_line_1": address_line_1, "address_line_2": address_line_2,
                        "address_line_3": address_line_3, "place": billing_city, "zip": billing_postal_code,
                        "country_code": billing_country_code
                        }

        billing_address_instance = Adress.objects.filter(**address_data).first()
        if billing_address_instance is None:
            billing_address_instance = Adress(**address_data)
            billing_address_instance.save()
        return billing_address_instance

    def get_street_and_housenumber_from_address(self, address_line_1, address_line_2, address_line_3):
        street_components = {}

        if address_line_1 != "" and address_line_2 != "":
            street_components["company"] = address_line_1
            street_components["street_and_housenumber"] = address_line_2
        elif address_line_1 != "" and address_line_2 == "":
            street_components["street_and_housenumber"] = address_line_1
        elif address_line_2 != "" and address_line_1 == "":
            street_components["street_and_housenumber"] = address_line_2
        return street_components

    def parse_date(self, date):
        if date != "":
            date = dateutil.parser.parse(date)
            return date

    def column_from_row(self, column, row):
        index = None
        for header_col in self.header:
            if header_col == column:
                index = self.header.index(header_col)
        if index is not None:
            return row[index]
        return ""

    def get_business_account(self, address_instance, channel):
        country = None
        if address_instance.country is not None and address_instance.country != "":
            country = address_instance.country
        elif address_instance.country_code is not None:
            delivery_address_country_code = address_instance.country_code
            country = pycountry.countries.get(alpha_2=delivery_address_country_code)
            country = country.name

        if (country in ["Germany", "Deutschland"]) is True:
            business_account = channel.client.businessaccount_set.filter(type="national").first()
        else:
            business_account = channel.client.businessaccount_set.filter(type="foreign_country").first()

        return business_account

    # Adresse in Stasse und Hausnummer zerlegen durch Reguläre Ausdrücke
    def break_down_address_in_street_and_house_number(self, address):
        street_and_housenumber = address.street_and_housenumber
        country_code = address.country_code
        country_name = ""
        if country_code is not None and country_code != "":
            country = pycountry.countries.get(alpha_2=country_code)
            country_name = country.name
        elif address.country is not None and address.country != "":
            country_name = address.country

        if country_name != "France" and country_name != "Luxenburg":
            components = re.findall(r'(\D.+)\s+(\d+.*)$', street_and_housenumber)
            if len(components) > 0:
                components = components[0]
            if len(components) == 2:
                address.strasse = components[0]
                address.hausnummer = components[1]
                address.save()
        else:
            components = re.findall(r'^(\d+\w*)[,\s]*(\D.+)$', street_and_housenumber)
            if len(components) > 0:
                components = components[0]
            if len(components) == 2:
                address.hausnummer = components[0]
                address.strasse = components[1]
                address.save()
        if address.strasse is None and address.hausnummer is None:
            return True


@shared_task
def amazon_import_task(arg_list):
    amazon_import_instance = AmazonImportTask(arg_list)
    amazon_import_instance.run()
