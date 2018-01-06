from import_export import resources
from .models import Stock

class StockResource(resources.ModelResource):
    class Meta:
        model = Stock
        import_id_fields = ['ean_vollstaendig', 'lagerplatz']
        