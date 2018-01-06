from django.contrib import admin
from stock.models import Stockdocument, Stock
# Register your models here.

admin.site.register(Stockdocument)
admin.site.register(Stock)