from django.contrib import admin
from .models import Order, ProductOrder, InvoiceOrder,PositionProductOrder,PositionProductOrderPicklist

# Register your models here.
admin.site.register(Order)
admin.site.register(InvoiceOrder)
admin.site.register(ProductOrder)
admin.site.register(PositionProductOrder)
admin.site.register(PositionProductOrderPicklist)
