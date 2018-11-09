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

        for i, row in enumerate(self.result):
            sku = self.column_from_row("sku", row)
            print(f"this is sku: {sku}")
            sku_instance = None

            if sku != "":
                sku_instance = Sku.objects.filter(sku__iexact=sku.strip(), main_sku__isnull=True).first()

            shipping_address_instance = self.get_shipping_address_instance(row)
            billing_address_instance = self.get_billing_address_instance(row)

            channel_order_id = self.column_from_row("order-id", row)

            print(f'{channel_order_id}')

            delivery_date_from = self.parse_date(self.column_from_row('earliest-delivery-date', row))

            delivery_date_to = self.parse_date(self.column_from_row("latest-delivery-date", row))

            purchased_date = self.parse_date(self.column_from_row("purchase-date", row))

            payment_date = self.parse_date(self.column_from_row("payments-date", row))

            instance_data = {"channel_order_id": channel_order_id, "is_online": True, "is_amazon_fba": False,
                             "purchased_date": purchased_date, "delivery_date_from": delivery_date_from,
                             "delivery_date_to": delivery_date_to, "payment_date": payment_date,
                             }

            if shipping_address_instance is not None:
                instance_data.update({"delivery_address_id": shipping_address_instance.pk,
                                      })

            if billing_address_instance is not None:
                instance_data.update({"billing_address_id": billing_address_instance.pk,
                                      })

            if sku_instance is None:
                instance_data["not_matchable"] = True

            print(f"bankimoon: {instance_data}")
            mission_instance = Mission.objects.filter(channel_order_id=self.column_from_row("order-id", row)).first()

            if mission_instance is None:
                if purchased_date != "" and delivery_date_from != "" and delivery_date_to != "" and payment_date != "":
                    mission_instance = Mission(**instance_data)
                    mission_instance.save()
            else:
                if mission_instance.not_matchable is True:
                    continue

            if sku_instance is not None and mission_instance is not None:
                quantity_purchased = self.column_from_row("quantity-purchased", row)
                try:
                    quantity_purchased = int(quantity_purchased)
                except ValueError:
                    print(f"- {quantity_purchased} -  kann nicht in int geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()
                    continue

                item_price = self.column_from_row("item-price", row)
                try:
                    item_price = float(item_price)
                except ValueError:
                    print(f"- {item_price} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()
                    continue

                shipping_price = self.column_from_row("shipping-price", row)
                try:
                    shipping_price = float(shipping_price)
                except ValueError:
                    print(f"- {shipping_price} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()
                    continue

                shipping_price = self.column_from_row("shipping-price", row)
                try:
                    shipping_price = float(shipping_price)
                except ValueError:
                    print(f"- {shipping_price} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()
                    continue

                discount = self.column_from_row("item-promotion-discount", row)
                try:
                    discount = float(discount)
                except ValueError:
                    print(f"- {discount} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()
                    continue

                shipping_discount = self.column_from_row("ship-promotion-discount", row)
                try:
                    shipping_discount = float(shipping_discount)
                except ValueError:
                    print(f"- {shipping_discount} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()
                    continue

                productmission_data = {"sku": sku_instance, "amount": quantity_purchased, "mission": mission_instance,
                                       "brutto_price": item_price/quantity_purchased, "shipping_price": shipping_price,
                                       "discount": discount, "shipping_discount": shipping_discount}

                productmission_instance = ProductMission.objects.filter(
                    sku=sku_instance, mission=mission_instance).first()

                print(f"{sku} ------- {productmission_instance or 'No'}")

                if productmission_instance is None:
                    productmission_instance = ProductMission.objects.create(**productmission_data)
                    productmission_instance.save()

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
        print(f"akhi: {self.header}")
        if type(row) == OrderedDict:
            return row[column]
        index = None
        for header_col in self.header:
            if header_col == column:
                index = self.header.index(header_col)
        if index is not None:
            return row[index]
        return ""


@shared_task
def amazon_import_task(arg_list):
    amazon_import_instance = AmazonImportTask(arg_list)
    amazon_import_instance.run()
