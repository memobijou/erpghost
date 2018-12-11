from django.db import models
from django.db.models.query import ValuesIterable

from sku.models import Sku
from supplier.models import Supplier
from django.urls import reverse
from django.db.models import Max
from collections import OrderedDict


class Manufacturer(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Hersteller")


class Brand(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Markenname")


class ProductQuerySet(models.QuerySet):
    def values_as_instances(self, *fields, **expressions):
        clone = self._clone()
        if expressions:
            clone = clone.annotate(**expressions)
        clone._fields = fields
        return clone


class CustomManger(models.Manager):
    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)  # Important!


class ProductObjectManager(CustomManger):
    def table_list(self):

        return self.all()


class Product(models.Model):
    class Meta:
        ordering = ["-pk"]

    main_image = models.ImageField(verbose_name="Bild", null=True, blank=True)

    ean = models.CharField(blank=True, null=False, max_length=200, verbose_name="EAN")
    main_sku = models.IntegerField(blank=True, null=True, verbose_name="SKU")
    title = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Artikelname")
    manufacturer = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Hersteller")
    brandname = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Markenname")
    part_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Herstellernummer")

    short_description = models.TextField(null=True, blank=True, default="", verbose_name="Kurzbeschreibung")
    description = models.TextField(null=True, blank=True, default="", verbose_name="Beschreibung")

    single_product = models.NullBooleanField(verbose_name="Einzelartikel")

    height = models.FloatField(null=True, blank=True, default=None, verbose_name="Höhe")
    width = models.FloatField(null=True, blank=True, default=None, verbose_name="Breite")
    length = models.FloatField(null=True, blank=True, default=None, verbose_name="Länge")

    packing_unit = models.IntegerField(null=True, blank=True, default=1, verbose_name="Verpackungseinheit")

    packing_unit_parent = models.ForeignKey("product.Product", related_name="packing_unit_child", null=True,
                                            blank=True)

    objects = ProductObjectManager()

    def __str__(self):
        return f"{self.ean}"

    @property
    def calc_volume(self):
        if self.height and self.width and self.length:
            return self.height * self.width * self.length

    def get_absolute_url(self):
        return reverse("product:detail", kwargs={"pk": self.id})

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super().save()
        generate_skus = False

        if self.main_sku is None or self.main_sku == "":
            generate_skus = True
            self.main_sku = int(self.pk+1)

        super().save()

        if generate_skus is True:
            bulk_instances = [Sku(product_id=self.pk, sku=f"N{self.main_sku}", state="Neu", main_sku=True),
                              Sku(product_id=self.pk, sku=f"G{self.main_sku}", state="G", main_sku=True),
                              Sku(product_id=self.pk, sku=f"B{self.main_sku}", state="B", main_sku=True),
                              Sku(product_id=self.pk, sku=f"C{self.main_sku}", state="C", main_sku=True),
                              Sku(product_id=self.pk, sku=f"D{self.main_sku}", state="D", main_sku=True)]
            Sku.objects.bulk_create(bulk_instances)
        else:
            skus = self.sku_set.all()

            for sku in skus:
                if sku.sku.endswith(str(self.main_sku)) is True:
                    sku.main_sku = True
                    sku.save()

            sku_states = [sku.state for sku in skus]
            states = ["Neu", "G", "B", "C", "D"]

            for state in states:
                if state not in sku_states:

                    if state == "Neu":
                        prefix = "N"
                    else:
                        prefix = state

                    sku_instance = Sku(product_id=self.pk, sku=f"{prefix}{self.main_sku}", state=state, main_sku=True)
                    sku_instance.save()

    def get_state_from_sku(self, sku):
        if sku is not None and sku != "":
            for product_sku in self.sku_set.all():
                if product_sku.sku == sku:
                    return product_sku.state

    def get_sku_from_state(self, state):
        if state is not None and state != "":
            return self.sku_set.filter(state=state).first()


def get_states_totals_and_total(product, skus):
    total = {"total": 0, "available_total": 0}
    states_totals = OrderedDict()

    skus = skus.get_totals()

    for sku in skus:
        if sku.state not in states_totals:
            states_totals[sku.state] = {}
            states_totals[sku.state]["total"] = sku.total
            states_totals[sku.state]["available_total"] = sku.available_total
        else:
            states_totals[sku.state]["total"] += sku.total
            states_totals[sku.state]["available_total"] += sku.available_total

        total["total"] += sku.total
        total["available_total"] += sku.available_total
    return states_totals, total


class SingleProduct(models.Model):
    pass


class ProductImage(models.Model):
    product = models.ForeignKey(Product)
    image = models.ImageField(verbose_name="Weiteres Bild")
