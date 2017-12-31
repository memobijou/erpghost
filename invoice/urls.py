from django.conf.urls import url
from .views import InvoiceListView

urlpatterns = [
	url(r'^$', InvoiceListView.as_view(), name="list"),
]   