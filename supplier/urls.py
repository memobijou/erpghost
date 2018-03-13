from django.conf.urls import url
from supplier.views import SupplierListView, SupplierDetailView, SupplierCreateView, SupplierUpdateView

urlpatterns = [
    url(r'^$', SupplierListView.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/$', SupplierDetailView.as_view(), name="detail"),
    url(r'^create/$', SupplierCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/edit/$', SupplierUpdateView.as_view(), name="update"),
]