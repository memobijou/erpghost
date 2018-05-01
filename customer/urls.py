from django.conf.urls import url
from customer.views import CustomerListView, CustomerDetailView, CustomerCreateView, CustomerUpdateView, \
    CustomerDeleteView

urlpatterns = [
    url(r'^$', CustomerListView.as_view(), name="list"),
    url(r'^(?P<pk>\d+)/$', CustomerDetailView.as_view(), name="detail"),
    url(r'^create/$', CustomerCreateView.as_view(), name="create"),
    url(r'^(?P<pk>\d+)/edit/$', CustomerUpdateView.as_view(), name="update"),
    url(r'^delete/$', CustomerDeleteView.as_view(), name="delete"),
]
