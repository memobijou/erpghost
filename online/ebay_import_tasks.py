import dateutil.parser
from celery import Task
from celery import shared_task
import re
from adress.models import Adress
from mission.models import Channel, Mission, ProductMission
from collections import OrderedDict
import pycountry
from sku.models import Sku


class EbayImportTask(Task):
    ignore_result = True

    def __init__(self, arg):
        self.arg = arg
        self.header, self.result = self.arg
        self.missions_none_sku_amounts = {}
        print(f"before run: {self.header} - {self.result}")

    def run(self):
        print(f"in celery run: {self.header} - {self.result}")
        self.get_ebay_mission_instances()
        for _, data in self.missions_none_sku_amounts.items():
            amount = data.get("amount")
            mission = data.get("instance")
            mission.none_sku_products_amount = amount
            mission.save()
        print(f"{self.missions_none_sku_amounts}")

    def get_ebay_mission_instances(self):
        print(len(self.result))
        not_matchables = {}
        self.result = self.result[:-2]  # entfernt letzte zwei Zeilen mit Mitgliedsname und Protokolle
        for i, row in enumerate(self.result):
            channel_order_id = row.get("Verkaufsprotokollnummer", "") or ""
            sku = row.get("Bestandseinheit", "") or ""

            if channel_order_id == "":
                continue

            print(f"THIS IS SKU: {sku}")
            sku_instance = None

            if sku != "":
                sku_instance = Sku.objects.filter(sku__iexact=sku.strip(), main_sku__isnull=True).first()

            print(f'THIS IS ORDER ID: {channel_order_id}')

            ship_date_from = self.parse_date(row.get("Versanddatum", "") or "")  # not needed
            ship_date_to = self.parse_date(row.get("Versanddatum", "") or "")  # not needed

            purchased_date = self.parse_date(row.get("Datum der Kaufabwicklung", "") or "")
            payment_date = self.parse_date(row.get("Zahlungsdatum", "") or "")

            instance_data = {"channel_order_id": channel_order_id, "is_online": True,
                             "purchased_date": purchased_date, "payment_date": payment_date, "is_ebay": True
                             }

            channel = None
            if sku_instance is not None:
                instance_data["channel"] = sku_instance.channel
                channel = sku_instance.channel

            shipping_address_instance = self.get_shipping_address_instance(row)
            billing_address_instance = self.get_billing_address_instance(row)

            if shipping_address_instance is not None:
                instance_data.update({"delivery_address_id": shipping_address_instance.pk,
                                      })

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

            print(f"bankimoon: {instance_data}")
            mission_instance = Mission.objects.filter(channel_order_id=channel_order_id).first()

            if mission_instance is None:
                if purchased_date != "" and payment_date != "":
                    mission_instance = Mission(**instance_data)

            if instance_data.get("not_matchable", None) is True:
                not_matchables[channel_order_id] = True

            if not_matchables.get(channel_order_id, None) is not True:
                instance_data["not_matchable"] = None
                mission_instance.not_matchable = None

            mission_instance.save()

            if sku == "" and sku_instance is None:
                if mission_instance not in self.missions_none_sku_amounts:
                    self.missions_none_sku_amounts[mission_instance.pk] = {}
                    self.missions_none_sku_amounts[mission_instance.pk]["amount"] = 1
                else:
                    self.missions_none_sku_amounts[mission_instance.pk]["amount"] += 1
                self.missions_none_sku_amounts[mission_instance.pk]["instance"] = mission_instance
            else:
                if mission_instance not in self.missions_none_sku_amounts:
                    self.missions_none_sku_amounts[mission_instance.pk] = {"instance": mission_instance}

            product_description = row.get("Artikelbezeichnung", None)

            if mission_instance is not None:
                productmission_data = {"mission": mission_instance, "online_description": product_description}

                quantity_purchased = row.get("Stückzahl", "") or ""
                print(f"klaus: {quantity_purchased}")
                try:
                    quantity_purchased = int(quantity_purchased)
                    productmission_data["amount"] = quantity_purchased
                except ValueError:
                    print(f"- {quantity_purchased} -  kann nicht in int geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                item_price = row.get("Preis", "") or ""
                item_price = item_price.replace("EUR ", "")
                item_price = item_price.replace(",", ".")
                try:
                    item_price = float(item_price)
                    if quantity_purchased != "":
                        productmission_data["brutto_price"] = item_price/quantity_purchased
                except ValueError:
                    print(f"- {item_price} -  kann nicht in float geparset werden")
                    instance_data["not_matchable"] = True
                    mission_instance.save()

                shipping_price = row.get("Verpackung und Versand", "") or ""
                shipping_price = shipping_price.replace("EUR ", "")
                shipping_price = shipping_price.replace(",", ".")

                try:
                    shipping_price = float(shipping_price)
                    productmission_data["shipping_price"] = shipping_price
                except ValueError:
                    print(f"- {shipping_price} -  kann nicht in float geparset werden")
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

                print(f"why {channel_order_id} - {productmission_data}")

                if sku != "" or sku_instance is not None:
                    if productmission_instance is None:
                        productmission_instance = ProductMission.objects.create(**productmission_data)

                    productmission_instance.save()
                    mission_instance.save()  # damit der richtige Status gesetzt wird

    def get_shipping_address_instance(self, row):
        address_line_1 = row.get("Click &amp", "") or ""
        address_line_2 = row.get(" Collect: Referenznummer", "") or ""

        if address_line_1 == "":
            return

        shipping_address = address_line_1
        recipient_name, ship_city = row.get("Name des Käufers", "") or "", row.get("Versand nach Adresse 1", "") or ""
        ship_country = row.get("Versand nach Staat", "") or ""
        ship_postal_code = row.get("Versand nach Ort", "") or ""

        address_data = {"first_name_last_name": recipient_name, "adresszusatz": None, "adresszusatz2": None,
                        "street_and_housenumber": shipping_address,
                        "address_line_1": address_line_1, "address_line_2": address_line_2,
                        "place": ship_city, "zip": ship_postal_code,
                        "country": ship_country
                        }

        shipping_address_instance = Adress.objects.filter(**address_data).first()
        if shipping_address_instance is None:
            shipping_address_instance = Adress(**address_data)
            shipping_address_instance.save()
        return shipping_address_instance

    def get_billing_address_instance(self, row):
        address_line_1 = row.get("Adresse 1", "") or ""
        address_line_2 = row.get("Adresse 2", "") or ""

        if address_line_1 == "":
            return

        billing_address = address_line_1
        buyer_name, billing_city = row.get("Name des Käufers", "") or "", row.get("Ort", "") or ""
        billing_country = row.get("Land", "") or ""
        billing_postal_code = row.get("PLZ", "") or ""

        address_data = {"first_name_last_name": buyer_name, "adresszusatz": None, "adresszusatz2": None,
                        "street_and_housenumber": billing_address,
                        "address_line_1": address_line_1, "address_line_2": address_line_2,
                        "place": billing_city, "zip": billing_postal_code,"country": billing_country
                        }

        billing_address_instance = Adress.objects.filter(**address_data).first()
        if billing_address_instance is None:
            billing_address_instance = Adress(**address_data)
            billing_address_instance.save()
        return billing_address_instance

    def parse_date(self, date):
        if date != "":
            date = dateutil.parser.parse(date, dayfirst=True)
            return date

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

        print(f'why ??: {country} --- {country in ["Germany", "Deutschland"]} - {business_account.type}')

        print(f"{business_account.type} : {country}")

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

        print(f"sahbi {street_and_housenumber}")
        print(country_name)
        if country_name != "France" and country_name != "Luxenburg":
            components = re.findall(r'(\D.+)\s+(\d+.*)$', street_and_housenumber)
            if len(components) > 0:
                components = components[0]
            print(len(components))
            print(components)
            if len(components) == 2:
                print(components)
                address.strasse = components[0]
                address.hausnummer = components[1]
                address.save()
        else:
            components = re.findall(r'^(\d+\w*)[,\s]*(\D.+)$', street_and_housenumber)
            print(components)
            if len(components) > 0:
                components = components[0]
            if len(components) == 2:
                address.hausnummer = components[0]
                address.strasse = components[1]
                address.save()
        if address.strasse is None and address.hausnummer is None:
            return True
        print(f"sahbi {address.strasse} {address.hausnummer}")


@shared_task
def ebay_import_task(arg_list):
    ebay_import_instance = EbayImportTask(arg_list)
    ebay_import_instance.run()
