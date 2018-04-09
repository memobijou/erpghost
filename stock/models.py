from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.template import Context, Template


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
        if self.zustand.lower() == "neu" or self.zustand.lower() == "a":
            if self.ean_vollstaendig is None or self.ean_vollstaendig == "":
                stock_html = "<h1 style='color:red;'>Sie müssen eine EAN angeben</h1>"
                c = Context({'unique_message': 'Your message'})
                raise ValidationError(Template(stock_html).render(c))
        if self.zustand.lower() in ["b", "c", "d", "e"]:
            if self.ean_vollstaendig is not None:
                stocks = Stock.objects.filter(ean_vollstaendig=self.ean_vollstaendig, zustand=self.zustand,
                                              lagerplatz=self.lagerplatz, title=self.title).exclude(id=self.id)
            else:
                if (self.sku is None or self.sku == "") and (self.title is None or self.title == ""):
                    stock_html = "<h1 style='color:red;'>Sie müssen eine SKU oder Artikelnamen angeben</h1>"
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

    def total_amount_ean(self):
        if self.ean_vollstaendig is not None and self.ean_vollstaendig != "":
            total = Stock.objects.filter(ean_vollstaendig=str(self.ean_vollstaendig)).aggregate(Sum('bestand'))
        elif (self.sku is not None and self.sku != "") or (self.title is not None and self.title != ""):
            total = Stock.objects.filter(sku=self.sku, title=self.title).aggregate(Sum('bestand'))
        else:
            return "/"
        print("?!?!: " + str(total))
        total = {"bestand__sum": total["bestand__sum"]}
        return total["bestand__sum"]


class Stockdocument(models.Model):
    document = models.FileField(upload_to='documents/', null=True, blank=False)
    uploaded_at = models.DateTimeField(auto_now=True)

    def get_absolute_url(self):
        return reverse("stock:documentdetail", kwargs={"pk": self.id})
