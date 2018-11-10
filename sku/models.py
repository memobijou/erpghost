from django.db import models
from django.db.models import Q
from django.db.models import Sum, OuterRef, Case, When, F, Subquery
from django.db.models.functions import Coalesce
import datetime
from django.db.models import Func

from online.models import Offer


class SkuQuerySet(models.QuerySet):
    def get_totals(self):
        from product.models import Product
        from stock.models import Stock

        online_total_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            online_total=Sum(Case(When(productmission__sku__sku=F("sku"),
                                       productmission__mission__is_online=True,
                                       productmission__mission__online_picklist__completed__isnull=True,
                                       then="productmission__amount"), default=0))).annotate()[:1]

        delta_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            delta=Case(When(productmission__mission__delivery_date_to__isnull=False,
                            then=Func((F('productmission__mission__delivery_date_to') - datetime.date.today()),
                                      function='ABS')), default=None, output_field=models.IntegerField())
        )[:1]

        wholesale_total_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            wholesale_total=Sum(
                Case(When(Q(productmission__partialmissionproduct__product_mission__sku__sku=F("sku")),
                          then="productmission__partialmissionproduct__amount"),
                     default=0)))[:1]

        wholesale_picklists_total_subquery = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            wholesale_picklist_total=Sum(
                Case(When(productmission__sku__sku=F("sku"),
                          productmission__picklistproducts__pick_list__isnull=False,
                          productmission__picklistproducts__confirmed=True,
                          productmission__mission__is_online__isnull=True,
                          then="productmission__picklistproducts__amount"), default=0))
        )[:1]

        wholesale_total_booked_out = Sku.objects.filter(pk=OuterRef("pk")).annotate(
            wholesale_booked_out_total=Sum(Case(When(
                Q(productmission__sku__sku=F("sku"),
                  productmission__mission__is_online__isnull=True),
                then=F("productmission__deliverynoteproductmission__amount")),
                                                default=0)))[:1]
        return self.all().annotate(
            delta=Coalesce(Subquery(delta_subquery.values("delta")), None)).annotate(
            offer_total=Coalesce(Sum("offer__amount"), 0)
        ).annotate(
            total=Sum(Coalesce("stock__bestand", 0)),
            online_total=Case(When(delta__isnull=False, delta__lte=10, then=Subquery(
                online_total_subquery.values("online_total"),
                output_field=models.IntegerField())), default=0),
            wholesale_total=Coalesce(Subquery(wholesale_total_subquery.values("wholesale_total"),
                                     output_field=models.IntegerField()), 0),
            wholesale_picklist_total=Coalesce(
                Subquery(wholesale_picklists_total_subquery.values("wholesale_picklist_total"),
                         output_field=models.IntegerField()), 0),
            wholesale_total_booked_out=Coalesce(
                Subquery(wholesale_total_booked_out.values("wholesale_booked_out_total"),
                         output_field=models.IntegerField()), 0),).annotate(
            wholesale_total=F("wholesale_total")-F("wholesale_total_booked_out")-F("wholesale_picklist_total"),
            available_total=F("total")-F("offer_total")-F("online_total")-F("wholesale_total")
        )


class CustomManger(models.Manager):
    def get_queryset(self):
        return SkuQuerySet(self.model, using=self._db)  # Important!


class SkuObjectManager(CustomManger):
    pass


class Sku(models.Model):
    objects = SkuObjectManager()

    sku = models.CharField(max_length=200, null=True, blank=True, verbose_name="SKU")
    state = models.CharField(blank=False, null=True, max_length=200, verbose_name="Zustand")
    purchasing_price = models.FloatField(null=True, blank=True, verbose_name="Einkaufspreis")
    main_sku = models.NullBooleanField(blank=True, verbose_name="Haupt-SKU")
    product = models.ForeignKey("product.Product", null=True, blank=True)
    channel = models.ForeignKey("online.Channel", null=True, blank=False)
    asin = models.CharField(max_length=200, null=True, blank=True, verbose_name="ASIN")

    def __str__(self):
        return str(self.sku)

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.main_sku is not True and hasattr(self, "offer") is False:
            new_offer = Offer()
            new_offer.save()
            self.offer = new_offer
        super().save()
