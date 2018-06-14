from django.db import models

from sku.models import Sku
from supplier.models import Supplier
from django.urls import reverse
from django.db.models import Max


class Manufacturer(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Hersteller")


class Brand(models.Model):
    name = models.CharField(blank=True, null=False, max_length=200, verbose_name="Markenname")


class Product(models.Model):
    main_image = models.ImageField(verbose_name="Bild", null=True, blank=True)

    ean = models.CharField(blank=True, null=False, max_length=200, verbose_name="EAN")
    main_sku = models.IntegerField(blank=True, null=True, verbose_name="SKU")
    title = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Artikelname")
    manufacturer = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Hersteller")
    brandname = models.CharField(max_length=500, null=True, blank=True, default="", verbose_name="Markenname")
    part_number = models.CharField(blank=True, null=True, max_length=200, verbose_name="Herstellernummer")

    short_description = models.TextField(null=True, blank=True, default="", verbose_name="Kurzbeschreibung")
    description = models.TextField(null=True, blank=True, default="", verbose_name="Beschreibung")

    single_product = models.ForeignKey("product.SingleProduct", null=True, blank=True)

    height = models.FloatField(null=True, blank=True, default=None, verbose_name="Höhe")
    width = models.FloatField(null=True, blank=True, default=None, verbose_name="Breite")
    length = models.FloatField(null=True, blank=True, default=None, verbose_name="Länge")

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
            self.main_sku = int(self.pk) + 1

        super().save()

        if self.single_product is not None and self.single_product != "":
            return  # SKU will then be created from single_product form

        if generate_skus is True:
            bulk_instances = [Sku(product_id=self.pk, sku=f"{self.main_sku}", state="Neu"),
                              Sku(product_id=self.pk, sku=f"A{self.main_sku}", state="A"),
                              Sku(product_id=self.pk, sku=f"B{self.main_sku}", state="B"),
                              Sku(product_id=self.pk, sku=f"C{self.main_sku}", state="C"),
                              Sku(product_id=self.pk, sku=f"D{self.main_sku}", state="D")]
            Sku.objects.bulk_create(bulk_instances)

    def get_state_from_sku(self, sku):
        if sku is not None and sku != "":
            for product_sku in self.sku_set.all():
                if product_sku.sku == sku:
                    return product_sku.state

    def get_sku_from_state(self, state):
        if state is not None and state != "":
            return self.sku_set.filter(state=state).first()


class SingleProduct(models.Model):
    ean = models.CharField(max_length=200, verbose_name="EAN", null=True, blank=True)


class ProductImage(models.Model):
    product = models.ForeignKey(Product)
    image = models.ImageField(verbose_name="Weiteres Bild")
