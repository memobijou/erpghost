from django.db import models
import datetime
from django.utils import timezone
from django.core.urlresolvers import reverse
from product.models import Product
from invoice.models import Invoice
from supplier.models import Supplier
from django.core.exceptions import ValidationError
from position.models import Position
from picklist.models import Picklist
from datetime import date


# Create your models here.

terms_of_payment_choices = [
    ("Innerhalb 30 Tage netto, ohne Abzug", "Innerhalb 30 Tage netto, ohne Abzug"),
    ("Sofort nach Erhalt, ohne Abzug", "Sofort nach Erhalt, ohne Abzug"),
    ("Innerhalb 14 Tage netto, ohne Abzug", "Innerhalb 14 Tage netto, ohne Abzug"),
    ("30 Tage netto, 14 Tage 3% Skonto", "30 Tage netto, 14 Tage 3% Skonto"),
    ("7 Tage netto", "7 Tage netto"),
    ("Vorkasse", "Vorkasse"),
    ("innerhalb 45 Tage 3% Skonto", "innerhalb 45 Tage 3% Skonto"),
    ("innerhalb 60 Tagen, ohne Abzug", "innerhalb 60 Tagen, ohne Abzug"),
    ("innerhalb 21 Tage, ohne Abzug", "innerhalb 21 Tage, ohne Abzug"),
    ("15 Tage 3% Skonto, 45 Tage Valuta", "15 Tage 3% Skonto, 45 Tage Valuta"),
    ("innerhalb 90 Tage, ohne Abzug", "innerhalb 90 Tage, ohne Abzug"),
    ("10 Tage netto", "10 Tage netto"),
]

terms_of_delivery_choices = [
    ("DDP - Frei Haus verzollt", "DDP - Frei Haus verzollt"),
    ("CIF - Frei Haus", "CIF - Frei Haus"),
    ("CIP - Frei Haus", "CIP - Frei Haus"),
    ("EXW - Ab Werk", "EXW - Ab Werk"),
]


class Order(models.Model):
    ordernumber = models.CharField(max_length=13, blank=True, verbose_name="Bestellnummer")
    delivery_date = models.DateField(default=datetime.date.today, verbose_name="Lieferdatum")
    status = models.CharField(max_length=25, null=True, blank=True, default="OFFEN", verbose_name="Status")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, related_name='order', verbose_name="Lieferant")
    products = models.ManyToManyField(Product, through="ProductOrder")
    invoice = models.ManyToManyField(Invoice, through="InvoiceOrder")
    terms_of_payment = models.CharField(choices=terms_of_payment_choices, blank=True, null=True, max_length=200,
                                        verbose_name="Zahlungsbedingung")
    terms_of_delivery = models.CharField(choices=terms_of_delivery_choices, blank=True, null=True, max_length=200,
                                         verbose_name="Lieferkonditionen")

    created_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    modified_date = models.DateTimeField(auto_now=True, null=True, blank=True)

    CHOICES = (
        (None, "----"),
        (True, "Ja"),
        (False, "Nein")
    )
    verified = models.NullBooleanField(choices=CHOICES, verbose_name="Akzeptiert")

    def __str__(self):
        return self.ordernumber

    def get_absolute_url(self):
        return reverse("order:detail", kwargs={"pk": self.id})

    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        self.__original_verified = self.verified

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.__original_verified != self.verified:
            if self.verified is True:
                # name changed - do something here
                self.status = "AKZEPTIERT"
            elif self.verified is False:
                self.status = "ABGELEHNT"

        if self.ordernumber == "":
            today = date.today().strftime('%d%m%y')
            count = Order.objects.filter(ordernumber__icontains=today).count()+1
            self.ordernumber = f"B{today}-{count}"
        super().save(force_insert=False, force_update=False, *args, **kwargs)


class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="Artikel")
    order = models.ForeignKey(Order, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    amount = models.IntegerField(null=False, blank=False, default=0, verbose_name="Menge")
    missing_amount = models.IntegerField(null=True, blank=True, verbose_name="Fehlende Menge")
    netto_price = models.FloatField(null=True, blank=True, verbose_name="Einzelpreis (Netto)")
    confirmed = models.NullBooleanField(verbose_name="Bestätigt")

    def __str__(self):
        return str(self.product) + " : " + str(self.order) + " : " + str(self.amount)

    def save(self, *args, **kwargs):
        product_orders = self.order.productorder_set.all()
        all_scanned = True
        if self.confirmed == "1" or self.confirmed == "0":
            self.order.status = "WARENEINGANG"
        else:
            all_scanned = False
        for product_order in product_orders:
            if self.id != product_order.id:
                if product_order.confirmed is True or product_order.confirmed is False:
                    self.order.status = "WARENEINGANG"
                else:
                    all_scanned = False
        if all_scanned and product_orders.exists():
            self.order.status = "POSITIONIEREN"
        self.order.save()
        super(ProductOrder, self).save(*args, **kwargs)

    @property
    def real_amount(self):
        if self.amount and self.missing_amount:
            return self.amount - self.missing_amount
        else:
            return self.amount  #


class InvoiceOrder(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, unique=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    datum = models.CharField(max_length=13)
    extra_text = models.CharField(max_length=13)
    terms_of_payment = models.CharField(max_length=13)

    class Meta:
        unique_together = ('invoice', 'order',)

    def __str__(self):
        return str(self.invoice) + ":" + str(self.order)


class PositionProductOrder(models.Model):
    amount = models.IntegerField(null=False, blank=False, default=0)
    positions = models.ForeignKey(Position, on_delete=models.CASCADE,blank=True, null=True)
    CHOICES = (
        (None, "----"),
        (True, "Position"),
        (False, "WE")
    )
    status = models.NullBooleanField(choices=CHOICES)

    def __str__(self):
        return str(self.productorder) + " : " + str(self.amount) + " : " + str(self.positions) + " : " + str(self.status)


class PositionProductOrderPicklist(models.Model):
    positionproductorder = models.ForeignKey(PositionProductOrder, on_delete=models.CASCADE,blank=True, null=True,related_name='positionsproduct')
    picklist = models.ForeignKey(Picklist, on_delete=models.CASCADE, blank=True, null=True,related_name='artikeln')
    comment = models.CharField(max_length=13)
    pickerid = models.CharField(max_length=13)
    belegt = models.NullBooleanField()

    def __str__(self):
        return str(self.positionproductorder) + " : " + str(self.picklist) + " : " + str(self.comment) + " : " + str(self.pickerid)

    def __unicode__(self):
        return '%d: %s' % (self.picklist, self.positionproductorder)