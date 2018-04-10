from django.conf.urls import url
from .views import StockListView, StockCreateView, StockDocumentDetailView, StockUpdateView, StockDetailView, \
    StockImportView, StockCopyView, PositionListView, BookProductToPositionView, StockDeleteView

urlpatterns = [
    url(r'^$', StockListView.as_view(), name="list"),
    url(r'^create/$', StockCreateView.as_view(), name="create"),
    url(r'^delete/(?P<pk>\d+)/$', StockDeleteView.as_view(), name="delete"),
    url(r'^document/(?P<pk>\d+)/$', StockDocumentDetailView.as_view(), name="documentdetail"),
    url(r'^(?P<pk>\d+)/edit/$', StockUpdateView.as_view(), name="edit"),
    url(r'^(?P<pk>\d+)/$', StockDetailView.as_view(), name="detail"),
    url(r'^(?P<pk>\d+)/copy/$', StockCopyView.as_view(), name="copy"),
    url(r'^import/$', StockImportView.as_view(), name="import"),
    url(r'^position/$', PositionListView.as_view(), name="position_list"),
    url(r'^position/(?P<pk>\d+)/book/$', BookProductToPositionView.as_view(), name="position_book"),
]
