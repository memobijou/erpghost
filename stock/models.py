from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.template import Context, Template
import re

from mission.models import RealAmount
from product.models import Product


class Stock(models.Model):
    IGNORE_CHOICES = (
        ('IGNORE', 'Ja'),
        ('NOT_IGNORE', 'Nein'),
    )

    ean_vollstaendig = models.CharField(max_length=250, verbose_name="EAN", null=True, blank=True)
    bestand = models.IntegerField(null=True, blank=True, verbose_name="Bestand")
    ean_upc = models.CharField(max_length=250, null=True, blank=True)
    lagerplatz = models.CharField(max_length=250, null=True, blank=True, verbose_name="Lagerplatz")
    regal = models.CharField(max_length=250, null=True, blank=True, verbose_name="Regal")
    zustand = models.CharField(max_length=250, null=True, blank=True, verbose_name="Zustand")
    scanner = models.IntegerField(null=True, blank=True, verbose_name="Scanner")
    name = models.CharField(max_length=250, null=True, blank=True, verbose_name="Person")
    karton = models.CharField(max_length=250, null=True, blank=True, verbose_name="Karton")
    box = models.CharField(max_length=250, null=True, blank=True, verbose_name="Box")
    aufnahme_datum = models.CharField(max_length=250, null=True, blank=True, verbose_name="Aufnahme Datum")
    ignore_unique = models.CharField(max_length=250, null=True, blank=True, choices=IGNORE_CHOICES,
                                     verbose_name="Block")
    title = models.CharField(max_length=250, verbose_name="Artikelname", null=True, blank=True)
    sku = models.CharField(max_length=250, verbose_name="Sku", null=True, blank=True)

    def get_absolute_url(self):
        return reverse("stock:detail", kwargs={'pk': self.id})

    def __str__(self):
        return str(self.ean_vollstaendig)

    def clean(self):

        if self.lagerplatz is None:
            return

        has_ean = self.ean_vollstaendig is not None and self.ean_vollstaendig != ""
        has_sku = self.sku is not None and self.sku != ""
        has_title = self.title is not None and self.title != ""

        if has_ean is True and has_sku is True or has_sku is True and has_title is True or has_ean is True\
                and has_title is True:
            only_ean_or_sku_or_title_html =\
                "<h3 style='color:red;'>Sie dürfen nur eine Angabe machen: EAN, Sku oder Artikelname</h3>"
            c = Context({'unique_message': 'Your message'})
            raise ValidationError(Template(only_ean_or_sku_or_title_html).render(c))

        if self.zustand.lower() == "neu" or self.zustand.lower() == "a":
            if self.ean_vollstaendig is None or self.ean_vollstaendig == "":
                stock_html = "<h3 style='color:red;'>Sie müssen eine EAN angeben</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))
        if self.zustand.lower() in ["b", "c", "d", "e"]:
            if self.ean_vollstaendig is not None:
                stocks = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand,
                                              lagerplatz=self.lagerplatz, title=self.title).exclude(id=self.id)
            else:
                if (self.sku is None or self.sku == "") and (self.title is None or self.title == ""):
                    stock_html = "<h3 style='color:red;'>Sie müssen entweder eine SKU oder einen Artikelnamen angeben</h3>"
                    c = Context({'unique_message': 'Your message'})
                    raise ValidationError(Template(stock_html).render(c))
                stocks = Stock.objects.filter(sku=self.sku, zustand=self.zustand,
                                              lagerplatz=self.lagerplatz, title=self.title).exclude(id=self.id)
        else:
            stocks = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand,
                                          lagerplatz=self.lagerplatz).exclude(id=self.id)

        if stocks is not None and stocks.count() > 0:
            stock_html = "<h1 style='color:red;'>Lagerbestand schon vorhanden</h1>" \
                         "<table class='table table-bordered'>" \
                         "<thead>" \
                         "<tr>" \
                         "<th></th><th>EAN</th><th>Lagerplatz</th><th>Zustand</th><th>IST Bestand</th>"\
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
                                          f"<td>{stock_ean}</td>" \
                                          f"<td>{stock.lagerplatz}</td>" \
                                          f"<td>{stock.zustand}</td>" \
                                          f"<td>{stock_bestand}</td>" \
                                          f"</tr>"
            stock_html += "</tbody></table>"
            c = Context({'unique_message': 'Your message'})
            raise ValidationError(Template(stock_html).render(c))

    def total_amount_ean(self, state=None):
        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            if state is not None:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig), zustand__iexact=state).\
                    aggregate(Sum('bestand'))["bestand__sum"]

                if total is None:
                    total = 0

                product = Product.objects.filter(ean=str(self.ean_vollstaendig)).first()
                total = self.add_skus_to_total(state, total, product)

            else:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig))\
                    .aggregate(Sum('bestand'))["bestand__sum"]

                if total is None:
                    total = 0

                product = Product.objects.filter(ean=str(self.ean_vollstaendig)).first()
                total = self.add_skus_to_total(state, total, product)
        elif self.sku is not None and self.sku != "":
            total = self.get_total_from_sku()
        elif self.title is not None and self.title != "":
            if state is not None:
                total = Stock.objects.filter(title=str(self.title))\
                    .aggregate(Sum('bestand'))["bestand__sum"]
            else:
                total = Stock.objects.filter(title=str(self.title)).aggregate(Sum('bestand'))["bestand__sum"]
        else:
            return None
        return total

    def get_total_stocks(self):
        product = None

        if self.sku is not None and self.sku != "":
            product = Product.objects.filter(sku__sku=self.sku).first()
            total = self.get_total_from_product(product)
            return total

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            product = Product.objects.filter(ean=self.ean_vollstaendig).first()
            total = self.get_total_from_product(product)
            return total

        if product is None:
            total_from_sku = self.get_total_from_sku()
            if total_from_sku is not None:
                return {"Gesamt": total_from_sku}

            total_from_ean = self.get_total_from_ean()
            if total_from_ean is not None:
                return {"Gesamt": total_from_ean}

    def get_total_from_sku(self):
        total = Stock.objects.filter(sku=self.sku).aggregate(Sum("bestand"))["bestand__sum"]
        return total

    def get_total_from_ean(self):
        total = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig).aggregate(Sum("bestand"))["bestand__sum"]
        return total

    def get_total_from_product(self, product):
        result = {}
        all_skus = {}

        if product is not None:
            for sku in product.sku_set.all():
                all_skus[sku.sku] = sku
        print(all_skus)

        for sku_string, sku_instance in all_skus.items():
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
                result = add_ean_of_state_x_to_result("Neu", result)
                result = add_ean_of_state_x_to_result("A", result)
                result = add_ean_of_state_x_to_result("B", result)
                result = add_ean_of_state_x_to_result("C", result)
                result = add_ean_of_state_x_to_result("D", result)

        total = 0
        print(result)
        for k, v in result.items():
            total += int(v)

        result["Gesamt"] = total
        print(result)
        return result

    def available_total_amount(self, state=None):
        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            if state is not None:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig), zustand__iexact=state).\
                    aggregate(Sum('bestand'))
            else:
                total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig)).aggregate(Sum('bestand'))

            real_amounts = RealAmount.objects.filter(product_mission__product__ean=self.ean_vollstaendig)
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
            real_amounts = RealAmount.objects.filter(product_mission__product__title=self.title)
            total_reserved = 0
            for real_amount in real_amounts:
                total_reserved += real_amount.real_amount

            total["bestand__sum"] -= total_reserved
        else:
            return None
        print("?!?!: " + str(total))
        total = {"bestand__sum": total["bestand__sum"]}

        return total["bestand__sum"]


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