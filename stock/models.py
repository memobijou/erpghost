from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.db.models import Sum
from django.template import Context, Template
import re

from mission.models import PartialMissionProduct, DeliveryNoteProductMission, PickListProducts
from product.models import Product
from sku.models import Sku


class Stock(models.Model):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.states = ["Neu", "B", "C", "D", "G"]

    IGNORE_CHOICES = (
        ('IGNORE', 'Ja'),
        ('NOT_IGNORE', 'Nein'),
    )

    id = models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')
    ean_vollstaendig = models.CharField(max_length=250, verbose_name="EAN", null=True, blank=True)
    sku = models.CharField(max_length=250, verbose_name="Sku", null=True, blank=True)
    title = models.CharField(max_length=250, verbose_name="Artikelname", null=True, blank=True)
    zustand = models.CharField(max_length=250, null=True, blank=True, verbose_name="Zustand")
    ean_upc = models.CharField(max_length=250, null=True, blank=True)
    lagerplatz = models.CharField(max_length=250, null=True, blank=True, verbose_name="Lagerplatz")
    bestand = models.IntegerField(null=True, blank=True, verbose_name="Bestand")
    regal = models.CharField(max_length=250, null=True, blank=True, verbose_name="Regal")
    scanner = models.IntegerField(null=True, blank=True, verbose_name="Scanner")
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="Person")
    karton = models.CharField(max_length=250, null=True, blank=True, verbose_name="Karton")
    box = models.CharField(max_length=250, null=True, blank=True, verbose_name="Box")
    aufnahme_datum = models.CharField(max_length=250, null=True, blank=True, verbose_name="Aufnahme Datum")
    ignore_unique = models.CharField(max_length=250, null=True, blank=True, choices=IGNORE_CHOICES,
                                     verbose_name="Block")
    missing_amount = models.IntegerField(blank=True, null=True, verbose_name="Fehlender Bestand")
    product = models.ForeignKey(Product, blank=True, null=True, on_delete=models.SET_NULL)

    def get_absolute_url(self):
        return reverse("stock:detail", kwargs={'pk': self.id})

    def __str__(self):
        return str(self.ean_vollstaendig)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None, *args, **kwargs):
        product = self.get_product()
        if product is not None:
            self.product = product
        super().save(*args, **kwargs)

    def clean(self):

        if self.lagerplatz is None:
            return

        has_ean = self.ean_vollstaendig is not None and self.ean_vollstaendig != ""
        has_sku = self.sku is not None and self.sku != ""

        if has_ean is True and has_sku is True:
            only_ean_or_sku_or_title_html =\
                "<h3 style='color:red;'>Sie dürfen nur eine Angabe machen: EAN oder SKU</h3>"
            c = Context({'unique_message': 'Your message'})
            raise ValidationError(Template(only_ean_or_sku_or_title_html).render(c))

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            if self.zustand is None or self.zustand == "":
                stock_html = "<h3 style='color:red;'>Wenn Sie eine EAN eingeben, müssen Sie einen Zustand" \
                             " bestimmen.</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))

        if self.sku is not None and self.sku != "":
            if self.zustand is not None and self.zustand != "":
                stock_html = \
                    "<h3 style='color:red;'>Wenn Sie eine SKU angeben dürfen Sie keinen Zustand auswählen" \
                    "</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))

        if (self.sku is None or self.sku == "") and (self.ean_vollstaendig is None or self.ean_vollstaendig == ""):
            stock_html =\
                "<h3 style='color:red;'>Sie müssen entweder eine EAN oder eine SKU eingeben</h3>"
            c = Context({'unique_message': 'Your message'})
            raise ValidationError(Template(stock_html).render(c))

        stocks = None

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            skus_with_same_ean = []
            products_with_ean = Product.objects.filter(ean=self.ean_vollstaendig)

            for product_with_ean in products_with_ean:
                sku_of_product_with_ean = product_with_ean.sku_set.filter(state=self.zustand).first().sku
                stock_sku = Stock.objects.filter(sku=sku_of_product_with_ean)
                if stock_sku.count() > 0:
                    skus_with_same_ean.append(sku_of_product_with_ean)
            stocks = Stock.objects.filter(Q(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand,
                                          lagerplatz=self.lagerplatz) | Q(sku__in=skus_with_same_ean,
                                                                          lagerplatz=self.lagerplatz))\
                .exclude(id=self.id)

        elif self.sku is not None and self.sku != "":
            if Product.objects.filter(sku__sku__exact=self.sku).count() == 0:
                stock_html = \
                    f"<h3 style='color:red;'>Bitte geben Sie eine gültige SKU ein. " \
                    f"Die SKU {self.sku} existiert nicht im System." \
                    f"</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))

            product_with_sku = Product.objects.filter(sku__sku=self.sku).distinct().first()

            ean_from_sku = None
            state_from_sku = None

            if product_with_sku is not None and product_with_sku != "":
                ean_from_sku = product_with_sku.ean
                state_from_sku = product_with_sku.sku_set.filter(sku=self.sku).first().state

            stocks = Stock.objects.filter(Q(ean_vollstaendig=ean_from_sku, zustand=state_from_sku,
                                            lagerplatz=self.lagerplatz) | Q(sku=self.sku, lagerplatz=self.lagerplatz))\
                .exclude(id=self.id)
        if stocks is not None and stocks.count() > 0 and "block" not in self.lagerplatz.lower():
            stock_html = "<h1 style='color:red;'>Lagerbestand schon vorhanden</h1>" \
                         "<div class='table-responsive'><table class='table table-bordered'>" \
                         "<thead>" \
                         "<tr>" \
                         "<th></th><th>EAN</th><th>SKU</th><th>Lagerplatz</th><th>Zustand</th><th>IST Bestand</th>"\
                         "</tr>" \
                         "</thead>"\
                         "<tbody>"

            for stock in stocks:
                if stock.ean_vollstaendig is not None:
                    stock_ean = stock.ean_vollstaendig
                else:
                    stock_ean = ""

                if stock.bestand is not None:
                    stock_bestand = stock.bestand
                else:
                    stock_bestand = ""

                stock_html = stock_html + f"<tr>" \
                                          "<td><a href=" + "'{% " f"url 'stock:edit' pk={stock.id}" + " %}'" \
                                          + ">Bearbeiten</a></td>" \
                                          f"<td>{stock_ean or ''}</td>" \
                                          f"<td>{stock.sku or ''}</td>" \
                                          f"<td>{stock.lagerplatz}</td>" \
                                          f"<td>{stock.zustand}</td>" \
                                          f"<td>{stock_bestand}</td>" \
                                          f"</tr>"
            stock_html += "</tbody></table></div>"
            c = Context({'unique_message': 'Your message'})
            raise ValidationError(Template(stock_html).render(c))

    def get_total_stocks(self, product=None):

        if self.product is not None:
            product = self.product

        if product is None:
            product = self.get_product()

        if product is None:
            if self.sku is not None and self.sku != "":
                total_from_sku = self.get_total_from_sku()
                if total_from_sku is not None:
                    return {"Gesamt": total_from_sku, "Neu": self.get_total_from_sku(state="Neu"),
                            "B": self.get_total_from_sku(state="B"), "C": self.get_total_from_sku(state="C"),
                            "D": self.get_total_from_sku(state="D"), "G": self.get_total_from_sku(state="G")
                            }
            if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
                total_from_ean = self.get_total_from_ean()
                if total_from_ean is not None:
                    return {"Gesamt": total_from_ean, "Neu": self.get_total_from_ean(state="Neu"),
                            "B": self.get_total_from_ean(state="B"), "C": self.get_total_from_ean(state="C"),
                            "D": self.get_total_from_ean(state="D"), "G": self.get_total_from_ean(state="G"),
                            }
            if self.title is not None and self.title != "":
                total_from_title = self.get_total_from_title()
                if total_from_title is not None:
                    return {"Gesamt": total_from_title, "Neu": self.get_total_from_title(state="Neu"),
                            "B": self.get_total_from_title(state="B"), "C": self.get_total_from_title(state="C"),
                            "D": self.get_total_from_title(state="D"), "G": self.get_total_from_title(state="G")
                            }

        total = self.get_total_from_all_products(product)

        return total

    def get_total_from_all_products(self, product):
        all_products = self.get_all_products(product)
        total = self.get_total(product=product)
        print(f"Syrien: {product.ean} - {total}")
        total = self.get_available_total_from_all_products(all_products, total)
        print(f"Marokko: {product.ean} - {total}")

        return total

    def get_total(self, product=None):

        if product is None:
            product = self.get_product()

        total = {}

        for state in self.states:
            total[state] = 0
        print(f"babfadbdfbd: {self.states}")

        all_products = self.get_all_products(product)

        if all_products is not None:
            for p in all_products:
                for sku in p.sku_set.all():
                    sku_string = sku.sku
                    sku_state = sku.state

                    if sku_state not in self.states:
                        self.states.append(sku_state)
                        total[sku_state] = 0

                    state_total = Stock.objects.filter(sku=sku_string).aggregate(Sum("bestand")).\
                        get("bestand__sum")

                    if state_total is not None:
                        if sku_state in total:
                            total[sku_state] += int(state_total)

        ean_stocks = None

        if product is not None:
            if product.ean is not None and product.ean != "":
                ean_stocks = Stock.objects.filter(ean_vollstaendig=product.ean)

        if ean_stocks is not None:
            for ean_stock in ean_stocks:
                if ean_stock.zustand in total:
                    total[ean_stock.zustand] += int(ean_stock.bestand)

        total["Gesamt"] = 0

        for state in self.states:
            total["Gesamt"] += total[state]

        return total

    def get_available_total_from_all_products(self, products, total):

        available_total = total.copy()

        if products is not None:
            for product in products:

                for sku in product.sku_set.all():
                    sku_string = sku.sku
                    sku_state = sku.state

                    if sku_state not in self.states:
                        self.states.append(sku_state)
                        total[sku_state] = 0

                    real_amount_total = PartialMissionProduct.objects\
                        .filter(product_mission__product__sku__sku=sku_string, product_mission__state=sku_state)\
                        .aggregate(Sum("amount")).get("amount__sum")

                    pick_list_total = 0

                    for pick_row in PickListProducts.objects.filter(product_mission__product__sku__sku=sku_string,
                                                                    product_mission__state=sku_state):
                        if pick_row.confirmed is not None and pick_row.confirmed != "":
                            pick_list_total += pick_row.amount_minus_missing_amount()

                    delivery_note_total = 0

                    for delivery_note_product in DeliveryNoteProductMission.objects\
                            .filter(product_mission__product__sku__sku=sku_string, product_mission__state=sku_state):
                        delivery_note_total += delivery_note_product.amount
                    print(f"blade {real_amount_total}")
                    if real_amount_total is not None and real_amount_total != "":
                        real_amount_total -= pick_list_total
                        available_total[sku_state] = f"{int(total[sku_state])-int(real_amount_total)}"
                        available_total[sku_state] = f"{int(available_total[sku_state])+int(delivery_note_total)}"

        available_total_gesamt = 0
        print(f"bandi: {self.states}")
        for state in self.states:
            total[state] = f"{available_total.get(state)}/{total.get(state)}"
            available_total_gesamt += int(available_total.get(state))

        total["Gesamt"] = f"{available_total_gesamt}/{total['Gesamt']}"

        return total

    def get_all_products(self, product):
        products = None
        if product is not None:
            if product.ean is not None and product.ean != "":
                products = Product.objects.filter(ean=product.ean)

        if product is not None and products is None:
            return [product]
        return products

    def get_product(self):
        product = None
        if self.sku is not None and self.sku != "":
            product = Product.objects.filter(sku__sku=self.sku).first()

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            product = Product.objects.filter(ean=self.ean_vollstaendig).first()
        return product

    def get_total_from_sku(self, state=None):
        if state is None:
            total = Stock.objects.filter(sku=self.sku).aggregate(Sum("bestand"))["bestand__sum"]
        else:
            sku = None
            sku_number = re.findall('\d+', self.sku)
            if len(sku_number) > 0:
                sku = sku_number[0]
            total = Stock.objects.filter(sku=f"{state}{sku}").aggregate(Sum("bestand"))["bestand__sum"]
        if total is None:
            return "0"
        else:
            return total

    def get_total_from_ean(self, state=None):
        if state is None:
            total = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig)\
                .aggregate(Sum("bestand"))["bestand__sum"]
        else:
            total = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=state)\
                .aggregate(Sum("bestand"))["bestand__sum"]

        if total is None:
            return "0"
        else:
            return total

    def get_total_from_title(self, state=None):
        if state is None:
            total = Stock.objects.filter(title=self.title).\
                aggregate(Sum("bestand"))["bestand__sum"]
        else:
            total = Stock.objects.filter(title=self.title, zustand=state)\
                .aggregate(Sum("bestand"))["bestand__sum"]

        if total is None:
            return "0"
        else:
            return total

    def get_total_from_product(self, product):

        result = {}
        all_skus = {}

        if product is not None:
            for sku in product.sku_set.all():
                all_skus[sku.sku] = sku

        for sku_string, sku_instance in all_skus.items():
            if sku_instance.state not in self.states:
                self.states.append(sku_instance.state)

            sku_total = Stock.objects.filter(sku=sku_string).aggregate(Sum("bestand")).get("bestand__sum")

            if sku_total is not None:
                result[sku_instance.state] = sku_total
            else:
                result[sku_instance.state] = "0"

        if product is not None:
            def add_ean_of_state_x_to_result(state, result):
                total_of_state = Stock.objects.filter(ean_vollstaendig=product.ean, zustand__iexact=state)\
                    .aggregate(Sum("bestand")).get("bestand__sum")

                if total_of_state is None:
                    total_of_state = 0

                if state in result:
                    result[state] = f'{int(result[state]) + int(total_of_state)}'
                else:
                    result[state] = total_of_state
                return result

            if product.ean is not None and product.ean != "":
                for state in self.states:
                    result = add_ean_of_state_x_to_result(state, result)

        total = 0
        for k, v in result.items():
            total += int(v)

        result["Gesamt"] = total
        return result

    def get_available_total_stocks(self, product=None):

        if self.product is not None:
            product = self.product

        if product is None or product == "":
            product = self.get_product()

        total = self.get_total(product=product)

        products = self.get_all_products(product)

        available_total = total.copy()

        if products is not None:
            for product in products:
                for sku in product.sku_set.all():
                    sku_string = sku.sku
                    sku_state = sku.state

                    if sku_state not in self.states:
                        self.states.append(sku_state)
                        total[sku_state] = 0

                    real_amount_total = PartialMissionProduct.objects.\
                        filter(product_mission__product__sku__sku=sku_string, product_mission__state=sku_state)\
                        .aggregate(Sum("amount")).get("amount__sum")

                    pick_list_total = 0

                    for pick_row in PickListProducts.objects.filter(product_mission__product__sku__sku=sku_string,
                                                                    product_mission__state=sku_state):
                        if pick_row.confirmed is not None and pick_row.confirmed != "":
                            pick_list_total += pick_row.amount_minus_missing_amount()

                    delivery_note_total = 0

                    for delivery_note_product in DeliveryNoteProductMission.objects\
                            .filter(product_mission__product__sku__sku=sku_string, product_mission__state=sku_state):
                        delivery_note_total += delivery_note_product.amount

                    if real_amount_total is not None and real_amount_total != "":
                        real_amount_total -= pick_list_total
                        if sku_state not in self.states:
                            total[sku_state] = 0
                        available_total[sku_state] = f"{int(total[sku_state])-int(real_amount_total)}"
                        available_total[sku_state] = f"{int(available_total[sku_state])+int(delivery_note_total)}"

                        # total["Gesamt"] -= f"{int(total['Gesamt'])}"

        available_total_gesamt = 0

        for state in self.states:
            available_total_gesamt += int(available_total.get(state))

        available_total["Gesamt"] = f"{available_total_gesamt}"

        return available_total

    def get_reserved_stocks(self):

        available_stocks = self.get_available_total_stocks()
        total_stocks = self.get_total()

        print(f"bababa: {available_stocks}")
        print(f"rafael: {total_stocks}")
        reserved_stocks = {}

        for state in self.states:
            reserved_stocks[state] = int(total_stocks.get(state))-int(available_stocks.get(state))
        reserved_stocks["Gesamt"] = int(total_stocks.get("Gesamt")) - int(available_stocks.get("Gesamt"))

        return reserved_stocks

    def get_available_stocks_of_total_stocks(self, product=None):
        total_stocks = self.get_total_stocks(product=product)
        return total_stocks

    def available_total_amount(self, state=None):
        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            if state is not None:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig), zustand__iexact=state).\
                    aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig)).aggregate(Sum('bestand'))

            real_amounts = PartialMissionProduct.objects.filter(product_mission__product__ean=self.ean_vollstaendig)
            total_reserved = 0
            for real_amount in real_amounts:
                total_reserved += real_amount.real_amount

            total["bestand__sum"] -= total_reserved

        elif self.sku is not None and self.sku != "":
            if state is not None:
                total = Stock.objects.filter(sku=str(self.sku), zustand__iexact=state).aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(sku=str(self.sku)).aggregate(Sum('bestand'))
        elif self.title is not None and self.title != "":
            if state is not None:
                total = Stock.objects.filter(title=str(self.title), zustand__iexact=state).aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(title=str(self.title)).aggregate(Sum('bestand'))
            real_amounts = PartialMissionProduct.objects.filter(product_mission__product__title=self.title)
            total_reserved = 0
            for real_amount in real_amounts:
                total_reserved += real_amount.real_amount

            total["bestand__sum"] -= total_reserved
        else:
            return None
        total = {"bestand__sum": total["bestand__sum"]}

        return total["bestand__sum"]

    def get_state(self):
        if self.zustand is not None and self.zustand != "":
            return self.zustand

        if self.product is not None:
            return self.product.get_state_from_sku(self.sku)


class Stockdocument(models.Model):
    document = models.FileField(upload_to='documents/', null=True, blank=False)
    uploaded_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("stock:documentdetail", kwargs={"pk": self.id})


class Position(models.Model):

    prefix = models.CharField(blank=True, null=False, max_length=250, verbose_name="Prefix")
    shelf = models.IntegerField(blank=True, null=False, verbose_name="Regal")
    level = models.IntegerField(blank=True, null=False, verbose_name="Ebene")
    column = models.IntegerField(blank=True, null=False, verbose_name="Spalte")

    def __str__(self):
        return self.position

    @property
    def position(self):
        if str(self.level).isdigit():
            level = '%03d' % (int(self.level),)
        else:
            level = self.level
        if str(self.column).isdigit():
            column = '%03d' % (int(self.column),)
        else:
            column = self.column

        position = f"{self.prefix}{self.shelf}-{level}-{column}"

        if all(char.isalpha() or char.isspace() or char == "-" for char in position):
            return self.prefix

        return position

    class Meta:
           ordering = ["prefix", "shelf", "level", "column"]
