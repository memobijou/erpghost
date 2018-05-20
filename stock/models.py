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
        print(f"HEROKU:::: {self.lagerplatz} --- {self.sku} --- {self.zustand}")
        has_ean = self.ean_vollstaendig is not None and self.ean_vollstaendig != ""
        has_sku = self.sku is not None and self.sku != ""
        has_title = self.title is not None and self.title != ""

        if has_ean is True and has_sku is True or has_sku is True and has_title is True or has_ean is True\
                and has_title is True:
            only_ean_or_sku_or_title_html =\
                "<h3 style='color:red;'>Sie dürfen nur eine Angabe machen: EAN, Sku oder Artikelname</h3>"
            c = Context({'unique_message': 'Your message'})
            raise ValidationError(Template(only_ean_or_sku_or_title_html).render(c))

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            if self.zustand is None or self.zustand == "":
                stock_html = "<h3 style='color:red;'>Wenn Sie eine EAN eingeben, müssen Sie einen Zustand" \
                             " bestimmen.</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))

        if self.title is not None and self.title != "":
            if self.zustand is None or self.zustand == "":
                stock_html = "<h3 style='color:red;'>Wenn Sie einen Artikelnamen eingeben, müssen Sie einen Zustand" \
                             " bestimmen.</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))
        if self.zustand is not None and self.zustand != "":
            if self.zustand.lower() == "neu" or self.zustand.lower() == "a":
                if self.ean_vollstaendig is None or self.ean_vollstaendig == "":
                    stock_html = "<h3 style='color:red;'>Sie müssen eine EAN angeben</h3>"
                    c = Context({'unique_message': 'Your message'})
                    raise ValidationError(Template(stock_html).render(c))

            if self.zustand.lower() in ["b", "c", "d", "e"]:
                if (self.sku is None or self.sku == "") and (self.title is None or self.title == ""):
                    stock_html =\
                        "<h3 style='color:red;'>Sie müssen entweder eine SKU oder einen Artikelnamen angeben</h3>"
                    c = Context({'unique_message': 'Your message'})
                    raise ValidationError(Template(stock_html).render(c))
                else:
                    if self.sku is not None and self.sku != "":
                        if self.zustand is not None:
                            stock_html = \
                                "<h3 style='color:red;'>Wenn Sie eine SKU angeben dürfen Sie keinen Zustand auswählen" \
                                "</h3>"
                            c = Context({'unique_message': 'Your message'})
                            raise ValidationError(Template(stock_html).render(c))

        stocks = None

        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            stocks = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand,
                                          lagerplatz=self.lagerplatz).exclude(id=self.id)
        elif self.sku is not None and self.sku != "":
            if Product.objects.filter(sku__sku__exact=self.sku).count() == 0:
                stock_html = \
                    f"<h3 style='color:red;'>Bitte geben Sie eine gültige SKU ein. " \
                    f"die SKU {self.sku} existiert nicht im System." \
                    f"</h3>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))

            stocks = Stock.objects.filter(sku=self.sku, zustand=self.zustand,
                                          lagerplatz=self.lagerplatz).exclude(id=self.id)
        elif self.title is not None and self.title != "":
            stocks = Stock.objects.filter(title=self.title, zustand=self.zustand,
                                          lagerplatz=self.lagerplatz).exclude(id=self.id)

        if stocks is not None and stocks.count() > 0:
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
                                          f"<td>{stock_ean}</td>" \
                                          f"<td>{stock.sku}</td>" \
                                          f"<td>{stock.lagerplatz}</td>" \
                                          f"<td>{stock.zustand}</td>" \
                                          f"<td>{stock_bestand}</td>" \
                                          f"</tr>"
            stock_html += "</tbody></table></div>"
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
        product = self.get_product()

        if product is None:
            if self.sku is not None and self.sku != "":
                total_from_sku = self.get_total_from_sku()
                if total_from_sku is not None:
                    return {"Gesamt": total_from_sku, "Neu": self.get_total_from_sku(state="Neu"),
                            "A": self.get_total_from_sku(state="A"), "B": self.get_total_from_sku(state="B"),
                            "C": self.get_total_from_sku(state="C"), "D": self.get_total_from_sku(state="D"),
                            }
            if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
                total_from_ean = self.get_total_from_ean()
                if total_from_ean is not None:
                    return {"Gesamt": total_from_ean, "Neu": self.get_total_from_ean(state="Neu"),
                            "A": self.get_total_from_ean(state="A"), "B": self.get_total_from_ean(state="B"),
                            "C": self.get_total_from_ean(state="C"), "D": self.get_total_from_ean(state="D"),
                            }
            if self.title is not None and self.title != "":
                total_from_title = self.get_total_from_title()
                if total_from_title is not None:
                    return {"Gesamt": total_from_title, "Neu": self.get_total_from_title(state="Neu"),
                            "A": self.get_total_from_title(state="A"), "B": self.get_total_from_title(state="B"),
                            "C": self.get_total_from_title(state="C"), "D": self.get_total_from_title(state="D"),
                            }
        total = self.get_total_from_product(product)
        return total

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
        return total

    def get_total_from_product(self, product):
        result = {}
        all_skus = {}

        if product is not None:
            for sku in product.sku_set.all():
                all_skus[sku.sku] = sku

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
        for k, v in result.items():
            total += int(v)

        result["Gesamt"] = total
        return result

    def get_available_total_stocks(self):
        stocks = self.get_total_stocks()
        print(f"KRANK: {stocks}")
        available_stocks = {}
        states = ["Neu", "A", "B", "C", "D"]

        for state, total in stocks.items():
            print(f"SOLL: {state}  ---  {states}")

            real_amounts = None
            if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
                if state in states:
                    real_amounts = RealAmount.objects.filter(product_mission__product__ean=self.ean_vollstaendig,
                                                             product_mission__state__exact=state)
                else:
                    real_amounts = RealAmount.objects.filter(product_mission__product__ean=self.ean_vollstaendig)

            elif self.sku is not None and self.sku != "":
                print(f"hare: {self.sku}")
                if state in states:
                    real_amounts = RealAmount.objects.filter(product_mission__product__sku__sku=self.sku,
                                                             product_mission__state=state)
                else:
                    real_amounts = RealAmount.objects.filter(product_mission__product__sku__sku=self.sku)

            total_reserved = 0
            if real_amounts is not None:
                for real_amount in real_amounts:
                    total_reserved += real_amount.real_amount
                if total is not None:
                    if state in states:
                        print(f"battaaa: {total} ... {total_reserved}")
                        available_stocks[state] = str(int(total)-total_reserved)
                    else:
                        available_stocks["Gesamt"] = str(int(stocks.get("Gesamt"))-total_reserved)
                else:
                    available_stocks[state] = total
        print(f"AVAILABLE:::: {available_stocks}")
        return available_stocks

    def get_available_stocks_of_total_stocks(self):
        result = {}
        total_stocks = self.get_total_stocks()
        available_stocks = self.get_available_total_stocks()
        for state, total in total_stocks.items():
            result[state] = f"{available_stocks.get(state)}/{total}"
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