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
    status = models.CharField(max_length=25, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, null=True, blank=True,related_name = 'order')

    products = models.ManyToManyField(Product, through="ProductOrder")
    invoice = models.ManyToManyField(Invoice, through="InvoiceOrder")

    def __str__(self):
        return self.ordernumber

    def get_absolute_url(self):
        return reverse("order:detail", kwargs={"pk": self.id})


class ProductOrder(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, unique=False, blank=False, null=False)
    amount = models.IntegerField(null=False, blank=False, default=0)

    confirmed = models.NullBooleanField()

    def __str__(self):
    	return str(self.product) + " : " + str(self.order) + " : " + str(self.amount)


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

 