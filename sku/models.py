from django.db import models
from django.db.models import Q
from django.db.models import Sum, OuterRef, Case, When, F, Subquery
from django.db.models.functions import Coalesce


class SkuQuerySet(models.QuerySet):
    def get_totals(self):
        from product.models import Product
        from stock.models import Stock

        online_total_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            online_total=Sum(Case(When(product__productmission__product=F("product"),
                                       product__productmission__state=F("state"),
                                       product__productmission__mission__is_online=True,
                                       product__productmission__mission__online_picklist__completed__isnull=True,
                                       then="product__productmission__amount"), default=0)))[:1]

        wholesale_total_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            wholesale_total=Sum(
                Case(When(Q(product__productmission__partialmissionproduct__product_mission__state=F("state"),
                          product__productmission__partialmissionproduct__product_mission__product=F("product")),
                          then="product__productmission__partialmissionproduct__amount"),
                     default=0)))[:1]

        wholesale_picklists_total_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            wholesale_picklist_total=Sum(
                Case(When(product__productmission__product=F("product"),
                          product__productmission__state=F("state"),
                          product__productmission__picklistproducts__pick_list__isnull=False,
                          product__productmission__picklistproducts__confirmed=True,
                          product__productmission__mission__is_online__isnull=True,
                          then="product__productmission__picklistproducts__amount"), default=0))
        )[:1]

        wholesale_total_booked_out = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            wholesale_booked_out_total=Sum(Case(When(
                Q(product__productmission__state=F("state"),
                  product__productmission__product=F("product"),
                  product__productmission__mission__is_online__isnull=True
                ),
                then=F("product__productmission__deliverynoteproductmission__amount")),
                                                default=0)))[:1]

        return self.all().annotate(
            total=Sum(Coalesce("stock__bestand", 0))).annotate(
            online_total=Coalesce(Subquery(online_total_subquery.values("online_total"),
                                           output_field=models.IntegerField()), 0),
            wholesale_total=Coalesce(Subquery(wholesale_total_subquery.values("wholesale_total"),
                                     output_field=models.IntegerField()), 0),
            wholesale_picklist_total=Coalesce(
                Subquery(wholesale_picklists_total_subquery.values("wholesale_picklist_total"),
                         output_field=models.IntegerField()), 0),
            wholesale_total_booked_out=Coalesce(
                Subquery(wholesale_total_booked_out.values("wholesale_booked_out_total"),
                         output_field=models.IntegerField()), 0),).annotate(
            wholesale_total=F("wholesale_total")-F("wholesale_total_booked_out")-F("wholesale_picklist_total"),
            available_total=F("total") - F("online_total") - F("wholesale_total")
        )


class CustomManger(models.Manager):
    def get_queryset(self):
        return SkuQuerySet(self.model, using=self._db)  # Important!


class SkuObjectManager(CustomManger):
    pass


class Sku(models.Model):
    objects = SkuObjectManager()

    sku = models.CharField(max_length=200, null=True, blank=True, verbose_name="SKU")
    state = models.CharField(blank=True, null=True, max_length=200, verbose_name="Zustand")
    purchasing_price = models.FloatField(null=True, blank=True, verbose_name="Einkaufspreis")
    main_sku = models.NullBooleanField(blank=True, verbose_name="Haupt-SKU")
    product = models.ForeignKey("product.Product", null=True, blank=True)

    def __str__(self):
        return str(self.sku)
