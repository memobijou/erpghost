from django.db import models
import datetime
from django.utils import timezone
from django.core.urlresolvers import reverse
from product.models import Product
from invoice.models import Invoice
from supplier.models import Supplier

# Create your models here.

class Order(models.Model):
    ordernumber = models.CharField(max_length=13)
    delivery_date = models.DateField(default=datetime.date.today)
    status = models.CharField(max_length=25, null=True, blank=True, default="OFFEN")
    supplier = models.ForeignKey(Supplier, null=True, blank=True,related_name = 'order')
    products = models.ManyToManyField(Product, through="ProductOrder")
    invoice = models.ManyToManyField(Invoice, through="InvoiceOrder")
    CHOICES = (
        (None, "----"),
        (True, "Ja"),
        (False, "Nein")
    )
    verified = models.NullBooleanField(choices = CHOICES)

    def __str__(self):
        return self.ordernumber

    def get_absolute_url(self):
        return reverse("order:detail", kwargs={"pk": self.id})

    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        self.__original_verified = self.verified

    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if self.__original_verified != self.verified:
            if self.verified == True:
                # name changed - do something here
                self.status = "AKZEPTIERT"
            elif self.verified == False:
                self.status = "ABGELEHNT"
        super(Order, self).save(force_insert=False, force_update=False, *args, **kwargs)

class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    amount = models.IntegerField(null=False, blank=False, default=0)

    confirmed = models.NullBooleanField()

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
                if product_order.confirmed == True or product_order.confirmed == False:
                    self.order.status = "WARENEINGANG"
                else:
                    all_scanned = False

        if all_scanned and product_orders.exists():
            self.order.status = "POSITIONIEREN"
        self.order.save()
        super(ProductOrder, self).save(*args, **kwargs)



class InvoiceOrder(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE,unique=False)
    order= models.ForeignKey(Order, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    datum = models.CharField(max_length=13)
    extra_text = models.CharField(max_length=13)
    terms_of_payment = models.CharField(max_length=13)
    
    class Meta:
        unique_together = ('invoice', 'order',)


    def __str__(self):
    	return str(self.invoice) + ":" +  str(self.order)

 