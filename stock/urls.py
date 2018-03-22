from django.conf.urls import url
from .views import StockListView, StockCreateView, StockDocumentDetailView, StockUpdateView, StockDetailView, \
    StockImportView

urlpatterns = [
    url(r'^$', StockListView.as_view(), name="list"),
    url(r'^create/$', StockCreateView.as_view(), name="create"),
    url(r'^document/(?P<pk>\d+)/$', StockDocumentDetailView.as_view(), name="documentdetail"),
    url(r'^(?P<pk>\d+)/edit/$', StockUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/$', StockDetailView.as_view(), name="detail"),
    url(r'^table/$', StockListView.as_view(), name="table"),
    url(r'^table/(?P<pk>\d+)/edit/$', StockUpdateView.as_view(), name="edit"),
    url(r'^table/(?P<pk>\d+)/$', StockDetailView.as_view(), name="detail"),
    url(r'^import/$', StockImportView.as_view(), name="import"),
]
