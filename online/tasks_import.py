import dateutil.parser
from celery import Task
from celery import shared_task

from adress.models import Adress
from mission.models import Channel, Mission, ProductMission
from collections import OrderedDict

from sku.models import Sku


class AmazonImportTask(Task):
    ignore_result = True

    def __init__(self, arg):
        self.arg = arg
        self.header, self.result = self.arg
        print(f"before run: {self.header} - {self.result}")

    def run(self):
        print(f"in celery run: {self.header} - {self.result}")
        self.get_amazon_mission_instances()

    def get_amazon_mission_instances(self):
        print(len(self.result))
        channel_instance = Channel.objects.get(name="Amazon.de")

        for i, row in enumerate(self.result):
            sku = self.column_from_row("sku", row)
            shipping_price = self.column_from_row("shipping-price", row)
            print(f"this is shipping-price: {shipping_price}")
            print(f"this is sku: {sku}")
            sku_instance = Sku.objects.filter(sku__iexact=sku.strip()).first()

            if sku_instance is None:
                continue

            shipping_address_instance = self.get_shipping_address_instance(row)
            billing_address_instance = self.get_billing_address_instance(row)

            print(shipping_address_instance)

            quantity_purchased = int(self.column_from_row("quantity-purchased", row))
            item_price = float(self.column_from_row("item-price", row))

            delivery_date_from = self.parse_date(self.column_from_row('earliest-delivery-date', row))

            delivery_date_to = self.parse_date(self.column_from_row("latest-delivery-date", row))

            instance_data = {"channel_order_id": self.column_from_row("order-id", row),
                             "is_online": True, "is_amazon_fba": False,
                             "purchased_date": dateutil.parser.parse(self.column_from_row("purchase-date", row),),
                             "delivery_date_from":
                                 self.parse_date(self.column_from_row('earliest-delivery-date', row)),
                             "delivery_date_to": delivery_date_to,
                             "payment_date": delivery_date_from,
                             "delivery_address_id": shipping_address_instance.pk,
                             "channel_id": channel_instance.pk, "billing_address_id": billing_address_instance.pk,
                             "online_transport_cost": shipping_price}
            print(f"bankimoon: {instance_data}")
            mission_instance = Mission.objects.filter(channel_order_id=self.column_from_row("order-id", row)).first()

            if mission_instance is None:
                mission_instance = Mission(**instance_data)
                mission_instance.save()

            productmission_data = {"sku": sku_instance, "amount": quantity_purchased, "mission": mission_instance,
                                   "netto_price": item_price}

            productmission_instance = ProductMission.objects.filter(sku=sku_instance, mission=mission_instance).first()

            print(f"{sku} ------- {productmission_instance or 'No'}")

            if productmission_instance is None:
                productmission_instance = ProductMission.objects.create(**productmission_data)
                productmission_instance.save()

    def get_shipping_address_instance(self, row):
        address_line_1 = self.column_from_row("ship-address-1", row)
        address_line_2 = self.column_from_row("ship-address-2", row)
        address_line_3 = self.column_from_row("ship-address-3", row)
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
        print(f"akhi: {self.header}")
        if type(row) == OrderedDict:
            return row[column]
        index = None
        for header_col in self.header:
            if header_col == column:
                index = self.header.index(header_col)
        if index is not None:
            return row[index]


@shared_task
def amazon_import_task(arg_list):
    amazon_import_instance = AmazonImportTask(arg_list)
    amazon_import_instance.run()
